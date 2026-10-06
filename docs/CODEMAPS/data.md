# Data Models, Configuration & Storage

**Last refreshed:** 2026-10-02

## RenderSettings (`SpinRender/core/settings.py`)

Single dataclass holding everything that is persisted or sent to the render.

```python
@dataclass
class RenderSettings:
    # Camera / motion (universal-joint model)
    board_tilt: float = 0.0          # -90..90   board on the spindle
    board_roll: float = 0.0          # -180..180
    spin_tilt: float = 0.0           # -90..90   spindle itself
    spin_heading: float = 0.0        # -180..180 camera around the board
    zoom: float = DEFAULT_ZOOM       # MIN_ZOOM..MAX_ZOOM, passed to kicad-cli --zoom
    period: float = 10.0             # seconds per 360° (UI: 0.1..30), 30 fps
    direction: str = 'ccw'           # 'cw' | 'ccw'
    easing: str = 'linear'
    lighting: str = 'studio'         # 'studio' | 'dramatic' | 'soft' | 'workspace'

    # Output
    format: str = 'mp4'              # 'mp4' | 'gif' | 'png_sequence'
    resolution: str = '1920x1080'    # 'WxH'
    custom_resolutions: List[str] = field(default_factory=list)  # user-added 'WxH' entries
    bg_color: str = '#000000'        # composited under transparent frames
    hide_vias: bool = True           # render filters (see note below)
    hide_components: bool = True
    hide_test_points: bool = True
    output_auto: bool = True         # True → <board dir>/Renders/<timestamp>/
    output_path: str = ''            # used when output_auto is False
    cli_overrides: str = ''          # extra kicad-cli flags; replace matching base flags

    # Preview / app state
    render_mode: str = 'both'        # preview style: 'shaded' | 'wireframe' | 'both'
    preset: str = 'custom'           # selected preset id
    logging_level: str = 'info'
    theme_mode: str = 'system'       # 'dark' | 'light' | 'system'
    params_collapsed: bool = True    # sidebar section state
    output_collapsed: bool = False
```

**Validation** (`__post_init__`, raises `ValueError`): `board_tilt` and `spin_tilt` in ±90,
`board_roll` and `spin_heading` in ±180, `period > 0`, `MIN_ZOOM <= zoom <= MAX_ZOOM`.

**Zoom constants** (module level, shared by settings, renderer, preview and UI):
`DEFAULT_ZOOM = 0.8` (the fixed `--zoom` used before zoom was configurable), `MIN_ZOOM = 0.1`,
`MAX_ZOOM = 5.0`.

**Serialization:** `to_dict()` (`dataclasses.asdict`) and `from_dict(d)` (`cls(**d)`, so unknown
keys raise `TypeError`; missing keys take defaults).

**Render filter naming:** despite the names, the `hide_*` fields back the VIAS / COMPONENTS /
TEST POINTS checkboxes where *checked = include*. `SpinRenderPanel` passes
`hide_vias=not settings.hide_vias` (etc.) to `BoardWorkspace.prepare_for_render`.

`RenderEngine` receives `RenderSettings.to_dict()`, not the dataclass.

## Built-in presets (`RenderEngine.PRESETS`)

| id | board_tilt | board_roll | spin_tilt | spin_heading | period | zoom | direction | lighting |
|---|---|---|---|---|---|---|---|---|
| `hero` | 0 | -45 | 90 | 90 | 5 | 0.8 | ccw | dramatic |
| `spin` | 0 | -90 | -90 | -90 | 5 | 0.8 | ccw | studio |
| `flip` | 0 | -180 | 90 | 45 | 5 | 0.8 | cw | dramatic |

The fourth card ("Select custom") recalls a saved preset. `PresetController.check_preset_match`
compares the five numeric fields and `zoom` (±0.01) plus `direction` and `lighting`. Presets
saved before `zoom` existed load with `DEFAULT_ZOOM`.

## Lighting (`RenderEngine.LIGHTING_PRESETS`)

Each preset maps to kicad-cli `--light-top/-side/-bottom/-camera` intensities and
`--light-side-elevation`. `workspace` is empty: kicad-cli uses the 3D viewer settings.

## Storage locations

| What | Where | Written by |
|---|---|---|
| Global presets | `~/.spinrender/presets/<name>.json` | `PresetManager.save_preset(is_global=True)` |
| Project presets | `<board dir>/.spinrender/<name>.json` | `PresetManager.save_preset()` |
| Last-used settings | `<board dir>/.spinrender/last_used.json` and `~/.spinrender/presets/last_used.json` | `save_last_used_settings` (debounced from the UI) |
| Rendered output | `<board dir>/Renders/<yymmdd_HHMMSS>/<board>.mp4/.gif` or `<board>_00000.png...` | `RenderEngine.get_output_path` |
| Frame scratch | `<tmp>/spinrender_frames_*/frame0000.png...` | `RenderEngine.render` (removed by the UI later) |
| Last preview frame | `<tmp>/spinrender_preview/last_render_preview.png` | `RenderEngine.render` |
| Preview GLB cache | `<tmp>/SpinRender_Cache/<board>_<sha1[:16]>.glb` | `GLPreviewRenderer` |
| kicad-cli config home | `<tmp>/SpinRender_kicad_config/<9.0|10.0>/`: our `3d_viewer.json` + empty global library tables | `_prepare_kicad_config_home` |
| Board working copy | hidden `.<board>.spinrender-tmp.kicad_pcb` (+ project siblings, `.spinrender-src` snapshot) next to the board | `BoardWorkspace` |
| Logs | `SpinRender/logs/` (fallback `<tmp>/SpinRender_Logs`), 30-day retention | `SpinLogger` |

`get_last_used_settings` prefers the project file, then the global one.

### Preset JSON
```json
{
  "name": "My Preset",
  "settings": { "...": "RenderSettings.to_dict()" }
}
```
Preset names are sanitized to `[A-Za-z0-9_-]`, lowercased, for the filename. `last_used.json`
is the bare `RenderSettings.to_dict()` without the wrapper. There is no explicit schema
version: a field added to `RenderSettings` gets its default when an older file is loaded.

## Theme & locale data

- Themes: `resources/themes/dark.yaml`, `light.yaml`. Schema: `docs/reference/theme-schema-v2.md`,
  principles: `theme-design-principles.md`, validation: `theme-validation.md`.
- Locales: `resources/locale/<lang>.yaml` (19 files; `en_US` is the source of truth).
  Schema: `docs/reference/locale-schema-v2.md`. Lookup is dot-path (`Locale.get("parameters.period.label")`)
  with an inline English default at every call site.

## KiCad integration data

- `resources/kicad_config/<version>/3d_viewer.json` (the only tracked file there) forces
  raytracing settings (e.g. no floor) for kicad-cli renders. It is copied into the config home
  on every render; kicad-cli writes its other config JSONs there itself.
- The config home also gets empty `sym-lib-table`, `fp-lib-table` and `design-block-lib-table`
  when missing (never overwritten: kicad-cli adds PCM library rows to them). Without them,
  KiCad 10.0.x up to 10.0.6 segfaults during PCM library auto-load (issue #15).
- kicad-cli `--rotate` angles come from `compute_kicad_angles()` (rotation order
  `R_X(board_tilt) · R_spin · R_Z(board_roll)`), normalized to `[0, 360)`.
