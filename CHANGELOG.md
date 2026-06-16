# Changelog

All notable changes to DevLoop are documented here. Versioning is semantic.

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
