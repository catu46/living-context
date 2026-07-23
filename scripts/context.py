#!/usr/bin/env python3
"""context.py - deterministic generator + doctor for the .context/ layer.

The .context/ JSONs are DERIVED, not hand-written. The agent authors meaning
ONCE — in the knowledge/ concept-page frontmatter (id, aliases, source_files,
local_documentation) and the markdown cross-links — and this script harvests
that into the machine layer, plus scans the real files for the inventory. So the
mechanical parts are deterministic (same input -> same output), per the spec's
determinism boundary (see context-layer.md).

Commands:
  build <root>           write .context/{manifest,hashes,catalog,graph,state}.json
                         + append one events.jsonl line. Derives:
                           - manifest.json / hashes.json   <- the real artifacts on disk
                           - catalog.json                  <- knowledge/ concept frontmatter
                           - graph.json                    <- knowledge/ cross-links + supersedes
                           - state.json                    <- run control (pending_reviews preserved)
  build <root> --dry-run print what WOULD change; write nothing.
  check <root>           the DOCTOR: validate .context integrity. Exit 1 on error,
                         0 clean. Deterministic; no LLM. Errors: duplicate concept
                         id, duplicate alias across concepts, a concept id with no
                         knowledge/ file, a source_files path that doesn't resolve,
                         a graph edge referencing a missing node, an invalid
                         confidentiality level. Warnings (never fail): manifest
                         drift (files changed since the last build), missing
                         project-profile.json / confidentiality.

Stdlib only. Reuses snapshot.py (hashing/scan) and graph.py (concept/link parse)
from this directory, so the graph.json matches the rendered knowledge-graph.html.
"""

import sys
import os
import re
import json
import argparse
import hashlib
import shutil
import subprocess

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import snapshot  # noqa: E402  (hashing/scan/now_iso/is_tracked)
import graph     # noqa: E402  (parse_frontmatter/strip_code_fences/collect)

CONFIDENTIALITY = {"Public", "Internal", "Confidential", "Highly Confidential"}
# office formats OfficeCLI (optional) can extract to JSON — see extract_office()
OFFICE_EXTS = {"pptx", "xlsx", "docx"}
OFFICECLI_TIMEOUT = 90  # seconds per file — don't let a stuck extraction hang the build
# knowledge/ files that are NOT concepts (no catalog entry)
RESERVED_TYPES = {"index", "log", "agent-guide"}
# dirs never inventoried as artifacts
SKIP_DIRS = {".git", "node_modules", "dist", "build", ".next", "target", "vendor",
             "__pycache__", "_archive", "venv", "env", ".venv", "knowledge", ".context"}


# ---------- a small YAML-subset frontmatter reader (handles lists) ----------

def read_frontmatter(path):
    """Parse YAML frontmatter into {key: scalar-or-list}. Handles scalars,
    inline lists `k: [a, b]`, and block lists `k:\\n  - a\\n  - b`. A block list
    of maps (last_verified) yields the raw '- ' item strings (good enough — the
    catalog doesn't need the map's inner keys)."""
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}
    block = lines[1:end]
    fm = {}
    j = 0
    while j < len(block):
        raw = block[j]
        s = raw.strip()
        if not s or s.startswith("#") or raw.lstrip().startswith("- ") or ":" not in raw:
            j += 1
            continue
        key, _, val = raw.partition(":")
        key = key.strip()
        val = val.strip()
        if val and val[0] not in "\"'":
            m = re.search(r"\s+#", val)
            if m:
                val = val[:m.start()].strip()
        if val.startswith("[") and val.endswith("]"):
            fm[key] = [x.strip().strip("\"'") for x in val[1:-1].split(",") if x.strip()]
        elif val == "":
            items, k = [], j + 1
            while k < len(block):
                nxt = block[k]
                t = nxt.strip()
                if t.startswith("- "):
                    item = t[2:].strip().strip("\"'")
                    # "- file: path" (map item) -> keep the path after the first ': '
                    mm = re.match(r"^\w[\w-]*:\s*(.+)$", item)
                    items.append(mm.group(1).strip() if mm else item)
                    k += 1
                elif nxt.startswith((" ", "\t")) and ":" in nxt:
                    k += 1  # continuation line of a map item (e.g. "  hash: ...") — skip
                else:
                    break
            fm[key] = items if items else ""
            j = k
            continue
        else:
            fm[key] = val.strip("\"'")
        j += 1
    return fm


def as_list(v):
    if v is None or v == "":
        return []
    return v if isinstance(v, list) else [v]


# ---------- harvest ----------

def bundle_root(root):
    return os.path.join(root, "knowledge")


def harvest_concepts(root):
    """Walk knowledge/ and return concept dicts derived from frontmatter.
    source_files/local_documentation are resolved to project-root-relative paths
    (relative in the frontmatter is relative to the concept file)."""
    b = bundle_root(root)
    concepts = []
    if not os.path.isdir(b):
        return concepts
    for dirpath, dirnames, filenames in os.walk(b):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in sorted(filenames):
            if not fn.endswith(".md") or fn == "CLAUDE.md":
                continue
            fp = os.path.join(dirpath, fn)
            fm = read_frontmatter(fp)
            if not fm:
                continue
            ctype = fm.get("type", "")
            if ctype in RESERVED_TYPES:
                continue
            rel_in_bundle = os.path.relpath(fp, b)
            cid = fm.get("id") or rel_in_bundle[:-3]  # strip .md
            cdir = os.path.dirname(fp)

            def rootrel(p):
                ap = os.path.normpath(os.path.join(cdir, p))
                return os.path.relpath(ap, root)

            concepts.append({
                "id": cid,
                "title": fm.get("title") or fn,
                "type": ctype or "topic",
                "status": fm.get("status", "active"),
                "aliases": as_list(fm.get("aliases")),
                "source_files": [rootrel(p) for p in as_list(fm.get("source_files"))],
                "local_documentation": [rootrel(p) for p in as_list(fm.get("local_documentation"))],
                "_file": os.path.relpath(fp, root),  # for the doctor; dropped on write
            })
    return concepts


def scan_artifacts(root):
    """Inventory real artifacts across the tree (not the doc-set, not knowledge/,
    not .context/). Returns {rootrel_path: {size, mtime, hash}}."""
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        ignore = snapshot.load_okfignore(dirpath)
        for name in sorted(filenames):
            if not snapshot.is_tracked(name, ignore):
                continue
            full = os.path.join(dirpath, name)
            if not os.path.isfile(full):
                continue
            sha, size, mtime = snapshot.fingerprint(full)
            rel = os.path.relpath(full, root)
            out[rel] = {"size": size, "mtime": mtime, "hash": sha}
    return out


# ---------- OfficeCLI extraction (optional, preferred) ----------
# Uses OfficeCLI (https://github.com/iOfficeAI/OfficeCLI) when present: a
# dependency-free binary that reads pptx/xlsx/docx into JSON. We ONLY read
# (`get ... --json`) — never edit — so it's purely additive and file-lock safe.
# Not installed? Everything below is skipped; file-level hashes still work.

def _canon(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _office_parts(doc):
    """Best-effort, schema-TOLERANT: split an OfficeCLI `get / --depth N --json`
    tree into its top-level parts (slides / sheets / sections) so each can be
    hashed independently — a change then localizes to 'slide[3]' or 'Sheet1'
    (spec §6.2), not just the whole file. Returns {part_id: subtree} or None if
    the shape isn't recognized (caller falls back to a whole-file hash)."""
    children = None
    if isinstance(doc, list):
        children = doc
    elif isinstance(doc, dict):
        for k in ("children", "slides", "sheets", "worksheets", "elements", "items", "nodes"):
            v = doc.get(k)
            if isinstance(v, list):
                children = v
                break
    if not children:
        return None
    parts = {}
    for i, ch in enumerate(children, 1):
        pid = None
        if isinstance(ch, dict):
            pid = ch.get("path") or (str(ch.get("name") or ch.get("tag") or "part") + "[%d]" % i)
        parts[pid or "part[%d]" % i] = ch
    return parts


def extract_office(root, manifest_files, dry_run):
    """For each office artifact, run OfficeCLI to write .context/extracted/<file>.json
    (verbatim) and derive per-part hashes. Returns (count, part_hashes, status)."""
    office = [rel for rel, m in manifest_files.items() if m["type"] in OFFICE_EXTS]
    if not office:
        return 0, {}, "no-office-files"
    cli = shutil.which("officecli")
    if not cli:
        return 0, {}, "officecli-absent"
    if dry_run:
        return len(office), {}, "ready"

    ex_dir = os.path.join(root, ".context", "extracted")
    os.makedirs(ex_dir, exist_ok=True)
    part_hashes, ok, failed = {}, 0, []
    for rel in office:
        try:
            r = subprocess.run([cli, "get", os.path.join(root, rel), "/", "--depth", "99", "--json"],
                               capture_output=True, text=True, timeout=OFFICECLI_TIMEOUT)
            if r.returncode != 0 or not r.stdout.strip():
                failed.append(rel)
                continue
            doc = json.loads(r.stdout)
        except (subprocess.SubprocessError, ValueError, OSError):
            failed.append(rel)
            continue
        write_json(os.path.join(ex_dir, rel.replace(os.sep, "__") + ".json"), doc)
        parts = _office_parts(doc)
        if parts:
            part_hashes[rel] = {pid: hashlib.sha256(_canon(sub).encode("utf-8")).hexdigest()
                                for pid, sub in parts.items()}
        else:
            part_hashes[rel] = {"whole": hashlib.sha256(_canon(doc).encode("utf-8")).hexdigest()}
        ok += 1
    if failed:
        sys.stderr.write("officecli: could not extract %d file(s): %s\n"
                         % (len(failed), ", ".join(failed[:5]) + (" …" if len(failed) > 5 else "")))
    return ok, part_hashes, "done"


# ---------- build ----------

def build_payloads(root):
    arts = scan_artifacts(root)
    concepts = harvest_concepts(root)
    ts = snapshot.now_iso()

    manifest = {"generated": ts, "files": {}}
    hashes = {"generated": ts, "hashes": {}}
    for rel, meta in sorted(arts.items()):
        ext = os.path.splitext(rel)[1].lstrip(".").lower() or "file"
        manifest["files"][rel] = {
            "type": ext, "size": meta["size"], "hash": meta["hash"], "status": "indexed",
        }
        hashes["hashes"][rel] = meta["hash"]

    catalog = {"generated": ts,
               "concepts": [{k: c[k] for k in
                             ("id", "title", "type", "status", "aliases",
                              "source_files", "local_documentation")}
                            for c in concepts]}

    nodes, edges = graph.collect(bundle_root(root)) if os.path.isdir(bundle_root(root)) else ({}, [])
    graph_json = {
        "generated": ts,
        "nodes": [{"id": n["id"], "type": n["type"], "status": n["status"], "label": n["label"]}
                  for n in nodes.values()],
        "edges": [{"from": e["from"], "to": e["to"], "type": e["kind"]} for e in edges],
    }
    return manifest, hashes, catalog, graph_json, len(arts), len(concepts)


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def cmd_build(root, dry_run, do_extract=True):
    cdir = os.path.join(root, ".context")
    manifest, hashes, catalog, graph_json, n_art, n_con = build_payloads(root)

    if dry_run:
        print("[dry-run] would write into %s/:" % cdir)
        print("  manifest.json  (%d artifact%s)" % (n_art, "" if n_art == 1 else "s"))
        print("  hashes.json    (%d hash%s)" % (n_art, "" if n_art == 1 else "es"))
        print("  catalog.json   (%d concept%s)" % (n_con, "" if n_con == 1 else "s"))
        print("  graph.json     (%d node%s, %d edge%s)"
              % (len(graph_json["nodes"]), "" if len(graph_json["nodes"]) == 1 else "s",
                 len(graph_json["edges"]), "" if len(graph_json["edges"]) == 1 else "s"))
        print("  state.json     (run control; pending_reviews preserved)")
        print("  events.jsonl   (append 1 build event)")
        if do_extract:
            n_off, _, st = extract_office(root, manifest["files"], dry_run=True)
            if st == "ready":
                print("  extracted/     (%d office file%s via OfficeCLI + per-part hashes)"
                      % (n_off, "" if n_off == 1 else "s"))
            elif st == "officecli-absent" and n_off == 0:
                pass
            elif st == "officecli-absent":
                print("  extracted/     (OfficeCLI not installed — skipped; file-level hashes only)")
        return 0

    os.makedirs(cdir, exist_ok=True)

    # OfficeCLI extraction (optional): populate extracted/ + per-part hashes BEFORE
    # writing hashes.json so the part hashes are merged in.
    ex_count = 0
    if do_extract:
        ex_count, part_hashes, _ = extract_office(root, manifest["files"], dry_run=False)
        if part_hashes:
            hashes["parts"] = part_hashes

    write_json(os.path.join(cdir, "manifest.json"), manifest)
    write_json(os.path.join(cdir, "hashes.json"), hashes)
    write_json(os.path.join(cdir, "catalog.json"), catalog)
    write_json(os.path.join(cdir, "graph.json"), graph_json)

    # state.json: preserve pending_reviews across builds
    state_path = os.path.join(cdir, "state.json")
    pending = 0
    if os.path.isfile(state_path):
        try:
            pending = json.load(open(state_path, encoding="utf-8")).get("pending_reviews", 0)
        except (ValueError, OSError):
            pending = 0
    write_json(state_path, {"schema_version": 1, "last_successful_run": snapshot.now_iso(),
                            "run_status": "idle", "pending_reviews": pending})

    # events.jsonl: append-only
    ev_path = os.path.join(cdir, "events.jsonl")
    n_prev = 0
    if os.path.isfile(ev_path):
        with open(ev_path, encoding="utf-8") as f:
            n_prev = sum(1 for _ in f)
    with open(ev_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"event_id": "evt-%04d" % (n_prev + 1), "type": "context_build",
                            "at": snapshot.now_iso(), "artifacts": n_art, "concepts": n_con,
                            "extracted": ex_count, "status": "applied"}, ensure_ascii=False) + "\n")

    extra = (" · %d office extraction%s" % (ex_count, "" if ex_count == 1 else "s")) if ex_count else ""
    print("context.py :: built .context/ — %d artifacts, %d concepts, %d graph nodes, %d edges%s"
          % (n_art, n_con, len(graph_json["nodes"]), len(graph_json["edges"]), extra))
    return 0


# ---------- check (the doctor) ----------

def cmd_check(root):
    cdir = os.path.join(root, ".context")
    errors, warns = [], []

    def err(m):
        errors.append(m)

    def warn(m):
        warns.append(m)

    # catalog integrity — derived live from the concepts so we can compare to the file
    concepts = harvest_concepts(root)
    seen_id, alias_owner = {}, {}
    for c in concepts:
        if c["id"] in seen_id:
            err("duplicate concept id '%s' (%s and %s)" % (c["id"], seen_id[c["id"]], c["_file"]))
        seen_id[c["id"]] = c["_file"]
        # the concept id must map to a real knowledge/ file (id + .md under the bundle)
        expected = os.path.join(bundle_root(root), c["id"] + ".md")
        if not os.path.isfile(expected) and not os.path.isfile(os.path.join(root, c["_file"])):
            err("concept '%s' has no knowledge/ file (expected %s)"
                % (c["id"], os.path.relpath(expected, root)))
        for a in c["aliases"]:
            key = a.lower().strip()
            if key in alias_owner and alias_owner[key] != c["id"]:
                err("alias '%s' is claimed by two concepts: '%s' and '%s'"
                    % (a, alias_owner[key], c["id"]))
            alias_owner[key] = c["id"]
        for sf in c["source_files"]:
            if not os.path.exists(os.path.join(root, sf)):
                err("concept '%s' source_files path does not resolve: %s" % (c["id"], sf))

    # the written catalog.json (if present) should match the live harvest
    cat_path = os.path.join(cdir, "catalog.json")
    if os.path.isfile(cat_path):
        try:
            written = {c["id"] for c in json.load(open(cat_path, encoding="utf-8")).get("concepts", [])}
            live = {c["id"] for c in concepts}
            if written != live:
                warn("catalog.json is out of date with knowledge/ (run `context.py build`): "
                     "+%d / -%d concepts" % (len(live - written), len(written - live)))
        except (ValueError, OSError):
            err("catalog.json is not valid JSON")
    elif concepts:
        warn("no .context/catalog.json yet — run `context.py build`")

    # graph.json edges must reference existing nodes
    g_path = os.path.join(cdir, "graph.json")
    if os.path.isfile(g_path):
        try:
            g = json.load(open(g_path, encoding="utf-8"))
            ids = {n["id"] for n in g.get("nodes", [])}
            for e in g.get("edges", []):
                if e.get("from") not in ids or e.get("to") not in ids:
                    err("graph.json edge references a missing node: %s -> %s"
                        % (e.get("from"), e.get("to")))
        except (ValueError, OSError):
            err("graph.json is not valid JSON")

    # manifest drift (informational — drift is what TRIGGERS maintenance, not a failure)
    m_path = os.path.join(cdir, "manifest.json")
    if os.path.isfile(m_path):
        try:
            recorded = json.load(open(m_path, encoding="utf-8")).get("files", {})
            current = scan_artifacts(root)
            changed = [p for p in current if p in recorded and current[p]["hash"] != recorded[p].get("hash")]
            added = [p for p in current if p not in recorded]
            removed = [p for p in recorded if p not in current]
            if changed or added or removed:
                warn("manifest drift since last build: +%d added, ~%d changed, -%d removed "
                     "(run `context.py build` to refresh)" % (len(added), len(changed), len(removed)))
        except (ValueError, OSError):
            err("manifest.json is not valid JSON")

    # OfficeCLI availability — an office-heavy project should have it (a standard
    # setup step, not a hard block: warn, never fail, since it's an external binary
    # and a corporate machine may block the install).
    office_present = False
    for dp, dn, fns in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS and not d.startswith(".")]
        if any(os.path.splitext(f)[1].lstrip(".").lower() in OFFICE_EXTS for f in fns):
            office_present = True
            break
    if office_present and not shutil.which("officecli"):
        warn("this project has PowerPoint/Excel/Word files but OfficeCLI is not installed — "
             "decks/spreadsheets are tracked at file level only (no per-slide/tab detail). "
             "Install (single binary, no deps): curl -fsSL https://d.officecli.ai/install.sh | bash  "
             "(Windows: irm https://d.officecli.ai/install.ps1 | iex) — github.com/iOfficeAI/OfficeCLI")

    # Project Contract: confidentiality (from the consulting-bootstrap lineage)
    p_path = os.path.join(cdir, "project-profile.json")
    if os.path.isfile(p_path):
        try:
            prof = json.load(open(p_path, encoding="utf-8"))
            conf = (prof.get("project") or {}).get("confidentiality")
            if conf is None:
                warn("project-profile.json has no project.confidentiality "
                     "(one of: %s)" % ", ".join(sorted(CONFIDENTIALITY)))
            elif conf not in CONFIDENTIALITY:
                err("project.confidentiality '%s' is invalid — must be one of: %s"
                    % (conf, ", ".join(sorted(CONFIDENTIALITY))))
        except (ValueError, OSError):
            err("project-profile.json is not valid JSON")
    else:
        warn("no .context/project-profile.json (the Project Contract) yet")

    # report
    for w in warns:
        print("WARN: " + w)
    for e in errors:
        print("ERROR: " + e)
    if errors:
        print("\ncontext doctor: FAIL — %d error(s), %d warning(s)" % (len(errors), len(warns)))
        return 1
    print("context doctor: PASS — 0 errors, %d warning(s)" % len(warns))
    return 0


def main(argv):
    ap = argparse.ArgumentParser(prog="context.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["build", "check"])
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--dry-run", action="store_true", help="build: preview, write nothing")
    ap.add_argument("--no-extract", action="store_true",
                    help="build: skip OfficeCLI extraction of pptx/xlsx/docx even if installed")
    a = ap.parse_args(argv[1:])
    root = os.path.abspath(a.root)
    if not os.path.isdir(root):
        sys.stderr.write("not a directory: %s\n" % root)
        return 2
    if a.command == "build":
        return cmd_build(root, a.dry_run, do_extract=not a.no_extract)
    return cmd_check(root)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
