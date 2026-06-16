# DevLoop

A small, opinionated **role chain for business analysis** — inspired by Garry Tan's
[gstack](https://github.com/) (role-based skills) and obra's
[Superpowers](https://github.com/obra/superpowers) (a methodology that gates each phase on
the previous one). DevLoop takes a vague feature idea and walks it through five roles to a
review-ready backlog — grounded in a library of LLM-Wikis built from your existing company
knowledge:

```
Context Librarian  →  Requirements Analyst  →  Story Writer    →  Story Reviewer    →  Jira Organizer
(compile a wiki       (grounded interview)      (epics+stories)    (INVEST/DoR)         (epics/components/labels)
 library)             requirements.md           stories.md         story-review.md      jira-plan.md
```

It installs into **Claude Code**, **Kiro**, and **Codex** from one source.

> **Status / roadmap.** Today DevLoop covers the front of the loop — grounding, requirements,
> stories, and Jira organization (the five roles below). The back half — agents that pick up
> ready stories, implement them, open PRs, review each PR against its story's acceptance
> criteria, merge, and sync Jira — is the planned next phase (it will orchestrate and delegate
> to coding agents rather than reinvent them). That's the "loop" the name points at.

## The five roles

| Role | Command | Produces |
|---|---|---|
| **Context Librarian** | `/spec-context` | a library of LLM-Wikis (project, integrations, devops, codebase…) compiled from docs, meeting minutes, processes, integration specs, code repos, wikis, SharePoint, URLs |
| **Requirements Analyst** | `/spec-requirements` | `requirements.md` — numbered FR/NFR (each tagged with wiki + source refs), personas, scope, risks, acceptance |
| **Story Writer** | `/spec-stories` | `stories.md` — epics → INVEST user stories → Gherkin AC + traceability + component/label tags |
| **Story Reviewer** | `/spec-review` | `story-review.md` — INVEST/DoR/coverage findings + prioritized fixes |
| **Jira Organizer** | `/spec-jira` | `jira-plan.md` + `devloop.jira.json` — recommends the Jira org (BA vs TECH projects, issue types, Components from wikis, labels) and captures the real setup in config (guidance only) |

Each phase gates the next. The **Context Librarian** runs first — and instead of a flat
document it **compiles** your sources into interlinked knowledge wikis (Andrej Karpathy's
[LLM Wiki](https://karpathy.ai/llmwiki) pattern; see also
[nashsu/llm_wiki](https://github.com/nashsu/llm_wiki) and
[obsidian-llm-wiki-local](https://github.com/kytmanov/obsidian-llm-wiki-local)). The
**Requirements Analyst** then runs in *grounded mode* — it reads the primary project wiki,
pulls in the referenced shared wikis (integrations/devops/codebase) as needed, only asks
about gaps, and tags each requirement with the concept article + source IDs that back it.
The Story Writer traces every story to a requirement and tags components; the **Jira
Organizer** turns the backlog into an organization plan.

## A library of wikis (not just one)

Different knowledge belongs in different wikis, and several are shared across projects and
live in their own git repos. A registry `devloop.wikis.json` lists them; git-backed wikis
are cloned into `.devloop/wikis/<id>` and refreshed on demand. Built-in `kind` profiles
shape what each wiki extracts:

| kind | source | concepts extracted |
|---|---|---|
| `project` | this repo (local) | as-is processes, decisions (from minutes), product features, glossary |
| `integrations` | shared git repo | SSO, APIs, Email, FTP/SFTP, webhooks (one article each) |
| `devops` | shared git repo | pipelines, environments, deploy/release/incident, observability |
| `codebase` | a code git repo | services/modules, APIs/endpoints, data models, config, dependencies |

Concepts link within a wiki via `[[Concept]]` and **across** wikis via a namespace:
`[[integrations:SSO]]`, `[[codebase:AuthService]]`, `[[devops:Release Pipeline]]`. Jira
**Components** are derived from the `codebase`/`integrations` wikis. To refresh everything:
`wikikit.py sync --all`, recompile what changed, then `lint --all`.

### Inside a single wiki

Raw documents force every later question to re-discover knowledge from scratch. A compiled
wiki synthesizes once and stays current: concepts are deduplicated, connections are
explicit via `[[wikilinks]]`, and every claim traces to its source in YAML frontmatter.
There's no vector store — `index.md` is the routing layer.

```
knowledge/
├── raw/                  # normalized source copies (immutable)
├── wiki/
│   ├── index.md          # navigation + routing map, grouped by concept type
│   ├── concepts/         # one article per concept, linked via [[wikilinks]]
│   ├── sources/          # one summary page per source
│   └── glossary.md
├── sources/INDEX.md      # source manifest (S-IDs)
└── .wiki-state.json      # SHA256 cache → incremental recompile
```

The **host agent is the compiler** (Claude Code / Codex / Kiro) — no Ollama or API keys
needed — so the wiki builds wherever DevLoop runs. A pipeline of *ingest* (read source →
extract concepts) then *compile* (per concept → article with links) keeps it incremental:
unchanged sources are skipped via the SHA256 cache.

**Sources:** point a wiki at a whole documentation folder and run `tools/ingest.py SOURCES
--wiki <id>` — it walks **every subfolder** and extracts text, no third-party deps:
markdown/text/csv/json/yaml/html copied or de-tagged; **`.docx`/`.pptx`/`.xlsx`**,
**`.drawio`** (compressed or not), **`.vsdx` (Visio)**, and `.svg` parsed via zip+XML; `.pdf`
via `pdftotext`/`pypdf` if present. Scanned PDFs and raster images are **flagged** in
`raw/_INGEST.md` so the agent reads them with vision/OCR instead. SharePoint comes in via a
Microsoft MCP connector where the tool supports it, or via synced files / direct URLs.

### `tools/wikikit.py` — the deterministic helper

The LLM does the thinking; `wikikit.py` (pure-stdlib Python, no LLM) does the bookkeeping —
managing the registry, syncing git-backed wikis, change detection, and link-linting:

```
wikikit.py registry init             # create devloop.wikis.json (the wiki library)
wikikit.py registry list             # show wikis + last-synced commit
wikikit.py sync <id> | --all         # git clone/pull + report files changed since last build
wikikit.py scaffold --wiki <id>      # create a wiki's knowledge/ structure
wikikit.py status   --wiki <id>      # new / changed / unchanged raw sources (SHA256)
wikikit.py commit   --wiki <id>      # record source hashes after compiling
wikikit.py lint     --wiki <id>      # broken [[links]] / orphans (Obsidian-style resolution)
wikikit.py lint     --all            # validate cross-wiki [[namespace:Concept]] links
wikikit.py jira init                 # scaffold devloop.jira.json (BA + TECH projects)
wikikit.py jira validate             # validate the Jira config (routing/types/components)
```

(`scaffold/status/commit/lint` also accept a positional `DIR` instead of `--wiki` for a
standalone single wiki.)

## Jira: organization + config

The Jira Organizer gives you two things:

**1. How to organize Jira for the project.** It recommends splitting a **BA** project
(discovery: `Initiative`, `Requirement`, `Decision`, Epic) from a **TECH** project
(delivery: `Epic`, `Story`, `Task`, `Bug`, `Sub-task`) — so requirements and decisions are
tracked as first-class issues, separate from the delivery board. It derives the **Component**
list from your codebase/integration wikis, proposes a label taxonomy, and maps fields
(priority from MoSCoW, story points, epic link) and the issue hierarchy.

**2. A config that drives concrete mappings.** Once Jira is set up, capture the real
structure in `devloop.jira.json` (`wikikit.py jira init` → edit → `wikikit.py jira
validate`): projects, enabled issue types, `routing` of each artifact kind → (project,
type), components (linked to their wiki concept), labels, and the priority map. **When this
config exists, the Story Writer stops emitting generic tags and suggests a concrete per-story
mapping** — target project, issue type, component, labels, priority, epic link — all
conforming to your config, with a *Jira mapping* table in `stories.md`. `wikikit.py jira
validate` catches misroutes (a type not enabled in its project, an unknown component
project, a non-MoSCoW priority key) before you build anything in Jira.

This stays guidance + config only — no import file and no live Jira changes. (A connector
push could be added later if you want it.)

## Install

DevLoop is dependency-light — just `bash`, `python3`, and `git`. Three ways in:

**One-liner (curl bootstrap).** Clones the repo into `~/.devloop` and runs the CLI:

```bash
curl -fsSL https://raw.githubusercontent.com/aithinkers/devloop/main/install.sh | sh
# pick a host / scope:
curl -fsSL .../install.sh | sh -s -- --host claude --scope home
```

**Clone + CLI.** If you've cloned the repo:

```bash
./devloop install                         # all hosts, into the current project (./.claude, …)
./devloop install --host claude --scope home
./devloop install --dry-run               # show what would happen
./devloop list        # what's installed   ./devloop uninstall   # clean removal
./devloop doctor      # deps + build freshness + install status
```

`--host claude|kiro|codex|all` (default `all`) · `--scope project|home` (default `project`).

**Claude Code plugin marketplace.** For Claude-Code-only users:

```
/plugin marketplace add aithinkers/devloop
/plugin install devloop
```

### What lands where

- **Claude Code** — `skills/` (auto-triggering), `commands/` (slash commands), the
  `context-librarian`/`requirements-analyst` subagents, and `tools/wikikit.py`. Project scope
  → `./.claude/`, home scope → `~/.claude/`.
- **Kiro** — `steering/devloop-requirements-to-stories.md` + spec templates in
  `specs/_template/`. Project scope → `./.kiro/`, home scope → `~/.kiro/`. Reference it with
  `#devloop-requirements-to-stories`.
- **Codex** — `ba-*.md` prompts (each becomes a `/` command) into `$CODEX_HOME/prompts`
  (Codex only reads prompts from there); project scope also drops `AGENTS.md` into the repo.

## Usage

0. `/spec-context` — define your wikis in `devloop.wikis.json` (`wikikit.py registry init`),
   point them at local folders / git repos / URLs, `sync`, and it compiles the wiki
   library. (Skip if you have no source material.)
1. `/spec-requirements <one-line feature idea>` — it navigates the wikis, only asks about
   gaps; answer with A/B/C and approve the draft.
2. `/spec-stories` — get epics, user stories, Gherkin acceptance criteria, and component tags.
3. `/spec-review` — independent INVEST / Definition-of-Ready quality pass.
4. `/spec-jira` — a Jira organization plan: epics, components (from the wikis), labels, fields.

To **refresh** later: `wikikit.py sync --all`, recompile the wikis it reports as changed,
then re-run from step 1.

### Building one wiki at a time

Every `wikikit.py` op is per-wiki, so you can build/refresh wikis individually:

```bash
wikikit.py sync integrations           # refresh just this wiki's source
wikikit.py scaffold --wiki integrations
wikikit.py status   --wiki integrations    # what changed in this wiki only
# ... run /spec-context (the agent compiles concept articles for this wiki) ...
wikikit.py lint     --wiki integrations
wikikit.py commit   --wiki integrations
```

`lint --all` is the only cross-wiki step. The Context Librarian compiles each wiki with its
own `kind` profile, so wikis are fully independent.

## Testing

**Automated smoke test** (no LLM, no network — proves the single-wiki plumbing):

```bash
bash test/smoke_test.sh
```

It covers, end to end: registry + single-wiki scaffold, change-detection, the compile step,
lint and the incremental cache, a **git-backed** wiki (clone + upstream-change detection,
using a throwaway local repo — no network), **cross-wiki** `[[namespace:Concept]]` lint,
**Jira config** validation (clean config passes, a misrouted one is caught), a **build
freshness** check (the generated platform folders match `core/`), **cross-host install**
(both helper tools land in every host's `tools/` and are removed on uninstall), the
`ingest.py --wiki` registry-resolved path, and a **Codex self-containment** invariant
(every `shared/<file>` a role body cites is inlined into the prompt).
Expect `22 passed, 0 failed` (one stage self-skips if `git` isn't installed).

**Manual single-wiki test in your tool.** Install (`./install.sh claude`), then in a scratch
project: `wikikit.py registry init`, edit `devloop.wikis.json` down to one local wiki
pointing at `examples/integrations-src/` (or your own docs), copy those files into
`knowledge/raw/`, and run `/spec-context` — the agent should produce `knowledge/wiki/concepts/`
articles (SSO, Email, SFTP) with `[[wikilinks]]` and an `index.md`. Then `/spec-requirements`
to confirm it reads the wiki and only asks about gaps. See `examples/README.md` for the
exact steps.

**Git-backed wiki test.** Point a wiki's `source` at any git repo URL and run
`wikikit.py sync <id>` — it clones into `.devloop/wikis/<id>`, and a second `sync` after an
upstream commit reports the changed files.

## Source of truth & build

To avoid maintaining the same content in three places, DevLoop separates **common content**
from **tool-specific arrangement**, and a generic engine arranges one into the other:

- **Common source (edit these):** `core/roles.json` (neutral role definitions — id, title,
  body, command, description, summary), `core/*.md` (role bodies), `core/shared/*`
  (templates/guides/examples), and `tools/wikikit.py` (one copy).
- **Per-tool adapter (edit these):** each tool folder owns an `adapter.json` describing
  *only* its arrangement — which shared files a Claude skill bundles, which files Codex
  inlines into each prompt, the Kiro template-name mapping. `kind` selects the builder.
- **Authored, tool-specific (edit these):** `claude-code/.claude-plugin/plugin.json`,
  `.claude-plugin/marketplace.json`, `kiro/steering/*`, `kiro/README.md`, `codex/AGENTS.md`.
- **Generated (never edit by hand):** `claude-code/skills|commands|agents`, `codex/prompts`,
  `kiro/specs/_template`, and the per-tool copies of `wikikit.py`.

```bash
./build.sh          # read core/roles.json + each <tool>/adapter.json → generate the packages
./build.sh --check  # fail if the generated folders are stale (used by the smoke test)
```

`build/build.py` is a generic engine: it loads the common source, discovers every
`<tool>/adapter.json`, and dispatches to a small builder per `kind`. So a content change is
made **once** in `core/`; tool-specific arrangement lives **with the tool**; and
**adding a new tool is just a new folder with an `adapter.json`** (plus a ~15-line builder
if its packaging shape is genuinely new). The generated folders can't drift — the smoke test
fails if they do. Codex prompts come out self-contained (templates inlined, since Codex reads
one file per command); Claude skills bundle their own `shared/`; Kiro uses spec templates.

```
devloop/
├── build.sh / build/build.py   # generic engine (common + adapters → packages) + --check
├── install.sh
├── core/
│   ├── roles.json              # ← SOURCE: neutral role definitions (common)
│   ├── 0X-*.md                 # ← SOURCE: role bodies
│   └── shared/                 # ← SOURCE: templates, guides, example configs
├── tools/wikikit.py            # ← SOURCE: deterministic helper (registry/sync/jira/lint)
├── examples/                   # sample sources for trying a single wiki
├── test/smoke_test.sh          # 18-check smoke test (incl. build freshness)
├── claude-code/  adapter.json + .claude-plugin/plugin.json (authored) → skills/commands/agents (generated)
├── kiro/         adapter.json + steering/ + README (authored)         → specs/_template/ (generated)
├── codex/        adapter.json + AGENTS.md (authored)                  → prompts/ (generated)
└── .claude-plugin/marketplace.json
```

## License

MIT — see [LICENSE](LICENSE). Contributions welcome; see [CONTRIBUTING.md](CONTRIBUTING.md)
and [CHANGELOG.md](CHANGELOG.md).
