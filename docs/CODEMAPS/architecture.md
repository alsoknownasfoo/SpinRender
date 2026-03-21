<!-- Generated: 2026-03-21 | Files scanned: 29 Python files | Token estimate: ~750 -->

# SpinRender Architecture

## Project Overview

**Type**: KiCad Action Plugin (wxPython GUI Application)
**Language**: Python 3.8+
**Purpose**: Generate animated PCB renders with camera loops and lighting presets
**Entry Point**: `SpinRender/spinrender_plugin.py` (SpinRenderPlugin class)

## System Structure

```
SpinRender/
├── spinrender_plugin.py    # KiCad plugin entry point
├── core/                   # Business logic & data models
│   ├── theme.py           # Singleton theme manager (YAML tokens)
│   ├── presets.py         # PresetManager (JSON presets)
│   ├── preview.py         # GLPreviewRenderer (OpenGL viewport)
│   ├── renderer.py        # Rendering engine (trimesh-based)
│   ├── locale.py          # Internationalization (i18n)
│   └── settings.py        # RenderSettings data class
├── ui/                    # wxPython UI components
│   ├── main_panel.py      # SpinRenderPanel (main frame)
│   ├── preview_panel.py   # PreviewPanel (viewport + overlays)
│   ├── controls_side_panel.py  # ControlsSidePanel (left sidebar)
│   ├── custom_controls.py # Custom wx widgets (sliders, buttons, etc.)
│   ├── dialogs.py         # RecallPresetDialog, AdvancedOptionsDialog
│   ├── dependency_dialog.py  # DependencyChecker UI
│   ├── preset_controller.py  # Preset load/save/delete logic
│   ├── parameter_controller.py  # Parameter ↔ UI binding
│   ├── text_styles.py     # TextStyle singleton (font management)
│   ├── validation.py      # Theme validation utilities
│   └── helpers.py         # UI helper functions
├── resources/
│   ├── themes/            # YAML theme files (dark.yaml, light.yaml)
│   ├── locale/            # Translation files (en.yaml, en_US.yaml)
│   ├── kicad_config/      # KiCad config JSONs (9.0/, 10.0/)
│   └── fonts/             # Variable fonts (JetBrainsMono, Oswald, MDI)
└── utils/
    └── logger.py          # SpinLogger initialization
```

## Plugin Lifecycle

```
1. KiCad loads plugin → pcbnew.ActionPluginRegistry()
2. Plugin defaults() called → metadata registration
3. User clicks toolbar button → SpinRenderPlugin.Run()
4. DependencyChecker.check_and_prompt() → validate wxPython, OpenGL, trimesh
5. If SpinRenderFrame.active_instance exists → Raise() (singleton pattern)
6. Else → Create SpinRenderFrame (main window)
7. Main window initialization:
   - Load Theme singleton from YAML
   - Load Locale singleton
   - Initialize RenderSettings
   - Build UI panels (Preview, Controls, Status Bar)
8. Event loop starts → user interaction
```

## UI Component Hierarchy

```
SpinRenderPanel (main_panel.py)
├── top_panel (wx.Panel) - main horizontal container
│   ├── ControlsSidePanel (controls_side_panel.py) [LEFT]
│   │   └── ScrolledPanel with controls:
│   │       ├── Header (preset info)
│   │       ├── Resolution sliders
│   │       ├── Lighting controls
│   │       ├── Camera settings
│   │       └── Output options
│   │
│   └── PreviewPanel (preview_panel.py) [RIGHT - expandable]
│       ├── GLPreviewRenderer (OpenGL viewport)
│       ├── Overlay widgets (top/bottom metadata)
│       └── Render preview overlay (playback controls)
│
├── status_bar (StatusBar) - bottom status messages
│
└── Dialogs (modal)
    ├── RecallPresetDialog (dialogs.py) - preset management
    ├── AdvancedOptionsDialog (dialogs.py) - advanced settings
    └── DependencyDialog (dependency_dialog.py) - installation UI
```

## Data Flow: Theme System

```
Theme.singleton
   ↓ load(name=theme_name) from resources/themes/{name}.yaml
   ↓ parse YAML into _data dict
   ↓
Theme.current().color("token.path") → wx.Colour
   ↓resolve references (var, function references)
   ↓apply transforms (darken, lighten, mix)
   ↓return computed color
```

**Theme Token Resolution**:
- Direct values: `colors.primary: #ff0000`
- Variable references: `ref: colors.primary`
- Function calls: `darken(colors.primary, 0.1)`
- Compositions: `mix(colors.bg, colors.fg, 0.5)`

## Data Flow: Preset System

```
PresetManager(board_path)
   ↓
Global: ~/.spinrender/presets/
Project: {board_dir}/.spinrender/
   ↓
save_preset(name, settings, is_global=False)
   ↓ serialize RenderSettings to JSON
   ↓ write {safe_name}.json
   ↓
load_preset(name) → RenderSettings
   ↓ read JSON
   ↓ deserialize to RenderSettings object
```

**Preset Categories**:
- Global presets (user home directory)
- Project presets (next to .kicad_pcb file)

## External Dependencies

| Library | Purpose | Version |
|---------|---------|---------|
| wxPython | GUI framework | ^4.0 |
| PyOpenGL | OpenGL bindings | >=3.1.0 |
| PyOpenGL-accelerate | Performance boost | >=3.1.0 |
| trimesh | 3D mesh loading/processing | >=4.0.0 |
| numpy | Numeric operations | >=1.24.0 |
| PyYAML | Theme & locale YAML parsing | >=6.0 |
| pyobjc-core (macOS) | macOS integrations | - |
| pyobjc-framework-Cocoa (macOS) | Cocoa bindings | - |

**KiCad Integration**:
- Import: `import pcbnew`
- Plugin type: `pcbnew.ActionPlugin`
- Registration: KiCad's plugin manifest system
- Configuration: `kicad.json`, `pcbnew.json` in resources/kicad_config/

## Key Configuration Files

```
SpinRender/resources/
├── themes/
│   ├── dark.yaml          # Complete dark theme token set
│   └── light.yaml         # Complete light theme token set
├── locale/
│   ├── en.yaml            # Base English strings
│   └── en_US.yaml         # US English variants
├── kicad_config/
│   ├── 10.0/              # KiCad 10.0 action configs (7 JSONs)
│   └── 9.0/               # KiCad 9.0 action configs (7 JSONs)
└── fonts/                  # 3 variable fonts for UI
```

## Test Coverage

- **Location**: `tests/unit/`
- **Count**: 24 test files
- **Coverage target**: 80%
- **Framework**: pytest with coverage reporting
- **Key test areas**:
  - Theme validation (`test_validate_theme.py`, `test_core_theme.py`)
  - UI theming (`test_*_theme.py`)
  - Panel tests (`test_preview_panel.py`, `test_main_panel_theme.py`)
  - Controls (`test_custom_controls_theme.py`, `test_controls_side_panel.py`)
  - Dialogs (`test_dialogs_theme.py`, `test_dependency_dialog.py`)
  - Locale (`test_locale.py`)

## Architecture Patterns

- **Singleton**: Theme, Locale, TextStyles (global state, one instance)
- **MVC-ish**: Settings (Model) ↔ ParameterController (Controller) ↔ CustomControls (View)
- **Lazy Loading**: OpenGL/trimesh imports deferred until after dependency check
- **Hot-Reload**: Theme changes tracked via `_hotload_map` in ControlsSidePanel
- **Singleton Frame**: Only one SpinRenderFrame allowed (Raise() if exists)
- **Custom Controls**: Owner-drawn wx widgets for fine-grained theme control

## Current Development Branch

`feat/theme-v2` - Theme system enhancements

Modified files (git status):
- `SpinRender/core/presets.py`
- `SpinRender/core/theme.py`
- `SpinRender/resources/locale/*.yaml`
- `SpinRender/resources/themes/dark.yaml`
- `SpinRender/ui/*.py` (multiple)
- `tests/unit/test_*.py` (multiple test updates)
