---
name: living-context
description: Keep a whole PROJECT FOLDER's living context — for knowledge workers whose folders mix documents AND artifacts that run: decks, spreadsheets, PDFs, Word, meeting notes, plus SQL, JSON, small models and pipelines. Point it at a folder and it (1) understands the structure and reads the content, (2) builds ONE knowledge/ bundle in Markdown (concept-per-file with type/status/supersedes + cross-links) with a rendered knowledge graph, (3) builds a deterministic .context/ layer (manifest, hashes, catalog, graph, state, events) that maps natural language → concepts → real files, (4) keeps that context current as files change — structural updates automatically, semantic patches proposed for approval, meetings treated as evidence — and (5) lets you talk to the folder in natural language. Two scenarios converge on one architecture: an EXISTING project (survey, classify, contextualize; reorganize only with approval and rollback) and a NEW project (short kickoff interview, adaptive folder profile, a Project Contract). The real files stay the source of truth; knowledge/ is the navigable interpretation layer. Deterministic code detects/compares/locates/validates/applies; the LLM interprets/summarizes/proposes. A NON-ENGINEER front door — one-click "Talk to my files" / "Organize a folder" launcher, a background watcher, and forcing hooks — is an OPTIONAL, selectable layer, not the default. Triggers — "living context for my folder", "contexto vivo", "keep my project context updated", "talk to my folder/files", "organize my project folder for AI", "knowledge graph + catalog for a mixed doc/code folder", "what changed in this project since I was away".
---

# Living Context

**Keep a whole project folder's context alive** — for **knowledge workers** whose folders mix **documents you
read** (PowerPoint, Excel, PDF, Word, meeting notes, tool exports) **and artifacts that run** (SQL, JSON, small
models, pipelines). You point the skill at a project folder and it: understands the structure and **reads the
content**; builds a navigable **knowledge layer** in Markdown; **connects business concepts to the files that
back them**; **keeps that context current as files change**; lets you **talk to the folder** in natural
language; and **records what mattered** without turning the project into documentation bureaucracy.

**The real files stay the source of truth.** `knowledge/` is a *navigable, traceable interpretation layer* on
top — never a replacement, never a proprietary re-encoding of the folder.

This skill is the consolidation of two earlier siblings (`agent-friendly-docs`, `agent-friendly-knowledge-docs`)
into one: the **heavy engine** (an OKF `knowledge/` bundle + a rendered graph + a deterministic `.context/`
layer) is **always on**; the **non-engineer front door** (a one-click launcher, a background watcher, forcing
hooks) is an **optional, selectable layer** — see [The front door is optional](#the-front-door-is-optional-choose-it).

---

## The two layers: engine (always) + front door (optional)

```
living-context
├── ENGINE  (always)          knowledge/ bundle + graph + .context/ (manifest, hashes, catalog,
│                             graph, state, events, extracted) + validate. The context itself.
└── FRONT DOOR  (optional)    one-click launcher · background watcher · forcing hooks.
                              The "talk to my files without a terminal" surface for non-engineers.
```

**Decide the front door explicitly, early — it is a choice, not a default** (see the linked section). The engine
is the same either way.

**No web app.** There is deliberately **no bundled localhost UI**. The interface *is* the assistant chat (Claude
Code / Codex), reached directly or via the optional launcher. The knowledge is plain, portable Markdown + JSON;
anyone who wants a visual browser can open `knowledge/` as an Obsidian vault, but nothing depends on it.

---

## Language — two layers

This skill's OWN files (this SKILL.md, the references, the scripts) stay in **English** — the model executes them
whatever the chat language. Everything the skill **writes into the user's folders** — `knowledge/` pages,
`log.md`, the human-readable **Rules** in `AGENTS.md`, `overview.md` — is authored in the **content/project
language** (the language of the material and the user; detect it from evidence, don't assume). The **live chat**
always mirrors the user's language. Detect the two independently: a Portuguese consultant documenting an
English-language dataset gets Portuguese chat and Portuguese knowledge pages over English source files.

---

## The shape (the engine)

One **OKF `knowledge/` bundle** for the whole project + a thin auto-loaded router in each meaningful folder +
one deterministic **`.context/`** layer. Full copy-paste blocks: **[shape.md](shape.md)**. The `.context/`
schemas and the determinism boundary: **[context-layer.md](context-layer.md)**.

```
PROJECT/
├── CLAUDE.md                 # one line: @AGENTS.md  (the only auto-load bridge)
├── AGENTS.md                 # THIN router → ./knowledge/index.md  (Rules + pointers + Keep-current)
│
├── knowledge/                # ← THE ONE bundle (the project's meaning), Markdown, human-readable
│   ├── index.md              #   root map; each subdir also has its own index.md (progressive disclosure)
│   ├── overview.md           #   what the project is, scope, current state (the human face of the Contract)
│   ├── log.md                #   ONE append-only history — what changed, when, and the consequence
│   ├── systems/ processes/ topics/ people/   # concepts by kind (create only what earns a page)
│   └── knowledge-graph.html  #   ONE rendered graph (generated by scripts/graph.py)
│
├── .context/                 # ← deterministic, derived, RE-CREATABLE technical layer (not for humans)
│   ├── project-profile.json  #   the Project Contract (machine form)
│   ├── manifest.json         #   inventory of known files
│   ├── hashes.json           #   content/part hashes → "saved again" vs "really changed"
│   ├── catalog.json          #   natural language ↔ concept ↔ real files (the retrieval bridge)
│   ├── graph.json            #   explicit concept/file relations (impact analysis)
│   ├── state.json            #   run control (last run, pending reviews)
│   ├── events.jsonl          #   append-only processed-event log (idempotency, audit)
│   └── extracted/            #   intermediate extractions (slide text, sheet/tab names, formulas…)
│
├── sources/meetings/         # meeting notes/transcripts, when they exist (evidence, preserved)
└── <the project's own folders — deliverables, analyses, references, …>
```

- **`knowledge/` does NOT mechanically mirror the physical tree.** A concept page (`systems/resultados-xpto.md`)
  *points at* the real artifact (`.../endpoint_sql/materializa_resultados.sql`) via `source_files:`; it doesn't
  copy it. Meaning is organized by concept; files stay where they are.
- **A concept's ID is its path within the bundle** (`knowledge/systems/resultados-xpto.md` → `systems/resultados-xpto`).
- **`.context/` is derivable.** Every JSON in it can be regenerated from the real files + `knowledge/`. It exists
  to make the *mechanical* parts deterministic (detect, compare, locate, relate, validate, apply, record) so the
  agent never re-discovers the whole project from scratch — see **[context-layer.md](context-layer.md)**.
- **Local documentation stays next to the artifacts** when a work-unit needs a technical/operational explanation
  (`endpoint_sql/{index.md, overview.md, CLAUDE.md, materializa_resultados.sql}`). Don't create three Markdown
  files in every folder by obligation — only where they earn their place.

**The MECE document contract** — each artifact answers exactly one kind of question, and every fact has one
**canonical owner** even if mentioned elsewhere: **[contract.md](contract.md)**.

---

## The front door is optional — choose it

The launcher + watcher + forcing hooks are the **non-engineer surface**. Install them **only when they fit the
person who will actually use the folder** — ask, or infer from who the folder is for, and state your reasoning:

- **Engine only (default for a technical owner).** The person works *through the agent* already (Claude Code /
  Codex, direct). No launcher, no watcher, no forcing hooks. The context self-maintains **inline** as they work
  (see the self-maintenance pipeline) with git as the change-memory when the folder is a repo.
- **+ Front door (for a non-engineer, or a folder handed to one).** The person edits files **outside** any IDE
  (Excel over itself, a deck dropped in Drive, a SharePoint rename) and won't type commands. Add the layer:
  - **One-click launcher** in the root — `Talk to my files` / `Organize a folder with AI`, double-click, no
    terminal. **[LAUNCHER.md](LAUNCHER.md).**
  - **Reconcile-on-open + optional watcher** — catch up on what changed since last time.
    **[WATCHER.md](WATCHER.md).**
  - **Forcing hooks** — a deterministic gate so the context can't silently rot. **[FORCING.md](FORCING.md).**

**Never install the front door silently, and never withhold it silently — decide with the user.** When it's on,
tell them in one plain sentence what it does (*"whenever your files change, the assistant reminds itself to
update the notes — you don't have to do anything"*). When it's off, that's because a technical owner doesn't need
it. The choice is per-project and reversible.

---

## Two scenarios, one architecture — modes

Both scenarios converge on the same engine and the same self-maintenance. Full detail — the interview questions,
the auto-detection, the three existing-project organization sub-modes, KEEP-vs-REDESIGN, and the adaptive folder
profiles — is in **[modes.md](modes.md)**.

- **Mode A — existing project.** The folder already has material. Survey it, **preserve the current organization
  by default**, classify (sources / analyses / deliverables / references / meetings / history / temporary),
  infer core concepts, build `knowledge/` and `.context/`, and **flag questions and inconsistencies before
  changing anything relevant.** Never reorganize the whole folder without approval. Within Mode A the user picks
  one of three: **(1) contextualize only** (safe default — no moves/renames), **(2) organize with approval**
  (propose a move plan, execute only on OK, with a rollback snapshot), **(3) auto-organize within explicit
  limits** (objective rules only, reversible).
- **Mode B — new project.** Little or no material. Start with a **short kickoff interview**, propose a **minimal**
  structure (don't invent `systems/`/`processes/` before content justifies them), and seed pages with explicit
  `status: draft` / `source: initial-interview` so hypotheses are never presented as confirmed facts. As real
  files, meetings and analyses arrive, replace hypotheses with verified information.
- **Auto-detect the mode** from the folder (near-empty → suggest Mode B; many files → suggest Mode A); the user
  can override. After setup, both modes use the same maintenance flow.

**Adaptive structure (Mode B).** Propose an operational folder profile matched to the project type
(consulting/strategy · research · continuous-operation · product/implementation) — **proposed, never imposed**,
with the logic of each folder explained before creating it. Profiles are in [modes.md](modes.md).

---

## The Project Contract + the kickoff (show understanding before executing)

Treat setup as a brief discovery, like a kickoff. Build a **Project Contract** with the user, stored machine-form
in `.context/project-profile.json` and presented in human language in `knowledge/overview.md`. It records the
project's name/type/objective/lifecycle, the **organization policy** (may move files? may rename? archive
policy?), which sources are **canonical**, whether meeting notes count as evidence, what may update
automatically vs. what needs approval, the deliverables, and what always requires review. Template and fields:
**[contract.md](contract.md)**.

**Always show your understanding and get a yes before you build the baseline:**

> *My understanding: this is a continuous operation-and-tracking project; the spreadsheets are analytical
> sources; the decks are deliverables; the meetings are evidence; you don't want files reorganized now;
> structural changes may be automatic; meaning changes should be proposed. Correct?*

This is the step that stops the skill from inferring the wrong architecture.

---

## Deterministic where it can be, agent where it must be

The whole design rests on this split (full version + the reasoning: **[context-layer.md](context-layer.md)**):

- **Deterministic (code + fixed rules — same input, same output):** list files; compute hashes; detect
  create/modify/delete/move; ignore temporaries (`~$file.xlsx`); generate stable IDs; repoint links of moved
  files; refresh the auto blocks of `index.md`; check broken links; validate frontmatter/schemas; guarantee ID
  uniqueness; detect duplicate aliases; mark docs possibly-stale; prevent duplicate processing; snapshot +
  rollback; produce a change report. These run via the bundled scripts and the `.context/` layer.
- **Agent / LLM (interpretation — never fully deterministic):** is a change cosmetic or does it change meaning?
  was a sentence in a meeting a decision, a hypothesis, or a suggestion? which new concept to create? how to
  summarize a set of files? which parts of the wiki need textual update? which source is right when two diverge?

For every LLM call in that second list, the skill: produces a **small patch**, cites the **evidence**, assigns a
**confidence**, **validates** the document after, and **asks for approval** when there's ambiguity or real impact.
The goal is not "zero error" — it's **predictability**: deterministic to detect/map/validate/apply; agent to
interpret/propose; **human to resolve important ambiguity.**

---

## Bootstrap pipeline (initial creation)

Run once at setup (the discovery loop below feeds it). Detail per step in the references.

1. **Interview** — objective, deliverables, which files are sources vs. presentations, old versions, internal
   acronyms/names, may-move-or-only-document, what may be automatic vs. needs approval. (Mode B: also the
   structure-profile questions in [modes.md](modes.md).)
2. **Inventory** — paths, types, dates, sizes, hashes; sheets/tabs, slides, PDF pages, doc titles, explicit
   relations. Writes `manifest.json` + `hashes.json`.
3. **Classify** — each file as source / analysis / implementation / deliverable / reference / meeting / history /
   temporary / unknown.
4. **Concepts** — identify core concepts, create pages in `knowledge/` (frontmatter with `id`, `type`, `title`,
   `aliases`, `source_files`, `local_documentation`, `last_verified` hash — block 3 in [shape.md](shape.md)).
5. **Local documentation** — `index.md` + `overview.md` only in work-units that earn them; not everywhere.
6. **Catalog & graph** — `python3 <skill-dir>/scripts/context.py build .` derives the whole `.context/` layer
   (`manifest`/`hashes`/`catalog`/`graph`/`state`/`events`, + `extracted/` and per-part hashes if OfficeCLI is
   installed) from the real files + the concept frontmatter; then `scripts/graph.py knowledge/` renders
   `knowledge-graph.html`.
7. **Validate** — links, IDs, frontmatter, paths, concept coverage, orphan docs, missing sources, duplicates
   (`scripts/validate.py`).
8. **Report** — what was created/changed, concepts found, canonical sources, questions/conflicts, and which docs
   need human review.

**The discovery loop (interview ⇄ read — co-equal, alternating).** Understanding a real messy tree is iterative,
not linear. Interview reveals WHAT MATTERS and WHAT'S STILL TRUE; reading reveals WHAT IS. Interview → read the
content the answers point to (by default — read content, not just filenames) → **re-interview, sharper and
evidence-based** (*"you said the Q3 model is canonical, but there's v8, v8_FINAL, v8_FINAL_real — which?"*) → read
deeper → converge (usually 2–3 rounds) → **PROPOSE → BUILD → fresh-eyes verify.**

**Reading any document** — read the content by default; the interview decides what to *skip*, not what to open.
- **Office files (`.pptx`/`.xlsx`/`.docx`) — prefer OfficeCLI when available.** [OfficeCLI](https://github.com/iOfficeAI/OfficeCLI)
  is a single self-contained binary (no Python, no MS Office, offline, cross-platform, Apache-2.0) purpose-built
  for agents: `officecli get deck.pptx /slide[1] --json`, `officecli view file.xlsx outline` extract text /
  structure / sheet data / formulas as **JSON** — deterministic, ideal for populating `.context/extracted/` and
  for **slide/tab-level AND formula-by-formula** change detection (`context.py build` writes per-slide/sheet
  hashes + a per-cell formula map; verified against OfficeCLI v1.0.141). **Optional, not a hard dependency:** if
  it isn't installed, fall back to
  `python-pptx`/`openpyxl`/`python-docx` or zero-install `unzip -p` on the XML parts; legacy binaries via
  `textutil`/`soffice`.
- **PDF** via the Read tool's `pages` range. **Big spreadsheets** → used range + headers + dtypes + ~20 sample
  rows, never every cell.

**Office files — OfficeCLI + its skills are the companion engine (optional; don't reinvent it).** living-context
owns the *context* (`knowledge/` + `.context/`); it does not reimplement office read/write. When OfficeCLI is
installed, use it to READ (above) AND lean on its **per-format skills** to build and QA a project's deliverables
(`03_entregaveis/…`) — point the agent at the fitting one:
- decks → `officecli-pptx` · `officecli-pitch-deck` · `morph-ppt` / `morph-ppt-3d`
- spreadsheets/models/dashboards → `officecli-xlsx` · `officecli-financial-model` · `officecli-data-dashboard`
- Word docs/forms/papers → `officecli-docx` · `officecli-word-form` · `officecli-academic-paper`

living-context stays the source of context/truth and records what changed in `knowledge/log.md`; OfficeCLI
produces and reads the artifacts. Neither depends on the other — if OfficeCLI is absent, fall back to
`python-pptx`/`openpyxl`/`unzip`.

**Two channels to OfficeCLI — use the right one:**
- **MCP server, for the AGENT (preferred for interactive work).** OfficeCLI has a built-in MCP server — register
  it in one command: `officecli mcp claude` (also `cursor` / `vscode` / `lmstudio`; `officecli mcp list` to
  check). It exposes every document operation as **native MCP tools over JSON-RPC — no shell** — which is the
  clean channel for reading a deck/sheet in chat (catch-up, answering a question) and for building deliverables
  with the per-format skills.
- **CLI subprocess, for the SCRIPT.** `context.py build` shells `officecli get … --json` to populate
  `.context/extracted/` + per-part hashes deterministically. It's a headless script, so it uses the CLI directly,
  not MCP. (Both drive the same binary.)

**Install + register as a standard setup step when the folder has office files (offer, don't force).** During
bootstrap, if the project contains any `.pptx`/`.xlsx`/`.docx` and `officecli` isn't on PATH, **offer to install
it right then** — one command, consent, default yes — explaining plainly why (*"so I can read your decks and
spreadsheets properly and tell you exactly what changed — a slide or a tab, not just 'the file changed'"*):
`curl -fsSL https://d.officecli.ai/install.sh | bash` (Windows: `irm https://d.officecli.ai/install.ps1 | iex`),
then `officecli mcp claude` to give the agent the tools. Skip the offer if there are no office files. Do NOT
hard-block (a corporate machine may forbid the install; a folder may have zero office files) — `context.py check`
**warns** while it's missing on an office-heavy project, and the fallback keeps things working. This mirrors the
launcher's guided-install pattern.

**Fresh-eyes acceptance test (before self-maintenance takes over).** Deploy a subagent carrying **none** of this
conversation's context, rooted at the built tree, as a brand-new agent who just opened the folder. Using ONLY the
docs, have it (a) state what the project is and how it'd do a representative task, and (b) flag anything it could
**not** determine. Whatever it stumbles on is a real gap → fix and re-verify. `validate.py` checks the **shape**;
this checks **comprehension** — ship only when both pass.

---

## Self-maintenance pipeline (keep the context alive)

```
change detected → hash + diff → identify change type → consult catalog.json + graph.json
→ find potentially-affected docs → extract only the changed parts → classify impact
→ update structure automatically → propose semantic patches → validate
→ apply atomically → append to log.md when it mattered → refresh .context/ + events.jsonl
```

**Change classes decide the response:**

- **Structural** (file created/moved/renamed/deleted, new tab/slide/subfolder) → may update indexes, paths,
  catalog **automatically**.
- **Cosmetic** (column width, font, element position — no content change) → **do not** touch the wiki.
- **Semantic** (a formula/indicator/recommendation/input/output/rule changed, a new conclusion) → update
  documentation and knowledge **by patch, with approval when needed** (see the automation policy in
  [contract.md](contract.md)).

**How it self-feeds depends on the front door:**

- **Engine-only (technical owner):** **inline, as you work.** Every real change goes through the agent, which
  runs the *Keep this current* protocol embedded in every `AGENTS.md`, with **git** as the change-memory
  (`git diff <last-doc-commit>..HEAD --name-status` to catch up after a break). No snapshot file needed.
- **+ Front door (non-engineer):** **reconcile-on-open.** The `.okf-state.json` / `.context/` snapshots persist
  between sessions, so a future chat diffs the folder against them and reports *what changed since you were last
  here*, even across weeks nobody touched the chat. Optional unattended watcher in [WATCHER.md](WATCHER.md).

**When the agent edits a file THROUGH the skill,** the update is part of the same transaction: edit the real
file → recompute the hash → refresh catalog + graph → review local docs and concept pages → append to `log.md`
when it mattered → validate before finishing. Editing a file **outside** the skill does not update the context by
magic — some sync trigger (open-the-folder catch-up, the watcher, or an inline agent pass) must run.

**Meetings are evidence, not automatic truth — and are optional.** The skill must work with **no** meetings at
all (just watching the project's files). When they exist, notes/transcripts land in `sources/meetings/inbox/`;
the skill preserves the original, normalizes a note, associates it to concepts, updates affected pages, appends a
`knowledge/log.md` line when something relevant changed, and records pending items when implementation hasn't
happened yet. Granola is one possible input, never a dependency; no `decisions/` or `updates/` folders — decisions
live in their source meeting, current state is folded into the canonical pages, relevant changes go to `log.md`.

**Keep this current** (embedded in every `AGENTS.md`): after real changes, update the affected concept in the
bundle, **APPEND** one dated line to `knowledge/log.md`, restamp `timestamp`, **SUPERSEDE (never delete)**
anything replaced, refresh `.context/` and regenerate the graph; and when you **create a new meaningful folder,
scaffold its router + its bundle slice before you finish** so the tree never grows a blind spot. Change only what
the edit touched. If you can't tell whether a folder is meaningful or what it does, **ASK** — don't fabricate a
concept.

---

## Safety, reliability, reversibility (non-negotiable)

- **Never overwrite an original without a snapshot/version.** Use **atomic** writes; allow **rollback**.
- **Any reorganization is reversible:** a plan before execution, a snapshot of the prior state, a movements file
  (`.context/migrations/<date>-reorganization.json`), rollback, and automatic update of known paths.
- **Idempotent.** `events.jsonl` prevents applying the same event twice. Ignore temporaries.
- **No facts without evidence.** Mark inferences; preserve provenance; ask on conflict; don't modify manual
  content outside auto-blocks without need; present a clear summary of everything changed.
- **Automation policy** (`.context/project-profile.json`): inventory/hashing/movement-detection/index-updates/
  link-repairs/stale-marking are automatic; semantic documentation is *propose-then-apply* above a confidence
  threshold; business rules *require approval*; work-file editing *follows user instruction*. Full block:
  [contract.md](contract.md).

---

## Build, validate, visualize

- **[scripts/context.py](scripts/context.py)** (Python 3, stdlib only) — the **deterministic `.context/`
  engine**. `python3 <skill-dir>/scripts/context.py build <root>` derives `manifest.json` + `hashes.json` (from
  the real files) and `catalog.json` + `graph.json` (harvested from the `knowledge/` concept frontmatter +
  cross-links), inits `state.json`, and appends an `events.jsonl` line — **no hand-written JSON**. `--dry-run`
  previews without writing. `python3 <skill-dir>/scripts/context.py check <root>` is the **doctor**: unique
  concept ids, unique aliases across concepts, `source_files` resolve, graph edges reference real nodes, valid
  `confidentiality` — exit 1 on error, plus warnings for manifest drift / a missing Project Contract. Run `build`
  after writing/updating concept pages and after real file changes; run `check` as a gate. Reuses `snapshot.py`
  (hashing) and `graph.py` (parsing) so `graph.json` matches the rendered graph.
- **[scripts/validate.py](scripts/validate.py)** (Python 3, stdlib only) — the **shape** gate: every meaningful
  folder has `AGENTS.md` + `CLAUDE.md`, the `@AGENTS.md` stub exact, the single `knowledge/` bundle exists with
  its `index.md`, every concept has a non-empty `type`, links resolve (relative + bundle-relative `/…`),
  `resource:` and supersede pointers resolve, `status` valid, timestamps parse. Run it on the **generated tree**
  (`python3 <skill-dir>/scripts/validate.py <tree>`), after building and after real changes. Add a root
  `.okfignore` (one glob per line) to skip folders you deliberately don't document. Pair it with the fresh-eyes
  comprehension check — ship only when both pass. *(`source_files:` resolution, alias uniqueness, and `.context/`
  integrity are enforced by `context.py check` — the doctor — run alongside this shape gate. Kept separate on
  purpose: `validate.py` = shape, `context.py check` = context, like a project `doctor`.)*
- **[scripts/graph.py](scripts/graph.py)** — ONE graph for the whole bundle: `python3 <skill-dir>/scripts/graph.py
  <root>/knowledge` writes `knowledge/knowledge-graph.html` (nodes = concepts, edges = cross-links + supersedes,
  colored by `type`). Always use the bundled script as-is; re-run it on every real change. Data is embedded.

---

## Honesty notes (state these plainly)

- **A skill is not a runtime.** This skill runs during an invocation. "Keeping the context alive without a new
  invocation" is done by the **optional** watcher/hooks (real software with real limits — a sleeping laptop never
  runs a cron job; a cloud placeholder with no local bytes can't be hashed) or by the agent running inline. There
  is no bundled always-on service and no bundled web UI — the interface is the assistant chat.
- **Python is a real dependency** for the `.context/` engine (`snapshot.py`, `validate.py`, `graph.py`). On a
  fresh machine it may be missing — **degrade gracefully**: still build the Markdown and still chat, but tell the
  user plainly that the automatic *what-changed* tracking, the graph and the gate turn on once they install
  Python (https://www.python.org/downloads/). Don't loop on a failed script.
- **Auto-load is a harness feature tied to the filenames `CLAUDE.md` / `AGENTS.md`.** Claude Code reads
  `CLAUDE.md`, not `AGENTS.md`; the `@AGENTS.md` stub bridges. `knowledge/` and `.context/` are opened on demand —
  that lazy boundary is the whole point.
- **What in `.context/` is script-generated vs. agent-authored.** The agent authors **meaning ONCE** — in the
  `knowledge/` concept-page frontmatter (`id`, `aliases`, `source_files`, `local_documentation`) and the markdown
  cross-links. **`context.py build` then DERIVES the whole machine layer deterministically** from that + the real
  files: `manifest.json`, `hashes.json`, `catalog.json`, `graph.json`, `state.json`, and an `events.jsonl` line.
  So there is no hand-written JSON: same input → same output. `context.py check` is the **doctor** (unique ids,
  unique aliases, `source_files` resolve, graph edges reference real nodes, valid confidentiality). `extracted/`
  (slide/tab/formula text) + per-slide/sheet hashes + a per-cell formula map are populated by `build` **when
  OfficeCLI is installed** (else empty, file-level hashes) — so change detection reaches slide/tab and
  formula-by-formula. This is the spec's determinism boundary made real: deterministic to detect/map/validate/apply;
  agent to interpret (what a concept
  IS, which alias, which source) — and it writes that interpretation in ONE place, the concept page.
- **The `.context/` JSONs don't make interpretation 100% deterministic** — they make the *mechanical* parts
  deterministic and hand the LLM a small, verifiable set of candidates instead of the whole project.
- **Descriptions drift** from the artifacts they point at — which is why every doc carries a `timestamp`, every
  concept a `last_verified` hash, and why the self-maintenance pipeline exists.
