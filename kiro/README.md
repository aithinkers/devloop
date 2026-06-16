# DevLoop for Kiro

Targets **Kiro 0.9+** (Agent Skills, custom subagents, auto-steering, hooks; validated on Kiro
0.11, mid-2026 — check Kiro's docs if the layout has since changed). `devloop
install --host kiro` lands everything under `.kiro/` (project scope) or `~/.kiro/` (home):

- **`skills/<role>/SKILL.md`** — one Agent Skill per role (Context Librarian, Requirements
  Analyst, Story Writer, Story Reviewer, Jira Organizer), each bundling its `shared/`
  templates and `scripts/`. Kiro loads only the name + description until a skill is relevant,
  then pulls in the full method — so the five roles **auto-trigger** by what you're doing. To
  invoke one explicitly, mention `$context-librarian` (etc.) or pick it from the `/skills` menu.
  (agentskills.io format — the same packages DevLoop ships for Claude Code.)
- **`agents/*.md`** — custom subagents for the two isolated-context roles (`context-librarian`,
  `requirements-analyst`); invoke with `/context-librarian …`, or let Kiro auto-select by
  description. Each is a thin pointer to its skill (it never restates the method).
- **`steering/devloop.md`** — a lean `inclusion: auto` orchestrator that only **sequences** the
  five gated phases and points at each skill. It carries no role bodies, so nothing
  duplicates the skills. (Reference it explicitly with `#devloop` if you ever want to.)
- **`hooks/*.kiro.hook`** — manual Agent Hooks for the deterministic steps: **DevLoop: lint
  wikis** (`wikikit.py lint --all`) and **DevLoop: sync wikis** (`wikikit.py sync --all`). Run
  them from the Agent Hooks panel.
- **`tools/`** — `wikikit.py` (registry/sync/scaffold/status/commit/lint) and `ingest.py`
  (multi-format folder ingest), made executable on install.
- **`settings/mcp.json`** — a disabled, secret-free **example** MCP config for pulling
  SharePoint into the Context Librarian (see below). Installed **only if you don't already have
  one** — it never overwrites your real MCP config, and is left untouched on uninstall.

## SharePoint (and other MCP sources)

The Context Librarian can read SharePoint via an MCP server (Kiro's native MCP mechanism),
configured in `.kiro/settings/mcp.json` (workspace) or `~/.kiro/settings/mcp.json` (global).
There is no single official SharePoint MCP server, so the shipped example is **disabled**;
point it at the Microsoft Graph / SharePoint MCP server you use, pass the token via an env var
(never hardcode secrets), and flip `disabled` to `false`:

```json
{
  "mcpServers": {
    "sharepoint": {
      "command": "npx",
      "args": ["-y", "<your-sharepoint-or-microsoft-graph-mcp-server>"],
      "env": { "SHAREPOINT_TOKEN": "${SHAREPOINT_TOKEN}" },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

Once a server is connected, ingest its content into a wiki's `raw/` (or read it directly) and
compile as usual. If you have no MCP server, fall back to synced files / exported docs and
`ingest.py`.

## How it relates to Kiro's native specs

Kiro's feature specs generate `requirements.md` in **EARS** (`WHEN … THE SYSTEM SHALL …`),
then `design.md` and `tasks.md`. DevLoop's `requirements.md` is intentionally richer
(personas, numbered FR/NFR with source traceability, scope, risks, acceptance) and its
`stories.md` adds INVEST stories + Gherkin. Use DevLoop for **discovery** (idea → grounded
requirements → reviewed backlog); its output **feeds** a Kiro feature spec — it doesn't
replace it.

## Single source of truth

Everything here is **generated** from `core/` by `build.py` (the skills are byte-for-byte the
same as the Claude packages). Don't hand-edit `skills/`, `agents/`, `steering/`, `hooks/`, or
`tools/` — change `core/` (or `kiro/adapter.json`) and run `./devloop build`.
