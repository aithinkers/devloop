# Backlog: <Feature name>

_Source: requirements.md (approved <date>)_

## Backlog overview
| Story | Title | Epic | Priority | Size | Covers | Component(s) | Labels |
|---|---|---|---|---|---|---|---|
| US-1 | | EP-1 | Must | M | FR-1, FR-3 | SSO | security |

---

## EP-1 · <Epic name>
**Goal:** <one line>  ·  **Covers:** FR-1, FR-2

### US-1 · <Story title>
**As a** <persona>, **I want** <capability>, **so that** <benefit>.
- **Epic:** EP-1   **Priority:** Must   **Size:** M   **Covers:** FR-1, FR-3

**Acceptance criteria**
```gherkin
Scenario: <happy path>
  Given <context>
  When <action>
  Then <expected outcome>

Scenario: <edge / error case>
  Given <context>
  When <action>
  Then <expected outcome>
```

---

## Traceability matrix
| Requirement | Covered by | Status |
|---|---|---|
| FR-1 | US-1 | ✅ |
| NFR-1 | US-4 | ✅ |
| FR-9 | — | ⚠️ GAP |

## Jira mapping
_Only when `devloop.jira.json` is present — values must conform to the config._

| Story | Project | Issue type | Epic (link) | Component(s) | Labels | Priority | Points |
|---|---|---|---|---|---|---|---|
| US-1 | TECH | Story | EP-1 | SSO | security | Highest | 3 |
| US-7 | TECH | Task | EP-2 | auth-service | backend | High | 2 |

_Flag any component a story touches that is missing from the config so the Jira Organizer
can add it._
