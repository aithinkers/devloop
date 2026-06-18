#!/usr/bin/env python3
"""DevLoop build — generates the host packages from one canonical source.

All three hosts now consume the open agentskills.io Agent Skill format, so the skill bodies
are generated ONCE into the repo-root `skills/` library (no per-host copies). Around that one
library, the build adds only the genuinely host-specific wrappers:

  source of truth
    core/roles.json   role identity + which shared/ templates & scripts each skill bundles
    core/0X-*.md      role bodies
    core/shared/*     shared templates / guides / example configs
    tools/*.py        helper scripts (wikikit.py, ingest.py)

  generated
    skills/<id>/      the canonical Agent Skills (SKILL.md + shared/ + scripts/) — used by
                      Claude in place; the CLI copies them to .kiro/skills & .agents/skills
    commands/, agents/   Claude slash-command + subagent wrappers (thin pointers to skills)
    .claude-plugin/plugin.json   version stamped from VERSION
    kiro/steering/devloop.md     Kiro lean auto-steering orchestrator (skills installed by the CLI)

  authored (never generated): .claude-plugin/{plugin.json fields, marketplace.json},
    kiro/{adapter.json, README.md}, codex/AGENTS.md (Codex's gated-chain orchestrator).
  Codex needs no generated package — the CLI installs the root skills to .agents/skills.

Usage:
  build.py            regenerate in place
  build.py --check    rebuild in memory and diff against committed files; exit 1 if stale
"""
import os, sys, json, shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(REPO, "core")
SHARED = os.path.join(CORE, "shared")
PLUGIN_JSON = os.path.join(REPO, ".claude-plugin", "plugin.json")

# Everything under these prefixes is owned by the generator (cleaned + rewritten).
GEN_PREFIXES = [
    "skills/", "commands/", "agents/",
    "kiro/steering/",
]

# Claude subagent tool vocab (full Claude tool names), per role flagged subagent in roles.json.
CLAUDE_SUBAGENT_TOOLS = {
    "context-librarian": "Read, Write, Edit, Glob, Grep, Bash, WebFetch",
    "business-analyst": "Read, Write, Edit, Glob, Grep",
    "requirements-analyst": "Read, Write, Edit, Glob, Grep",
}

def rd(p):
    with open(p, "rb") as f:
        return f.read()

def shared(name):
    return rd(os.path.join(SHARED, name))

def load_roles():
    data = json.load(open(os.path.join(CORE, "roles.json")))
    return {r["id"]: r for r in data["roles"]}, [r["id"] for r in data["roles"]]

def load_tools():
    d = os.path.join(REPO, "tools")
    return {f: rd(os.path.join(d, f)) for f in sorted(os.listdir(d)) if f.endswith(".py")}

# ------------------------- the one canonical skill library -------------------
def build_skills(roles, order, tools, out):
    """One Agent Skill per role at repo-root skills/<id>/ (agentskills.io). This is the single
    copy every host uses — Claude reads it in place; the installer copies it to Kiro/Codex."""
    for rid in order:
        r = roles[rid]
        # description is JSON-quoted so colons/quotes in the text stay valid YAML frontmatter
        fm = f"---\nname: {rid}\ndescription: {json.dumps(r['description'], ensure_ascii=False)}\n---\n\n".encode()
        out[f"skills/{rid}/SKILL.md"] = fm + rd(os.path.join(CORE, r["body"]))
        for s in r.get("shared", []):
            out[f"skills/{rid}/shared/{s}"] = shared(s)
        for script in r.get("scripts", []):
            out[f"skills/{rid}/scripts/{script}"] = tools[script]

# ------------------------------- Claude (root host) --------------------------
def build_claude(roles, order, out):
    """Claude consumes root skills/ directly (plugin root = repo root). Add thin slash-command
    wrappers and, for subagent roles, a subagent that preloads + points at the skill."""
    for rid in order:
        r = roles[rid]
        out[f"commands/{r['command']}.md"] = (
            f"---\ndescription: {json.dumps(r['title'] + ' — see the ' + rid + ' skill', ensure_ascii=False)}\n"
            f"argument-hint: \"[optional: a one-line feature idea or context]\"\n---\n"
            f"Adopt the **{r['title']}** role defined in the `{rid}` skill. {r['summary']}\n\n"
            f"If any arguments were provided, treat them as the starting context: $ARGUMENTS\n").encode()
        if r.get("subagent"):
            out[f"agents/{rid}.md"] = (
                f"---\nname: {rid}\ndescription: {json.dumps(r['description'], ensure_ascii=False)}\n"
                f"tools: {CLAUDE_SUBAGENT_TOOLS[rid]}\nskills: [{rid}]\n---\n"
                f"You are the **{r['title']}**. Follow the method in the `{rid}` skill "
                f"(do not restate it). {r['summary']}\n").encode()

# ------------------------------- Kiro wrappers -------------------------------
def build_kiro(adapter, roles, order, out):
    """Kiro (gstack-style): the CLI installs the shared skills/ library namespaced under
    .kiro/skills/devloop/. The only generated wrapper is ONE lean auto-steering orchestrator that
    sequences the gated chain and points at each skill. No subagents / hooks / MCP."""
    st = adapter["steering"]
    lines = [f"---\ninclusion: auto\nname: {st['name']}\ndescription: {json.dumps(st['description'], ensure_ascii=False)}\n---\n",
             "# DevLoop — business-analysis chain\n",
             "Turn a feature idea into a review-ready backlog through a chain of **gated** roles. Each",
             "phase gates the next — do not skip ahead. Adopt the matching **Agent Skill** for each",
             "phase (auto-triggers by description, or invoke `$<role>` / pick from `/skills`); the",
             "skill carries the full method, so this file only sequences them.\n"]
    for i, rid in enumerate(order):
        r = roles[rid]
        lines.append(f"{i+1}. **{r['title']}** — adopt the `{rid}` skill (`${rid}` or `/skills`). {r['summary']}")
    lines += ["",
              "The helper scripts are bundled inside the `context-librarian` skill (`scripts/`) and",
              "also installed at `.kiro/tools/` — run them as `python3 .kiro/tools/wikikit.py …` and",
              "`python3 .kiro/tools/ingest.py <folder> --wiki <id>`. DevLoop's `requirements.md` is",
              "richer than Kiro's native EARS spec (personas, FR/NFR, risks); it **feeds** a Kiro",
              "feature spec, not replaces it.\n"]
    out[f"kiro/steering/{st['name']}.md"] = ("\n".join(lines)).encode()

# ------------------------------- engine --------------------------------------
def stamp_plugin_version(write):
    """Keep the Claude plugin manifest's `version` in lockstep with the VERSION file (else it is
    a hand-maintained duplicate that drifts). Returns the expected version if stale, else None."""
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
    build_skills(roles, order, tools, out)
    build_claude(roles, order, out)
    build_kiro(json.load(open(os.path.join(REPO, "kiro", "adapter.json"))), roles, order, out)
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
    print(f"✓ generated {len(p)} files from core/ + tools/ (one skills/ library + host wrappers)")

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
