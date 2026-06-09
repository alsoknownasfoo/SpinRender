@echo off
REM SpinRender Installation Script for Windows
REM Installs the plugin to every KiCad scripting/plugins directory found

setlocal EnableDelayedExpansion
chcp 65001 >nul

REM Color codes for output
set "CYAN=[36m"
set "TEAL=[38;5;38m"
set "GREEN=[32m"
set "YELLOW=[33m"
set "RED=[31m"
set "BOLD=[1m"
set "DIM=[2m"
set "NC=[0m"

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
echo SPINRENDER INSTALLER HELP
echo Usage: install.bat [options]
echo Options:
echo   -y, --yes              Automatically overwrite/remove without prompting
echo   --reinstall-deps       Uninstall dependencies and fonts from KiCad Python before install
echo   --link-theme           Create a symbolic link for dark.yaml (facilitates live theme editing^)
echo   -u, --uninstall        Completely remove SpinRender from all KiCad environments
echo   -h, --help             Show this help message
exit /b 0

:end_parse_args

echo ┌────────────────────────────────────────────────────────┐
echo │  SPINRENDER // PLUGIN_INSTALL // v0.6.1-beta            │
echo └────────────────────────────────────────────────────────┘
echo.

if "!REINSTALL_DEPS!"=="true" (
    echo [i] REINSTALL-DEPS MODE
    echo This will uninstall SpinRender dependencies and remove fonts from KiCad Python environment.

    if "!AUTO_YES!"=="false" (
        <nul set /p "=    Continue? (y/n): "
        choice /c yn /n /m ""
        if errorlevel 2 (
            echo [!] ABORTED.
            exit /b 0
        )
    )

    call :font_removal_notice
    echo [OK] Dependencies and fonts uninstalled.
    echo [i] Proceeding with plugin installation...
    echo.
)

set SCRIPT_DIR=%~dp0
set SOURCE_DIR=%SCRIPT_DIR%SpinRender

REM Source dir is only required when installing, not when uninstalling.
if "!UNINSTALL!"=="false" (
    if not exist "%SOURCE_DIR%" (
        echo [!] CRITICAL_ERROR: Source directory not found at:
        echo     %SOURCE_DIR%
        exit /b 1
    )
)

set FOUND_COUNT=0

echo [i] SCANNING FOR KICAD ENVIRONMENTS...

for %%v in (10.0 9.0 8.0 7.0) do (
    set "FOUND_THIS_VER=false"
    if "!FOUND_THIS_VER!"=="false" (
        if exist "!APPDATA!\kicad\%%v\scripting\plugins" (
            set "FOUND_THIS_VER=true"
            set /a FOUND_COUNT+=1
            set "FOUND_PATH_!FOUND_COUNT!=!APPDATA!\kicad\%%v\scripting\plugins"
            echo     [OK] FOUND KICAD %%v @ !APPDATA!\kicad\%%v\scripting\plugins
        )
    )
    if "!FOUND_THIS_VER!"=="false" (
        if exist "!USERPROFILE!\Documents\KiCad\%%v\scripting\plugins" (
            set "FOUND_THIS_VER=true"
            set /a FOUND_COUNT+=1
            set "FOUND_PATH_!FOUND_COUNT!=!USERPROFILE!\Documents\KiCad\%%v\scripting\plugins"
            echo     [OK] FOUND KICAD %%v @ !USERPROFILE!\Documents\KiCad\%%v\scripting\plugins
        )
    )
    if "!FOUND_THIS_VER!"=="false" (
        if exist "!USERPROFILE!\Documents\KiCad\%%v\3rdparty\plugins" (
            set "FOUND_THIS_VER=true"
            set /a FOUND_COUNT+=1
            set "FOUND_PATH_!FOUND_COUNT!=!USERPROFILE!\Documents\KiCad\%%v\3rdparty\plugins"
            echo     [OK] FOUND KICAD %%v @ !USERPROFILE!\Documents\KiCad\%%v\3rdparty\plugins
        )
    )
)

if !FOUND_COUNT! EQU 0 (
    echo [!] CRITICAL_ERROR: No valid KiCad plugin directories found.
    echo     Run KiCad at least once to initialize system paths.
    exit /b 1
)

REM ----------------------------------------------------------------------
REM UNINSTALL MODE: completely remove the plugin from every environment.
REM ----------------------------------------------------------------------
if "!UNINSTALL!"=="true" (
    echo.
    echo [i] UNINSTALL MODE
    echo This will remove SpinRender from all detected KiCad environments.
    echo Python dependencies and fonts are left untouched (they may be in use elsewhere^).

    if "!AUTO_YES!"=="false" (
        <nul set /p "=    Continue? (y/n): "
        choice /c yn /n /m ""
        if errorlevel 2 (
            echo [!] ABORTED.
            exit /b 0
        )
    )

    echo.
    echo [i] REMOVING FROM ALL !FOUND_COUNT! KICAD ENVIRONMENT(S^) FOUND.

    set "UNINSTALL_FAILED=false"
    for /l %%i in (1,1,!FOUND_COUNT!) do (
        call :uninstall_from_path "!FOUND_PATH_%%i!"
    )

    echo.
    if "!UNINSTALL_FAILED!"=="true" (
        echo [!] One or more removals failed. Review output above.
        exit /b 1
    )

    echo [OK] UNINSTALL_COMPLETE: SpinRender has been removed.
    exit /b 0
)

call :warn_if_pcm_installed

echo.
echo [i] INSTALLING TO ALL !FOUND_COUNT! KICAD ENVIRONMENT(S^) FOUND.

set "DEPLOY_FAILED=false"
for /l %%i in (1,1,!FOUND_COUNT!) do (
    call :deploy_to_path "!FOUND_PATH_%%i!"
)

echo.
echo [i] NEXT STEPS:
echo     1. Restart KiCad if active
echo     2. Locate SpinRender in the toolbar
echo        or: Tools -^> External Plugins -^> SpinRender
echo.

if "!DEPLOY_FAILED!"=="true" (
    echo [!] One or more deployments failed. Review output above.
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
echo [i] TARGET: !TARGET_DIR!

if exist "!TARGET_DIR!" (
    if "!AUTO_YES!"=="false" (
        <nul set /p "=    ⚠ EXISTING_INSTALL_DETECTED: Overwrite? (y/n): "
        choice /c yn /n /m ""
        if errorlevel 2 (
            echo     [!] SKIPPED: Installation left untouched.
            goto :eof
        )
    ) else (
        echo     ⚠ EXISTING_INSTALL_DETECTED: Overwritting.. (-y/--yes flag used^)
    )
)

echo [i] DEPLOYING ASSETS TO: !TARGET_DIR!
REM Clear read-only/hidden attributes before removal: a prior install may have
REM left read-only files (e.g. resources\kicad_config\*) that block rmdir.
if exist "!TARGET_DIR!" attrib -r -h "!TARGET_DIR!\*" /s /d >nul 2>&1
if exist "!TARGET_DIR!" rmdir /s /q "!TARGET_DIR!"
mkdir "!TARGET_DIR!"
xcopy "%SOURCE_DIR%" "!TARGET_DIR!\" /E /I /H /Y >nul

if not exist "!TARGET_DIR!\__init__.py" (
    echo     [!] DEPLOYMENT_FAILURE: Asset copy verify failed.
    set "DEPLOY_FAILED=true"
    goto :eof
)

call :write_build_stamp "!TARGET_DIR!"

echo     ✓ DEPLOYMENT_COMPLETE: SpinRender is active.

if "!LINK_THEME!"=="true" (
    set "THEME_FILE=resources\themes\dark.yaml"
    set "TARGET_THEME=!TARGET_DIR!\!THEME_FILE!"
    set "SOURCE_THEME=%SOURCE_DIR%\!THEME_FILE!"

    if exist "!SOURCE_THEME!" (
        echo     [i] LINKING THEME: !THEME_FILE!
        if exist "!TARGET_THEME!" del "!TARGET_THEME!"
        mklink "!TARGET_THEME!" "!SOURCE_THEME!" >nul
        echo     ✓ Theme symlinked for live editing.
    ) else (
        echo     ⚠ LINK_THEME_WARNING: Source theme not found at !SOURCE_THEME!
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
echo [i] TARGET: !TARGET_DIR!

if not exist "!TARGET_DIR!" (
    echo     No SpinRender installation here. Skipping.
    goto :eof
)

if "!AUTO_YES!"=="false" (
    <nul set /p "=    ⚠ Remove this installation? (y/n): "
    choice /c yn /n /m ""
    if errorlevel 2 (
        echo     [!] SKIPPED: Installation left untouched.
        goto :eof
    )
)

REM Clear read-only/hidden attributes before removal: a prior install may have
REM left read-only files (e.g. resources\kicad_config\*) that block rmdir.
attrib -r -h "!TARGET_DIR!\*" /s /d >nul 2>&1
rmdir /s /q "!TARGET_DIR!"

if exist "!TARGET_DIR!" (
    echo     [!] REMOVAL_FAILURE: Could not delete !TARGET_DIR!
    set "UNINSTALL_FAILED=true"
    goto :eof
)

echo     ✓ REMOVED: SpinRender deleted.
goto :eof

REM ----------------------------------------------------------------------
REM Warn (and offer to abort) when a PCM-managed SpinRender is already present.
REM PCM extracts into a "com_alsoknownasfoo_spinrender" dir under 3rdparty; a
REM manual install uses "SpinRender". Both loaded at once registers twice.
:warn_if_pcm_installed
set "PCM_FOUND=false"
for %%v in (10.0 9.0 8.0 7.0) do (
    if exist "!USERPROFILE!\Documents\KiCad\%%v\3rdparty\plugins\com_alsoknownasfoo_spinrender" set "PCM_FOUND=true"
)
if "!PCM_FOUND!"=="false" goto :eof

echo.
echo ⚠ PCM_INSTALL_DETECTED: SpinRender is already installed via KiCad's Plugin and Content Manager:
for %%v in (10.0 9.0 8.0 7.0) do (
    if exist "!USERPROFILE!\Documents\KiCad\%%v\3rdparty\plugins\com_alsoknownasfoo_spinrender" echo     !USERPROFILE!\Documents\KiCad\%%v\3rdparty\plugins\com_alsoknownasfoo_spinrender
)
echo     Running the PCM copy and this manual install at the same time registers the
echo     plugin twice and can shadow its resources.
echo     Recommended: uninstall the PCM copy first ^(KiCad -^> Plugin and Content Manager
echo     -^> Installed -^> SpinRender -^> Uninstall^), then re-run this script.
echo.
if "!AUTO_YES!"=="false" (
    <nul set /p "=    Continue with the manual install anyway? (y/n): "
    choice /c yn /n /m ""
    if errorlevel 2 (
        echo     [!] Aborted. Uninstall the PCM copy, then re-run.
        exit /b 0
    )
)
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
echo     [i] Stamped dev build: !PLUGIN_VERSION!+!GIT_SHA!
goto :eof

REM ----------------------------------------------------------------------
REM Print font removal instructions (Windows).
:font_removal_notice
echo [i] Font removal instructions:
echo     The following fonts may have been installed to your system:
echo     - JetBrains Mono
echo     - Oswald
echo     - Material Design Icons
echo.
echo     To remove these fonts:
echo     Windows: Settings -^> Personalization -^> Fonts, right-click -^> Uninstall
echo.
goto :eof
