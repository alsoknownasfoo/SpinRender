#!/bin/bash

# SpinRender Installation Script
# Installs the plugin to KiCad 9.0 3rdparty plugins directory

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   SpinRender Plugin Installer v0.9.0  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo

# Determine the source directory (where this script is located)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SOURCE_DIR="$SCRIPT_DIR/SpinRender"

# Target directory
TARGET_BASE="$HOME/Documents/KiCad/9.0/3rdparty/plugins"
TARGET_DIR="$TARGET_BASE/SpinRender"

# Parse command line arguments
AUTO_YES=false
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -y) AUTO_YES=true ;;
    esac
    shift
done

# Verify source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo -e "${RED}✗ Error: SpinRender source directory not found at:${NC}"
    echo -e "  $SOURCE_DIR"
    exit 1
fi

echo -e "${BLUE}Installation Details:${NC}"
echo -e "  Source: ${YELLOW}$SOURCE_DIR${NC}"
echo -e "  Target: ${YELLOW}$TARGET_DIR${NC}"
echo

# Check if target directory already exists
if [ -d "$TARGET_DIR" ]; then
    echo -e "${YELLOW}⚠ Warning: SpinRender is already installed at:${NC}"
    echo -e "  $TARGET_DIR"
    echo

    if [ "$AUTO_YES" = false ]; then
        while true; do
            read -p "Do you want to overwrite the existing installation? (y/n): " -n 1 -r
            echo
            case $REPLY in
                [Yy]* ) break;;
                [Nn]* ) echo -e "${BLUE}Installation cancelled.${NC}"; exit 0;;
                * ) echo "Please answer y or n.";;
            esac
        done
    fi

    echo -e "${YELLOW}→ Removing existing installation...${NC}"
    rm -rf "$TARGET_DIR"
fi

# Create target directory structure
echo -e "${BLUE}→ Creating plugin directory...${NC}"
mkdir -p "$TARGET_BASE"

# Copy plugin files
echo -e "${BLUE}→ Copying SpinRender plugin files...${NC}"
cp -r "$SOURCE_DIR" "$TARGET_DIR"

# Verify installation
if [ -f "$TARGET_DIR/__init__.py" ]; then
    echo
    echo -e "${GREEN}✓ SpinRender plugin installed successfully!${NC}"
    echo
    echo -e "${BLUE}Next steps:${NC}"
    echo -e "  1. Restart KiCad if it's currently running"
    echo -e "  2. Open a PCB in the PCB Editor"
    echo -e "  3. Look for the SpinRender button in the toolbar"
    echo -e "     or go to ${YELLOW}Tools → External Plugins → SpinRender${NC}"
    echo
    echo -e "${BLUE}Plugin location:${NC}"
    echo -e "  $TARGET_DIR"
    echo
    echo -e "${YELLOW}Note:${NC} On first launch, SpinRender will check for dependencies"
    echo -e "      (kicad-cli and ffmpeg) and offer to install them if missing."
    echo
else
    echo -e "${RED}✗ Installation failed: Files not copied correctly${NC}"
    exit 1
fi
