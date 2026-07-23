# The `.context/` layer + the determinism boundary

Open this to build or maintain `.context/`. The `.context/` JSONs are **not** the human knowledge base — that's
`knowledge/`. They are a **derived, re-creatable technical layer** that makes the *mechanical* parts of
maintenance deterministic, so the agent never re-discovers the whole project on each run. Everything here can be
regenerated from the real files + `knowledge/`.

**How this layer is produced (deterministic).** You do NOT hand-write these JSONs. **`context.py build <root>`**
derives them: `manifest.json` + `hashes.json` from the real files, and `catalog.json` + `graph.json` **harvested
from the `knowledge/` concept-page frontmatter + cross-links** — so the agent authors meaning ONCE (in the
concept page) and the machine layer is generated, same input → same output. `context.py check <root>` is the
**doctor** that validates integrity. `state.json` + `events.jsonl` are written by `build` too. `extracted/` is
populated by `build` **when OfficeCLI is installed** (deck/sheet/doc content → JSON, + per-part hashes); without
OfficeCLI it stays empty and hashes are file-level. So: **the agent's job is the concept pages; the `.context/`
JSONs are downstream of them.** Related bundled scripts: `snapshot.py` (per-folder change
memory for reconcile-on-open), `validate.py` (shape gate), `graph.py` (render `knowledge-graph.html`).

---

## What lives in `.context/`

```
.context/
├── project-profile.json   # the Project Contract (see contract.md)
├── manifest.json          # inventory of known files
├── hashes.json            # content/part hashes
├── catalog.json           # natural language ↔ concept ↔ real files (the retrieval bridge)
├── graph.json             # explicit concept/file relations (impact analysis)
├── state.json             # run control
├── events.jsonl           # append-only processed-event log
├── extracted/             # intermediate extractions (regenerable)
└── migrations/            # reorganization plans + rollback (see contract.md §4)
```

### `manifest.json` — inventory of known files
```json
{
  "files": {
    "Análises/Resultados Financeiros.xlsx": {
      "type": "xlsx", "size": 482910,
      "modified_at": "2026-07-23T14:20:00-03:00",
      "hash": "a81c...", "status": "indexed"
    }
  }
}
```
Knows which files exist; detects creation/removal/move; avoids reprocessing intact files; records the last-index
state.

### `hashes.json` — content / part hashes / formulas
File-level hashes (`hashes`) distinguish *saved again* from *content really changed* and a *move without change*.
When OfficeCLI is installed, `context.py build` adds two more layers for office files (verified against OfficeCLI
v1.0.141):
```json
{
  "hashes": { "03_entregaveis/budget.xlsx": "a81c…" },
  "parts":  { "03_entregaveis/budget.xlsx": { "/Sheet1": "644b…" },
              "03_entregaveis/deck.pptx":   { "/slide[1]": "6343…", "/slide[2]": "81fd…" } },
  "formulas": { "03_entregaveis/budget.xlsx": { "/Sheet1/A4": "SUM(A2:A3)" } }
}
```
- **`parts`** → one hash per **slide / sheet**, so a change localizes to `/slide[3]` or `/Sheet1` (§6.2), not
  just "the file changed".
- **`formulas`** → per-cell formula map; its DIFF is **formula-by-formula**: *"/Sheet1/A4 changed from
  `SUM(A2:A3)` to `SUM(A2:A3)+10`"*. (OfficeCLI keeps a 60s in-memory resident; `context.py` runs
  `officecli close` before reading so it never sees a stale copy.)

### `catalog.json` — the retrieval bridge (natural language → concept → files)
```json
{
  "concepts": [
    {
      "id": "system.resultados-xpto",
      "title": "Resultados XPTO",
      "aliases": ["sql do XPTO", "materialização do XPTO", "resultado do dashboard"],
      "source_files": ["Incubadora High Touch/2. Dashboard/endpoint_sql/materializa_resultados.sql"],
      "local_documentation": ["Incubadora High Touch/2. Dashboard/endpoint_sql/overview.md"]
    }
  ]
}
```
When the user says *"I need to adjust the SQL that materializes the XPTO results,"* the agent consults the
catalog, finds the concept, and **validates the associated files before editing**. `id`, `aliases`, and
`title` mirror the concept page's frontmatter — keep them in sync. Alias uniqueness is a maintenance invariant.

### `graph.json` — explicit relations (impact analysis)
```json
{
  "edges": [
    { "from": "system.resultados-xpto", "to": "product.dashboard-high-touch", "type": "feeds" },
    { "from": "materializa_resultados.sql", "to": "system.resultados-xpto", "type": "implements" }
  ]
}
```
Answers: which pages depend on a file; which deliverables use an analysis; which concepts may be stale; which
backlinks need updating. `graph.py` renders `knowledge/knowledge-graph.html` from the concept cross-links; keep
`graph.json` consistent with those links.

### `state.json` — run control
```json
{ "schema_version": 1, "last_successful_run": "2026-07-23T15:00:00-03:00", "run_status": "idle", "pending_reviews": 2 }
```

### `events.jsonl` — append-only processed-event log
```json
{"event_id":"evt-001","type":"file_modified","path":"Análises/Resultados Financeiros.xlsx","status":"applied"}
```
For audit, **idempotency** (never apply the same event twice), and diagnosis.

### `extracted/` — regenerable intermediate extractions
Slide text, tab names, formulas, page titles, metadata, JSON structures, references found. All regenerable.
**Best populated with [OfficeCLI](https://github.com/iOfficeAI/OfficeCLI)** (optional, preferred) — a
dependency-free binary that emits deck/sheet/doc content as JSON (`officecli get <file> <path> --json`),
deterministically. It also enables **part-level `hashes.json`** (hash each slide/tab, not just the file) so a
change localizes to "slide 3" or "tab Resultados", per §6.2. **`context.py build` does this automatically when
OfficeCLI is on PATH** — writes `.context/extracted/<file>.json` per office artifact and `hashes.json["parts"]`.
Not installed → `extracted/` stays empty, hashes are file-level; fall back to `python-pptx`/`openpyxl`/`unzip` for
one-off reads.

---

## How the layer raises determinism (the worked chain)

```
Resultados Financeiros.xlsx changed
  → hashes.json proves the CONTENT changed (not just a re-save)
  → manifest.json identifies path, format, previous version
  → catalog.json says which CONCEPTS use the spreadsheet
  → graph.json says which decks/docs DEPEND on it
  → the skill processes ONLY the affected items
  → state.json records the run
  → events.jsonl blocks re-applying the same event
```
Without this layer the agent re-discovers the project every run. With it, the agent gets a **restricted,
verifiable** candidate set.

---

## The boundary: deterministic vs. agent

**Deterministic (code + fixed rules — same input, same output):** list files; compute hashes; detect
create/modify/delete/move; ignore temporaries (`~$file.xlsx`); generate stable IDs; repoint links of moved files;
refresh the auto blocks of `index.md`; check broken links; validate frontmatter/schemas; guarantee ID uniqueness;
detect duplicate aliases; mark docs possibly-stale; prevent duplicate processing; snapshot + rollback; produce a
change report. **Same output for the same input.**

**Agent / LLM (interpretation — never fully deterministic):** whether a change is cosmetic or changes meaning;
whether a meeting sentence was a decision, a hypothesis, or a suggestion; which new concept to create; how to
summarize a set of files; which parts of the wiki need textual update; which source is right when two diverge.

**For every agent call in that second list:** produce a **small patch**, cite the **evidence**, assign a
**confidence**, **validate** the document after, and **ask for approval** when there's ambiguity or real impact.

> Deterministic to detect, map, validate, apply · agent to interpret and propose · human to resolve important
> ambiguity. The goal is not "zero error" — it's **predictability**.
