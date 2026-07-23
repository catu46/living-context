# living-context

A Claude Code / Codex **skill** that keeps a whole **project folder's context alive** — for knowledge workers
whose folders mix **documents you read** (PowerPoint, Excel, PDF, Word, meeting notes) **and artifacts that run**
(SQL, JSON, small models, pipelines).

Point it at a folder and it:

1. understands the structure and **reads the content**;
2. builds ONE **`knowledge/` bundle** in Markdown (concept-per-file with `type`/`status`/`supersedes` +
   cross-links) with a rendered **knowledge graph**;
3. builds a deterministic **`.context/`** layer (manifest, hashes, catalog, graph, state, events) that maps
   **natural language → concepts → real files**;
4. **keeps that context current** as files change — structural updates automatically, semantic patches proposed
   for approval, meetings treated as evidence;
5. lets you **talk to the folder** in natural language.

The real files stay the **source of truth**; `knowledge/` is the navigable interpretation layer. Deterministic
code detects/compares/locates/validates/applies; the LLM interprets/summarizes/proposes.

## Two layers

- **Engine (always on):** `knowledge/` bundle + graph + `.context/` + `validate.py`. The context itself.
- **Front door (optional, selectable):** a one-click **"Talk to my files" / "Organize a folder"** launcher, a
  background **watcher**, and **forcing hooks** — the non-engineer surface. Off by default; turned on per project
  for a non-technical owner.

There is **no bundled web app** — the interface is the assistant chat.

## Layout

```
SKILL.md            # the backbone (modes, contract, pipelines, safety)
shape.md            # copy-paste blocks: knowledge/ bundle + routers + .context/
modes.md            # Mode A/B, org sub-modes, KEEP-vs-REDESIGN, adaptive structures
context-layer.md    # .context/ JSON schemas + the deterministic-vs-agent boundary
contract.md         # the MECE document-type contract + the Project Contract + automation policy
LAUNCHER.md WATCHER.md FORCING.md   # the optional front-door layer
scripts/            # context.py (derive .context/ + doctor) · validate.py (shape gate)
                    #   snapshot.py (change-memory) · graph.py (render graph)
hooks/  distribute/  assets/
```

## Origin

Consolidates two earlier sibling skills — `agent-friendly-docs` (heavy OKF bundle + graph, for engineers) and
`agent-friendly-knowledge-docs` (simple docs + one-click launcher, for non-engineers) — into one skill where the
heavy engine is always on and the non-engineer front door is an optional layer. Built from the
`ESPECIFICACAO_CONTEXTO_VIVO_v3` specification.

## Requirements

- `python3` for the `.context/` engine (`context.py`, `snapshot.py`, `validate.py`, `graph.py`). Degrades
  gracefully if absent (still builds Markdown and chats; the change-tracking, graph and gate turn on once Python
  is installed).
- **[OfficeCLI](https://github.com/iOfficeAI/OfficeCLI)** (optional, recommended when the folder has
  PowerPoint/Excel/Word) — a dependency-free binary that reads/builds office files. `context.py build` uses it to
  populate `.context/extracted/` and **three layers of change detection** (verified against OfficeCLI v1.0.141):
  per-slide/sheet **part hashes** (*where* — "slide 3 / Sheet1 changed"), a per-cell **formula** map
  (*formula-by-formula* — "A4: `SUM(A2:A3)` → `+10`"), and a per-item **content** map (*value/text* —
  "A2: 100 → 150", "title: Q4 → Q4 2026"; capped for huge sheets). The agent can also register its MCP server
  (`officecli mcp claude`) for interactive reading/building. Without OfficeCLI, office reading falls back to
  `python-pptx`/`openpyxl`/`unzip` and change detection stays file-level.
