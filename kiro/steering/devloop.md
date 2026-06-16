---
inclusion: auto
name: devloop
description: DevLoop business-analysis chain — turning a feature idea into requirements, INVEST user stories, a story review, and a Jira organization plan, grounded in compiled LLM-Wikis. Use when the user asks to gather requirements, write stories/tickets, or plan a backlog.
---

# DevLoop — business-analysis chain

Turn a feature idea into a review-ready backlog through a chain of **gated** roles. Each
phase gates the next — do not skip ahead. Adopt the matching **Agent Skill** for each
phase; the skill carries the full method, so this file only sequences them.

1. **Context Librarian** — adopt the `context-librarian` skill (or the `/context-librarian` subagent). Ask me one category at a time where knowledge lives (local files/folders, wikis & URLs, SharePoint, paste-in text), manage the wiki registry with `wikikit.py`, and compile a library of interlinked LLM-Wikis under `knowledge/`. Cite every fact; flag conflicts and gaps. Hand off to the Requirements Analyst when done.
2. **Business Analyst (BRD)** — adopt the `business-analyst` skill (or the `/business-analyst` subagent). (Optional — for teams that need a formal BRD/sign-off.) Read the wiki library for current-state grounding, then interview Socratically (one question at a time, A/B/C options) to capture business objectives + metrics (OBJ-n), scope, stakeholders, and numbered business requirements (BR-n) in business language — no `system shall`. Produce `brd.md` and get explicit sign-off. Hand off to the Requirements Analyst, who traces each FR/NFR back to a BR.
3. **Requirements Analyst** — adopt the `requirements-analyst` skill (or the `/requirements-analyst` subagent). Read the wiki library if present and run a Socratic, one-question-at-a-time interview (offer A/B/C options), only asking about gaps the wikis don't cover. Then draft `requirements.md` (numbered FR/NFR, each tagged with wiki + source refs) and get my sign-off. No stories or code in this phase.
4. **Story Writer** — adopt the `story-writer` skill (`$story-writer` or `/skills`). Read the approved `requirements.md`, group requirements into epics, decompose into INVEST user stories with Gherkin acceptance criteria, and write `stories.md` with a traceability matrix. If `devloop.jira.json` exists, add a concrete per-story Jira mapping; otherwise tag components/labels lightly. Stop if requirements are missing/unapproved.
5. **Story Reviewer** — adopt the `story-reviewer` skill (`$story-reviewer` or `/skills`). Independently review `stories.md` against `requirements.md`: coverage/traceability, INVEST, acceptance-criteria quality, and Definition of Ready. Write `story-review.md` with a findings table and prioritized fixes. Recommend changes; do not silently rewrite.
6. **Jira Organizer** — adopt the `jira-organizer` skill (`$jira-organizer` or `/skills`). Do two things: (1) recommend how Jira should be organized for this project (BA vs TECH projects, issue types incl. Requirement/Decision, Components from the wikis, labels, field/hierarchy mappings); (2) capture the real setup in `devloop.jira.json` (`wikikit.py jira init` / `jira validate`). Write `jira-plan.md` and, if `stories.md` exists, a Story→Project→Type→Component→Labels→Priority mapping table. Guidance + config only.

Helpers are installed at `.kiro/tools/` — run them as `python3 .kiro/tools/wikikit.py …`
and `python3 .kiro/tools/ingest.py <folder> --wiki <id>` (or use the DevLoop hooks,
which call the same paths). DevLoop's `requirements.md` is richer than Kiro's native
EARS spec (personas, FR/NFR, risks); it **feeds** a Kiro feature spec, not replaces it.
