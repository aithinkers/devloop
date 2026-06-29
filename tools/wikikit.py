#!/usr/bin/env python3
"""wikikit — deterministic helpers for the DevLoop LLM-Wiki library (no LLM, stdlib only).

The Context Librarian (an LLM agent) does the thinking; wikikit does the bookkeeping:
manage a registry of named wikis, sync git-backed sources, detect changed sources
(SHA256), and lint wikis for broken [[links]] / orphans — including cross-wiki
[[namespace:Concept]] links.

Registry (devloop.wikis.json):
  {
    "version": 1,
    "cache_dir": ".devloop/wikis",
    "wikis": [
      {"id":"project","kind":"project","role":"primary",
       "source":{"type":"local","path":"."}, "wiki_path":"knowledge/wiki"},
      {"id":"integrations","kind":"integrations",
       "source":{"type":"git","url":"<repo>","ref":"main","subpath":"","contains":"sources"},
       "wiki_path":".devloop/wikis/integrations/knowledge/wiki"}
    ]
  }
  source.type: local | git | url      source.contains: sources (compile) | wiki (reference)

Usage:
  wikikit.py registry init [--path devloop.wikis.json]
  wikikit.py registry list [--path ...]
  wikikit.py sync (ID | --all) [--path ...]    # git: clone/pull + report changed files
  wikikit.py scaffold (--wiki ID | DIR)        # create knowledge/ structure
  wikikit.py status   (--wiki ID | DIR)        # new / changed / unchanged raw sources
  wikikit.py commit   (--wiki ID | DIR)        # record source hashes after compiling
  wikikit.py lint     (--wiki ID | DIR | --all)# broken/orphan links (+cross-wiki with --all)
  wikikit.py okf-lint (--wiki ID | DIR)         # check Open Knowledge Format (OKF v0.1) conformance
  wikikit.py export --okf (--wiki ID | DIR) [--out PATH]  # emit a portable OKF bundle
  wikikit.py jira init [--path devloop.jira.json]   # scaffold a Jira config (BA + TECH)
  wikikit.py jira validate [--path ...]             # validate the Jira config

OKF interop: DevLoop wikis are a superset of the Open Knowledge Format
(github.com/GoogleCloudPlatform/knowledge-catalog). `export --okf` rewrites
[[wikilinks]] to portable bundle-relative markdown links, maps `sources:`
frontmatter + the sources index into per-concept `# Citations`, and stamps
`okf_version` on the root index — producing a bundle other OKF tools can read.
"""
import sys, os, re, json, hashlib, subprocess, time

# ----------------------------- helpers ---------------------------------------
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(8192), b""):
            h.update(c)
    return h.hexdigest()

def opt(args, name, default=None):
    return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else default

def reg_path(args):
    return os.path.abspath(opt(args, "--path", "devloop.wikis.json"))

def load_registry(args):
    p = reg_path(args)
    if not os.path.exists(p):
        sys.exit(f"No registry at {p} — run: wikikit.py registry init")
    return p, json.load(open(p))

def save_registry(p, reg):
    json.dump(reg, open(p, "w"), indent=2)

def find_wiki(reg, wid):
    for w in reg["wikis"]:
        if w["id"] == wid:
            return w
    sys.exit(f"No wiki '{wid}' in registry")

def knowledge_dir_for(reg_dir, w):
    # knowledge/ is the parent of wiki_path (.../knowledge/wiki -> .../knowledge)
    wp = os.path.join(reg_dir, w["wiki_path"])
    return os.path.dirname(wp)

def resolve_dir(args):
    """Return the knowledge/ dir from --wiki ID or a positional DIR (default ./knowledge)."""
    if "--wiki" in args:
        p, reg = load_registry(args)
        w = find_wiki(reg, opt(args, "--wiki"))
        return knowledge_dir_for(os.path.dirname(p) or ".", w)
    pos = [a for a in args[2:] if not a.startswith("--")]
    return os.path.abspath(pos[0]) if pos else os.path.abspath("knowledge")

def raw_files(k):
    """All files under raw/, recursively (subfolders included)."""
    r = os.path.join(k, "raw"); out = []
    for dp, _, fs in os.walk(r):
        for f in fs:
            out.append(os.path.join(dp, f))
    return sorted(out)

def rawname(k, p):
    """Stable key = path relative to raw/ (so files in subfolders don't collide)."""
    return os.path.relpath(p, os.path.join(k, "raw"))

def state_file(k):
    return os.path.join(k, ".wiki-state.json")

def load_state(k):
    p = state_file(k)
    return json.load(open(p)) if os.path.exists(p) else {}

def save_state(k, s):
    json.dump(s, open(state_file(k), "w"), indent=2)

def norm(s):  # Obsidian-style link resolution: space/hyphen/underscore + case insensitive
    return re.sub(r"[\s_-]+", " ", s.strip().lower())

# ----------------------------- registry --------------------------------------
def registry(args):
    sub = args[2] if len(args) > 2 else ""
    if sub == "init":
        p = reg_path(args)
        if os.path.exists(p):
            sys.exit(f"{p} already exists")
        project = {"id": "project", "kind": "project", "role": "primary",
                   "source": {"type": "local", "path": "."}, "wiki_path": "knowledge/wiki"}
        # --minimal: just the local project wiki (clean starting point for `devloop init`).
        shared = [
            {"id": "integrations", "kind": "integrations",
             "source": {"type": "git", "url": "<repo-url>", "ref": "main",
                        "subpath": "", "contains": "sources"},
             "wiki_path": ".devloop/wikis/integrations/knowledge/wiki"},
            {"id": "devops", "kind": "devops",
             "source": {"type": "git", "url": "<repo-url>", "ref": "main",
                        "subpath": "", "contains": "sources"},
             "wiki_path": ".devloop/wikis/devops/knowledge/wiki"},
            {"id": "app-codebase", "kind": "codebase",
             "source": {"type": "git", "url": "<repo-url>", "ref": "main",
                        "subpath": "", "contains": "sources"},
             "wiki_path": ".devloop/wikis/app-codebase/knowledge/wiki"},
        ]
        skel = {"version": 1, "cache_dir": ".devloop/wikis",
                "wikis": [project] if "--minimal" in args else [project, *shared]}
        save_registry(p, skel)
        print(f"✓ wrote {p}" + ("" if "--minimal" in args else
              " — edit it to point at your real sources, then: wikikit.py sync --all"))
        return 0
    if sub == "list":
        p, reg = load_registry(args)
        print(f"Registry: {p}  (cache_dir={reg.get('cache_dir')})")
        for w in reg["wikis"]:
            src = w["source"]
            loc = src.get("url") or src.get("path") or "—"
            ls = w.get("last_synced", {})
            stamp = f" synced {ls.get('sha','')[:8]} @ {ls.get('time','')}" if ls else " (never synced)"
            role = f" [{w['role']}]" if w.get("role") else ""
            print(f"  - {w['id']:<14} kind={w['kind']:<12} {src['type']:<5} {loc}{role}{stamp}")
        return 0
    sys.exit("usage: wikikit.py registry (init|list)")

# ------------------------------- sync ----------------------------------------
class _GitResult:
    def __init__(self, returncode, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr

def git(*a):
    try:
        return subprocess.run(["git", *a], capture_output=True, text=True)
    except FileNotFoundError:
        return _GitResult(127, stderr="git is not installed")

INGEST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ingest.py")

def _git_err(r):
    return r.stderr.strip().splitlines()[-1] if r.stderr and r.stderr.strip() else "error"

def sync_one(reg_dir, reg, w):
    """Refresh one wiki's raw sources. Returns True on success, False on a fatal error.
    Only `git` sources are auto-fetched; `local` folders are pulled in with ingest.py and
    `url` sources are fetched/pasted manually (both reported, never a hard failure)."""
    src = w["source"]
    if src["type"] == "url":
        urls = src.get("url") or src.get("urls") or []
        n = len(urls) if isinstance(urls, list) else 1
        print(f"  {w['id']}: url source ({n} link(s)) — fetch/paste into raw/ manually, then `commit`")
        return True
    if src["type"] == "local":
        k = knowledge_dir_for(reg_dir, w)
        if os.path.isdir(os.path.join(k, "raw")) and raw_files(k):
            st = load_state(k); changed = [rawname(k, p) for p in raw_files(k)
                                           if st.get(rawname(k, p)) != sha(p)]
            print(f"  {w['id']}: local — {len(changed)} source(s) new/changed" +
                  (": " + ", ".join(changed) if changed else ""))
        else:
            # No raw material yet. `sync` does not auto-walk a local folder (it could be the
            # repo root); tell the developer the exact ingest command for source.path.
            path = src.get("path")
            hint = (f"python3 {INGEST} {path} --wiki {w['id']}" if path
                    else "add files under raw/ or run ingest.py")
            print(f"  {w['id']}: local — no raw/ sources yet. Ingest first:\n      {hint}")
        return True
    # git — the only source type `sync` fetches automatically
    dest = os.path.join(reg_dir, reg.get("cache_dir", ".devloop/wikis"), w["id"])
    ref = src.get("ref", "main")
    prev = w.get("last_synced", {}).get("sha")
    if not os.path.isdir(os.path.join(dest, ".git")):
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        r = git("clone", "--depth", "50", "--branch", ref, src["url"], dest)
        if r.returncode:
            print(f"  {w['id']}: clone FAILED — {_git_err(r)}")
            return False
        action = "cloned"
    else:
        for op in (("fetch", "--depth", "50", "origin", ref), ("checkout", ref),
                   ("reset", "--hard", f"origin/{ref}")):
            r = git("-C", dest, *op)
            if r.returncode:
                print(f"  {w['id']}: {op[0]} FAILED — {_git_err(r)}")
                return False
        action = "pulled"
    head = git("-C", dest, "rev-parse", "HEAD").stdout.strip()
    changed = []
    if prev and prev != head:
        d = git("-C", dest, "diff", "--name-only", prev, head)
        changed = [l for l in d.stdout.splitlines() if l.strip()]
    w["last_synced"] = {"sha": head, "time": time.strftime("%Y-%m-%dT%H:%M:%S")}
    msg = f"  {w['id']}: {action} {head[:8]}"
    if prev == head:
        msg += " (no change)"
    elif prev:
        msg += f" — {len(changed)} file(s) changed since last build"
    print(msg)
    return True

def sync(args):
    p, reg = load_registry(args)
    reg_dir = os.path.dirname(p) or "."
    targets = reg["wikis"] if "--all" in args else \
        [find_wiki(reg, [a for a in args[2:] if not a.startswith("--")][0])]
    print("Syncing:")
    failed = [w["id"] for w in targets if not sync_one(reg_dir, reg, w)]
    save_registry(p, reg)
    if failed:
        print(f"sync: {len(failed)} wiki(s) FAILED — {', '.join(failed)}")
        return 1
    return 0

# --------------------------- per-wiki ops ------------------------------------
def scaffold(args):
    k = resolve_dir(args)
    for d in ["raw", "wiki/concepts", "wiki/sources", "sources"]:
        os.makedirs(os.path.join(k, d), exist_ok=True)
    idx = os.path.join(k, "wiki", "index.md")
    if not os.path.exists(idx):
        open(idx, "w").write("# Knowledge Wiki — Index\n")
    man = os.path.join(k, "sources", "INDEX.md")
    if not os.path.exists(man):
        open(man, "w").write("# Source Index\n\n| ID | Title | Type | Origin | Owner | Date | Summary |\n|---|---|---|---|---|---|---|\n")
    if not os.path.exists(state_file(k)):
        save_state(k, {})
    print(f"✓ scaffolded {k}")
    return 0

def status(args):
    k = resolve_dir(args); st = load_state(k); new = chg = same = 0
    for p in raw_files(k):
        name = rawname(k, p); h = sha(p)
        if name not in st:
            print(f"NEW      {name}"); new += 1
        elif st[name] != h:
            print(f"CHANGED  {name}"); chg += 1
        else:
            same += 1
    print(f"-- {new} new, {chg} changed, {same} unchanged --")
    return 0

def commit(args):
    k = resolve_dir(args)
    st = {rawname(k, p): sha(p) for p in raw_files(k)}
    save_state(k, st)
    print(f"✓ recorded {len(st)} source hashes for {k}")
    return 0

def _articles(wiki_dir):
    arts = {}
    for root, _, files in os.walk(wiki_dir):
        for f in files:
            if f.endswith(".md"):
                arts[os.path.splitext(f)[0]] = os.path.join(root, f)
    return arts

def lint(args):
    if "--all" in args:
        return lint_all(args)
    k = resolve_dir(args)
    wiki = os.path.join(k, "wiki")
    arts = _articles(wiki)
    by_norm = {norm(t): t for t in arts}
    link_re = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
    inbound = {t: 0 for t in arts}
    broken = []; problems = 0
    for title, path in arts.items():
        for tgt in link_re.findall(open(path, encoding="utf-8", errors="ignore").read()):
            tgt = tgt.strip()
            if ":" in tgt:   # cross-wiki link — only checkable via --all
                continue
            if norm(tgt) in by_norm:
                inbound[by_norm[norm(tgt)]] += 1
            elif norm(tgt) not in ("index", "glossary"):
                broken.append((title, tgt))
    if broken:
        problems += len(broken); print("Broken wikilinks:")
        for s, t in broken:
            print(f"  [[{t}]] in {s}.md → no such article")
    orphans = [t for t, n in inbound.items()
               if n == 0 and os.path.dirname(arts[t]).endswith("concepts")]
    if orphans:
        problems += len(orphans); print("Orphan concept articles (no inbound links):")
        for t in orphans:
            print(f"  {t}.md")
    print(f"-- lint {os.path.basename(k)}: {problems} issue(s), {len(arts)} articles --")
    return 1 if problems else 0

def lint_all(args):
    p, reg = load_registry(args)
    reg_dir = os.path.dirname(p) or "."
    # build namespace -> normalized-concept-set
    ns = {}
    for w in reg["wikis"]:
        wd = os.path.join(reg_dir, w["wiki_path"])
        ns[w["id"]] = {norm(t) for t in _articles(wd)}
    link_re = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
    problems = 0
    for w in reg["wikis"]:
        wd = os.path.join(reg_dir, w["wiki_path"])
        for title, path in _articles(wd).items():
            for tgt in link_re.findall(open(path, encoding="utf-8", errors="ignore").read()):
                if ":" not in tgt:
                    continue
                space, concept = tgt.split(":", 1)
                space = space.strip()
                if space not in ns:
                    print(f"  [[{tgt}]] in {w['id']}/{title}.md → unknown wiki '{space}'")
                    problems += 1
                elif norm(concept) not in ns[space] and norm(concept) not in ("index", "glossary"):
                    print(f"  [[{tgt}]] in {w['id']}/{title}.md → no '{concept}' in wiki '{space}'")
                    problems += 1
    print(f"-- cross-wiki lint: {problems} issue(s) across {len(reg['wikis'])} wikis --")
    return 1 if problems else 0

# -------------------------------- jira ---------------------------------------
def jira_path(args):
    return os.path.abspath(opt(args, "--path", "devloop.jira.json"))

ARTIFACTS = ["initiative", "requirement", "decision", "epic", "story", "task", "bug", "subtask"]

def jira(args):
    sub = args[2] if len(args) > 2 else ""
    if sub == "init":
        p = jira_path(args)
        if os.path.exists(p):
            sys.exit(f"{p} already exists")
        skel = {
            "version": 1,
            "instance": "https://your-org.atlassian.net",
            "projects": [
                {"key": "BA", "name": "Business Analysis",
                 "purpose": "Discovery: requirements, decisions, initiatives",
                 "issue_types": ["Initiative", "Requirement", "Decision", "Epic"]},
                {"key": "TECH", "name": "Engineering Delivery",
                 "purpose": "Implementation work",
                 "issue_types": ["Epic", "Story", "Task", "Bug", "Sub-task"]},
            ],
            "routing": {
                "initiative": {"project": "BA", "type": "Initiative"},
                "requirement": {"project": "BA", "type": "Requirement"},
                "decision": {"project": "BA", "type": "Decision"},
                "epic": {"project": "TECH", "type": "Epic"},
                "story": {"project": "TECH", "type": "Story"},
                "task": {"project": "TECH", "type": "Task"},
                "bug": {"project": "TECH", "type": "Bug"},
                "subtask": {"project": "TECH", "type": "Sub-task"},
            },
            "components": [],
            "labels": ["security", "tech-debt", "frontend", "backend", "spike"],
            "priority_map": {"Must": "Highest", "Should": "High", "Could": "Medium", "Won't": "Lowest"},
            "custom_fields": [{"name": "Story Points", "applies_to": ["Story", "Task"]},
                              {"name": "Epic Link", "applies_to": ["Story", "Task", "Bug"]}],
            "hierarchy": ["Initiative", "Epic", "Story|Task|Bug", "Sub-task"],
        }
        json.dump(skel, open(p, "w"), indent=2)
        print(f"✓ wrote {p} — edit it to match your real Jira, then: wikikit.py jira validate")
        return 0
    if sub == "validate":
        p = jira_path(args)
        if not os.path.exists(p):
            sys.exit(f"No jira config at {p} — run: wikikit.py jira init")
        try:
            cfg = json.load(open(p))
        except json.JSONDecodeError as e:
            print(f"  invalid JSON: {e}"); print("-- jira validate: 1 issue --"); return 1
        issues = []
        projects = {pr.get("key"): pr for pr in cfg.get("projects", [])}
        if not projects:
            issues.append("no projects defined")
        for pr in cfg.get("projects", []):
            if not pr.get("key") or not pr.get("name"):
                issues.append(f"project missing key/name: {pr}")
            if not pr.get("issue_types"):
                issues.append(f"project {pr.get('key')} has no issue_types")
        routing = cfg.get("routing", {})
        for kind, tgt in routing.items():
            if kind not in ARTIFACTS:
                issues.append(f"routing has unknown artifact '{kind}'")
            proj = projects.get(tgt.get("project"))
            if not proj:
                issues.append(f"routing.{kind} → project '{tgt.get('project')}' not defined")
            elif tgt.get("type") not in proj.get("issue_types", []):
                issues.append(f"routing.{kind} → type '{tgt.get('type')}' not in project {proj['key']} issue_types")
        for c in cfg.get("components", []):
            if c.get("project") and c["project"] not in projects:
                issues.append(f"component '{c.get('name')}' → unknown project '{c['project']}'")
        moscow = {"Must", "Should", "Could", "Won't"}
        for k in cfg.get("priority_map", {}):
            if k not in moscow:
                issues.append(f"priority_map has non-MoSCoW key '{k}'")
        for kind in ("story", "epic", "bug"):
            if kind not in routing:
                issues.append(f"routing missing recommended kind '{kind}'")
        for i in issues:
            print(f"  {i}")
        print(f"-- jira validate: {len(issues)} issue(s), {len(projects)} project(s) --")
        return 1 if issues else 0
    sys.exit("usage: wikikit.py jira (init|validate)")

# ------------------------------- OKF interop ---------------------------------
# Open Knowledge Format v0.1 (github.com/GoogleCloudPlatform/knowledge-catalog):
# markdown + YAML frontmatter "knowledge bundles" with a required `type`, standard
# (bundle-relative) markdown links, and an `index.md` with `okf_version` at the root.
# DevLoop's wiki is a superset; these commands check conformance and emit a portable bundle.

def _split_fm(text):
    """Return (frontmatter_inner, body). frontmatter_inner is None when absent."""
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            rest = text[end + 4:]
            return text[4:end], rest[1:] if rest.startswith("\n") else rest
    return None, text

def _join_fm(fm, body):
    return body if fm is None else f"---\n{fm}\n---\n\n{body.lstrip(chr(10))}"

def _fm_get(fm, key):
    if not fm:
        return None
    m = re.search(rf"^{re.escape(key)}:\s*(.+?)\s*(?:#.*)?$", fm, re.M)
    return m.group(1).strip() if m else None

def _fm_set(fm, key, val):
    line = f"{key}: {val}"
    if fm is None:
        return line
    if re.search(rf"^{re.escape(key)}:", fm, re.M):
        return re.sub(rf"^{re.escape(key)}:.*$", line, fm, count=1, flags=re.M)
    return fm + "\n" + line

def _load_sources(k):
    """Parse knowledge/sources/INDEX.md → {S-ID: 'Title — Location — Summary'}."""
    p = os.path.join(k, "sources", "INDEX.md")
    out = {}
    if not os.path.exists(p):
        return out
    for line in open(p, encoding="utf-8", errors="ignore"):
        cells = [c.strip() for c in line.split("|")]
        if len(cells) >= 3 and re.fullmatch(r"S\d+", cells[1] or ""):
            title = cells[2] if len(cells) > 2 else ""
            loc = cells[4] if len(cells) > 4 else ""
            summary = cells[7] if len(cells) > 7 else ""
            out[cells[1]] = " — ".join(x for x in (title, loc, summary) if x) or cells[1]
    return out

def _citations(fm, src):
    sids = re.findall(r"S\d+", _fm_get(fm, "sources") or "")
    if not sids:
        return ""
    return "\n".join(f"[{s}] {src.get(s, '(see sources index)')}" for s in sids) + "\n"

def _rewrite_wikilinks(text, by_norm):
    """[[Concept]] / [[Concept|alias]] → bundle-relative markdown links.
    Cross-wiki [[ns:Concept]] and unresolved links render as plain text (OKF bundles
    are self-contained, and we never fabricate a target path)."""
    link_re = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
    def repl(m):
        tgt = m.group(1).strip()
        alias = (m.group(2) or m.group(1)).strip()
        if ":" in tgt:
            return alias
        f = by_norm.get(norm(tgt))
        return f"[{alias}](/{f})" if f else alias
    return link_re.sub(repl, text)

def okf_lint(args):
    k = resolve_dir(args)
    wiki = os.path.join(k, "wiki")
    if not os.path.isdir(wiki):
        print(f"no wiki at {wiki}"); return 1
    reserved = {"index.md", "log.md"}
    arts = _articles(wiki)
    problems = 0
    for path in arts.values():
        if os.path.basename(path) in reserved:
            continue
        fm, _ = _split_fm(open(path, encoding="utf-8", errors="ignore").read())
        if not _fm_get(fm, "type"):
            problems += 1
            print(f"  {os.path.relpath(path, wiki)} → missing required OKF `type` frontmatter")
    blob = "".join(open(p, encoding="utf-8", errors="ignore").read() for p in arts.values())
    wl = len(re.findall(r"\[\[[^\]]+\]\]", blob))
    if wl:
        print(f"  note: {wl} [[wikilink]](s) present — not OKF-portable; run `export --okf` for a portable bundle")
    idx = arts.get("index")
    if idx:
        ifm, _ = _split_fm(open(idx, encoding="utf-8", errors="ignore").read())
        if not _fm_get(ifm, "okf_version"):
            print("  note: root index.md has no `okf_version` — `export --okf` stamps it")
    print(f"-- okf-lint {os.path.basename(k)}: {problems} conformance issue(s), {len(arts)} files --")
    return 1 if problems else 0

def export(args):
    if "--okf" not in args:
        sys.exit("usage: wikikit.py export --okf (--wiki ID | DIR) [--out PATH]")
    k = resolve_dir(args)
    wiki = os.path.join(k, "wiki")
    if not os.path.isdir(wiki):
        print(f"no wiki at {wiki}"); return 1
    out = os.path.abspath(opt(args, "--out") or os.path.join(k, "okf-export"))
    arts = _articles(wiki)
    by_norm = {norm(n): os.path.relpath(p, wiki).replace(os.sep, "/")
               for n, p in arts.items()}
    src = _load_sources(k)
    n = 0
    for name, path in arts.items():
        relpath = os.path.relpath(path, wiki).replace(os.sep, "/")
        fm, body = _split_fm(open(path, encoding="utf-8", errors="ignore").read())
        body = _rewrite_wikilinks(body, by_norm)
        if relpath == "index.md":
            fm = _fm_set(fm, "okf_version", '"0.1"')
        else:
            cites = _citations(fm, src)
            if cites and "# Citations" not in body:
                body = body.rstrip() + "\n\n# Citations\n" + cites
        dest = os.path.join(out, relpath)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, "w", encoding="utf-8").write(_join_fm(fm, body))
        n += 1
    print(f"✓ OKF bundle: {out} ({n} files, okf_version 0.1)")
    print("  [[wikilinks]] → bundle-relative markdown links; sources → per-concept # Citations.")
    return 0

# -------------------------------- main ---------------------------------------
def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    cmd = sys.argv[1]
    table = {"registry": registry, "sync": sync, "scaffold": scaffold,
             "status": status, "commit": commit, "lint": lint, "jira": jira,
             "okf-lint": okf_lint, "export": export}
    if cmd not in table:
        print(__doc__); sys.exit(2)
    sys.exit(table[cmd](sys.argv) or 0)

if __name__ == "__main__":
    main()
