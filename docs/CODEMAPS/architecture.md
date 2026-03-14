<!-- Generated: 2026-03-13 | Files scanned: 9 | Token estimate: ~600 -->
# SpinRender Architecture

## Project Type
KiCad Action Plugin — animated PCB render generator with camera loops and lighting presets.

## Tech Stack
- Python 3 (KiCad bundled) | wxPython GUI | OpenGL preview
- kicad-cli (frame rendering) | ffmpeg (video assembly)

## System Diagram
```
User (KiCad) → SpinRenderPlugin.Run()
                     │
                     ▼
              SpinRenderPanel (wx.Dialog)
             ┌────────┴────────┐
         Controls           GLPreviewRenderer
         (params)           (live OpenGL preview)
             │
             ▼
         RenderEngine
             │
    ┌────────┴────────┐
kicad-cli           ffmpeg
(PNG frames)     (MP4/GIF/sequence)
```

## Plugin Entry Flow
1. KiCad loads `SpinRenderPlugin` via `pcbnew.ActionPlugin`
2. `Run()` → launches `SpinRenderPanel` as modal dialog
3. User sets params → live GL preview updates
4. Render → `RenderEngine.render()` → kicad-cli + ffmpeg pipeline

## MVC Pattern
- **Model:** `PresetManager` (JSON), `RenderEngine` settings dict
- **View:** `SpinRenderPanel` + custom wxPython controls
- **Controller:** Event handlers (`on_preset_change`, `on_board_tilt_change`, etc.)

## Render Pipeline
```
settings dict → compute_kicad_angles() → kicad-cli args
                                              │
                                         PNG frames
                                              │
                          ┌───────────────────┤
                       MP4/GIF          PNG sequence
                      (ffmpeg)
```

## Key Rotation Math
Universal joint model: board_tilt, board_roll → board orientation; spin_tilt, spin_heading → spin axis
Euler XYZ: `M = R_X(kx) · R_Y(ky) · R_Z(kz)` → converted to kicad-cli `--pivot` args
