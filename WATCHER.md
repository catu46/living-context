# The reconciliation watcher — OPTIONAL, v2 (unattended)

> **This is NOT the default.** The default self-maintenance is **reconcile-on-open**: the assistant catches up
> on what changed whenever the user opens the folder (see the `## Catch up on changes` block in the root
> `AGENTS.md`, and *Self-maintenance* in [SKILL.md](SKILL.md)). That needs no cron, no headless auth, and fits
> a laptop that's only on when someone's using it.
>
> **Reach for this scheduled watcher only when the machine is ALWAYS ON** (a server, an always-on desktop) and
> you want the docs to reconcile with nobody present. On a laptop it will disappoint — see the honest limits
> at the bottom before arming it.

When it does apply: a scheduled agent wakes up, reads what changed since the snapshot, updates the **owning
concept in `knowledge/`** + the affected `index.md`, appends to `knowledge/log.md` (append-only), and refreshes
`.context/`. The exact agent instructions live in
**[scripts/watcher-prompt.txt](scripts/watcher-prompt.txt)** — that file is the contract; this page is the
operator's guide.

## What each run does

1. **Discover new scopes** — scaffold any meaningful folder that has artifacts but no docs yet (or queue an
   ask if it's ambiguous).
2. **Detect** — diff the filesystem against each folder's `.okf-state.json` snapshot (by `sha256`, not mtime),
   using the strongest backend available (git → filesystem → Drive/SharePoint API).
3. **Classify** — read each changed file (bounded reads) and decide: data-refresh / new-version / new-file /
   structural / deletion. A **materiality gate** (`artifact-diff.py`) skips cosmetic edits so the docs only
   move when the folder's *contents* actually change.
4. **Apply** — update `index.md` and append one line to `log.md`, append-only, in the owning folder.
5. **Ask when unsure** — queue a question in `ASKS.md` at the tree root instead of guessing; attribute the
   last editor honestly per source.
6. **Rewrite the snapshot** and **report** `validate.py` PASS/FAIL.

## Arming it — `scripts/arm-watcher.sh`

Runner-agnostic; drives any headless agent over any local path (including a synced SharePoint / OneDrive /
Drive folder) or a git checkout.

```
scripts/arm-watcher.sh <TARGET_DIR> [--runner "<cmd>"] [--cron "<expr>"] [--install]
```

- **`--runner`** — the headless agent command. Default `claude -p`; e.g. `codex exec`, `gemini -p`.
- **`--cron`** — schedule. Default `30 7 * * 1-5` (07:30, weekdays).
- **`--install`** — actually write the line into your crontab. **Omit it for a dry run** that just prints the
  line. **Confirm with the user before installing a scheduled job.**

It deploys `watcher-prompt.txt` + `validate.py` + `artifact-diff.py` into a hidden `.okf/` inside the target
(dotted, so `validate.py` prunes it), and resolves the runner to an absolute path (cron runs with a minimal
PATH, so a bare `claude` would silently fail).

```
# dry run first (prints the cron line, installs nothing)
scripts/arm-watcher.sh ~/SharePoint/ClientX
# then, once confirmed:
scripts/arm-watcher.sh ~/SharePoint/ClientX --install
```

## Optional control files (at the tree root)

- **`.okfignore`** — one glob per line; excludes files/folders from both the validator and the watcher.
- **`.okf/always-ask`** — one glob per line; any change to a matching file is **always** queued as an ask and
  never auto-applied, however confident the watcher is (use for sensitive artifacts).
- **`ASKS.md`** — append-only; where the watcher files questions it can't answer. Review it periodically.

## Honest limits — why this is v2, not the default

- **A sleeping/off laptop never runs it, and plain `cron` does NOT catch up.** If the machine is asleep at the
  scheduled time (the normal state of a consultant's laptop), the run is simply skipped — no make-up run. Only
  `launchd` (macOS, fires on wake) or a systemd timer with `Persistent=true` / `anacron` (Linux) catch up;
  `arm-watcher.sh` installs a plain crontab line, which does none of that. **This alone defeats "always current"
  on a laptop** — which is why reconcile-on-open is the default.
- **Headless auth + write permission must be set up, or the run silently does nothing.** A cron `claude -p` has
  no TTY: subscription/Keychain auth often can't unlock, and without `--allowedTools "Edit,Write,Bash"` (or an
  equivalent settings.json) it cannot write `index.md` / `log.md` / the snapshot — it detects changes and then
  can't apply them, re-detecting the same change every run. Errors land in `.okf/.watcher.log`, which nobody
  reads. Prefer API-key auth (env var) for headless, and preflight once with a human present.
- **macOS:** `/usr/sbin/cron` needs Full Disk Access to read Documents/Drive folders, and is deprecated in
  favor of `launchd`.
- **`validate.py PASS` is shape-only** — it cannot tell you the docs are *stale*, only that the files are
  well-formed. Don't read PASS as "the docs are current."
- **Scheduled = next run, not instant;** attribution depends on the source (git author vs Drive "last modified
  by" vs an OS account); the runner needs read access to the source.
