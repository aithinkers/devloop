# OKF compatibility (Open Knowledge Format)

DevLoop's Context Librarian produces an **LLM-Wiki**: markdown concept files with YAML
frontmatter, an `index.md` routing layer, source-traceable citations, and cross-links —
distributed as a git repo. Google Cloud independently specified the same artifact as the
[**Open Knowledge Format (OKF)**](https://github.com/GoogleCloudPlatform/knowledge-catalog),
a minimal interoperability standard for "knowledge bundles." Both lineages cite Karpathy's
[LLM wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

DevLoop's wiki is a **superset** of OKF. These commands let DevLoop wikis interoperate with
the OKF ecosystem without giving up DevLoop's value-adds (multi-wiki registry, cross-wiki
namespacing, stable source IDs, incremental SHA recompile, `kind` extraction profiles).

## What maps to what

| OKF v0.1 | DevLoop | Notes |
|---|---|---|
| Knowledge **bundle** (git) | a **wiki** (`knowledge/wiki/`) | same unit |
| `type` (required) | `type` frontmatter | DevLoop always sets it |
| `title` / `description` / `resource` | `title` (+ now `description` / `resource`) | added to the concept template |
| `index.md` + root `okf_version` | `index.md` (now stamped on export) | progressive-disclosure entry point |
| `# Citations` | `sources:` frontmatter + `sources/INDEX.md` (S-IDs) | `export` synthesizes `# Citations` per concept |
| standard markdown links | `[[wikilinks]]` + cross-wiki `[[ns:Concept]]` | `export` rewrites to portable links |
| `log.md` (optional) | git history + `.wiki-state.json` | optional |

DevLoop keeps `[[wikilinks]]` **internally** — they auto-resolve via `wikikit lint` and
power cross-wiki references OKF doesn't specify. `export --okf` produces the portable form.

## Emit a portable OKF bundle

```bash
# from a project with a compiled wiki:
python3 tools/wikikit.py export --okf --wiki project --out ./okf-bundle
# or against a directory directly:
python3 tools/wikikit.py export --okf knowledge --out ./okf-bundle
```

The export:
- rewrites `[[Concept]]` / `[[Concept|alias]]` → bundle-relative markdown links pointing at
  paths like `/concepts/Concept.md`, which render on GitHub and need no resolver;
- renders cross-wiki `[[ns:Concept]]` and any unresolved link as plain text (OKF bundles
  are self-contained — DevLoop never fabricates a target path);
- turns each concept's `sources:` IDs into a `# Citations` section using `sources/INDEX.md`;
- stamps `okf_version: "0.1"` on the root `index.md`.

The result is a conformant OKF knowledge bundle other OKF-aware tools can consume.

## Check conformance

```bash
python3 tools/wikikit.py okf-lint --wiki project
```

Flags concept files missing the required `type`, and notes any remaining `[[wikilinks]]`
or a missing root `okf_version` (both resolved by `export --okf`).

## Consume an OKF bundle

An OKF bundle is already a compiled wiki. Register it like any shared wiki and reference it
with `contains: "wiki"` — `wikikit sync --all` clones it into `.devloop/wikis/`, and the
Requirements Analyst grounds requirements in it. See
[org-rollout.md](org-rollout.md) and
[../examples/devloop.wikis.shared.example.json](../examples/devloop.wikis.shared.example.json).

> OKF is a v0.1 **draft**. DevLoop's alignment is additive and low-risk — it lets you ride an
> emerging standard while keeping the richer internal model. See
> [architecture.md](architecture.md) for how the single source maps to each host.
