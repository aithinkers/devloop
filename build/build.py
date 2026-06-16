#!/usr/bin/env python3
"""DevLoop build — a generic engine that arranges common artifacts into per-tool packages.

Source of truth:
  core/roles.json        neutral role definitions (id, title, body, command, description, summary)
  core/*.md              role bodies
  core/shared/*          shared templates / guides / example configs
  tools/wikikit.py       the helper script (one copy)

Each tool folder owns an `adapter.json` describing ONLY its tool-specific arrangement
(kind = claude-code | codex | kiro). This script reads core + every adapter and generates
that tool's files. Adding a new tool = add a folder with an adapter.json (+ a builder here
if its packaging shape is new). Authored, never generated: plugin.json, marketplace.json,
kiro steering/README, codex AGENTS.md.

Usage:
  build.py            regenerate the platform folders in place
  build.py --check    rebuild in memory and diff against committed files; exit 1 if stale
"""
import os, sys, json, shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(REPO, "core")
SHARED = os.path.join(CORE, "shared")
WIKIKIT = os.path.join(REPO, "tools", "wikikit.py")
PLUGIN_JSON = os.path.join(REPO, "claude-code", ".claude-plugin", "plugin.json")

# Everything under these prefixes is owned by the generator (cleaned + rewritten).
GEN_PREFIXES = [
    "claude-code/skills/", "claude-code/commands/", "claude-code/agents/",
    "codex/prompts/", "codex/tools/",
    "kiro/skills/", "kiro/agents/", "kiro/steering/", "kiro/hooks/", "kiro/settings/", "kiro/tools/",
]

def rd(p):
    with open(p, "rb") as f:
        return f.read()

def shared(name):
    return rd(os.path.join(SHARED, name))

def load_roles():
    data = json.load(open(os.path.join(CORE, "roles.json")))
    return {r["id"]: r for r in data["roles"]}, [r["id"] for r in data["roles"]]

def load_adapters():
    """Find every <tool>/adapter.json under the repo and return {dir: adapter}."""
    out = {}
    for name in sorted(os.listdir(REPO)):
        ap = os.path.join(REPO, name, "adapter.json")
        if os.path.isfile(ap):
            out[name] = json.load(open(ap))
    return out

# ----------------------------- per-tool builders -----------------------------
def emit_skill(tooldir, rid, r, cfg, tools, out):
    """An Agent Skill (agentskills.io shape): skills/<id>/SKILL.md = name+description
    frontmatter + the role body, bundling its shared/ templates and scripts/. Shared by the
    Claude and Kiro builders — the skill body is the single canonical copy of each role."""
    base = f"{tooldir}/skills/{rid}"
    fm = f"---\nname: {rid}\ndescription: {r['description']}\n---\n\n".encode()
    out[f"{base}/SKILL.md"] = fm + rd(os.path.join(CORE, r["body"]))
    for s in cfg.get("shared", []):
        out[f"{base}/shared/{s}"] = shared(s)
    for script in cfg.get("scripts", []):
        out[f"{base}/scripts/{script}"] = tools[script]

def build_claude(tooldir, adapter, roles, order, tools, out):
    for rid in order:
        r = roles[rid]
        cfg = adapter["roles"].get(rid)
        if cfg is None:
            continue
        emit_skill(tooldir, rid, r, cfg, tools, out)
        out[f"{tooldir}/commands/{r['command']}.md"] = (
            f"---\ndescription: {r['title']} — see the {rid} skill\n"
            f"argument-hint: \"[optional: a one-line feature idea or context]\"\n---\n"
            f"Adopt the **{r['title']}** role defined in the `{rid}` skill. {r['summary']}\n\n"
            f"If any arguments were provided, treat them as the starting context: $ARGUMENTS\n").encode()
        if cfg.get("subagent"):
            out[f"{tooldir}/agents/{rid}.md"] = (
                f"---\nname: {rid}\ndescription: {r['description']}\n"
                f"tools: {cfg['subagent_tools']}\nskills: [{rid}]\n---\n"
                f"You are the **{r['title']}**. Follow the method in the `{rid}` skill "
                f"(do not restate it). {r['summary']}\n").encode()

def _tools_into(tooldir, adapter, tools, out):
    """Copy every tools/*.py into the tool's tools dir (dir of wikikit_dest)."""
    dest = adapter.get("wikikit_dest")
    if not dest:
        return
    d = os.path.dirname(dest)
    for name, data in tools.items():
        out[f"{tooldir}/{d}/{name}" if d else f"{tooldir}/{name}"] = data

def build_codex(tooldir, adapter, roles, order, tools, out):
    titles = adapter.get("titles", {})
    for rid in order:
        r = roles[rid]
        spec = adapter["prompts"].get(r["command"])
        if spec is None:
            continue
        buf = bytearray(rd(os.path.join(CORE, r["body"])))
        for inc in spec.get("includes", []):
            title = titles.get(inc, inc)
            body = shared(inc).decode()
            if inc.endswith(".json"):
                body = "```json\n" + body.rstrip("\n") + "\n```"
            buf += f"\n---\n## {title}\n\n{body}\n".encode()
        out[f"{tooldir}/prompts/{r['command']}.md"] = bytes(buf)
    _tools_into(tooldir, adapter, tools, out)

def build_kiro(tooldir, adapter, roles, order, tools, out):
    """Kiro 0.9 packaging: one Agent Skill per role (reusing emit_skill — identical to
    Claude), a thin custom subagent per subagent role, ONE lean auto-steering orchestrator
    that only sequences the phases (no restated bodies), and manual hooks for the
    deterministic helpers."""
    present = [rid for rid in order if adapter["roles"].get(rid) is not None]
    for rid in present:
        r, cfg = roles[rid], adapter["roles"][rid]
        emit_skill(tooldir, rid, r, cfg, tools, out)
        if cfg.get("subagent"):
            tools_list = ", ".join(cfg["subagent_tools"])
            out[f"{tooldir}/agents/{rid}.md"] = (
                f"---\nname: {rid}\ndescription: {r['description']}\n"
                f"tools: [{tools_list}]\n---\n"
                f"You are the **{r['title']}**. Follow the method in the `{rid}` Agent Skill "
                f"(do not restate it). {r['summary']}\n").encode()
    # Lean auto-steering orchestrator — sequences the chain, points at each skill, no bodies.
    st = adapter["steering"]
    lines = [f"---\ninclusion: auto\nname: {st['name']}\ndescription: {st['description']}\n---\n",
             "# DevLoop — business-analysis chain\n",
             "Turn a feature idea into a review-ready backlog through five **gated** roles. Each",
             "phase gates the next — do not skip ahead. Adopt the matching **Agent Skill** for each",
             "phase; the skill carries the full method, so this file only sequences them.\n"]
    for i, rid in enumerate(present):
        r = roles[rid]
        lines.append(f"{i+1}. **{r['title']}** — adopt the `{rid}` skill (or `/{rid}` subagent). {r['summary']}")
    lines += ["",
              "Helpers live in `tools/` — run them as `python3 tools/wikikit.py …` and",
              "`python3 tools/ingest.py <folder> --wiki <id>` (or use the DevLoop hooks). DevLoop's",
              "`requirements.md` is richer than Kiro's native EARS spec (personas, FR/NFR, risks); it",
              "**feeds** a Kiro feature spec rather than replacing it.\n"]
    out[f"{tooldir}/steering/{st['name']}.md"] = ("\n".join(lines)).encode()
    # Manual hooks for the deterministic steps (.kiro.hook JSON).
    for h in adapter.get("hooks", []):
        hook = {"enabled": True, "name": h["name"], "description": h["description"],
                "version": "1", "when": {"type": h["trigger"]},
                "then": {"type": "runCommand", "command": h["command"]}}
        out[f"{tooldir}/hooks/{h['file']}.kiro.hook"] = (json.dumps(hook, indent=2) + "\n").encode()
    # Example MCP config (schema-clean: only mcpServers). Installed only-if-absent so it never
    # clobbers a real .kiro/settings/mcp.json. SharePoint server ships disabled by default.
    mcp = adapter.get("mcp")
    if mcp:
        out[f"{tooldir}/settings/mcp.json"] = (
            json.dumps({"mcpServers": mcp["servers"]}, indent=2) + "\n").encode()
    _tools_into(tooldir, adapter, tools, out)

BUILDERS = {"claude-code": build_claude, "codex": build_codex, "kiro": build_kiro}

# ------------------------------- engine --------------------------------------
def load_tools():
    d = os.path.join(REPO, "tools")
    return {f: rd(os.path.join(d, f)) for f in sorted(os.listdir(d)) if f.endswith(".py")}

def stamp_plugin_version(write):
    """Keep the Claude plugin manifest's `version` in lockstep with the VERSION file (it would
    otherwise be a hand-maintained duplicate that drifts). Returns the expected version if
    plugin.json is stale, else None."""
    v = open(os.path.join(REPO, "VERSION")).read().strip()
    data = json.load(open(PLUGIN_JSON))
    if data.get("version") == v:
        return None
    if write:
        data["version"] = v
        with open(PLUGIN_JSON, "w") as f:
            json.dump(data, f, indent=2); f.write("\n")
    return v

def plan():
    roles, order = load_roles()
    tools = load_tools()
    out = {}
    for tooldir, adapter in load_adapters().items():
        builder = BUILDERS.get(adapter.get("kind"))
        if not builder:
            raise SystemExit(f"{tooldir}/adapter.json: unknown kind {adapter.get('kind')!r}")
        builder(tooldir, adapter, roles, order, tools, out)
    return out

def on_disk_generated():
    found = set()
    for pre in GEN_PREFIXES:
        for dp, _, files in os.walk(os.path.join(REPO, pre)):
            for f in files:
                found.add(os.path.relpath(os.path.join(dp, f), REPO))
    return found

def write_all():
    for pre in GEN_PREFIXES:
        shutil.rmtree(os.path.join(REPO, pre.rstrip("/")), ignore_errors=True)
    p = plan()
    for rel, data in p.items():
        dst = os.path.join(REPO, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "wb") as f:
            f.write(data)
    if stamp_plugin_version(write=True):
        print("  stamped plugin.json version from VERSION")
    print(f"✓ generated {len(p)} files from core/ + tools/ + adapters")

def check():
    p = plan()
    want, disk = set(p), on_disk_generated()
    drift = []
    for rel in sorted(want | disk):
        if rel not in disk:
            drift.append(f"missing on disk: {rel}")
        elif rel not in want:
            drift.append(f"stale (not in source): {rel}")
        elif rd(os.path.join(REPO, rel)) != p[rel]:
            drift.append(f"out of date: {rel}")
    stale_v = stamp_plugin_version(write=False)
    if stale_v:
        drift.append(f"plugin.json version != VERSION ({stale_v}) — run ./build.sh")
    if drift:
        print("Generated tree is STALE — run ./build.sh:")
        for d in drift:
            print(f"  {d}")
        return 1
    print(f"✓ generated tree is up to date ({len(want)} files)")
    return 0

def main():
    sys.exit(check()) if "--check" in sys.argv else write_all()

if __name__ == "__main__":
    main()
