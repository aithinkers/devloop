# Jira organization plan: Partner file-exchange modernization

_From brd.md / requirements.md / stories.md · guidance + config only (no live Jira changes)._

## 1. Project split
| Project | Purpose | Issue types |
|---|---|---|
| **BA** (Business Analysis) | discovery & sign-off | **Initiative**, **Requirement**, **Decision** |
| **TECH** (Delivery) | implementation | **Epic**, **Story**, **Task**, **Bug**, **Sub-task** |

Keep requirements/decisions as first-class BA issues so the business can sign off and track
coverage independently of the delivery board; link delivery items back with an "implements" link.

## 2. Components (derived from the wikis)
From the `integrations` wiki concepts the feature touches: **SSO**, **SFTP**, **Email**. (If a
`codebase` wiki existed, service/module concepts would add components too.)

## 3. Hierarchy & field mapping
```
Initiative  ← OBJ-1/2/3 (BRD objectives)
  └─ Epic            ← EP-1, EP-2
       └─ Story/Task ← US-1 … US-5
  Requirement (BA)   ← FR-/NFR-, linked up to its BR-/Initiative
```
- **Priority** ← MoSCoW: Must→Highest, Should→High, Could→Medium, Won't→Lowest.
- **Story points** ← size (S=2, M=3, L=5). **Epic link** ← EP-n. **Labels** ← story labels.

## 4. BA project — Initiatives & Requirements
| BA issue | Type | From | Title |
|---|---|---|---|
| INIT-1 | Initiative | OBJ-1 | Cut partner onboarding time to < 1 hour |
| INIT-2 | Initiative | OBJ-2 | Eliminate insecure credential sharing |
| REQ-1 | Requirement | FR-1 (BR-2) | SSO-authenticated partner access |
| REQ-3 | Requirement | FR-3 (BR-3) | Key-based auth; no emailed secrets |
| … | Requirement | FR-2/4/5, NFR-1/2/3 | (one per FR/NFR, linked to its BR) |

## 5. Per-story mapping (TECH project)
_Conforms to `devloop.jira.json`; emitted because a Jira config is present._

| Story | Project | Issue type | Epic | Component(s) | Labels | Priority | Points |
|---|---|---|---|---|---|---|---|
| US-1 | TECH | Story | EP-1 | SSO | security | Highest | 2 |
| US-2 | TECH | Story | EP-1 | SFTP | onboarding | Highest | 3 |
| US-3 | TECH | Story | EP-1 | SFTP | security | Highest | 3 |
| US-4 | TECH | Story | EP-2 | Email | notifications | Highest | 2 |
| US-5 | TECH | Story | EP-2 | SFTP | audit | High | 2 |

## 6. Decisions to record (BA)
- **DEC-1:** key-based SFTP auth only (no passwords) — from BR-3 / Security sign-off.

> Guidance + config only. To get issues into Jira, hand this table to your import tool or paste
> it into the tracker — DevLoop does not write to Jira.
