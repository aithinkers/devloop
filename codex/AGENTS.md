# DevLoop — business-analysis workflow for this repo

When asked to define a feature, gather requirements, or create stories/tickets, follow this
chain. Each phase gates the next; do not skip ahead.

0. **/spec-context** — Act as a Context Librarian. Ask, one category at a time, where
   company knowledge lives (local files/folders, wikis & URLs, SharePoint, paste-in text).
   Compile the sources into an interlinked LLM-Wiki under `knowledge/` (concept
   articles with [[wikilinks]] + source-traceable frontmatter + an `index.md` routing
   layer). Use `tools/wikikit.py` for scaffold/status/commit/lint. Run this FIRST when source material exists.
1. **/spec-requirements** — Act as a Requirements Analyst. First read `knowledge/wiki/index.md` if present, open relevant concept articles, and only ask about gaps. Interview Socratically, ONE
   question at a time with A/B/C options, until the checklist is covered. Produce
   `requirements.md` with numbered FR/NFR IDs and explicit sign-off. No solutioning, no
   stories yet.
2. **/spec-stories** — Act as a Story Writer. Convert approved `requirements.md` into epics
   and INVEST user stories with Gherkin acceptance criteria and a traceability matrix.
   Produce `stories.md`.
3. **/spec-review** — Act as an independent Story Reviewer. Check INVEST, Definition of
   Ready, acceptance-criteria quality, and requirement coverage. Produce `story-review.md`.
4. **/spec-jira** — Act as a Jira Organizer. Turn `stories.md` into `jira-plan.md`:
   Initiative→Epic→Story/Task hierarchy, Components derived from the codebase/integration
   wikis, label taxonomy, field mappings. Guidance only; no import file.

Custom prompts live in `~/.codex/prompts/` (run the installer). Invoke as `/spec-requirements`,
`/spec-stories`, `/spec-review`.
