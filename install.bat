@echo off
REM SpinRender Installation Script for Windows
REM Installs the plugin to KiCad 9.0 3rdparty plugins directory

setlocal EnableDelayedExpansion

echo ========================================
echo   SpinRender Plugin Installer v0.9.0
echo ========================================
echo.

REM Determine the source directory (where this script is located)
set SCRIPT_DIR=%~dp0
set SOURCE_DIR=%SCRIPT_DIR%SpinRender

REM Target directory
set TARGET_BASE=%USERPROFILE%\Documents\KiCad\9.0\3rdparty\plugins
set TARGET_DIR=%TARGET_BASE%\SpinRender

REM Parse command line arguments
set AUTO_YES=false
:parse_args
if "%~1"=="" goto end_parse_args
if /i "%~1"=="-y" set AUTO_YES=true
shift
goto parse_args
:end_parse_args

REM Verify source directory exists
if not exist "%SOURCE_DIR%" (
    echo [ERROR] SpinRender source directory not found at:
    echo   %SOURCE_DIR%
    pause
    exit /b 1
)

echo Installation Details:
echo   Source: %SOURCE_DIR%
echo   Target: %TARGET_DIR%
echo.

REM Check if target directory already exists
if not exist "%TARGET_DIR%" goto skip_overwrite

echo [WARNING] SpinRender is already installed at:
echo   %TARGET_DIR%
echo.

if "!AUTO_YES!"=="true" goto do_overwrite

:prompt_overwrite
set /p OVERWRITE="Do you want to overwrite the existing installation? (y/n): "
if /i "!OVERWRITE!"=="y" goto do_overwrite
if /i "!OVERWRITE!"=="n" (
    echo Installation cancelled.
    pause
    exit /b 0
)
echo Please answer y or n.
goto prompt_overwrite

:do_overwrite
echo Removing existing installation...
rmdir /s /q "%TARGET_DIR%"

:skip_overwrite
REM Create target directory structure
echo Creating plugin directory...
if not exist "%TARGET_BASE%" mkdir "%TARGET_BASE%"

REM Copy plugin files
echo Copying SpinRender plugin files...
xcopy "%SOURCE_DIR%" "%TARGET_DIR%\" /E /I /H /Y >nul

REM Verify installation
if exist "%TARGET_DIR%\__init__.py" (
    echo.
    echo [SUCCESS] SpinRender plugin installed successfully!
    echo.
    echo Next steps:
    echo   1. Restart KiCad if it's currently running
    echo   2. Open a PCB in the PCB Editor
    echo   3. Look for the SpinRender button in the toolbar
    echo      or go to Tools -^> External Plugins -^> SpinRender
    echo.
    echo Plugin location:
    echo   %TARGET_DIR%
    echo.
    echo Note: On first launch, SpinRender will check for dependencies
    echo       (kicad-cli and ffmpeg) and offer to install them if missing.
    echo.
) else (
    echo [ERROR] Installation failed: Files not copied correctly
    pause
    exit /b 1
)

pause
