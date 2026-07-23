#!/usr/bin/env python3
"""artifact-diff.py — materiality-first content diff for Office/PDF, stdlib only.

The reconciliation watcher only cares about changes that alter WHAT A FOLDER
CONTAINS. A retuned formula constant, a reworded bullet or a fixed typo does not
change what's inside — it should not trigger a doc update or an ask. A new tab, a
new slide/section, a relabeled structure, a version bump or a deletion does.

So this tool has two levels, and defaults to the coarse one:

  STRUCTURAL (default) — the shape / inventory. Cosmetic edits are invisible here:
    .xlsx  -> sheet names, each sheet's used range + header row
    .pptx  -> slide count + slide titles
    .docx  -> heading outline + paragraph count
    .pdf   -> page count + each page's first line
  A structural diff is non-empty only when something MATERIAL changed.

  DETAIL (--detail) — every cell / paragraph / page. Use ONLY for critical files
  (a board model, a pricing sheet) that you list in .okf/always-ask, where you do
  want to know every number move:
    .xlsx  -> {"Sheet!Cell": "=formula" | typed input value}  (numbers are the focus;
              a formula's derived result is skipped to avoid cascade noise)
    .pptx/.docx/.pdf -> paragraph / page text

Office formats are zip+XML, read WITHOUT openpyxl/python-pptx/python-docx so this
stays stdlib-only. PDF has no stdlib text layer: it shells out to `pdftotext` when
present, else reports unsupported (exit 3) so the watcher falls back to its read.

Usage:
  artifact-diff.py dump <file> [--detail]              # print the fingerprint (JSON)
  artifact-diff.py diff <file> <baseline.json> [--detail] [--json]
  exit codes of `diff`: 0 = no change, 1 = changed, 2 = read error,
      3 = unsupported type / backend missing. Missing/empty baseline = exit 0.

Watcher wiring: keep the last fingerprint at .okf/fingerprints/<relpath>.json;
diff each run, act on MATERIAL changes, then refresh the baseline with `dump`.
"""
import json
import os
import re
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET

REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


class Unsupported(Exception):
    pass


def _local(tag):
    return tag.split("}", 1)[1] if "}" in tag else tag


def _text_of(el):
    return "".join(t.text or "" for t in el.iter() if _local(t.tag) == "t").strip()


def _xlsx_sheets(zf):
    """[(sheet_name, worksheet_zip_path)] in workbook order; + shared strings."""
    names = zf.namelist()
    shared = []
    if "xl/sharedStrings.xml" in names:
        for si in ET.fromstring(zf.read("xl/sharedStrings.xml")):
            if _local(si.tag) == "si":
                shared.append(_text_of(si))
    sheets = []
    if "xl/workbook.xml" in names:
        wb = ET.fromstring(zf.read("xl/workbook.xml"))
        rels = {}
        if "xl/_rels/workbook.xml.rels" in names:
            for r in ET.fromstring(zf.read("xl/_rels/workbook.xml.rels")):
                if _local(r.tag) == "Relationship":
                    tgt = re.sub(r"^/?xl/", "", r.get("Target", "")).lstrip("/")
                    rels[r.get("Id")] = "xl/" + tgt
        for grp in wb:
            if _local(grp.tag) == "sheets":
                for s in grp:
                    if _local(s.tag) == "sheet":
                        p = rels.get(s.get("{%s}id" % REL_NS))
                        if p in names:
                            sheets.append((s.get("name", "?"), p))
    if not sheets:
        sheets = [(re.search(r"sheet\d+", p).group(), p) for p in names
                  if re.match(r"xl/worksheets/sheet\d+\.xml$", p)]
    return sheets, shared


def _cell_value(cell, ctype, shared):
    formula = value = inline = None
    for child in cell:
        lt = _local(child.tag)
        if lt == "f":
            formula = (child.text or "").strip() or (
                "shared(si=%s)" % child.get("si", "?")
                if child.get("t") == "shared" else "")
        elif lt == "v":
            value = (child.text or "").strip()
        elif lt == "is":
            inline = _text_of(child)
    if formula:
        return "=" + formula
    if ctype == "s" and value:
        try:
            return shared[int(value)]
        except (ValueError, IndexError):
            return value
    if inline:
        return inline
    return value or None


# --------------------------------------------------------------------------- #
# DETAIL extractors — every cell / paragraph / page
# --------------------------------------------------------------------------- #
def _xlsx_detail(path):
    out = {}
    with zipfile.ZipFile(path) as zf:
        sheets, shared = _xlsx_sheets(zf)
        for name, wpath in sheets:
            for cell in ET.fromstring(zf.read(wpath)).iter():
                if _local(cell.tag) != "c" or not cell.get("r"):
                    continue
                v = _cell_value(cell, cell.get("t"), shared)
                if v is not None and v != "":
                    out["%s!%s" % (name, cell.get("r"))] = v
    return out


def _ooxml_paras(path, member, prefix):
    out = {}
    with zipfile.ZipFile(path) as zf:
        if member not in zf.namelist():
            return out
        i = 0
        for para in (e for e in ET.fromstring(zf.read(member)).iter()
                     if _local(e.tag) == "p"):
            txt = _text_of(para)
            if txt:
                out["%s%d" % (prefix, i)] = txt
                i += 1
    return out


def _pptx_detail(path):
    out = {}
    with zipfile.ZipFile(path) as zf:
        for sp in _pptx_slides(zf):
            n = re.search(r"slide(\d+)", sp).group(1)
            i = 0
            for para in (e for e in ET.fromstring(zf.read(sp)).iter()
                         if _local(e.tag) == "p"):
                txt = _text_of(para)
                if txt:
                    out["slide%s#%d" % (n, i)] = txt
                    i += 1
    return out


def _docx_detail(path):
    return _ooxml_paras(path, "word/document.xml", "p")


def _pdf_pages(path):
    from shutil import which
    if not which("pdftotext"):
        raise Unsupported("pdftotext not installed (brew install poppler / apt install poppler-utils)")
    try:
        raw = subprocess.run(["pdftotext", "-layout", path, "-"],
                             capture_output=True, timeout=120).stdout.decode("utf-8", "replace")
    except (OSError, subprocess.SubprocessError) as e:
        raise Unsupported("pdftotext failed: %s" % e)
    return [pg.strip() for pg in raw.split("\x0c") if pg.strip()]


def _pdf_detail(path):
    return {"page%d" % i: pg for i, pg in enumerate(_pdf_pages(path))}


# --------------------------------------------------------------------------- #
# STRUCTURAL extractors — shape / inventory (cosmetic edits are invisible)
# --------------------------------------------------------------------------- #
def _pptx_slides(zf):
    return sorted((p for p in zf.namelist()
                   if re.match(r"ppt/slides/slide\d+\.xml$", p)),
                  key=lambda p: int(re.search(r"(\d+)", p).group()))


def _xlsx_struct(path):
    out = {}
    with zipfile.ZipFile(path) as zf:
        sheets, shared = _xlsx_sheets(zf)
        out["sheets"] = " | ".join(n for n, _ in sheets)
        for name, wpath in sheets:
            root = ET.fromstring(zf.read(wpath))
            for d in root.iter():
                if _local(d.tag) == "dimension" and d.get("ref"):
                    out["%s!range" % name] = d.get("ref")
                    break
            # header row = row 1 cell values, left to right
            header = []
            for row in root.iter():
                if _local(row.tag) == "row" and row.get("r") == "1":
                    for cell in row:
                        if _local(cell.tag) == "c":
                            v = _cell_value(cell, cell.get("t"), shared)
                            if v:
                                header.append(v)
                    break
            if header:
                out["%s!header" % name] = " | ".join(header)
    return out


def _pptx_struct(path):
    out = {}
    with zipfile.ZipFile(path) as zf:
        slides = _pptx_slides(zf)
        out["nslides"] = str(len(slides))
        for sp in slides:
            n = re.search(r"slide(\d+)", sp).group(1)
            title = ""
            for para in (e for e in ET.fromstring(zf.read(sp)).iter()
                         if _local(e.tag) == "p"):
                title = _text_of(para)
                if title:
                    break
            out["slide%s.title" % n] = title
    return out


def _docx_struct(path):
    out = {}
    with zipfile.ZipFile(path) as zf:
        if "word/document.xml" not in zf.namelist():
            return out
        root = ET.fromstring(zf.read("word/document.xml"))
        headings, nparas, hi = [], 0, 0
        for para in (e for e in root.iter() if _local(e.tag) == "p"):
            txt = _text_of(para)
            if not txt:
                continue
            nparas += 1
            style = ""
            for st in para.iter():
                if _local(st.tag) == "pStyle":
                    style = (st.get("{%s}val" % st.tag.split("}", 1)[0].strip("{"))
                             or st.get("val") or "")
            is_heading = bool(re.search(r"head|title|t.tulo", style, re.I))
            if is_heading:
                out["h%d" % hi] = txt
                hi += 1
        out["nparas"] = str(nparas)
    return out


def _pdf_struct(path):
    pages = _pdf_pages(path)
    out = {"npages": str(len(pages))}
    for i, pg in enumerate(pages):
        first = next((ln for ln in pg.splitlines() if ln.strip()), "")
        out["page%d.head" % i] = first.strip()
    return out


DETAIL = {".xlsx": _xlsx_detail, ".pptx": _pptx_detail, ".docx": _docx_detail, ".pdf": _pdf_detail}
STRUCT = {".xlsx": _xlsx_struct, ".pptx": _pptx_struct, ".docx": _docx_struct, ".pdf": _pdf_struct}


def fingerprint(path, detail=False):
    ext = os.path.splitext(path)[1].lower()
    table = DETAIL if detail else STRUCT
    fn = table.get(ext)
    if not fn:
        raise Unsupported("unsupported type: %s (supported: %s)"
                          % (ext or "?", ", ".join(sorted(table))))
    return fn(path)


def diff_maps(old, new):
    changed, added, removed = [], [], []
    for k in sorted(set(old) | set(new)):
        o, n = old.get(k), new.get(k)
        if o is None:
            added.append((k, n))
        elif n is None:
            removed.append((k, o))
        elif o != n:
            changed.append((k, o, n))
    return {"changed": changed, "added": added, "removed": removed}


def main(argv):
    if len(argv) < 3 or argv[1] not in ("dump", "diff"):
        sys.stderr.write(__doc__)
        return 2
    cmd, target = argv[1], argv[2]
    flags = argv[3:]
    detail = "--detail" in flags
    as_json = "--json" in flags
    try:
        current = fingerprint(target, detail=detail)
    except Unsupported as e:
        sys.stderr.write("%s\n" % e)
        return 3
    except (zipfile.BadZipFile, ET.ParseError, OSError) as e:
        sys.stderr.write("cannot read %s: %s\n" % (target, e))
        return 2

    if cmd == "dump":
        print(json.dumps(current, indent=2, sort_keys=True, ensure_ascii=False))
        return 0

    base_path = next((a for a in flags if not a.startswith("-")), "")
    try:
        with open(base_path, encoding="utf-8") as f:
            baseline = json.load(f)
    except (OSError, ValueError):
        baseline = None
    if not baseline:
        print(json.dumps({"initialized": True}) if as_json
              else "baseline initialized (no prior fingerprint) — no diff")
        return 0

    d = diff_maps(baseline, current)
    n = len(d["changed"]) + len(d["added"]) + len(d["removed"])
    if as_json:
        print(json.dumps(d, ensure_ascii=False))
        return 1 if n else 0
    if not n:
        print("no material change" if not detail else "no content change")
        return 0
    for k, o, nw in d["changed"]:
        print("CHANGED %s: %s -> %s" % (k, o, nw))
    for k, nw in d["added"]:
        print("ADDED   %s: %s" % (k, nw))
    for k, o in d["removed"]:
        print("REMOVED %s: %s" % (k, o))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
