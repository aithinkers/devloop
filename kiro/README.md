# DevLoop for Kiro

DevLoop ships to Kiro as **Agent Skills** — following the same skills-only model gstack uses for
Kiro (skills are the surface Kiro reliably exposes; we don't ship custom subagents or hooks).
`devloop install --host kiro` lands (project scope `.kiro/`, home scope `~/.kiro/`):

- **`skills/devloop/<role>/SKILL.md`** — one Agent Skill per role (Context Librarian, the
  optional Business Analyst (BRD), Requirements Analyst, Story Writer, Story Reviewer, Jira
  Organizer), each bundling its `shared/` templates and `scripts/`, namespaced under a `devloop/`
  folder. Kiro loads only the name + description until a skill is relevant, then pulls in the full
  method — so the roles **auto-trigger** by what you're doing. To invoke one explicitly, mention
  `$context-librarian` (etc.) or pick it from the **`/skills`** menu. (agentskills.io format — the
  same packages DevLoop ships for Claude and Codex.)
- **`steering/devloop.md`** — a lean `inclusion: auto` orchestrator that only **sequences** the
  gated phases (incl. the optional BRD) and points at each skill. It carries no role bodies, so
  nothing duplicates the skills. (Reference it explicitly with `#devloop` if you ever want to.)
- **`tools/`** — `wikikit.py` (registry/sync/scaffold/status/commit/lint) and `ingest.py`
  (multi-format folder ingest), made executable on install. (They're also bundled inside the
  `context-librarian` skill's `scripts/`.)

> **Note:** the roles don't appear as `/` slash commands in Kiro — skills surface via
> auto-trigger, the **`/skills`** picker, or `$<role>`. That's expected.

## SharePoint (and other MCP sources)

The Context Librarian can read SharePoint via an MCP server, configured in Kiro's own
`.kiro/settings/mcp.json` (workspace) or `~/.kiro/settings/mcp.json` (global). DevLoop doesn't
ship an MCP config (that file is user-owned). There's no single official SharePoint MCP server —
point one at the Microsoft Graph / SharePoint server you use and pass the token via an env var
(never hardcode secrets):

```json
{
  "mcpServers": {
    "sharepoint": {
      "command": "npx",
      "args": ["-y", "<your-sharepoint-or-microsoft-graph-mcp-server>"],
      "env": { "SHAREPOINT_TOKEN": "${SHAREPOINT_TOKEN}" }
    }
  }
}
```

If you have no MCP server, fall back to synced / exported files and `ingest.py`.

## How it relates to Kiro's native specs

Kiro's feature specs generate `requirements.md` in **EARS** (`WHEN … THE SYSTEM SHALL …`),
then `design.md` and `tasks.md`. DevLoop's `requirements.md` is intentionally richer
(personas, numbered FR/NFR with source traceability, scope, risks, acceptance) and its
`stories.md` adds INVEST stories + Gherkin. Use DevLoop for **discovery** (idea → grounded
requirements → reviewed backlog); its output **feeds** a Kiro feature spec — it doesn't
replace it.

## Single source of truth

The skills are **generated** from `core/` by `build.py` (byte-for-byte the same packages Claude
and Codex get); the only Kiro-generated wrapper is `steering/devloop.md`. Don't hand-edit them —
change `core/` (or `kiro/adapter.json`) and run `./devloop build`.
