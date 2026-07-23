# Organize a folder with AI — download & use

Pick one of your folders (decks, spreadsheets, PDFs, notes) and the AI sets it up so it can navigate it and
answer questions — and it keeps itself updated as you and your teammates add and change files.

You only need **one file**, and about 10 minutes the first time.

---

## Step 1 — Download the right file

| Your computer | Download this file |
|---|---|
| **macOS** | [`Organize a folder with AI.command`](https://github.com/catu46/agent-friendly-knowledge-docs/blob/main/distribute/Organize%20a%20folder%20with%20AI.command) |
| **Windows** | [`Organize a folder with AI.bat`](https://github.com/catu46/agent-friendly-knowledge-docs/blob/main/distribute/Organize%20a%20folder%20with%20AI.bat) |

**How to download from GitHub:** click the link above → on the file page click the **download icon** (⬇,
"Download raw file") near the top-right. The file lands in your **Downloads** folder.

> *(If a colleague sent you the file directly on Teams/email/Drive, just save it — skip to Step 2. On **Mac**,
> ask them to send it **zipped** — see the Mac note below.)*

## Step 2 — Put it somewhere handy

From your **Downloads** folder, **drag it to your Desktop** so it's easy to find — or just double-click it right
there in Downloads. Either works.

## Step 3 — Open it

**Double-click the file.**

The **first time**, your computer shows a one-time safety warning (normal — the file came from the internet):

- **macOS:** right-click the file → **Open** → **Open**
- **Windows:** **More info** → **Run anyway**

> ### ⚠️ Mac note — if double-clicking just opens a text window
> macOS removes the "may run" permission from files downloaded from the web, so the `.command` can refuse to
> run. The easy fix: get it **zipped**. Ask whoever shared it to **right-click the file → Compress**, send you
> the `.zip`, and you **double-click the .zip to unzip** — the unzipped file runs normally. (A technical
> colleague can instead make it runnable with one command.) **Windows `.bat` files don't have this issue.**

## Step 4 — One-time setup (the app helps you)

You need two things, once per computer. If either is missing, the app **offers to install it for you** — just
say **yes**.

1. **An assistant** — Claude Code **or** Codex:
   - Claude Code — https://claude.com/claude-code
   - Codex — https://learn.chatgpt.com/docs/codex/cli
2. **Python** — powers the automatic "what changed" tracking. If it's missing the app asks and installs it
   (macOS: Apple's installer; Windows: `winget`), then continues on its own. You can also skip it — setup and
   chat still work; the tracking just turns on once Python is there.

## Step 5 — Use it

1. **Pick the folder** you want to organize (a window opens).
2. **Pick the assistant** — `1` = Claude Code, `2` = Codex.
3. **Done** — the AI works right in front of you. It may ask a few questions about the folder (what it is, what
   to skip). That's normal and helps it get things right.

## After that

- To chat with a folder's files any time, double-click the **"Talk to my files"** file that appears inside it.
- Create new folders and files as usual — next time you open the chat, ask **"what changed?"** and it catches
  up (great for folders shared on Drive/SharePoint, where several people edit).

Questions? Ask whoever sent you this file.
