# The document-type contract (MECE), the Project Contract, and the automation policy

Open this when you set up a project or when you're deciding *which file owns a fact*. The reasoning is in
[SKILL.md](SKILL.md); the file shapes are in [shape.md](shape.md).

---

## 1. Type exclusivity is what makes self-update reliable

The single biggest failure mode of "docs that rot" is **blurred types** — when it's unclear whether something is
knowledge, a rule, an index entry, or history, the agent doesn't know what to update, so it updates the wrong
thing or nothing. **Fix it at the root: every file type answers exactly ONE kind of question, and every fact has
exactly ONE canonical owner.** Then self-maintenance is mechanical — a change maps to a known owner, and the type
tells the agent what to do with it.

| Artifact | The one question it answers |
|---|---|
| `knowledge/index.md` | What knowledge exists, and where do I start? |
| `knowledge/overview.md` | What is the project — its scope and current state? |
| A page in `knowledge/` (`systems/`, `processes/`, `topics/`, `people/`) | What does this concept mean, and which files back it? |
| `knowledge/log.md` | What changed that mattered, when, and with what consequence? |
| local `index.md` | What's in this folder, and where do I navigate? |
| local `overview.md` | How does this unit work — its inputs, outputs, validations? |
| `AGENTS.md` / `CLAUDE.md` | How should the agent work here, and what are the limits? |
| `sources/meetings/` | What was discussed and recorded in meetings? |
| the real files | What is the actual source, implementation, or deliverable? |
| `.context/` | What is the derived technical state for indexing and maintenance? |

**Canonical owner, worked example.** "Resultados XPTO" is *defined* once in
`knowledge/systems/resultados-xpto.md`; its technical working lives in `endpoint_sql/overview.md`; the change on
23/07 is a line in `knowledge/log.md`; the evidence is the 23/07 meeting note; the real calculation is in the SQL
or the spreadsheet. A fact may be *mentioned* in several places, but it is *owned* in exactly one — and updates
go to the owner.

**Self-maintenance uses the table directly:** a structural change touches indexes/paths/catalog; a semantic
change touches the owning concept page (+ `log.md` if it mattered); a cosmetic change touches nothing. The type
of the changed thing selects the response — no guessing.

---

## 2. The Project Contract

Setup is a brief discovery, like a kickoff. Build the contract *with* the user, store it machine-form in
`.context/project-profile.json`, and present it in human language in `knowledge/overview.md`.

```yaml
# .context/project-profile.json  (shown as YAML for readability)
project:
  name: Incubadora
  type: continuous-operation          # consulting | research | continuous-operation | product | mixed
  objective: Track and accelerate sellers at the start of their journey
  lifecycle: continuous               # one-off | continuous

organization:
  current_structure: preserve         # preserve | reorganize
  preferred_style: numbered-folders   # numbered-folders | plain-names
  may_move_files: false
  may_rename_files: false
  archive_policy: propose             # propose | auto | never

knowledge:
  canonical_sources:
    - results spreadsheets
    - approved documents
  meeting_notes_are_evidence: true
  automatic_updates: structural-only  # structural-only | none
  semantic_updates: propose           # propose | auto-above-threshold

deliverables:
  - dashboard
  - executive presentation
  - monthly report

review:
  required_for:
    - business rules
    - conflicts between sources
    - moving critical files

front_door:                           # the OPTIONAL non-engineer layer (see SKILL.md)
  launcher: false                     # true → drop the one-click launcher in the root
  watcher: false                      # true → arm reconcile-on-open / scheduled watcher
  forcing_hooks: false                # true → install the SessionStart/Stop + pre-commit gate
```

**Alignment flow:** short interview → initial folder read → proposed understanding of the project → proposed
structure & rules → user corrects or approves → skill builds the baseline. **Always show your understanding and
get an explicit yes before building** (the block in [SKILL.md](SKILL.md)). This is the step that prevents
inferring the wrong architecture.

**Progressive refinement.** The initial understanding isn't final. As the project evolves, *suggest* adjustments
based on observable patterns — never execute a relevant reorganization silently:

> *This folder started getting weekly meeting notes — want a permanent meetings area?*
> *12 files now share the same theme — create a "Financial Results" front?*

---

## 3. The automation policy (lives inside `project-profile.json`)

The default policy — deterministic housekeeping is automatic; meaning changes are proposed; business rules and
file edits are gated:

```yaml
automation:
  inventory: automatic
  hashing: automatic
  movement_detection: automatic
  index_updates: automatic
  link_repairs: automatic
  stale_marking: automatic
  duplicate_event_prevention: automatic

  semantic_documentation:
    mode: propose_then_apply
    minimum_confidence: 0.90

  business_rules:
    mode: require_approval

  meeting_interpretation:
    mode: propose_then_apply

  work_file_editing:
    mode: follow_user_instruction
```

Read this against the change classes in [SKILL.md](SKILL.md): **structural → automatic**, **cosmetic → nothing**,
**semantic → propose_then_apply (approval when impact/ambiguity)**. Business-rule changes always require a human.

---

## 4. Reversibility (every reorganization)

Any move/rename produces: a **plan** before execution; a **snapshot** of the prior state; a **movements file**
`.context/migrations/<date>-reorganization.json`; **rollback**; and automatic update of known paths. Never
overwrite an original without a snapshot/version; writes are atomic. When in doubt, KEEP (contextualize only).
