#!/bin/bash
# ─────────────────────────────────────────────────────────────
# Organize a folder with AI
# Double-click, pick a folder and an assistant, and watch the AI
# organize that folder for you. No coding knowledge needed.
# Self-installs on first run: uses the skill sitting next to it if
# you have the whole repo, otherwise downloads it from GitHub. So
# you can hand someone JUST this file and it still works.
# (agent-friendly-knowledge-docs)
# ─────────────────────────────────────────────────────────────

SKILL_NAME="agent-friendly-knowledge-docs"
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
TARBALL="https://github.com/catu46/${SKILL_NAME}/archive/refs/heads/main.tar.gz"
SKILL_HOME="$HOME/.agents/skills/$SKILL_NAME"

clear
if [ -t 1 ]; then
  B=$'\033[1m'; DIM=$'\033[2m'; BLUE=$'\033[38;5;68m'; GREEN=$'\033[38;5;71m'; R=$'\033[0m'
else B=""; DIM=""; BLUE=""; GREEN=""; R=""; fi

printf '\n   %s%sLet'\''s organize a folder with AI 🗂️%s\n\n' "$B" "$BLUE" "$R"
printf '   I'\''ll set up a folder of yours so AI can navigate it and keep it\n'
printf '   organized. Two clicks: pick the folder, pick the assistant.\n\n'
printf '   %s──────────────────────────────────────────────%s\n\n' "$DIM" "$R"

# 1) Install the skill for both assistants (idempotent).
# The skill files may sit next to this app, or one level up (app lives in distribute/).
if [ -f "$SKILL_DIR/SKILL.md" ]; then SKILL_ROOT="$SKILL_DIR"
elif [ -f "$SKILL_DIR/../SKILL.md" ]; then SKILL_ROOT="$(cd "$SKILL_DIR/.." && pwd)"
else SKILL_ROOT=""; fi

if [ -n "$SKILL_ROOT" ]; then
  # Running from inside the skill repo → link this copy.
  # ln -sfn (re)creates the link even if a previous one went dangling after a move.
  for base in "$HOME/.claude/skills" "$HOME/.agents/skills"; do
    mkdir -p "$base"
    ln -sfn "$SKILL_ROOT" "$base/$SKILL_NAME" 2>/dev/null
  done
else
  # Handed as a standalone file → download the skill once from GitHub.
  if [ ! -d "$SKILL_HOME" ]; then
    printf '   %sSetting up for the first time (one-time download)…%s\n' "$DIM" "$R"
    mkdir -p "$HOME/.agents/skills"
    TMP="$(mktemp -d)"
    if curl -fsSL "$TARBALL" | tar -xz -C "$TMP" 2>/dev/null && [ -d "$TMP/${SKILL_NAME}-main" ]; then
      mv "$TMP/${SKILL_NAME}-main" "$SKILL_HOME"; rm -rf "$TMP"
      printf '   %s✓ ready%s\n\n' "$GREEN" "$R"
    else
      rm -rf "$TMP"
      printf '\n   %sCouldn'\''t download.%s Check your internet and try again.\n\n' "$B" "$R"
      exit 1
    fi
  fi
  mkdir -p "$HOME/.claude/skills"
  ln -sfn "$SKILL_HOME" "$HOME/.claude/skills/$SKILL_NAME" 2>/dev/null
fi

# 1b) Python powers the automatic "what changed" tracking + checks. Offer to install
# it via the native macOS installer (Command Line Tools, which include python3).
if ! command -v python3 >/dev/null 2>&1; then
  printf '   %sPython isn'\''t installed%s — it powers the automatic change-tracking.\n' "$B" "$R"
  printf '   Install it now?  %s[y]%s yes   /   %s[n]%s skip for now: ' "$B" "$R" "$B" "$R"
  read -r pyans
  printf '\n'
  case "$pyans" in
    y|Y|s|S|yes|sim)
      # xcode-select --install pops the native GUI installer (Command Line Tools
      # include python3). Then wait for it to finish and continue automatically.
      printf '   %sOpening the macOS installer for Python…%s click "Install" and let it run.\n' "$DIM" "$R"
      xcode-select --install 2>/dev/null || true
      printf '   %sWaiting for Python to finish installing (a few minutes)… Ctrl-C to cancel.%s\n' "$DIM" "$R"
      tries=0
      until python3 --version >/dev/null 2>&1; do
        sleep 5; tries=$((tries + 1))
        [ $((tries % 12)) -eq 0 ] && printf '   %s…still installing…%s\n' "$DIM" "$R"
        if [ "$tries" -ge 240 ]; then   # ~20 min cap
          printf '\n   %sThis is taking a while.%s When it'\''s done, double-click this app again.\n\n' "$B" "$R"
          exit 0
        fi
      done
      printf '   %s✓ Python is ready — continuing.%s\n\n' "$GREEN" "$R"
      ;;
    *)
      printf '   %sOK, skipping — the automatic tracking stays off until Python is installed.%s\n\n' "$DIM" "$R"
      ;;
  esac
fi

# 2) Native folder picker.
printf '   Opening a window to choose the folder…\n'
TARGET="$(osascript -e 'try
POSIX path of (choose folder with prompt "Which folder should the AI organize?")
end try' 2>/dev/null)"
if [ -z "$TARGET" ]; then
  printf '\n   %sNo folder chosen — nothing to do. You can close this window.%s\n\n' "$DIM" "$R"
  exit 0
fi
TARGET="${TARGET%/}"
printf '   %sFolder:%s %s\n\n' "$B" "$R" "$TARGET"

# 3) Which assistant?
have() { command -v "$1" >/dev/null 2>&1; }
have_claude=0; have claude && have_claude=1
have_codex=0;  have codex  && have_codex=1
status() { if [ "$1" -eq 1 ]; then printf '%s✓ installed%s' "$GREEN" "$R"; else printf "%s— not installed%s" "$DIM" "$R"; fi; }

printf '   %sWhich assistant should organize it?%s\n\n' "$B" "$R"
printf '   %s[1]%s Claude Code   ' "$B" "$R"; status "$have_claude"; printf '\n'
printf '   %s[2]%s Codex         ' "$B" "$R"; status "$have_codex";  printf '\n\n'
printf '   Type 1 or 2 and press Enter: '
read -r choice
printf '\n'
case "$choice" in 2) sel=codex; name="Codex"; installed=$have_codex; url="https://learn.chatgpt.com/docs/codex/cli" ;;
                  *) sel=claude; name="Claude Code"; installed=$have_claude; url="https://claude.com/claude-code" ;; esac

if [ "$installed" -ne 1 ]; then
  printf "   %s%s isn'\''t installed yet.%s Install it once, then run this again:\n" "$B" "$name" "$R"
  printf '   %s%s%s\n\n' "$BLUE" "$url" "$R"
  open "$url" >/dev/null 2>&1
  exit 0
fi

# 4) Apply the skill inside the chosen folder.
cd "$TARGET" || { printf '   Could not open that folder.\n'; exit 1; }
PROMPT="Use the $SKILL_NAME skill to organize this folder (the current directory) so an AI can navigate it and keep it updated. Interview me in my language, then set it up."
printf '   %sOrganizing your folder now — watch below.%s\n' "$GREEN" "$R"
printf '   %s(If it just opens a chat, type: "organize this folder for AI".)%s\n\n' "$DIM" "$R"

if [ "$sel" = codex ]; then codex "$PROMPT"; else claude "$PROMPT"; fi

printf '\n   %sDone! Your folder is set up. You can close this window 👋%s\n\n' "$BLUE" "$R"
