# UI Refactor Project Plan

**Comprehensive task breakdown derived from:**
- `docs/MIGRATION_STRATEGY.md` (Theme System)
- `docs/ARCHITECTURE_IMPLEMENTATION.md` (Non-Theme Architecture)
- `docs/TDD_PLAN.md` (Testing Strategy)

---

## Legend

- **Priority:** P0 (critical), P1 (high), P2 (medium), P3 (low)
- **Effort:** in developer days (d)
- **Dependencies:** tasks that must complete first
- **Parallel:** tasks that can run simultaneously

---

## Phase 0: Foundation (Before Implementation)

### Task 0.1: Set up test infrastructure
- **Priority:** P0
- **Effort:** 0.5d
- **Dependencies:** None
- **Deliverables:**
  - Create `tests/` directory structure
  - Set up `conftest.py` with wx mock fixtures
  - Configure `pytest.ini` / `pyproject.toml` for pytest
  - Install test dependencies (pytest, pytest-cov,.mock)
- **References:** TDD_PLAN.md Section 2

### Task 0.2: Create theme module skeleton
- **Priority:** P0
- **Effort:** 0.5d
- **Dependencies:** None
- **Deliverables:**
  - Create `SpinRender/ui/theme.py` with all color constants from MIGRATION_STRATEGY Phase 1
  - Add `disabled()` helper
  - No imports from other UI files (standalone)
- **References:** MIGRATION_STRATEGY.md Phase 1

---

## Phase 1: Theme System Implementation (P0 — Must complete first)

**Total Effort:** ~8-10 days

### Task 1.1: Define complete theme color palette
- **Priority:** P0
- **Effort:** 1d
- **Dependencies:** 0.2 (theme skeleton)
- **Deliverables:**
  - All 20+ color constants defined in `theme.py`
  - BG_PAGE, BG_PANEL, BG_INPUT, BG_SURFACE, BG_MODAL unified
  - TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED
  - ACCENT_CYAN, ACCENT_YELLOW, ACCENT_GREEN, ACCENT_ORANGE
  - BORDER_DEFAULT, BORDER_MODAL
  - DISABLED_ALPHA constant
- **Verification:** `grep` confirms no wx.Colour calls outside theme.py

### Task 1.2: Add typography constants to theme
- **Priority:** P0
- **Effort:** 0.5d
- **Dependencies:** 1.1
- **Deliverables:**
  - FONT_MONO, FONT_ICONS, FONT_DISPLAY string constants
  - Document font weight schemes
- **References:** MIGRATION_STRATEGY.md Phase 1

### Task 1.3: Update custom_controls.py — font constants
- **Priority:** P0
- **Effort:** 1d
- **Dependencies:** 1.2
- **Deliverables:**
  - Replace `_JETBRAINS_MONO`, `_MDI_FONT_FAMILY`, `_OSWALD` with `theme.FONT_*`
  - Replace `_get_paint_color()` with `theme.disabled()`
- **Files:** `SpinRender/ui/custom_controls.py`
- **References:** MIGRATION_STRATEGY.md Phase 2a

### Task 1.4: Update custom_controls.py — replace inline colors (Part 1)
- **Priority:** P0
- **Effort:** 2d
- **Dependencies:** 1.3
- **Deliverables:** Replace hardcoded wx.Colour calls in 7 controls:
  - CustomSlider (track, handle, text)
  - CustomToggleButton (active/inactive fill, text)
  - CustomDropdown + DropdownPopup (bg, border, text)
  - CustomButton (primary fill, ghost border, danger)
- **Mapping:** See MIGRATION_STRATEGY.md Table in Phase 2c
- **References:** MIGRATION_STRATEGY.md Phase 2b-2c

### Task 1.5: Update custom_controls.py — replace inline colors (Part 2)
- **Priority:** P0
- **Effort:** 2d
- **Dependencies:** 1.4
- **Deliverables:** Replace colors in remaining 6 controls:
  - PresetCard (bg, selected border, text)
  - SectionLabel (text, divider line)
  - NumericDisplay (bg, text)
  - NumericInput (bg, focused border, text)
  - CustomTextInput (bg, placeholder, text)
  - ProjectFolderChip, CustomColorPicker, PathInputControl
- **References:** MIGRATION_STRATEGY.md Phase 2c

### Task 1.6: Update dialogs.py — remove class color attrs
- **Priority:** P0
- **Effort:** 1d
- **Dependencies:** 1.2
- **Deliverables:**
  - Remove BG_MODAL, BORDER_DEFAULT, ACCENT_YELLOW, TEXT_PRIMARY from BaseStyledDialog
  - Replace all `self.BG_MODAL` etc. with `theme.*`
  - Update paint/draw methods in BaseStyledDialog, AdvancedOptionsDialog, SavePresetDialog
- **Files:** `SpinRender/ui/dialogs.py`
- **References:** MIGRATION_STRATEGY.md Phase 3

### Task 1.7: Update main_panel.py — remove class color attrs
- **Priority:** P0
- **Effort:** 1.5d
- **Dependencies:** 1.2
- **Deliverables:**
  - Remove all class-level color constants from SpinRenderPanel
  - Global find/replace: `self.BG_*` → `theme.BG_*`, `self.TEXT_*` → `theme.TEXT_*`, etc.
  - `self.ACCENT_*` → `theme.ACCENT_*`
  - `self.BORDER_*` → `theme.BORDER_*`
- **Files:** `SpinRender/ui/main_panel.py`
- **References:** MIGRATION_STRATEGY.md Phase 4

### Task 1.8: Update ui/__init__.py
- **Priority:** P0
- **Effort:** 0.5d
- **Dependencies:** 1.7
- **Deliverables:**
  - Add `from . import theme` to expose in package namespace
- **Files:** `SpinRender/ui/__init__.py`

### Task 1.9: Theme system verification
- **Priority:** P0
- **Effort:** 0.5d
- **Dependencies:** 1.8
- **Deliverables:**
  - Run `grep -r "wx.Colour(" SpinRender/ui/` — should only hit `theme.py`
  - Ensure no `self.BG_*` etc. remain
  - Plugin loads in KiCad without errors
  - Manual visual check: all controls render correctly
  - Disabled state opacity works via `theme.disabled()`
- **References:** MIGRATION_STRATEGY.md Verification Checklist

---

## Phase 2: Dependency Inversion & State Management (P0 — Blocks other work)

**Total Effort:** ~3-4 days

### Task 2.1: Analyze utils → ui dependency
- **Priority:** P0
- **Effort:** 0.5d
- **Dependencies:** Phase 1 complete
- **Deliverables:**
  - Document all imports from `utils.dependencies` into `ui.*`
  - Identify what `dependencies.py` actually needs from UI
  - Propose break strategy: move UI-agnostic code to utils, or create abstraction layer
- **References:** ARCHITECTURE_IMPLEMENTATION.md Section 5

### Task 2.2: Refactor dependencies module
- **Priority:** P0
- **Effort:** 1.5d
- **Dependencies:** 2.1
- **Deliverables:**
  - Remove any UI imports from `utils/check_dependencies.py`
  - Move pure functions to appropriate utils submodules
  - If UI needs something from dependencies, invert via interfaces/protocols
  - Add tests for moved functions
- **Files:** `SpinRender/utils/check_dependencies.py`, possibly new files in `utils/`
- **Risk:** High — may break existing code, need careful coordination

### Task 2.3: Unify state management
- **Priority:** P0
- **Effort:** 2d
- **Dependencies:** 2.2 (can overlap partially)
- **Deliverables:**
  - Replace `self.settings: dict` with a `@dataclass` `RenderSettings`
  - Define schema with typed fields and defaults
  - Add validation (pydantic or manual __post_init__)
  - Replace all `self.settings["key"]` access with attributes `self.settings.key`
  - Migrate JSON persistence to use new dataclass (de/serialization)
- **Files:** `SpinRender/core/presets.py`, `SpinRender/ui/main_panel.py`, any module accessing settings
- **References:** ARCHITECTURE_IMPLEMENTATION.md Section 7

---

## Phase 3: Typography System (P1 — Can parallel with Phase 4)

**Total Effort:** ~3-4 days

### Task 3.1: Design TextStyle class
- **Priority:** P1
- **Effort:** 1d
- **Dependencies:** Phase 1 complete (theme.py exists)
- **Deliverables:**
  - Create `SpinRender/ui/text_styles.py`
  - Define `@dataclass(frozen=True)` TextStyle with: family, size, weight, color, formatting
  - Add `apply_to(wx.Font)` method or factory
  - Document array-based definitions: `[family, size, weight, color_role]`
  - Support semantic token resolution (e.g., `TextStyle.from_token("HEADER")`)
- **References:** ARCHITECTURE_IMPLEMENTATION.md Section 1

### Task 3.2: Define font scales and semantic tokens
- **Priority:** P1
- **Effort:** 0.5d
- **Dependencies:** 3.1
- **Deliverables:**
  - Create `FONT_SCALES` dict: xs/sm/md/lg/xl mappings
  - Define semantic tokens: `HEADER`, `BODY`, `CAPTION`, `BUTTON`, `INPUT`
  - Map tokens to `TextStyle` instances with theme color references
- **Files:** `SpinRender/ui/text_styles.py`

### Task 3.3: Implement case formatting
- **Priority:** P1
- **Effort:** 0.5d
- **Dependencies:** 3.1
- **Deliverables:**
  - Add `uppercase: bool` field to TextStyle
  - Add `.format_text(text)` method that applies case transformation
  - Auto-uppercase for Oswald headers
- **References:** UI_REFACTOR.md 2.3

### Task 3.4: Update CustomText control
- **Priority:** P1
- **Effort:** 1d
- **Dependencies:** 3.2, 3.3
- **Deliverables:**
  - Modify `CustomText` to accept `style: TextStyle` parameter
  - Replace `type` parameter usage with semantic color from TextStyle
  - Apply formatting via `style.format_text()`
  - Migrate all callers to use TextStyle objects instead of text+size+weight
- **Files:** `SpinRender/ui/custom_controls.py` (CustomText), all call sites

### Task 3.5: Migrate all font creation to TextStyle
- **Priority:** P1
- **Effort:** 1.5d
- **Dependencies:** 3.4
- **Deliverables:**
  - Replace `get_custom_font(size, weight, family)` calls with `TextStyle(...).apply_to()`
  - Update 13 custom controls and dialogs/main_panel
  - Remove `get_custom_font()` function once unused
- **Files:** `SpinRender/ui/custom_controls.py`, `SpinRender/ui/dialogs.py`, `SpinRender/ui/main_panel.py`

### Task 3.6: TextStyle testing
- **Priority:** P1
- **Effort:** 0.5d
- **Dependencies:** 3.5
- **Deliverables:**
  - Unit tests: `tests/unit/test_text_styles.py`
  - Verify token resolution, formatting, font creation
  - Coverage ≥95% (per TDD_PLAN)
- **References:** TDD_PLAN.md Section 2

---

## Phase 4: Component Construction Alignment (P1 — Parallel with Phase 3)

**Total Effort:** ~4-5 days

### Task 4.1: Define unified construction pattern
- **Priority:** P1
- **Effort:** 1d
- **Dependencies:** Phase 1 complete
- **Deliverables:**
  - Document standard sequence: create frame → apply theme → instantiate text → bind events
  - Define canonical function signatures for component factories
  - Create template examples for: simple controls, interactive controls, compound controls
- **Files:** `docs/COMPONENT_PATTERNS.md` (new reference)
- **References:** ARCHITECTURE_IMPLEMENTATION.md Section 2.5

### Task 4.2: Extract shared helper functions
- **Priority:** P1
- **Effort:** 1.5d
- **Dependencies:** 4.1
- **Deliverables:**
  - Create `SpinRender/ui/helpers.py` with:
    - `create_frame(parent, style_token)` — applies bg, returns frame
    - `create_text(parent, label, text_style)` — applies font/color
    - `bind_mouse_events(widget, handlers)` — standard hover/click wiring
    - `apply_disabled_state(widget, is_enabled)` — uses theme.disabled()
  - Refactor 2-3 controls to use helpers as proof of concept
- **Files:** `SpinRender/ui/helpers.py` (new), refactor sample controls

### Task 4.3: Standardize all 13 custom controls
- **Priority:** P1
- **Effort:** 2.5d
- **Dependencies:** 4.2, Task 1.4-1.5 (theme colors already done), 3.5 (font system done)
- **Deliverables:**
  - Refactor each control to follow unified construction pattern
  - Use shared helpers for common setup
  - Ensure consistent event binding (hover state updates, disabled handling)
  - Standardize internal hierarchy (all similar controls have similar child structures)
  - Update all call sites if signatures change
- **Files:** `SpinRender/ui/custom_controls.py` (all 13 classes)

### Task 4.4: Component pattern testing
- **Priority:** P1
- **Effort:** 0.5d
- **Dependencies:** 4.3
- **Deliverables:**
  - Unit tests for shared helpers
  - Integration tests: verify each control constructs without display errors
  - Structural consistency checks (all buttons have expected children)
- **References:** TDD_PLAN.md test structure

---

## Phase 5: Interaction Integrity (P2 — Can run in parallel with Phase 6)

**Total Effort:** ~1 day

### Task 5.1: Identify non-interactive labels
- **Priority:** P2
- **Effort:** 0.5d
- **Dependencies:** Phase 1 complete
- **Deliverables:**
  - Audit all CustomText/Label usage in codebase
  - Identify which are inside clickable containers (e.g., PresetCard)
  - Document instances where non-interactive text blocks clicks
- **References:** ARCHITECTURE_IMPLEMENTATION.md Section 2.4

### Task 5.2: Implement mouse pass-through
- **Priority:** P2
- **Effort:** 0.5d
- **Dependencies:** 5.1
- **Deliverables:**
  - Add `wx.EVT_LEFT_DOWN` handler to non-interactive labels that calls `event.Skip()`
  - Ensure click propagates to parent
  - Verify PresetCard clicks work through label area
  - Add regression test: simulate click on label, assert parent receives event
- **Files:** `SpinRender/ui/custom_controls.py` (CustomText/SectionLabel), tests

---

## Phase 6: Validation Layer (P2 — Parallel with Phase 5)

**Total Effort:** ~2 days

### Task 6.1: Token resolution validation
- **Priority:** P2
- **Effort:** 0.5d
- **Dependencies:** Phase 1 complete (theme tokens exist)
- **Deliverables:**
  - Create `SpinRender/ui/validation.py`
  - Function `validate_all_tokens()` — checks every theme token resolves for dark/light
  - Test: all tokens defined → valid wx.Colour objects
  - Fail fast with clear error: "Unknown token: BUTTON_RENDER_FILL"
- **Files:** ` SpinRender/ui/validation.py` (new)
- **References:** ARCHITECTURE_IMPLEMENTATION.md Section 4

### Task 6.2: Contrast checking implementation
- **Priority:** P2
- **Effort:** 1d
- **Dependencies:** 6.1
- **Deliverables:**
  - Create `ContrastChecker` class with `check_contrast(bg_color, text_color)` method
  - Use WCAG AA standard (4.5:1 for normal text, 3:1 for large text)
  - Integrate with token resolution: if contrast fails, retry with opposite L_/D_ token family
  - Auto-adjustment algorithm (brightness shift, fallback to white/black)
  - Unit tests for contrast calculations
- **Files:** `SpinRender/ui/validation.py` (ContrastChecker)
- **References:** UI_REFACTOR.md 1.3, 2.2

### Task 6.3: Config validation
- **Priority:** P2
- **Effort:** 0.5d
- **Dependencies:** 6.2
- **Deliverables:**
  - If YAML loading exists, add schema validation at startup
  - Check: unknown tokens, malformed arrays, invalid override shapes
  - Clear error messages with line numbers and suggestions
  - Schema version field checking
- **Files:** `SpinRender/ui/theme.py` or `SpinRender/ui/config.py`
- **References:** UI_REFACTOR.md 1.4

---

## Phase 7: God Class Extraction (P2 — Highest risk, do after phases 1-4)

**Total Effort:** ~5-7 days

### Task 7.1: Analyze SpinRenderPanel responsibilities
- **Priority:** P2
- **Effort:** 1d
- **Dependencies:** Phases 1-4 complete (theme, fonts, component patterns done)
- **Deliverables:**
  - Map all 64 methods to responsibility domains:
    - UI construction
    - State management
    - Business logic
    - File I/O
    - Subprocess orchestration
    - Preview management
    - Event handling
  - Identify natural module boundaries
  - Draft new module names and APIs
- **References:** ARCHITECTURE_IMPLEMENTATION.md Section 6
- **Status:** ✅ Complete — See `docs/TASK_7_1_ANALYSIS.md` for full analysis

### Task 7.2: Extract PreviewPanel
- **Priority:** P2
- **Effort:** 2d
- **Dependencies:** 7.1
- **Deliverables:**
  - Create `SpinRender/ui/preview_panel.py`
  - Move preview-related methods: `update_preview_overlay`, `_on_render_preview_paint`, `start_playback`, `stop_playback`, `on_playback_timer`, `on_close_render_preview`, `_update_viewport_rotation`
  - Define `PreviewPanel` class with clean interface (viewport, overlay, playback)
  - Update `SpinRenderPanel.create_preview_panel()` to instantiate `PreviewPanel`
  - Wire event bindings (drag, render mode buttons, close button)
  - Tests: preview lifecycle, playback state, overlay updates
- **Files:** `SpinRender/ui/preview_panel.py` (new), `SpinRender/ui/main_panel.py` (refactor)
- **Risk:** High — preview logic tightly coupled with UI
- **Status:** ✅ Complete

### Task 7.3: Extract RenderController
- **Priority:** P2
- **Effort:** 2d
- **Dependencies:** 7.2
- **Deliverables:**
  - Create `SpinRender/core/render_controller.py`
  - Move render orchestration: `on_render`, `on_render_progress`, `on_render_finished` logic
  - Define `RenderController` class with `start_render()`, `cancel()`, `is_rendering()`
  - Use background thread with wx.CallAfter for UI callbacks
  - Update `SpinRenderPanel.on_render()` to delegate to controller
  - Tests: subprocess mocking, progress tracking, cancellation
- **Files:** `SpinRender/core/render_controller.py` (new), `SpinRender/ui/main_panel.py` (refactor)
- **Status:** ✅ Complete

### Task 7.4: Extract PresetController
- **Priority:** P2
- **Effort:** 1.5d
- **Dependencies:** 7.3
- **Deliverables:**
  - Create `SpinRender/ui/preset_controller.py` (requires UI control refs → stays in ui/)
  - Move preset logic: `on_preset_change`, `apply_preset_data`, `check_preset_match`, `save_settings`, `on_save_preset`
  - Define `PresetController` class with adapter pattern: accepts `controls` dict and `preview` reference
  - Use `PresetManager` for persistence
  - Update `SpinRenderPanel._init_preset_controller()` to instantiate controller
  - Tests: preset matching, custom preset dialogs, control updates
- **Files:** `SpinRender/ui/preset_controller.py` (new), `SpinRender/ui/main_panel.py` (refactor)
- **Status:** ✅ Complete

### Task 7.5: Extract ControlsSidePanel
- **Priority:** P2
- **Effort:** 2d
- **Dependencies:** 7.4
- **Deliverables:**
  - Create `SpinRender/ui/controls_side_panel.py`
  - Move UI construction methods: `create_controls_panel`, `create_header`, `create_preset_section`, `create_parameters_section`, `create_rotation_controls`, `create_axis_control`, `create_period_control`, `create_direction_control`, `create_lighting_control`, `create_output_settings_section`, `create_export_section`
  - Keep in `SpinRenderPanel`: `create_status_bar`, `create_section_label`, `create_numeric_input` (helpers)
  - `ControlsSidePanel` constructor: `__init__(self, parent, settings, board_path)`
  - Store created controls as instance attributes for parent access
  - Event handlers bound to parent callbacks (passed via constructor or direct refs)
  - Update `SpinRenderPanel.build_ui()` to instantiate `ControlsSidePanel`
  - Update `_init_preset_controller()` to pull controls from `self.controls_side_panel`
  - Tests: UI construction, control creation, settings application
- **Files:** `SpinRender/ui/controls_side_panel.py` (new), `SpinRender/ui/main_panel.py` (refactor)
- **Risk:** Medium — many control references need correct wiring
- **Status:** 🔄 In Progress (next task)

### Task 7.6: Refactor SpinRenderPanel to orchestrator
- **Priority:** P2
- **Effort:** 1.5d
- **Dependencies:** 7.2, 7.3, 7.4, 7.5
- **Deliverables:**
  - Reduce `SpinRenderPanel` from ~1,200 lines to ~300 lines
  - Remove all extracted methods
  - Keep only: `__init__`, `build_ui`, event handlers that forward to controllers, `enable_left_panel_controls`, `cleanup`
  - Instantiate and wire: `PreviewPanel`, `RenderController`, `PresetController`, `ControlsSidePanel`
  - Simplify state management (pass RenderSettings to controllers)
  - Tests: integration tests verify all delegates work
- **Files:** `SpinRender/ui/main_panel.py` (final refactor)
- **Verification:** Line count < 400, each extracted class has single responsibility
- **Status:** Pending

### Task 7.7: Update module-level imports
- **Priority:** P2
- **Effort:** 0.5d
- **Dependencies:** 7.6
- **Deliverables:**
  - Update `SpinRender/__init__.py` to expose new simplified exports
  - Update any imports from external code (KiCad plugin entry point)
  - Verify import chain doesn't create cycles
- **Status:** Pending

---

## Phase 8: Testing & Final Integration (P1 — Interleave throughout)

**Interleave testing tasks with implementation.** See TDD_PLAN.md for structure.

### Testing Tasks (run in parallel with implementation)

| Task | When to run | Effort |
|------|-------------|--------|
| 8.1: Write theme unit tests | After Task 1.1 | 1d |
| 8.2: Write custom_controls unit tests | After Task 1.5 | 2d |
| 8.3: Write text_styles unit tests | After Task 3.6 | 0.5d |
| 8.4: Write helpers unit tests | After Task 4.2 | 0.5d |
| 8.5: Write component integration tests | After Task 4.4 | 1d |
| 8.6: Write validation tests | After Task 6.3 | 0.5d |
| 8.7: Write preview_manager tests | After Task 7.2 | 1d |
| 8.8: Write render_controller tests | After Task 7.3 | 1d |
| 8.9: Write state_manager tests | After Task 7.4 | 1d |
| 8.10: Write full suite integration tests | After Task 7.7 | 1d |
| 8.11: Coverage validation & fix gaps | Final | 1d |

**Overall coverage target:** ≥80% (TDD_PLAN.md Section 1)

---

## Critical Path & Timeline

```
Week 1:
  Days 1-2: Phase 0 (setup) + Phase 1.1-1.3
  Days 3-4: Phase 1.4-1.5 (custom controls colors — bulk of work)
  Day 5: Phase 1.6-1.9 (dialogs, main_panel, verification)

Week 2:
  Day 1: Phase 2.1-2.2 (dependency fix)
  Days 2-3: Phase 2.3 (state unification)
  Days 4-5: Phase 3 (typography) + Phase 4.1-4.2 (component helpers)

Week 3:
  Days 1-2: Phase 4.3 (standardize all controls)
  Day 3: Phase 5 (interaction integrity)
  Days 4-5: Phase 6 (validation layer)

Week 4:
  Day 1: Phase 7.1 (analysis)
  Days 2-4: Phase 7.2-7.4 (extract 3 managers)
  Day 5: Phase 7.5-7.6 (project manager + refactor panel)

Week 5:
  Days 1-2: Phase 7.7 (final cleanup)
  Days 3-4: Testing tasks 8.1-8.10 (parallel)
  Day 5: Coverage validation, final integration test, documentation update

**Total estimated elapsed time:** 4-5 weeks with one developer
**Parallelization potential:** Phases 3 and 4 can run ~50% parallel; testing interleaved
```

---

## Risk Register

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Theme colors incomplete/mismatched | High | Medium | Thorough grep verification; visual testing before proceeding |
| Dependency inversion breaks imports | High | Medium | Use feature flags, work in isolation branch, comprehensive smoke test |
| God Class extraction uncovers hidden coupling | High | High | Do detailed analysis Task 7.1 first; allow iterative extraction |
| Testing time underestimates | Medium | High | Interleave testing with implementation; 20% buffer allocated |
| wxPython mocking issues | Medium | Medium | Build robust conftest fixtures early; document patterns |
| KiCad integration test unavailable | Low | High | Mock KiCad API; use headless smoke tests |

---

## Success Criteria

- [ ] All theme colors centralized in `theme.py`; no wx.Colour elsewhere
- [ ] `theme.py` is the single source of truth (docs/MIGRATION_STRATEGY.md verification)
- [ ] All 13 custom controls use unified construction pattern
- [ ] All components use TextStyle for fonts
- [ ] Mouse pass-through working for non-interactive labels
- [ ] Contrast validation passes ≥95% of tokens
- [ ] SpinRenderPanel ≤400 lines (extracted modules cover responsibilities)
- [ ] Test coverage ≥80% overall (per module targets in TDD_PLAN.md)
- [ ] Plugin loads and functions correctly in KiCad
- [ ] No regression in existing functionality (all manual tests pass)

---

## Notes

- **Worktree Strategy:** Each phase or major task can be done in separate git worktree for isolation (see dmux-workflows skill)
- **Parallel Execution:** Phases 3 & 4 can overlap; testing tasks should be done immediately after each feature
- **Rollback Plan:** Each major task committed on feature branch; merge only after verification
- **Documentation Updates:** Update README.md and developer docs as APIs change
- **Code Review:** Use `/code-review` agent after each major task (per CLAUDE.md guidelines)
