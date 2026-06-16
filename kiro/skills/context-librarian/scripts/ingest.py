#!/usr/bin/env python3
"""ingest — recursively normalize a sources tree into a wiki's raw/ as plain text.

The Context Librarian compiles the wiki; ingest does the boring extraction first. It walks
SOURCES recursively (all subfolders), pulls text out of common document and diagram formats,
and writes normalized .txt next to a mirror of the source tree under raw/. Anything it can't
extract (scanned PDFs, raster images) is FLAGGED in the manifest so the agent can read it
with vision/OCR instead.

No third-party dependencies are required:
  text/markdown/csv/json/yaml/html/rst/adoc/log  → copied / de-tagged          (stdlib)
  .docx .pptx .xlsx                               → text via zip + XML          (stdlib)
  .drawio (and .drawio.xml)                       → node labels (de/compressed) (stdlib)
  .vsdx  (Visio)                                  → shape text via zip + XML    (stdlib)
  .svg                                            → <text> elements             (stdlib)
  .pdf                                            → pdftotext or pypdf IF present, else FLAG
  images (.png/.jpg/.tiff/…), unknown binary      → FLAG (read via agent vision/OCR)

Usage:
  ingest.py SOURCES_DIR --into RAW_DIR
  ingest.py SOURCES_DIR --wiki ID [--registry devloop.wikis.json]   # resolve raw/ via registry
"""
import os, sys, re, html, json, zipfile, shutil, subprocess
import xml.etree.ElementTree as ET

TEXT_EXT = {".md", ".markdown", ".txt", ".text", ".csv", ".tsv", ".json", ".yaml",
            ".yml", ".rst", ".adoc", ".asciidoc", ".log", ".ini", ".toml", ".org"}
HTML_EXT = {".html", ".htm", ".xhtml"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".webp", ".heic"}

def localname(tag): return tag.split("}")[-1]

def office_text(xml_bytes, text_tag, para_tag):
    """Join <text_tag> contents in document order, newline at each <para_tag>."""
    try: root = ET.fromstring(xml_bytes)
    except ET.ParseError: return ""
    buf = []
    for el in root.iter():
        t = localname(el.tag)
        if t == para_tag: buf.append("\n")
        elif t == text_tag and el.text: buf.append(el.text)
    return "".join(buf).strip()

def from_zip(path, members_glob, text_tag, para_tag):
    out = []
    with zipfile.ZipFile(path) as z:
        for n in sorted(z.namelist()):
            if re.search(members_glob, n):
                out.append(office_text(z.read(n), text_tag, para_tag))
    return "\n\n".join(x for x in out if x)

def docx_text(p): return from_zip(p, r"^word/document\.xml$", "t", "p")
def pptx_text(p): return from_zip(p, r"^ppt/slides/slide\d+\.xml$", "t", "p")
def xlsx_text(p): return from_zip(p, r"^xl/sharedStrings\.xml$", "t", "si")

def vsdx_text(p):
    out = []
    with zipfile.ZipFile(path := p) as z:
        for n in sorted(z.namelist()):
            if re.search(r"^visio/pages/page\d+\.xml$", n):
                try: root = ET.fromstring(z.read(n))
                except ET.ParseError: continue
                for el in root.iter():
                    if localname(el.tag) == "Text":
                        txt = "".join(el.itertext()).strip()
                        if txt: out.append(txt)
    return "\n".join(out)

def _inflate(s):
    import base64, zlib, urllib.parse
    try:
        return urllib.parse.unquote(zlib.decompress(base64.b64decode(s), -15).decode("utf-8", "ignore"))
    except Exception:
        return None

def _cells(xml_text):
    vals = []
    try: root = ET.fromstring(xml_text)
    except ET.ParseError: return vals
    for c in root.iter():
        if localname(c.tag) == "mxCell" and c.get("value"):
            vals.append(c.get("value"))
    return vals

def drawio_text(p):
    raw = open(p, "rb").read().decode("utf-8", "ignore")
    vals = _cells(raw)                       # uncompressed diagrams
    try: root = ET.fromstring(raw)
    except ET.ParseError: root = None
    if root is not None:
        for d in root.iter():
            if localname(d.tag) == "diagram" and (d.text or "").strip() and "<" not in (d.text or "").strip()[:1]:
                dec = _inflate(d.text.strip())
                if dec: vals += _cells(dec)
    clean = [re.sub(r"<[^>]+>", " ", html.unescape(v)).strip() for v in vals]
    return "\n".join(x for x in clean if x)

def svg_text(p):
    try: root = ET.fromstring(open(p, "rb").read())
    except ET.ParseError: return ""
    return "\n".join("".join(e.itertext()).strip() for e in root.iter()
                     if localname(e.tag) in ("text", "tspan") and "".join(e.itertext()).strip())

def html_text(p):
    t = open(p, encoding="utf-8", errors="ignore").read()
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    return html.unescape(re.sub(r"<[^>]+>", " ", t))

def pdf_text(p):
    if shutil.which("pdftotext"):
        r = subprocess.run(["pdftotext", "-layout", p, "-"], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip(): return r.stdout
    try:
        import pypdf
        return "\n".join((pg.extract_text() or "") for pg in pypdf.PdfReader(p).pages)
    except Exception:
        return ""   # scanned or no extractor → flag

EXTRACTORS = {".docx": docx_text, ".pptx": pptx_text, ".xlsx": xlsx_text,
              ".vsdx": vsdx_text, ".drawio": drawio_text, ".svg": svg_text, ".pdf": pdf_text}

def raw_dir(args):
    if "--wiki" in args:
        reg = args[args.index("--registry") + 1] if "--registry" in args else "devloop.wikis.json"
        if not os.path.exists(reg): sys.exit(f"registry not found: {reg}")
        wid = args[args.index("--wiki") + 1]
        for w in json.load(open(reg))["wikis"]:
            if w["id"] == wid:
                return os.path.join(os.path.dirname(os.path.abspath(reg)) or ".",
                                    os.path.dirname(w["wiki_path"]), "raw")
        sys.exit(f"no wiki '{wid}' in {reg}")
    if "--into" in args: return os.path.abspath(args[args.index("--into") + 1])
    sys.exit("specify --into RAW_DIR or --wiki ID")

def main():
    if len(sys.argv) < 2 or sys.argv[1].startswith("-"):
        print(__doc__); sys.exit(2)
    src = os.path.abspath(sys.argv[1])
    if not os.path.isdir(src): sys.exit(f"not a directory: {src}")
    raw = raw_dir(sys.argv)
    os.makedirs(raw, exist_ok=True)
    rows, n_ok, n_flag = [], 0, 0
    for dp, _, files in os.walk(src):
        for f in sorted(files):
            sp = os.path.join(dp, f)
            rel = os.path.relpath(sp, src)
            ext = os.path.splitext(f)[1].lower()
            try:
                if ext in TEXT_EXT:
                    dst = os.path.join(raw, rel); os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copyfile(sp, dst); rows.append((rel, ext[1:] or "text", "copied")); n_ok += 1; continue
                if ext in HTML_EXT:           text = html_text(sp); kind = "html"
                elif ext in EXTRACTORS:       text = EXTRACTORS[ext](sp); kind = ext[1:]
                elif ext in IMAGE_EXT:        text = ""; kind = "image"
                else:                          text = ""; kind = "binary/unknown"
            except Exception as e:
                text, kind = "", f"error:{type(e).__name__}"
            if text and text.strip():
                dst = os.path.join(raw, rel + ".txt"); os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(dst, "w", encoding="utf-8") as fh:
                    fh.write(f"# Extracted from {rel} ({kind})\n\n{text.strip()}\n")
                rows.append((rel, kind, "extracted")); n_ok += 1
            else:
                reason = "read via agent vision/OCR" if (ext in IMAGE_EXT or ext == ".pdf") else "unsupported"
                rows.append((rel, kind, f"FLAGGED ({reason})")); n_flag += 1
    with open(os.path.join(raw, "_INGEST.md"), "w", encoding="utf-8") as fh:
        fh.write("# Ingest manifest\n\n| Source | Type | Status |\n|---|---|---|\n")
        for r, k, s in rows: fh.write(f"| {r} | {k} | {s} |\n")
    print(f"ingested {len(rows)} file(s) → {raw}")
    print(f"  {n_ok} extracted/copied, {n_flag} flagged for agent vision/OCR")
    if n_flag:
        for r, k, s in rows:
            if s.startswith("FLAGGED"): print(f"  ⚑ {r} ({k})")

if __name__ == "__main__":
    main()
