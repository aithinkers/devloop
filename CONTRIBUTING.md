# Contributing to DevLoop

Thanks for helping! DevLoop has **one source of truth**; the per-tool folders are generated.

## Layout
- Edit **content** in `core/` — role bodies (`core/0X-*.md`), shared templates
  (`core/shared/*`), and the neutral role definitions (`core/roles.json`).
- Edit **arrangement** in each tool's `adapter.json` (`claude-code/`, `kiro/`, `codex/`).
- Edit the **helper** in `tools/wikikit.py` (one copy).
- Authored, tool-specific files you may also edit: `claude-code/.claude-plugin/plugin.json`,
  `.claude-plugin/marketplace.json`, `kiro/README.md`, `codex/AGENTS.md`.
- **Never** hand-edit anything under `claude-code/skills|commands|agents`, `codex/prompts`,
  `kiro/skills|agents|steering|hooks|settings`, or the generated `wikikit.py`/`ingest.py`
  copies — they are build outputs.

## Workflow
```bash
# make your change in core/ (or an adapter), then:
./devloop build          # regenerate the platform folders
./devloop build --check  # verify the tree is in sync (CI runs this)
bash test/smoke_test.sh  # 41 checks, no network/LLM required
```
A pull request must keep `./devloop build --check` clean and the smoke test green — CI
enforces both.

## Adding a new tool/host
1. Create a folder (e.g. `cursor/`) with an `adapter.json` (`kind` selects the builder).
2. If its packaging shape matches an existing builder, you're done. If it's genuinely new,
   add a ~15-line builder function in `build/build.py` and register it in `BUILDERS`.
3. Add an `install_<host>` / `uninstall_<host>` / `list_host` case in `devloop`.
4. `./devloop build && bash test/smoke_test.sh`.

## Adding or changing a role
Edit/add the body in `core/`, register it in `core/roles.json`, and list the shared files
it needs in each tool's `adapter.json`. Rebuild and test.
