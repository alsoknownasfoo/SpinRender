<!-- Generated: 2026-03-18 | Files scanned: 36 | Token estimate: ~800 -->
# SpinRender System Architecture

## Project Type
KiCad Action Plugin — animated PCB render generator with camera loops and lighting presets.

## Tech Stack
- Python 3.8+ | wxPython GUI | OpenGL preview (PyOpenGL)
- kicad-cli (frame rendering) | ffmpeg (video assembly)
- YAML-based theme system | JSON preset management

## System Overview
```
┌─────────────────────────────────────────────────────────────┐
│                      KiCad PCB Editor                        │
│                     (pcbnew.ActionPlugin)                   │
└──────────────────────────┬──────────────────────────────────┘
                           │ loads
                           ▼
              ┌─────────────────────────┐
              │  SpinRenderPlugin       │
              │  (spinrender_plugin.py) │
              └──────────┬──────────────┘
                         │ Run() → dependency check
                         ▼
              ┌─────────────────────────┐
              │  SpinRenderFrame        │
              │  (wx.Frame container)   │
              └──────────┬──────────────┘
                         │ hosts
                         ▼
              ┌─────────────────────────┐
              │  SpinRenderPanel        │
              │  (main_panel.py)        │
              │  ┌──────────────────┐   │
              │  │ ControlsSidePanel│   │◄───── PresetController
              │  │  (450px width)   │   │       ParameterController
              │  └──────────────────┘   │
              │  ┌──────────────────┐   │
              │  │ PreviewPanel     │   │◄───── GLPreviewRenderer
              │  │  (OpenGL canvas) │   │       RenderController
              │  └──────────────────┘   │
              └─────────────────────────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
        RenderEngine           PresetManager
        (renderer.py)          (presets.py)
              │
       ┌──────┴──────┐
       ▼              ▼
    kicad-cli     frame PNGs
       │              │
       └──────┬───────┘
              ▼
           ffmpeg
              │
       ┌──────┴──────┐
       ▼              ▼
    MP4 (H.264)   GIF   PNG sequence
```

## Module Structure

### Core (`SpinRender/core/`)
| File | Lines | Purpose |
|------|-------|---------|
| `theme.py` | ~900 | YAML-based theme singleton with fallback colors |
| `renderer.py` | ~650 | Frame generation via kicad-cli |
| `render_controller.py` | ~180 | Thread management for background rendering |
| `presets.py` | ~280 | Preset save/load (JSON, global + project) |
| `settings.py` | ~48 | RenderSettings dataclass with validation |
| `__init__.py` | ~10 | Package exports |

### UI (`SpinRender/ui/`)
| File | Lines | Purpose |
|------|-------|---------|
| `main_panel.py` | ~800 | Main panel layout, event orchestration |
| `custom_controls.py` | ~1800 | CustomSlider, CustomDropdown, PresetCard, etc. |
| `controls_side_panel.py` | ~650 | Left panel with all controls |
| `dialogs.py` | ~1000 | File dialogs, settings override dialog |
| `preview_panel.py` | ~800 | OpenGL preview canvas + overlay |
| `parameter_controller.py` | ~400 | Parameter validation & coordination |
| `preset_controller.py` | ~500 | Preset UI logic (load/save/apply) |
| `status_bar.py` | ~200 | Progress status display |
| `text_styles.py` | ~150 | Typography token definitions |
| `validation.py` | ~270 | WCAG contrast checking utilities |
| `helpers.py` | ~170 | Token resolution helpers |
| `dependencies.py` | ~210 | Dependency checker for KiCad/pip packages |
| `__init__.py` | ~5 | Package exports |

### Utils (`SpinRender/utils/`)
| File | Lines | Purpose |
|------|-------|---------|
| `logger.py` | ~150 | SpinLogger setup (wxPython-aware) |
| `__init__.py` | ~2 | Package exports |

### Foundation (`SpinRender/foundation/`)
| File | Lines | Purpose |
|------|-------|---------|
| `fonts.py` | ~120 | Font family constants from theme |
| `icons.py` | ~80 | Icon SVG loading utilities |
| `__init__.py` | ~2 | Package exports |

### Entry Points
- **Plugin registration**: `spinrender_plugin.py:SpinRenderPlugin` (pcbnew.ActionPlugin)
- **Main window**: `spinrender_plugin.py:SpinRenderFrame` (wx.Frame)
- **Primary panel**: `ui/main_panel.py:SpinRenderPanel` (wx.Panel)

## Data Flow

### Render Pipeline
1. User adjusts params → `ParameterController` updates `RenderSettings`
2. `RenderController.start_render()` spawns background thread
3. `RenderEngine.render()` generates frames:
   - Compute camera angles per frame using tilted-loop model
   - Call `kicad-cli pcb render` for each frame (PNG output)
4. `RenderEngine.assemble()` calls `ffmpeg` to create final video/GIF
5. Progress callbacks → `StatusBar` updates via `wx.CallAfter`

### Preset Management
- **Global presets**: `~/.spinrender/presets/*.json`
- **Project presets**: `<board_dir>/.spinrender/*.json`
- `PresetManager` handles I/O, `PresetController` handles UI

### Theme System
- **Primary**: `SpinRender/core/theme.py` — singleton `Theme` class
- **YAML source**: `SpinRender/resources/themes/*.yaml` (e.g., `dark.yaml`)
- **Fallback**: Hardcoded palette if PyYAML unavailable or file missing
- Access: `Theme.current().color("path")`, `font()`, `size()`

## External Dependencies

### Required (bundled with KiCad)
- Python 3.8+
- wxPython
- pcbnew (KiCad API)

### Optional (preview enhancement)
```
PyOpenGL>=3.1.0
PyOpenGL-accelerate>=3.1.0
trimesh>=4.0.0
numpy>=1.24.0
```

### System tools
- `kicad-cli` (KiCad 8+) — frame rendering
- `ffmpeg` — video/GIF assembly

### Python packages
- `PyYAML>=6.0` — theme loading (fallback to hardcoded if missing)

## Testing
- **16 test files** under `tests/` and `tests/unit/`
- Framework: pytest with coverage
- Requirement: 80%+ coverage
- Key test suites:
  - Theme validation (`test_core_theme.py`)
  - UI theme integration (`test_*_theme.py` files)
  - Component tests (`test_preview_panel.py`, `test_main_panel_theme.py`)
  - Comparator tests (`test_comparator.py`)

## Configuration Files
- `pyproject.toml` — project metadata, dependencies, pytest config
- `pytest.ini` — test discovery settings
- `resources/themes/dark.yaml` — active color/font/spacing tokens

## File Locations
```
SpinRender/
├── __init__.py (package metadata)
├── spinrender_plugin.py (KiCad entry point)
├── core/ (business logic, no GUI dependencies)
├── ui/ (wxPython components)
├── utils/ (logging, helpers)
├── foundation/ (fonts, icons)
└── resources/
    ├── fonts/ (Oswald, JetBrains Mono, MDI)
    ├── themes/dark.yaml
    └── icon.png, logo.svg
```
