# SpinRender UI Analysis

**Date:** 2026-03-13
**Scope:** `SpinRender/ui/` — `main_panel.py`, `custom_controls.py`, `dialogs.py`

---

## 1. File Inventory

| File | Lines | Classes | Methods | Colors |
|------|-------|---------|---------|--------|
| `main_panel.py` | 1,543 | 2 | 64 | 28 |
| `custom_controls.py` | ~1,250 | 10+ | ~80 | 69 (37 class-level + 32 inline) |
| `dialogs.py` | 474 | 4 | 23 | 18 |
| **Total** | **~3,267** | **16** | **~167** | **~115** |

---

## 2. Component Map

### main_panel.py

```
SVGLogoPanel(wx.Panel)          — logo renderer only
SpinRenderPanel(wx.Panel)       — GOD CLASS (1,470 lines, 64 methods)
  ├── build_ui()
  ├── create_controls_panel()   — left sidebar
  │   ├── create_header()
  │   ├── create_preset_section()
  │   ├── create_parameters_section()
  │   │   ├── create_rotation_controls()
  │   │   │   └── create_axis_control() × 4
  │   │   ├── create_period_control()
  │   │   ├── create_direction_control()
  │   │   └── create_lighting_control()
  │   └── create_output_settings_section()
  │       └── create_export_section()
  ├── create_preview_panel()    — right panel (viewport + overlays)
  ├── create_status_bar()
  ├── [64 event handlers + state methods]
  └── [playback: start_playback, stop_playback, on_playback_timer]
```

### custom_controls.py

```
ensure_fonts_loaded()           — module-level font loader
get_custom_font() / get_mdi_font() — font helpers

CustomSlider(wx.Panel)          — drag slider with custom paint
CustomToggleButton(wx.Panel)    — 2+ state toggle
DropdownPopup(wx.PopupTransientWindow)
CustomDropdown(wx.Panel)        — dropdown with popup
CustomButton(wx.Panel)          — styled button w/ icon support
SectionLabel(wx.Panel)          — section header label
NumericDisplay(wx.Panel)        — read-only value + unit
NumericInput(wx.Panel)          — editable value + unit
CustomTextInput(wx.Panel)       — text field w/ placeholder
ProjectFolderChip(wx.Panel)     — folder path chip
CustomColorPicker(wx.Panel)     — hex color input + swatch
PathInputControl(wx.Panel)      — file path input w/ browse
```

### dialogs.py

```
BaseStyledDialog(wx.Dialog)     — dark-themed base, draggable
AdvancedOptionsDialog(BaseStyledDialog)  — output path, logging, render opts
SavePresetDialog(BaseStyledDialog)       — name input
RecallPresetDialog(BaseStyledDialog)     — preset list with delete
```

---

## 3. Dependency Graph

```
spinrender_plugin.py
  └── ui/main_panel.py (SpinRenderPanel)
        ├── ui/custom_controls.py  [top-level import]
        ├── core/preview.py        [top-level import]
        ├── core/renderer.py       [LATE import ×3, inside methods]
        ├── core/presets.py        [LATE import ×4, inside methods]
        ├── ui/dialogs.py          [LATE import ×2, inside methods]
        ├── ui/custom_controls.py  [LATE import ×3 redundant, inside methods]
        └── utils/logger.py        [LATE import ×2, inside methods]

ui/dialogs.py
        ├── ui/custom_controls.py  [top-level + 4 late imports]
        ├── core/presets.py        [LATE import ×2]
        └── utils/logger.py        [LATE import ×1]

ui/custom_controls.py
        └── (no internal SpinRender imports — leaf node ✓)
```

**Late import count:** 14 in `main_panel.py`, 7 in `dialogs.py` = **21 total deferred imports**

---

## 4. Coupling Issues

### 4.1 God Class — `SpinRenderPanel` (CRITICAL)

`SpinRenderPanel` at 1,470 lines / 64 methods handles six distinct concerns:

| Concern | Methods |
|---------|---------|
| Layout construction | `build_ui`, `create_*` (14 methods) |
| Settings state | `self.settings` dict (94 direct accesses) |
| Render coordination | `on_render_click`, `on_stop_click`, `_on_render_thread` |
| Preset management | `on_preset_*`, `on_recall_preset`, `on_save_preset` |
| Playback state | `start_playback`, `stop_playback`, `on_playback_timer` |
| Preview/overlay | `update_preview_overlay`, `_on_render_preview_paint`, `enable_left_panel_controls` |

### 4.2 Untyped Settings Dict (HIGH)

`self.settings` is a raw `dict` with 94 access sites using bare string keys:
```python
self.settings['board_tilt']
self.settings.get('format', 'mp4')
self.settings['spin_heading']
```
No schema, no validation, no IDE completion. A typo in any key silently returns `None`.

### 4.3 Scattered Color Palette (HIGH)

20 unique RGB values are redefined as class constants **37 times** across 3 files and 8+ classes. The same 8 core palette entries appear in every widget:

| Color | RGB | Redefined |
|-------|-----|-----------|
| Background dark | `(13, 13, 13)` | 11× |
| Accent cyan | `(0, 188, 212)` | 9× |
| Border | `(51, 51, 51)` | 8× |
| Text primary | `(224, 224, 224)` | 5× |
| Text secondary | `(119, 119, 119)` | 4× |
| Text muted | `(85, 85, 85)` | 3× |
| Accent yellow | `(255, 214, 0)` | 3× |
| BG panel | `(26, 26, 26)` | 2× |

Additional 32 **inline** `wx.Colour(...)` literals are scattered throughout paint handlers and layout code.

### 4.4 Deferred Imports (MEDIUM)

21 imports inside method bodies — originally to work around circular imports — now obscure the real dependency structure and prevent static analysis:

```python
# L987 — inside on_render_click
from core.renderer import RenderEngine
# L1068 — inside another method, same import
from core.renderer import RenderEngine
```

`RenderEngine` is imported 3× in separate methods. Same pattern for `PresetManager` (4×) and `SpinLogger` (2×).

### 4.5 `custom_controls.py` Monolith (MEDIUM)

~1,250 lines containing 10+ unrelated widget classes. Changes to `CustomSlider` require opening the same file as `CustomColorPicker`. The file has no internal structure separating widget families.

### 4.6 Mixed Import Styles (LOW)

`main_panel.py` uses both `from ui.custom_controls import ...` (absolute, KiCad-compatible) and `from .custom_controls import ...` (relative) in different method bodies, indicating inconsistent patching over time.

---

## 5. Prioritized Refactoring Plan

### Priority 1 — Central Theme System *(Foundation for everything else)*

**Complexity:** Low | **Impact:** High | **Risk:** Low

Create `ui/theme.py` as the single source of truth:

```python
# ui/theme.py
import wx

class Theme:
    # Backgrounds
    BG_PAGE    = wx.Colour(18, 18, 18)
    BG_PANEL   = wx.Colour(26, 26, 26)
    BG_INPUT   = wx.Colour(13, 13, 13)
    BG_SURFACE = wx.Colour(34, 34, 34)
    # Text
    TEXT_PRIMARY   = wx.Colour(224, 224, 224)
    TEXT_SECONDARY = wx.Colour(119, 119, 119)
    TEXT_MUTED     = wx.Colour(85, 85, 85)
    # Borders
    BORDER_DEFAULT = wx.Colour(51, 51, 51)
    # Accents
    ACCENT_CYAN   = wx.Colour(0, 188, 212)
    ACCENT_YELLOW = wx.Colour(255, 214, 0)
    ACCENT_GREEN  = wx.Colour(76, 175, 80)
    ACCENT_ORANGE = wx.Colour(255, 107, 53)
```

Then replace all class-level color constants with `from ui.theme import Theme` and use `Theme.BG_INPUT` etc.

**Files affected:** `main_panel.py`, `custom_controls.py`, `dialogs.py`
**Estimated LOC removed:** ~115 color definitions → 1 module

---

### Priority 2 — Settings Dataclass *(Eliminates silent key errors)*

**Complexity:** Medium | **Impact:** High | **Risk:** Low

Replace `self.settings: dict` with a typed dataclass:

```python
# core/settings.py
from dataclasses import dataclass, field

@dataclass
class RenderSettings:
    board_tilt: float = 0.0
    board_roll: float = 0.0
    spin_tilt: float = 15.0
    spin_heading: float = 0.0
    period: float = 10.0
    direction: str = 'ccw'
    lighting: str = 'studio'
    format: str = 'mp4'
    resolution: str = '1920x1080'
    bg_color: str = '#000000'
    render_mode: str = 'both'
    preset: str = ''
    logging_level: str = 'simple'
    # ... etc
```

**Files affected:** `main_panel.py` (94 accesses), `dialogs.py`

---

### Priority 3 — Split `SpinRenderPanel` *(Eliminates god class)*

**Complexity:** High | **Impact:** High | **Risk:** Medium

Extract focused panel/controller classes from `SpinRenderPanel`:

| New Class | Responsibility | Est. Lines |
|-----------|---------------|------------|
| `ControlsSidePanel` | Left sidebar layout + controls | ~400 |
| `PreviewPanel` | Viewport + overlays + playback | ~250 |
| `RenderController` | Render thread, stop, status updates | ~150 |
| `PresetController` | Load/save/recall presets | ~100 |
| `SpinRenderPanel` (residual) | Wires the above together | ~200 |

`SpinRenderPanel` becomes a coordinator that holds instances of the above, reducing it from 1,470 lines to ~200.

---

### Priority 4 — Fix Deferred Imports *(Enables static analysis)*

**Complexity:** Low | **Impact:** Medium | **Risk:** Low

Move all late imports to module top-level. The circular-import concern that originally caused this is likely resolved once the god class is split (Priority 3). For now, consolidate duplicate imports:

- `RenderEngine`: 3 method-level imports → 1 top-level
- `PresetManager`: 4 method-level imports → 1 top-level
- `SpinLogger`: 2 method-level imports → 1 top-level

Also standardize on absolute imports (`from ui.custom_controls`) throughout.

---

### Priority 5 — Split `custom_controls.py` *(Improves navigability)*

**Complexity:** Low | **Impact:** Medium | **Risk:** Low

Split by widget family:

```
ui/
  custom_controls.py      → re-exports all (backwards compat shim)
  controls/
    __init__.py
    fonts.py              — ensure_fonts_loaded, get_custom_font, get_mdi_font
    slider.py             — CustomSlider
    toggle.py             — CustomToggleButton
    button.py             — CustomButton
    dropdown.py           — CustomDropdown, DropdownPopup
    numeric.py            — NumericDisplay, NumericInput
    text_input.py         — CustomTextInput, PathInputControl
    color_picker.py       — CustomColorPicker
    labels.py             — SectionLabel, ProjectFolderChip
```

The existing `from ui.custom_controls import X` imports in `main_panel.py` remain valid through the shim.

---

## 6. Refactoring Sequence

```
Phase 1 (no breakage risk)
  [P1] Create ui/theme.py
  [P1] Update all 3 files to reference Theme.*
  [P2] Create core/settings.py dataclass
  [P4] Consolidate duplicate late imports

Phase 2 (moderate risk, test after each)
  [P2] Migrate main_panel.py + dialogs.py to RenderSettings
  [P5] Split custom_controls.py into controls/ package

Phase 3 (high complexity, requires tests)
  [P3] Extract PreviewPanel
  [P3] Extract RenderController
  [P3] Extract PresetController
  [P3] Extract ControlsSidePanel
  [P3] Slim SpinRenderPanel to coordinator
```

---

## 7. Quick Wins (< 1 hour each)

1. **`ui/theme.py`** — creates the palette in one file, zero behaviour change
2. **Consolidate `RenderEngine` imports** — remove 2 redundant method-level imports
3. **`SVGLogoPanel` → `ui/logo.py`** — trivial extraction, reduces `main_panel.py` by 44 lines
4. **Inline color literals in paint handlers** — replace `wx.Colour(255, 255, 255, 30)` → `Theme.BORDER_GHOST` etc.
5. **`create_section_label` duplication** — identical method exists in both `SpinRenderPanel` and `AdvancedOptionsDialog`; extract to a shared utility function
