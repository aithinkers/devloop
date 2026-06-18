# Architecture

DevLoop is **one source, arranged per host**. The role content lives once; each host gets the
thin wrapper it natively understands. That's what lets the same methodology run on Claude Code,
Kiro, and Codex without three copies to keep in sync.

## The flow: `core/` → `skills/` → host wrappers

```
core/roles.json     role identity + which shared/ templates & scripts each role bundles
core/0X-*.md        role bodies (the actual method)            ─┐
core/shared/*       templates, guides, example configs          │  build/build.py
tools/*.py          wikikit.py, ingest.py                       ─┘        │
                                                                          ▼
skills/<role>/SKILL.md          ← the ONE canonical Agent Skill library (agentskills.io)
   + shared/  + scripts/           (name + description frontmatter + the role body)
                                                                          │
                 ┌────────────────────────────────┼────────────────────────────────┐
                 ▼                                 ▼                                 ▼
   Claude: skills/ in place              Kiro: skills → .kiro/skills/devloop/   Codex: skills →
   + commands/ + agents/ (subagents)     + a lean inclusion:auto steering/      .agents/skills/
   + .claude-plugin/plugin.json          devloop.md orchestrator                + AGENTS.md orchestrator
```

- **Skills are generated once.** All three hosts read the same `SKILL.md` format, so the skill
  bodies are byte-identical across hosts (a smoke test enforces it). Only the *wrappers* differ.
- **Each host gets its idiom, nothing more.** Claude has first-class commands + subagents, so it
  ships them. Kiro reliably surfaces *skills* (not `/`-slash subagents), so it ships skills + one
  steering orchestrator — no subagents/hooks. Codex ships skills + an `AGENTS.md` orchestrator
  (its custom prompts are deprecated).
- **The CLI assembles per host.** `devloop install` copies the root `skills/` to each host's
  location (`.claude/skills`, `.kiro/skills/devloop`, `.agents/skills`) and lays down the
  wrappers; `wikikit.py` + `ingest.py` go to the host's `tools/`.

## No-drift guarantees
A content change is made **once** in `core/`. `./devloop build` regenerates everything;
`./devloop build --check` (run in CI and the smoke test) **fails** if:
- the generated tree is stale vs `core/`,
- `.claude-plugin/plugin.json`'s version ≠ `VERSION` (it's stamped, not hand-maintained),
- and the smoke suite additionally checks: frontmatter is valid YAML, descriptions are quoted,
  shared docs carry no host-specific `/spec-*`, the Codex orchestrator lists every role, and
  skill bodies are identical across hosts.

## Adding a host or a role
- **New host** mostly means: copy the shared `skills/` to its location + a thin wrapper. See
  `build/build.py` (`build_kiro` is the example) and `devloop` (`install_*`).
- **New role**: add the body in `core/0X-*.md` and register it in `core/roles.json` (its bundled
  `shared`/`scripts` + whether it's a `subagent`). Two authored files don't regenerate — update
  `codex/AGENTS.md` (guarded by a smoke test) and the host-count prose in the READMEs. See
  [../RELEASE-CHECKLIST.md](../RELEASE-CHECKLIST.md) and [../CONTRIBUTING.md](../CONTRIBUTING.md).
