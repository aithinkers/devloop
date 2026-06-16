# Changelog

All notable changes to DevLoop are documented here. Versioning is semantic.

## [0.11.0]
Collapsed to **one canonical skills library** (Superpowers-style), now that all three hosts read
the agentskills.io Agent Skill format. Previously the build generated three byte-identical skill
trees (`claude-code/skills`, `codex/skills`, `kiro/skills`) — that triplication is gone:
- **Single `skills/` at the repo root** is the only skill copy. Claude uses it in place (the
  plugin root is now the repo root: `.claude-plugin/plugin.json` moved to root,
  `marketplace.json` source → `.`); the CLI copies the same `skills/` to `.kiro/skills` and
  `.agents/skills` at install. Skills *can't* fork because there's one tree.
- **Slimmer engine.** `build.py` generates the one `skills/` library plus only host-specific
  wrappers — Claude `commands/`+`agents/` at root, and `kiro/{agents,steering,hooks,settings}`.
  Generated file count dropped from 80 → 34. Per-role `shared`/`scripts`/`subagent` config moved
  into `core/roles.json`; `kiro/adapter.json` keeps only Kiro's tool vocab + steering/hooks/MCP.
- **Removed** the `claude-code/` package dir and `codex/adapter.json` (Codex needs no generated
  package — its skills come from the root library; `codex/AGENTS.md` stays as the orchestrator).
- CLI install/uninstall/list/doctor updated for the new layout; helper tools still install to
  each host and stay executable.
- **tests:** smoke test stays at 44 — now asserting a single-source `skills/` (no per-host
  copies), the root-level Claude plugin (`source: "."`), and all-host install from the one library.

## [0.10.0]
Migrated the **Codex** integration off deprecated custom prompts to **Agent Skills** — so all
three hosts now share one agentskills.io skill packaging:
- **Codex Agent Skills.** One skill per role under `.agents/skills/<role>/SKILL.md` (home →
  `$HOME/.agents/skills`, project → the repo), bundling each role's `shared/` + `scripts/`.
  These are the **same packages as Claude/Kiro** (build.py shares one `emit_skill`); a smoke
  test asserts the Codex skill bodies are byte-identical to Claude's.
- **AGENTS.md is now the lean gated-chain orchestrator** that points at the skills (auto-select
  by description, `$skill` / `/skills`), with a documented `config.toml [mcp_servers]` snippet
  for wiring SharePoint/MCP (config.toml is user-owned, so it's documented, not shipped).
- **Dropped the deprecated `codex/prompts/`.** OpenAI deprecated Codex custom prompts in favor
  of skills; the `/spec-*` prompt commands are replaced by the auto-triggering skills.
- CLI `install`/`uninstall`/`list`/`doctor` updated for the `.agents/skills` layout; uninstall
  also clears any legacy `spec-*` prompts from a prior install.
- **tests:** smoke test 41 → 44 — Codex installs valid skills to `.agents/skills`, skill bodies
  match Claude's, AGENTS.md points at skills (not deprecated prompts), and `codex/prompts` is gone.

## [0.9.2]
Claude Code QA (validated against current 2026 plugin/skill/command/subagent schemas):
- **plugin.json version no longer drifts.** It was hardcoded (`0.8.0`) and stale; `build.py`
  now **stamps the version from the `VERSION` file**, and `build --check` fails if it drifts —
  same single-source/no-drift guarantee as the generated tree.
- **Cleaner plugin manifest.** Dropped the redundant `commands`/`skills`/`agents` path keys
  (Claude Code auto-discovers those default dirs; the `skills` key even *adds to* the default),
  and added `license`, `homepage`, `repository`.
- **Idiomatic commands & subagents.** Slash commands now declare `argument-hint` (and use
  `$ARGUMENTS` as starting context instead of a trailing "Arguments:" line); the two subagents
  now `skills:`-preload their own skill, making the thin-pointer wiring robust.
- Confirmed Kiro & Claude skill `SKILL.md` bodies remain byte-identical (single source).
- **tests:** smoke test 36 → 41 — plugin/marketplace manifest validity, version-drift guard
  (catch + restamp), and command/subagent frontmatter wiring.

## [0.9.1]
Kiro QA + SharePoint/MCP follow-up (validated against a live Kiro 0.11 install):
- Verified every generated Kiro artifact (skills, subagents, auto-steering, hooks) conforms to
  the documented 0.9–0.11 schemas — name==folder, agentskills.io frontmatter, allowed subagent
  tool vocab, valid `inclusion`, and `userTriggered`/`runCommand` hooks.
- **Wired the SharePoint promise to Kiro's native MCP.** Ship a disabled, secret-free example
  `.kiro/settings/mcp.json` (env-var token ref, schema-clean `mcpServers`). It installs **only
  if absent** — it never overwrites your real MCP config and is left untouched on uninstall.
  kiro/README documents pointing it at a Microsoft Graph / SharePoint MCP server.
- **tests:** smoke test 34 → 36 — the MCP example is valid/disabled/secret-free, and install
  never clobbers an existing `mcp.json`.

## [0.9.0]
Modernized the **Kiro** integration to the Kiro 0.9 model (Agent Skills, custom subagents,
auto-steering, hooks). Previously Kiro got a single manual steering file that hand-restated the
whole methodology plus inert `specs/_template/` copies; now it gets the same first-class
treatment as Claude:
- **Agent Skills** (`.kiro/skills/<role>/SKILL.md`) — one per role, auto-triggering by
  description, bundling each role's `shared/` templates + `scripts/`. These are **byte-identical
  to the Claude skill packages** (agentskills.io shape); the build engine now shares one
  `emit_skill` between the Claude and Kiro builders, so role content has a single source.
- **Custom subagents** (`.kiro/agents/`) for the two isolated-context roles
  (context-librarian, requirements-analyst), with Kiro's `read/write/shell/web` tool vocab.
  Each is a thin pointer to its skill — it never restates the method.
- **Lean auto-steering** (`.kiro/steering/devloop.md`, `inclusion: auto`) that only *sequences*
  the five gated phases and points at each skill (no duplicated bodies — fixes the prior
  hand-maintained drift).
- **Hooks** (`.kiro/hooks/*.kiro.hook`) — manual *DevLoop: lint wikis* / *sync wikis* runners
  for the deterministic helper steps.
- Dropped the non-idiomatic `specs/_template/`; README now positions DevLoop's richer
  `requirements.md` as *feeding* Kiro's native EARS feature spec, not replacing it.
- CLI `install`/`uninstall`/`list`/`doctor` updated for the new Kiro layout; `doctor` no longer
  writes a stray `__pycache__` during its runnability check.
- **tests:** smoke test 28 → 34 — Kiro install lands valid skills/subagents/auto-steering/hooks,
  and Kiro skill bodies are byte-identical to Claude's (single-source guard).

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
