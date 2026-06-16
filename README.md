# DevLoop

DevLoop gives your coding agent a disciplined **business-analyst workflow**: it turns a vague
feature idea into a review-ready backlog — requirements, user stories, a quality review, and a
Jira plan — all **grounded in your company's existing knowledge**.

```
Context Librarian  →  Requirements Analyst  →  Story Writer  →  Story Reviewer  →  Jira Organizer
(compile a wiki        (grounded interview)     (epics+stories)   (INVEST/DoR)       (epics/components/labels)
 library)              requirements.md          stories.md        story-review.md    jira-plan.md
```

It installs into **Claude Code**, **Kiro**, and **Codex** from one source — as auto-triggering
Agent Skills, so you don't invoke anything special; the right role activates when you need it.
Inspired by Garry Tan's [gstack](https://github.com/) (role-based skills) and obra's
[Superpowers](https://github.com/obra/superpowers) (gate each phase on the last).

> **Status.** DevLoop covers the *front* of the loop today — grounding → requirements →
> stories → Jira plan. The back half (agents that pick up ready stories, implement, open/review
> PRs, merge, sync Jira) is the planned next phase. That's the "loop" the name points at.

## Quickstart

Dependency-light — just `bash`, `python3`, and `git`. The installer is a shell script, so it
runs on **macOS/Linux** (and **Windows via WSL or Git Bash**); the generated skills themselves
are host-native and work wherever the host runs.

```bash
# One-liner (clones into ~/.devloop and runs the installer):
curl -fsSL https://raw.githubusercontent.com/aithinkers/devloop/main/install.sh | sh

# …or from a clone:
./devloop install                       # all hosts, into ./ (project scope)
./devloop install --host claude --scope home
./devloop list   ./devloop uninstall   ./devloop doctor
```

`--host claude|kiro|codex|all` · `--scope project|home`. **Claude Code** users can also install
from the plugin marketplace:

```
/plugin marketplace add aithinkers/devloop
/plugin install devloop
```

Then just describe a feature and let the chain auto-trigger. To call a phase directly, the
surface differs by host: **Claude Code** has `/spec-context`, `/spec-requirements`, … commands;
**Kiro** auto-triggers the role skills (invoke one with `$context-librarian` or via `/skills`;
the two subagents also run as `/context-librarian` & `/requirements-analyst`); **Codex** invokes
the role skill (`$context-librarian` or `/skills`).

## How it works

When you ask to build something, DevLoop *doesn't* jump to stories. It steps back through a chain
of **gated** roles — each one finishes (and you sign off) before the next begins:

1. **Context Librarian** — asks where your knowledge lives (docs, meeting minutes, SharePoint,
   wikis, repos, URLs) and **compiles it into a library of LLM-Wikis** you can trust. Run this
   first when you have source material.
1b. **Business Analyst (BRD)** *(optional)* — for waterfall/regulated/SI teams that need a formal
   **Business Requirements Document**: business objectives + metrics, scope, stakeholders,
   current/future state, and numbered business requirements (`BR-n`) with sign-off → `brd.md`.
   Agile teams skip this and start at the Requirements Analyst. The later phases trace
   `BR → FR → US` when a BRD exists.
2. **Requirements Analyst** — reads the wikis (and the BRD if present), then interviews you
   Socratically, **one question at a time**, only about the gaps. Produces `requirements.md`
   (numbered FR/NFR, each traced to its source — and to a `BR` when a BRD exists).
3. **Story Writer** — turns approved requirements into epics + INVEST user stories with Gherkin
   acceptance criteria and a traceability matrix → `stories.md`.
4. **Story Reviewer** — an independent pass for INVEST, Definition of Ready, coverage, and AC
   quality → `story-review.md`.
5. **Jira Organizer** — recommends how to organize Jira and writes a `jira-plan.md`. Guidance +
   config only — no live Jira changes.

Because the skills auto-trigger, the agent picks the right role for what you're doing.

## Grounded in your knowledge (a library of LLM-Wikis)

Requirements are only as good as what they're based on. So before eliciting anything, the
Context Librarian **compiles** your scattered sources into interlinked knowledge wikis (Andrej
Karpathy's [LLM Wiki](https://karpathy.ai/llmwiki) pattern) — concepts are de-duplicated, linked
with `[[wikilinks]]`, and every claim traces to its source. There's no vector store; an
`index.md` is the routing layer.

Different knowledge lives in different wikis, several shared across projects in their own git
repos. A registry (`devloop.wikis.json`) lists them, and built-in `kind` profiles shape what each
extracts:

| kind | source | extracts |
|---|---|---|
| `project` | this repo (local) | as-is processes, decisions, product features, glossary |
| `integrations` | shared git repo | SSO, APIs, Email, FTP/SFTP, webhooks |
| `devops` | shared git repo | pipelines, environments, deploy/release, observability |
| `codebase` | a code git repo | services, APIs/endpoints, data models, config, deps |

Concepts link within a wiki via `[[Concept]]` and **across** wikis via a namespace
(`[[integrations:SSO]]`). Point a wiki at a folder of mixed docs and `ingest.py` walks every
subfolder, extracting text from markdown, `.docx/.pptx/.xlsx`, `.drawio`, `.vsdx`, `.svg`, and
PDFs (scanned files/images are flagged for the agent to read with vision). SharePoint comes in
via an MCP connector (see the per-host notes) or synced files.

**Reuse shared wikis across projects.** Build company-wide `devops`/`integrations` wikis — or a
**`codebase` wiki that distills an existing code repo** (services, APIs, data models) — **once**
in their own git repos, then reference them from any project: list them in `devloop.wikis.json`
with `contains: "wiki"` (already compiled) and `wikikit.py sync --all` clones them into
`.devloop/wikis/`. `/spec-requirements` pulls them in automatically and you link across with
`[[devops:Release Pipeline]]` or `[[app-codebase:AuthService]]` — so a project uses the distilled
knowledge instead of reading the whole source tree. Ready-to-edit registry + recipe:
[examples/devloop.wikis.shared.example.json](examples/devloop.wikis.shared.example.json) and
[examples/README.md](examples/README.md).

## Jira: a plan, plus optional config

The Jira Organizer recommends splitting a **BA** project (`Initiative`, `Requirement`,
`Decision`) from a **TECH** delivery project (`Epic`, `Story`, `Task`, `Bug`), derives
**Components** from your wikis, and proposes labels + field mappings. If you capture your real
setup in `devloop.jira.json`, the Story Writer then suggests a **concrete per-story mapping**
(project, type, component, labels, priority) that conforms to it — and `wikikit.py jira validate`
catches misroutes before you build anything. Guidance + config only; no import file.

## The helpers

The LLM does the thinking; two pure-stdlib scripts (installed into each host, and run by the
agent for you) do the deterministic bookkeeping:

- **`wikikit.py`** — manage the wiki registry, `sync` git-backed wikis, detect changed sources
  (SHA256), lint `[[links]]` (incl. cross-wiki), and scaffold/validate the Jira config.
- **`ingest.py`** — recursive, multi-format folder ingest into a wiki's `raw/` (no third-party deps).

## Per-host notes

All three hosts get the **same Agent Skills** (the `skills/` library). Each adds its own idioms.
Host-specific details below reflect each tool **as of mid-2026** — these are fast-moving products,
so check the host's current docs if something has changed. Validated live on **Kiro 0.11**; the
Claude marketplace install and the Codex layout are built to the documented conventions.

- **Claude Code** — skills + thin `/spec-*` commands + `context-librarian`/`requirements-analyst`
  subagents. Installs to `./.claude/` or `~/.claude/`.
- **Kiro** (0.9+) — skills + subagents + a lean `inclusion: auto` steering orchestrator + manual
  lint/sync **hooks** + a disabled SharePoint **MCP** example (`.kiro/settings/mcp.json`, seeded
  only if absent). See [kiro/README.md](kiro/README.md).
- **Codex** — skills into `.agents/skills/` + `AGENTS.md` as the gated-chain orchestrator (Codex
  custom prompts were deprecated in favor of skills, per OpenAI's docs). Wire SharePoint via
  `config.toml` `[mcp_servers]`; see [codex/AGENTS.md](codex/AGENTS.md).

## Testing

```bash
bash test/smoke_test.sh    # 53 checks, no LLM, no network
```

End to end: registry + scaffold, change-detection, the compile step, lint + incremental cache, a
git-backed wiki, cross-wiki lint, Jira validation, build freshness, single-source skills, and
all-host install/uninstall. Expect `53 passed, 0 failed`.

## How it's built

All three hosts read the same `SKILL.md` Agent Skill format (the [agentskills.io](https://agentskills.io)
shape), so DevLoop keeps **one** `skills/` library (generated from `core/`) and layers only thin
host-specific wrappers on top — Claude's commands/subagents, Kiro's steering/hooks/MCP, Codex's
`AGENTS.md`. A content change is made once; `./devloop build --check` fails if anything drifts.
Details for contributors: [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE). Contributions welcome ([CONTRIBUTING.md](CONTRIBUTING.md),
[CHANGELOG.md](CHANGELOG.md)).
