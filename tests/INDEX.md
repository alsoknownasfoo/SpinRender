# Tests

Run with KiCad's bundled interpreter so the wxPython build matches the
plugin's runtime. `pytest.ini` adds coverage flags that require `pytest-cov`;
bypass with `-o addopts=` if it isn't installed:

```
& "C:\Program Files\KiCad\10.0\bin\python.exe" -m pytest tests/unit -q -o addopts=
```

## Top level

| File | Purpose |
| :--- | :--- |
| `conftest.py` | Shared fixtures and wx test bootstrapping for the suite. |
| `test_environment.py` | Sanity-checks the test environment itself (interpreter, imports, paths). |
| `test_validate_theme_integration.py` | End-to-end run of the theme validator CLI against the real theme files. |

## Unit tests (`unit/`)

| File | Covers |
| :--- | :--- |
| `test_controls_side_panel.py` | Left sidebar construction: sections, registry, collapse/expand behaviour. |
| `test_core_theme.py` | Theme engine: token resolution, refs/pointers, colors, fonts, state lookups. |
| `test_custom_controls_theme.py` | Custom controls' theme-token usage and state-dependent styling. |
| `test_custom_listview_single.py` | CustomListView item add/clear/select/delete behaviour. |
| `test_dependency_dialog.py` | Dependency-checker dialog flow and UI states. |
| `test_dialogs_layout_tokens.py` | Dialog layout dimensions sourced from theme tokens. |
| `test_dialogs_theme.py` | Dialog theming: colors, hot-reload (`reapply_theme`). |
| `test_helpers.py` | `ui/helpers.py`: text creation/registry, backgrounds, SVG helpers. |
| `test_layout_structure.py` | Structural expectations of the main panel layout tree. |
| `test_locale.py` | Locale loading and key lookup/fallback. |
| `test_main_panel.py` | Main panel wiring: preview, controls, render flow callbacks. |
| `test_main_panel_theme.py` | Main panel theme application and hot-reload. |
| `test_no_inline_colors.py` | Lint-style guard: no hardcoded colors outside the theme system. |
| `test_parameter_controller.py` | Parameter controller: slider/input syncing and validation. |
| `test_preview_panel.py` | Preview panel: overlay text, render-mode switching, playback state. |
| `test_settings.py` | Settings persistence: defaults, save/load round-trips. |
| `test_status_bar.py` | Status bar states: ready/error/progress/complete. |
| `test_svg_helpers.py` | SVG loading, markup loading, and fill-replacement helpers. |
| `test_text_styles.py` | TextStyle resolution, formatting transforms, alias map. |
| `test_v2_migration.py` | Migration of legacy settings/themes to the v2 format. |
| `test_validate_theme.py` | Theme validator internals (scanner/comparator/fixer units). |
| `test_validation.py` | Input validation helpers (numeric parsing, clamping, etc.). |
