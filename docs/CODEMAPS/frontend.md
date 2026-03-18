<!-- Generated: 2026-03-18 | Files scanned: 13 | Token estimate: ~700 -->
# Frontend (UI) Architecture

## Entry Point
`ui/main_panel.py` → `SpinRenderPanel(wx.Panel)` — ~800 lines

## Component Hierarchy
```
SpinRenderFrame (wx.Frame)
└─ SpinRenderPanel (wx.Panel)
   ├─ ControlsSidePanel (wx.Panel, 450px fixed width)
   │  ├─ PresetSection (wx.Panel)
   │  │  └─ PresetCard[] (grid layout, 2 columns)
   │  ├─ ParametersSection (wx.Panel)
   │  │  ├─ board_tilt → CustomSlider + CustomInput (-90..90)
   │  │  ├─ board_roll → CustomSlider + CustomInput (-180..180)
   │  │  ├─ spin_tilt  → CustomSlider + CustomInput (-90..90)
   │  │  ├─ spin_heading → CustomSlider + CustomInput (0..180)
   │  │  ├─ period → CustomSlider (2..30s)
   │  │  └─ direction → CustomToggleButton (ccw|cw)
   │  ├─ LightingSection → CustomDropdown (studio|outdoor|warm|cool|none)
   │  ├─ OutputSection (wx.Panel)
   │  │  ├─ format → CustomDropdown (mp4|gif|png_sequence)
   │  │  ├─ resolution → CustomDropdown (720|1080|1440|2160)
   │  │  ├─ frame_rate → CustomDropdown (24|30|60)
   │  │  └─ bg_color → ColorPickerButton (#RRGGBB)
   │  ├─ AdvancedButton → opens OutputPathDialog
   │  ├─ RenderButton (primary) / CancelButton (danger)
   │  └─ StatusBar (bottom)
   └─ PreviewPanel (wx.Panel, remaining width)
      ├─ GLPreviewRenderer (wx.glcanvas.GLCanvas)
      │  └─ OpenGL context: board mesh, camera, lighting
      └─ OverlayPanel (floating)
         ├─ Playback controls (pause/resume)
         ├─ Progress bar
         └─ Frame counter
```

## Custom Controls (`custom_controls.py` — ~1800 lines)

| Class | Base | Purpose | Key Features |
|-------|------|---------|--------------|
| `CustomSlider` | wx.Panel | Range slider + input pair | live value display, min/max enforcement |
| `CustomToggleButton` | wx.Button | 2-state toggle | label switching (ccw/cw), visual state |
| `CustomDropdown` | wx.Panel | Styled selector | popup menu, icon support, theme-aware |
| `DropdownPopup` | wx.Frame | Dropdown menu | keyboard navigation, search filter |
| `CustomButton` | wx.Button | Primary/ghost/danger variants | theme colors, hover states |
| `PresetCard` | wx.Panel | Clickable preset tile | title, icon, delete button |
| `NumericDisplay` | wx.StaticText | Read-only number | monospace, theme text color |
| `NumericInput` | wx.TextCtrl | Validated number entry | range validation, step arrows |

### Control Styling
- All controls use `Theme` singleton for colors
- Fonts from `text_styles.py` (presets: `headline`, `body`, `caption`)
- Spacing: 4px base grid (2, 4, 8, 12, 16, 24, 32)
- Corner radius: 8px standard, 12px for cards

## Controllers (`ui/`)

| Controller | Lines | Responsibility |
|------------|-------|----------------|
| `parameter_controller.py` | ~400 | Validates UI inputs, updates `RenderSettings`, computes derived params |
| `preset_controller.py` | ~500 | Loads/saves presets, manages `PresetManager`, UI preset cards |
| `render_controller.py` (core) | ~180 | Background thread orchestration, progress callbacks |

### Parameter Flow
```
UI Control (CustomSlider)
   → on_change event
   → ParameterController.validate()
   → RenderSettings update
   → PresetController.mark_dirty()
   → update_preview() (debounced 200ms)
   → StatusBar update
```

## Preview System (`preview_panel.py` + `core/preview.py`)

### Modes
- **Wireframe** (default): Simple rotating box
- **Full 3D** (requires PyOpenGL/trimesh/numpy):
  - Loads GLB export from KiCad (running `kicad-cli pcb export glb`)
  - Real-time camera orbit with tilt
  - Camera lights: studio (3-point), outdoor, warm, cool

### Overlay Features
- Play/pause toggle for live preview rotation
- Progress bar during render
- Current frame / total frames
- Cancel button (interrupts render thread)

## State Management

### Current Settings
- Stored in `SpinRenderPanel.settings` (`RenderSettings` dataclass)
- Initialized from defaults, optionally merged with `PresetManager.get_last_used_settings()`
- Persisted to JSON via `PresetManager.save_preset()` or on app exit

### Render State
- `RenderController._is_rendering`, `_cancel_flag`
- Worker thread (`threading.Thread`, daemon=True)
- Callbacks: `on_progress(current, total, message, frame_path)`, `on_complete(result, error)`

### Theme
- `Theme.current()` singleton (from `core/theme.py`)
- Loaded from `resources/themes/dark.yaml` or hardcoded fallback
- Access: `_theme.color("colors.bg.primary")`, `font("body")`, `size("spacing.lg")`

## Layout Grid

### Spacing Scale (from theme)
- xs: 4px | sm: 8px | md: 12px | lg: 16px | xl: 24px | xxl: 32px

### Section Padding
- Sidebar: 16px horizontal, 12px vertical between sections
- Preview: 8px margin to frame edges

### Control Heights
- Slider row: 40px
- Dropdown: 36px
- Buttons: 44px (primary), 36px (secondary)
- Cards: 80px (preset), 64px (section headers)

## Color Usage (Theme tokens)
- `colors.bg.page` — main panel background
- `colors.bg.control` — control panel background
- `colors.bg.panel` — section panels
- `colors.border.default` — control borders
- `colors.text.primary` / `secondary` / `disabled` — text
- `colors.accent.primary` — primary button, slider thumb
- `colors.accent.danger` — cancel button

## Key Files
| File | Lines | Purpose |
|------|-------|---------|
| `ui/main_panel.py` | 800 | Panel setup, event wiring |
| `ui/custom_controls.py` | 1800 | Control implementations |
| `ui/controls_side_panel.py` | 650 | Controls container + layout |
| `ui/preview_panel.py` | 800 | GL canvas + overlay |
| `ui/dialogs.py` | 1000 | Advanced settings dialog |
| `ui/parameter_controller.py` | 400 | Parameter mutation logic |
| `ui/preset_controller.py` | 500 | Preset UI management |
| `ui/status_bar.py` | 200 | Progress indicator |
| `core/render_controller.py` | 180 | Thread orchestration |
| `core/renderer.py` | 650 | kicad-cli + ffmpeg pipeline |
| `core/settings.py` | 48 | RenderSettings dataclass |
