# DevLoop quick reference

## Which lane do I run?
| You are… | Start at | Chain |
|---|---|---|
| **Agile team** | Requirements Analyst | Context → Requirements → Stories → Review → Jira |
| **BRD / waterfall / regulated / SI team** | Business Analyst (BRD) | Context → **BRD** → Requirements → Stories → Review → Jira |
| **No docs/wikis yet** | Context Librarian | compile a wiki first, *or* skip straight to Requirements (it runs cold) |
| **Already have a BRD** | Requirements Analyst | it reads `brd.md` and traces each FR back to a `BR` |
| **Shared knowledge across projects** | Context Librarian | build `devops`/`integrations`/`codebase` wikis once → reference everywhere (see [docs/org-rollout.md](docs/org-rollout.md)) |

The roles are **gated** — each finishes (you sign off) before the next. The BRD step is **opt-in**.

## Invoke a phase (differs by host)
| Phase (skill) | Claude Code | Kiro | Codex |
|---|---|---|---|
| Context Librarian | `/spec-context` | `$context-librarian` or `/skills` | `$context-librarian` or `/skills` |
| Business Analyst (BRD) | `/spec-brd` | `$business-analyst` | `$business-analyst` |
| Requirements Analyst | `/spec-requirements` | `$requirements-analyst` | `$requirements-analyst` |
| Story Writer | `/spec-stories` | `$story-writer` | `$story-writer` |
| Story Reviewer | `/spec-review` | `$story-reviewer` | `$story-reviewer` |
| Jira Organizer | `/spec-jira` | `$jira-organizer` | `$jira-organizer` |

You usually don't invoke anything — skills **auto-trigger** by what you're doing. On Kiro/Codex
the roles aren't `/` slash commands; use the `/skills` picker or `$<role>`. (`#devloop` loads the
Kiro steering orchestrator.)

## CLI (`devloop`)
| Command | Does |
|---|---|
| `devloop install [--host claude\|kiro\|codex\|all] [--scope project\|home]` | install the skills/wrappers |
| `devloop init [--sample] [--jira]` | scaffold a project here (registry + `knowledge/`; `--sample` seeds demo sources) |
| `devloop status [--markdown]` | project readiness + where you are in the chain |
| `devloop list` / `uninstall` / `doctor` | what's installed / remove / environment check |

## Helpers (`wikikit.py` · `ingest.py`)
Run from where they're installed (`~/.claude/tools/`, `.kiro/tools/`, `$CODEX_HOME/tools/`), or
`python3 tools/wikikit.py …` from a clone. The agent usually runs these for you.

| Command | Does |
|---|---|
| `wikikit.py registry init [--minimal]` | create `devloop.wikis.json` (the wiki library) |
| `wikikit.py sync <id> \| --all` | git: clone/pull (non-zero on failure); local/url: report status |
| `wikikit.py scaffold --wiki <id>` | create a wiki's `knowledge/` structure |
| `wikikit.py status \| commit --wiki <id>` | SHA256 change detection / record after compiling |
| `wikikit.py lint --wiki <id> \| --all` | broken `[[links]]` / orphans (incl. cross-wiki) |
| `wikikit.py jira init \| validate` | scaffold / validate `devloop.jira.json` |
| `ingest.py SOURCES --wiki <id>` | recursive multi-format folder ingest into `raw/` |

## ID conventions (traceability)
`OBJ-n` business objective (BRD) → `BR-n` business requirement (BRD) → `FR-n`/`NFR-n` functional
requirement → `EP-n` epic → `US-n` user story. See a full worked chain in
[examples/sample-output/](examples/sample-output/).
