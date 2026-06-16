# DevLoop — business-analysis workflow for this repo

When asked to define a feature, gather requirements, or create stories/tickets, follow this
**gated chain**. Each phase gates the next; do not skip ahead. Each phase has an **Agent Skill**
(installed under `.agents/skills/`) that carries the full method — adopt it (Codex auto-selects
by description, or invoke `$<skill>` / pick it from `/skills`). This file only sequences them.

0. **`context-librarian` skill** — Act as a Context Librarian. Ask, one category at a time,
   where company knowledge lives (local files/folders, wikis & URLs, SharePoint, paste-in
   text). Compile sources into an interlinked LLM-Wiki under `knowledge/` (concept articles
   with [[wikilinks]] + source-traceable frontmatter + an `index.md` routing layer). Run FIRST
   when source material exists.
0b. **`business-analyst` skill** *(optional — waterfall/regulated/SI teams)* — produce a
   Business Requirements Document (`brd.md`): business objectives + metrics (`OBJ-n`), scope,
   stakeholders, current/future state, and numbered business requirements (`BR-n`) in business
   language (no "system shall"), with sign-off. Agile teams skip this and go straight to
   requirements. When a BRD exists, later phases trace `BR → FR → US`.
1. **`requirements-analyst` skill** — Read `knowledge/wiki/index.md` if present (and `brd.md` if
   it exists — tag each FR/NFR with the `BR-n` it serves), open relevant concept articles, and
   only ask about gaps. Interview Socratically, ONE question at a time with A/B/C options, until
   the checklist is covered. Produce `requirements.md` (numbered FR/NFR) with explicit sign-off.
   No solutioning, no stories yet.
2. **`story-writer` skill** — Convert approved `requirements.md` into epics and INVEST user
   stories with Gherkin acceptance criteria and a traceability matrix. Produce `stories.md`.
3. **`story-reviewer` skill** — Independently review against INVEST, Definition of Ready,
   acceptance-criteria quality, and requirement coverage. Produce `story-review.md`.
4. **`jira-organizer` skill** — Turn `stories.md` into `jira-plan.md`: Initiative→Epic→
   Story/Task hierarchy, Components from the codebase/integration wikis, label taxonomy, field
   mappings. Guidance only; no import file.

## Helpers

The installer places `wikikit.py` (registry/sync/scaffold/status/commit/lint) and `ingest.py`
(multi-format folder ingest) in `$CODEX_HOME/tools` (default `~/.codex/tools/`); each skill
also bundles them under its `scripts/`. Run as `python3 ~/.codex/tools/wikikit.py …` and
`python3 ~/.codex/tools/ingest.py <folder> --wiki <id>`.

## SharePoint / MCP sources

To let the Context Librarian read SharePoint (or other MCP sources), add an MCP server to your
Codex `config.toml` (`~/.codex/config.toml`, or `.codex/config.toml` for a trusted project) —
there is no single official SharePoint server, so point it at the Microsoft Graph / SharePoint
MCP server you use and pass secrets via env, never inline:

```toml
[mcp_servers.sharepoint]
command = "npx"
args = ["-y", "<your-sharepoint-or-microsoft-graph-mcp-server>"]
env = { SHAREPOINT_TOKEN = "${SHAREPOINT_TOKEN}" }
```

If you have no MCP server, fall back to synced/exported files and `ingest.py`. DevLoop's
`requirements.md` is intentionally richer than a plain spec (personas, FR/NFR with source
traceability, scope, risks).
