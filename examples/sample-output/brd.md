# BRD: Partner file-exchange modernization

| | |
|---|---|
| **Author** | Business Analyst (DevLoop) |
| **Status** | Approved |
| **Last updated** | 2026-06-16 |
| **Sponsor** | VP, Partner Operations |
| **Stakeholders** | Partner Operations, Integration Ops, Security, Partner Success |

## 1. Executive summary
Onboarding a partner for file exchange is a manual, multi-day task that ships credentials over
email and ties up Integration Ops. We will let partners **self-serve** their file exchange,
authenticated through our existing identity provider, with no credentials sent by email — cutting
onboarding from days to minutes and removing a recurring security risk.

## 2. Business objectives & success metrics
| ID | Objective | Metric | Baseline → Target |
|---|---|---|---|
| OBJ-1 | Cut partner onboarding time | median time from request to first file exchanged | ~3 days → < 1 hour |
| OBJ-2 | Eliminate insecure credential sharing | # credentials sent by email | ~all → 0 |
| OBJ-3 | Reduce Ops onboarding toil | onboarding tickets handled by Ops / month | baseline → ↓ 80% |

## 3. Background & problem statement
Partners exchange files with us over SFTP. Today Integration Ops provisions each account by hand,
emails a username/password and a PDF of the directory layout [S3]. It is slow, the emailed
credentials are a standing security exposure [S1], and the toil scales with partner growth. Doing
nothing keeps onboarding a multi-day ticket and an audit finding waiting to happen.

## 4. Stakeholders
| Stakeholder | Role / interest | Involvement (RACI) |
|---|---|---|
| VP, Partner Operations | Sponsor; owns onboarding SLA | Accountable |
| Integration Ops | Runs the SFTP platform | Responsible |
| Security | Owns credential & access policy | Consulted |
| Partner Success | Partner relationship | Consulted |
| Partner Admin | External technical contact | Informed |

## 5. Current state (as-is)
Ops manually creates an SFTP account, sets directory permissions per the documented convention
[[integrations:SFTP]] [S3], and emails the partner a password plus layout PDF. Authentication is
not tied to our identity provider [[integrations:SSO]] [S1], and there is no audit trail of who
provisioned what.

## 6. Future state (to-be)
A partner admin signs in with their existing company identity, requests an exchange space, and is
exchanging files within the hour — no ticket, no emailed secret, every action recorded. Ops moves
from doing onboarding to overseeing it. _(Process flow: see attached `to-be-onboarding.drawio` —
not embedded; this artifact is narrative + tables.)_

## 7. Scope
- **In scope:** partner self-service SFTP onboarding; SSO-authenticated access; key-based auth;
  status notifications; audit; Ops ability to revoke.
- **Out of scope (this initiative):** file content validation/transformation; partner analytics
  dashboard; non-SFTP transports (AS2, API upload).

## 8. Business requirements
| ID | Business requirement | Priority (MoSCoW) | Objective | Source refs |
|---|---|---|---|---|
| BR-1 | Partners can set up a file exchange themselves, without a support ticket | Must | OBJ-1, OBJ-3 | [S3] |
| BR-2 | Partner access uses our existing company identity (no new password store) | Must | OBJ-2 | [[integrations:SSO]] [S1] |
| BR-3 | No credentials or secrets are ever shared over insecure channels (e.g. email) | Must | OBJ-2 | [[integrations:SFTP]] [S3], [[integrations:Transactional Email]] [S2] |
| BR-4 | Every onboarding action is auditable for Security review | Should | OBJ-2 | [S3] |
| BR-5 | Ops can revoke a partner's access when a relationship ends | Could | OBJ-3 | — |

## 9. Assumptions, constraints & dependencies
- **Assumptions:** partners can produce an SSH key pair (with guidance).
- **Constraints:** reuse the existing Okta IdP and SES sending domain; no new infrastructure; the
  SFTP directory convention is fixed [S3].
- **Dependencies:** Security sign-off on the access model; Integration Ops platform capacity.

## 10. Risks
| Risk | Impact | Likelihood | Mitigation / owner |
|---|---|---|---|
| Partners struggle with SSH keys | Onboarding stalls | Med | In-portal guide; Ops-assisted fallback (Partner Success) |
| Self-service misconfig exposes a directory | Security | Low | Fixed layout + audit + Security review gate (Security) |

## 11. High-level milestones
| Milestone | Target | Notes |
|---|---|---|
| BRD sign-off | Q3 wk1 | this document |
| Functional requirements approved | Q3 wk2 | `requirements.md` |
| Pilot with 2 partners | Q3 wk6 | measure OBJ-1 |

## 12. Approvals / sign-off
| Approver | Role | Decision | Date |
|---|---|---|---|
| VP, Partner Operations | Sponsor | Approved | 2026-06-16 |
| Head of Security | Consulted | Approved (with audit requirement → BR-4) | 2026-06-16 |

## Open questions
- [ ] BR-5 (Ops revoke): in this initiative or a fast-follow? (Currently `Could`.)

---
_Next: the Requirements Analyst turns these `BR-n` into functional requirements in
[`requirements.md`](requirements.md) — each FR cites the BR it serves — and the Story Writer
carries that to user stories in [`stories.md`](stories.md), giving a `BR → FR → US` chain._
