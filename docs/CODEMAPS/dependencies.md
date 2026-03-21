<!-- Generated: 2026-03-21 | Files scanned: 29 Python files | Token estimate: ~600 -->

# External Dependencies & Resources

## Python Package Dependencies

From `pyproject.toml`:

| Package | Version | Purpose |
|---------|---------|---------|
| PyYAML | >=6.0 | YAML parsing for themes and locales |
| PyOpenGL | >=3.1.0 | OpenGL bindings for 3D rendering |
| PyOpenGL-accelerate | >=3.1.0 | C-accelerated OpenGL wrappers |
| trimesh | >=4.0.0 | 3D mesh loading (STEP, STL, OBJ) |
| numpy | >=1.24.0 | Numeric operations for transforms |
| pyobjc-core | macOS only | Cocoa bridge for macOS integration |
| pyobjc-framework-Cocoa | macOS only | Cocoa framework bindings |

**Installation**: `pip install -e .` or bundled installer scripts
- `install.sh` (Unix/macOS)
- `install.bat` (Windows)

---

## System Dependencies

### OpenGL
- Must have GL/glext.h available
- Tested via `DependencyChecker._check_opengl()`
- Required for 3D viewport rendering

### KiCad
- **Version**: 9.0 or 10.0
- **Integration**: Action Plugin via `pcbnew` module
- **Plugin Loading**: KiCad's plugin manifest system
  - Manifest: `resources/kicad_config/{version}/*.json`
  - Actions define toolbar buttons and menu items

---

## KiCad Configuration Files

### Purpose
Map SpinRender actions to KiCad's plugin system.

### Locations
```
SpinRender/resources/kicad_config/
├── 9.0/
│   ├── 3d_viewer.json   # 3D viewer toolbar
│   ├── eeschema.json    # Schematic editor
│   ├── fpedit.json      # Footprint editor
│   ├── kicad.json       # Main PCB editor
│   ├── kicad_common.json # Shared config
│   ├── pcbnew.json      # PCB editor (primary)
│   └── cvpcb.json       # Footprint assigner
└── 10.0/                # Updated for KiCad 10.0
    └── [same 7 files]
```

**Format**: KiCad action plugin JSON configuration
Defines toolbar/menu bindings for `SpinRenderPlugin`.

---

## Theme Resources

### Theme Files
```
SpinRender/resources/themes/
├── dark.yaml   # Default dark theme (comprehensive token set)
└── light.yaml  # Light theme variant
```

**Schema**: See `docs/THEME_SCHEMA.md`

**Token Structure**:
```yaml
colors:
  primary: "#ff5500"
  background: "ref: colors.surface"
  hover: "func: darken(colors.primary, 0.1)"

typography:
  heading:
    family: "Oswald"
    size: 24
    weight: "bold"

layout:
  spacing:
    small: 8
    medium: 16
    large: 24
```

### Theme Resolution
- Direct hex values: `#rrggbb` or `#rgb`
- Variable references: `ref: token.path`
- Function calls: `func: darken(color, amount)`
- Compositions: `mix(color1, color2, ratio)`

---

## Localization Resources

### Locale Files
```
SpinRender/resources/locale/
├── en.yaml        # Base English strings
└── en_US.yaml     # US English (date/number formats)
```

**Format**: YAML key-value pairs

```yaml
menu:
  file: "File"
  edit: "Edit"
  view: "View"

dialog:
  presets:
    title: "Manage Presets"
    save: "Save Current Settings"
    delete: "Delete Selected"
```

**Usage**: `_locale.get("menu.file")`

---

## Font Resources

```
SpinRender/resources/fonts/
├── JetBrainsMono-VariableFont_wght.ttf  # Monospace (code, data)
├── Oswald-VariableFont_wght.ttf        # Sans-serif (headings)
└── materialdesignicons-webfont.ttf     # MDI icons (delete, play, etc.)
```

**Registration**: Loaded by `wx.Font.AddPrivateFontDirectory()`

**Usage**:
- `TextStyles` → `wx.Font` creation via `TextStyle.create_font()`
- Icons → `wx.svg.SVGimage` from embedded SVG or icon font

---

## Icon Resources

```
SpinRender/resources/
├── icon.png          # Plugin toolbar icon (48x48 or 256x256)
└── logo.svg          # Application/About logo (vector)
```

**Icon Requirements**:
- PNG format
- Multiple sizes (toolbar, about dialog)
- Used in KiCad toolbar and SpinRender frame

---

## KiCAD Action Config Syntax

**Example** (`kicad.json`):
```json
{
  "action_id": "SpinRender:Execute",
  "action_name": "SpinRender",
  "icon": "icon.png",
  "shortcut": "",
  "tooltip": "Generate animated PCB renders",
  "menu_item": true,
  "toolbar": true,
  "class": "SpinRenderPlugin"
}
```

**Versioning**:
- `9.0/` configs target KiCad 9.x API
- `10.0/` configs target KiCad 10.x API
- Plugin auto-detects KiCad version and loads matching config

---

## Dependency Checker Logic

**File**: `SpinRender/ui/dependencies.py`

**Checks**:
1. **wxPython**: `import wx` + version check (>=4.0)
2. **OpenGL**: Check for `GL/glext.h` in system headers
3. **trimesh**: `import trimesh` + version (>=4.0.0)
4. **PyYAML**: `import yaml` + version (>=6.0)

**Installation Prompt**:
If dependencies missing, dialog offers to run:
```bash
pip install --user PyYAML PyOpenGL PyOpenGL-accelerate trimesh numpy
```

**Platform-specific**:
- macOS: also installs pyobjc-core, pyobjc-framework-Cocoa

---

## Build & Packaging

**Distribution**:
- Source: `SpinRender/` directory + `pyproject.toml`
- Packaged: `SpinRender.zip` (zipped plugin for KiCad)
- Installers: `install.sh` / `install.bat` (pip + KiCad config)

**Build Process**:
1. Python packages installed to user site-packages
2. KiCad action configs copied to KiCad config directory
3. Plugin zip created for manual installation

**Entry Registration**:
KiCad scans plugin directories for `*.json` action configs and loads
the specified Python class on demand.
