# Jira organization guide

How to organize Jira for the project, and how DevLoop artifacts map onto it. Guidance only
— no import file and no live changes.

## Projects & issue types — split discovery from delivery
Use two Jira projects so analysis artifacts don't clutter the delivery board:

| Project | Purpose | Issue types |
|---|---|---|
| **BA** (Business Analysis) | discovery & analysis | **Initiative**, **Requirement**, **Decision**, Epic |
| **TECH** (Engineering) | implementation | **Epic**, **Story**, **Task**, **Bug**, **Sub-task** |

- **Requirement** (BA) — one issue per FR/NFR, traced from `requirements.md`. Lets the
  business sign off and track coverage independently of delivery.
- **Decision** (BA) — one issue per decision mined into the wikis (an ADR-style record).
- **Epic / Story / Task / Bug / Sub-task** (TECH) — the delivery backlog from `stories.md`.
- Link delivery items back to their BA Requirement(s) with an issue link ("implements").

Smaller teams can collapse this into a single project with the same issue types; keep
Requirement and Decision as distinct types so traceability survives.

## Hierarchy: map DevLoop artifacts to Jira issue types
```
Initiative (optional, big multi-epic bet)
  └─ Epic            ← DevLoop EP-n (a coherent capability / journey)
       └─ Story      ← DevLoop US-n (user value, "as a … I want …")
       └─ Task       ← enabling work with no direct user story (e.g. infra)
       └─ Bug
            └─ Sub-task  ← checklist breakdown of a single story/task
```
Rules of thumb:
- An **Epic** should deliver a releasable slice of value, not a team or a quarter. If an
  epic never "finishes", it's really a Component or a label — fix it.
- A **Story** is one INVEST-sized increment; if it needs more than a sprint, split it.
- Use **Sub-tasks** only for intra-story breakdown, never to model dependencies.

## Components — derive them from the wikis (don't invent ad hoc)
Components represent the parts of the system a piece of work touches. Build the component
list from the **codebase** and **integrations** wikis:
- each `service`/`module` in the codebase wiki → a Component (e.g. `auth-service`, `web`).
- each `integration` in the integrations wiki → a Component (e.g. `SSO`, `Email`, `SFTP`).
Then tag every Story/Task with the Component(s) it touches, taken from the concept articles
that story traces to. Keep components stable and few; one owner per component.

## Labels — cross-cutting, not structural
Use labels for themes that cut across epics/components: `security`, `tech-debt`,
`accessibility`, `spike`, `frontend`/`backend`, release-train tags. Don't duplicate
Components as labels, and don't encode hierarchy in labels.

## Other fields
- **Fix Version / Release** — the release a story is targeted to (from roadmap/priority).
- **Sprint** — assignment at planning time, not at authoring time.
- **Priority** — map MoSCoW: Must→Highest/High, Should→Medium, Could→Low.
- **Story points** — relative estimate (Fibonacci); set the team baseline first.
- **Epic Link** — every story links to its parent epic (EP-n).

## Anti-patterns to avoid
- Epics named after teams, sprints, or "miscellaneous".
- Components used as a status or a label.
- Deeply nested sub-tasks used to fake dependencies (use issue links instead).
- One giant epic that accretes forever.

## Capture the real setup in `devloop.jira.json`
The recommendation above is a starting point. Once Jira is actually configured, record the
real structure in a config file `devloop.jira.json` (seed it with `wikikit.py jira init`,
then edit; validate with `wikikit.py jira validate`). It captures:
- `projects` — each project's key, name, purpose, and its `issue_types`.
- `routing` — which (project, issue type) each DevLoop artifact kind maps to
  (`requirement`, `decision`, `epic`, `story`, `task`, `bug`, `subtask`, `initiative`).
- `components` — the component list (ideally each linked to its `wiki` concept) and owners.
- `labels` — the allowed cross-cutting label set.
- `priority_map` — MoSCoW → your Jira priority names.
- `custom_fields` — e.g. Story Points, Epic Link, Acceptance Criteria.

When this file exists, the **Story Writer** stops emitting generic guidance and instead
suggests a concrete mapping for each story using the configured projects, types,
components, labels, and priorities — so the backlog conforms to your actual Jira.
