#!/bin/bash

# SpinRender Installation Script
# Installs the plugin to the most recent KiCad scripting/plugins directory found

set -e  # Exit on error

# Colors for output
CYAN='\033[0;36m'
TEAL='\033[38;5;38m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m' # No Color

# Flag parsing
AUTO_YES=false
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -y|--yes) AUTO_YES=true ;;
        -h|--help) 
            echo -e "${CYAN}SPINRENDER INSTALLER HELP${NC}"
            echo -e "${TEAL}Usage:${NC} ${DIM}./install.sh [options]${NC}"
            echo -e "${TEAL}Options:${NC}"
            echo -e "  ${TEAL}-y, --yes${NC}    ${DIM}Automatically overwrite existing installation${NC}"
            echo -e "  ${TEAL}-h, --help${NC}    ${DIM}Show this help message${NC}"
            exit 0 
            ;;
    esac
    shift
done

# Header with precise 56-character content width
echo -e "${CYAN}┌────────────────────────────────────────────────────────┐${NC}"
echo -e "${CYAN}│${BOLD}  SPINRENDER // PLUGIN_INSTALL // v0.9.0-ALPHA          ${NC}${CYAN}│${NC}"
echo -e "${CYAN}└────────────────────────────────────────────────────────┘${NC}"
echo

# Determine the source directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SOURCE_DIR="$SCRIPT_DIR/SpinRender"

# Verify source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo -e "${RED}[!] CRITICAL_ERROR: Source directory not found at:${NC}"
    echo -e "    ${DIM}$SOURCE_DIR${NC}"
    exit 1
fi

# Search for KiCad versions in descending order
declare -a SEARCH_VERSIONS=("9.0" "8.0" "7.0")
TARGET_PATH=""

echo -e "${CYAN}[i] SCANNING FOR KICAD ENVIRONMENTS...${NC}"

for version in "${SEARCH_VERSIONS[@]}"; do
    # Define possible paths for this version
    declare -a PATHS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        PATHS=("$HOME/Documents/KiCad/$version/scripting/plugins" "$HOME/Library/Preferences/kicad/$version/scripting/plugins" "$HOME/Documents/KiCad/$version/3rdparty/plugins")
    else
        # Linux
        PATHS=("$HOME/.local/share/kicad/$version/scripting/plugins" "$HOME/.kicad/$version/scripting/plugins")
    fi

    for path in "${PATHS[@]}"; do
        if [ -d "$path" ]; then
            TARGET_PATH="$path"
            echo -e "    ${GREEN}✓ FOUND KICAD $version${NC} ${DIM}@ $path${NC}"
            break 2 # Found the best location, stop searching
        fi
    done
done

if [ -n "$TARGET_PATH" ]; then
    TARGET_DIR="$TARGET_PATH/SpinRender"
    
    if [ -d "$TARGET_DIR" ]; then
        if [ "$AUTO_YES" = false ]; then
            echo -ne "    ${YELLOW}⚠ EXISTING_INSTALL_DETECTED: Overwrite? (y/n): ${NC}"
            while true; do
                read -s -n 1 response
                case $response in
                    [Yy]) echo "y"; break ;;
                    [Nn]) 
                        echo "n"
                        echo -e "${RED}[!] ABORTED: Installation cancelled by user.${NC}"
                        exit 0 
                        ;;
                esac
            done
        else
            echo -e "    ${YELLOW}⚠ EXISTING_INSTALL_DETECTED: Overwritting.. (-y/--yes flag used)${NC}"
        fi
        rm -rf "$TARGET_DIR"
    fi

    echo -e "${CYAN}[i] DEPLOYING ASSETS TO:${NC} ${TEAL}$TARGET_DIR${NC}"
    rm -rf "$TARGET_DIR"
    mkdir -p "$TARGET_DIR"
    cp -R "$SOURCE_DIR/." "$TARGET_DIR/"
    
    if [ -f "$TARGET_DIR/__init__.py" ]; then
        echo -e "    ${GREEN}✓ DEPLOYMENT_COMPLETE: SpinRender is active.${NC}"
        echo
        echo -e "${CYAN}[i] NEXT STEPS:${NC}"
        echo -e "    ${DIM}1. Restart KiCad if active${NC}"
        echo -e "    ${DIM}2. Locate${NC} ${TEAL}SpinRender${NC} ${DIM}in the toolbar${NC}"
        echo -e "       ${DIM}or: Tools → External Plugins → SpinRender${NC}"
        echo
    else
        echo -e "${RED}[!] DEPLOYMENT_FAILURE: Asset copy verify failed.${NC}"
        exit 1
    fi
else
    echo -e "${RED}[!] CRITICAL_ERROR: No valid KiCad plugin directories found.${NC}"
    echo -e "    ${DIM}Run KiCad at least once to initialize system paths.${NC}"
    exit 1
fi
