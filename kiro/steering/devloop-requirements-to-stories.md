---
inclusion: manual
---
# DevLoop — Requirements → Stories methodology

This steering file gives Kiro a disciplined business-analysis workflow. It maps directly
onto Kiro's native spec flow (requirements → design → tasks): treat **requirements.md** as
the requirements phase and **stories.md** as part of the design/tasks phase.

Run the phases in order. Each phase gates the next.

## Phase 0 — Context Librarian → wiki library
Run FIRST when source material exists. Compile sources into a **library of LLM-Wikis** (not
one flat doc), described in a registry `devloop.wikis.json` (see
`specs/_template/devloop.wikis.example.json`). Typical wikis: **project** (local: meeting
minutes, SOPs, product docs, workflows), **integrations** (SSO/APIs/Email/FTP — often a git
repo), **devops** (CI/CD, environments, release), **codebase** (generated from a code repo).
Git-backed wikis are cloned/refreshed with `tools/wikikit.py sync`. For each wiki use the
matching profile in `specs/_template/wiki-profiles.md`, then compile concept articles with
`[[wikilinks]]` (namespace cross-wiki links like `[[integrations:SSO]]`) and an `index.md`
routing layer. Use `tools/wikikit.py` (registry/sync/scaffold/status/commit/lint, incl.
`lint --all` for cross-wiki links). Cite every fact; skip unchanged sources.

## Phase 1 — Requirements Analyst → requirements.md
First read the primary project wiki's `index.md` (via the registry) and pull in referenced wikis (integrations/devops/codebase) as needed, summarize what is already known, and only ask about gaps (confirm documented facts rather than asking cold; tag each FR/NFR with source IDs and flag contradictions). Interview the user Socratically, ONE question at a time, offering A/B/C options each time.
Cover: problem & outcome, personas, current state, scope (in/out), functional requirements
(number them FR-1…), non-functional requirements (NFR-1…), data & integrations,
constraints & assumptions, risks, acceptance & metrics. Do not design a solution or write
stories. Produce `requirements.md` using the template in `specs/_template/requirements.md`
and get explicit approval before moving on.

## Phase 2 — Story Writer → stories.md
Only after requirements are approved. Group FR/NFR into epics (EP-1…), decompose into
INVEST user stories (US-1…) in "As a / I want / so that" form, each tracing to requirement
IDs, with MoSCoW priority, a size, and Gherkin (Given/When/Then) acceptance criteria
covering happy path + edge/error cases. Produce `stories.md` using the template in
`specs/_template/stories.md`, ending with a traceability matrix.

## Phase 3 — Story Reviewer → story-review.md
Independently review stories.md against requirements.md: coverage/traceability, INVEST,
acceptance-criteria quality, Definition of Ready (`specs/_template/definition-of-ready.md`),
consistency, sizing. Produce `story-review.md` with a findings table and prioritized fixes.
Recommend changes; do not silently rewrite.

## Phase 4 — Jira Organizer → jira-plan.md + devloop.jira.json
Two capabilities: (1) recommend how Jira should be organized — split a **BA** project
(Initiative, Requirement, Decision) from a **TECH** project (Epic, Story, Task, Bug,
Sub-task), derive Components from the codebase/integration wikis, define a label taxonomy
and field/hierarchy mappings (priority from MoSCoW, story points); (2) capture the real
setup in `devloop.jira.json` (`tools/wikikit.py jira init` then `jira validate`). When that
config exists, the Story Writer suggests a concrete per-story mapping (project, issue type,
component, labels, priority) instead of generic tags. Guidance + config only — no import
file. See `specs/_template/jira-organization.md` and `devloop.jira.example.json`.
