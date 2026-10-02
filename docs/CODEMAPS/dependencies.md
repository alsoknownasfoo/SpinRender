# External Dependencies & Resources

**Last refreshed:** 2026-10-02

## Runtime dependencies

Checked on every launch by `DependencyChecker` (`utils/check_dependencies.py`, UI wrapper in
`ui/dependencies.py` + `ui/dependency_dialog.py`). From the dialog, missing Python packages
are pip-installed into KiCad's Python; missing commands are installed via Homebrew (macOS) or
`pkexec apt-get` (Linux). On Windows, command dependencies get manual instructions instead.

| Dependency | Type | Used for |
|---|---|---|
| `kicad-cli` | command (ships with KiCad 9/10) | frame rendering (`pcb render`), preview mesh (`pcb export glb`), cache warm-up |
| `ffmpeg` | command (PATH or common install dirs) | MP4/GIF assembly, frame padding |
| `PyOpenGL` (+ `PyOpenGL-accelerate`) | Python | live preview |
| `numpy` | Python | mesh/camera math |
| `trimesh` | Python | GLB loading |
| `PyYAML` | Python | themes, locales |
| `pyobjc-core`, `pyobjc-framework-Cocoa` | Python, macOS only | suppressing native focus rings on custom controls |
| `wxPython` | provided by KiCad | UI |
| `pcbnew` | provided by KiCad | Action Plugin API, live board capture |

`find_command()` (`core/renderer.py`) and `find_kicad_sibling_binary()`
(`utils/subprocess_utils.py`) locate the commands: PATH first, then platform install
locations (Homebrew, Program Files, the KiCad app bundle).

Fonts (bundled in `resources/fonts/`, installed on first launch; `utils/linux_fonts.py` uses
fontconfig on Linux): JetBrains Mono, Oswald, Material Design Icons.

## Bundled resources (`SpinRender/resources/`)

| Path | Contents |
|---|---|
| `themes/dark.yaml`, `themes/light.yaml` | design tokens (`core/theme.py`) |
| `locale/*.yaml` | 19 locales, `en_US` is the source (`core/locale.py`) |
| `fonts/` | the three font files above |
| `icons/` | `logo.svg`, author/AI-assistant SVGs for the About dialog |
| `kicad_config/9.0/`, `kicad_config/10.0/` | config homes for kicad-cli (raytracing settings, see `data.md`) |
| `icon.png` | toolbar icon |

`vendor/` holds a vendored `wx.svg` fallback used by `utils/wx_svg_compat.py`.

## Installation & packaging

| Path | How |
|---|---|
| PCM (recommended) | flat zip: `plugins/`, `resources/`, `metadata.json`. Build steps in `docs/GUIDE_RELEASE_PROCESS.md`; `packaging/pcm/` holds the PCM icon and a schema reference copy |
| `install.sh` / `install.bat` | finds every installed KiCad version, copies the plugin into its plugins dir, installs Python deps into KiCad's Python. Flags: `-y`, `--reinstall-deps`, `--link-theme` (symlink `dark.yaml` for live theme editing), `-u/--uninstall` |
| Self-update | non-PCM installs can update from the About dialog (`core/self_update.py`, GitHub releases) |

Version: `__version__` in `SpinRender/__init__.py` is the source of truth;
`scripts/check_version.py` checks the copies in `metadata.json` match. `version.py` resolves
the runtime version (stamp file, git HEAD, PCM install).

## Development

- Tests: `pytest` (`pytest.ini`, `tests/`). wx is mocked in `tests/conftest.py`, so the
  unit suite runs headless without wxPython.
- CI: `.github/workflows/tests.yml` runs the suite on Ubuntu, macOS and Windows with Python 3.11.
- Theme tooling: `tools/validate_theme.py`, `tools/theme_validator/`, `tools/visual_debug/`
  (see `tools/INDEX.md`).

## Platform notes

- **macOS:** Homebrew `ffmpeg`; Rosetta-translated `kicad-cli` is detected in crash diagnostics.
- **Windows:** subprocesses use `NO_WINDOW_FLAGS`; `install.bat` can install ffmpeg via winget.
- **Linux:** PyOpenGL context patch (`utils/gl_context_compat.py`), fontconfig fonts,
  `pkexec` for privileged dependency installs.
