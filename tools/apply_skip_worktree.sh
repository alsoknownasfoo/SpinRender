#!/bin/bash
# Apply --skip-worktree to KiCad config files in all existing git worktrees.
#
# Run this once after cloning or after adding new config files to the protected list.
# New worktrees get this applied automatically via .githooks/post-checkout.
#
# Usage: ./tools/apply_skip_worktree.sh

set -e

KICAD_CONFIGS=(
    "SpinRender/resources/kicad_config/10.0/3d_viewer.json"
)

REPO_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"

echo "Applying --skip-worktree in all worktrees..."

git -C "$REPO_ROOT" worktree list --porcelain \
    | grep '^worktree ' \
    | awk '{print $2}' \
    | while read -r wt_path; do
        for f in "${KICAD_CONFIGS[@]}"; do
            if git -C "$wt_path" ls-files --error-unmatch "$f" &>/dev/null 2>&1; then
                git -C "$wt_path" update-index --skip-worktree "$f"
                echo "  ✓ $wt_path → $f"
            else
                echo "  - $wt_path → $f (not in index, skipped)"
            fi
        done
    done

echo "Done."
