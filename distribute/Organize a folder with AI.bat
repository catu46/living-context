@echo off
REM ---------------------------------------------------------------
REM  Organize a folder with AI
REM  Double-click, pick a folder and an assistant, watch the AI set
REM  that folder up. No coding knowledge needed.
REM  Self-installs on first run: uses the skill next to it if you have
REM  the whole repo, otherwise downloads it from GitHub. So you can hand
REM  someone JUST this file and it still works.
REM  (agent-friendly-knowledge-docs)
REM ---------------------------------------------------------------
chcp 65001 >nul 2>nul
setlocal
set "SKILL_NAME=agent-friendly-knowledge-docs"
set "SKILL_DIR=%~dp0"
if "%SKILL_DIR:~-1%"=="\" set "SKILL_DIR=%SKILL_DIR:~0,-1%"
set "TARBALL=https://github.com/catu46/%SKILL_NAME%/archive/refs/heads/main.tar.gz"
set "SKILL_HOME=%USERPROFILE%\.agents\skills\%SKILL_NAME%"
cls

echo(
echo    Let's organize a folder with AI
echo(
echo    Pick the folder and the assistant, and the AI sets it up.
echo(
echo    ----------------------------------------------
echo(

REM 1) Install the skill for both assistants.
REM The skill files may sit next to this app, or one level up (app in distribute\).
set "SKILL_ROOT="
if exist "%SKILL_DIR%\SKILL.md" set "SKILL_ROOT=%SKILL_DIR%"
if not defined SKILL_ROOT for %%I in ("%SKILL_DIR%\..") do if exist "%%~fI\SKILL.md" set "SKILL_ROOT=%%~fI"
if defined SKILL_ROOT (
  REM Running from inside the skill repo -> junction this copy (no admin needed).
  for %%B in ("%USERPROFILE%\.claude\skills" "%USERPROFILE%\.agents\skills") do (
    if not exist "%%~B" mkdir "%%~B"
    if not exist "%%~B\%SKILL_NAME%\SKILL.md" ( rmdir "%%~B\%SKILL_NAME%" >nul 2>nul & mklink /J "%%~B\%SKILL_NAME%" "%SKILL_ROOT%" >nul 2>nul )
  )
) else (
  REM Handed as a standalone file -> download the skill once from GitHub.
  if not exist "%SKILL_HOME%" (
    echo    Setting up for the first time ^(one-time download^)...
    if not exist "%USERPROFILE%\.agents\skills" mkdir "%USERPROFILE%\.agents\skills"
    curl -fsSL "%TARBALL%" -o "%TEMP%\%SKILL_NAME%.tgz"
    if errorlevel 1 ( echo    Couldn't download. Check your internet and try again. & pause & exit /b 1 )
    tar -xzf "%TEMP%\%SKILL_NAME%.tgz" -C "%USERPROFILE%\.agents\skills"
    move "%USERPROFILE%\.agents\skills\%SKILL_NAME%-main" "%SKILL_HOME%" >nul
    del "%TEMP%\%SKILL_NAME%.tgz" >nul 2>nul
  )
  if not exist "%USERPROFILE%\.claude\skills" mkdir "%USERPROFILE%\.claude\skills"
  if not exist "%USERPROFILE%\.claude\skills\%SKILL_NAME%\SKILL.md" ( rmdir "%USERPROFILE%\.claude\skills\%SKILL_NAME%" >nul 2>nul & mklink /J "%USERPROFILE%\.claude\skills\%SKILL_NAME%" "%SKILL_HOME%" >nul 2>nul )
)
echo(

REM 1b) Python powers the automatic "what changed" tracking + checks. Offer to install
REM it via winget (the Windows Package Manager), else fall back to the download page.
set HAVE_PY=0
where python  >nul 2>nul && set HAVE_PY=1
where python3 >nul 2>nul && set HAVE_PY=1
if "%HAVE_PY%"=="1" goto py_ok
echo    Python isn't installed -- it powers the automatic change-tracking.
choice /c yn /n /m "   Install it now? [y] yes / [n] skip: "
if errorlevel 2 goto py_skip
where winget >nul 2>nul
if errorlevel 1 (
  echo    Opening the Python download page ^(winget isn't available^)...
  start "" "https://www.python.org/downloads/"
  echo    After installing, close this window and double-click again.
  pause
  exit /b 0
)
echo    Installing Python via winget...
winget install -e --id Python.Python.3.13 --accept-source-agreements --accept-package-agreements
if errorlevel 1 (
  echo    winget couldn't install it -- opening the download page instead...
  start "" "https://www.python.org/downloads/"
  echo    After installing, close this window and double-click again.
  pause
  exit /b 0
)
REM Refresh PATH from the registry (winget wrote Python there) so THIS window sees it.
for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')"`) do set "PATH=%PATH%;%%P"
where python >nul 2>nul || where python3 >nul 2>nul
if errorlevel 1 (
  echo    Python installed -- please close this window and double-click again.
  pause
  exit /b 0
)
echo    Python is ready -- continuing...
echo(
goto py_ok
:py_skip
echo    OK, skipping -- tracking stays off until Python is installed.
echo(
:py_ok

REM 2) Native folder picker.
echo    Opening a window to choose the folder...
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms | Out-Null; $f=New-Object System.Windows.Forms.FolderBrowserDialog; $f.Description='Which folder should the AI organize?'; if($f.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK){Write-Output $f.SelectedPath}"`) do set "TARGET=%%I"
if not defined TARGET ( echo    No folder chosen. You can close this window. & pause & exit /b 0 )
echo    Folder: %TARGET%
echo(

REM 3) Which assistant?
set HAVE_CLAUDE=0
where claude >nul 2>nul && set HAVE_CLAUDE=1
set HAVE_CODEX=0
where codex >nul 2>nul && set HAVE_CODEX=1
set "S1=not installed"
if "%HAVE_CLAUDE%"=="1" set "S1=installed"
set "S2=not installed"
if "%HAVE_CODEX%"=="1" set "S2=installed"
echo    Which assistant should organize it?
echo(
echo    [1] Claude Code   %S1%
echo    [2] Codex         %S2%
echo(
choice /c 12 /n /m "   Type 1 or 2: "
if errorlevel 2 ( set "SEL=codex" & set "SELOK=%HAVE_CODEX%" & set "URL=https://learn.chatgpt.com/docs/codex/cli" ) else ( set "SEL=claude" & set "SELOK=%HAVE_CLAUDE%" & set "URL=https://claude.com/claude-code" )

if not "%SELOK%"=="1" (
  echo(
  echo    That assistant isn't installed yet. Install it once, then run this again.
  start "" "%URL%"
  pause & exit /b 0
)

REM 4) Apply the skill in the chosen folder.
cd /d "%TARGET%"
set "PROMPT=Use the %SKILL_NAME% skill to organize this folder (the current directory) so an AI can navigate it and keep it updated. Interview me in my language, then set it up."
echo(
echo    Organizing your folder now -- watch below.
echo(
if "%SEL%"=="codex" ( codex "%PROMPT%" ) else ( claude "%PROMPT%" )
echo(
echo    Done! You can close this window.
echo(
