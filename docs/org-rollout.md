# Rolling DevLoop out across an org

DevLoop shines when several teams share grounded knowledge and a consistent requirements →
backlog pipeline. This is the playbook.

## 1. Build shared wikis once
Different knowledge lives in different wikis, several shared across projects in their own git
repos (so they're versioned and reusable):

| kind | source | extracts |
|---|---|---|
| `project` | the repo you're in (local) | as-is processes, decisions, product features, glossary |
| `integrations` | shared git repo | SSO, APIs, Email, FTP/SFTP, webhooks |
| `devops` | shared git repo | pipelines, environments, deploy/release, observability |
| `codebase` | a code git repo | services, APIs/endpoints, data models, config, deps |

Compile `devops`/`integrations`/`codebase` **once** in their own repos (commit the compiled
`knowledge/wiki/`), then any project references them in `devloop.wikis.json` with
`contains: "wiki"`; `wikikit.py sync --all` clones them into `.devloop/wikis/`. Teams then link
across with `[[integrations:SSO]]`, `[[devops:Release Pipeline]]`, `[[app-codebase:AuthService]]`
— using distilled knowledge instead of re-reading whole source trees. Ready-to-edit registry +
recipes: [../examples/devloop.wikis.shared.example.json](../examples/devloop.wikis.shared.example.json)
and [../examples/README.md](../examples/README.md).

## 2. Pick a lane per team
- Product/agile teams → the [Agile lane](agile-lane.md).
- Regulated / consulting / RFP teams → the [BRD lane](brd-lane.md) (formal sign-off + `OBJ→BR→FR→US`).

Both produce the same downstream artifacts, so a mixed org still gets one consistent backlog shape.

## 3. Organize Jira once
The Jira Organizer recommends splitting a **BA** project (`Initiative`, `Requirement`, `Decision`)
from a **TECH** delivery project (`Epic`, `Story`, `Task`, `Bug`), derives **Components** from the
`codebase`/`integrations` wikis, and proposes labels + field mappings. Capture the real setup once
in `devloop.jira.json` (`wikikit.py jira init` → edit → `jira validate`); after that the Story
Writer emits a concrete per-story mapping that conforms to it. Guidance + config only — DevLoop
never writes to Jira.

## 4. Keep it fresh
`wikikit.py sync --all` (git pull + report changed sources) → recompile changed wikis →
`lint --all`. In any project, `devloop status` shows registry/source/lint/Jira readiness and which
artifacts exist. See [architecture.md](architecture.md) for how the one source maps to each host.
