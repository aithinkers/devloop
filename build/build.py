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

# Everything under these prefixes is owned by the generator (cleaned + rewritten).
GEN_PREFIXES = [
    "claude-code/skills/", "claude-code/commands/", "claude-code/agents/",
    "codex/prompts/", "codex/tools/", "kiro/specs/_template/", "kiro/tools/",
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
def build_claude(tooldir, adapter, roles, order, tools, out):
    for rid in order:
        r = roles[rid]
        cfg = adapter["roles"].get(rid)
        if cfg is None:
            continue
        base = f"{tooldir}/skills/{rid}"
        fm = f"---\nname: {rid}\ndescription: {r['description']}\n---\n\n".encode()
        out[f"{base}/SKILL.md"] = fm + rd(os.path.join(CORE, r["body"]))
        for s in cfg.get("shared", []):
            out[f"{base}/shared/{s}"] = shared(s)
        for script in cfg.get("scripts", []):
            out[f"{base}/scripts/{script}"] = tools[script]
        out[f"{tooldir}/commands/{r['command']}.md"] = (
            f"---\ndescription: {r['title']} — see the {rid} skill\n---\n"
            f"Adopt the **{r['title']}** role defined in the `{rid}` skill. {r['summary']}\n\n"
            f"Arguments (optional): $ARGUMENTS\n").encode()
        if cfg.get("subagent"):
            out[f"{tooldir}/agents/{rid}.md"] = (
                f"---\nname: {rid}\ndescription: {r['description']}\n"
                f"tools: {cfg['subagent_tools']}\n---\n"
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
    for src, dest in adapter.get("templates", {}).items():
        out[f"{tooldir}/specs/_template/{dest}"] = shared(src)
    _tools_into(tooldir, adapter, tools, out)

BUILDERS = {"claude-code": build_claude, "codex": build_codex, "kiro": build_kiro}

# ------------------------------- engine --------------------------------------
def load_tools():
    d = os.path.join(REPO, "tools")
    return {f: rd(os.path.join(d, f)) for f in sorted(os.listdir(d)) if f.endswith(".py")}

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
