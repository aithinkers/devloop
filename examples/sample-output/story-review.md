# Story review: Self-service partner SFTP onboarding

_Source: stories.md · reviewed against requirements.md (approved 2026-06-16) · 2026-06-16_

## Verdict
**Ready with minor fixes.** Coverage is complete for the in-scope requirements; two AC gaps and
one sizing nit should be addressed before the stories enter a sprint. FR-6 is intentionally
deferred (it's `Could` in the BRD) — tracked, not a defect.

## Findings
| ID | Area | Severity | Finding | Suggested fix |
|---|---|---|---|---|
| R-1 | Coverage | Info | FR-6 (Ops suspend access) has no story. | Expected — `Could`/deferred per BR-5; leave out of this iteration, keep the GAP row visible. |
| R-2 | AC quality | Should-fix | US-2 (create space) has no AC for the **60s p95** target in NFR-2. | Add a scenario asserting provisioning completes within the SLA, or note it's covered by a perf test. |
| R-3 | AC quality | Should-fix | US-4 (notifications) doesn't cover the **bounce/complaint** path from NFR-3. | Add an edge scenario: a bounced confirmation surfaces status in-portal, not email-only. |
| R-4 | INVEST (Small) | Consider | US-2 + US-3 are both `M` and tightly coupled (a space isn't usable without a key). | Fine to keep separate for review clarity; consider delivering them in one PR. |
| R-5 | Testability | Info | "valid SSH public key" (US-3) is subjective. | Define "valid" (parseable OpenSSH public key, supported types) in the AC or a linked standard. |

## Coverage & traceability
- **FR → US:** FR-1→US-1, FR-2→US-2, FR-3→US-3, FR-4→US-4, FR-5→US-5. ✅ all Must/Should covered.
- **NFR:** NFR-1→US-1/US-3 ✅; NFR-2→US-2 ⚠ (see R-2); NFR-3→US-4 ⚠ (see R-3).
- **Gap:** FR-6 → — (deferred, BR-5 `Could`).

## INVEST
Stories are independent, negotiable, valuable, and (mostly) small with clear AC. US-2/US-3
coupling (R-4) is the only INVEST smell, and it's acceptable.

## Definition of Ready
Each story has a persona, a clear outcome, and Gherkin AC. **Blocking before sprint:** resolve
R-2 and R-3 (NFR coverage in AC). R-5 (define "valid key") recommended.
