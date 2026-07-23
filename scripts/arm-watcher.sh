#!/usr/bin/env bash
# arm-watcher.sh — arm the agent-friendly-docs reconciliation watcher on a tree.
#
# Agnostic: any local path (incl. a locally-synced SharePoint / OneDrive / Drive
# folder) or a git checkout, driven by ANY headless agent runner.
#
# Usage:  arm-watcher.sh <TARGET_DIR> [--runner "<cmd>"] [--cron "<expr>"] [--install]
# Defaults: --runner 'claude -p'   --cron '30 7 * * 1-5'   (07:30, weekdays)
# Examples:
#   arm-watcher.sh ~/SharePoint/ClientX
#   arm-watcher.sh ~/SharePoint/ClientX --runner "codex exec" --cron "0 * * * *" --install
set -euo pipefail

usage() {
  echo "usage: arm-watcher.sh <TARGET_DIR> [--runner \"<cmd>\"] [--cron \"<expr>\"] [--install]"
  echo "  --runner   headless agent command (default: 'claude -p'; e.g. 'codex exec', 'gemini -p')"
  echo "  --cron     cron schedule (default: '30 7 * * 1-5')"
  echo "  --install  write the line into your crontab (default: print only)"
}

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET=""; RUNNER="claude -p"; CRON="30 7 * * 1-5"; INSTALL=0
while [ $# -gt 0 ]; do
  case "$1" in
    --runner) RUNNER="${2:?--runner needs a value}"; shift 2 ;;
    --cron)   CRON="${2:?--cron needs a value}"; shift 2 ;;
    --install) INSTALL=1; shift ;;
    -h|--help) usage; exit 0 ;;
    -*) echo "unknown option: $1" >&2; usage; exit 1 ;;
    *) TARGET="$1"; shift ;;
  esac
done
[ -n "$TARGET" ] || { usage; exit 1; }
[ -d "$TARGET" ] || { echo "not a directory: $TARGET" >&2; exit 1; }
TARGET="$(cd "$TARGET" && pwd)"

# Resolve the runner's binary to an absolute path. cron runs with a minimal
# PATH (/usr/bin:/bin), so a bare 'claude'/'codex'/'gemini' resolves to exit 127
# ("command not found") and the watcher silently never fires.
RUNNER_CMD="${RUNNER%% *}"; RUNNER_ARGS="${RUNNER#"$RUNNER_CMD"}"
RUNNER_BIN="$(command -v "$RUNNER_CMD")" || {
  echo "runner not found on PATH: $RUNNER_CMD" >&2
  echo "install it, or pass an absolute path via --runner \"/abs/path -p\"" >&2
  exit 1
}
RUNNER="$RUNNER_BIN$RUNNER_ARGS"

# Deploy into a hidden .okf/ (dotted → pruned by validate.py's dir exclusion, so
# arming the watcher never trips the validator on a router-only "mother" root).
# The prompt calls its helper scripts by .okf/-relative paths (cron's cwd is
# $TARGET), so they must live BESIDE the prompt — the skill's own scripts/ dir is
# not on the cron PATH, and a scheduled run can't reach it otherwise.
mkdir -p "$TARGET/.okf"
cp "$HERE/watcher-prompt.txt" "$TARGET/.okf/watcher-prompt.txt"
COPIED_SCRIPTS=""
for s in artifact-diff.py validate.py snapshot.py; do
  if [ -f "$HERE/$s" ]; then
    cp "$HERE/$s" "$TARGET/.okf/$s"
    COPIED_SCRIPTS="$COPIED_SCRIPTS $s"
  fi
done

LINE="$CRON  cd \"$TARGET\" && $RUNNER \"\$(cat .okf/watcher-prompt.txt)\" >> .okf/.watcher.log 2>&1"

echo "Prompt installed -> $TARGET/.okf/watcher-prompt.txt"
echo "Scripts installed ->$COPIED_SCRIPTS (in .okf/)"
echo "Runner          -> $RUNNER"
echo
echo "Cron line:"
echo "  $LINE"
echo

if [ "$INSTALL" -eq 1 ]; then
  TMP="$(mktemp)"
  crontab -l 2>/dev/null | grep -vF "cd \"$TARGET\" && " > "$TMP" || true
  echo "$LINE" >> "$TMP"
  crontab "$TMP"
  rm -f "$TMP"
  echo "Installed into crontab. Verify with: crontab -l"
else
  echo "Dry run — nothing installed. Re-run with --install, or paste the line via 'crontab -e'."
fi
