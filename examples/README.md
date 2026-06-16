# Example: build a single 'integrations' wiki

`integrations-src/` holds three tiny sample sources (SSO, Email, SFTP). Use them to try
building **one** wiki end to end. See `../test/smoke_test.sh` for an automated run, or do it
by hand:

```bash
# from a scratch project dir
python3 /path/to/wikikit.py registry init
# edit devloop.wikis.json: keep one local wiki, e.g. id "integrations", wiki_path "knowledge/wiki"
python3 /path/to/wikikit.py scaffold --wiki integrations
cp /path/to/examples/integrations-src/*.md knowledge/raw/
python3 /path/to/wikikit.py status --wiki integrations      # -> 3 NEW
#  ... now run /spec-context (the LLM compiles concept articles from knowledge/raw) ...
python3 /path/to/wikikit.py lint   --wiki integrations
python3 /path/to/wikikit.py commit --wiki integrations
```

# Example: reuse shared wikis (devops, integrations) across projects

Build company-wide wikis **once**, then reference them from every project.
`devloop.wikis.shared.example.json` is a ready-to-edit registry: a local `project` wiki plus
shared `devops` and `integrations` wikis pulled from their own git repos.

**1. Build each shared wiki once** (in its own repo, or a scratch dir), then commit its compiled
`knowledge/wiki/` to that repo — see the single-wiki recipe above. (Build it from raw docs with
`ingest.py <folder> --wiki <id>` then `/spec-context`.)

**2. In your current project**, drop in the registry and pull the shared wikis:

```bash
cp /path/to/examples/devloop.wikis.shared.example.json ./devloop.wikis.json
# edit the git URLs to your repos; keep `contains: "wiki"` for already-compiled wikis
python3 /path/to/wikikit.py sync --all     # clones devops + integrations into .devloop/wikis/
python3 /path/to/wikikit.py lint --all     # checks [[devops:…]] / [[integrations:…]] resolve
```

**3. Run the chain.** `/spec-requirements` reads your primary project wiki, pulls in the
referenced `devops`/`integrations` wikis as needed, and tags each requirement with the backing
concept + source. Link shared concepts with a namespace: `[[integrations:SSO]]`,
`[[devops:Release Pipeline]]`.

**Refresh later:** `wikikit.py sync --all` (git pull + report changed files), then `lint --all`.
Use `contains: "sources"` instead of `"wiki"` if a shared repo holds raw docs you want compiled
per project rather than a pre-built wiki.

# Example: a wiki for a code repo (stored in the repo, referenced elsewhere)

Distill an existing code repository into a `codebase` wiki, commit it **inside that repo**, and
let other projects use the distilled knowledge (services, APIs, data models, config, deps)
instead of reading the source. The `app-codebase` entry in `devloop.wikis.shared.example.json`
shows the consumer side.

**1. In the code repo — generate the wiki once and commit it:**

```bash
# from inside the code repo
python3 /path/to/wikikit.py registry init               # minimal registry: one codebase wiki, source local "."
python3 /path/to/wikikit.py scaffold --wiki app-codebase
#  ... run /spec-context — the Context Librarian walks the tree and DESCRIBES it (services,
#      api/endpoint, data model, config, dependency); it does not paste code ...
python3 /path/to/wikikit.py lint   --wiki app-codebase
python3 /path/to/wikikit.py commit --wiki app-codebase  # records .wiki-state.json for incremental refresh
git add knowledge/ && git commit -m "Add DevLoop codebase wiki"   # the wiki ships WITH the code
```

**2. In your current project — reference it (clone & use the knowledge, not the code):**

```bash
# add the app-codebase entry from devloop.wikis.shared.example.json to your devloop.wikis.json
python3 /path/to/wikikit.py sync --all     # clones the repo into .devloop/wikis/app-codebase/
python3 /path/to/wikikit.py lint --all     # checks [[app-codebase:…]] links resolve
```

`/spec-requirements` and `/spec-stories` then read the compiled wiki and link with
`[[app-codebase:AuthService]]`; the Jira Organizer derives **Components** from its services/modules.

**Refresh:** when the code changes, the repo owners re-run `/spec-context` (only changed files
recompile, via the SHA cache), `commit`, and push; consumers `sync --all`.

Notes: `sync` shallow-clones the whole repo, so the code files land on disk — but the agent only
reads `knowledge/wiki/`, so its effort is the distilled wiki, not the source. For a code-free
artifact, publish just the compiled `knowledge/wiki/` to a separate lightweight wiki repo and
point `url` there. Each article records its **key files**, so the agent can open a specific file
for ground truth when needed. Prefer `contains: "sources"` if you'd rather compile the code
per-project than ship a pre-built wiki.
