#!/usr/bin/env python3
"""graph.py - generate a self-contained interactive knowledge-graph HTML.

Stdlib only. Walks a living-context / OKF tree, reads every markdown file
that has YAML frontmatter, and emits ONE HTML file: nodes = docs (concepts,
index, AGENTS routers), edges = the markdown cross-links plus supersedes /
superseded_by. You never hand-edit the HTML — re-run this script (build loop
step 7, and again on every real change) and the graph tracks the docs.

The graph DATA is embedded in the file (nothing about your content leaves the
page). The rendering library (vis-network) loads from a public CDN, so a first
open needs internet; the CDN request carries no client data. Pass --vendor <path>
to point <script src> at a locally-hosted copy for a fully offline file.

Usage:
    python3 graph.py [ROOT] [-o OUTPUT] [--title T] [--vendor URL_OR_PATH]
    # ROOT defaults to '.'; OUTPUT defaults to ROOT/knowledge-graph.html
"""

import argparse
import html
import json
import os
import re
import fnmatch
import sys

EXCLUDED = {".git", "node_modules", "dist", "build", ".next", "target",
            "vendor", "__pycache__", "_archive", "venv", "env", ".venv"}
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
CDN = "https://cdn.jsdelivr.net/npm/vis-network@9.1.9/standalone/umd/vis-network.min.js"

# type -> colour (superseded/deprecated get faded automatically)
PALETTE = {
    "agent-guide": "#8892b0", "index": "#5c6b8a", "log": "#3d4a63",
    "metric": "#64b5f6", "table": "#4db6ac", "dataset": "#4db6ac",
    "excel-model": "#81c784", "deck": "#ba68c8", "sql": "#ffb74d",
    "api": "#4dd0e1", "runbook": "#f06292", "decision": "#e57373",
    "code": "#a5d6a7", "pipeline": "#7986cb", "config": "#b0bec5",
    "service": "#4dd0e1", "schema": "#ffb74d",
}
DEFAULT_COLOR = "#90a4ae"


def parse_frontmatter(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None, text
    fm = {}
    for raw in lines[1:end]:
        line = raw.rstrip()
        s = line.strip()
        if not s or s.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        m = re.search(r"\s+#", value)
        if m:
            value = value[:m.start()].strip()
        if len(value) >= 2 and value[0] in "\"'" and value[-1] == value[0]:
            value = value[1:-1]
        fm[key.strip()] = value
    return fm, "\n".join(lines[end + 1:])


def strip_code_fences(text):
    out, fence = [], None
    for line in text.splitlines():
        m = re.match(r"(`{3,}|~{3,})", line.lstrip())
        if fence is None:
            if m:
                fence = m.group(1)[0]
                continue
            out.append(line)
        elif m and m.group(1)[0] == fence:
            fence = None
    return "\n".join(out)


def is_url(v):
    return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://", v)) or v.startswith("mailto:")


def resolve(base_dir, target, root):
    target = target.strip()
    mt = re.match(r'^(.*?)\s+"[^"]*"$', target)
    if mt:
        target = mt.group(1).strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    if not target or is_url(target) or target.startswith("#") or target.startswith("/"):
        return None
    target = target.split("#", 1)[0]
    if not target:
        return None
    p = os.path.normpath(os.path.join(base_dir, target))
    if not os.path.isfile(p):
        return None
    return os.path.relpath(p, root)


def load_okfignore(root):
    globs = []
    path = os.path.join(root, ".okfignore")
    if os.path.isfile(path):
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    globs.append(line.rstrip("/"))
    return globs


def collect(root):
    nodes, scan = {}, []
    ignore = load_okfignore(root)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in EXCLUDED and not d.startswith(".")
                       and not any(fnmatch.fnmatch(d, g) or fnmatch.fnmatch(
                           os.path.relpath(os.path.join(dirpath, d), root), g) for g in ignore)]
        for fn in filenames:
            if not fn.endswith(".md") or fn == "CLAUDE.md":
                continue
            fp = os.path.join(dirpath, fn)
            try:
                text = open(fp, encoding="utf-8").read()
            except OSError:
                continue
            fm, body = parse_frontmatter(text)
            if fm is None:
                continue
            rel = os.path.relpath(fp, root)
            nodes[rel] = {
                "id": rel,
                "label": fm.get("title") or fn,
                "type": fm.get("type", "doc"),
                "status": fm.get("status", "active"),
            }
            scan.append((rel, os.path.dirname(fp), fm, body))

    edges, seen = [], set()

    def add(src, dst, kind):
        k = (src, dst, kind)
        if dst in nodes and src != dst and k not in seen:
            seen.add(k)
            edges.append({"from": src, "to": dst, "kind": kind})

    for rel, base_dir, fm, body in scan:
        for m in LINK_RE.finditer(strip_code_fences(body)):
            dst = resolve(base_dir, m.group(1), root)
            if dst:
                add(rel, dst, "link")
        for key in ("supersedes", "superseded_by"):
            v = fm.get(key, "")
            if v and not is_url(v):
                p = os.path.normpath(os.path.join(base_dir, v))
                if os.path.isfile(p):
                    add(rel, os.path.relpath(p, root), key)
    return nodes, edges


def build_html(nodes, edges, title, lib_src):
    vis_nodes, types_used = [], set()
    for n in nodes.values():
        faded = n["status"] in ("superseded", "deprecated")
        color = PALETTE.get(n["type"], DEFAULT_COLOR)
        types_used.add(n["type"])
        vis_nodes.append({
            "id": n["id"],
            "label": n["label"],
            "group": n["type"],
            "title": "%s  ·  %s%s" % (n["type"], n["id"],
                                      "  ·  " + n["status"] if faded else ""),
            "shape": "diamond" if n["type"] == "decision" else "dot",
            "color": {"background": "#20242e" if faded else color,
                      "border": color,
                      "highlight": {"background": color, "border": "#ffffff"}},
            "opacity": 0.45 if faded else 1.0,
        })
    vis_edges = []
    for e in edges:
        sup = e["kind"] != "link"
        vis_edges.append({
            "from": e["from"], "to": e["to"],
            "arrows": "to",
            "dashes": sup,
            "color": {"color": "#e0803f" if sup else "#3a4358",
                      "highlight": "#ffffff"},
            "title": e["kind"],
        })
    legend = " ".join(
        '<span class="lg"><i style="background:%s"></i>%s</span>'
        % (PALETTE.get(t, DEFAULT_COLOR), html.escape(t))
        for t in sorted(types_used))

    data = json.dumps({"nodes": vis_nodes, "edges": vis_edges})
    return TEMPLATE.replace("__TITLE__", html.escape(title)) \
                   .replace("__LIB__", html.escape(lib_src, quote=True)) \
                   .replace("__LEGEND__", legend) \
                   .replace("__COUNTS__", "%d nodes · %d edges" % (len(vis_nodes), len(vis_edges))) \
                   .replace("__DATA__", data)


TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<script src="__LIB__"></script>
<style>
  html,body{margin:0;height:100%;background:#0f1117;color:#c9d1d9;
    font:14px/1.4 -apple-system,Segoe UI,Roboto,sans-serif}
  #net{position:absolute;inset:0}
  #bar{position:absolute;top:0;left:0;right:0;padding:8px 12px;z-index:2;
    background:linear-gradient(#0f1117,rgba(15,17,23,0));pointer-events:none}
  #bar b{font-size:15px;color:#e6edf3}
  #bar .sub{color:#8b949e;margin-left:8px}
  #legend{margin-top:6px}
  .lg{display:inline-flex;align-items:center;margin-right:12px;color:#8b949e}
  .lg i{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:5px}
  #hint{position:absolute;bottom:8px;left:12px;color:#586069;z-index:2}
</style></head>
<body>
<div id="bar"><b>__TITLE__</b><span class="sub">__COUNTS__</span>
  <div id="legend">__LEGEND__ <span class="lg"><i style="background:#e0803f"></i>supersedes (dashed)</span></div>
</div>
<div id="net"></div>
<div id="hint">drag to reposition · scroll to zoom · click a node to open it</div>
<script>
const G = __DATA__;
const nodes = new vis.DataSet(G.nodes);
const edges = new vis.DataSet(G.edges);
const net = new vis.Network(document.getElementById('net'), {nodes, edges}, {
  nodes:{font:{color:'#c9d1d9',size:14},borderWidth:2,size:16},
  edges:{smooth:{type:'continuous'},width:1.2},
  physics:{solver:'forceAtlas2Based',stabilization:{iterations:200},
    forceAtlas2Based:{gravitationalConstant:-45,springLength:110,springConstant:0.06}},
  interaction:{hover:true,tooltipDelay:120}
});
net.on('click', p => { if(p.nodes.length){ const id=p.nodes[0]; if(id) window.location.href=id; }});
net.once('stabilizationIterationsDone', () => net.fit({animation:true}));
</script>
</body></html>
"""


def main(argv):
    ap = argparse.ArgumentParser(prog="graph.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("-o", "--output")
    ap.add_argument("--title", default="Knowledge graph")
    ap.add_argument("--vendor", help="URL or local path for vis-network (default: jsDelivr CDN)")
    a = ap.parse_args(argv[1:])

    root = os.path.abspath(a.root)
    if not os.path.isdir(root):
        sys.stderr.write("ERROR: not a directory: %s\n" % root)
        return 2
    # Root guard: the graph is built on the BUNDLE (<root>/knowledge). If you pointed
    # at a tree that CONTAINS a knowledge/ bundle, you probably meant the bundle itself
    # (else the AGENTS.md routers get pulled in as nodes). Warn, don't fail.
    if os.path.basename(root) != "knowledge" and os.path.isfile(os.path.join(root, "knowledge", "index.md")):
        sys.stderr.write("note: this looks like the repo root — did you mean %s?\n"
                         % os.path.join(root, "knowledge"))
    out = a.output or os.path.join(root, "knowledge-graph.html")
    nodes, edges = collect(root)
    if not nodes:
        sys.stderr.write("No markdown-with-frontmatter found under %s\n" % root)
        return 1
    open(out, "w", encoding="utf-8").write(
        build_html(nodes, edges, a.title, a.vendor or CDN))
    print("graph.py :: %d nodes, %d edges -> %s" % (len(nodes), len(edges), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
