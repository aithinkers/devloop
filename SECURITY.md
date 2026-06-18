# Security

DevLoop is a local, dependency-light toolkit (`bash` + `python3` + `git`). It runs entirely on
your machine and **makes no network calls of its own** — model calls are made by your host
(Claude Code / Kiro / Codex), and DevLoop never writes to Jira or any external service (the Jira
Organizer produces guidance + config only). Still, a few things are worth knowing.

## Install from the official source only
The bootstrap is a `curl … | sh` that clones and runs code, so only install from the official
repository — **https://github.com/aithinkers/devloop** (or a clone you've reviewed). Don't pipe an
installer from a fork or mirror you don't trust. You can always read [`install.sh`](install.sh)
and [`devloop`](devloop) first; both are short, dependency-free shell.

## Threat model & guidance
- **Ingesting documents (`ingest.py`).** It parses office/zip/XML files (`.docx/.pptx/.xlsx`,
  `.drawio`, `.vsdx`, `.svg`) with the Python standard library. Parsing **untrusted** files is an
  attack surface (e.g. a hostile XML could attempt resource exhaustion). Run `ingest.py` on
  sources you trust; treat third-party documents with the same caution you'd give any untrusted
  input. It copies/extracts text locally and never uploads anything.
- **Git-backed wikis (`wikikit.py sync`).** This clones the git URLs *you* put in
  `devloop.wikis.json`. Only add repositories you trust.
- **Helper execution.** `wikikit.py` and `ingest.py` are pure-stdlib scripts that run locally
  under your host's normal permission model; review them if your environment requires it.
- **Secrets.** DevLoop ships no credentials. The MCP examples reference secrets via environment
  variables (e.g. `${SHAREPOINT_TOKEN}`) — never hardcode tokens into configs you commit.

## Reporting a vulnerability
Please report security issues privately via a
[GitHub security advisory](https://github.com/aithinkers/devloop/security/advisories/new) rather
than a public issue, and allow time for a fix before disclosure.
