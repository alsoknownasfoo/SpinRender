# SpinRender Architecture

**Last refreshed:** 2026-10-02 (v0.9.0 + unreleased fixes on `main`)

## Project Type

KiCad 9/10 **Action Plugin** (Python 3, wxPython) that drives `kicad-cli pcb render` to
produce looping 360° turntable animations of a PCB (MP4, GIF or PNG sequence).

SpinRender does **not** render frames itself. It:
- shows a live OpenGL approximation of the shot (preview of a GLB export of the board),
- translates its camera parameters into per-frame `kicad-cli pcb render` calls,
- assembles the frames with `ffmpeg`.

## High-Level Architecture

```
KiCad PCB Editor
  └─ SpinRenderPlugin.Run()                     spinrender_plugin.py
       ├─ DependencyChecker (prompt/install)    ui/dependencies.py → utils/check_dependencies.py
       ├─ ensure_model_cache_warm()             core/cache_warmer.py
       └─ SpinRenderFrame (wx.Frame)
            └─ SpinRenderPanel                  ui/main_panel.py
                 ├─ ControlsSidePanel           ui/controls_side_panel.py   (left: presets, parameters, output, footer)
                 ├─ PreviewPanel                ui/preview_panel.py         (right: viewport + overlays)
                 │    └─ GLPreviewRenderer      core/preview.py             (OpenGL canvas, GLB mesh)
                 ├─ StatusBar                   ui/status_bar.py
                 ├─ ParameterController         ui/parameter_controller.py  (control → settings → preview)
                 ├─ PresetController            ui/preset_controller.py     (apply / match / save presets)
                 ├─ RenderController            core/render_controller.py   (background thread)
                 │    └─ RenderEngine           core/renderer.py            (kicad-cli frames + ffmpeg assembly)
                 └─ BoardWorkspace              core/board_workspace.py     (hidden working copy of the board)

Shared services: Theme (core/theme.py), Locale (core/locale.py), PresetManager (core/presets.py),
RenderSettings (core/settings.py), SpinLogger (utils/logger.py)
```

## Key Data Flows

### 1. Startup
1. `SpinRenderPlugin.Run()` runs the dependency check (`kicad-cli`, `ffmpeg`, PyOpenGL,
   numpy, trimesh, PyYAML) and offers to install anything missing.
2. Reuses the open window if one exists (`SpinRenderFrame.active_instance`).
3. Requires a saved board, loads last-used settings (`PresetManager.get_last_used_settings`)
   and the active locale.
4. `ensure_model_cache_warm()` runs a throwaway `kicad-cli` render with a progress dialog so
   KiCad's 3D model tessellation cache is populated (a cold cache can take many minutes).
5. Creates `SpinRenderFrame` → `SpinRenderPanel`, which builds the UI and creates a
   `BoardWorkspace` for the board.
6. `GLPreviewRenderer` exports the board to GLB (`kicad-cli pcb export glb`, cached in the
   temp dir by board content hash) on a background thread and starts the preview.

### 2. Parameter change
`Custom*` control event → `ParameterController.on_*` → updates `RenderSettings` →
updates the paired slider/input → pushes the value to `PreviewPanel` / `GLPreviewRenderer`
→ `PresetController.check_preset_match()` → `schedule_save()` (500 ms debounce →
`last_used.json`). Any enabled control also fires `EVT_PARAMETER_INTERACTION`, which
dismisses a displayed render result.

### 3. Render
1. `SpinRenderPanel.on_render` → `_prepare_render_board_path()` →
   `BoardWorkspace.prepare_for_render()`, which snapshots the live (possibly unsaved) board
   into the hidden working copy and applies the render filters (vias / components /
   test points).
2. `RenderController.start_render` runs `RenderEngine.render()` on a daemon thread.
3. `RenderEngine.generate_frames`: per frame, converts the universal-joint parameters to
   `--rotate X,Y,Z` (`compute_kicad_angles`), runs `kicad-cli pcb render`, retries at
   `basic` quality if it crashes, then pads the frame back to the requested size
   (`_pad_frame_to_size`: kicad-cli writes a centered crop a few px smaller).
4. Assembly by format: `assemble_mp4` / `assemble_gif` (ffmpeg, background color composited
   under the transparent frames) or `assemble_png_sequence` (copy).
5. Progress is marshalled to the UI with `wx.CallAfter`; the result loops in the preview
   (`PreviewPanel.start_playback`) and the frame dir is cleaned up later on the UI thread.

### 4. Theme hot-reload
`SpinRenderFrame` polls the active theme YAML's mtime every second; on change it reloads
`Theme` and calls `reapply_theme()` down the panel tree.

## Extension Points

### Adding a parameter control
1. `RenderSettings` field (+ validation) in `core/settings.py`.
2. Builder in `ControlsSidePanel` (`create_*_control`), registered with
   `section='parameters'` so it is enabled/disabled with the section.
3. Expose it in `SpinRenderPanel`'s controls dict so `ParameterController` and
   `PresetController` receive it; bind events in `_wire_parameter_events`.
4. Handler in `ParameterController`; apply it in `PresetController.apply_preset_data`
   (and `check_preset_match` if presets should compare it).
5. Pass it to `kicad-cli` in `RenderEngine.generate_frames` and mirror it in
   `GLPreviewRenderer` if it affects the shot.
6. Locale keys in `resources/locale/en_US.yaml` (and the other locales).

### Adding a theme or locale
- Theme: `resources/themes/<name>.yaml` following `docs/reference/theme-schema-v2.md`.
- Locale: `resources/locale/<lang>.yaml` following `docs/reference/locale-schema-v2.md`.

## Design Notes
- **Controllers over a god panel:** `SpinRenderPanel` wires things together;
  behaviour lives in `ParameterController`, `PresetController` and `RenderController`.
- **Singletons:** `Theme.current()` and `Locale.current()`.
- **ControlRegistry:** every control registers with a section so whole sections can be
  enabled/disabled (e.g. during a render).
- **Working copy:** renders never touch the user's `.kicad_pcb`; `BoardWorkspace` keeps a
  hidden copy and cleans it up on close.
- **Isolated KiCad config:** `kicad-cli` runs with `KICAD_CONFIG_HOME` pointed at a
  per-user copy of `resources/kicad_config/<version>/` (forces raytracing settings).
- **Preview ≠ render engine:** the preview is an OpenGL approximation of the shot, not a
  kicad-cli render, so framing and lighting are close but not pixel-identical.
