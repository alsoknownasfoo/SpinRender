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
REINSTALL_DEPS=false
LINK_THEME=false
UNINSTALL=false
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -y|--yes) AUTO_YES=true ;;
        --reinstall-deps) REINSTALL_DEPS=true ;;
        --link-theme) LINK_THEME=true ;;
        -u|--uninstall) UNINSTALL=true ;;
        -h|--help)
            echo -e "${CYAN}SPINRENDER INSTALLER HELP${NC}"
            echo -e "${TEAL}Usage:${NC} ${DIM}./install.sh [options]${NC}"
            echo -e "${TEAL}Options:${NC}"
            echo -e "  ${TEAL}-y, --yes${NC}    ${DIM}Automatically overwrite/remove without prompting${NC}"
            echo -e "  ${TEAL}--reinstall-deps${NC} ${DIM}Uninstall dependencies and fonts from KiCad Python before install${NC}"
            echo -e "  ${TEAL}--link-theme${NC} ${DIM}Create a symbolic link for dark.yaml (facilitates live theme editing)${NC}"
            echo -e "  ${TEAL}-u, --uninstall${NC} ${DIM}Completely remove SpinRender from all KiCad environments${NC}"
            echo -e "  ${TEAL}-h, --help${NC}    ${DIM}Show this help message${NC}"
            exit 0
            ;;
    esac
    shift
done

# Search for KiCad versions in descending order
declare -a SEARCH_VERSIONS=("10.0" "9.0" "8.0" "7.0")

# Find KiCad Python interpreter
find_kicad_python() {
    # Try to find KiCad's bundled Python
    local possible_pythons=()

    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - KiCad app bundle Python
        for version in "${SEARCH_VERSIONS[@]}"; do
            local kicad_app="/Applications/KiCad/KiCad$version.app"
            if [ -d "$kicad_app" ]; then
                possible_pythons+=("$kicad_app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3")
                possible_pythons+=("$kicad_app/Contents/MacOS/python3")
            fi
        done
        # Also check common install locations
        possible_pythons+=("/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3")
        possible_pythons+=("/Applications/KiCad/KiCad.app/Contents/MacOS/python3")
    else
        # Linux - typically system Python or venv in /usr/share/kicad
        for version in "${SEARCH_VERSIONS[@]}"; do
            possible_pythons+=("/usr/share/kicad/$version/bin/kicad")
            possible_pythons+=("/usr/lib/kicad/$version/python")
        done
    fi

    for py in "${possible_pythons[@]}"; do
        if [ -x "$py" ]; then
            echo "$py"
            return 0
        fi
    done

    return 1
}

# Scan all KiCad environments and populate the global FOUND_PATHS array.
# Exits with an error if no plugin directories are found.
declare -a FOUND_PATHS=()
scan_kicad_paths() {
    FOUND_PATHS=()

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
                FOUND_PATHS+=("$path")
                echo -e "    ${GREEN}✓ FOUND KICAD $version${NC} ${DIM}@ $path${NC}"
                break  # take first match per version
            fi
        done
    done

    if [ ${#FOUND_PATHS[@]} -eq 0 ]; then
        echo -e "${RED}[!] CRITICAL_ERROR: No valid KiCad plugin directories found.${NC}"
        echo -e "    ${DIM}Run KiCad at least once to initialize system paths.${NC}"
        exit 1
    fi
}

# Identifier-named directory KiCad's PCM uses for SpinRender. A manual install
# (this script) deploys a "SpinRender" dir instead; having BOTH present makes
# KiCad register the plugin twice and can shadow its bundled resources.
PCM_PLUGIN_DIRNAME="com_alsoknownasfoo_spinrender"

# Return the PCM 3rdparty/plugins base for a given KiCad version.
pcm_base_for_version() {
    local version="$1"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "$HOME/Documents/KiCad/$version/3rdparty/plugins"
    else
        echo "$HOME/.local/share/kicad/$version/3rdparty/plugins"
    fi
}

# Warn (and offer to abort) when a PCM-managed SpinRender is already installed.
warn_if_pcm_installed() {
    local found_pcm=()
    for version in "${SEARCH_VERSIONS[@]}"; do
        local pcm_dir
        pcm_dir="$(pcm_base_for_version "$version")/$PCM_PLUGIN_DIRNAME"
        [ -d "$pcm_dir" ] && found_pcm+=("$pcm_dir")
    done

    [ ${#found_pcm[@]} -eq 0 ] && return 0

    echo
    echo -e "${YELLOW}⚠ PCM_INSTALL_DETECTED: SpinRender is already installed via KiCad's Plugin & Content Manager:${NC}"
    for p in "${found_pcm[@]}"; do
        echo -e "    ${DIM}$p${NC}"
    done
    echo -e "    ${YELLOW}Running the PCM copy and this manual install at the same time registers the${NC}"
    echo -e "    ${YELLOW}plugin twice and can shadow its resources.${NC}"
    echo -e "    ${CYAN}Recommended: uninstall the PCM copy first (KiCad → Plugin and Content Manager${NC}"
    echo -e "    ${CYAN}→ Installed → SpinRender → Uninstall), then re-run this script.${NC}"
    echo

    if [ "$AUTO_YES" = false ]; then
        echo -ne "    ${YELLOW}Continue with the manual install anyway? (y/n): ${NC}"
        while true; do
            read -s -n 1 response
            case $response in
                [Yy]) echo "y"; break ;;
                [Nn]) echo "n"; echo -e "    ${DIM}Aborted. Uninstall the PCM copy, then re-run.${NC}"; exit 0 ;;
            esac
        done
    fi
}

# Write a build-provenance stamp into a freshly deployed plugin directory.
# Only stamps when this script runs from a git clone, so the installed copy can
# report the exact commit it came from (e.g. 0.6.1-beta+6f70af5). Extracted
# release installs stay clean, which is how the updater tells the two apart.
write_build_stamp() {
    local target_dir="$1"
    local stamp_file="$target_dir/_version"
    rm -f "$stamp_file"

    [ -d "$SCRIPT_DIR/.git" ] || return 0  # extracted release -> no stamp

    local plugin_version sha
    plugin_version=$(grep -E '^__version__' "$SOURCE_DIR/__init__.py" 2>/dev/null \
        | head -1 | sed -E 's/.*"([^"]+)".*/\1/')
    sha=$(git -C "$SCRIPT_DIR" rev-parse --short=7 HEAD 2>/dev/null)

    if [ -n "$plugin_version" ] && [ -n "$sha" ]; then
        echo "${plugin_version}+${sha}" > "$stamp_file"
        echo -e "    ${DIM}[i] Stamped dev build: ${plugin_version}+${sha}${NC}"
    fi
}

# Uninstall Python dependencies and surface font removal instructions.
remove_deps_and_fonts() {
    # Find KiCad Python
    local KICAD_PYTHON
    KICAD_PYTHON=$(find_kicad_python) || true
    if [ -n "$KICAD_PYTHON" ]; then
        echo -e "${CYAN}[i] Using KiCad Python:${NC} ${TEAL}$KICAD_PYTHON${NC}"
        echo -e "\n${CYAN}[i] Uninstalling Python dependencies...${NC}"
        "$KICAD_PYTHON" -m pip uninstall -y PyYAML PyOpenGL PyOpenGL-accelerate trimesh numpy 2>/dev/null || true
    else
        echo -e "${YELLOW}[!] Could not find KiCad Python interpreter; skipping dependency removal.${NC}"
    fi

    echo -e "\n${CYAN}[i] Font removal instructions:${NC}"
    echo -e "    ${DIM}The following fonts may have been installed to your system:${NC}"
    echo -e "    ${DIM}- JetBrains Mono${NC}"
    echo -e "    ${DIM}- Oswald${NC}"
    echo -e "    ${DIM}- Material Design Icons${NC}"
    echo
    echo -e "    ${YELLOW}To remove these fonts:${NC}"
    echo -e "    ${DIM}macOS:${NC} Open Font Book, find the fonts, right-click → 'Remove from System'"
    echo -e "    ${DIM}Linux:${NC} Remove from ~/.local/share/fonts/ or /usr/share/fonts/"
    echo -e "    ${DIM}Windows:${NC} Settings → Personalization → Fonts, right-click → Uninstall"
    echo
}

# Header with precise 56-character content width
echo -e "${CYAN}┌────────────────────────────────────────────────────────┐${NC}"
echo -e "${CYAN}│${BOLD}  SPINRENDER // PLUGIN_INSTALL // v0.6.2-beta            ${NC}${CYAN}│${NC}"
echo -e "${CYAN}└────────────────────────────────────────────────────────┘${NC}"
echo

# ---------------------------------------------------------------------------
# UNINSTALL MODE: completely remove the plugin from every KiCad environment.
# ---------------------------------------------------------------------------
if [ "$UNINSTALL" = true ]; then
    echo -e "${CYAN}[i] UNINSTALL MODE${NC}"
    echo -e "${YELLOW}This will remove SpinRender from all detected KiCad environments.${NC}"
    echo -e "${DIM}Python dependencies and fonts are left untouched (they may be in use elsewhere).${NC}"

    if [ "$AUTO_YES" = false ]; then
        echo -ne "    ${YELLOW}Continue? (y/n): ${NC}"
        read -s -n 1 response
        echo
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo -e "${RED}[!] ABORTED.${NC}"
            exit 0
        fi
    fi
    echo

    scan_kicad_paths

    # Remove the deployed plugin from a single KiCad plugins directory.
    # Returns 0 on success/skip, 1 on removal failure.
    uninstall_from_path() {
        local TARGET_PATH="$1"
        local TARGET_DIR="$TARGET_PATH/SpinRender"

        echo
        echo -e "${CYAN}[i] TARGET:${NC} ${TEAL}$TARGET_DIR${NC}"

        if [ ! -d "$TARGET_DIR" ]; then
            echo -e "    ${DIM}No SpinRender installation here. Skipping.${NC}"
            return 0
        fi

        if [ "$AUTO_YES" = false ]; then
            echo -ne "    ${YELLOW}⚠ Remove this installation? (y/n): ${NC}"
            while true; do
                read -s -n 1 response
                case $response in
                    [Yy]) echo "y"; break ;;
                    [Nn])
                        echo "n"
                        echo -e "    ${YELLOW}[!] SKIPPED: Installation left untouched.${NC}"
                        return 0
                        ;;
                esac
            done
        fi

        # Restore write permissions before removal: a prior install may have left
        # read-only dirs/files (e.g. resources/kicad_config/*), and rm can't delete
        # entries inside a directory that lacks write permission.
        chmod -R u+w "$TARGET_DIR" 2>/dev/null || true
        rm -rf "$TARGET_DIR"

        if [ -d "$TARGET_DIR" ]; then
            echo -e "    ${RED}[!] REMOVAL_FAILURE: Could not delete $TARGET_DIR${NC}"
            return 1
        fi

        echo -e "    ${GREEN}✓ REMOVED: SpinRender deleted.${NC}"
        return 0
    }

    echo
    echo -e "${CYAN}[i] REMOVING FROM ALL ${#FOUND_PATHS[@]} KICAD ENVIRONMENT(S) FOUND.${NC}"

    UNINSTALL_FAILED=false
    for path in "${FOUND_PATHS[@]}"; do
        uninstall_from_path "$path" || UNINSTALL_FAILED=true
    done

    echo
    if [ "$UNINSTALL_FAILED" = true ]; then
        echo -e "${RED}[!] One or more removals failed. Review output above.${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ UNINSTALL_COMPLETE: SpinRender has been removed.${NC}"
    exit 0
fi

# Handle reinstall-deps flag
if [ "$REINSTALL_DEPS" = true ]; then
    echo -e "${CYAN}[i] REINSTALL-DEPS MODE${NC}"
    echo -e "${YELLOW}This will uninstall SpinRender dependencies and remove fonts from KiCad Python environment.${NC}"

    if [ "$AUTO_YES" = false ]; then
        echo -ne "    ${YELLOW}Continue? (y/n): ${NC}"
        read -s -n 1 response
        echo
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo -e "${RED}[!] ABORTED.${NC}"
            exit 0
        fi
    fi

    remove_deps_and_fonts

    echo -e "${GREEN}✓ Dependencies and fonts uninstalled.${NC}"
    echo -e "${CYAN}[i] Proceeding with plugin installation...${NC}"
    echo
fi

# Determine the source directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SOURCE_DIR="$SCRIPT_DIR/SpinRender"

# Verify source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo -e "${RED}[!] CRITICAL_ERROR: Source directory not found at:${NC}"
    echo -e "    ${DIM}$SOURCE_DIR${NC}"
    exit 1
fi

scan_kicad_paths

warn_if_pcm_installed

echo
echo -e "${CYAN}[i] INSTALLING TO ALL ${#FOUND_PATHS[@]} KICAD ENVIRONMENT(S) FOUND.${NC}"

# Deploy the plugin to a single KiCad plugins directory.
# Returns 0 on success/skip, 1 on deployment failure.
deploy_to_path() {
    local TARGET_PATH="$1"
    local TARGET_DIR="$TARGET_PATH/SpinRender"

    echo
    echo -e "${CYAN}[i] TARGET:${NC} ${TEAL}$TARGET_DIR${NC}"

    if [ -d "$TARGET_DIR" ]; then
        if [ "$AUTO_YES" = false ]; then
            echo -ne "    ${YELLOW}⚠ EXISTING_INSTALL_DETECTED: Overwrite? (y/n): ${NC}"
            while true; do
                read -s -n 1 response
                case $response in
                    [Yy]) echo "y"; break ;;
                    [Nn])
                        echo "n"
                        echo -e "    ${YELLOW}[!] SKIPPED: Installation left untouched.${NC}"
                        return 0
                        ;;
                esac
            done
        else
            echo -e "    ${YELLOW}⚠ EXISTING_INSTALL_DETECTED: Overwritting.. (-y/--yes flag used)${NC}"
        fi
    fi

    echo -e "${CYAN}[i] DEPLOYING ASSETS TO:${NC} ${TEAL}$TARGET_DIR${NC}"
    # Restore write permissions before removal: a prior install may have left
    # read-only dirs/files (e.g. resources/kicad_config/*), and rm can't delete
    # entries inside a directory that lacks write permission.
    if [ -d "$TARGET_DIR" ]; then
        chmod -R u+w "$TARGET_DIR" 2>/dev/null || true
    fi
    rm -rf "$TARGET_DIR"
    mkdir -p "$TARGET_DIR"
    # Clean Python bytecode from source to avoid stale .pyc files
    find "$SOURCE_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    cp -R "$SOURCE_DIR/." "$TARGET_DIR/"

    if [ ! -f "$TARGET_DIR/__init__.py" ]; then
        echo -e "    ${RED}[!] DEPLOYMENT_FAILURE: Asset copy verify failed.${NC}"
        return 1
    fi

    write_build_stamp "$TARGET_DIR"

    echo -e "    ${GREEN}✓ DEPLOYMENT_COMPLETE: SpinRender is active.${NC}"

    # Handle theme linking if requested
    if [ "$LINK_THEME" = true ]; then
        local THEME_FILE="resources/themes/dark.yaml"
        local TARGET_THEME="$TARGET_DIR/$THEME_FILE"
        local SOURCE_THEME="$SOURCE_DIR/$THEME_FILE"

        if [ -f "$SOURCE_THEME" ]; then
            echo -e "    ${CYAN}[i] LINKING THEME: $THEME_FILE${NC}"
            rm -f "$TARGET_THEME"
            ln -s "$SOURCE_THEME" "$TARGET_THEME"
            echo -e "    ${GREEN}✓ Theme symlinked for live editing.${NC}"
        else
            echo -e "    ${YELLOW}⚠ LINK_THEME_WARNING: Source theme not found at $SOURCE_THEME${NC}"
        fi
    fi

    return 0
}

DEPLOY_FAILED=false
for path in "${FOUND_PATHS[@]}"; do
    deploy_to_path "$path" || DEPLOY_FAILED=true
done

echo
echo -e "${CYAN}[i] NEXT STEPS:${NC}"
echo -e "    ${DIM}1. Restart KiCad if active${NC}"
echo -e "    ${DIM}2. Locate${NC} ${TEAL}SpinRender${NC} ${DIM}in the toolbar${NC}"
echo -e "       ${DIM}or: Tools → External Plugins → SpinRender${NC}"
echo

if [ "$DEPLOY_FAILED" = true ]; then
    echo -e "${RED}[!] One or more deployments failed. Review output above.${NC}"
    exit 1
fi
