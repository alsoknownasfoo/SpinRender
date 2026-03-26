# External Dependencies & Resources

<!-- Generated: 2026-03-25 | Files scanned: 30 Python modules | Token estimate: ~600 -->

## Python Package Dependencies

**From `pyproject.toml`**:

| Package | Version | Purpose | Import Location |
|---------|---------|---------|-----------------|
| PyYAML | >=6.0 | YAML parsing for themes and locales | `yaml.safe_load()` |
| PyOpenGL | >=3.1.0 | OpenGL bindings for 3D rendering | `OpenGL.GL` |
| PyOpenGL-accelerate | >=3.1.0 | C-accelerated OpenGL wrappers | (same) |
| trimesh | >=4.0.0 | 3D mesh loading (STEP, STL, OBJ) | `trimesh.load()` |
| numpy | >=1.24.0 | Numeric operations for transforms | `numpy arrays` |
| pyobjc-core | macOS only | Cocoa bridge for macOS integration | `objc` |
| pyobjc-framework-Cocoa | macOS only | Cocoa framework bindings | `Cocoa` |

**Installation**: `pip install -e .` or bundled installer scripts
- `install.sh` (Unix/macOS)
- `install.bat` (Windows)

**Development**:
- `typescript`/`tsx` for building ClojureScript (if applicable)
- `vitest` for testing

---

## System Dependencies

### OpenGL

- **Requirement**: GL/glext.h available in system headers
- **Check**: `DependencyChecker._check_opengl()` attempts to compile test program
- **Purpose**: 3D viewport rendering in `GLPreviewRenderer`
- **Fallback**: None - plugin disables if OpenGL unavailable

### KiCad

- **Versions**: 9.0 or 10.0 (tested)
- **Integration**: Action Plugin via `pcbnew` module
- **Plugin Loading**: KiCad's plugin manifest system
  - Manifest location: `resources/kicad_config/{version}/*.json`
  - KiCad scans plugin directories for `*.json` action configs
  - On toolbar click: imports module, instantiates `SpinRenderPlugin`, calls `Run()`

---

## KiCad Configuration Files

### Purpose
Map SpinRender actions to KiCad's plugin system (toolbar buttons, menu items).

### Directory Layout
```
SpinRender/resources/kicad_config/
├── 9.0/
│   ├── 3d_viewer.json   # 3D viewer toolbar
│   ├── eeschema.json    # Schematic editor
│   ├── fpedit.json      # Footprint editor
│   ├── kicad.json       # Main PCB editor (KiCad 9)
│   ├── kicad_common.json # Shared config
│   ├── pcbnew.json      # PCB editor
│   └── cvpcb.json       # Footprint assigner
└── 10.0/                # Updated for KiCad 10.0
    └── [same 7 files]
```

**Total**: 14 JSON files (7 per version)

### Action Config Schema (example)
```json
{
  "action_id": "SpinRender:Render",
  "action_name": "SpinRender",
  "icon": "icon.png",
  "class": "SpinRenderPlugin",
  "shortcut": "",
  "tooltip": "Generate animated PCB renders",
  "menu_item": true,
  "menu_path": "Tools/SpinRender",
  "toolbar": true,
  "toolbar_id": "SpinRenderToolbar",
  "visibility": "always"
}
```

**Version Differences**:
- KiCad 9: Primary config is `kicad.json` (main app) and `pcbnew.json` (PCB editor)
- KiCad 10: Unified under `pcbnew.json`; added `toolbar_id`, `visibility`

---

## Theme Resources

### Theme Files
```
SpinRender/resources/themes/
├── dark.yaml   # Default dark theme (comprehensive token set)
└── light.yaml  # Light theme variant
```

**Current Status**: Both themes fully implemented, hot-reload supported.

**Schema Version**: Implicit v2 (YAML structure with `components.buttons.*` etc.)

**Token Categories**:
- `colors.*` — color palette (60+ tokens)
- `radius.*` — corner rounding scale
- `borders.*` — border widths and roles
- `dividers.*` — separator line styles
- `typography.*` — font families, sizes, weights, spacing
- `text.*` — text style roles (25+ roles)
- `glyphs.*` — icon font Unicode mappings (50+ icons)
- `layout.*` — app layout tokens (main, dialogs)
- `components.*` — reusable UI component specs (buttons, sliders, toggles, etc.)

**Token Resolution**:
- Direct values: `"#rrggbb"`, `"rgba(r,g,b,a)"`, `"white"`
- Variable references: `"@colors.primary"` or `"ref: colors.primary"`
- Function calls: `"func: darken(colors.bg, 0.1)"`
- Compositions: `"mix(colors.bg, colors.fg, 0.5)"`

**Theme Hot-Reload**:
- `SpinRenderFrame` timer checks YAML mtime every 1s
- On change: `Theme.reload()` → `panel.reapply_theme()` → all controls refresh colors/fonts

---

## Localization Resources

### Locale Files
```
SpinRender/resources/locale/
├── en.yaml        # Base English strings
├── en_US.yaml     # US English (date/number formats, variants)
└── en_US_COMPLETE.yaml  # Auto-generated full set (all keys)
```

**Structure (YAML)**:
```yaml
locale:
  en:
    component:
      button:
        render:
          label: "RENDER"
          icon_ref: "render-action"
        stop:
          label: "STOP"
          icon_ref: "stop"
    dialog:
      title:
        preset_save: "Save Preset"
        about: "About SpinRender"
      # ... 100+ keys total
```

**Interpolation**:
```python
_locale.get("component.status.rendering", current=12, total=60)
# → "Rendering frame 12/60"
```

**Hot-Reload**: Same as theme — file mtime watcher in `SpinRenderFrame` calls `Locale.reload()`.

**Orphan Detection**: Recent audit found 50+ orphaned keys in `en_US.yaml` not referenced in code. Safe to remove, but retained for future translations.

---

## Font Resources

```
SpinRender/resources/fonts/
├── JetBrainsMono-VariableFont_wght.ttf  # Monospace (code, data)
├── Oswald-VariableFont_wght.ttf        # Sans-serif (headings)
└── materialdesignicons-webfont.ttf     # MDI icons (delete, play, etc.)
```

**Registration**: Loaded at startup via `wx.Font.AddPrivateFontDirectory()` and `wx.FontInfo()`.

**Usage**:
- `TextStyles` → `wx.Font` creation via `TextStyle.create_font()`
- Icons → Icon font via `wx.Font` + `wx.StaticText` with Unicode codepoint

**Fallback**: If font fails to load, defaults to system font (wx.DEFAULT).

---

## Icon Resources

```
SpinRender/resources/
├── icon.png          # Plugin toolbar icon (48x48 or 256x256)
├── logo.svg          # Application/About logo (vector)
└── icons/            # Additional SVG icons
    ├── gemini.svg
    ├── claude.svg
    ├── copilot.svg
    ├── stepfun.svg
    ├── chatgpt.svg
    └── FH.svg        # Sponsor logo
```

**Icon Requirements**:
- `icon.png`: PNG format, 256x256 recommended (KiCad scales)
- Used in KiCad toolbar and SpinRender frame title bar
- `logo.svg`: Vector format for high-DPI about dialog

**AI Service Icons**: Used in AboutDialog to link to external services.

---

## Dependency Checker Logic

**File**: `SpinRender/ui/dependencies.py` (178 lines) + `ui/dependency_dialog.py` (368 lines)

### Checks Performed

1. **wxPython**
   - `import wx`
   - Check version: `wx.VERSION` >= (4, 0)
   - Test creation: `wx.App()`, `wx.Frame()`

2. **OpenGL**
   - Check for header: `GL/glext.h` in system include paths
   - Compile test program: `#include <GL/glext.h>`
   - Link test: `-lGL` (Linux), `-framework OpenGL` (macOS), `opengl32` (Windows)

3. **trimesh**
   - `import trimesh`
   - Check version: `trimesh.__version__` >= "4.0.0"

4. **PyOpenGL**
   - `import OpenGL.GL`
   - Check version if needed

5. **PyYAML**
   - `import yaml`
   - Check version: `yaml.__version__` >= "6.0"

6. **Platform-specific (macOS)**
   - `import pyobjc_core`
   - `import Cocoa`

### UI: DependencyDialog

If checks fail:
- Dialog shows status (pass/fail icons)
- Lists missing packages
- Offers to run `pip install --user ...`
- Can cancel and exit

### Console: check_dependencies.py

For debugging/CLI usage:
```bash
python -m SpinRender.utils.check_dependencies
```
Outputs table of checks, suggests install command.

---

## Build & Packaging

### Distribution Formats

- **Source**: `SpinRender/` directory + `pyproject.toml` (editable install)
- **Plugin Zip**: `SpinRender.zip` (zipped plugin for KiCad manual install)
- **Wheel**: `dist/SpinRender-*.whl` (pip installable)

### Installers

- `install.sh` (Bash, Unix/macOS)
  - Runs `pip install --user .`
  - Copies KiCad configs to KiCad plugin directory
  - Sets up desktop shortcut (optional)

- `install.bat` (Windows CMD)
  - Same as above, Windows-specific paths

### Build Process

1. Python packages installed to user site-packages (`site.getusersitepackages()`)
2. KiCad action configs copied to KiCad plugin directory:
   - Linux: `~/.local/share/kicad/9.0/plugins/`
   - macOS: `~/Library/Application Support/kicad/plugins/`
   - Windows: `%APPDATA%\kicad\9.0\plugins\`
3. Plugin zip created for manual installation (drag-drop to KiCad plugin manager)

### Entry Registration

KiCad scans plugin directories for `*.json` action configs.
On toolbar click, imports module specified in `"class"` field.
Module-level `SpinRenderPlugin().register()` called automatically on import.

---

## Resource Loading Strategy

All resources loaded via relative paths from `__file__`:

```python
plugin_dir = os.path.dirname(os.path.abspath(__file__))
theme_path = Path(plugin_dir) / "resources" / "themes" / "dark.yaml"
icon_path = os.path.join(plugin_dir, "resources", "icon.png")
```

**KiCad Plugin Context**:
Plugin directory is added to `sys.path` for imports.
Resources directory sits alongside Python modules.

**Path Resolution**:
- `spinrender_plugin.py` adds `plugin_parent` and `plugin_dir` to `sys.path`
- Enables both `import SpinRender.core.theme` and `import core.theme`
- Robust for KiCad's Python embedding quirks

---

## Optional Dependencies

None currently - all dependencies required for core functionality.

**Future**:
- `pillow` for advanced image processing (optional)
- `ffmpeg` for alternative video encoding (system binary, not PyPI)

---

## Development Dependencies

Not tracked in `pyproject.toml` (dev-only):

- `pytest` + `pytest-cov` - testing
- `types-wxPython` - type stubs (if mypy used)
- `ruff` / `black` / `isort` - linting/formatting
- `typing-extensions` - backports (if needed)

---

## Security Considerations

**No hardcoded secrets**:
- All API keys (if any future) must use environment variables
- Theme/locale are pure data, no security impact

**User Data**:
- Presets stored in `~/.spinrender/` (user home)
- Board cache in same directory
- No network access by plugin (except optional update check)

**Subprocess Execution**:
- Blender CLI invoked via `subprocess.Popen()`
- Arguments sanitized (from RenderSettings)
- User board path escaped to prevent injection

---

## Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| Linux (Ubuntu 22.04+) | ✅ Tested | Requires `libgl1-mesa-glx`, `libglu1-mesa` |
| macOS (11+) | ✅ Tested | Requires pyobjc, Cocoa bindings |
| Windows (10/11) | ✅ Tested | wxPython bundled in KiCad |

**OpenGL**: All platforms require working GL drivers. Integrated GPUs OK; discrete recommended for large boards.
