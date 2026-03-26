# Module Reference

<!-- Generated: 2026-03-25 | Files scanned: 30 Python modules | Token estimate: ~800 -->

## Core Modules (`SpinRender/core/`)

### `theme.py` (532 lines)
**Purpose**: Singleton theme manager with YAML-based design tokens

**Key Classes**:
- `Theme` - Singleton theme manager
  - `load(name="dark", force=False)` → Theme
  - `current() → Theme`
  - `color(path: str) → wx.Colour`
  - `_resolve_ref(ref: str) → Any`
  - `_apply_darken(value, amount)`
  - `_apply_lighten(value, amount)`
  - `_apply_mix(a, b, ratio)`

**Token Resolution**:
```
colors.primary
├── raw value: "#ff0000"
├── variable ref: "ref: colors.primary"
├── function: "func: darken(colors.bg, 0.1)"
└── composed: "mix(colors.bg, colors.fg, 0.5)"
```

**Dependencies**: PyYAML, logging, pathlib, re

---

### `locale.py` (~170 lines)
**Purpose**: Internationalization (i18n) singleton

**Key Classes**:
- `Locale`
  - `load(lang="en_US")`
  - `current() → Locale`
  - `get(key: str, **kwargs) → str` (format with args)

**Sources**: YAML files in `resources/locale/`
- `en.yaml` - base translations
- `en_US.yaml` - US English variants
- `en_US_COMPLETE.yaml` - full locale set

**Usage**: `_locale.get("component.button.render.label")`

---

### `presets.py` (268 lines)
**Purpose**: Preset management (save/load/delete render settings)

**Key Classes**:
- `PresetManager`
  - `__init__(board_path=None)`
  - `save_preset(name, settings, is_global=False) → bool`
  - `load_preset(name) → RenderSettings`
  - `delete_preset(name) → bool`
  - `list_presets() → list[str]`
  - `get_preset_path(name, is_global=False) → str`
  - `save_last_used_settings(settings)`
  - `get_last_used_settings() → RenderSettings | None`

**Storage Locations**:
- Global: `~/.spinrender/presets/{name}.json`
- Project: `{board_dir}/.spinrender/{name}.json`

**Data Format**: JSON serialized `RenderSettings.to_dict()`

---

### `preview.py` (884 lines)
**Purpose**: OpenGL viewport renderer for 3D PCB preview

**Key Classes**:
- `GLPreviewRenderer` (wx.GLCanvas)
  - `__init__(parent, board_path)`
  - `load_board(board_path) → bool`
  - `render_frame(camera_pos, lighting, resolution) → wx.Bitmap`
  - `start_render_animation(frames, callback)`
  - `stop_render_animation()`
  - `update_view_rotation(dx, dy)`
  - `set_render_mode(mode: str)`  # 'wireframe', 'shaded', 'both'

**Integrations**:
- trimesh for mesh loading
- OpenGL for rendering
- numpy for transforms

---

### `render_controller.py` (NEW)
**Purpose**: Asynchronous render orchestration

**Key Classes**:
- `RenderController`
  - `start_render(board_path, settings, progress_cb, complete_cb)`
  - `cancel()`
  - `is_rendering() → bool`

**Responsibilities**:
- Manage subprocess lifecycle (Blender CLI)
- Thread-safe progress callbacks via wx.CallAfter()
- Render cancellation handling

---

### `renderer.py` (605 lines)
**Purpose**: Core rendering engine (frame generation, export)

**Key Functions**:
- `render_animation(settings, board_path, progress_callback) → list[str]`
- `render_single_frame(settings, board_path) → str`
- `export_video(frames, output_path, fps) → bool`
- `export_gif(frames, output_path, fps) → bool`
- `build_camera_path(settings) → list[dict]`

**Input**: `RenderSettings` object (resolution, lighting, camera path, etc.)
**Output**: PNG frames + MP4/GIF final render

---

### `settings.py` (~100 lines)
**Purpose**: RenderSettings data class (serializable configuration)

**Class**: `RenderSettings`
- Resolution: `width`, `height`
- Camera: `board_tilt`, `board_roll`, `spin_tilt`, `spin_heading`
- Animation: `period`, `easing`, `direction`
- Lighting: `lighting` preset name
- Output: `format`, `resolution`, `bg_color`, `output_auto`, `output_path`
- Advanced: `render_mode`, `logging_level`, `theme_mode`

**Methods**:
- `to_dict() → dict`
- `from_dict(d: dict) → RenderSettings`
- `validate() → list[str]` (error messages)

---

## UI Modules (`SpinRender/ui/`)

### `main_panel.py` (672 lines)
**Purpose**: Main application window (top-level frame)

**Key Classes**:
- `SpinRenderPanel` (wx.Panel)
  - `__init__(parent, board_path)`
  - `build_ui()`
  - `reapply_theme()` - hot-reload orchestration
  - `enable_parameter_controls(enable: bool)`
  - `on_render(event)` - render trigger
  - `on_render_progress(current, total, message, frame_path)`
  - `on_render_finished(result, error)`
  - `schedule_save()` - debounced settings persist
  - `save_settings()` - write to preset manager

**Composition**:
- `ControlsSidePanel` (left, 450px fixed)
- `PreviewPanel` (right, expandable)
- `StatusBar` (bottom)
- Various modal dialogs

**State Management**:
- `settings` - current RenderSettings
- `render_controller` - RenderController instance
- `preset_controller` - PresetController instance
- `parameter_controller` - ParameterController instance

---

### `preview_panel.py` (488 lines)
**Purpose**: Preview viewport with render playback overlay

**Key Classes**:
- `PreviewPanel` (wx.Panel)
  - `_create_viewport(board_path)` → GLPreviewRenderer
  - `_create_overlay_widgets()` - top/bottom overlays
  - `update_preview_overlay()` - update metadata labels
  - `start_playback(frames: list[str])`
  - `stop_playback()`
  - `on_playback_timer(event)`

**Components**:
- `GLPreviewRenderer` - OpenGL canvas (from core.preview)
- `ov_top_left` - metadata (preset name or parameters)
- `ov_top_right` - render progress
- `ov_bottom` - frame counter / playback controls
- `render_preview_panel` - full-frame render preview overlay

---

### `controls_side_panel.py` (607 lines)
**Purpose**: Left sidebar with all rendering controls

**Key Classes**:
- `ControlsSidePanel` (wx.Panel)
  - `create_controls_panel(parent)`
  - `create_preset_row()` - hero/spin/flip/custom cards
  - `create_resolution_section()` - width/height sliders + dropdown
  - `create_lighting_section()` - ambient/diffuse/specular + bg picker
  - `create_camera_section()` - tilt/roll/orbit sliders
  - `create_output_section()` - format/resolution/fps + render button
  - `reapply_theme()` - hot-reload support

**Custom Controls Used**:
- `CustomSlider` - with theme-aware tick marks
- `CustomToggleButton` - binary options (direction, lighting, logging)
- `CustomButton` - action buttons (render, cancel, options, etc.)
- `PresetCard` - preset thumbnail + label
- `CustomDropdown` - format/resolution selection
- `CustomColorPicker` - background color selection

**Hot-Reload**: `_hotload_map` tracks theme-dependent widgets for refresh
**Control Registry**: `_registry` (ControlRegistry) for bulk enable/disable

---

### `custom_controls.py` (1553 lines) **LARGEST MODULE**
**Purpose**: Owner-drawn wx widgets with full theme integration

**Key Classes**:
- `CustomSlider` - slider with custom track, thumb, ticks (363 lines)
- `CustomToggleButton` - toggle switch with animation (206 lines)
- `CustomButton` - button with hover/active states (192 lines)
- `PresetCard` - preset display card (image + label) (148 lines)
- `CustomDropdown` - dropdown with custom items (192 lines)
- `CustomColorPicker` - color well with popup picker (162 lines)
- `CustomListView` - virtual list for preset items (177 lines)
- `CustomListItem` - individual list entry (129 lines)
- `ThumbnailCache` - LRU cache for preset images (58 lines)

**Theme Integration**:
Each control binds to `TextStyles` and theme tokens:
- `styles.normal.color` (text)
- `colors.primary` (accent)
- `layout.control.padding` (spacing)
- `icons.delete` (delete action icon)

**Pattern**: All custom controls emit custom wx events (EVT_*).

---

### `dialogs.py` (1629 lines) **SECOND LARGEST**
**Purpose**: Modal dialogs for user interactions

**Key Classes**:
- `RecallPresetDialog` (wx.Dialog) - preset management (456 lines)
  - `__init__(parent, preset_controller)`
  - `_build_ui()` - CustomListView with thumbnails
  - `get_selected_preset() → str`

- `SavePresetDialog` (wx.Dialog) - save new preset (165 lines)
  - Name entry + thumbnail preview

- `AdvancedOptionsDialog` (wx.Dialog) - advanced settings (468 lines)
  - Notebook with tabs: Render, Material, Post-processing
  - Theme mode toggle (dark/light/system)
  - `get_settings() → RenderSettings`

- `AboutDialog` (wx.Dialog) - app info + links (231 lines)
  - Version, license, donation links
  - Gift icon for "free for personal use"

**Custom List View**:
Uses `CustomListView` + `CustomListItem` for preset selection with delete.

---

### `preset_controller.py` (304 lines)
**Purpose**: Business logic for preset operations

**Key Classes**:
- `PresetController`
  - `__init__(preset_manager, main_panel)`
  - `save_preset(name, is_global)`
  - `recall_preset(name)`
  - `delete_preset(name)`
  - `list_available_presets() → dict[str, list[str]]`  # global + project
  - `_generate_thumbnail(settings) → wx.Bitmap`
  - `check_preset_match() → bool` - compare settings to preset

**Events**:
- `EVT_PRESET_SAVED` - emitted after save
- `EVT_PRESET_RECALLED` - emitted after recall
- `EVT_PRESET_DELETED` - emitted after delete

**Thumbnail Generation**:
Renders single frame at low resolution (200x150) for preset cards.

---

### `parameter_controller.py` (213 lines)
**Purpose**: Bidirectional binding between UI controls and RenderSettings

**Key Classes**:
- `ParameterController`
  - `__init__(settings, controls, preview, preset_controller, schedule_save)`
  - `bind_control(control, setting_path: str, converter=None)`
  - `unbind_control(control)`
  - `update_settings_from_ui()`
  - `update_ui_from_settings()`

**Bound Controls**:
- Sliders → float settings (with /10 or /100 scaling)
- Toggles → enum settings ('ccw'/'cw', 'studio'/'custom')
- Color picker → hex color strings
- Dropdowns → format/resolution strings

**Auto-Save**: Triggers `schedule_save()` callback on change (debounced 500ms).

---

### `text_styles.py` (176 lines)
**Purpose**: Typography singleton (font family, size, weight)

**Key Classes**:
- `TextStyle` - named tuple (family, size, weight, color)
- `TextStyles` - class with static style attributes
  - `heading`, `subheading`, `body`, `caption`, `mono`
  - `info`, `warning`, `error`
  - `button`, `label`, `nav`, `dropdown`, `status`
  - `icon`, `icon_lg`
- `TextStyles.initialize(theme)` - load from theme tokens

**Theme Tokens**:
- `typography.{style}.family`
- `typography.{style}.size`
- `typography.{style}.weight`
- `colors.*` for text color

**Methods**: `TextStyle.create_font() → wx.Font`

---

### `status_bar.py` (~100 lines)
**Purpose**: Render progress status bar

**Key Classes**:
- `StatusBar` (wx.StatusBar)
  - `set_status(message, progress=0.0, fg_color=None)`
  - `set_ready()`
  - `set_progress()`
  - `set_complete()`
  - `set_error(message)`
  - `_on_paint(event)` - custom draw with progress bar

**State**:
- Fields: status message (left), resolution dims (right)
- Progress bar: drawn in background field during render

---

### `helpers.py` (539 lines)
**Purpose**: UI utility functions

**Key Functions**:
- `create_text(parent, label, style_name)` - themed StaticText with hot-reload
- `create_section_label(parent, text, style_name)`
- `create_numeric_input(parent, label, initial, min, max)`
- `create_button_row(parent, buttons)`
- `format_text(text, style)` - apply uppercase, etc.
- `_text_registry` (global weakref set) - tracks all themed text

**Hot-Reload**: `_text_registry` allows `reapply_text_styles()` to update all text widgets.

---

### `validation.py` (~250 lines)
**Purpose**: Theme validation utilities

**Key Functions**:
- `validate_theme_file(path) → ValidationReport`
- `validate_color_token(token_def) → bool`
- `validate_token_references(data, refs)`
- `check_circular_references(graph) → list[str]`
- `validate_theme_schema(data) → list[ValidationError]`

**Used By**: `test_validate_theme.py` for CI validation; also `SpinRender/validate_theme.py` CLI tool.

---

### `dependency_dialog.py` (368 lines)
**Purpose**: Dependency checking and installation UI

**Key Classes**:
- `DependencyChecker`
  - `check_and_prompt() → bool`
  - `_check_wxpython() → bool`
  - `_check_opengl() → bool`
  - `_check_trimesh() → bool`
  - `_install_missing() → bool`
  - `_show_install_dialog(missing: list)`

**Dependencies Checked**:
- wxPython (importable)
- OpenGL support (GL/glext.h)
- trimesh (importable + version)
- PyOpenGL (importable)
- PyYAML (importable)

**Installation Prompt**:
If dependencies missing, dialog offers to run:
```bash
pip install --user PyYAML PyOpenGL PyOpenGL-accelerate trimesh numpy
```
Platform-specific: macOS adds pyobjc-core, pyobjc-framework-Cocoa.

---

### `dependencies.py` (178 lines)
**Purpose**: Dependency validation without UI

**Key Classes**:
- `DependencyChecker` (console version)
  - `check_all() → dict[str, bool]`
  - `missing_deps` property

**Usage**: Called from plugin entry point before importing heavy modules.

---

### `events.py` (~100 lines)
**Purpose**: Custom wx events for component communication

**Key Events**:
- `EVT_PARAMETER_INTERACTION` - emitted when any control changes
- `EVT_PRESET_SAVED` - preset saved
- `EVT_PRESET_RECALLED` - preset loaded
- `EVT_PRESET_DELETED` - preset removed
- `EVT_COLOURPICKER_CHANGED` - color selection made

**Pattern**: Event classes inherit from `wx.PyEventBinder`; use `widget.ProcessEvent()`.

---

### `registry.py` (~150 lines)
**Purpose**: Control registry for bulk operations

**Key Classes**:
- `ControlRegistry`
  - `add(control, **metadata)` - register control with optional tags
  - `controls(section=None)` - retrieve controls
  - `controls_by_type(ctrl_class)` - filter by type
  - `enable_all(enable=True)` - batch enable/disable

**Usage**: `main_panel.enable_parameter_controls(False)` disables all sliders/buttons during render.

---

## Foundation Modules (`SpinRender/foundation/`)

### `fonts.py`
**Purpose**: Font family loading and registration

**Functions**:
- `register_fonts()` - add private font directories to wx
- `get_font_family(name) → str` - resolve font name from theme token

**Fonts**:
- JetBrains Mono (monospace)
- Oswald (display/headings)
- Material Design Icons (icon font)

---

### `icons.py`
**Purpose**: Icon font/glyph resolution

**Functions**:
- `get_glyph(name) → str` - return Unicode codepoint for icon name
- `load_svg(name) → wx.svg.SVGimage` - load SVG from resources/icons/

**Icons**:
- App actions: render, exit, settings, save, folder, close, stop, trash, etc.
- Controls: cw, ccw, sun, moon, computer, bolt, cloud, edit
- Status: status-ok, status-error, alert-octagram
- Axes: axis-x, axis-y, axis-y-rot, axis-z-rot
- Presets: preset-hero, preset-spin, preset-flip, preset-custom
- External: github, heart, web, tag, help-circle, release, etc.

---

## Utils Modules (`SpinRender/utils/`)

### `logger.py`
**Purpose**: Centralized logging configuration

**Classes**:
- `SpinLogger`
  - `setup(level='info', log_file=None)` - configure root logger
  - `get_logger(name) → logging.Logger`

**Configuration**:
- Format: `%(asctime)s [%(levelname)-8s] %(name)s: %(message)s`
- Default level: INFO (configurable via settings)
- Console handler only (no file by default)

---

### `check_dependencies.py` (289 lines)
**Purpose**: Standalone dependency validation (CLI usage)

**Functions**:
- `check_all() → bool`
- `check_wxpython() → bool`
- `check_opengl() → bool`
- `check_trimesh() → bool`
- `print_report()`

**Entry Point**: `python -m SpinRender.utils.check_dependencies`

---

## Entry Point

### `spinrender_plugin.py` (322 lines)
**Purpose**: KiCad Action Plugin registration and lifecycle

**Key Classes**:
- `SpinRenderPlugin(pcbnew.ActionPlugin)`
  - `defaults()` - plugin metadata (name, category, description)
  - `Run()` - main entry point when user clicks toolbar button

**Lifecycle**:
1. KiCad loads plugin module
2. Calls `SpinRenderPlugin().register()`
3. User clicks toolbar → `Run()` executes
4. Dependency check → create `SpinRenderFrame`
5. Frame shows main panel → user interacts

**Singleton Pattern**: Only one `SpinRenderFrame` allowed; existing instance raised if already open.

**Hot-Reload**: Frame includes theme file watcher timer (1s interval) that calls `Theme.reload()` and `panel.reapply_theme()` if mtime changes.

---

## Module Count Summary

| Category | Count | Total Lines (approx) |
|----------|-------|---------------------|
| Core     | 7     | ~3,200              |
| UI       | 15    | ~7,500              |
| Foundation | 2   | ~300                |
| Utils    | 2     | ~400                |
| **Total** | **30** | **~11,400**        |

**Largest Modules**:
1. `ui/custom_controls.py` - 1553 lines (owner-drawn widgets)
2. `ui/dialogs.py` - 1629 lines (modal dialogs)
3. `ui/main_panel.py` - 672 lines (main container)
4. `core/preview.py` - 884 lines (OpenGL viewport)
5. `ui/controls_side_panel.py` - 607 lines (sidebar controls)
