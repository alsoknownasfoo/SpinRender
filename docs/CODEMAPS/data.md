# Data Models, Configuration & Settings

<!-- Generated: 2026-03-25 | Files scanned: 30 Python modules | Token estimate: ~600 -->

## Core Data Structures

### RenderSettings (`SpinRender/core/settings.py:100`)

**Purpose**: Serializable configuration for a single render

**Fields** (dataclass):
```python
@dataclass
class RenderSettings:
    # Camera orientation (degrees)
    board_tilt: float = 0.0          # -90 to +90
    board_roll: float = -45.0        # -180 to +180
    spin_tilt: float = 90.0          # -90 to +90
    spin_heading: float = 90.0       # -180 to +180

    # Animation
    period: float = 10.0             # seconds, 3-30
    easing: str = 'linear'           # linear, ease_in, ease_out, etc.
    direction: str = 'ccw'           # cw or ccw

    # Lighting preset
    lighting: str = 'studio'         # studio, custom, etc.

    # Output
    format: str = 'mp4'              # mp4, gif
    resolution: str = '1920x1080'    # WxH
    bg_color: str = '#000000'        # hex color
    output_auto: bool = True         # auto-path from board
    output_path: str = ''            # manual override
    render_mode: str = 'both'        # wireframe, shaded, both

    # Advanced
    cli_overrides: str = ''          # extra Blender args
    logging_level: str = 'info'      # debug, info, warning, error
    theme_mode: str = 'system'       # dark, light, system
```

**Validation** (`__post_init__`):
- `board_tilt`: -90 ≤ value ≤ 90
- `board_roll`: -180 ≤ value ≤ 180
- `spin_tilt`: -90 ≤ value ≤ 90
- `spin_heading`: -180 ≤ value ≤ 180
- `period`: > 0 (3-30 typical)

**Serialization**:
- `to_dict() → dict` - all fields as JSON-compatible dict
- `from_dict(d: dict) → RenderSettings` - construct from dict (ignores extra keys)

---

### Theme Data Model

**Source**: YAML files (`resources/themes/*.yaml`)

**Structure** (high-level):
```yaml
name: "Dark"                   # Theme display name
version: 2                     # Theme schema version (optional)
description: "Dark theme"      # Human description

colors:
  auto_states:
    hover: rgb(60, 60, 60)      # Lighten for hover in dark mode
    active: rgb(-60, -60, -60)  # Darken for active
    disabled: rgb(0, 0, 0, 0.5) # 50% opacity

  # Base palette (raw values)
  gray-black:  "#0D0D0D"
  gray-dark:   "#121212"
  gray-div:    "#1A1A1A"
  gray-border: "#222222"
  gray-medium: "#444444"
  gray-light:  "#646464"
  gray-text:   "#777777"
  gray-white:  "#E0E0E0"

  # Accent colors
  cyan:   "#00BCD4"
  yellow: "#FFD600"
  green:  "#4CAF50"
  orange: "#FF6B35"
  red:    "#FF3B30"
  purple: "#AA6BFF"
  pink:   "#F240FF"

  # Tint variants (opacity-based)
  cyan-10:  "rgba(0, 188, 212, 0.1)"
  cyan-20:  "rgba(0, 188, 212, 0.2)"
  cyan-50:  "rgba(0, 188, 212, 0.5)"
  cyan-80:  "rgba(0, 188, 212, 0.8)"
  # ... similar for other accents

  # Semantic aliases
  primary:     "@colors.cyan"
  secondary:   "@colors.yellow"
  tertiary:    "@colors.purple"
  quaternary:  "@colors.pink"
  ok:          "@colors.green"
  warning:     "@colors.orange"
  error:       "@colors.red"

  # Brand colors (external services)
  brand:
    github-sponsors: "#ea4aaa"
    kofi:            "#29ABE0"
    ai:
      claude:  "#d97757"
      gemini:  "#3186FF"
      chatgpt: "#12a37f"
      copilot: "#7c3aed"

radius:
  none: 0
  sm:   4
  md:   6
  lg:   8
  full: 9999

borders:
  width:
    none:   0
    thin:   1
    medium: 2
  roles:
    default:  { size: "@borders.width.thin", color: "@colors.gray-border" }
    subtle:   { size: "@borders.width.thin", color: "@colors.gray-border" }
    button:   { size: "@borders.width.thin", color: "@colors.gray-medium" }
    focus:    { size: "@borders.width.thin", color: "@colors.primary" }
    strong:   { size: "@borders.width.medium", color: "@colors.primary" }

dividers:
  width:
    thin: 1
    medium: 2
  default:
    size: "@dividers.width.thin"
    color: "@colors.gray-div"

typography:
  families:
    mono:    "JetBrains Mono"
    display: "Oswald"
    icon:    "Material Design Icons"

  weights:
    hairline: 100
    thin:     200
    light:    300
    normal:   400
    medium:   500
    semibold: 600
    bold:     700
    extrabold: 800
    black:    900

  scale:
    xs: 7
    sm: 9
    base: 11
    md: 14
    lg: 18
    xl: 24
    icon: 16
    icon-lg: 20

  spacing:
    none: 0
    xs: 4
    sm: 6
    base: 10
    md: 16
    lg: 24

text:
  title:
    color: "@colors.gray-white"
    formatting: "uppercase"
    font:
      typeface: "@typography.families.display"
      size: "@typography.scale.lg"
      weight: "@typography.weights.bold"
  # ... 20+ more text roles (subtitle, header, body, button, label, etc.)

glyphs:
  render-action: "\U000F0A1C"
  settings:      "\U000F0493"
  trash:         "\U000F0A7A"
  # ... 50+ icon glyph mappings

layout:
  main:
    frame:   { bg: "@colors.gray-black", radius: "@radius.none" }
    header:  { bg: "@colors.gray-black", title: "@text.title", subtitle: "@text.subtitle" }
    leftpanel:
      width: 450
      headers: "@text.header"
      body: "@text.body"
      padding: 16
      control:
        heading_gap: "@typography.spacing.sm"
        description_gap: "@typography.spacing.xs"
        between_items: "@typography.spacing.base"
      border: "@borders.default"
    divider: { bg: "@dividers.default.color", size: 1 }
    rightpanel:
      bg: "@colors.black"
      title: "@text.title"
    status: "@components.status"

  dialogs:
    default:
      frame: { width: 600, height: 500, bg: "@colors.gray-dark", radius: "@radius.md" }
      header: { bg: "@colors.gray-black", border: "@borders.default", height: 48 }
      body: { padding: { all: "@typography.spacing.lg" }, text: "@text.body" }
      # ... more dialog layouts

components:
  # Reusable UI component specifications
  preset_card:
    default:
      frame: { width: 90, height: 64, bg: { default: "@colors.gray-div", hover: "@colors.cyan-80" }, radius: "@radius.lg" }
      icon:  { ref: "@text.icon_lg", color: { default: "@colors.gray-light", hover: "@colors.gray-dark" } }
      label: { ref: "@text.button", color: { default: "@colors.gray-light", hover: "@colors.gray-dark" } }

  input:
    default:
      frame: { height: 32, bg: "@colors.gray-black", radius: "@radius.md" }
      label: { ref: "@text.numeric" }
      color: { default: "@colors.gray-light", hover: "@colors.primary" }
    path:
      ref: "@components.input.default"
      frame: { height: 36 }
      icon: { ref: "glyphs.folder", color: "@colors.primary" }

  slider:
    default:
      track: { frame: { height: 8, radius: "@radius.sm" }, color: "@colors.gray-border" }
      nub:   { width: 1, height: 14, color: "@colors.primary" }
      # ... variants: primary (yellow), secondary (orange), etc.

  button:
    default:
      frame: { height: 36, bg: { default: "@colors.gray-div", hover: "#00B2CA" }, radius: "@radius.md" }
      label: { ref: "@text.button", color: { default: "@colors.gray-light", hover: "@colors.black" } }
    ok:
      ref: "@components.button.default"
      frame: { bg: "#00B2CA" }
      label: { color: "@colors.black" }
    # ... variants: cancel, close, render, options, about, etc.

  toggle:
    default:
      frame: { height: 32, radius: "@radius.md", bg: "@colors.gray-div" }
      items:
        frame: { bg: { default: "transparent", hover: "@colors.primary", active: "@colors.primary" } }
        icon:  { ref: "@text.icon", color: { default: "@colors.gray-light", hover: "@colors.gray-dark" } }
        label: { ref: "@text.label", color: { default: "@colors.gray-light", hover: "@colors.gray-dark" } }

  dropdown:
    default:
      frame: { height: 32, bg: "transparent", radius: "@radius.md" }
      label: { font: "@text.numeric.font", color: "@colors.gray-light" }
      icon:  { ref: "@text.icon", color: "@colors.gray-light" }
      menu:
        frame: { bg: "@colors.gray-dark", radius: "@radius.md" }
        items: { bg: "transparent", hover: "@colors.cyan-20", active: "@colors.primary" }

  colorpicker:
    default:
      bg: "transparent"
      border: "@borders.subtle"
      label: { font: { typeface: "mono", size: "sm", weight: "semibold" }, color: "@colors.gray-light" }
      items:
        innerborder: { size: 1, color: { default: "@colors.gray-black", hover: "@colors.red" } }
        border:       { size: 2, color: "@colors.gray-border" }

  status:
    default:  { bg: "@colors.gray-black", label: { ref: "@text.status", color: "@colors.gray-white" } }
    ready:    { bg: "@colors.gray-black", label: { ref: "@text.status", color: "@colors.ok" } }
    progress: { bg: "@colors.primary", label: { ref: "@text.status", color: "@colors.gray-black" } }
    complete: { bg: "@colors.gray-black", label: { ref: "@text.status", color: "@colors.ok" } }
    error:    { bg: "@colors.gray-black", label: { ref: "@text.status", color: "@colors.error" } }

  scrollbar:
    track:   { frame: { bg: "transparent" } }
    thumb:   { frame: { bg: "@colors.gray-medium", radius: "full" } }
```

**Token Resolution**:
Theme supports:
1. Direct: `"#rrggbb"`, `"rgba(r,g,b,a)"`, `"white"` (named color)
2. Reference: `"@colors.primary"` or `"ref: colors.primary"`
3. Function: `"func: darken(colors.bg, 0.1)"`
4. Composition: `"mix(colors.bg, colors.fg, 0.5)"`

**Resolved by**: `Theme._resolve(path)` with circular reference detection and parent inheritance.

---

## Preset Storage Format

### Directory Layout
```
~/.spinrender/presets/           (global presets)
  hero.json
  spin.json
  flip.json

{board_dir}/.spinrender/         (project presets)
  custom_shots.json
  lighting_test.json
```

### JSON Structure
```json
{
  "name": "hero",
  "created_at": "2026-03-20T14:30:00Z",
  "is_global": false,
  "settings": {
    "board_tilt": 0.0,
    "board_roll": -45.0,
    "spin_tilt": 90.0,
    "spin_heading": 90.0,
    "period": 10.0,
    "easing": "linear",
    "direction": "ccw",
    "lighting": "studio",
    "format": "mp4",
    "resolution": "1920x1080",
    "bg_color": "#000000",
    "output_auto": true,
    "output_path": "",
    "render_mode": "both",
    "logging_level": "info",
    "theme_mode": "system"
  }
}
```

**Schema Version**: Implicit v1 (flat RenderSettings fields)
**Backwards Compat**: `RenderSettings.from_dict()` ignores extra keys.

---

## Locale Strings

### Locale Files
```
SpinRender/resources/locale/
├── en.yaml        # Base English strings
├── en_US.yaml     # US English (formats, variants)
└── en_US_COMPLETE.yaml  # Generated full locale (all keys)
```

### YAML Structure
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
      status:
        ready: "Ready"
        preparing: "Preparing render..."
        rendering: "Rendering frame {current}/{total}"
        complete: "RENDER COMPLETE"
        error: "Error: {message}"
        stopped: "Render stopped"
    dialog:
      title:
        preset_save: "Save Preset"
        advanced: "Advanced Options"
        about: "About SpinRender"
      button:
        ok: "OK"
        cancel: "Cancel"
        save: "Save"
    # ... 100+ more keys
```

**Interpolation**: `_locale.get("component.status.rendering", current=12, total=60)` → `"Rendering frame 12/60"`

**Fallback**: If key missing, returns `"???" + key` for visibility.

---

## KiCad Configuration Schema

### Action Plugin JSON (v9.0 and v10.0)

**Location**: `SpinRender/resources/kicad_config/{version}/`

**Files per version** (7 total):
- `kicad.json` - Main PCB editor (pcbnew)
- `3d_viewer.json` - 3D viewer toolbar
- `eeschema.json` - Schematic editor
- `fpedit.json` - Footprint editor
- `pcbnew.json` - PCB editor (legacy, v9 only)
- `cvpcb.json` - Footprint assigner
- `kicad_common.json` - Shared config

**Example** (`10.0/pcbnew.json`):
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
- `icon`: Relative path to icon file (in plugin directory)
- `class`: Python class name to instantiate (`SpinRenderPlugin`)
- `shortcut`: Optional keyboard shortcut
- `tooltip`: Hover tooltip
- `menu_item`: Show in menu bar (true/false)
- `menu_path`: Menu hierarchy (e.g., "Tools/Render")
- `toolbar`: Show in toolbar (true/false)
- `toolbar_id`: Toolbar group identifier
- `visibility`: "always", "pcbnew", "footprint_editor", etc.

**Version Differences**:
- KiCad 9.0: Uses `"kicad.json"` for main app; `"pcbnew.json"` is primary
- KiCad 10.0: Updated schema with `toolbar_id`, `visibility`; unified under `pcbnew.json`

---

## Board Loader Data Flow

**Input**: `.kicad_pcb` file path (from KiCad API)

**Process**:
1. Parse KiCad PCB using `pcbnew` API
   - Get board object: `board = pcbnew.GetBoard()`
   - Traverse footprints: `board.GetFootprints()`
2. For each footprint, extract 3D model references (`Get3DModel()`)
3. For each 3D model:
   - Resolve model path (STEP/STL/OBJ/WRL)
   - Load via `trimesh.load(path)`
   - Apply footprint transform (position, rotation)
   - Merge into single `trimesh.Scene`
4. Build final `trimesh.Scene` with all board meshes
5. Provide to `GLPreviewRenderer` for OpenGL display

**Caching**:
- Board geometry cached in memory (per session, in `GLPreviewRenderer.scene`)
- Thumbnails cached on disk (`~/.spinrender/cache/thumbnails/`)

**Performance**:
- Large STEP files: 2-5s initial load
- Subsequent loads: cached meshes → instant
- Consider: progressive loading for future (LOD)

---

## Preset Thumbnail Cache

**Location**: `~/.spinrender/cache/thumbnails/`

**Naming**: `{preset_hash}.png`
- Hash = SHA256(preset_name + RenderSettings JSON sorted keys)

**Generation**:
- On preset save: render single frame at 200×150
- Save PNG to thumb cache (quality 80)
- Associate with preset via hash lookup

**Invalidation**:
- If thumbnail missing → regenerate on demand
- If preset settings changed → new hash, new file
- Old thumbnails evicted via LRU (optional cleanup)

---

## Settings Persistence (UI State)

**Non-preset UI state** (between sessions):

| Setting | Path | Format |
|---------|------|--------|
| Last board | `~/.spinrender/last_board.json` | `{ "path": "/.../board.kicad_pcb" }` |
| Window geometry | `~/.spinrender/window_geometry.json` | `{ "x": 100, "y": 100, "w": 1200, "h": 800 }` |
| Last preset | `~/.spinrender/last_preset.json` | `{ "name": "hero", "is_global": true }` |
| Theme preference | `~/.spinrender/theme.json` | `{ "mode": "dark" }` |

**Format**: Single-key JSON files for easy merge.

**Loading**:
- On startup: `SpinRenderPanel.__init__()` reads these files
- Overrides default settings if files exist

---

## Configuration Hierarchy

```
┌─────────────────────────────────────────────┐
│  CLI Arguments / Environment Variables     │  (highest priority)
└─────────────────┬───────────────────────────┘
                  ↓
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
- CLI args override everything (parsed in `main_panel` if present)
- Loaded preset fills session settings on recall
- If no preset recalled → defaults used
- UI changes update session settings only
- Save to preset writes current session state to JSON
- `save_settings()` writes `last_used_settings.json` (non-preset)

---

## Schema Versioning & Migrations

### Theme Schema Versioning
- Theme YAML may include `version: 2`
- If missing → assume v1
- Migration: None - validation fails if incompatible
- Strategy: Add new keys as optional; maintain backward-compatible resolution

### Preset Schema Versioning
- Preset JSON may include `"schema_version": 1` (optional)
- Backward compatibility: `RenderSettings.from_dict()` ignores extra fields
- Forward compatibility: Newer app works with old presets (missing fields → defaults)
- Migration: Not needed; additive changes only

### KiCad Config Versioning
- Separate directories: `resources/kicad_config/9.0/` and `10.0/`
- Plugin auto-detects KiCad version at runtime
  - `import pcbnew; version = pcbnew.GetMajorVersion()`
- Loads matching config files
- No migration; both versions coexist

---

## Validation Rules

### Theme Validation (`validation.py:250`)

**Checks**:
1. **Required sections**: `colors`, `typography`, `layout`
2. **Color format**: Hex `#rrggbb` or `rgba(r,g,b,a)` or reference `@path`
3. **Circular references**: Detect A → B → A in token graph
4. **Missing references**: `ref: colors.missing` must exist somewhere
5. **Function syntax**: `func: name(args)` with valid function name
6. **Type checking**: colors are strings, layout/spacing are numeric

**Output**: `ValidationReport` with `errors`, `warnings`, `infos`

**CLI**: `python -m SpinRender.validation path/to/theme.yaml`

---

### Settings Validation

**Method**: `RenderSettings.validate() → list[str]`

**Ranges**:
- `board_tilt`, `spin_tilt`: -90 to +90
- `board_roll`, `spin_heading`: -180 to +180
- `period`: 3.0 to 30.0 seconds
- `resolution`: parse `WxH` → 320 ≤ W,H ≤ 4096
- `format`: one of `"mp4"`, `"gif"`
- `bg_color`: hex color regex `^#[0-9a-fA-F]{6}$`

**UI Enforcement**: Sliders bound to ranges; invalid values clamped.

---

### Preset Name Validation

**Rules**:
- Sanitized: lowercase alphanumeric + underscores only
- Max length: 64 characters
- Reserved names: `"hero"`, `"spin"`, `"flip"` (built-in, read-only)

**Enforcement**: `PresetManager._sanitize_name(name)` strips invalid chars.

---

## Performance Considerations

**YAML Loading**:
- Lazy with mtime-based caching
- `Theme._resolved_cache` memoizes token resolution per session
- Cache cleared on `Theme.reload()`

**Preset I/O**:
- JSON serialization (fast, builtin)
- Filename sanitization (lowercase, underscores)
- Thumbnail PNG compression (quality 80)

**Board Loading**:
- `trimesh` caches loaded meshes in memory (`scene_cache`)
- Large STEP files may take 2-5 seconds on first load (disk + parsing)
- Subsequent loads: instant (from trimesh cache)
- Consider: background loading thread for future

**Rendering**:
- Blender runs as separate subprocess (no GIL contention)
- Progress reported via stdout pipe (frame count)
- UI updates via `wx.CallAfter()` (thread-safe)
- Preview frames: PNG → `wx.Image` → `wx.Bitmap` (GPU upload)

**Hot-Reload**:
- Theme: file mtime check every 1s (timer)
- Locale: same mechanism
- Mtime check cheap (stat syscall); full reapply ~10ms for 40 controls
