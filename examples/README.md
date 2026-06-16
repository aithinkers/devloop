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
