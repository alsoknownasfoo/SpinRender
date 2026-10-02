# Module Reference

**Last refreshed:** 2026-10-02. Line counts are approximate; public API only.

## Entry Point

### `spinrender_plugin.py` (~540 lines)
- `SpinRenderPlugin(pcbnew.ActionPlugin)` — `defaults()`, `Run()`: dependency check, single-window
  reuse, last-used settings, cache warm-up, then opens the frame.
- `SpinRenderFrame(wx.Frame)` — hosts `SpinRenderPanel`; theme hot-reload timer
  (`on_theme_watch_timer`), `on_activate`, `on_close`.

### `version.py` (~195 lines)
`get_version()`, `base_version()`, `is_newer()`, `is_pcm_install()`, `is_dev_build()`,
`installed_package_dir()` — runtime version from the stamp file, git HEAD or PCM install.

## Core (`SpinRender/core/`)

### `settings.py` (~55 lines)
`RenderSettings` dataclass — every persisted setting, validated in `__post_init__`;
`to_dict()` / `from_dict()`. See `data.md`.

### `renderer.py` (~990 lines)
`RenderEngine(board_path, settings: dict, progress_callback, source_board_path)`
- `render()` → `{'output', 'preview', 'frame_dir', 'frame_count'}` or `None` if canceled
- `generate_frames(dir)` — one `kicad-cli pcb render` per frame (30 fps × period)
- `assemble_mp4` / `assemble_gif` / `assemble_png_sequence`, `get_output_path()`, `cancel()`
- `PRESETS` (hero / spin / flip), `LIGHTING_PRESETS` (studio / dramatic / soft / workspace)

Module helpers:
- `compute_kicad_angles()` — universal-joint parameters → kicad-cli `--rotate X,Y,Z`
- `find_command()` — locates `kicad-cli` / `ffmpeg` (PATH + platform install dirs)
- `_pad_frame_to_size()`, `_png_size()`, `_render_size_from_cmd()` — restore kicad-cli's
  cropped frames to the effective requested size
- `_apply_overrides()` — user CLI overrides replace base flags
- Crash handling: `_is_probable_crash()`, `_crash_diagnostics()`, `_run_minimal_probe()`,
  `_kicad_cli_arch_report()` (macOS Rosetta detection)
- `_prepare_kicad_config_home()` — per-user copy of `resources/kicad_config/<version>/`

### `render_controller.py` (~145 lines)
`RenderController` — `start_render(...)` runs `RenderEngine.render()` on a daemon thread,
`cancel()`, `is_rendering()`; progress/completion delivered via `wx.CallAfter`; frame dirs
removed on the UI thread after pending callbacks.

### `preview.py` (~1040 lines)
- `PCBModelLoader` — `export_glb(board, out)` (kicad-cli GLB export), `load_glb_mesh(path)`
  (trimesh, concatenated without texture packing, rotated face-up, scaled to mm).
- `GLPreviewRenderer(glcanvas.GLCanvas)` — background GLB load (cached by board SHA-1 in
  `<tmp>/SpinRender_Cache`), shaded + feature-edge drawing, animation timer.
  `set_universal_joint_parameters`, `set_period`, `set_direction`, `set_lighting`,
  `set_background_color`, `set_render_mode`, `set_aspect_ratio`, `reload_model`,
  `start_preview` / `stop_preview`, `cleanup`.
- `PreviewRenderer(wx.Panel)` — legacy wx-drawn wireframe renderer; not instantiated anywhere
  (candidate for removal).

### `board_workspace.py` (~600 lines)
`BoardWorkspace(board_path)` — hidden working copy of the `.kicad_pcb` (+ project siblings):
`capture_live_board()` (snapshot of the open, possibly unsaved board), `prepare_for_render(...)`,
`reset()`, `cleanup()`. Render filters: `apply_render_filters_to_board_file()` and the
`remove_*_from_board_file()` helpers (vias, components, test points, user drawings).

### `cache_warmer.py` (~470 lines)
`ensure_model_cache_warm(parent, board_path) → bool` — runs a throwaway render behind a themed
progress dialog so KiCad's 3D model cache is warm; `False` if the user cancels.

### `presets.py` (~270 lines)
`PresetManager(board_path)` — `save_preset`, `load_preset`, `list_presets`, `delete_preset`,
`get_last_used_settings`, `save_last_used_settings`. Storage layout in `data.md`.

### `theme.py` (~550 lines)
`Theme` singleton (`Theme.current()`) — loads `resources/themes/{dark,light}.yaml`, resolves
tokens: `color()`, `color_states()`, `font()`, `font_size()`, `size()`, `glyph()`, `frame()`,
`border()`, `text_style()`, `is_light()`, `reload()`.

### `locale.py` (~170 lines)
`Locale` singleton (`Locale.current()`) — YAML locale with dot-path `get(key, default)`.

### `self_update.py` (~150 lines)
Non-PCM installs only: `resolve_latest()`, `download()`, `extract_zip()`, `find_package_root()`,
`apply_package()`; raises `UpdateError` with user-facing messages. Used by the About dialog.

## UI (`SpinRender/ui/`)

### `main_panel.py` (~790 lines)
`SpinRenderPanel` — builds the two-panel layout, owns the controllers and `BoardWorkspace`,
wires control events (`_wire_parameter_events`), render lifecycle (`on_render`,
`on_render_progress`, `on_render_finished`, `on_cancel`), settings persistence
(`schedule_save` / `flush_save` / `save_settings`), theme reapply, live-board refresh.

### `controls_side_panel.py` (~1010 lines)
`ControlsSidePanel` — left sidebar: header, preset cards, parameters (rotation axes, period,
direction, lighting), output (format, resolution, background, render filters), footer
buttons. `BUILTIN_RESOLUTIONS`. `SVGLogoPanel`. See `frontend.md`.

### `preview_panel.py` (~570 lines)
`PreviewPanel` — viewport container, render-mode nav (shaded / wireframe / both), corner
overlays (`update_preview_overlay`), render-result display and looping playback
(`start_playback` / `stop_playback`), pass-throughs to the viewport.

### `parameter_controller.py` (~280 lines)
`ParameterController` — one handler per control (`on_board_tilt_change`, `on_period_change`,
`on_direction_change`, `on_lighting_change`, `on_format_change`, `on_resolution_change`,
`on_hide_*_change`, `on_bg_color_change`, ...): settings → paired control → preview → preset
match → debounced save.

### `preset_controller.py` (~300 lines)
`PresetController` — `on_preset_change`, `apply_preset_data`, `check_preset_match` (built-in
and custom presets), `on_save_preset`.

### `custom_controls.py` (~2000 lines)
Themed, self-painted controls: `CustomSlider`, `CustomToggleButton`, `CustomCheckbox`,
`CustomDropdown` (+ `DropdownPopup`), `CustomButton`, `PresetCard`, `SectionLabel`,
`SectionToggle`, `CustomInput`, `ProjectFolderChip`, `CustomColorPicker`,
`CustomListView` / `CustomListItem`. Custom events: `EVT_LIST_ITEM_SELECTED`,
`EVT_LIST_ITEM_DELETED`, `EVT_COLOURPICKER_CHANGED`.

### `dialogs.py` (~2170 lines)
`BaseStyledDialog` (chromeless, draggable, themed) and subclasses: `AdvancedOptionsDialog`,
`SavePresetDialog`, `RecallPresetDialog`, `AddResolutionDialog`, `CustomResolutionsDialog`,
`FilenameEntryDialog`, `MessageDialog` (+ `show_message()`), `AboutSpinRenderDialog`
(version + self-update).

### Smaller UI modules
| Module | Contents |
|---|---|
| `helpers.py` (~660) | `create_text`, `update_text`, `create_numeric_input`, `create_section_label`, `apply_transparent_background`, `effective_background`, SVG loading, disabled/hover state helpers |
| `status_bar.py` (~110) | `StatusBar` — `set_status`, `set_error`, `set_complete`, `reset` |
| `text_styles.py` (~175) | `TextStyle` (immutable spec), `TextStyles` (semantic styles from theme) |
| `registry.py` (~35) | `ControlRegistry` — `add`, `filter`, `controls` (by section) |
| `events.py` (~10) | `EVT_PARAMETER_INTERACTION` |
| `validation.py` (~225) | `validate_all_tokens`, `validate_theme_schema`, `ContrastChecker` (WCAG) |
| `dependencies.py` (~250) | `DependencyChecker.check_and_prompt()` (UI wrapper) |
| `dependency_dialog.py` (~420) | `DependencyDialog` — self-contained styling (runs before Theme is usable) |
| `error_dialog.py` (~65) | `show_copyable_error()` |

## Foundation (`SpinRender/foundation/`)
- `fonts.py` — font family constants (`JETBRAINS_MONO`, `OSWALD`, `INTER`, `MDI_FONT_FAMILY`).
- `icons.py` — `STATUS_ICONS`, `UI_ICONS`, `get_glyph()`.

## Utils (`SpinRender/utils/`)
| Module | Contents |
|---|---|
| `check_dependencies.py` | `DependencyChecker` (no UI): `check_all`, `check_dependency`, `check_python_package`, `install_dependency` |
| `logger.py` | `SpinLogger` — date-named logs in `SpinRender/logs/` (temp dir fallback), 30-day cleanup, `open_logs_folder()` |
| `subprocess_utils.py` | `NO_WINDOW_FLAGS`, `find_kicad_sibling_binary()` |
| `paint_guard.py` | `guarded_paint` — keeps paint-handler exceptions from killing the app |
| `gl_context_compat.py` | `patch_context_lookup()` — PyOpenGL context fix (Linux/Mesa) |
| `wx_svg_compat.py` | `ensure_wx_svg()` — wx.svg shim / vendored fallback |
| `linux_fonts.py` | `install_linux_fonts()` — bundled fonts into fontconfig |
