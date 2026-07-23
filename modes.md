# Modes, organization sub-modes, and adaptive structures

Open this at setup. Both scenarios converge on the **same engine** and the **same self-maintenance**; only the
ratio of create-vs-reorganize differs, and it's self-evident from what you read. Reasoning: [SKILL.md](SKILL.md).

---

## Auto-detect the mode (user can override)

```
Empty / near-empty folder   → suggest Mode B ("Start a project")
Folder with many files      → suggest Mode A ("Understand an existing project")
```

After setup, both modes use the same maintenance flow.

---

## Mode A — existing project

The folder already has material. The skill:

1. surveys the current structure;
2. **preserves the existing organization by default**;
3. identifies main files, old versions, duplicates, temporary artifacts;
4. classifies sources / analyses / deliverables / references / meetings;
5. infers core concepts;
6. builds `knowledge/`;
7. builds local documentation only where it earns its place;
8. builds the `.context/` baseline;
9. **flags questions and inconsistencies before changing anything relevant.**

Example initial output:

```
Found: 9 presentations · 6 spreadsheets · 18 PDFs · 4 meeting docs · 3 apparent version groups ·
8 core concepts · 2 possible inconsistencies between spreadsheets and decks.

Proposal: a wiki of 8 concept pages · mark 5 files as canonical sources · treat 2 folders as history ·
local docs in 3 work-units · keep the current file structure.
```

**Never reorganize the whole folder without approval.** Within Mode A, the user picks one of three:

### A1 — Contextualize only (safe default)
Preserve structure; **no moves, no renames**; build `knowledge/`, `.context/`, local docs where needed; flag
organization problems but don't fix them without approval. This is the default.

### A2 — Organize with approval
Analyze → identify redundant folders, versions, loose files, possible groupings → **propose a new structure** →
show a **move plan** → execute only after approval → update references, indexes, catalog after the move.

```
Reorg proposal
- move 8 meeting notes → 04. Reuniões/
- move 5 reference files → 02. Referências/
- consolidate 3 old versions → 99. Arquivo/
- keep the two current decks in 06. Entregáveis/
- do NOT move the main spreadsheet (external links)
```

### A3 — Auto-organize within explicit limits
The user authorizes **objective** rules only; optional and reversible:

```yaml
organization:
  auto_move: { meeting_notes: true, obvious_archives: true, temporary_files: true }
  require_approval:
    spreadsheets_with_external_links: true
    presentations_marked_final: true
    files_used_by_other_documents: true
    ambiguous_files: true
```

Every reorganization is reversible (plan + snapshot + migrations file + rollback — see [contract.md](contract.md) §4).

---

## Mode B — starting a project

Little or no material (empty folder, a few starter files, or just an idea/briefing/kickoff note). Start with a
**short interview**: objective · main expected result · deliverable types · known workstreams · people/areas ·
internal terms & acronyms · where sources/analyses/deliverables/meetings will live · what may update
automatically · what needs approval.

Then propose a **minimal** structure — don't invent `systems/`/`processes/`/`topics/` or empty local docs before
content justifies them. Seed pages with **explicit status** so hypotheses are never presented as fact:

```yaml
status: draft
confidence: user-provided
source: initial-interview
```

As files, meetings and analyses arrive, the skill: registers new material → associates it to existing concepts →
creates new concepts when needed → **replaces hypotheses with verified information** → updates project state →
keeps traceability between knowledge and sources.

Minimal Mode-B baseline:

```
PROJECT/
├── CLAUDE.md
├── knowledge/ { index.md, overview.md, log.md }
├── sources/meetings/inbox/
├── <deliverables/analyses/references — per the chosen profile>
└── .context/
```

---

## Adaptive structure (Mode B) — proposed, never imposed

Infer the profile from the interview; explain the logic of each folder before creating it; combinations allowed.
Ask: one-off or continuous? · analytical / creative / operational / technical? · which deliverables? · clear
stages? · sources to preserve? · a meeting cadence? · one person or a team? · numbered folders or plain names? ·
any company standard already in place? The skill may incorporate an existing folder-organizer step to interview,
propose a taxonomy, create approved folders, classify starter material, and register the structure — kept
**decoupled** from the self-maintenance runtime (it helps set up/reorganize; the engine maintains afterward).

**Consulting / strategy**
```
00. Gestão do Projeto/ · 01. Briefing e Escopo/ · 02. Referências/ · 03. Análises/ · 04. Reuniões/
05. Work in Progress/ · 06. Entregáveis/ · 99. Arquivo/ · knowledge/ · .context/
```

**Research**
```
01. Pergunta e Hipóteses/ · 02. Fontes/ · 03. Base de Evidências/ · 04. Análises/ · 05. Sínteses/
06. Entregáveis/ · knowledge/ · .context/
```

**Continuous operation**
```
01. Operação Atual/ · 02. Processos/ · 03. Indicadores/ · 04. Reuniões/ · 05. Melhorias/
06. Materiais de Apoio/ · knowledge/ · .context/
```

**Product / implementation**
```
01. Contexto e Escopo/ · 02. Requisitos/ · 03. Desenho da Solução/ · 04. Implementação/
05. Testes e Validação/ · 06. Rollout/ · 07. Operação/ · knowledge/ · .context/
```

---

## KEEP or REDESIGN? (ask early — it changes everything)

Two very different jobs hide behind "organize my folders." Ask explicitly, up front.

- **KEEP (default).** The folders are organized the way the user likes; just make them agent-navigable and
  self-maintaining — layer `knowledge/` / `.context/` / routers **on top, without moving or renaming a file.** If
  the user doesn't clearly ask for a redesign, do this. (This is Mode A1.)
- **REDESIGN.** The user wants the *structure itself* rethought. Because it **moves user files it is
  DESTRUCTIVE** — run these phases (this is Mode A2/A3 done carefully):
  1. **MAP** — inventory by reading **content, not filenames**; surface duplicates & versions
     (`v8`/`v8_final`/`v8_final_real`), orphans, misfiled items, stale files, inconsistent names, too-deep nesting.
  2. **UNDERSTAND the mental model — a real back-and-forth, not a form.** Ground every question in the MAP
     (*"you've got `model_v8` and `model_v8_final` — which is real, and how would you have known?"*); a few
     questions at a time, plain language. Dig for: how they think about the work (client? project? phase?
     deliverable type?); what they search *by* (that's the natural top level); who else uses the folders; the
     lifecycle (draft → final → sent → archived) and what's canonical vs scratch.
  3. **DIAGNOSE** — name the specific problems against that model; confirm which actually matter.
  4. **PROPOSE** — pick **ONE primary organizing axis** (the grain); draw a concrete before → after; set
     naming/versioning conventions and where `archive/` and scratch live; keep it shallow.
  5. **CONFIRM, then APPLY carefully** — explicit yes on before→after; **move (never delete)**; keep the original
     arrangement recoverable until validated; **log every move**; on shared Drive/SharePoint, warn plainly that
     moving/renaming breaks everyone else's links and muscle memory. When in doubt, KEEP.

**At scale (hundreds of folders), DECENTRALIZE:** one subagent per subtree writes that subtree's concepts INTO
the single bundle + its routers; roll the per-level `index.md` maps leaf → mid → root so no context holds the
whole tree.
