# Contributing to DevLoop

Thanks for helping! DevLoop has **one source of truth**; the per-tool folders are generated.

## Layout
All hosts share **one** Agent Skill library (`skills/`, generated once); each host adds only
thin wrappers around it.
- Edit **content** in `core/` — role bodies (`core/0X-*.md`), shared templates
  (`core/shared/*`), and role definitions incl. each role's bundled `shared`/`scripts` +
  `subagent` flag (`core/roles.json`).
- Edit the **helpers** in `tools/*.py` (`wikikit.py`, `ingest.py` — one copy each).
- Authored, host-specific files you may also edit: `.claude-plugin/{plugin.json,
  marketplace.json}` (the Claude plugin is the repo root), `kiro/adapter.json` (Kiro subagent
  tools + steering/hooks/MCP), `kiro/README.md`, `codex/AGENTS.md`. (`plugin.json`'s `version`
  is stamped from `VERSION` — don't hand-edit it.)
- **Never** hand-edit the build outputs: `skills/`, `commands/`, `agents/`, and
  `kiro/{agents,steering,hooks,settings}`.

## Workflow
```bash
# make your change in core/ (or an adapter), then:
./devloop build          # regenerate the platform folders
./devloop build --check  # verify the tree is in sync (CI runs this)
bash test/smoke_test.sh  # 52 checks, no network/LLM required
```
A pull request must keep `./devloop build --check` clean and the smoke test green — CI
enforces both.

## Adding a new tool/host
Most new hosts just consume the shared `skills/` library, so it's mostly CLI wiring:
1. Add an `install_<host>` / `uninstall_<host>` / `list_host` case in `devloop` that copies the
   root `skills/` (and `tools/`) to the host's location.
2. If the host needs generated wrappers (commands/subagents/steering/hooks), add a small
   builder step in `build/build.py` (see `build_kiro`) driven by a `<host>/adapter.json`, and
   list its outputs in `GEN_PREFIXES`.
3. `./devloop build && bash test/smoke_test.sh`.

## Adding or changing a role
Edit/add the body in `core/0X-*.md`, register it in `core/roles.json` (including the `shared`
templates + `scripts` its skill bundles and whether it's a `subagent`). Rebuild and test.
