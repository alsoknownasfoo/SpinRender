@echo off
REM SpinRender Installation Script for Windows
REM Installs the plugin to the most recent KiCad scripting/plugins directory found

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
:parse_args
if "%~1"=="" goto end_parse_args
if /i "%~1"=="-y" set AUTO_YES=true
if /i "%~1"=="--yes" set AUTO_YES=true
if /i "%~1"=="--reinstall-deps" set REINSTALL_DEPS=true
if /i "%~1"=="--link-theme" set LINK_THEME=true
if /i "%~1"=="-h" goto show_help
if /i "%~1"=="--help" goto show_help
shift
goto parse_args

:show_help
echo SPINRENDER INSTALLER HELP
echo Usage: install.bat [options]
echo Options:
echo   -y, --yes              Automatically overwrite existing installation
echo   --reinstall-deps       Uninstall dependencies and fonts from KiCad Python before install
echo   --link-theme           Create a symbolic link for dark.yaml (facilitates live theme editing^)
echo   -h, --help             Show this help message
exit /b 0

:end_parse_args

echo ┌────────────────────────────────────────────────────────┐
echo │  SPINRENDER // PLUGIN_INSTALL // v0.9.0-ALPHA          │
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
    
    echo [i] Font removal instructions:
    echo     The following fonts may have been installed to your system:
    echo     - JetBrains Mono
    echo     - Oswald
    echo     - Material Design Icons
    echo.
    echo     To remove these fonts:
    echo     Windows: Settings -^> Personalization -^> Fonts, right-click -^> Uninstall
    echo.
    echo [OK] Dependencies and fonts uninstalled.
    echo [i] Proceeding with plugin installation...
    echo.
)

set SCRIPT_DIR=%~dp0
set SOURCE_DIR=%SCRIPT_DIR%SpinRender

if not exist "%SOURCE_DIR%" (
    echo [!] CRITICAL_ERROR: Source directory not found at:
    echo     %SOURCE_DIR%
    exit /b 1
)

set TARGET_PATH=

echo [i] SCANNING FOR KICAD ENVIRONMENTS...

for %%v in (9.0 8.0 7.0) do (
    if "!TARGET_PATH!"=="" (
        if exist "!APPDATA!\kicad\%%v\scripting\plugins" (
            set "TARGET_PATH=!APPDATA!\kicad\%%v\scripting\plugins"
            echo     [OK] FOUND KICAD %%v @ !TARGET_PATH!
        )
    )
    
    if "!TARGET_PATH!"=="" (
        if exist "!USERPROFILE!\Documents\KiCad\%%v\scripting\plugins" (
            set "TARGET_PATH=!USERPROFILE!\Documents\KiCad\%%v\scripting\plugins"
            echo     [OK] FOUND KICAD %%v @ !TARGET_PATH!
        )
    )
    
    if "!TARGET_PATH!"=="" (
        if exist "!USERPROFILE!\Documents\KiCad\%%v\3rdparty\plugins" (
            set "TARGET_PATH=!USERPROFILE!\Documents\KiCad\%%v\3rdparty\plugins"
            echo     [OK] FOUND KICAD %%v @ !TARGET_PATH!
        )
    )
)

if "!TARGET_PATH!"=="" (
    echo [!] CRITICAL_ERROR: No valid KiCad plugin directories found.
    echo     Run KiCad at least once to initialize system paths.
    exit /b 1
)

set "TARGET_DIR=!TARGET_PATH!\SpinRender"

if exist "!TARGET_DIR!" (
    if "!AUTO_YES!"=="false" (
        <nul set /p "=    ⚠ EXISTING_INSTALL_DETECTED: Overwrite? (y/n): "
        choice /c yn /n /m ""
        if errorlevel 2 (
            echo [!] ABORTED: Installation cancelled by user.
            exit /b 0
        )
    ) else (
        echo     ⚠ EXISTING_INSTALL_DETECTED: Overwritting.. (-y/--yes flag used^)
    )
)

echo [i] DEPLOYING ASSETS TO: !TARGET_DIR!
if exist "!TARGET_DIR!" rmdir /s /q "!TARGET_DIR!"
mkdir "!TARGET_DIR!"
xcopy "%SOURCE_DIR%" "!TARGET_DIR!\" /E /I /H /Y >nul

if exist "!TARGET_DIR!\__init__.py" (
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
    
    echo.
    echo [i] NEXT STEPS:
    echo     1. Restart KiCad if active
    echo     2. Locate SpinRender in the toolbar
    echo        or: Tools -^> External Plugins -^> SpinRender
    echo.
) else (
    echo [!] DEPLOYMENT_FAILURE: Asset copy verify failed.
    exit /b 1
)

exit /b 0
