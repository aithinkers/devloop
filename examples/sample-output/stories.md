# Backlog: Self-service partner SFTP onboarding

_Source: requirements.md (approved 2026-06-16)_

## Backlog overview
| Story | Title | Epic | Priority | Size | Covers | Component(s) | Labels |
|---|---|---|---|---|---|---|---|
| US-1 | SSO login to the onboarding portal | EP-1 | Must | S | FR-1, NFR-1 | SSO | security |
| US-2 | Create an SFTP exchange space | EP-1 | Must | M | FR-2, NFR-2 | SFTP | onboarding |
| US-3 | Register SSH key (no emailed secret) | EP-1 | Must | M | FR-3, NFR-1 | SFTP | security |
| US-4 | Provisioning + failure notifications | EP-2 | Must | S | FR-4, NFR-3 | Email | notifications |
| US-5 | Audit trail for space/key changes | EP-2 | Should | S | FR-5 | SFTP | audit |

---

## EP-1 · Self-service exchange setup
**Goal:** a partner admin sets up a working SFTP exchange via SSO, key-based.  ·  **Covers:** FR-1, FR-2, FR-3

### US-1 · SSO login to the onboarding portal
**As a** partner admin, **I want** to sign in with my company SSO, **so that** I reach the portal without a new password.
- **Epic:** EP-1   **Priority:** Must   **Size:** S   **Covers:** FR-1, NFR-1

**Acceptance criteria**
```gherkin
Scenario: Successful SAML sign-in
  Given I am a partner admin with an Okta identity
  When I open the onboarding portal
  Then I am redirected to SSO and returned authenticated, with my partner org resolved

Scenario: Unauthorized user
  Given I authenticate but my account is not mapped to a partner org
  When the assertion is processed
  Then I am denied access and shown how to request onboarding
```

### US-2 · Create an SFTP exchange space
**As a** partner admin, **I want** to create my SFTP space, **so that** I can exchange files without a ticket.
- **Epic:** EP-1   **Priority:** Must   **Size:** M   **Covers:** FR-2, NFR-2

**Acceptance criteria**
```gherkin
Scenario: Provision a new space
  Given I am an authenticated partner admin with no existing space
  When I request a space
  Then a home directory with inbound/ and outbound/ is created within 60s
  And I see the host, path, and connection details in the portal

Scenario: Space already exists
  Given my org already has a space
  When I request another
  Then creation is blocked and I am shown the existing space instead
```

### US-3 · Register SSH key (no emailed secret)
**As a** partner admin, **I want** to register my SSH public key, **so that** I connect securely without a password.
- **Epic:** EP-1   **Priority:** Must   **Size:** M   **Covers:** FR-3, NFR-1

**Acceptance criteria**
```gherkin
Scenario: Add a valid public key
  Given I am setting up my space
  When I paste a valid SSH public key
  Then key-based SFTP auth is enabled and no password is ever issued or emailed

Scenario: Invalid key
  Given I paste malformed key text
  When I submit
  Then it is rejected with guidance, and no partial credential is created
```

---

## EP-2 · Notifications & audit
**Goal:** every onboarding action is communicated and recorded.  ·  **Covers:** FR-4, FR-5

### US-4 · Provisioning + failure notifications
**As an** integration ops engineer, **I want** automated status emails, **so that** partners get confirmation and I hear about failures.
- **Epic:** EP-2   **Priority:** Must   **Size:** S   **Covers:** FR-4, NFR-3

**Acceptance criteria**
```gherkin
Scenario: Successful provisioning notifies the partner (no secrets)
  Given a space is provisioned
  When the process completes
  Then the partner admin receives a confirmation email containing no credentials

Scenario: Provisioning failure notifies Ops
  Given provisioning fails
  When the error is detected
  Then Ops is emailed with the failure detail and the partner is not sent a confirmation
```

### US-5 · Audit trail for space/key changes
**As an** integration ops engineer, **I want** an audit entry per change, **so that** Security can review who did what.
- **Epic:** EP-2   **Priority:** Should   **Size:** S   **Covers:** FR-5

**Acceptance criteria**
```gherkin
Scenario: Record a provisioning event
  Given a partner admin creates a space or changes a key
  When the action completes
  Then an audit entry with actor, action, target, and timestamp is recorded
```

---

## Traceability matrix
| Requirement | Covered by | Status |
|---|---|---|
| FR-1 | US-1 | ✅ |
| FR-2 | US-2 | ✅ |
| FR-3 | US-3 | ✅ |
| FR-4 | US-4 | ✅ |
| FR-5 | US-5 | ✅ |
| FR-6 (Ops suspend) | — | ⚠️ GAP — deferred; not in this iteration (no source) |
| NFR-1 | US-1, US-3 | ✅ |
| NFR-2 | US-2 | ✅ |
| NFR-3 | US-4 | ✅ |

_No `devloop.jira.json` present in this example, so no per-story Jira mapping table is emitted.
With a config, the Story Writer would add target project / issue type / component / labels /
priority per story here._
