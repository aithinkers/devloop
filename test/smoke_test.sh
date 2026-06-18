#!/usr/bin/env bash
# DevLoop smoke test — proves single-wiki generation plumbing end to end, no LLM and no
# network. It exercises wikikit.py exactly as the Context Librarian would, then simulates
# the LLM "compile" step by writing two concept articles, and checks lint/commit/status.
#
# Usage:  bash test/smoke_test.sh
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # repo root (devloop/)
WK="$HERE/tools/wikikit.py"
SAMPLE="$HERE/examples/integrations-src"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
PASS=0; FAIL=0
ok(){ echo "  ✓ $1"; PASS=$((PASS+1)); }
no(){ echo "  ✗ $1"; FAIL=$((FAIL+1)); }

echo "Repo:   $HERE"
echo "Sandbox: $TMP"
cd "$TMP"

echo "[1] registry init + trim to a single local 'integrations' wiki"
python3 "$WK" registry init >/dev/null
python3 - <<'PY'
import json
r=json.load(open("devloop.wikis.json"))
r["wikis"]=[{"id":"integrations","kind":"integrations","role":"primary",
             "source":{"type":"local","path":"."},"wiki_path":"knowledge/wiki"}]
json.dump(r,open("devloop.wikis.json","w"),indent=2)
PY
python3 "$WK" registry list | grep -q integrations && ok "registry lists the single wiki" || no "registry list"

echo "[2] scaffold ONLY that wiki"
python3 "$WK" scaffold --wiki integrations >/dev/null
[ -d knowledge/wiki/concepts ] && [ -f knowledge/sources/INDEX.md ] && ok "knowledge/ scaffolded" || no "scaffold"

echo "[3] add sample sources -> status shows 3 NEW"
cp "$SAMPLE"/*.md knowledge/raw/
N=$(python3 "$WK" status --wiki integrations | grep -c '^NEW')
[ "$N" -eq 3 ] && ok "3 new sources detected" || no "status NEW count = $N (want 3)"

echo "[4] simulate LLM compile: write 2 concept articles + index"
cat > knowledge/wiki/concepts/SSO.md <<'EOF'
---
title: SSO
type: integration
sources: [S1]
status: published
confidence: high
updated: 2026-06-14
---
# SSO
Okta IdP, SAML for web / OIDC for mobile [S1]. Related [[Transactional Email]].
EOF
cat > knowledge/wiki/concepts/Transactional-Email.md <<'EOF'
---
title: Transactional Email
type: integration
sources: [S2]
status: published
confidence: high
updated: 2026-06-14
---
# Transactional Email
AWS SES us-east-1 [S2]. Used alongside [[SSO]] for login notifications.
EOF
printf '# Knowledge Wiki — Index\n## Integrations\n- [[SSO]]\n- [[Transactional Email]]\n' > knowledge/wiki/index.md
ok "wrote concept articles + index"

echo "[5] lint the single wiki (cross-links resolve, no orphans)"
if python3 "$WK" lint --wiki integrations; then ok "lint clean"; else no "lint reported issues"; fi

echo "[6] commit hashes -> status now shows 0 new/changed"
python3 "$WK" commit --wiki integrations >/dev/null
if python3 "$WK" status --wiki integrations | grep -q '0 new, 0 changed'; then ok "incremental cache works"; else no "status after commit"; fi

echo "[7] change one source -> status detects exactly 1 changed"
echo "Daily send limit raised to 500k." >> knowledge/raw/email.md
C=$(python3 "$WK" status --wiki integrations | grep -c '^CHANGED')
[ "$C" -eq 1 ] && ok "1 changed source detected" || no "changed count = $C (want 1)"

echo "[8] git-backed wiki: clone + detect an upstream change (uses a local repo, no network)"
if command -v git >/dev/null 2>&1; then
  GT="$TMP/git-test"; mkdir -p "$GT/remote"
  ( cd "$GT/remote" && git init -q && git config user.email t@t.t && git config user.name t \
    && echo "SSO via Okta" > sso.md && git add -A && git commit -qm init )
  REF="$(git -C "$GT/remote" symbolic-ref --short HEAD)"   # main or master
  mkdir -p "$GT/proj"; cd "$GT/proj"
  python3 "$WK" registry init >/dev/null
  REMOTE="$GT/remote" REF="$REF" python3 - <<'PY'
import json, os
r = json.load(open("devloop.wikis.json"))
r["wikis"] = [{"id": "integrations", "kind": "integrations",
               "source": {"type": "git", "url": os.environ["REMOTE"],
                          "ref": os.environ["REF"], "subpath": "", "contains": "sources"},
               "wiki_path": ".devloop/wikis/integrations/knowledge/wiki"}]
json.dump(r, open("devloop.wikis.json", "w"), indent=2)
PY
  python3 "$WK" sync integrations | grep -q "cloned" && ok "git clone on first sync" || no "git clone"
  ( cd "$GT/remote" && echo "Email via SES" > email.md && git add -A && git commit -qm email )
  python3 "$WK" sync integrations | grep -q "1 file(s) changed" \
    && ok "upstream change detected on re-sync" || no "git change detection"
  cd "$TMP"
else
  echo "  (git not found — skipping git-backed test)"
fi

echo "[8b] sync exits NON-ZERO on a fatal git error (no silent success)"
SF="$TMP/syncfail"; mkdir -p "$SF"; cd "$SF"
python3 "$WK" registry init >/dev/null
python3 - <<'PY'
import json
r=json.load(open("devloop.wikis.json"))
r["wikis"]=[{"id":"bad","kind":"integrations",
            "source":{"type":"git","url":"/no/such/repo.git","ref":"main"},
            "wiki_path":".devloop/wikis/bad/knowledge/wiki"}]
json.dump(r,open("devloop.wikis.json","w"),indent=2)
PY
if python3 "$WK" sync bad >/dev/null 2>&1; then no "sync returned 0 on git clone failure"; else ok "sync exits non-zero on git failure"; fi
cd "$TMP"

echo "[8c] sync on a local source with no raw/ prints the exact ingest command"
SL="$TMP/synclocal"; mkdir -p "$SL"; cd "$SL"
python3 "$WK" registry init >/dev/null
python3 - <<'PY'
import json
r=json.load(open("devloop.wikis.json"))
r["wikis"]=[{"id":"proj","kind":"project","role":"primary",
            "source":{"type":"local","path":"srcdocs"},"wiki_path":"knowledge/wiki"}]
json.dump(r,open("devloop.wikis.json","w"),indent=2)
PY
python3 "$WK" scaffold --wiki proj >/dev/null
python3 "$WK" sync proj | grep -q "ingest.py srcdocs --wiki proj" \
  && ok "local sync points at the ingest command for source.path" || no "local sync missing ingest hint"
cd "$TMP"

echo "[9] cross-wiki lint: catch a broken [[namespace:Concept]] link"
XW="$TMP/xwiki"; mkdir -p "$XW"; cd "$XW"
python3 "$WK" registry init >/dev/null
python3 - <<'PY'
import json
r = json.load(open("devloop.wikis.json"))
r["wikis"] = [
  {"id": "project", "kind": "project", "role": "primary",
   "source": {"type": "local", "path": "."}, "wiki_path": "knowledge/wiki"},
  {"id": "integrations", "kind": "integrations",
   "source": {"type": "local", "path": "."},
   "wiki_path": ".devloop/wikis/integrations/knowledge/wiki"}]
json.dump(r, open("devloop.wikis.json", "w"), indent=2)
PY
python3 "$WK" scaffold --wiki project >/dev/null
python3 "$WK" scaffold --wiki integrations >/dev/null
printf '# SSO\nOkta.\n' > .devloop/wikis/integrations/knowledge/wiki/concepts/SSO.md
printf '# Login\nUses [[integrations:SSO]] and a missing [[integrations:Nope]].\n' \
  > knowledge/wiki/concepts/Login.md
XOUT="$(python3 "$WK" lint --all || true)"
echo "$XOUT" | grep -q "no 'Nope'" && ok "cross-wiki broken link detected" \
  || no "cross-wiki lint (got: $XOUT)"
echo "$XOUT" | grep -q "integrations:SSO" && no "valid cross-wiki link wrongly flagged" \
  || ok "valid cross-wiki link [[integrations:SSO]] resolves"
cd "$TMP"

echo "[10] jira config: init validates clean, a broken config is caught"
JT="$TMP/jira"; mkdir -p "$JT"; cd "$JT"
python3 "$WK" jira init >/dev/null
python3 "$WK" jira validate >/dev/null && ok "skeleton jira config validates" || no "jira skeleton invalid"
python3 - <<'PY'
import json
c=json.load(open("devloop.jira.json"))
c["routing"]["story"]={"project":"TECH","type":"Stroy"}   # typo type
json.dump(c,open("devloop.jira.json","w"),indent=2)
PY
if python3 "$WK" jira validate >/dev/null; then no "broken jira config not caught"; else ok "broken jira config rejected"; fi
cd "$TMP"

echo "[11] generated platform folders are in sync with core/ (no drift)"
if python3 "$HERE/build/build.py" --check >/dev/null 2>&1; then
  ok "generated tree up to date"
else
  no "generated tree is STALE — run ./build.sh"
fi

echo "[12] devloop CLI: install (project) lands files, uninstall removes them"
CT="$TMP/cli"; mkdir -p "$CT"; cd "$CT"
HOME="$CT" "$HERE/devloop" install --host claude --scope project >/dev/null
[ -f "$CT/.claude/skills/story-writer/SKILL.md" ] && [ -f "$CT/.claude/commands/spec-jira.md" ] \
  && ok "CLI install placed skills + commands" || no "CLI install missing files"
HOME="$CT" "$HERE/devloop" install --dry-run --host all >/dev/null && ok "CLI --dry-run runs for all hosts" || no "CLI dry-run failed"
HOME="$CT" "$HERE/devloop" uninstall --host claude --scope project >/dev/null
[ -f "$CT/.claude/skills/story-writer/SKILL.md" ] && no "CLI uninstall left files" || ok "CLI uninstall removed our files"
cd "$TMP"

echo "[12b] every host installs BOTH helper tools (wikikit.py + ingest.py) where the docs say"
HT="$TMP/hosttools"; mkdir -p "$HT"
HOME="$HT" CODEX_HOME="$HT/.codex" "$HERE/devloop" install --host all --scope home >/dev/null
miss=""
for pair in ".claude/tools" ".kiro/tools" ".codex/tools"; do
  for tool in wikikit.py ingest.py; do
    [ -f "$HT/$pair/$tool" ] || miss="$miss $pair/$tool"
  done
done
[ -z "$miss" ] && ok "wikikit.py + ingest.py present for claude/kiro/codex" || no "missing helper(s):$miss"
HOME="$HT" CODEX_HOME="$HT/.codex" "$HERE/devloop" uninstall --host all --scope home >/dev/null
left=""
for pair in ".claude/tools" ".kiro/tools" ".codex/tools"; do
  for tool in wikikit.py ingest.py; do
    [ -f "$HT/$pair/$tool" ] && left="$left $pair/$tool"
  done
done
[ -z "$left" ] && ok "uninstall removed both helpers for all hosts" || no "uninstall left:$left"
cd "$TMP"

echo "[12c] the INSTALLED helper actually runs (docs invocation path), and is executable"
RT="$TMP/runtest"; mkdir -p "$RT"
HOME="$RT" "$HERE/devloop" install --host claude --scope home >/dev/null
IWK="$RT/.claude/tools/wikikit.py"
[ -x "$IWK" ] && ok "installed wikikit.py has the executable bit" || no "installed wikikit.py not executable"
WORK="$RT/work"; mkdir -p "$WORK"; cd "$WORK"
if python3 "$IWK" registry init >/dev/null 2>&1 && [ -f "$WORK/devloop.wikis.json" ]; then
  ok "installed wikikit.py runs end to end (registry init)"
else
  no "installed wikikit.py did not run from its host location"
fi
cd "$TMP"

echo "[12d] devloop doctor verifies real files + helper runnability (not just dirs)"
DT="$TMP/doctor"; mkdir -p "$DT"
HOME="$DT" CODEX_HOME="$DT/.codex" "$HERE/devloop" install --host claude --scope home >/dev/null
OUT="$(cd "$DT" && HOME="$DT" CODEX_HOME="$DT/.codex" "$HERE/devloop" doctor 2>&1)"
echo "$OUT" | grep -q "claude (home) — content + helpers" && ok "doctor confirms installed claude is runnable" \
  || no "doctor did not confirm runnable claude install"
# break the install: remove wikikit.py and confirm doctor flags it instead of reporting OK
rm -f "$DT/.claude/tools/wikikit.py"
OUT2="$(cd "$DT" && HOME="$DT" CODEX_HOME="$DT/.codex" "$HERE/devloop" doctor 2>&1)"
echo "$OUT2" | grep -q "wikikit.py missing/not runnable" && ok "doctor flags a broken install (missing helper)" \
  || no "doctor stayed optimistic with wikikit.py removed"
cd "$TMP"

echo "[12e] Kiro layout: skills-only under .kiro/skills/devloop + lean auto-steering (no agents/hooks/mcp)"
KT="$TMP/kiro"; mkdir -p "$KT"
HOME="$KT" "$HERE/devloop" install --host kiro --scope home >/dev/null
K="$KT/.kiro"
# Skills installed namespaced under devloop/, agentskills.io frontmatter (name + description)
sk_ok=1
for s in "$HERE"/skills/*/; do id="$(basename "$s")"
  f="$K/skills/devloop/$id/SKILL.md"
  [ -f "$f" ] && grep -q "^name: $id$" "$f" && grep -q "^description: " "$f" || sk_ok=0
done
[ "$sk_ok" = 1 ] && ok "skills installed under .kiro/skills/devloop with valid frontmatter" || no "Kiro skills missing/invalid"
# Lean auto-steering: inclusion: auto + name/description, sequences roles, no restated bodies
{ head -5 "$K/steering/devloop.md" | grep -q "^inclusion: auto$" \
  && grep -q "^name: devloop$" "$K/steering/devloop.md" \
  && ! grep -q "^## " "$K/steering/devloop.md"; } \
  && ok "steering is a lean inclusion:auto orchestrator (no role bodies)" || no "steering not lean/auto"
# gstack-style skills-only: NO subagents / hooks / settings shipped to Kiro
{ [ ! -e "$K/agents" ] && [ ! -e "$K/hooks" ] && [ ! -e "$K/settings" ] && [ ! -e "$K/specs" ]; } \
  && ok "skills-only: no agents/hooks/settings shipped to Kiro" || no "unexpected Kiro surfaces present"
cd "$TMP"

echo "[12n] install itself is metacharacter-safe (paths with a space AND an apostrophe)"
PQ="$TMP/pro j'q"; mkdir -p "$PQ"   # project dir with space + apostrophe
( cd "$PQ" && HOME="$PQ" CODEX_HOME="$PQ/.codex" "$HERE/devloop" install --host all --scope project >/dev/null 2>&1 )
{ [ -f "$PQ/.claude/skills/context-librarian/SKILL.md" ] \
  && [ -f "$PQ/.agents/skills/story-writer/SKILL.md" ] \
  && [ -f "$PQ/.kiro/skills/devloop/jira-organizer/SKILL.md" ]; } \
  && ok "project-scope install works for a path with space + apostrophe (no eval)" \
  || no "install broke on a space/apostrophe project path"
HQ="$TMP/ho me'q"; mkdir -p "$HQ"   # HOME with space + apostrophe
HOME="$HQ" CODEX_HOME="$HQ/.codex" "$HERE/devloop" install --host all --scope home >/dev/null 2>&1
{ [ -f "$HQ/.kiro/skills/devloop/context-librarian/SKILL.md" ] && [ -f "$HQ/.kiro/steering/devloop.md" ]; } \
  && ok "home-scope install works for a HOME with space + apostrophe" || no "install broke on a space/apostrophe HOME"
cd "$TMP"

echo "[12f] ONE canonical skills/ library at repo root — no per-host skill copies"
n=$(ls -d "$HERE"/skills/*/ 2>/dev/null | wc -l | tr -d ' ')
fork=""
for stale in claude-code codex/skills kiro/skills; do [ -e "$HERE/$stale" ] && fork="$fork $stale"; done
{ [ "$n" -eq 6 ] && [ -f "$HERE/skills/context-librarian/SKILL.md" ] && [ -z "$fork" ]; } \
  && ok "single root skills/ (6 roles), no per-host copies to fork" || no "skills not single-source (n=$n fork:$fork)"
cd "$TMP"

echo "[12o] optional BRD role: skill + /spec-brd command + Claude subagent + in Kiro steering, flagged optional"
{ [ -f "$HERE/skills/business-analyst/SKILL.md" ] \
  && [ -f "$HERE/commands/spec-brd.md" ] \
  && [ -f "$HERE/agents/business-analyst.md" ] \
  && grep -qi 'optional' "$HERE/skills/business-analyst/SKILL.md" \
  && grep -q '^skills: \[business-analyst\]$' "$HERE/agents/business-analyst.md" \
  && grep -q 'business-analyst' "$HERE/kiro/steering/devloop.md"; } \
  && ok "BRD role: skill + /spec-brd + Claude subagent + sequenced in Kiro steering, flagged optional" \
  || no "BRD role not generated/wired correctly"
cd "$TMP"

echo "[12p] authored Codex orchestrator (AGENTS.md) references every role — can't go stale"
missing=""
for rid in $(python3 -c "import json;[print(r['id']) for r in json.load(open('$HERE/core/roles.json'))['roles']]"); do
  grep -q "$rid" "$HERE/codex/AGENTS.md" || missing="$missing $rid"
done
[ -z "$missing" ] && ok "codex/AGENTS.md sequences all roles (incl. business-analyst)" \
  || no "codex/AGENTS.md is stale — missing role(s):$missing"
cd "$TMP"

echo "[12h] Claude plugin manifest: version tracks VERSION, no redundant path keys, has metadata"
VER="$(cat "$HERE/VERSION")"
if python3 - "$HERE" "$VER" <<'PY'
import json,sys
repo,ver=sys.argv[1],sys.argv[2]
pj=json.load(open(f"{repo}/.claude-plugin/plugin.json"))
assert pj.get("name")=="devloop"
assert pj.get("version")==ver, (pj.get("version"),ver)            # stamped, not drifting
for k in ("commands","skills","agents"): assert k not in pj, k    # rely on auto-discovery
for k in ("license","homepage","repository"): assert k in pj, k
mk=json.load(open(f"{repo}/.claude-plugin/marketplace.json"))
assert mk["owner"]["name"]
for pl in mk["plugins"]:
    assert pl["name"] and pl["source"]
    assert pl["source"]==".", pl["source"]                        # plugin root = repo root
PY
then ok "plugin.json stamped to $VER, clean manifest + marketplace valid"; else no "plugin/marketplace manifest invalid"; fi
cd "$TMP"

echo "[12i] build --check fails when plugin.json version drifts from VERSION (then restamps)"
python3 - "$HERE" <<'PY'
import json,sys; p=f"{sys.argv[1]}/.claude-plugin/plugin.json"
d=json.load(open(p)); d["version"]="0.0.0-drift"; json.dump(d,open(p,"w"),indent=2); open(p,"a").write("\n")
PY
if python3 "$HERE/build/build.py" --check >/dev/null 2>&1; then no "build --check missed plugin.json version drift"; else ok "build --check catches plugin.json version drift"; fi
python3 "$HERE/build/build.py" >/dev/null 2>&1   # restamp from VERSION → clean
python3 "$HERE/build/build.py" --check >/dev/null 2>&1 && ok "rebuild restamps plugin.json clean" || no "restamp failed"
cd "$TMP"

echo "[12j] Claude commands carry argument-hint; subagents preload their skill"
ch_ok=1
for c in "$HERE"/commands/*.md; do grep -q '^argument-hint:' "$c" && grep -q '^description:' "$c" || ch_ok=0; done
[ "$ch_ok" = 1 ] && ok "every command has description + argument-hint" || no "command frontmatter incomplete"
ag_ok=1
for a in "$HERE"/agents/*.md; do id="$(basename "$a" .md)"
  grep -q "^skills: \[$id\]$" "$a" && grep -q "Follow the method in the \`$id\` skill" "$a" || ag_ok=0
done
[ "$ag_ok" = 1 ] && ok "every subagent preloads + points at its skill" || no "subagent skill wiring incomplete"
cd "$TMP"

echo "[12q] generated frontmatter descriptions are quoted (valid YAML even with colons)"
# A description value containing ': ' is invalid YAML unless quoted. Every generated
# `description:` line must be a quoted scalar (description: "...").
unquoted="$(grep -rhn '^description: ' "$HERE"/skills/*/SKILL.md "$HERE"/agents/*.md "$HERE"/commands/*.md "$HERE"/kiro/steering/*.md 2>/dev/null | grep -v '^[0-9]*:description: "' || true)"
[ -z "$unquoted" ] && ok "all generated descriptions are quoted YAML scalars" \
  || no "unquoted description (breaks YAML on a colon): $unquoted"
cd "$TMP"

echo "[12r] shared docs are host-neutral (no Claude-only /spec-* in examples/)"
leak="$(grep -rn '/spec-' "$HERE"/examples/ 2>/dev/null || true)"
[ -z "$leak" ] && ok "examples/ docs use host-neutral role names (no /spec-* leak)" \
  || no "Claude-only /spec-* leaked into shared docs: $leak"
cd "$TMP"

echo "[12s] every relative doc link resolves (no broken links in README/docs/examples)"
if python3 - "$HERE" <<'PY'
import os, re, glob, sys
repo = sys.argv[1]
files = ["README.md", "CONTRIBUTING.md", "SECURITY.md", "RELEASE-CHECKLIST.md", "DEVLOOP-QUICK-REF.md"]
files += [os.path.relpath(p, repo) for p in glob.glob(repo + "/docs/**/*.md", recursive=True)]
files += [os.path.relpath(p, repo) for p in glob.glob(repo + "/examples/**/*.md", recursive=True)]
broken = []
for rel in files:
    p = os.path.join(repo, rel)
    if not os.path.isfile(p): continue
    base = os.path.dirname(p)
    for m in re.finditer(r'\]\(([^)]+)\)', open(p).read()):
        t = m.group(1).strip()
        if t.startswith(("http://", "https://", "#", "mailto:")): continue
        t = t.split('#', 1)[0]
        if t and not os.path.exists(os.path.join(base, t)):
            broken.append(f"{rel} -> {t}")
if broken: print("\n".join(broken)); sys.exit(1)
PY
then ok "all relative doc links resolve"; else no "broken relative doc link(s) above"; fi
cd "$TMP"

echo "[13] ingest.py: recursive multi-format extraction (docx + drawio + nested md; image flagged)"
IG="$TMP/ig"; SRCD="$IG/sources"; mkdir -p "$SRCD/sub"
printf '# SOP\nStep one.\n' > "$SRCD/sub/sop.md"
python3 - "$SRCD/spec.docx" <<'PY'
import zipfile,sys; p=sys.argv[1]
z=zipfile.ZipFile(p,'w')
z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
z.writestr('word/document.xml','<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Hello from DOCX</w:t></w:r></w:p></w:body></w:document>')
z.close()
PY
printf '<mxfile><diagram><mxGraphModel><root><mxCell id="2" value="Auth Service"/></root></mxGraphModel></diagram></mxfile>\n' > "$SRCD/arch.drawio"
printf '\x89PNG\r\n' > "$SRCD/shot.png"
python3 "$HERE/tools/ingest.py" "$SRCD" --into "$IG/knowledge/raw" >/dev/null
{ [ -f "$IG/knowledge/raw/sub/sop.md" ] && grep -q "Hello from DOCX" "$IG/knowledge/raw/spec.docx.txt" \
  && grep -q "Auth Service" "$IG/knowledge/raw/arch.drawio.txt" \
  && grep -q "FLAGGED" "$IG/knowledge/raw/_INGEST.md"; } \
  && ok "ingest extracted docx+drawio, recursed subfolder, flagged image" || no "ingest extraction"
cd "$TMP"

echo "[13b] ingest.py --wiki: resolve raw/ via devloop.wikis.json registry (documented path)"
IW="$TMP/igwiki"; mkdir -p "$IW"; cd "$IW"
python3 "$WK" registry init >/dev/null
python3 - <<'PY'
import json
r=json.load(open("devloop.wikis.json"))
r["wikis"]=[{"id":"project","kind":"project","role":"primary",
             "source":{"type":"local","path":"."},"wiki_path":"knowledge/wiki"}]
json.dump(r,open("devloop.wikis.json","w"),indent=2)
PY
mkdir -p src; printf '# Note\nhi\n' > src/note.md
python3 "$HERE/tools/ingest.py" src --wiki project >/dev/null
[ -f "$IW/knowledge/raw/note.md" ] && ok "--wiki resolved raw/ from devloop.wikis.json" \
  || no "--wiki path did not land raw/ via registry"
cd "$TMP"

echo "[13c] devloop init scaffolds a ready-to-run project (minimal registry + sample + jira)"
IT="$TMP/init"; mkdir -p "$IT"
( cd "$IT" && HOME="$IT" "$HERE/devloop" init --sample --jira >/dev/null 2>&1 )
init_ok=1
python3 -c "import json,sys; w=[x['id'] for x in json.load(open(sys.argv[1]))['wikis']]; sys.exit(0 if w==['project'] else 1)" "$IT/devloop.wikis.json" || init_ok=0
for f in knowledge/raw/sso.md knowledge/raw/sftp.md knowledge/raw/email.md devloop.jira.json knowledge/wiki; do
  [ -e "$IT/$f" ] || { init_ok=0; echo "    missing: $f"; }
done
[ "$init_ok" = 1 ] && ok "init: minimal (project-only) registry + scaffolded knowledge/ + seeded sample + jira config" \
  || no "devloop init scaffold incomplete"
# never clobbers an existing registry
printf '{"_sentinel":"keep","version":1,"cache_dir":".devloop/wikis","wikis":[{"id":"project","kind":"project","role":"primary","source":{"type":"local","path":"."},"wiki_path":"knowledge/wiki"}]}\n' > "$IT/devloop.wikis.json"
( cd "$IT" && HOME="$IT" "$HERE/devloop" init >/dev/null 2>&1 )
grep -q '_sentinel' "$IT/devloop.wikis.json" && ok "init never clobbers an existing devloop.wikis.json" || no "init clobbered the registry"
cd "$TMP"

echo "[13d] devloop status reports readiness + chain progress (human + --markdown)"
ST="$TMP/status"; mkdir -p "$ST"
# before init: registry none (capture first — avoids grep -q SIGPIPE under pipefail)
preout="$( cd "$ST" && "$HERE/devloop" status 2>&1 )"
printf '%s' "$preout" | grep -q 'run: devloop init' \
  && ok "status (no registry) tells you to run devloop init" || no "status didn't report missing registry"
( cd "$ST" && HOME="$ST" "$HERE/devloop" init --sample >/dev/null 2>&1 )
printf '# r\n' > "$ST/requirements.md"   # one artifact present, others not
mdout="$( cd "$ST" && "$HERE/devloop" status --markdown 2>&1 )"
{ printf '%s' "$mdout" | grep -q '| Registry | present' \
  && printf '%s' "$mdout" | grep -q 'Sources (project) | 3 new' \
  && printf '%s' "$mdout" | grep -q 'requirements ✓' \
  && printf '%s' "$mdout" | grep -q 'stories –'; } \
  && ok "status --markdown shows registry + sources + per-artifact chain progress" \
  || no "status --markdown output incomplete"
cd "$TMP"

echo "[14] Codex installs the shared Agent Skills to .agents/skills (no deprecated prompts)"
CX="$TMP/codex"; mkdir -p "$CX"
HOME="$CX" CODEX_HOME="$CX/.codex" "$HERE/devloop" install --host codex --scope home >/dev/null
sd="$CX/.agents/skills"
cx_ok=1; diffs=0
for s in "$HERE"/skills/*/SKILL.md; do id="$(basename "$(dirname "$s")")"
  [ -f "$sd/$id/SKILL.md" ] && grep -q "^name: $id$" "$sd/$id/SKILL.md" || cx_ok=0
  cmp -s "$s" "$sd/$id/SKILL.md" || diffs=$((diffs+1))   # installed == the one canonical skill
done
[ "$cx_ok" = 1 ] && ok "Codex installs Agent Skills to .agents/skills with valid frontmatter" || no "Codex skills missing/invalid"
[ "$diffs" = 0 ] && ok "installed Codex skills are the canonical root skills/ (no copy drift)" || no "$diffs Codex skill mismatch(es)"
# AGENTS.md orchestrator landed (home → $CODEX_HOME) and points at skills, not deprecated prompts
{ [ -f "$CX/.codex/AGENTS.md" ] && grep -q 'context-librarian` skill' "$CX/.codex/AGENTS.md" \
  && ! grep -q '/spec-context' "$CX/.codex/AGENTS.md"; } \
  && ok "AGENTS.md orchestrator points at skills (no deprecated /spec-* prompts)" || no "AGENTS.md not migrated"
# The repo no longer ships generated codex prompts
[ ! -e "$HERE/codex/prompts" ] && ok "deprecated codex/prompts removed from the package" || no "codex/prompts still present"
cd "$TMP"

echo
echo "==== smoke test: $PASS passed, $FAIL failed ===="
[ "$FAIL" -eq 0 ]
