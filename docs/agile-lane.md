# The Agile lane

The default, lightweight path: **idea → requirements → stories → review → backlog**, no formal
BRD. Best for product/agile teams who want grounded, traceable stories without a sign-off gate.

```
Context Librarian → Requirements Analyst → Story Writer → Story Reviewer → Jira Organizer
(optional, if you   requirements.md         stories.md     story-review.md  jira-plan.md
 have source docs)
```

## Steps
1. **Context Librarian** *(optional)* — if you have docs/repos/wikis, compile them into an
   LLM-Wiki so requirements are grounded and source-traced. No sources? Skip it.
2. **Requirements Analyst** — Socratic, one-question-at-a-time interview; only asks about gaps the
   wikis don't cover. Produces `requirements.md` (numbered `FR`/`NFR`, each source-traced). Sign off.
3. **Story Writer** — groups requirements into epics (`EP-n`) and INVEST stories (`US-n`) with
   Gherkin acceptance criteria + a traceability matrix → `stories.md`.
4. **Story Reviewer** — independent INVEST / Definition-of-Ready / coverage / AC-quality pass →
   `story-review.md`. Recommends fixes; doesn't silently rewrite.
5. **Jira Organizer** — recommends the Jira org and writes `jira-plan.md` (+ a per-story mapping
   if `devloop.jira.json` exists). Guidance + config only.

## Try it
```bash
devloop init --sample      # registry + knowledge/ + bundled SSO/Email/SFTP sources
```
Then adopt the **Context Librarian**, then the **Requirements Analyst** for a feature. Cold start
(no sources)? Skip straight to the Requirements Analyst — it just interviews you.

## Traceability
`FR → US` (the story matrix). Want business objectives above the functional layer
(`OBJ → BR → FR → US`) and a sign-off gate? Use the [BRD lane](brd-lane.md) instead.
See a full worked example in [../examples/sample-output/](../examples/sample-output/).
