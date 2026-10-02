# UI Component Hierarchy & State

**Last refreshed:** 2026-10-02

## Application Shell

```
SpinRenderFrame (wx.Frame, spinrender_plugin.py)
└── SpinRenderPanel (ui/main_panel.py)
    ├── top_container (horizontal)
    │   ├── ControlsSidePanel (ui/controls_side_panel.py)  [LEFT, fixed width]
    │   │   ├── Header: SVGLogoPanel · title · version · close CustomButton
    │   │   ├── ScrolledPanel
    │   │   │   ├── Presets: PresetCard ×4 (card1 Hero, card2 Spin, card3 Flip, card4 Select custom)
    │   │   │   ├── Parameters [collapsible: SectionToggle, "+ PRESET" save CustomButton]
    │   │   │   │   ├── Rotation: 4 axis rows, each icon + CustomSlider + numeric CustomInput
    │   │   │   │   │     board_tilt ±90 · board_roll ±180 · spin_tilt ±90 · spin_heading ±180
    │   │   │   │   ├── Rotation period: CustomSlider + input (0.1–30 s) + frame-count readout
    │   │   │   │   ├── Direction: CustomToggleButton (CCW / CW)
    │   │   │   │   ├── Zoom: CustomSlider + input (0.1–5.0x)
    │   │   │   │   └── Lighting: CustomToggleButton (Studio / Dramatic / Soft / Workspace)
    │   │   │   └── Output [collapsible]
    │   │   │       ├── Format: CustomDropdown (MP4 (H.264) / GIF / PNG Sequence)
    │   │   │       ├── Resolution: CustomDropdown (BUILTIN_RESOLUTIONS + custom) + ⚙ CustomButton
    │   │   │       ├── Background color: CustomColorPicker
    │   │   │       └── Board options: CustomCheckbox ×3 (vias, components, test points)
    │   │   └── Footer: ⚙ advanced options · about · exit/cancel · RENDER (CustomButton)
    │   └── PreviewPanel (ui/preview_panel.py)  [RIGHT, expands]
    │       ├── top bar: ov_top_left (preset name or parameters) · render-mode nav [ SHADED | WIREFRAME | BOTH ] · ov_top_right (close render result)
    │       ├── viewport_container
    │       │   ├── GLPreviewRenderer (core/preview.py)  — live OpenGL preview; mouse wheel zooms
    │       │   └── render_preview_panel  — overlays the viewport with render frames / result
    │       └── bottom bar: ov_bottom_left · ov_bottom_center · ov_bottom_right
    └── StatusBar (ui/status_bar.py) — message + progress, color-coded states
```

Dialogs (all `BaseStyledDialog`, `ui/dialogs.py`): Advanced Options (output location,
CLI overrides, logging, theme), Save Preset, Recall Preset, Custom Resolutions / Add Resolution,
PNG filename entry, About (with self-update), and `show_message()` for alerts.
`DependencyDialog` (`ui/dependency_dialog.py`) styles itself because it can run before
`Theme` is usable.

## State Management

### Settings flow
```
control event
  → ParameterController.on_<param>()           ui/parameter_controller.py
      → settings.<param> = value                 (RenderSettings, shared instance)
      → paired slider/input .SetValue()
      → PreviewPanel / GLPreviewRenderer setter → Refresh
      → PresetController.check_preset_match(manual_change=True)
      → SpinRenderPanel.schedule_save()          (500 ms debounce → last_used.json)
```
Applying a preset goes the other way: `PresetController.apply_preset_data()` writes the preset
into `settings`, updates every control and the viewport, then re-runs `check_preset_match`.

### ControlRegistry (`ui/registry.py`)
Controls register with a section (`'presets' | 'parameters' | 'output' | 'footer'`).
`SpinRenderPanel.enable_parameter_controls(False)` disables the presets, parameters and output
sections during a render; the footer stays live so STOP can cancel it.

### EVT_PARAMETER_INTERACTION (`ui/events.py`)
Enabled parameter controls emit it; `SpinRenderPanel.on_parameter_interaction` →
`reset_status_bar()`, which also closes a displayed render result. Mouse-wheel zoom does the
same via `SpinRenderPanel._on_viewport_zoom` (and `_on_render_preview_wheel` when the result
overlay has focus); wheel zoom is ignored while rendering.

## Render UI lifecycle
1. **RENDER** → `on_render`: prepare the working copy, disable controls, turn RENDER into a
   wide STOP button, hide exit/options.
2. Each frame → `on_render_progress`: status bar progress; the latest frame is drawn into
   `render_preview_panel` over the viewport.
3. Done → `on_render_finished`: re-enable controls, show the result and loop the frames
   (`PreviewPanel.start_playback`, ~30 fps). Close button or any parameter change dismisses it.

## Theming
- `Theme.current()` resolves tokens from `resources/themes/<dark|light>.yaml`; `theme_mode`
  `'system'` follows the OS appearance (`_detect_system_theme`).
- Custom controls paint themselves from tokens; text uses semantic `TextStyles`
  (`create_text(parent, text, "subheader" | "description" | "info" | ...)`).
- On a theme change, `reapply_theme()` cascades through the panels and re-applies text styles.
- Theme YAML edits hot-reload while the window is open (1 s mtime poll).

## Custom controls (`ui/custom_controls.py`)
Self-painted `wx.Panel` subclasses so they look identical on macOS, Windows and Linux.
Most implement `AcceptsFocus*() → False` to avoid native focus rings, and expose
wx-like accessors (`GetValue` / `SetValue`, `GetSelection` / `SetSelection`).

| Control | Used for |
|---|---|
| `CustomSlider` | axis angles, period, zoom |
| `CustomInput` | numeric inputs next to sliders, path/text fields |
| `CustomToggleButton` | direction, lighting |
| `CustomDropdown` | format, resolution |
| `CustomCheckbox` | board options |
| `CustomColorPicker` | background color |
| `PresetCard` | preset row |
| `CustomButton` | header/footer/action buttons |
| `SectionToggle`, `SectionLabel` | collapsible section headers |
| `CustomListView` / `CustomListItem` | preset recall, custom resolutions lists |
