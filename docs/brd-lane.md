# The BRD lane

The formal path: a **Business Requirements Document with sign-off** before any functional work,
then the same chain — with traceability all the way from business objectives down to stories.
Best for **waterfall, regulated (finance/health/gov), consulting/SI, and vendor-RFP** teams.

```
Context Librarian → Business Analyst (BRD) → Requirements Analyst → Story Writer → Story Reviewer → Jira Organizer
(optional)          brd.md                   requirements.md        stories.md     story-review.md  jira-plan.md
```

## What the BRD adds
The **Business Analyst (BRD)** role produces `brd.md` in *business* language (never "the system
shall…"): executive summary, business **objectives + success metrics** (`OBJ-n`), scope,
stakeholders, current/future state, numbered **business requirements** (`BR-n`), assumptions /
constraints / risks, and an **approvals/sign-off** table. It's gated — the chain doesn't proceed
until the BRD is signed off.

## Traceability: `OBJ → BR → FR → US`
Downstream roles thread the chain automatically:
- The **Requirements Analyst** reads `brd.md` and tags each `FR`/`NFR` with the `BR-n` it serves
  (flagging FRs that serve no BR = scope creep, and BRs with no FR = coverage gap).
- The **Story Writer** carries `FR → US`; the **Jira Organizer** maps `OBJ-n → Initiative` and
  `BR-n → Requirement` (BA project).

A complete worked chain — `brd.md → requirements.md → stories.md → story-review.md → jira-plan.md`
with an end-to-end trace — is in [../examples/sample-output/](../examples/sample-output/).

## Run it
Start at the **Business Analyst (BRD)** (`/spec-brd` on Claude; `$business-analyst` / `/skills` on
Kiro/Codex), get sign-off, then continue with the Requirements Analyst. Already have a BRD from
elsewhere? Drop it in as `brd.md` and start at the Requirements Analyst — it'll trace to your
`BR-n`. Don't need a formal BRD? Use the [Agile lane](agile-lane.md).
