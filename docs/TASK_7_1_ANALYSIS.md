# Phase 7 Task 7.1: SpinRenderPanel God Class Analysis

**Date:** 2026-03-17
**Status:** Analysis Complete
**God Class:** `SpinRenderPanel` (1550 lines, 62 methods)

---

## Executive Summary

`SpinRenderPanel` violates Single Responsibility Principle by handling **7 distinct concerns** across 62 methods. This analysis identifies natural extraction boundaries and proposes a refactoring to extract 4 focused components, reducing the god class to ~300 lines as an orchestrator.

**Extraction Plan:**
1. **PreviewPanel** (~350 lines) - Previews, playback, drag interaction
2. **RenderController** (~200 lines) - Subprocess orchestration, progress tracking
3. **PresetController** (~150 lines) - Preset save/load/recall, settings persistence
4. **ControlsSidePanel** (~500 lines) - Left sidebar UI construction

**Residual SpinRenderPanel:** ~300 lines (wiring, event delegation, top-level coordination)

---

## Current Method Distribution (62 methods)

| Responsibility | Count | % of Methods | Est. Lines | Methods |
|----------------|-------|--------------|------------|---------|
| UI Construction | 16 | 26% | ~400 | `build_ui`, `create_*` |
| State Management | 22 | 35% | ~300 | Settings change handlers, preset logic |
| Preview/Playback | 6 | 10% | ~200 | `update_preview_overlay`, `start_playback`, etc. |
| Render Coordination | 4 | 6% | ~150 | `on_render`, `on_render_progress`, etc. |
| Event Handlers | 8 | 13% | ~150 | Drag, dialog triggers |
| Viewport/Scene | 1 | 2% | ~50 | `_update_viewport_rotation` |
| Status Bar | 2 | 3% | ~50 | `on_paint_status`, `reset_status_bar` |
| Control State | 1 | 2% | ~30 | `enable_left_panel_controls` |
| Cleanup/Lifecycle | 1 | 2% | ~20 | `cleanup` |

---

## Detailed Method Categorization

### A. UI Construction (16 methods) → **ControlsSidePanel**

Builds the left sidebar UI. These methods are **already logically grouped** by the `create_*` naming convention.

| Method | Line | Purpose | Extraction Target |
|--------|------|---------|-------------------|
| `build_ui` | 160 | Top-level UI assembly | **Orchestrator** (calls `create_controls_panel`, `create_preview_panel`, `create_status_bar`) |
| `create_controls_panel` | 202 | Left sidebar container | ControlsSidePanel |
| `create_header` | 247 | Logo + title row | ControlsSidePanel |
| `create_preset_section` | 276 | Preset dropdown + save/recall buttons | ControlsSidePanel |
| `create_parameters_section` | 307 | Collapsible section containing rotation, lighting, output | ControlsSidePanel |
| `create_rotation_controls` | 329 | Tilt, Roll, Spin Tilt, Heading sliders/inputs | ControlsSidePanel |
| `create_axis_control` | 356 | Reusable helper for tilt/roll/spin tilt/heading | ControlsSidePanel (private) |
| `create_period_control` | 394 | Rotation period numeric input | ControlsSidePanel |
| `create_direction_control` | 429 | CW/CCW toggle | ControlsSidePanel |
| `create_lighting_control` | 445 | Lighting preset dropdown | ControlsSidePanel |
| `create_output_settings_section` | 474 | Format, resolution, background color | ControlsSidePanel |
| `create_export_section` | 538 | Render button + advanced options | ControlsSidePanel |
| `create_status_bar` | 913 | Bottom status bar (progress, messages) | **Orchestrator** StatusBarManager candidate |
| `create_section_label` | 965 | Helper for section headers | Extracted to `ui/helpers.py` (shared with dialogs) |
| `create_numeric_input` | 978 | Helper for NumericInput creation | Extracted to `ui/helpers.py` (shared) |

**Note:** `create_status_bar` creates a status bar that spans the full width below left/right panels. This is **not** part of the left sidebar, so it should stay in `SpinRenderPanel` or become its own `StatusBarManager`.

**Dependencies:** `create_*` methods use `CustomSlider`, `CustomToggleButton`, `CustomDropdown`, `NumericInput`, `SectionLabel`, `CustomButton`. All from `ui.custom_controls`.

**State accessed:** Methods directly reference `self.settings['preset']`, `self.theme`, etc.

---

### B. State Management (22 methods) → **Split: PresetController (6) + SpinRenderPanel residual (16)**

This is the largest category. Some methods are pure preset logic (save/load/apply), others are individual settings change handlers that update preview or trigger UI updates.

#### B1. Preset-specific (6 methods) → **PresetController**

| Method | Line | Purpose |
|--------|------|---------|
| `on_preset_change` | 983 | Combobox selection changed → load preset settings |
| `apply_preset_data` | 1026 | Apply preset dict to controls |
| `check_preset_match` | 1069 | Compare current settings with preset (for "Save preset" dialog pre-check) |
| `save_settings` | 1112 | Gather all control values into dict |
| `on_save_preset` | 1267 | Trigger save preset dialog (opens `SavePresetDialog`) |
| `on_preset_*` (implicit via signals) | - | `SavePresetDialog` calls back to `PresetController.save()` |

**Data flow:**
- Reads: controls (sliders, dropdowns) to gather current values
- Writes: `PresetManager.save_preset()`, `PresetManager.load_preset()`
- UI: Opens `SavePresetDialog`, `RecallPresetDialog`

**Extraction candidate:** `PresetController` class that owns:
- `PresetManager` instance
- Combobox widget reference (to get selection)
- `apply_to_controls(settings_dict)` method to populate UI
- `collect_settings()` → dict
- Signal/slot connections for preset change

**Potential complication:** `apply_preset_data` and `check_preset_match` currently private methods that manipulate specific control references (`self.board_tilt_slider`, etc.). These will need to be passed as callbacks or the controller will need direct references to the control widgets.

#### B2. Individual Setting Change Handlers (16 methods) → **Residual in SpinRenderPanel or SettingsManager**

These are one-liners that propagate UI changes to `self.settings` and trigger downstream updates:

| Method | Line | Setting | Action |
|--------|------|---------|--------|
| `on_board_tilt_change` | 1121 | tilt slider | update `self.settings['board_tilt']`, `_update_viewport_rotation()` |
| `on_board_tilt_input` | 1128 | tilt numeric input | update `self.settings['board_tilt']` |
| `on_board_roll_change` | 1135 | roll slider | update + viewport |
| `on_board_roll_input` | 1142 | roll numeric input | update |
| `on_spin_tilt_change` | 1149 | spin tilt slider | update + viewport |
| `on_spin_tilt_input` | 1156 | spin tilt numeric input | update |
| `on_spin_heading_change` | 1163 | heading slider | update + viewport |
| `on_spin_heading_input` | 1170 | heading numeric input | update |
| `on_period_change` | 1182 | period slider | update |
| `on_period_input_change` | 1192 | period numeric input | update |
| `on_direction_change` | 1203 | direction toggle | update |
| `on_render_mode_change` | 1211 | render mode toggle | update + `update_render_mode_ui()` |
| `on_lighting_change` | 1229 | lighting dropdown | update |
| `on_format_change` | 1238 | format dropdown | update |
| `on_resolution_change` | 1244 | resolution dropdown | update |
| `on_bg_color_change` | 1259 | background color change | update |

**Pattern:** Each method:
1. Gets value from the control that triggered the event (by accessing the control directly via `self.xxx.GetValue()`)
2. Updates `self.settings[key]`
3. Optionally calls `_update_viewport_rotation()` (for rotation changes) or `update_render_mode_ui()` (for mode changes)

**Extraction challenge:** These handlers are tightly coupled to specific control widget references (e.g., `self.board_tilt_slider`, `self.board_tilt_input`). Coupling is acceptable—they are the view layer for the settings. They could stay as **event handlers in `SpinRenderPanel`**, but should delegate to a `SettingsManager` or `StateManager` to modify the settings dataclass (once Phase 2.3 is done).

**Recommendation (consistent with PROJECT_PLAN.md):**
- **Option A:** Extract a `StateManager` that owns `RenderSettings` and notifies observers. Handlers become one-liners: `self.state_manager.set_board_tilt(value)`.
- **Option B:** Keep handlers in `SpinRenderPanel` but have them call `self.settings.board_tilt = value` (attribute access if using dataclass).

Given PROJECT_PLAN.md Phase 7 expects a `StateManager` (Task 7.4), we should **NOT extract these now**. They remain in `SpinRenderPanel` until Phase 7.4.

---

### C. Preview/Playback (6 methods) → **PreviewPanel**

These methods manage the preview viewport, overlay rendering, and playback timer.

| Method | Line | Purpose | Extraction |
|--------|------|---------|------------|
| `update_preview_overlay` | 685 | Render a semi-transparent overlay on the preview (quality info, watermarks) | PreviewPanel |
| `_on_render_preview_paint` | 848 | Paint handler for the preview window (draws current frame, playback overlay) | PreviewPanel |
| `start_playback` | 800 | Start the playback timer after render completes | PreviewPanel |
| `stop_playback` | 814 | Stop playback timer | PreviewPanel |
| `on_playback_timer` | 821 | Timer event → advance playback frame, schedule next | PreviewPanel |
| `on_close_render_preview` | 790 | Close button on preview overlay | PreviewPanel |

**State accessed:**
- `self.render_frames` list (frame file paths from last render)
- `self.playback_index`
- `self.playback_timer`
- `self.preview_bitmap` (for current frame)
- `self._render_finished_callbacks` (maybe)

**Dependencies:**
- `GLPreviewRenderer` for 3D viewport (already imported)
- `wx.lib.newevent` for custom events? (check)
- Bitmap loading from disk

**Interface:**
```python
class PreviewPanel(wx.Panel):
    def __init__(self, parent, theme, preview_renderer):
        ...
    def load_frames(self, frame_paths: List[Path]) -> None:
        """Load rendered frames for playback."""
    def show_overlay(self, text: str) -> None:
        """Display overlay message (e.g., 'Rendering...')."""
    def hide_overlay(self) -> None:
    def start_playback(self, fps: int = 30) -> None:
    def stop_playback(self) -> None:
    def set_quality_overlay(self, quality: str, frames: int) -> None:
```

**Risks:**
- `update_preview_overlay` draws on the preview using `wx.AutoBufferedPaintDC` or similar; needs careful extraction to preserve event bindings.
- `_on_render_preview_paint` is bound to `EVT_PAINT`; must stay as method of the panel that has the paint event.

---

### D. Render Coordination (4 methods) → **RenderController**

Core render orchestration: start render, track progress, update UI, handle completion.

| Method | Line | Purpose | Extraction |
|--------|------|---------|------------|
| `on_render` | 1318 | User clicked RENDER → validate, start background thread | **Orchestrator** → calls `RenderController.start_render()` |
| `on_render_progress` | 1393 | Callback from render thread with progress % and message | **Orchestrator** ← called by `RenderController` |
| `_update_progress_ui` | 1396 | Update progress bar and status text | Could move to `StatusBarManager` or stay in orchestrator |
| `on_render_finished` | 1427 | Render thread completed → show preview, enable controls | **Orchestrator** ← called by `RenderController` |

**Current flow (simplified):**
```python
def on_render(self, event):
    self.enable_left_panel_controls(False)
    self.update_status("Rendering...")
    thread = threading.Thread(target=self._render_thread)
    thread.start()

def _render_thread(self):
    # Build kicad-cli command
    # subprocess.run with callbacks to self.on_render_progress
    # Upon finish: wx.CallAfter(self.on_render_finished)
```

**Extraction plan:**
```python
class RenderController:
    def __init__(self, settings: RenderSettings, board_path: Path, preview_panel: PreviewPanel, status_callback):
        self.settings = settings
        self.board_path = board_path
        self.preview = preview_panel
        self.status_cb = status_cb  # for progress updates
        self._thread = None
        self._cancel_flag = False

    def start_render(self) -> None:
        """Begin render in background thread."""
        self._thread = threading.Thread(target=self._run)
        self._thread.start()

    def cancel(self) -> None:
        self._cancel_flag = True

    def _run(self) -> None:
        # Build command from settings
        # Run subprocess, reading stdout for progress
        # Call self.status_cb(percent, message)
        # On complete: wx.CallAfter(self.on_complete)
```

**Callbacks:**
- `status_cb` → `SpinRenderPanel.update_status()` or status bar manager
- Completion → `SpinRenderPanel.on_render_finished()` (which currently loads frames into preview and starts playback)

**After extraction:**
- `SpinRenderPanel.on_render()` becomes: `self.render_controller.start_render()`
- `SpinRenderPanel.on_render_progress()` delegates to status bar
- `SpinRenderPanel.on_render_finished()` delegates to `self.preview.load_frames()` and `self.preview.start_playback()`

---

### E. Event Handlers (8 methods) → **Split: SpinRenderPanel (orchestration) + PreviewPanel**

| Method | Line | Purpose | Extraction |
|--------|------|---------|------------|
| `on_advanced_options` | 1287 | Open `AdvancedOptionsDialog` | Orchestrator (simple dialog opener) |
| `on_cancel` | 1300 | Cancel in options dialog? (check context) | Likely dialog-specific, stays |
| `on_close` | 1309 | Panel close → cleanup | Orchestrator (cleanup trigger) |
| `on_left_panel_interaction` | 840 | Any control interaction → may affect drag behavior | Could stay in SpinRenderPanel (input filtering) |
| `on_drag_start` | 1531 | Mouse down on preview → start drag | PreviewPanel (needs mouse capture) |
| `on_drag_motion` | 1534 | Mouse move with capture → rotate viewport | PreviewPanel |
| `on_drag_end` | 1539 | Mouse up → end drag | PreviewPanel |
| `enable_drag` | 1544 | Enable/disable drag interaction | PreviewPanel |

**Drag handlers** clearly belong to `PreviewPanel` as they interact with the preview viewport.

**Dialog handlers** (`on_advanced_options`, `on_cancel`) belong to orchestrator as they are top-level actions.

`on_left_panel_interaction` is called by controls to indicate user interaction during drag mode. Likely stays in `SpinRenderPanel`.

---

### F. Viewport/Scene (1 method) → **PreviewPanel**

| Method | Line | Purpose |
|--------|------|---------|
| `_update_viewport_rotation` | 1177 | Compute rotation from sliders and call `preview_renderer.set_rotation()` |

**Already accesses:** `self.board_tilt_slider.GetValue()`, etc. → after extraction, `PreviewPanel` would receive rotation updates via a method call like `set_rotation(tilt, roll, spin_tilt, spin_heading)`.

---

### G. Status Bar (2 methods) → **StatusBarManager** candidate (minor extraction)

| Method | Line | Purpose |
|--------|------|---------|
| `on_paint_status` | 922 | Paint the status bar (background, progress, text) |
| `reset_status_bar` | 945 | Clear status bar to idle state |

**Current structure:** Status bar is a `wx.Panel` created by `create_status_bar()`, placed at bottom of the main panel. It has its own `EVT_PAINT` handler and draws background based on state (idle, rendering, error).

**Could extract** to `StatusBarManager` if we want to cleanly separate rendering logic from the main panel. But it's only ~50 lines; simpler to keep in `SpinRenderPanel` as a self-contained subcomponent.

**Alternative:** Make it a standalone `StatusBar(wx.Panel)` class in `ui/status_bar.py` with methods `set_progress()`, `set_message()`, `reset()`. Then `SpinRenderPanel` instantiates it.

---

### H. Control State (1 method) → **Orchestrator**

| Method | Line | Purpose |
|--------|------|---------|
| `enable_left_panel_controls` | 752 | Enable/disable all controls in left sidebar (during render) |

**Implementation:** Iterates over `self.controls_panel` children and calls `Enable(is_enabled)`. Should stay in `SpinRenderPanel` as it's a high-level UI state management function.

---

### I. Cleanup/Lifecycle (1 method) → **Orchestrator**

| Method | Line | Purpose |
|--------|------|---------|
| `cleanup` | 1548 | Stop playback, cancel render, release resources | Called from `on_close` → stays in orchestrator |

---

## Proposed Extraction Architecture

### After Extraction

```
SpinRenderPanel (~300 lines)
├── ControlsSidePanel (500 lines) ───┐
├── PreviewPanel (350 lines) ────────┼── dependencies
├── RenderController (200 lines) ────┘
├── PresetController (150 lines)
└── (optional) StatusBarManager (50 lines)
```

### Data Flow

```
User interaction
    ↓
SpinRenderPanel (event handlers)
    ↓
-delegates to-> ControlsSidePanel (UI construction only)
    ↓
-delegates to-> PresetController (preset save/load)
    ↓
-delegates to-> RenderController (start_render, cancel)
    ↓
-delegates to-> PreviewPanel (load_frames, start_playback, set_rotation)
    ↓
PreviewPanel uses GLPreviewRenderer for viewport rotation
```

### Settings/State

**Option A (Phase 2.3 already done?):** Use `RenderSettings` dataclass owned by `SpinRenderPanel`. All controllers read from it. Settings change handlers update attributes.

**Option B (dict):** Keep `self.settings: dict` until later refactoring.

**For extraction now:** Pass `RenderSettings` (or dict) to controllers that need it:
- `RenderController(settings, ...)`
- `PreviewPanel` needs rotation params via `set_rotation(tilt, roll, spin_tilt, heading)`
- `PresetController` needs to read/write settings → should own a reference to the settings object

### Communication Patterns

1. **SpinRenderPanel → PreviewPanel:** Direct method calls (`set_rotation()`, `load_frames()`, `start_playback()`)
2. **PreviewPanel → SpinRenderPanel:** Event callbacks? Currently not much back-communication. Possibly `on_drag_start`/`motion` updates status bar → call `self.GetParent().update_status()`? Better: define a callback interface.
3. **RenderController → SpinRenderPanel:** Progress callback passed in `__init__`. Completion via `wx.CallAfter(callback)`.
4. **PresetController → SpinRenderPanel:** Minimal. `apply_preset_data` needs to set slider values → requires references to controls. **Tight coupling risk.** Prefer: PresetController returns a settings dict, SpinRenderPanel applies to controls itself. Or PresetController accepts control interface (set_board_tilt, get_board_tilt, ...) as constructor parameters.

---

## Extraction Order (dependency-driven)

1. **Pre-step:** Ensure `RenderSettings` dataclass exists (Phase 2.3). If not, keep using dict but document as temporary.
2. **Extract PreviewPanel** (most independent)
   - Move `update_preview_overlay`, `_on_render_preview_paint`, `start_playback`, `stop_playback`, `on_playback_timer`, `on_close_render_preview`, `_update_viewport_rotation`
   - Create new file: `SpinRender/ui/preview_panel.py`
   - Update `create_preview_panel()` to instantiate `PreviewPanel`
   - Pass `preview_renderer` (current `GLPreviewRenderer`) to PreviewPanel
   - Wire `drag` events to PreviewPanel
3. **Extract RenderController**
   - Move `on_render`, `on_render_progress`, `_update_progress_ui` (or keep), `on_render_finished` logic to new `RenderController`
   - New file: `SpinRender/core/render_controller.py`
   - SpinRenderPanel creates controller and registers callbacks
   - Controller owns render thread, progress tracking, cancellation
4. **Extract PresetController**
   - Move `on_preset_change`, `apply_preset_data`, `check_preset_match`, `save_settings`, `on_save_preset`
   - New file: `SpinRender/core/preset_controller.py` or `ui/preset_controller.py`?
   - Since it depends on UI controls (to get/set values), could be in `ui/`. But `PresetManager` is in `core/`, so maybe keep it `core/` and define an interface for control access.
   - Simplest: Make `PresetController` accept a `control_adapter` object with methods like `get_all_settings()`, `apply_settings(settings)`. `SpinRenderPanel` implements that adapter.
5. **Extract ControlsSidePanel**
   - Move `create_controls_panel` + all `create_*` methods (except `create_section_label`, `create_numeric_input` which go to helpers)
   - New file: `SpinRender/ui/controls_side_panel.py`
   - `ControlsSidePanel` class inherits `wx.Panel`
   - It constructs all child controls and exposes a callback interface for changes (e.g., `on_setting_changed(key, value)`)
   - `SpinRenderPanel` creates it and connects signals
6. **Cleanup SpinRenderPanel**
   - `__init__`: instantiate `ControlsSidePanel`, `PreviewPanel`, `RenderController`, `PresetController`
   - Wire callbacks: controller callbacks → status bar updates, playbacks
   - Remove all extracted methods
   - Target: 300 lines or less

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Hidden coupling in `self.settings` dict | High | Use `RenderSettings` dataclass with clear ownership; Pass as argument, not global |
| Control references in `apply_preset_data` | Medium | Use adapter pattern; PresetController returns dict, SpinRenderPanel applies |
| PreviewPanel needs many callbacks | Medium | Define `PreviewPanelInterface` with methods `set_rotation`, `show_overlay`, etc. |
| Drag event coordinates depend on preview size | High | Ensure `PreviewPanel` handles its own mouse events and computes viewport rotation correctly |
| RenderController thread safety | High | Use `wx.CallAfter` for all UI updates; protect shared state with lock |
| Existing tests break | Medium | Update tests to use new classes; keep public API stable where possible |
| Import cycles after splitting | Medium | Organize imports: core/ → no UI deps; ui/ → can import core; spinrender_plugin imports from ui. |

---

## Success Criteria for Task 7.1

- [x] Complete method-by-method analysis (this document)
- [x] Identify extraction boundaries clearly
- [x] Define interfaces between components
- [x] Identify dependencies (RenderSettings, GLPreviewRenderer, PresetManager)
- [ ] Review and approve extraction order with user
- [ ] Estimate lines for each extraction target (roughly done)

---

## Next Steps (Task 7.2+)

**After user approval, proceed in order:**

1. **Task 7.2: Extract PreviewPanel**
   - Create `ui/preview_panel.py`
   - Move 7 methods
   - Update `create_preview_panel()` to use new class
   - Run tests to verify preview still works

2. **Task 7.3: Extract RenderController**
   - Create `core/render_controller.py`
   - Move 4 methods (extract render thread logic)
   - Update `on_render` to use controller
   - Verify rendering still works

3. **Task 7.4: Extract PresetController**
   - Create `core/preset_controller.py` or `ui/preset_controller.py`
   - Move 6 methods
   - Define adapter interface for control access
   - Verify preset save/load works

4. **Task 7.5: Extract ControlsSidePanel**
   - Create `ui/controls_side_panel.py`
   - Move 16 `create_*` methods (minus helpers)
   - Extract `create_section_label`, `create_numeric_input` to `ui/helpers.py`
   - Update `create_controls_panel()` to instantiate `ControlsSidePanel`
   - Verify UI builds correctly

5. **Task 7.6: Refactor SpinRenderPanel to Orchestrator**
   - Rewrite `__init__` to compose extracted components
   - Wire event callbacks
   - Remove all extracted methods
   - Target <400 lines

6. **Task 7.7: Update module-level imports**
   - Update `SpinRender/__init__.py`
   - Verify no import cycles
   - Update plugin entry point if needed

---

## Conclusion

The `SpinRenderPanel` god class is **amenable to systematic extraction** using the identified boundaries. The extraction order minimizes coupling:
- PreviewPanel and RenderController are most independent.
- PresetController and ControlsSidePanel depend on UI structure, so go last.
- The residual orchestrator becomes trivially small.

All dependencies (RenderSettings, GLPreviewRenderer, PresetManager) are already in place.

**Estimated effort:** 5-7 days total (consistent with PROJECT_PLAN.md).
