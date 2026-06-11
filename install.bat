@echo off
REM SpinRender Installation Script for Windows
REM Installs the plugin to every KiCad scripting/plugins directory found

REM Ensure standard Windows utilities (chcp, findstr, reg, xcopy, etc.) are
REM reachable regardless of how this script was launched.
set "PATH=%SystemRoot%\System32;%SystemRoot%;%PATH%"

REM Literal "!" for use in [!EXCL!!EXCL!]-style markers under delayed expansion.
REM Must be set here, before delayed expansion is enabled, since "!" is consumed
REM as an empty-named variable reference once delayed expansion is active.
set "EXCL=!"

setlocal EnableDelayedExpansion
chcp 65001 >nul

REM Generate ESC character for ANSI sequences (works on Windows 10+)
for /f %%a in ('echo prompt $E^| cmd /q') do set "ESC=%%a"
reg add HKCU\Console /v VirtualTerminalLevel /t REG_DWORD /d 1 /f >nul 2>&1

REM Color codes
set "CYAN=!ESC![36m"
set "TEAL=!ESC![38;5;38m"
set "GREEN=!ESC![32m"
set "YELLOW=!ESC![33m"
set "RED=!ESC![31m"
set "BOLD=!ESC![1m"
set "DIM=!ESC![2m"
set "NC=!ESC![0m"

REM Flag parsing
set AUTO_YES=false
set REINSTALL_DEPS=false
set LINK_THEME=false
set UNINSTALL=false
:parse_args
if "%~1"=="" goto end_parse_args
if /i "%~1"=="-y" set AUTO_YES=true
if /i "%~1"=="--yes" set AUTO_YES=true
if /i "%~1"=="--reinstall-deps" set REINSTALL_DEPS=true
if /i "%~1"=="--link-theme" set LINK_THEME=true
if /i "%~1"=="-u" set UNINSTALL=true
if /i "%~1"=="--uninstall" set UNINSTALL=true
if /i "%~1"=="-h" goto show_help
if /i "%~1"=="--help" goto show_help
shift
goto parse_args

:show_help
echo !BOLD!SPINRENDER INSTALLER HELP!NC!
echo Usage: install.bat [options]
echo Options:
echo   !CYAN!-y, --yes!NC!              Automatically overwrite/remove without prompting
echo   !CYAN!--reinstall-deps!NC!       Uninstall dependencies and fonts from KiCad Python before install
echo   !CYAN!--link-theme!NC!           Create a symbolic link for dark.yaml (facilitates live theme editing)
echo   !CYAN!-u, --uninstall!NC!        Completely remove SpinRender from all KiCad environments
echo   !CYAN!-h, --help!NC!             Show this help message
exit /b 0

:end_parse_args

set SCRIPT_DIR=%~dp0
set SOURCE_DIR=%SCRIPT_DIR%SpinRender

REM Parse version from source
set "PLUGIN_VERSION=unknown"
if exist "%SOURCE_DIR%\__init__.py" (
    for /f "tokens=2 delims== " %%a in ('findstr /b /c:"__version__" "%SOURCE_DIR%\__init__.py"') do set "PLUGIN_VERSION=%%~a"
)

REM Compute banner padding: inner box width = 54, fixed prefix = 35 chars.
REM padding = 54 - 35 - len(version) = 19 - len(version)
set "VER_STR=!PLUGIN_VERSION!"
set /a VER_LEN=0
:strlen_loop
if not "!VER_STR!"=="" (
    set "VER_STR=!VER_STR:~1!"
    set /a VER_LEN+=1
    goto strlen_loop
)
set /a PAD_LEN=19-VER_LEN
if !PAD_LEN! LSS 1 set /a PAD_LEN=1
set "PAD="
:pad_loop
if !PAD_LEN! GTR 0 (
    set "PAD=!PAD! "
    set /a PAD_LEN-=1
    goto pad_loop
)

echo !CYAN!┌──────────────────────────────────────────────────────┐!NC!
echo !CYAN!│!NC!  SPINRENDER // PLUGIN_INSTALL // v!PLUGIN_VERSION!!PAD!!CYAN!│!NC!
echo !CYAN!└──────────────────────────────────────────────────────┘!NC!
echo.

if "!REINSTALL_DEPS!"=="true" (
    echo !CYAN![i]!NC! REINSTALL-DEPS MODE
    echo     This will uninstall SpinRender dependencies and remove fonts from KiCad Python environment.

    if "!AUTO_YES!"=="false" (
        <nul set /p "=    Continue? (y/n): "
        choice /c yn /n /m ""
        if errorlevel 2 (
            echo !YELLOW![!EXCL!!EXCL!] ABORTED.!NC!
            exit /b 0
        )
    )

    call :font_removal_notice
    echo !GREEN![OK]!NC! Dependencies and fonts uninstalled.
    echo !CYAN![i]!NC! Proceeding with plugin installation...
    echo.
)

REM Resolve the user's Documents folder — handles OneDrive redirection and other
REM custom locations that %USERPROFILE%\Documents would miss.
REM Uses a temp file to avoid for/f backtick + parenthesised-block parsing issues.
set "PS_EXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
set "DOCS_DIR="
if exist "!PS_EXE!" "!PS_EXE!" -NoProfile -Command "[Environment]::GetFolderPath('MyDocuments')" > "%TEMP%\_sr_docs.tmp" 2>nul
if exist "%TEMP%\_sr_docs.tmp" for /f "usebackq delims=" %%d in ("%TEMP%\_sr_docs.tmp") do set "DOCS_DIR=%%d"
if exist "%TEMP%\_sr_docs.tmp" del "%TEMP%\_sr_docs.tmp" >nul 2>&1
if "!DOCS_DIR!"=="" set "DOCS_DIR=%USERPROFILE%\Documents"

REM Source dir is only required when installing, not when uninstalling.
if "!UNINSTALL!"=="false" (
    if not exist "%SOURCE_DIR%" (
        echo !RED![!EXCL!!EXCL!] CRITICAL_ERROR:!NC! Source directory not found at:
        echo     !DIM!%SOURCE_DIR%!NC!
        exit /b 1
    )
)

set FOUND_COUNT=0

echo !CYAN![i]!NC! SCANNING FOR KICAD ENVIRONMENTS...

for %%v in (10.0 9.0 8.0 7.0) do (
    if exist "!APPDATA!\kicad\%%v" (
        set /a FOUND_COUNT+=1
        set "FOUND_PATH_!FOUND_COUNT!=!DOCS_DIR!\KiCad\%%v\scripting\plugins"
        echo     !GREEN![OK]!NC! FOUND KICAD %%v !DIM!@ !DOCS_DIR!\KiCad\%%v\scripting\plugins!NC!
    )
)

if !FOUND_COUNT! EQU 0 (
    echo !RED![!EXCL!!EXCL!] CRITICAL_ERROR:!NC! No valid KiCad plugin directories found.
    echo     !DIM!Run KiCad at least once to initialize system paths.!NC!
    exit /b 1
)

REM ----------------------------------------------------------------------
REM UNINSTALL MODE: completely remove the plugin from every environment.
REM ----------------------------------------------------------------------
if "!UNINSTALL!"=="true" (
    echo.
    echo !CYAN![i]!NC! UNINSTALL MODE
    echo     This will remove SpinRender from all detected KiCad environments.
    echo     !DIM!Python dependencies and fonts are left untouched ^(they may be in use elsewhere^).!NC!

    if "!AUTO_YES!"=="false" (
        <nul set /p "=    Continue? (y/n): "
        choice /c yn /n /m ""
        if errorlevel 2 (
            echo !YELLOW![!EXCL!!EXCL!] ABORTED.!NC!
            exit /b 0
        )
    )

    echo.
    echo !CYAN![i]!NC! REMOVING FROM ALL !FOUND_COUNT! KICAD ENVIRONMENT^(S^) FOUND.

    set "UNINSTALL_FAILED=false"
    for /l %%i in (1,1,!FOUND_COUNT!) do (
        call :uninstall_from_path "!FOUND_PATH_%%i!"
    )

    echo.
    if "!UNINSTALL_FAILED!"=="true" (
        echo !RED![!EXCL!!EXCL!]!NC! One or more removals failed. Review output above.
        exit /b 1
    )

    echo !GREEN![OK]!NC! UNINSTALL_COMPLETE: SpinRender has been removed.
    exit /b 0
)

call :warn_if_pcm_installed
call :check_ffmpeg

echo.
echo !CYAN![i]!NC! INSTALLING TO ALL !FOUND_COUNT! KICAD ENVIRONMENT(S) FOUND.

set "DEPLOY_FAILED=false"
for /l %%i in (1,1,!FOUND_COUNT!) do (
    call :deploy_to_path "!FOUND_PATH_%%i!"
)

echo.
echo !CYAN![i]!NC! NEXT STEPS:
echo     1. Restart KiCad if active
echo     2. Locate SpinRender in the toolbar
echo        !DIM!or: Tools -^> External Plugins -^> SpinRender!NC!
echo.

if "!DEPLOY_FAILED!"=="true" (
    echo !RED![!EXCL!!EXCL!]!NC! One or more deployments failed. Review output above.
    exit /b 1
)

exit /b 0

REM ----------------------------------------------------------------------
REM Deploy the plugin to a single KiCad plugins directory.
REM   %~1 = target plugins path
REM Sets DEPLOY_FAILED=true on failure; skips (leaves intact) on user decline.
:deploy_to_path
set "TARGET_PATH=%~1"
set "TARGET_DIR=!TARGET_PATH!\SpinRender"

echo.
echo !CYAN![i]!NC! TARGET: !TEAL!!TARGET_DIR!!NC!

if exist "!TARGET_DIR!" (
    if "!AUTO_YES!"=="false" (
        <nul set /p "=    !YELLOW!⚠ EXISTING_INSTALL_DETECTED: Overwrite? (y/n): !NC!"
        choice /c yn /n /m ""
        if errorlevel 2 (
            echo     !YELLOW![!EXCL!!EXCL!] SKIPPED:!NC! Installation left untouched.
            goto :eof
        )
    ) else (
        echo     !YELLOW!⚠ EXISTING_INSTALL_DETECTED:!NC! Overwriting.. !DIM!^(-y/--yes flag used^)!NC!
    )
)

echo !CYAN![i]!NC! DEPLOYING ASSETS TO: !TEAL!!TARGET_DIR!!NC!
REM Clear read-only/hidden attributes before removal: a prior install may have
REM left read-only files (e.g. resources\kicad_config\*) that block rmdir.
if exist "!TARGET_DIR!" attrib -r -h "!TARGET_DIR!\*" /s /d >nul 2>&1
if exist "!TARGET_DIR!" rmdir /s /q "!TARGET_DIR!"

REM If the directory is still present, KiCad may be holding a file lock.
if exist "!TARGET_DIR!" (
    call :prompt_kill_kicad
    if exist "!TARGET_DIR!" rmdir /s /q "!TARGET_DIR!"
)

if exist "!TARGET_DIR!" (
    echo     !RED![!EXCL!!EXCL!] DEPLOYMENT_FAILURE:!NC! Could not clear existing install. Close KiCad and retry.
    set "DEPLOY_FAILED=true"
    goto :eof
)

mkdir "!TARGET_DIR!"
xcopy "%SOURCE_DIR%" "!TARGET_DIR!\" /E /I /H /Y >nul

if not exist "!TARGET_DIR!\__init__.py" (
    echo     !RED![!EXCL!!EXCL!] DEPLOYMENT_FAILURE:!NC! Asset copy verify failed.
    set "DEPLOY_FAILED=true"
    goto :eof
)

call :write_build_stamp "!TARGET_DIR!"

echo     !GREEN!✓ DEPLOYMENT_COMPLETE:!NC! SpinRender is active.

if "!LINK_THEME!"=="true" (
    set "THEME_FILE=resources\themes\dark.yaml"
    set "TARGET_THEME=!TARGET_DIR!\!THEME_FILE!"
    set "SOURCE_THEME=%SOURCE_DIR%\!THEME_FILE!"

    if exist "!SOURCE_THEME!" (
        echo     !CYAN![i]!NC! LINKING THEME: !THEME_FILE!
        if exist "!TARGET_THEME!" del "!TARGET_THEME!"
        mklink "!TARGET_THEME!" "!SOURCE_THEME!" >nul
        echo     !GREEN!✓!NC! Theme symlinked for live editing.
    ) else (
        echo     !YELLOW!⚠ LINK_THEME_WARNING:!NC! Source theme not found at !DIM!!SOURCE_THEME!!NC!
    )
)
goto :eof

REM ----------------------------------------------------------------------
REM Remove the deployed plugin from a single KiCad plugins directory.
REM   %~1 = target plugins path
REM Sets UNINSTALL_FAILED=true on failure; skips (leaves intact) on decline.
:uninstall_from_path
set "TARGET_PATH=%~1"
set "TARGET_DIR=!TARGET_PATH!\SpinRender"

echo.
echo !CYAN![i]!NC! TARGET: !TEAL!!TARGET_DIR!!NC!

if not exist "!TARGET_DIR!" (
    echo     !DIM!No SpinRender installation here. Skipping.!NC!
    goto :eof
)

if "!AUTO_YES!"=="false" (
    <nul set /p "=    !YELLOW!⚠ Remove this installation? (y/n): !NC!"
    choice /c yn /n /m ""
    if errorlevel 2 (
        echo     !YELLOW![!EXCL!!EXCL!] SKIPPED:!NC! Installation left untouched.
        goto :eof
    )
)

REM Clear read-only/hidden attributes before removal: a prior install may have
REM left read-only files (e.g. resources\kicad_config\*) that block rmdir.
attrib -r -h "!TARGET_DIR!\*" /s /d >nul 2>&1
rmdir /s /q "!TARGET_DIR!"

REM If the directory is still present, KiCad may be holding a file lock.
if exist "!TARGET_DIR!" (
    call :prompt_kill_kicad
    if exist "!TARGET_DIR!" rmdir /s /q "!TARGET_DIR!"
)

if exist "!TARGET_DIR!" (
    echo     !RED![!EXCL!!EXCL!] REMOVAL_FAILURE:!NC! Could not delete !TARGET_DIR!
    set "UNINSTALL_FAILED=true"
    goto :eof
)

echo     !GREEN!✓ REMOVED:!NC! SpinRender deleted.
goto :eof

REM ----------------------------------------------------------------------
REM Check if KiCad is running; if so, warn about unsaved work and offer to
REM kill it. Caller retries the rmdir after this returns.
:prompt_kill_kicad
set "KICAD_RUNNING=false"
for %%p in (kicad.exe pcbnew.exe eeschema.exe) do (
    tasklist /fi "imagename eq %%p" 2>nul | find /i "%%p" >nul 2>&1
    if not errorlevel 1 set "KICAD_RUNNING=true"
)
if "!KICAD_RUNNING!"=="false" goto :eof

echo.
echo     !YELLOW!⚠  KICAD IS RUNNING — plugin files may be locked.!NC!
echo     !RED!   WARNING: Killing KiCad will close it immediately.!NC!
echo     !RED!            Any UNSAVED WORK will be LOST.!NC!
echo.
<nul set /p "=    Kill KiCad and retry? (y/n): "
choice /c yn /n /m ""
if errorlevel 2 goto :eof

for %%p in (kicad.exe pcbnew.exe eeschema.exe) do (
    taskkill /f /im %%p >nul 2>&1
)
echo     !DIM!Waiting for KiCad to close...!NC!
timeout /t 2 /nobreak >nul
goto :eof

REM ----------------------------------------------------------------------
REM Warn (and offer to abort) when a PCM-managed SpinRender is already present.
REM PCM extracts into a "com_alsoknownasfoo_spinrender" dir under 3rdparty; a
REM manual install uses "SpinRender". Both loaded at once registers twice.
:warn_if_pcm_installed
set "PCM_FOUND=false"
for %%v in (10.0 9.0 8.0 7.0) do (
    if exist "!DOCS_DIR!\KiCad\%%v\3rdparty\plugins\com_alsoknownasfoo_spinrender" set "PCM_FOUND=true"
)
if "!PCM_FOUND!"=="false" goto :eof

echo.
echo !YELLOW!⚠ PCM_INSTALL_DETECTED:!NC! SpinRender is already installed via KiCad's Plugin and Content Manager:
for %%v in (10.0 9.0 8.0 7.0) do (
    if exist "!DOCS_DIR!\KiCad\%%v\3rdparty\plugins\com_alsoknownasfoo_spinrender" echo     !DIM!!DOCS_DIR!\KiCad\%%v\3rdparty\plugins\com_alsoknownasfoo_spinrender!NC!
)
echo     Running the PCM copy and this manual install at the same time registers the
echo     plugin twice and can shadow its resources.
echo     !DIM!Recommended: uninstall the PCM copy first ^(KiCad -^> Plugin and Content Manager
echo     -^> Installed -^> SpinRender -^> Uninstall^), then re-run this script.!NC!
echo.
if "!AUTO_YES!"=="false" (
    <nul set /p "=    Continue with the manual install anyway? (y/n): "
    choice /c yn /n /m ""
    if errorlevel 2 (
        echo     !YELLOW![!EXCL!!EXCL!] Aborted.!NC! Uninstall the PCM copy, then re-run.
        exit /b 0
    )
)
goto :eof

REM ----------------------------------------------------------------------
REM Check for ffmpeg and offer to install it via winget if missing.
REM The KiCad-bundled Python cannot reliably drive winget itself, so this
REM is handled here in the installer instead.
:check_ffmpeg
set "FFMPEG_FOUND=false"
where ffmpeg >nul 2>&1
if not errorlevel 1 set "FFMPEG_FOUND=true"

if "!FFMPEG_FOUND!"=="false" (
    for %%p in (
        "%LOCALAPPDATA%\Microsoft\WinGet\Links\ffmpeg.exe"
        "%PROGRAMFILES%\Gyan\FFmpeg\bin\ffmpeg.exe"
        "%PROGRAMFILES%\ffmpeg\bin\ffmpeg.exe"
        "C:\ffmpeg\bin\ffmpeg.exe"
    ) do (
        if exist %%p set "FFMPEG_FOUND=true"
    )
)

if "!FFMPEG_FOUND!"=="true" (
    echo !GREEN![OK]!NC! FFMPEG: Found.
    goto :eof
)

echo !YELLOW![!EXCL!!EXCL!] FFMPEG_MISSING:!NC! Required for video rendering, not found.

REM winget may not yet be on PATH for newly-launched shells even when installed
REM (the WindowsApps PATH entry is only picked up after a logon/PATH refresh).
set "WINGET_EXE="
where winget >nul 2>&1
if not errorlevel 1 set "WINGET_EXE=winget"
if "!WINGET_EXE!"=="" if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\winget.exe" set "WINGET_EXE=%LOCALAPPDATA%\Microsoft\WindowsApps\winget.exe"

if "!WINGET_EXE!"=="" (
    echo     !DIM!winget not available. Install ffmpeg manually: https://ffmpeg.org/download.html!NC!
    goto :eof
)

if "!AUTO_YES!"=="false" (
    <nul set /p "=    Install ffmpeg now via winget? (y/n): "
    choice /c yn /n /m ""
    if errorlevel 2 (
        echo     !YELLOW![!EXCL!!EXCL!] SKIPPED:!NC! ffmpeg not installed.
        goto :eof
    )
)

echo !CYAN![i]!NC! INSTALLING FFMPEG VIA WINGET...
"!WINGET_EXE!" install --id Gyan.FFmpeg --silent --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
    echo     !RED![!EXCL!!EXCL!]!NC! ffmpeg installation failed. Install manually: !DIM!https://ffmpeg.org/download.html!NC!
    goto :eof
)
echo     !GREEN!✓!NC! ffmpeg installed. !DIM!Restart KiCad/terminal for PATH changes to take effect.!NC!
goto :eof

REM ----------------------------------------------------------------------
REM Write a build-provenance stamp when installing from a git clone, so the
REM installed copy reports the exact commit it came from (e.g.
REM 0.6.1-beta+6f70af5). Release installs stay clean.
REM   %~1 = deployed plugin directory
:write_build_stamp
set "STAMP_TARGET=%~1"
if exist "!STAMP_TARGET!\_version" del /f /q "!STAMP_TARGET!\_version" >nul 2>&1
if not exist "%SCRIPT_DIR%.git" goto :eof
where git >nul 2>&1
if errorlevel 1 goto :eof

set "PLUGIN_VERSION="
for /f "tokens=2 delims== " %%a in ('findstr /b /c:"__version__" "%SOURCE_DIR%\__init__.py"') do set "PLUGIN_VERSION=%%~a"
set "GIT_SHA="
for /f %%s in ('git -C "%SCRIPT_DIR%." rev-parse --short=7 HEAD 2^>nul') do set "GIT_SHA=%%s"

if not defined PLUGIN_VERSION goto :eof
if not defined GIT_SHA goto :eof
> "!STAMP_TARGET!\_version" echo !PLUGIN_VERSION!+!GIT_SHA!
echo     !DIM![i] Stamped dev build: !PLUGIN_VERSION!+!GIT_SHA!!NC!
goto :eof

REM ----------------------------------------------------------------------
REM Print font removal instructions (Windows).
:font_removal_notice
echo !CYAN![i]!NC! Font removal instructions:
echo     The following fonts may have been installed to your system:
echo     !DIM!- JetBrains Mono
echo     - Oswald
echo     - Material Design Icons!NC!
echo.
echo     To remove: !DIM!Settings -^> Personalization -^> Fonts, right-click -^> Uninstall!NC!
echo.
goto :eof
