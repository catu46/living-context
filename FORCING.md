# Forcing updates — the strong gate

A dumb script cannot **write** the doc updates (summarizing "the model changed, revenue is now X because Y"
needs the assistant's judgment). But it **can force the update to happen**, deterministically, outside the chat
— so the docs can't silently rot even when the assistant forgets due to a full context window.

The gate has three enforcement points, all built on **one deterministic check**:
`python3 <hooks>/snapshot.py check <root>` → exits **3** if there's anything to catch up on, **0** if the tree is
fully in sync. It flags **two** kinds of drift:
- **STALE** — a tracked folder whose artifacts changed since its snapshot (a re-saved spreadsheet, a new/renamed
  deck).
- **NEW / UNSCAFFOLDED** — a folder that holds real files but has **no docs yet** — i.e. a brand-new folder
  someone created outside the chat. This is what makes new-folder scaffolding a hard guarantee, not just a soft
  instruction: the `Stop` hook won't let the agent finish while an undocumented folder exists.

## 1. Claude Code hooks (block the chat) — the primary force

The skill drops, into the mother folder:

```
<root>/.claude/
├── settings.json          # merged from hooks/settings.json.template
└── hooks/
    ├── okf-stale-hook.sh   # from this skill's hooks/
    └── snapshot.py         # copied so the hook is self-contained
```

- **`SessionStart` hook** → on opening the folder, if stale, injects *"catch up first"* + the change list into
  the agent's context, so the reconcile happens before anything else.
- **`Stop` hook** → when the agent tries to finish, if stale, **blocks it** (exit 2) and feeds back *"update the
  docs first"*. The agent literally cannot end the turn without reconciling. A loop-guard (`stop_hook_active`)
  means it blocks once, not forever.

Deploy (loop step 9): create `<root>/.claude/hooks/`, copy `okf-stale-hook.sh` + `scripts/snapshot.py` there
(`chmod +x` the hook), and merge `hooks/settings.json.template` into `<root>/.claude/settings.json` (create it
if absent; if it exists, merge the `hooks` keys, don't clobber). **Install it by default** — it's the
self-maintenance the user asked for; don't gate it behind a yes/no. Just tell them in one plain sentence what it
does (it changes how Claude Code behaves in that folder: reminding the assistant to update the docs when files
change). A clearly technical user, or one who says no, can skip it.

## 2. The launcher check (covers Codex too)

Hooks are a **Claude Code** feature — they don't fire under Codex. So the launcher also runs the same check on
open: if stale, it prints a visible banner (*"⚠️ Files changed since last time — ask me 'what changed?' first"*)
before handing off to the chat. Belt and suspenders for whichever assistant the user picked.

## 3. Honest limits

- The gate **detects and blocks**; the assistant still does the actual reconcile. That's the correct division —
  detection is deterministic, summarization is judgment.
- **Expect questions.** When the gate flags a NEW or unfamiliar folder, the assistant should **ask the user
  what it is** before documenting it — it must not invent an `index.md` for a folder it doesn't understand.
  Being asked "what is this folder?" is the system working, not a bug.
- Hooks bind to **this folder** (project-level `.claude/settings.json`); they don't affect the user's other
  work. **They apply when the session's project root is this folder** — i.e. when the user opens the tree via
  the root launcher (or `claude`/`codex` at the root). If someone opens `claude` *directly inside a subfolder*,
  the root `.claude/settings.json` may not be in scope, so drop the hooks at the root the user actually opens
  (the launcher lives at the root for exactly this reason), and rely on the launcher's own check for Codex.
- Under **Codex**, only the launcher banner fires (no Stop-block). That's the honest ceiling of a non-Claude
  assistant.
- The check compares file **bytes** (sha256) against the snapshot, so it catches changed numbers in a re-saved
  spreadsheet — not just new/deleted files.
