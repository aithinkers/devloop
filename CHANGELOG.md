# Changelog

All notable changes to DevLoop are documented here. Versioning is semantic.

## [0.8.2]
Execution-model honesty + operational robustness (review follow-up):
- **sync exits non-zero on fatal git errors.** `wikikit.py sync` now returns a non-zero exit
  (and a `FAILED` summary) when a clone/fetch/checkout fails, instead of silently exiting 0 —
  so scripted sync/refresh steps surface failures. Missing `git` is reported cleanly (no traceback).
- **Source types are no longer presented as interchangeable `sync` targets.** Only `git`
  sources are auto-fetched by `sync`; for a `local` source with no `raw/` yet, `sync` prints the
  exact `ingest.py <source.path> --wiki <id>` command; `url` sources are fetched/pasted manually.
  README, the Context Librarian role, and the cheatsheet now describe each path accurately.
- **Helper invocation model documented + helpers made executable.** Installed `wikikit.py`/
  `ingest.py` get the executable bit, and the docs explain they aren't on `PATH` — the host
  agent runs them from the install location, or you run `python3 <path>/wikikit.py …`. Manual
  test path and Codex `AGENTS.md` now use runnable commands at the installed location.
- **`devloop doctor` checks reality, not optimism.** Install status now verifies a real marker
  file + that `wikikit.py` compiles/runs and `ingest.py` is present, flagging broken installs
  instead of reporting OK on directory existence alone.
- **tests:** smoke test 22 → 28 — sync non-zero on git failure, local-sync ingest hint,
  installed-helper runs end to end + executable bit, and `doctor` flags a broken install.

## [0.8.1]
First-run / onboarding fixes (host parity + docs accuracy):
- **install:** the CLI now installs **both** helper tools (`wikikit.py` + `ingest.py`) into every host's `tools/`, matching the docs that reference `tools/ingest.py`. Previously only `wikikit.py` was copied, so the documented ingest workflow was missing after install. Uninstall removes both.
- **ingest.py:** fixed the `--wiki` default registry name (`bastack.wikis.json` → `devloop.wikis.json`), which broke the documented registry-resolved ingest path by default.
- **Codex:** prompts are now genuinely self-contained — `spec-context` inlines `wiki-index-template.md` and `spec-stories` inlines `definition-of-ready.md`, both previously cited in the body but not bundled.
- **install URLs:** replaced `<owner>`/`your-org` placeholders with `aithinkers` in `install.sh` and the README so the `curl … | sh` bootstrap and plugin commands work as published.
- **tests:** smoke test grows from 18 → 22 checks — cross-host install/uninstall of both helpers, the `ingest.py --wiki` registry path, and a Codex self-containment invariant (every `shared/<file>` a role body cites must be inlined).

## [0.8.0]
- Renamed the project to **DevLoop** (binary `devloop`, configs devloop.*.json). Spec-phase commands stay `/spec-*`; the planned delivery loop will add its own.
- `tools/ingest.py`: recursive multi-format extraction (docx/pptx/xlsx/drawio/vsdx/svg/html/text, PDF via pdftotext/pypdf), flags images/scanned for agent vision. Wiki source scan is now recursive (subfolders).

## [0.7.0]
- Renamed the project to **DevLoop** (CLI `devloop`, commands `/spec-*`).
- `devloop` CLI: `install` / `uninstall` / `list` / `doctor` / `build`, with
  `--host claude|kiro|codex|all`, `--scope project|home`, and `--dry-run`.
- `install.sh` is now a `curl … | sh` bootstrap (clones the repo and runs the CLI).
- MIT license, CONTRIBUTING, CHANGELOG, and GitHub Actions CI.

## [0.6.0]
- Single source of truth: `core/roles.json` + per-tool `adapter.json`; `build.py` is a
  generic engine that arranges common artifacts into each tool's package.
- Smoke test enforces build freshness (`build.py --check`).

## [0.5.0]
- Jira: organization recommendation (BA vs TECH projects, issue types incl. Requirement/
  Decision), `devloop.jira.json` config, config-aware per-story mapping, `wikikit jira` cmds.

## [0.4.0]
- Multi-wiki registry (project / integrations / devops / codebase), git-backed sources with
  `wikikit sync`, cross-wiki `[[namespace:Concept]]` links and `lint --all`.

## [0.3.0]
- Context Librarian adopts the LLM-Wiki model; `wikikit.py` helper; smoke test.

## [0.2.0]
- Context Librarian role grounds requirements in existing documentation.

## [0.1.0]
- Initial role chain: Requirements Analyst, Story Writer, Story Reviewer for Claude Code,
  Kiro, and Codex.
