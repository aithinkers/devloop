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

echo "[12e] Kiro 0.9 layout: install lands skills + subagents + auto-steering + valid hooks"
KT="$TMP/kiro"; mkdir -p "$KT"
HOME="$KT" "$HERE/devloop" install --host kiro --scope home >/dev/null
K="$KT/.kiro"
# Agent Skills: name==folder, agentskills.io frontmatter (name + description)
sk_ok=1
for s in "$HERE"/kiro/skills/*/; do id="$(basename "$s")"
  f="$K/skills/$id/SKILL.md"
  [ -f "$f" ] && grep -q "^name: $id$" "$f" && grep -q "^description: " "$f" || sk_ok=0
done
[ "$sk_ok" = 1 ] && ok "all role skills installed with valid SKILL.md frontmatter" || no "Kiro skills missing/invalid"
# Subagents present with a Kiro tools: [..] line and a pointer to the skill (no restated body)
{ [ -f "$K/agents/context-librarian.md" ] && grep -q "^tools: \[" "$K/agents/context-librarian.md" \
  && grep -q "Follow the method in the \`context-librarian\` Agent Skill" "$K/agents/context-librarian.md"; } \
  && ok "Kiro subagent points at its skill (no duplicated body)" || no "Kiro subagent missing/!pointer"
# Lean auto-steering: inclusion: auto + name/description, and it does NOT restate a full body
{ head -5 "$K/steering/devloop.md" | grep -q "^inclusion: auto$" \
  && grep -q "^name: devloop$" "$K/steering/devloop.md" \
  && ! grep -q "^## " "$K/steering/devloop.md"; } \
  && ok "steering is a lean inclusion:auto orchestrator (no role bodies)" || no "steering not lean/auto"
# Hooks: valid JSON, userTriggered + runCommand
hk_ok=1
for h in "$K"/hooks/*.kiro.hook; do
  python3 -c "import json,sys; d=json.load(open(sys.argv[1])); assert d['when']['type']=='userTriggered'; assert d['then']['type']=='runCommand'; assert d['enabled'] is True" "$h" 2>/dev/null || hk_ok=0
done
[ "$hk_ok" = 1 ] && [ -f "$K/hooks/devloop-wiki-lint.kiro.hook" ] \
  && ok "Kiro hooks are valid userTriggered/runCommand JSON" || no "Kiro hooks invalid/missing"
# No leftover pre-0.9 artifacts
[ ! -e "$K/specs/_template" ] && ok "no stale specs/_template installed" || no "stale specs/_template present"
# MCP example: valid JSON, schema-clean (only mcpServers), SharePoint shipped DISABLED, no secrets
if python3 - "$K/settings/mcp.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
assert list(d)==["mcpServers"], d
s=d["mcpServers"]["sharepoint"]
assert s["disabled"] is True
assert s["env"]["SHAREPOINT_TOKEN"]=="${SHAREPOINT_TOKEN}"   # env ref, not a literal secret
PY
then ok "MCP example is valid, disabled, secret-free"; else no "MCP example invalid/enabled/leaky"; fi
cd "$TMP"

echo "[12g] Kiro MCP config is user-owned: install never clobbers an existing mcp.json"
MT="$TMP/kiro-mcp"; mkdir -p "$MT/.kiro/settings"
printf '{"mcpServers":{"mine":{"command":"node","args":["x.js"]}}}\n' > "$MT/.kiro/settings/mcp.json"
( cd "$MT" && HOME="$MT" "$HERE/devloop" install --host kiro --scope project >/dev/null 2>&1 )
grep -q '"mine"' "$MT/.kiro/settings/mcp.json" && ok "existing mcp.json preserved on install" || no "install clobbered user mcp.json"
cd "$TMP"

echo "[12f] Kiro skill bodies are byte-identical to the Claude skill bodies (single source)"
diffs=0
for s in "$HERE"/kiro/skills/*/SKILL.md; do id="$(basename "$(dirname "$s")")"
  cmp -s "$s" "$HERE/claude-code/skills/$id/SKILL.md" || diffs=$((diffs+1))
done
[ "$diffs" = 0 ] && ok "Kiro & Claude skill SKILL.md bodies match (no content fork)" || no "$diffs skill body mismatch(es)"
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

echo "[14] codex prompts are self-contained: every shared/<file> a role body cites is inlined"
if REPO="$HERE" python3 - <<'PY'
import json, os, re, sys
repo = os.environ["REPO"]
roles = {r["id"]: r for r in json.load(open(f"{repo}/core/roles.json"))["roles"]}
adapter = json.load(open(f"{repo}/codex/adapter.json"))
gaps = []
for rid, r in roles.items():
    cmd = r["command"]
    spec = adapter["prompts"].get(cmd)
    if spec is None:
        continue
    body = open(f"{repo}/core/{r['body']}").read()
    cited = set(re.findall(r'shared/([A-Za-z0-9._-]+)', body))
    inlined = set(spec.get("includes", []))
    for f in sorted(cited - inlined):
        gaps.append(f"{cmd}:{f}")
if gaps:
    print(" ".join(gaps)); sys.exit(1)
PY
then ok "no codex prompt cites an un-inlined shared/ file"; else no "codex un-inlined shared refs (see above)"; fi
cd "$TMP"

echo
echo "==== smoke test: $PASS passed, $FAIL failed ===="
[ "$FAIL" -eq 0 ]
