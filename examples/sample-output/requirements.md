# Requirements: Self-service partner SFTP onboarding

| | |
|---|---|
| **Author** | Requirements Analyst (DevLoop) |
| **Status** | Approved |
| **Last updated** | 2026-06-16 |
| **Stakeholders** | Integration Ops, Partner Success, Security |

## 1. Problem & outcome
Partners that exchange files with us are onboarded by hand: Ops creates an SFTP account, emails
credentials, and manually tells the partner the directory layout. It takes days, credentials get
shared insecurely, and Ops carries the toil. **Outcome:** a partner admin can self-serve an SFTP
exchange in minutes, authenticated through our existing SSO, with credentials never sent by email.
Cost of doing nothing: onboarding stays a multi-day manual ticket and a recurring security risk.

## 2. Goals & non-goals
- **Goals:** self-service SFTP space creation; SSO-authenticated partner access; key-based auth
  (no emailed passwords); automated status notifications.
- **Non-goals (out of scope this iteration):** file *content* validation/transformation; a
  partner-facing analytics dashboard; non-SFTP transports (AS2, API upload).

## 3. Personas
| Persona | Context | Primary goal |
|---|---|---|
| Partner Admin | External; technical contact at a partner org | Set up & manage their file exchange without a ticket |
| Integration Ops | Internal; owns the SFTP platform | Stop doing manual onboarding; keep it auditable |

## 4. Current state
Ops manually provisions an account on the SFTP host, sets directory permissions, and emails the
partner a username/password plus a PDF of the directory layout. No self-service, credentials in
email, and no audit trail of who set up what.

## 5. Functional requirements
_Source refs cite the context pack and (since a BRD exists) the business requirement each FR
serves; ⚠ marks a conflict or gap._

| ID | Requirement | Priority (MoSCoW) | Source refs | Notes |
|---|---|---|---|---|
| FR-1 | Partner admins shall authenticate via company SSO (SAML for web) before reaching the onboarding portal. | Must | BR-2, [[integrations:SSO]] [S1] | Reuses Okta IdP; no new password store |
| FR-2 | The system shall let an authenticated partner admin create an SFTP exchange space (home dir + `inbound/`/`outbound/` layout). | Must | BR-1, [[integrations:SFTP]] [S3] | Mirrors the documented directory convention |
| FR-3 | The system shall register the partner's **SSH public key**; passwords shall never be issued or emailed. | Must | BR-3, [[integrations:SFTP]] [S3] | Closes the emailed-credentials gap |
| FR-4 | The system shall email the partner admin a confirmation (no secrets) when a space is provisioned, and Ops on failure. | Must | BR-3, [[integrations:Transactional Email]] [S2] | Via SES; honors bounce handling |
| FR-5 | The system shall record an audit entry (who, what, when) for every space created or key changed. | Should | BR-4, [S3] | For Security review |
| FR-6 | Ops shall be able to suspend a partner's access from an admin view. | Could | BR-5 | Traces to BR-5 (`Could` in the BRD) |

## 6. Non-functional requirements
| ID | Type | Requirement / target | Source refs |
|---|---|---|---|
| NFR-1 | Security | SSO via SAML; SFTP key-based auth only; secrets never in email or logs. | BR-2, BR-3, [[integrations:SSO]] [S1], [[integrations:SFTP]] [S3] |
| NFR-2 | Performance | Space provisioning completes within 60s p95 of submission. | — |
| NFR-3 | Deliverability | Confirmation emails respect SES sending limits and bounce/complaint handling. | [[integrations:Transactional Email]] [S2] |

## 7. Data & integrations
Reads: SSO assertion (partner identity, org). Writes: SFTP account + directory tree, stored SSH
public key, audit log. External systems: Okta (SSO), AWS SES (email), the SFTP host.

## 8. Constraints & assumptions
- Assumes partners can produce an SSH key pair (provide a short how-to in the portal).
- Reuses the existing Okta IdP and SES sending domain; no new infra.
- SFTP host directory convention is fixed by [[integrations:SFTP]] [S3].

## 9. Risks
| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Partners struggle with SSH keys | Onboarding stalls | Med | In-portal key guide; allow Ops-assisted fallback |
| SES bounces to partner domains | Missed confirmations | Low | Surface status in-portal too, not email-only |
| Self-service misconfig exposes a dir | Security | Low | Fixed layout + audit (FR-5); Security review gate |

## 10. Acceptance & metrics
Done when a partner admin can self-onboard an SFTP space end to end via SSO with a key (no emailed
secret) and receive a confirmation. Watch: median onboarding time (target < 1 day → minutes),
# of onboarding tickets (target ↓), % spaces created without Ops involvement.

## Open questions
- [ ] FR-6 (Ops suspend) — confirm it's in this iteration; no source backs it yet.
- [ ] Do any partners require password auth as a fallback, or is key-only acceptable for all?
