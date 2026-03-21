<!-- Generated: 2026-03-21 | Files scanned: 29 Python files | Token estimate: ~700 -->

# Data Models & Configuration

## Core Data Structures

### RenderSettings (`SpinRender/core/settings.py`)

**Purpose**: Serializable configuration for a single render

**Fields**:
```python
@dataclass
class RenderSettings:
    # Resolution
    width: int = 1920
    height: int = 1080

    # Camera
    orbit_speed: float = 1.0
    elevation: float = 30.0
    distance: float = 100.0

    # Lighting
    ambient: float = 0.3
    diffuse: float = 0.7
    specular: float = 0.5
    light_color: str = "#ffffff"

    # Material Colors
    board_color: str = "#2d5a27"
    solder_color: str = "#ffb347"
    copper_color: str = "#b87333"
    silkscreen_color: str = "#e0e0e0"

    # Animation
    fps: int = 30
    duration: float = 10.0  # seconds
    total_frames: int = 300  # computed: fps * duration

    # Output
    format: str = "mp4"  # or "gif"
    output_path: Optional[str] = None
```

**Serialization**:
- `to_dict()` → JSON-compatible dict
- `from_dict(d: dict)` → RenderSettings
- `validate()` → list of error strings

**Validation Rules**:
- `width`, `height`: 320-4096
- `orbit_speed`: 0.1-10.0
- `elevation`: -90 to 90
- `distance`: 10.0-500.0
- `ambient`, `diffuse`, `specular`: 0.0-1.0
- `fps`: 24-60
- `duration`: 3.0-30.0

---

### Theme Data Model

**Source**: YAML files (`resources/themes/*.yaml`)

**Schema** (high-level):
```yaml
name: "Dark"                   # Theme display name
version: 2                    # Theme schema version
description: "Dark theme"     # Human description

colors:
  primary: "#ff5500"          # Direct hex
  secondary: "ref: colors.accent"
  background: "func: darken(colors.surface, 0.1)"
  hover: "mix(colors.bg, colors.fg, 0.05)"
  surface: "#1e1e1e"
  text:
    primary: "#ffffff"
    secondary: "ref: colors.text.disabled"
    disabled: "func: alpha(colors.text.primary, 0.5)"

typography:
  heading:
    family: "Oswald"
    size: 24
    weight: "bold"
  body:
    family: "JetBrainsMono"
    size: 12
    weight: "normal"
  caption:
    family: "JetBrainsMono"
    size: 10
    weight: "normal"

layout:
  spacing:
    small: 8
    medium: 16
    large: 24
  border:
    radius: 4
    width: 1

  control:
    padding: 12
    min_height: 32

  panel:
    padding: 16
    gap: 8

icons:
  delete: "delete"           # Icon font glyph name
  play: "play"
  pause: "pause"
  add: "plus"

actions:
  render:
    bg: "ref: colors.primary"
    hover: "func: lighten(colors.primary, 0.1)"
  cancel:
    bg: "#ff4444"
```

**Token Resolution**:
1. Direct: `"#rrggbb"` or `"rgb(r,g,b)"`
2. Reference: `"ref: path.to.token"`
3. Function: `"func: darken(color, 0.1)"`
4. Composition: `"mix(a, b, 0.5)"`

**Supported Functions**:
- `darken(color, factor: 0-1)`
- `lighten(color, factor: 0-1)`
- `alpha(color, opacity: 0-1)`
- `saturate(color, factor)`
- `desaturate(color, factor)`
- `mix(a, b, ratio: 0-1)`
- `contrast(color)` - return black or white

---

### Preset Storage Format

**Directory Layout**:
```
~/.spinrender/presets/           (global)
  camera_loop.json
  high_quality.json
  xxx.kicad_pcb/.spinrender/    (project)
    preset1.json
    preset2.json
```

**JSON Structure**:
```json
{
  "name": "camera_loop",
  "created_at": "2026-03-20T14:30:00Z",
  "settings": {
    "width": 1920,
    "height": 1080,
    "orbit_speed": 1.5,
    "elevation": 30.0,
    "distance": 100.0,
    "ambient": 0.3,
    "diffuse": 0.7,
    "specular": 0.5,
    "light_color": "#ffffff",
    "board_color": "#2d5a27",
    "solder_color": "#ffb347",
    "copper_color": "#b87333",
    "silkscreen_color": "#e0e0e0",
    "fps": 30,
    "duration": 10.0,
    "format": "mp4"
  },
  "thumbnail": "presets/thumbnail.png"  # optional cached thumbnail
}
```

**Schema Version**: `settings` is flat RenderSettings fields (v1)

---

### Locale Strings

**Source**: `resources/locale/{lang}.yaml`

**Structure**:
```yaml
# Menus
menu:
  file: "File"
  edit: "Edit"
  view: "View"
  render: "Render"
  presets: "Presets"
  help: "Help"

# Menu items
menu.file.open_board: "Open Board..."
menu.file.exit: "Exit"
menu.presets.save: "Save Preset..."
menu.presets.manage: "Manage Presets..."

# Dialogs
dialog:
  title:
    preset_save: "Save Preset"
    preset_manage: "Manage Presets"
    advanced: "Advanced Options"
  button:
    ok: "OK"
    cancel: "Cancel"
    save: "Save"
    delete: "Delete"
    load: "Load"

# Status messages
status:
  ready: "Ready"
  rendering: "Rendering frame {current}/{total}"
  complete: "Render complete: {filename}"
  error: "Error: {message}"

# Tooltips
tooltip:
  resolution_width: "Output width in pixels"
  render_button: "Start rendering animation"
```

**Interpolation**: `_locale.get("status.rendering", current=12, total=60)`

---

## KiCad Configuration Schema

### Action Plugin JSON (v9.0 and v10.0)

**Example** (`resources/kicad_config/10.0/pcbnew.json`):
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

**Fields**:
- `action_id`: Unique ID (namespace:action)
- `action_name`: Display name in menus
- `icon`: Relative path to icon file
- `class`: Python class name to instantiate
- `shortcut`: Optional keyboard shortcut
- `tooltip`: Hover tooltip
- `menu_item`: Show in menu bar
- `menu_path`: Menu hierarchy (e.g., "Tools/Render")
- `toolbar`: Show in toolbar
- `toolbar_id`: Toolbar group
- `visibility`: "always", "pcbnew", etc.

**Version Differences**:
- KiCad 9.0: Uses `"kicad.json"` for main app
- KiCad 10.0: Updated schema with `toolbar_id`, `visibility`

---

## Board Loader Data Flow

**Input**: `.kicad_pcb` file path

**Process**:
1. Parse KiCad PCB using `pcbnew` API
2. Extract 3D model references (3D models in footprints)
3. For each 3D model:
   - Load STEP/STL/OBJ via `trimesh.load()`
   - Transform to board position (apply footprint transform)
   - Merge into single scene
4. Build `trimesh.Scene` with all board meshes
5. Provide to `GLPreviewRenderer` for OpenGL display

**Caching**:
- Board geometry cached in memory (per session)
- Thumbnails cached on disk (`~/.spinrender/cache/thumbnails/`)

---

## Preset Thumbnail Cache

**Location**: `~/.spinrender/cache/thumbnails/`

**Naming**: `{preset_hash}.png`

**Hash**: SHA256 of (preset_name + RenderSettings JSON)

**Generation**:
- On preset save: render single frame at 200x150
- Save PNG to thumb cache
- Associate with preset

**Invalidation**:
- If thumbnail missing → regenerate
- If preset settings changed → new hash, new thumbnail

---

## Settings Persistence

**UI State** (not presets):
- Last used board path: `~/.spinrender/last_board.json`
- Window geometry: `~/.spinrender/window_geometry.json`
- Last selected preset: `~/.spinrender/last_preset.json`
- Theme preference: `"dark"` or `"light"` → `~/.spinrender/theme.json`

**Format**: JSON with single key-value pairs

Example:
```json
{ "theme": "dark" }
{ "last_board": "/path/to/board.kicad_pcb" }
{ "geometry": { "x": 100, "y": 100, "w": 1200, "h": 800 } }
```

---

## Configuration Hierarchy

```
┌─────────────────────────────────────────────┐
│  CLI Arguments / Environment Variables     │
└─────────────────┬───────────────────────────┘
                  ↓ (highest priority)
┌─────────────────────────────────────────────┐
│  Session Settings (in-memory RenderSettings)│
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│  Preset (loaded from JSON file)            │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│  Default Settings (hardcoded in class)     │
└─────────────────────────────────────────────┘
```

**Overlay Rules**:
- CLI args override everything
- Loaded preset fills session settings
- If no preset → defaults used
- Changes in UI update session settings only
- Save to preset writes current session state

---

## Migrations & Versioning

**Theme Schema Versioning**:
- Theme YAML may include `version: 2`
- If missing → assume v1
- Migration on load? No, validation fails instead

**Preset Schema Versioning**:
- Preset JSON may include `"schema_version": 1`
- Backward compatibility: `RenderSettings.from_dict()` ignores extra fields
- Forward compatibility: Newer app should work with old presets (missing fields → defaults)

**KiCad Config Versioning**:
- Separate directories: `9.0/` and `10.0/`
- Plugin loads correct config based on detected KiCad version
- No migration needed, both coexist

---

## Validation Rules

### Theme Validation (`validation.py`)

**Checks**:
1. **Required sections**: `colors`, `typography`, `layout`
2. **Color format**: Hex or function/reference
3. **Circular references**: Detect `A → B → A`
4. **Missing references**: `ref: colors.missing` must exist
5. **Function syntax**: `func: name(args)` with valid name
6. **Type checking**: colors are strings, layout are numeric

**Output**: `ValidationReport` with errors, warnings, infos

---

### Settings Validation

**Method**: `RenderSettings.validate() → list[str]`

**Ranges**:
- 320 ≤ width, height ≤ 4096
- 0.1 ≤ orbit_speed ≤ 10.0
- -90 ≤ elevation ≤ 90
- 10.0 ≤ distance ≤ 500.0
- 0.0 ≤ lighting ≤ 1.0
- 24 ≤ fps ≤ 60
- 3.0 ≤ duration ≤ 30.0

**Color Format**: Hex regex `^#[0-9a-fA-F]{6}$`

---

## Performance Considerations

**YAML Loading**:
- Lazy with caching: Theme only reloads if mtime changed
- `_resolved_cache` memoizes token resolution

**Preset I/O**:
- JSON serialization (fast)
- Filenames sanitized (lowercase, alphanumeric only)
- Thumbnails PNG-compressed (quality 80)

**Board Loading**:
- trimesh caches loaded meshes in memory
- Large STEP files may take 2-5 seconds on first load
- Consider progressive loading for future
