#!/usr/bin/env bash
# okf-stale-hook.sh — FORCE the docs to stay in sync with the files.
#
# Wired as a SessionStart AND Stop hook in the target folder's
# .claude/settings.json (see SKILL.md "Forcing updates"). It runs the
# deterministic staleness check and:
#   - SessionStart → if stale, injects "catch up first" into the agent's context.
#   - Stop         → if stale, BLOCKS the agent from finishing (exit 2) so it
#                    cannot forget to reconcile, even when context is tight.
#
# Self-contained: the skill copies snapshot.py next to this file, so the hook has
# no dependency on where the skill lives. Runs deterministically, outside the chat.
set -u

DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
SNAP="$DIR/.claude/hooks/snapshot.py"
INPUT="$(cat)"

# The staleness engine must be present; if not, never block.
[ -f "$SNAP" ] || exit 0

EVENT="$(printf '%s' "$INPUT" | python3 -c 'import sys,json
try: print(json.load(sys.stdin).get("hook_event_name",""))
except Exception: print("")' 2>/dev/null)"
STOP_ACTIVE="$(printf '%s' "$INPUT" | python3 -c 'import sys,json
try: print(json.load(sys.stdin).get("stop_hook_active",False))
except Exception: print(False)' 2>/dev/null)"

REPORT="$(python3 "$SNAP" check "$DIR" 2>/dev/null)"
CODE=$?

# CODE 3 = stale. Anything else (0 in-sync, or an error) never blocks.
[ "$CODE" -eq 3 ] || exit 0

case "$EVENT" in
  SessionStart)
    echo "The documents changed since the docs were last updated. BEFORE anything else, run the '## Catch up on changes' protocol from AGENTS.md: reconcile index.md / log.md for the changes below, then refresh the snapshot. Details:"
    echo "$REPORT"
    exit 0
    ;;
  Stop)
    # Already re-entered once → don't trap the agent in a loop.
    [ "$STOP_ACTIVE" = "True" ] && exit 0
    echo "Documentation is OUT OF SYNC with the files — do NOT finish yet. Update index.md / log.md for the changes below, then run 'python3 .claude/hooks/snapshot.py write <folder>' for each changed folder to clear this gate." 1>&2
    echo "$REPORT" 1>&2
    exit 2
    ;;
  *)
    exit 0
    ;;
esac
