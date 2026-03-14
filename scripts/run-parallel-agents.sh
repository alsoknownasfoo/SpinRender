#!/bin/bash
# Automated Parallel Agent Orchestration for UI Refactor
# Creates git worktrees and launches agents in tmux panes

set -e

SESSION_NAME="spinrender-ui-refactor"
BASE_BRANCH="feat/ui-refactor"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

OUTPUT_DIR="$REPO_ROOT/.orchestration/$SESSION_NAME"
mkdir -p "$OUTPUT_DIR"

# Task definitions (order matters for pane assignment)
TASK_NAMES=("ui-analysis" "theme-schema" "migration" "tdd-plan")

TASK_UI_ANALYSIS="Analyze all UI-related files in the SpinRender codebase (main_panel.py, custom_controls.py, and any other UI modules). Map dependencies between components, identify coupling issues, and create a prioritized refactoring plan based on complexity and impact. Output findings to docs/UI_ANALYSIS.md."
TASK_THEME_SCHEMA="Design a comprehensive YAML-based theme schema to replace 60+ hardcoded color definitions in custom_controls.py and main_panel.py. Define color palettes, semantic tokens, typography scales, and spacing systems. Create example YAML structure in docs/THEME_SCHEMA.md with all discovered colors organized logically."
TASK_MIGRATION="Create a detailed migration strategy for implementing the theme system. Since this is unreleased, we don't need backward compatibility. Outline the file modification order, dependency graph, and step-by-step implementation phases. Include code examples showing before/after for key components. Document in docs/MIGRATION_STRATEGY.md."
TASK_TDD_PLAN="Plan the test-driven development approach for the UI refactor. Identify what needs testing (component creation, theme application, color resolution, layout). Define test structure, mock requirements, and coverage targets (minimum 80%). Create a test specification in docs/TDD_PLAN.md."

echo "=== Parallel Agent Orchestration ==="
echo "Session: $SESSION_NAME"
echo "Base branch: $BASE_BRANCH"
echo "Worktree root: $OUTPUT_DIR"
echo ""

# Kill existing tmux session if any
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  echo "Killing existing tmux session: $SESSION_NAME"
  tmux kill-session -t "$SESSION_NAME"
fi

# Create worktrees and task files
PANE_INDEX=0
for TASK_NAME in "${TASK_NAMES[@]}"; do
  WORKTREE_BRANCH="${TASK_NAME}-${BASE_BRANCH}"
  WORKTREE_PATH="${OUTPUT_DIR}/worktree-${TASK_NAME}"

  echo "Setting up worktree for: $TASK_NAME"

  # Create worktree
  git worktree add -B "$WORKTREE_BRANCH" "$WORKTREE_PATH" "origin/$BASE_BRANCH" 2>/dev/null || \
  git worktree add -B "$WORKTREE_BRANCH" "$WORKTREE_PATH" "$BASE_BRANCH"

  # Create task file
  TASK_FILE="$OUTPUT_DIR/task-${TASK_NAME}.md"
  echo "# Task: $TASK_NAME" > "$TASK_FILE"
  echo "" >> "$TASK_FILE"

  # Add the task description
  case $TASK_NAME in
    "ui-analysis") echo "$TASK_UI_ANALYSIS" >> "$TASK_FILE" ;;
    "theme-schema") echo "$TASK_THEME_SCHEMA" >> "$TASK_FILE" ;;
    "migration") echo "$TASK_MIGRATION" >> "$TASK_FILE" ;;
    "tdd-plan") echo "$TASK_TDD_PLAN" >> "$TASK_FILE" ;;
  esac

  # Create handoff/status files
  HANDOFF_FILE="$OUTPUT_DIR/handoff-${TASK_NAME}.md"
  STATUS_FILE="$OUTPUT_DIR/status-${TASK_NAME}.md"
  touch "$HANDOFF_FILE" "$STATUS_FILE"
done

# Create tmux session with first pane
echo ""
echo "Starting tmux session: $SESSION_NAME"
cd "$REPO_ROOT" || exit 1

tmux new-session -d -s "$SESSION_NAME" -n "orchestrator"

# For each task, create a pane and launch the agent
for TASK_NAME in "${TASK_NAMES[@]}"; do
  WORKTREE_PATH="$OUTPUT_DIR/worktree-${TASK_NAME}"
  TASK_FILE="$OUTPUT_DIR/task-${TASK_NAME}.md"
  HANDOFF_FILE="$OUTPUT_DIR/handoff-${TASK_NAME}.md"
  STATUS_FILE="$OUTPUT_DIR/status-${TASK_NAME}.md"

  if [ "$PANE_INDEX" -eq 0 ]; then
    # First pane - rename and set up
    tmux rename-window -t "$SESSION_NAME:0" "agent-$TASK_NAME"
    tmux send-keys -t "$SESSION_NAME:0" "cd '$WORKTREE_PATH' && claude < '$TASK_FILE' | tee '$STATUS_FILE'" C-m
  else
    # Additional panes
    tmux split-window -h -t "$SESSION_NAME:0"
    tmux send-keys -t "$SESSION_NAME:0.$PANE_INDEX" "cd '$WORKTREE_PATH' && claude < '$TASK_FILE' | tee '$STATUS_FILE'" C-m
  fi

  ((PANE_INDEX++))
done

# Arrange panes in a grid
tmux select-layout -t "$SESSION_NAME:0" tiled

# Wait a moment for agents to start
sleep 2

echo ""
echo "✓ Orchestration launched!"
echo "  Session name: $SESSION_NAME"
echo "  Attach with: tmux attach -t $SESSION_NAME"
echo ""
echo "Worktrees created at:"
for TASK_NAME in "${TASK_NAMES[@]}"; do
  echo "  - $OUTPUT_DIR/worktree-$TASK_NAME"
done
echo ""
echo "Status files:"
for TASK_NAME in "${TASK_NAMES[@]}"; do
  echo "  - $OUTPUT_DIR/status-$TASK_NAME.md"
done
echo ""
echo "When all agents complete, merge the worktrees:"
for TASK_NAME in "${TASK_NAMES[@]}"; do
  echo "  git merge ${TASK_NAME}-$BASE_BRANCH"
done
echo ""
echo "Orchestrator pane (leftmost) can be used to monitor and coordinate."
