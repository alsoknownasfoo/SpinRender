# SpinRender Architecture

<!-- Generated: 2026-03-25 | Files scanned: 30 Python modules | Token estimate: ~600 -->

## Project Type

**KiCad 8/10 Action Plugin** — Desktop GUI application for generating animated PCB renders.

**Tech Stack**:
- Python 3 (KiCad's embedded Python)
- wxPython 6 (GUI framework)
- PyYAML (theme/locale configuration)
- trimesh + OpenGL (3D rendering)
- subprocess (external Blender communication)

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    KiCad 8/10 (pcbnew)                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  SpinRenderPlugin (spinrender_plugin.py)             │  │
│  │  - Registers as ActionPlugin                         │  │
│  │  - Creates SpinRenderFrame on Run()                  │  │
│  │  - Theme/Locale hot-reload watcher                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              SpinRender Package (Pure Python)              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ui/ (15 modules)                                     │  │
│  │  • main_panel.py — Root container                   │  │
│  │  • controls_side_panel.py — Parameter controls      │  │
│  │  • preview_panel.py — 3D viewport                   │  │
│  │  • dialogs.py — Modal dialogs (options, presets)    │  │
│  │  • custom_controls.py — Themed wx controls (1629l)  │  │
│  │  • status_bar.py — Render progress                  │  │
│  │  • registry.py — Control registry for bulk ops      │  │
│  │  • events.py — Custom wx events                      │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  core/ (7 modules)                                    │  │
│  │  • theme.py — YAML design token singleton (532l)    │  │
│  │  • locale.py — YAML localization singleton (170l)   │  │
│  │  • settings.py — RenderSettings dataclass           │  │
│  │  • presets.py — PresetManager (JSON persistence)    │  │
│  │  • render_controller.py — Async render orchestration│  │
│  │  • renderer.py — Blender CLI wrapper (605l)         │  │
│  │  • preview.py — OpenGL viewport rendering (884l)    │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  foundation/ (2 modules)                              │  │
│  │  • fonts.py — Font family loading                   │  │
│  │  • icons.py — Icon font/glyph resolution            │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  utils/ (2 modules)                                   │  │
│  │  • logger.py — SpinLogger singleton                 │  │
│  │  • check_dependencies.py — Dependency checker (289l)│  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              External Dependencies                         │
│  • Blender (CLI) — Actual 3D rendering engine            │
│  • wxPython 6 — GUI widgets (bundled in KiCad)           │
│  • PyYAML — Config parsing                               │
│  • trimesh + PyOpenGL — 3D viewport                      │
└─────────────────────────────────────────────────────────────┘
```

## Key Data Flows

### 1. Startup Flow
```
SpinRenderPlugin.Run()
  ├─ DependencyChecker.check_and_prompt()  (wxPython, PyYAML, Blender)
  ├─ pcbnew.GetBoard()                     (KiCad API)
  ├─ SpinRenderFrame(parent, board_path)
  │     └─ SpinRenderPanel(board_path)
  │           ├─ Load RenderSettings
  │           ├─ Theme.load(mode)              (YAML → Theme singleton)
  │           ├─ Locale.load("en_US")          (YAML → Locale singleton)
  │           └─ build_ui()
  └─ frame.Show()
```

### 2. Render Flow
```
User clicks RENDER button
  ├─ RenderController.start_render()
  │     ├─ Generate camera path from settings
  │     ├─ Build Blender CLI command
  │     └─ subprocess.Popen([blender, ...])
  │
  ├─ Background process:
  │     Blender renders frames → output folder
  │
  ├─ Progress callback (_update_progress_ui):
  │     ├─ StatusBar.set_status(message, progress)
  │     └─ PreviewPanel shows latest frame (bitmap)
  │
  └─ Completion callback (on_render_finished):
        ├─ StatusBar.set_complete()
        ├─ PreviewPanel.start_playback(frame_dir)
        └─ Open output folder in file manager
```

### 3. Theme Hot-Reload
```
Timer thread (1s interval) in SpinRenderFrame
  └─ Check theme YAML mtime
      └─ If changed:
            Theme.reload()
            panel.reapply_theme()
                  ├─ Update all wx.Colour lookups
                  ├─ Refresh dividers, panels, buttons
                  └─ Recursive Refresh() calls
```

## Extension Points

### Adding New Controls
1. **Define in `ui/controls_side_panel.py`**:
   - Add widget to `build_*_section()` method
   - Store reference in `self._registry.add(ctrl)`
   - Expose via `self.<name>_ctl` attribute

2. **Bind in `ui/main_panel.py`**:
   - Add to `param_controls` dict in `_init_preset_controller()`
   - Bind event to `ParameterController` handler

3. **Preset integration**:
   - Add field to `RenderSettings` dataclass
   - Update `PresetController` to read/write field

### Adding New Themes
1. Copy `resources/themes/dark.yaml` to `light.yaml` or create new
2. Edit design tokens (colors, radius, typography)
3. Theme auto-discovered by filename: `Theme.load("name")`

### Adding New Locales
1. Copy `resources/locale/en_US.yaml` to `de_DE.yaml`, etc.
2. Translate all `locale.<lang>` subtree values
3. Locale auto-discovered: `Locale.load("de_DE")`

## File Organization Rationale

**`ui/`** — All wx.Panel subclasses and dialog windows
- Self-contained widget styling via `Theme.color()`
- Event handling and layout grid

**`core/`** — Business logic, no wx dependencies
- Singleton managers (Theme, Locale)
- Settings and presets persistence
- Render orchestration (subprocess)
- OpenGL viewport rendering

**`foundation/`** — Asset abstractions
- Font family resolution from YAML
- Glyph/icon mapping from font chars

**`resources/`** — Static assets
- `themes/*.yaml` — Design token definitions
- `locale/*.yaml` — UI text translations
- `fonts/` — TTF files (JetBrains Mono, Oswald, MDI)
- `kicad_config/` — KiCad 9.0/10.0 JSON configs
- `icons/` — SVG logos

**`utils/`** — Cross-cutting utilities
- `logger.py` — Centralized logging setup
- `check_dependencies.py` — Dependency validation

## Design Patterns

- **Singleton**: Theme, Locale, SpinLogger (one instance per process)
- **Observer (implicit)**: Theme hot-reload via timer polling → panel.reapply_theme()
- **Controller**: RenderController separates rendering logic from UI
- **MVC-ish**: Settings (model) → UI controls (view) → ParameterController (controller)
- **Factory**: `CustomButton`, `CustomSlider` create themed controls
- **Registry**: `ControlRegistry` tracks UI controls for bulk enable/disable
- **Hot-Reload**: Theme/Locale file watchers update UI in-place

## Performance Considerations

- **Theme lookups**: O(log N) deep path resolution with `_resolved_cache` memoization
- **Hot-reload**: File mtime check every 1s; full re-theme ~10ms for 40 controls
- **Rendering**: Non-blocking subprocess; UI updates via wx.CallAfter()
- **Preview frames**: Loaded as wx.Bitmap from PNG; 60 FPS playback via wx.Timer
- **Board loading**: trimesh caches meshes; large STEP files 2-5s initial load
