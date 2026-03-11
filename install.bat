@echo off
REM SpinRender Installation Script for Windows
REM Installs the plugin to the most recent KiCad scripting/plugins directory found

setlocal EnableDelayedExpansion
chcp 65001 >nul

REM Flag parsing
set AUTO_YES=false
:parse_args
if "%~1"=="" goto end_parse_args
if /i "%~1"=="-y" set AUTO_YES=true
if /i "%~1"=="--yes" set AUTO_YES=true
if /i "%~1"=="-h" goto show_help
if /i "%~1"=="--help" goto show_help
shift
goto parse_args

:show_help
echo SPINRENDER INSTALLER HELP
echo Usage: install.bat [options]
echo Options:
echo   -y, --yes    Automatically overwrite existing installation
echo   -h, --help   Show this help message
exit /b 0

:end_parse_args

echo ┌────────────────────────────────────────────────────────┐
echo │  SPINRENDER // PLUGIN_INSTALL // v0.9.0-ALPHA          │
echo └────────────────────────────────────────────────────────┘
echo.

REM Determine the source directory
set SCRIPT_DIR=%~dp0
set SOURCE_DIR=%SCRIPT_DIR%SpinRender

REM Verify source directory exists
if not exist "%SOURCE_DIR%" (
    echo [!] CRITICAL_ERROR: Source directory not found at:
    echo     %SOURCE_DIR%
    pause
    exit /b 1
)

set TARGET_PATH=

echo [i] SCANNING FOR KICAD ENVIRONMENTS...

REM Search versions in descending order
for %%v in (9.0 8.0 7.0) do (
    if "!TARGET_PATH!"=="" (
        if exist "!APPDATA!\kicad\%%v\scripting\plugins" (
            set "TARGET_PATH=!APPDATA!\kicad\%%v\scripting\plugins"
            echo     [OK] FOUND KICAD %%v @ APPDATA
        )
    )
    
    if "!TARGET_PATH!"=="" (
        if exist "!USERPROFILE!\Documents\KiCad\%%v\scripting\plugins" (
            set "TARGET_PATH=!USERPROFILE!\Documents\KiCad\%%v\scripting\plugins"
            echo     [OK] FOUND KICAD %%v @ DOCUMENTS
        )
    )
    
    if "!TARGET_PATH!"=="" (
        if exist "!USERPROFILE!\Documents\KiCad\%%v\3rdparty\plugins" (
            set "TARGET_PATH=!USERPROFILE!\Documents\KiCad\%%v\3rdparty\plugins"
            echo     [OK] FOUND KICAD %%v @ 3RDPARTY
        )
    )
)

if "!TARGET_PATH!"=="" (
    echo [!] CRITICAL_ERROR: No valid KiCad plugin directories found.
    echo     Run KiCad at least once to initialize system paths.
    pause
    exit /b 1
)

set "TARGET_DIR=!TARGET_PATH!\SpinRender"

if exist "!TARGET_DIR!" (
    if "!AUTO_YES!"=="false" (
        <nul set /p "=    [!] EXISTING_INSTALL_DETECTED: Overwrite? (y/n): "
        choice /c yn /n /m ""
        if errorlevel 2 (
            echo n
            echo [!] ABORTED: Installation cancelled by user.
            exit /b 0
        )
        echo y
    ) else (
        echo     [!] EXISTING_INSTALL_DETECTED: Overwritting.. (-y/--yes flag used)
    )
    rmdir /s /q "!TARGET_DIR!"
)

echo [i] DEPLOYING ASSETS TO: !TARGET_DIR!
mkdir "!TARGET_DIR!"
xcopy "%SOURCE_DIR%" "!TARGET_DIR!\" /E /I /H /Y >nul

if exist "!TARGET_DIR!\__init__.py" (
    echo     ✓ DEPLOYMENT_COMPLETE: SpinRender is active.
    echo.
    echo [i] NEXT STEPS:
    echo     1. Restart KiCad if active
    echo     2. Locate SpinRender in the toolbar
    echo        or: Tools -^> External Plugins -^> SpinRender
    echo.
) else (
    echo [!] DEPLOYMENT_FAILURE: Asset copy verify failed.
    pause
    exit /b 1
)

pause
exit /b 0
