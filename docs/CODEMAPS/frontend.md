# UI Component Hierarchy & State Management

<!-- Generated: 2026-03-25 | Files scanned: 30 Python modules | Token estimate: ~700 -->

## Application Shell

```
SpinRenderPanel (main_panel.py:672)
├── top_container (wx.Panel) - main horizontal container
│   ├── ControlsSidePanel (controls_side_panel.py:607) [LEFT, 450px FIXED]
│   │   ├── Header (title + subtitle)
│   │   │   ├── StaticText (title)
│   │   │   └── StaticText (subtitle)
│   │   │
│   │   ├── Preset Row (horizontal boxsizer)
│   │   │   ├── PresetCard (preset-hero)
│   │   │   ├── PresetCard (preset-spin)
│   │   │   ├── PresetCard (preset-flip)
│   │   │   ├── PresetCard (preset-custom)
│   │   │   └── CustomButton (add preset)
│   │   │
│   │   ├── Section: Resolution (subheader label)
│   │   │   ├── CustomSlider (width: 320-4096)
│   │   │   ├── CustomSlider (height: 320-4096)
│   │   │   └── CustomDropdown (presets: 1080p, 4K, etc.)
│   │   │
│   │   ├── Section: Lighting (subheader label)
│   │   │   ├── CustomSlider (ambient: 0-100%)
│   │   │   ├── CustomSlider (diffuse: 0-100%)
│   │   │   ├── CustomSlider (specular: 0-100%)
│   │   │   └── CustomColorPicker (background)
│   │   │
│   │   ├── Section: Camera (subheader label)
│   │   │   ├── CustomSlider (board_tilt: -90° to +90°)
│   │   │   ├── CustomSlider (board_roll: -180° to +180°)
│   │   │   ├── CustomSlider (spin_tilt: 0-360°)
│   │   │   └── CustomSlider (spin_heading: 0-360°)
│   │   │
│   │   ├── Section: Output (subheader label)
│   │   │   ├── CustomDropdown (format: mp4, gif)
│   │   │   ├── CustomSlider (fps: 24-60)
│   │   │   ├── CustomSlider (period: 3-30s)
│   │   │   └── ToggleButton row: DIRECTION (ccw/cw)
│   │   │       └── ToggleButton row: LIGHTING (studio/custom)
│   │   │
│   │   └── Section: Advanced (subheader label)
│   │       ├── CustomButton (options)
│   │       └── CustomButton (cancel/close)
│   │
│   └── PreviewPanel (preview_panel.py:488) [RIGHT, EXPAND to fill]
│       ├── GLPreviewRenderer (OpenGL canvas, from core.preview)
│       │   ├── Board mesh loading (trimesh)
│       │   ├── Camera orbit controls (mouse drag)
│       │   ├── Lighting preview (real-time)
│       │   └── Render mode: wireframe/shaded/both
│       │
│       ├── Overlay Top (transparent panel over viewport)
│       │   ├── ov_top_left (StaticText) - preset name OR param summary
│       │   └── ov_top_right (StaticText) - render progress "Frame N/M"
│       │
│       ├── Overlay Bottom (transparent panel, centered)
│       │   ├── Play/Pause button (toggle, icon only)
│       │   ├── Progress bar (wx.Gauge or custom drawn)
│       │   └── Frame counter "N / M"
│       │
│       └── Overlay Render Preview (shown during render)
│           ├── Semi-transparent dark panel (covers viewport)
│           ├── Preview frames (bitmap cycling, latest frame)
│           ├── Progress percentage (large text)
│           └── Cancel button (stops render)
│
├── status_divider (wx.Panel, height=1px) - divider line
│   └── Color: theme.colors.dividers.default
│
├── StatusBar (status_bar.py)
│   ├── Field 1: Status message (left-aligned)
│   │   - "Ready" (green)
│   │   - "Preparing render..." (cyan)
│   │   - "Rendering frame X/Y" (cyan, with progress bar)
│   │   - "Render complete" (green)
│   │   - "Error: <msg>" (red)
│   └── Field 2: Resolution dims + board filename (right-aligned)
│
└── Modals (wx.Dialog, shown on demand)
    ├── RecallPresetDialog
    │   ├── Splitter window
    │   │   ├── LEFT: CustomListView (preset names)
    │   │   └── RIGHT: Preview thumbnail (bitmap) + preset info
    │   ├── CustomButton (Load)
    │   ├── CustomButton (Delete)
    │   └── CustomButton (Cancel)
    │
    ├── SavePresetDialog
    │   ├── TextCtrl (preset name)
    │   ├── Preview thumbnail (auto-generated)
    │   ├── CustomButton (Save)
    │   └── CustomButton (Cancel)
    │
    ├── AdvancedOptionsDialog
    │   ├── Notebook (tabs)
    │   │   ├── Tab "Render" - samples, denoise, motion blur
    │   │   ├── Tab "Material" - PCB colors, roughness
    │   │   └── Tab "Post" - bloom, gamma, exposure
    │   ├── Theme Mode toggle: [Dark ○ Light ○ System]
    │   ├── CustomButton (OK)
    │   └── CustomButton (Cancel)
    │
    ├── AboutDialog
    │   ├── Logo (wx.StaticBitmap)
    │   ├── Version badge (CustomButton style)
    │   ├── License tagline
    │   ├── Gift icon + "Free for personal use" (mdi-gift)
    │   ├── Link labels: GitHub, Issues, README, Ko-fi, etc.
    │   └── CustomButton (Close)
    │
    └── DependencyDialog
        ├── Header icon + title
        ├── Status list (checkmark/cross for each dep)
        ├── Missing packages list (if any)
        ├── CustomButton (Install) - runs pip in subprocess
        └── CustomButton (Cancel)
```

---

## Component Details

### ControlsSidePanel

**Role**: Left sidebar, all parameter inputs (607 lines)

**State**:
- `settings` (RenderSettings) - current config reference
- `_registry` (ControlRegistry) - all UI controls with metadata
- `_hotload_map` (dict) - theme-dependent widgets for fast refresh

**Construction Flow**:
```
create_controls_panel()
├── Setup ScrolledPanel (450px width, vertical sizer)
├── Set background from theme (layout.main.leftpanel.bg)
├── create_header() → title + subtitle (uppercase)
├── create_preset_row() → 4 PresetCard + add button
├── create_resolution_section()
│   ├── create_subheader("Resolution")
│   ├── CustomSlider (width)
│   ├── CustomSlider (height)
│   └── CustomDropdown (1080p, 4K, custom)
├── create_lighting_section()
│   ├── create_subheader("Lighting")
│   ├── CustomSlider (ambient)
│   ├── CustomSlider (diffuse)
│   ├── CustomSlider (specular)
│   └── CustomColorPicker (background)
├── create_camera_section()
│   ├── create_subheader("Camera")
│   ├── CustomSlider (board tilt)
│   ├── CustomSlider (board roll)
│   ├── CustomSlider (spin tilt)
│   └── CustomSlider (spin heading)
├── create_output_section()
│   ├── create_subheader("Output")
│   ├── CustomDropdown (format)
│   ├── CustomSlider (fps)
│   ├── CustomSlider (period)
│   ├── CustomToggleButton (direction: ccw/cw)
│   ├── CustomToggleButton (lighting: studio/custom)
│   └── CustomButton (render)
├── create_action_buttons()
│   ├── CustomButton (cancel)
│   ├── CustomButton (options)
│   └── CustomButton (about)
└── Bind(EVT_SIZE, _on_size) for responsive layout
```

**Hot-Reload**:
`reapply_theme()` calls:
1. `reapply_text_styles()` - iterates global `_text_registry` (weakrefs to all `wx.StaticText`)
2. For each control in `_hotload_map`: `control.reapply_theme()`
3. `self.Refresh()` - trigger repaint

**Control Registration**:
Every control added to `_registry` with section='presets'|'parameters'|'output' for batch enable/disable.

---

### PreviewPanel

**Role**: Right panel, viewport + playback (488 lines)

**State**:
- `board_path` (str) - path to .kicad_pcb file
- `viewport` (GLPreviewRenderer) - OpenGL canvas
- `render_preview_active` (bool) - showing render preview overlay
- `is_rendering` (bool) - render in progress
- `playback_frames: list[str]` - file paths for animation
- `playback_index` (int) - current frame
- `playback_timer` (wx.Timer) - animation timer
- `render_preview_bitmap` (wx.Bitmap) - latest rendered frame
- `current_render_frame`, `total_render_frames` - progress tracking

**Viewport Creation**:
```
_create_viewport(board_path)
├── Create wx.Panel with background from theme
├── Instantiate GLPreviewRenderer (wx.GLCanvas)
│   ├── Load board: pcbnew.GetBoard() → STEP files → trimesh
│   ├── Build trimesh.Scene
│   └── Set up OpenGL shaders (via core/preview.py)
├── Bind mouse events (drag to rotate)
└── Bind EVT_PAINT → on_paint()
```

**Overlay System**:
All overlay widgets are `wx.StaticText` or `wx.Panel` positioned absolutely over the viewport using `SetPosition()`. They are children of `PreviewPanel`, not the GL canvas, so they paint on top.

- **Top overlay** (above viewport):
  - `ov_top_left`: Shows preset name OR camera parameters (tilt/roll)
  - `ov_top_right`: Shows render progress "Frame 12/60" during render

- **Bottom overlay** (below viewport, centered):
  - Play/Pause button (toggle playback)
  - Progress bar (themed)
  - Frame counter "12 / 60"

- **Render preview overlay** (during full render):
  - Semi-transparent dark panel covering viewport
  - Shows latest rendered frame bitmap
  - Progress percentage text
  - Cancel button (top-right corner)

**Playback**:
```
Timer EVENT (every 1000/fps ms)
  → on_playback_timer()
    → Load next frame bitmap from PNG file
    → Display in ov_bottom center (or overlay)
    → Increment index (loop or stop)
```

---

### Custom Controls Architecture

All custom controls inherit from wx-native classes and override:
- `OnPaint()` - custom drawing
- `OnSize()` - layout updates
- `OnMouse*()` - interaction handling

**Common Base**: Most inherit from `wx.Panel` (owner-drawn) or subclass wx control (Slider, Button).

**Theme Integration Pattern**:
```python
class CustomButton(wx.Panel):
    def __init__(self, parent, label, icon=None, style="default"):
        self._style = style
        self._hovered = False
        self._pressed = False
        # Theme tokens resolved on init and hot-reload
        self._apply_theme()

    def reapply_theme(self):
        self._apply_theme()
        self.Refresh()

    def _apply_theme(self):
        theme = Theme.current()
        # Resolve tokens
        self.bg_colors = theme.color_states(f"components.button.{self._style}.frame.bg")
        self.text_color = theme.color(f"components.button.{self._style}.label.color")
        self.font = theme.font(f"components.button.{self._style}.label.font")
        self.border = theme.border(f"components.button.{self._style}.border")
```

**Hot-Reload Support**:
All custom controls implement `reapply_theme()` method (no-op for simple ones, full update for complex).

**Text Creation Rule**:
All `wx.StaticText` widgets must be created via `helpers.create_text(parent, label, style_name)`.
- `style_name` must map to a `layout.*` or `components.*` YAML path (via `TextStyles._ALIASES`).
- `create_text()` applies `format_text()` (e.g. uppercase from YAML), sets font+color, and registers the widget in global `_text_registry` for automatic hot-reload.
- Never use bare `wx.StaticText(...)` + `SetFont()` for themed text.

---

## State Management

### Settings Flow (RenderSettings)

```
┌─────────────────────────────────────────────────────────┐
│              RenderSettings (dataclass)                 │
│  board_tilt, board_roll, spin_tilt, spin_heading       │
│  period, easing, direction, lighting                   │
│  format, resolution, bg_color, output_auto, output_path│
│  render_mode, logging_level, theme_mode, cli_overrides │
└─────────────────────────────────────────────────────────┘
         ▲                    ▲                    ▲
         │                    │                    │
    ParameterController   PresetController   main_panel
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                    save_settings() → PresetManager
```

**Lifecycle**:
1. `main_panel.__init__()` creates default `RenderSettings`
2. `PresetManager.get_last_used_settings()` loads saved values (if any)
3. `ParameterController.bind_control()` connects UI controls to fields
4. User interaction → `ParameterController.update_settings_from_ui()` → updates `settings`
5. Debounced `schedule_save()` (500ms) → `PresetManager.save_last_used_settings()`
6. On render: `RenderController.start_render(settings, ...)`

**Presets**:
- `PresetController` manages named presets (global or project)
- `PresetManager` handles file I/O (JSON)
- Thumbnail generation: `render_single_frame()` at 200×150

---

### ControlRegistry

**Purpose**: Track UI controls for bulk operations (enable/disable during render).

**Pattern**:
```python
class ControlRegistry:
    def __init__(self):
        self._entries = []  # list of dicts: {control, section, metadata}

    def add(self, control, section='general', **meta):
        self._entries.append({'control': control, 'section': section, **meta})

    def controls(self, section=None):
        if section:
            return [e['control'] for e in self._entries if e['section'] == section]
        return [e['control'] for e in self._entries]
```

**Usage in ControlsSidePanel**:
```python
self._registry = ControlRegistry()
# Build UI, adding controls with:
self._registry.add(slider, section='parameters')
self._registry.add(button, section='output')
```

**Usage in main_panel**:
```python
def enable_parameter_controls(self, enable=True):
    for ctrl in self.controls_side_panel._registry.controls(
            section='presets') + \
            self.controls_side_panel._registry.controls(section='parameters'):
        ctrl.Enable(enable)
# Output section (render/options/cancel) remains enabled
```

---

## Event Flow: Render Trigger

```
User clicks "Render" button (CustomButton)
  ↓ EVT_LEFT_DOWN
  ↓ ControlsSidePanel._on_render_click() (bound in main_panel)
  ↓ main_panel.on_render()
  ├─ ParameterController.update_settings_from_ui()
  │   → Collect all control values
  │   → Update main_panel.settings object
  ├─ main_panel.enable_parameter_controls(False)
  │   → Disable all sliders/buttons in registry (presets, parameters)
  │   → Hide cancel, options buttons
  ├─ status_bar.set_status("Preparing render...", progress=0)
  ├─ preview.stop_playback()
  ├─ preview.render_preview_active = True
  ├─ preview.render_preview_bitmap = None
  ├─ RenderController.start_render(board_path, settings,
  │                               progress_cb, complete_cb)
  │   └─ subprocess.Popen([blender, ...])
  │
  ├─ Background: Blender renders frames to temp folder
  │
  └─ Progress callback (called from render thread)
      ↓ RenderController → wx.CallAfter → main_panel._update_progress_ui
      ├─ status_bar.set_status(message, progress=current/total)
      ├─ preview.current_render_frame = current
      ├─ preview.total_render_frames = total
      ├─ Load frame bitmap from PNG → preview.render_preview_bitmap
      └─ preview.update_preview_overlay() - show preview panel
      │
      └─ Completion callback
          ↓ main_panel.on_render_finished()
          ├─ enable_parameter_controls(True) - re-enable controls
          ├─ status_bar.set_complete()
          ├─ preview.start_playback(frame_dir) - loop rendered frames
          ├─ Open output folder in file manager
          └─ Message box (success or error)
```

---

## Theme Application Strategy

**At Startup**:
1. `Theme.load(mode)` → parse YAML → `Theme._instance`
2. `Locale.load("en_US")` → parse YAML → `Locale._instance`
3. `TextStyles.initialize(theme)` extracts font tokens
4. Panels constructed; all controls read theme tokens on `__init__`

**Hot-Reload** (if theme/locale file modified on disk):
- `SpinRenderFrame.on_theme_watch_timer()` checks mtime every 1s
- If changed:
  - `Theme.reload()` (re-parse YAML)
  - `panel.reapply_theme()` (recursive update)
    - Update panel backgrounds (`SetBackgroundColour`)
    - `reapply_text_styles()` - iterate `_text_registry`, re-apply fonts/colors
    - `controls_side_panel.reapply_theme()` - update each control
    - `preview_panel.reapply_theme()` - update viewport if needed
    - `Refresh()` all affected windows

**Token Resolution**:
- Lazy: Each `Theme.color("path")` resolves on demand
- Cached: `_resolved_cache` memoizes results per call
- Invalidation: Cache cleared on `Theme.reload()`

**Dynamic Color States**:
Controls query `Theme.color_states(token)` for [normal, hover, active, disabled] palettes.

---

## Key Custom Controls

| Control | Base Class | Lines | Purpose | Theme Tokens Used |
|---------|------------|-------|---------|-------------------|
| CustomSlider | wx.Panel | 363 | Ranged values with ticks | `colors.slider.*`, `borders.*`, `typography.scale` |
| CustomToggleButton | wx.Panel | 206 | On/off switch animation | `colors.toggle.*`, `borders.*` |
| CustomButton | wx.Panel | 192 | Action buttons | `colors.button.*`, `text.button.*` |
| CustomDropdown | wx.Panel | 192 | Dropdown selection | `colors.dropdown.*`, `layout.control.*` |
| CustomColorPicker | wx.Panel | 162 | Color picker with popup | `colors.picker.*` |
| PresetCard | wx.Panel | 148 | Preset thumbnail + label | `components.preset_card.*` |
| CustomColorPicker | wx.Panel | 162 | Color selection with popup | `colors.picker.*` |
| CustomListView | wx.Panel | 177 | Virtual list (presets) | `components.list.*` |
| CustomListItem | wx.Panel | 129 | List entry with delete | `components.list.default.*` |

---

## Responsive Layout

**Width Constraints**:
- Controls panel: fixed 450px (`SetMinSize((450, -1))`)
- Center divider: 1px
- Preview panel: minimum 700px (`SetMinSize((700, -1))`)
- Frame minimum width: 1120px (enforced in `_finalize_init()`)

**Height**:
- Frame uses `Fit()` then `Centre()`
- Min height computed from sizer `CalcMin()`

**Scrolling**:
ControlsSidePanel wraps a `wx.ScrolledWindow` (virtual size ~1200px) so content scrolls if taller than window.

---

## Accessibility Considerations

- **Keyboard navigation**: All controls support TAB focus traversal
- **High contrast**: Theme tokens must have sufficient contrast ratios
- **Font scaling**: Text sizes from YAML scale; user can change via theme
- **Colorblind support**: State colors use both color and position (toggle switch)
- **Screen readers**: wxPython accessibility APIs used (minimal implementation)
