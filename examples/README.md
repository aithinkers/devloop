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
