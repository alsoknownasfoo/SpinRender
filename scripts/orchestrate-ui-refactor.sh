#!/bin/bash
# Automated Parallel Agent Orchestration for UI Refactor
# Uses tmux directly (dmux-like) to run 4 Claude agents in parallel with isolated worktrees

SESSION_NAME="spinrender-ui-refactor"
BASE_BRANCH="feat/ui-refactor"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="$REPO_ROOT/.orchestration/$SESSION_NAME"

# Task definitions (in order for panes 1-4)
TASK_UI_ANALYSIS="Analyze all UI-related files in the SpinRender codebase (main_panel.py, custom_controls.py, and any other UI modules). Map dependencies between components, identify coupling issues, and create a prioritized refactoring plan based on complexity and impact. Output findings to docs/UI_ANALYSIS.md."

TASK_THEME_SCHEMA="Design a comprehensive YAML-based theme schema to replace 60+ hardcoded color definitions in custom_controls.py and main_panel.py. Define color palettes, semantic tokens, typography scales, and spacing systems. Create example YAML structure in docs/THEME_SCHEMA.md with all discovered colors organized logically."

TASK_MIGRATION="Create a detailed migration strategy for implementing the theme system. Since this is unreleased, we don't need backward compatibility. Outline the file modification order, dependency graph, and step-by-step implementation phases. Include code examples showing before/after for key components. Document in docs/MIGRATION_STRATEGY.md."

TASK_TDD_PLAN="Plan the test-driven development approach for the UI refactor. Identify what needs testing (component creation, theme application, color resolution, layout). Define test structure, mock requirements, and coverage targets (minimum 80%). Create a test specification in docs/TDD_PLAN.md."

TASK_NAMES=("ui-analysis" "theme-schema" "migration" "tdd-plan")
TASK_PROMPTS=("$TASK_UI_ANALYSIS" "$TASK_THEME_SCHEMA" "$TASK_MIGRATION" "$TASK_TDD_PLAN")

# Find Claude command
CLAUE_CMD="$(command -v claude 2>/dev/null || echo "claude")"
if ! command -v claude &>/dev/null; then
  echo "ERROR: claude command not found in PATH. Install Claude Code CLI first."
  exit 1
fi

echo "=== Parallel Agent Orchestration (tmux) ==="
echo "Session: $SESSION_NAME"
echo "Base branch: $BASE_BRANCH"
echo "Claude command: $CLAUE_CMD"
echo ""

# Clean up previous run
if [ -d "$OUTPUT_DIR" ]; then
  echo "Cleaning up previous run at $OUTPUT_DIR"
  rm -rf "$OUTPUT_DIR"
fi
mkdir -p "$OUTPUT_DIR"

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  echo "Killing existing tmux session: $SESSION_NAME"
  tmux kill-session -t "$SESSION_NAME" || true
fi

# Create worktrees and task files
echo "Creating worktrees and task files..."
for i in "${!TASK_NAMES[@]}"; do
  TASK_NAME="${TASK_NAMES[$i]}"
  WORKTREE_BRANCH="${TASK_NAME}-${BASE_BRANCH}"
  WORKTREE_PATH="${OUTPUT_DIR}/worktree-${TASK_NAME}"

  echo "  - $TASK_NAME"

  # Remove any stale worktree first
  git worktree remove -f "$WORKTREE_PATH" 2>/dev/null || true
  git branch -D "$WORKTREE_BRANCH" 2>/dev/null || true

  # Create worktree from local branch (doesn't need to be pushed)
  if ! git worktree add -B "$WORKTREE_BRANCH" "$WORKTREE_PATH" "$BASE_BRANCH"; then
    echo "ERROR: Failed to create worktree for $TASK_NAME"
    exit 1
  fi

  # Write task prompt to file within worktree (for reference)
  echo "${TASK_PROMPTS[$i]}" > "$WORKTREE_PATH/TASK_PROMPT.md"

  # Create runner script that passes prompt to claude as argument
  cat > "$WORKTREE_PATH/run-agent.sh" << 'RUNNER_EOF'
#!/bin/bash
set -e
cd "$(dirname "$0")"
if [ -f "TASK_PROMPT.md" ]; then
  exec claude "$(cat "TASK_PROMPT.md")"
else
  echo "ERROR: TASK_PROMPT.md not found"
  exit 1
fi
RUNNER_EOF
  chmod +x "$WORKTREE_PATH/run-agent.sh"

  # Create output log file
  : > "$OUTPUT_DIR/status-${TASK_NAME}.md"
done

# Create tmux session
echo ""
echo "Starting tmux session..."
tmux new-session -d -s "$SESSION_NAME" -n "orchestrator"

# Launch agents in parallel panes
PANE_INDEX=0
for i in "${!TASK_NAMES[@]}"; do
  TASK_NAME="${TASK_NAMES[$i]}"
  WORKTREE_PATH="${OUTPUT_DIR}/worktree-${TASK_NAME}"
  STATUS_FILE="${OUTPUT_DIR}/status-${TASK_NAME}.md"

  if [ "$PANE_INDEX" -eq 0 ]; then
    tmux rename-window -t "$SESSION_NAME:0" "agent-$TASK_NAME"
    tmux send-keys -t "$SESSION_NAME:0" "cd '$WORKTREE_PATH' && ./run-agent.sh 2>&1 | tee '$STATUS_FILE'" C-m
  else
    tmux split-window -h -t "$SESSION_NAME:0"
    tmux send-keys -t "$SESSION_NAME:0.$PANE_INDEX" "cd '$WORKTREE_PATH' && ./run-agent.sh 2>&1 | tee '$STATUS_FILE'" C-m
  fi

  ((PANE_INDEX++))
done

# Arrange panes
tmux select-layout -t "$SESSION_NAME:0" tiled

# Summary
echo ""
echo "✓ Orchestration launched!"
echo "  Session name: $SESSION_NAME"
echo "  Attach with: tmux attach -t $SESSION_NAME"
echo ""
echo "Worktrees:"
for TASK_NAME in "${TASK_NAMES[@]}"; do
  echo "  - $OUTPUT_DIR/worktree-$TASK_NAME"
done
echo ""
echo "Status logs:"
for TASK_NAME in "${TASK_NAMES[@]}"; do
  echo "  - $OUTPUT_DIR/status-$TASK_NAME.md"
done
echo ""
echo "When agents finish, merge branches:"
for TASK_NAME in "${TASK_NAMES[@]}"; do
  echo "  git merge ${TASK_NAME}-$BASE_BRANCH"
done
echo ""
echo "Press 'Ctrl-B' then '?' in tmux to see controls (navigate panes with Ctrl-B arrow keys)."
