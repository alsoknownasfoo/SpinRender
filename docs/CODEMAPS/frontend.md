<!-- Generated: 2026-03-21 | Files scanned: 29 Python files | Token estimate: ~800 -->

# UI Component Hierarchy

## Application Shell

```
SpinRenderPanel (main_panel.py)
├── top_panel (wx.Panel) - main container [HORIZONTAL]
│   ├── ControlsSidePanel [LEFT ~400px, FIXED]
│   │   └── ScrolledPanel (vertical)
│   │       ├── Header: title + subtitle
│   │       ├── Preset Cards Row (horizontal)
│   │       │   ├── PresetCard (thumbnail + label)
│   │       │   ├── PresetCard
│   │       │   └── "+" Add button
│   │       │
│   │       ├── Section: Resolution
│   │       │   ├── Label "Resolution"
│   │       │   ├── CustomSlider (width: 320-4096)
│   │       │   ├── CustomSlider (height: 320-4096)
│   │       │   └── CustomDropdown (presets: 1080p, 4K, etc.)
│   │       │
│   │       ├── Section: Lighting
│   │       │   ├── Label "Lighting"
│   │       │   ├── CustomSlider (ambient: 0-100%)
│   │       │   ├── CustomSlider (diffuse: 0-100%)
│   │       │   ├── CustomSlider (specular: 0-100%)
│   │       │   └── CustomColorPicker (background)
│   │       │
│   │       ├── Section: Camera
│   │       │   ├── Label "Camera"
│   │       │   ├── CustomSlider (orbit speed)
│   │       │   ├── CustomSlider (elevation)
│   │       │   ├── CustomSlider (distance)
│   │       │   └── CustomToggleButton (auto-rotate preview)
│   │       │
│   │       └── Section: Output
│   │           ├── Label "Output"
│   │           ├── CustomSlider (FPS: 24-60)
│   │           ├── CustomSlider (duration: 3-30s)
│   │           ├── CustomDropdown (format: MP4, GIF)
│   │           └── CustomButton (render)
│   │
│   └── PreviewPanel [RIGHT, EXPAND]
│       ├── GLPreviewRenderer (OpenGL viewport)
│       │   └── Handles:
│       │       - Board loading (STEP/FCStd via trimesh)
│       │       - Camera orbit controls
│       │       - Lighting preview
│       │
│       ├── Overlay Top (transparent panel)
│       │   ├── ov_top_left (StaticText) - preset/params
│       │   └── ov_top_right (StaticText) - render progress
│       │
│       ├── Overlay Bottom (transparent panel)
│       │   ├── Play/Pause button (toggle)
│       │   ├── Progress bar (wx.Gauge or custom)
│       │   └── Frame counter (StaticText)
│       │
│       └── Overlay Render Preview (shown during render)
│           ├── Semi-transparent dark panel
│           ├── Preview frames (bitmap cycling)
│           ├── Progress percentage
│           └── Cancel button
│
├── status_bar (StatusBar)
│   ├── Field 1: "Ready" / "Rendering..."
│   └── Field 2: Resolution dims, board name
│
└── Modals (wx.Dialog)
    ├── RecallPresetDialog
    │   ├── CustomListView (preset names list)
    │   ├── Preview thumbnail (right panel)
    │   ├── Delete button (bottom)
    │   └── Load button (bottom)
    │
    ├── AdvancedOptionsDialog
    │   ├── Notebook / Tabs
    │   ├── Tab 1: Render (samples, denoise, etc.)
    │   ├── Tab 2: Material (colors, roughness)
    │   ├── Tab 3: Post-processing (bloom, gamma)
    │   └── OK / Cancel buttons
    │
    └── DependencyDialog (from DependencyChecker)
        ├── Status list (pass/fail icons)
        ├── Missing packages list
        ├── Install button
        └── Cancel / Help buttons
```

---

## Component Details

### ControlsSidePanel

**Role**: Left sidebar, all parameter inputs

**State**:
- `settings` (RenderSettings) - current config

**Construction Flow**:
```
create_controls_panel()
├── Setup scrolledpanel (400px width)
├── Set background from theme
├── create_header() → title + subtitle
├── create_preset_row() → preset cards + add button
├── create_resolution_section()
├── create_lighting_section()
├── create_camera_section()
├── create_output_section()
└── create_action_buttons() → [Render, Cancel]
```

**Hot-Reload**:
`reapply_theme()` calls `reapply_text_styles()` from `helpers.py`.
`reapply_text_styles()` iterates the global `_text_registry` (weak-refs to all
`wx.StaticText` widgets created via `create_text()`), re-resolves fonts, colors,
and `format_text()` output from the live theme, then prunes dead references.

---

### PreviewPanel

**Role**: Right panel, viewport + playback

**State**:
- `board_path` (str) - path to .kicad_pcb file
- `render_preview_active` (bool)
- `is_rendering` (bool)
- `playback_frames: list[str]` - file paths
- `playback_index` (int)
- `playback_timer` (wx.Timer)

**Viewport**:
- `GLPreviewRenderer` (subclass wx.GLCanvas)
- OpenGL context shared with renderer
- Renders board mesh (trimesh) in real-time (preview mode)

**Overlay System**:
- Top overlay: Absolute positioned panel over viewport
  - `ov_top_left`: Left-aligned (preset name or "W×H, FPS")
  - `ov_top_right`: Right-aligned (render progress: "Frame 12/60")
- Bottom overlay: Centered panel
  - Play/Pause button (SVG icon)
  - Progress bar (themed)
  - Frame counter ("12 / 60")

**Playback**:
```
Timer EVENT (every 1000/fps ms)
  → on_playback_timer()
    → Load next frame bitmap (wx.Bitmap)
    → Display in overlay (static bitmap)
    → Increment index
    → Loop or stop
```

**Render Preview Overlay**:
During full render:
- Hides normal controls (semi-transparent overlay)
- Shows live frames as they complete
- Progress percentage
- Cancel button (stops render)

---

### Custom Controls Architecture

All custom controls inherit from wx-native classes and override:
- `OnPaint()` - custom drawing
- `OnSize()` - layout updates
- `OnMouse*()` - interaction handling

**Theme Integration**:
Each control queries theme tokens:
```python
bg_color = _theme.color("colors.control.background")
text_color = _theme.color("colors.text.primary")
font = TextStyles.normal.create_font()
padding = _theme.token("layout.control.padding")
```

**Text Creation Rule**:
All `wx.StaticText` widgets must be created via `helpers.create_text(parent, label, style_name)`.
- `style_name` must map to a `layout.*` or `components.*` YAML path (via `TextStyles._ALIASES`).
- `style_name` should be an alias key (for example `dialog_link`, `leftpanel_description`) for create_text callsites, not a raw `layout.*` or `components.*` path.
- `create_text()` applies `format_text()` (e.g. uppercase from YAML), sets font+color, and
  registers the widget in the global `_text_registry` for automatic hot-reload.
- `prepare_styled_text()` may use direct component theme paths for paint-time rendering (for example `components.badge.label`).
- Never use bare `wx.StaticText(...)` + `SetFont()` for themed text.

---

## Event Flow: Render Trigger

```
User clicks "Render" button
  ↓ CustomButton → EVT_BUTTON
  ↓ ControlsSidePanel._on_render_click()
  ↓ main_panel.start_render()
  ↓
ParameterController.update_settings_from_ui()
  → Collect all control values
  → Update RenderSettings object
  ↓
main_panel.enable_left_panel_controls(False)
  → Disable all sliders/buttons
  ↓
core.renderer.render_animation(settings, board_path, progress_cb)
  ↓ per frame:
    progress_cb(frame_num, total, bitmap)
      → main_panel._on_frame_rendered(bitmap)
        → preview_panel.update_render_overlay(bitmap, frame_num)
  ↓
core.export_video(frames, output_path, fps)
  ↓
main_panel._on_render_complete()
  → enable_left_panel_controls(True)
  → status_bar.update("Render complete: output.mp4")
```

---

## Event Flow: Preset Management

```
PresetCard clicked
  ↓ EVT_LEFT_DOWN on custom control
  ↓ ControlsSidePanel._on_preset_card_click(preset_name)
  ↓ main_panel.recall_preset(name)
  ↓ PresetController.recall_preset(name)
    → load JSON → RenderSettings
    → update settings
  ↓ ParameterController.update_ui_from_settings()
    → Set all slider positions, color pickers, etc.
  ↓
PresetCard (Save) clicked
  ↓ main_panel.save_preset_dialog()
  ↓ RecallPresetDialog (modal)
    → User enters name
    → PresetController.save_preset(name, settings)
      → thumbnail = render_single_frame(settings)
      → write JSON + thumbnail.png
    → emit EVT_PRESET_SAVED
  ↓ ControlsSidePanel._refresh_preset_row()
    → rebuild preset cards list
```

---

## Theme Application Strategy

**At Startup**:
1. `Theme.load("dark")` reads YAML
2. `Locale.load("en")` reads YAML
3. `TextStyles.initialize(theme)` extracts font tokens
4. Panels constructed, all controls read theme tokens on init

**Hot-Reload** (if theme file modified on disk):
- `Theme.reload()` called
- `main_panel.refresh_theme()` called
- Recursively walks all controls
- For each control:
  - Reapply colors (foreground, background)
  - Reapply fonts (via TextStyles)
  - Redraw (`Refresh()`)

**Token Resolution Lazy**:
Theme doesn't pre-compute all tokens. Each `color()` call resolves on demand,
caching results in `_resolved_cache` (memoized per token path).

---

## Key Custom Controls

| Control | WX Base | Purpose | Theme Tokens Used |
|---------|---------|---------|-------------------|
| CustomSlider | wx.Slider | Ranged values with tick marks | `colors.slider.track`, `colors.slider.thumb`, `colors.slider.tick` |
| CustomToggleButton | wx.Panel (owner-drawn) | On/off switch animation | `colors.toggle.on`, `colors.toggle.off`, `colors.toggle.handle` |
| CustomButton | wx.Button (owner-drawn) | Actions | `colors.button.bg`, `colors.button.hover`, `colors.button.text` |
| PresetCard | wx.Panel | Preset thumbnail + label | `colors.card.bg`, `colors.card.border`, `typography.caption` |
| CustomDropdown | wx.ComboBox (custom popup) | Dropdown selection | `colors.dropdown.bg`, `colors.dropdown.item`, `colors.dropdown.hover` |
| CustomColorPicker | wx.Panel | Color selection with popup | `colors.picker.frame`, `colors.picker.preview` |
| CustomListView | wx.ListCtrl (virtual) | List of items | `colors.list.bg`, `colors.list.text`, `colors.list.hover` |
| CustomListItem | wx.Panel | Single list entry | `colors.item.bg`, `colors.item.delete` |
