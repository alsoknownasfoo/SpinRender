<!-- Generated: 2026-03-21 | Files scanned: 29 Python files | Token estimate: ~800 -->

# Module Reference

## Core Modules (`SpinRender/core/`)

### `theme.py` (466 lines)
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

### `presets.py` (~300 lines)
**Purpose**: Preset management (save/load/delete render settings)

**Key Classes**:
- `PresetManager`
  - `__init__(board_path=None)`
  - `save_preset(name, settings, is_global=False) → bool`
  - `load_preset(name) → RenderSettings`
  - `delete_preset(name) → bool`
  - `list_presets() → list[str]`
  - `get_preset_path(name, is_global=False) → str`

**Storage Locations**:
- Global: `~/.spinrender/presets/{name}.json`
- Project: `{board_dir}/.spinrender/{name}.json`

**Data Format**: JSON serialized `RenderSettings.to_dict()`

---

### `preview.py` (338 lines)
**Purpose**: OpenGL viewport renderer for 3D PCB preview

**Key Classes**:
- `GLPreviewRenderer` (wx.GLCanvas)
  - `__init__(parent, board_path)`
  - `load_board(board_path) → bool`
  - `render_frame(camera_pos, lighting, resolution) → wx.Bitmap`
  - `start_render_animation(frames, callback)`
  - `stop_render_animation()`
  - `update_view_rotation(dx, dy)`

**Integrations**:
- trimesh for mesh loading
- OpenGL for rendering
- numpy for transforms

---

### `renderer.py` (~500 lines)
**Purpose**: Core rendering engine (frame generation, export)

**Key Functions**:
- `render_animation(settings, board_path, progress_callback) → list[str]`
- `render_single_frame(settings, board_path) → str`
- `export_video(frames, output_path, fps) → bool`
- `export_gif(frames, output_path, fps) → bool`

**Input**: `RenderSettings` object (resolution, lighting, camera path, etc.)
**Output**: PNG frames + MP4/GIF final render

---

### `settings.py` (~100 lines)
**Purpose**: RenderSettings data class (serializable configuration)

**Class**: `RenderSettings`
- Resolution: `width`, `height`
- Camera: `orbit_speed`, `elevation`, `distance`
- Lighting: `ambient`, `diffuse`, `specular`
- Material: `board_color`, `solder_color`, `copper_color`
- Output: `fps`, `duration`, `format` ("mp4" or "gif")

**Methods**:
- `to_dict() → dict`
- `from_dict(d: dict) → RenderSettings`
- `validate() → list[str]` (error messages)

---

### `locale.py` (~200 lines)
**Purpose**: Internationalization (i18n) singleton

**Key Classes**:
- `Locale`
  - `load(lang="en")`
  - `current() → Locale`
  - `get(key: str, **kwargs) → str` (format with args)

**Sources**: YAML files in `resources/locale/`
- `en.yaml` - base translations
- `en_US.yaml` - regional variants

**Usage**: `_locale.get("menu.file.open")`

---

## UI Modules (`SpinRender/ui/`)

### `main_panel.py` (669 lines)
**Purpose**: Main application window (top-level frame)

**Key Classes**:
- `SpinRenderPanel` (wx.Panel)
  - `__init__(parent, board_path)`
  - `create_layout()`
  - `enable_left_panel_controls(enable: bool)`
  - `_on_render_complete()`
  - `_on_frame_rendered(frame_path)`

**Composition**:
- `ControlsSidePanel` (left)
- `PreviewPanel` (right)
- `StatusBar` (bottom)

**State Management**:
- `settings` - current RenderSettings
- `is_rendering` - flag to disable controls during render
- `rendered_frames` - list of frame file paths

---

### `preview_panel.py` (524 lines)
**Purpose**: Preview viewport with render playback overlay

**Key Classes**:
- `PreviewPanel` (wx.Panel)
  - `_create_viewport(board_path)`
  - `_create_overlay_widgets()`
  - `update_preview_overlay()` (preset/param metadata)
  - `start_playback(frames: list[str])`
  - `stop_playback()`
  - `on_playback_timer(event)`

**Components**:
- `GLPreviewRenderer` - OpenGL canvas
- `ov_top_left` - metadata (preset name or parameters)
- `ov_top_right` - render progress
- `ov_bottom` - frame counter / playback controls

---

### `controls_side_panel.py` (603 lines)
**Purpose**: Left sidebar with all rendering controls

**Key Classes**:
- `ControlsSidePanel` (wx.Panel)
  - `create_controls_panel(parent)`
  - `create_resolution_section()`
  - `create_lighting_section()`
  - `create_camera_section()`
  - `create_output_section()`
  - `_refresh_theme()` (hot-reload support)

**Custom Controls Used**:
- `CustomSlider` - with theme-aware tick marks
- `CustomToggleButton` - binary options
- `CustomButton` - action buttons
- `PresetCard` - preset thumbnail + name
- `CustomDropdown` - themed dropdown
- `CustomColorPicker` - color selection

**Hot-Reload**: `_hotload_map` tracks theme-dependent widgets for refresh

---

### `custom_controls.py` (1880 lines)
**Purpose**: Owner-drawn wx widgets with full theme integration

**Key Classes**:
- `CustomSlider` - slider with custom track, thumb, ticks
- `CustomToggleButton` - toggle switch animation
- `CustomButton` - button with hover/active states
- `PresetCard` - preset display card (image + label)
- `CustomDropdown` - dropdown with custom items
- `CustomColorPicker` - color well with popup picker
- `CustomListView` - virtual list for preset items
- `CustomListItem` - individual list item (delete button, icons)
- `ThumbnailCache` - LRU cache for preset images

**Theme Integration**:
Each control binds to `TextStyles` and theme tokens:
- `styles.normal.color` (text)
- `colors.primary` (accent)
- `layout.control.padding` (spacing)
- `icons.delete` (delete action icon)

---

### `preset_controller.py` (404 lines)
**Purpose**: Business logic for preset operations

**Key Classes**:
- `PresetController`
  - `__init__(preset_manager, main_panel)`
  - `save_preset(name, is_global)`
  - `recall_preset(name)`
  - `delete_preset(name)`
  - `list_available_presets() → dict[str, list[str]]`
  - `_generate_thumbnail(settings) → wx.Bitmap`

**Events**:
- `EVT_PRESET_SAVED` - emitted after save
- `EVT_PRESET_RECALLED` - emitted after recall
- `EVT_PRESET_DELETED` - emitted after delete

**Thumbnail Generation**:
Renders single frame at low resolution (200x150) for preset cards.

---

### `dialogs.py` (552 lines)
**Purpose**: Modal dialogs for user interactions

**Key Classes**:
- `RecallPresetDialog` (wx.Dialog)
  - `__init__(parent, preset_controller)`
  - `_build_ui()`
  - `get_selected_preset() → str`

- `AdvancedOptionsDialog` (wx.Dialog)
  - `__init__(parent, settings)`
  - `get_settings() → RenderSettings`

**Custom List View**:
Uses `CustomListView` + `CustomListItem` for preset selection with delete.

---

### `dependency_dialog.py` (370 lines)
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

**Installation**: Guides user to `pip install` with instructions.

---

### `parameter_controller.py` (200 lines)
**Purpose**: Bidirectional binding between UI controls and RenderSettings

**Key Classes**:
- `ParameterController`
  - `bind_control(control, setting_path: str, converter=None)`
  - `unbind_control(control)`
  - `update_settings_from_ui()`
  - `update_ui_from_settings()`

**Usage**:
```python
controller.bind(slider, "lighting.ambient", lambda v: v/100.0)
```

---

### `text_styles.py` (100 lines)
**Purpose**: Typography singleton (font family, size, weight)

**Key Classes**:
- `TextStyle` - named tuple (family, size, weight, color)
- `TextStyles` - class with static style attributes
  - `heading`, `subheading`, `body`, `caption`, `mono`
  - `info`, `warning`, `error`
- `TextStyles.initialize(theme)` - load from theme tokens

**Theme Tokens**:
- `typography.heading.family`
- `typography.body.size`
- `colors.text.primary`

**Methods**: ` TextStyle.create_font() → wx.Font`

---

### `helpers.py` (100 lines)
**Purpose**: UI utility functions

**Functions**:
- `create_section_label(parent, text, style_name) → wx.StaticText`
- `create_numeric_input(parent, label, initial, min, max) → (wx.StaticText, wx.SpinCtrl)`
- `create_button_row(parent, buttons: list[tuple[str, wx.Event]])`

---

### `validation.py` (250 lines)
**Purpose**: Theme validation utilities

**Key Functions**:
- `validate_theme_file(path) → ValidationReport`
- `validate_color_token(token_def) → bool`
- `validate_token_references(data, refs)`
- `check_circular_references(graph) → list[str]`

**Used By**: `test_validate_theme.py` for CI validation.
