# Release checklist

DevLoop's docs have drifted from reality before (stale test counts, "five roles", host-specific
wording in shared docs). Most of that is now caught automatically — run these in order and the
machine tells you what's out of sync.

1. **Regenerate + prove no drift.**
   ```bash
   ./devloop build           # core/ + tools/ → skills/ + host wrappers
   ./devloop build --check    # fails if the generated tree OR plugin.json version is stale
   ```
2. **Run the smoke test (no LLM, no network).** `bash test/smoke_test.sh` → expect `N passed, 0 failed`.
   It already enforces: generated-tree freshness, plugin version == VERSION, frontmatter is valid
   YAML, descriptions are quoted, shared docs have no host-specific `/spec-*`, the Codex
   orchestrator lists every role, single-source skills, and all-host install/`init`/`status`.
3. **Bump the version.** Edit `VERSION` (semver), then `./devloop build` re-stamps
   `.claude-plugin/plugin.json`. Add a `CHANGELOG.md` entry (what changed + why).
4. **Sync the human-maintained counts** (the few the tests can't infer): the smoke-test count in
   `README.md` ("Expect `N passed`", "N checks") and `CONTRIBUTING.md` must equal the suite total.
   ```bash
   grep -rn 'passed, 0 failed\|checks, no' README.md CONTRIBUTING.md   # all match the suite?
   ```
5. **Grep for the usual drift** (should all return nothing in shared/cross-host docs):
   ```bash
   grep -rn '/spec-' examples/                 # Claude-only commands leaking into shared docs
   grep -rn 'five \(roles\|gated\|phases\)' .   # stale role count after adding/removing a role
   ```
6. **Commit, push, confirm CI is green** (`gh run list` / the CI badge). A PR must keep
   `./devloop build --check` clean and the smoke test green — CI enforces both.

> Adding/removing a **role**? It's defined once in `core/roles.json`, but two authored files don't
> regenerate — update **`codex/AGENTS.md`** (the orchestrator; a smoke test guards this) and the
> host-count prose in `kiro/README.md` / the main `README.md`. Then redo this checklist.
