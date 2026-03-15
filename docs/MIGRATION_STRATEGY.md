# SpinRender Theme System Migration Strategy

## Overview

The SpinRender UI currently duplicates color constants across three class hierarchies. This document defines the step-by-step migration to a centralized theme system.

**No backward compatibility required** — the plugin is unreleased.

---

## Current State: The Problem

Color constants are defined independently in each class:

| Class | File | Colors Defined |
|-------|------|---------------|
| `SpinRenderPanel` | `main_panel.py:77-88` | 12 colors |
| `BaseStyledDialog` | `dialogs.py:17-20` | 4 colors (overlapping) |
| `AdvancedOptionsDialog` | `dialogs.py` | Inherits BaseStyledDialog |
| `SavePresetDialog` | `dialogs.py` | Inherits BaseStyledDialog |
| Individual controls | `custom_controls.py` | Inline per-widget |

**Notable inconsistency:** `BG_MODAL = wx.Colour(17, 17, 17)` in dialogs vs `BG_PAGE = wx.Colour(18, 18, 18)` in main panel — same role, different values.

---

## Dependency Graph

```
theme.py  (new — no dependencies)
    │
    ├──► custom_controls.py  (consumes theme colors + fonts)
    │         │
    │         └──► dialogs.py  (consumes theme + custom_controls)
    │                   │
    │                   └──► main_panel.py  (consumes all above)
    │
    └──► main_panel.py  (also consumes theme directly)
```

**File modification order (strict):**
1. `SpinRender/ui/theme.py` — create (no deps)
2. `SpinRender/ui/custom_controls.py` — update imports, remove inline colors
3. `SpinRender/ui/dialogs.py` — remove class-level color attrs, import theme
4. `SpinRender/ui/main_panel.py` — remove class-level color attrs, import theme
5. `SpinRender/ui/__init__.py` — expose `theme` in package namespace

---

## Phase 1: Create `SpinRender/ui/theme.py`

Create the centralized theme module. This is the **only file that defines colors**.

```python
# SpinRender/ui/theme.py
"""
SpinRender Design System — single source of truth for colors and typography.
All UI files import from here. Never define wx.Colour values elsewhere.
"""
import wx


# ---------------------------------------------------------------------------
# Color Palette
# ---------------------------------------------------------------------------

# Backgrounds
BG_PAGE    = wx.Colour(18,  18,  18)   # outermost page/window bg
BG_PANEL   = wx.Colour(26,  26,  26)   # side panel, scrolled areas
BG_INPUT   = wx.Colour(13,  13,  13)   # text inputs, numeric inputs
BG_SURFACE = wx.Colour(34,  34,  34)   # raised surfaces, cards
BG_MODAL   = wx.Colour(18,  18,  18)   # modal dialog background (unified)

# Text
TEXT_PRIMARY   = wx.Colour(224, 224, 224)
TEXT_SECONDARY = wx.Colour(119, 119, 119)
TEXT_MUTED     = wx.Colour(85,  85,  85)

# Accents
ACCENT_CYAN   = wx.Colour(0,   188, 212)  # primary accent / interactive
ACCENT_YELLOW = wx.Colour(255, 214, 0)    # secondary / highlights
ACCENT_GREEN  = wx.Colour(76,  175, 80)   # success / info
ACCENT_ORANGE = wx.Colour(255, 107, 53)   # warnings / badges

# Structure
BORDER_DEFAULT = wx.Colour(31, 31, 31)   # dividers, control borders
BORDER_MODAL   = wx.Colour(51, 51, 51)   # dialog chrome borders

# State
DISABLED_ALPHA = 128   # 50% opacity for disabled widgets


# ---------------------------------------------------------------------------
# Typography
# ---------------------------------------------------------------------------

FONT_MONO   = "JetBrains Mono"
FONT_ICONS  = "Material Design Icons"
FONT_DISPLAY = "Oswald"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def disabled(color: wx.Colour) -> wx.Colour:
    """Return a copy of *color* at disabled opacity."""
    return wx.Colour(color.Red(), color.Green(), color.Blue(), DISABLED_ALPHA)
```

**Key decisions:**
- `BG_MODAL` unified to `(18, 18, 18)` — matches `BG_PAGE`, eliminates the 17 vs 18 inconsistency
- `BORDER_MODAL` set to `(51, 51, 51)` — matches current dialog value
- `disabled()` function replaces the `_get_paint_color()` helper in `custom_controls.py`

---

## Phase 2: Update `custom_controls.py`

### 2a — Replace font constants and `_get_paint_color`

**Before** (`custom_controls.py:10-13, 63-68`):
```python
# Font Families
_JETBRAINS_MONO = "JetBrains Mono"
_MDI_FONT_FAMILY = "Material Design Icons"
_OSWALD = "Oswald"

# ...

def _get_paint_color(color, enabled=True):
    """Helper to apply alpha if component is disabled."""
    if not enabled:
        return wx.Colour(color.Red(), color.Green(), color.Blue(), 128)
    return color
```

**After**:
```python
from . import theme

# Font Families — consumed from theme
_JETBRAINS_MONO  = theme.FONT_MONO
_MDI_FONT_FAMILY = theme.FONT_ICONS
_OSWALD          = theme.FONT_DISPLAY


def _get_paint_color(color, enabled=True):
    """Helper to apply alpha if component is disabled."""
    return theme.disabled(color) if not enabled else color
```

### 2b — Update per-widget hardcoded colors

Each custom widget currently uses ad-hoc `wx.Colour(...)` calls inline. Replace with theme references.

**Before** (example from `CustomSlider`):
```python
class CustomSlider(wx.Panel):
    def on_paint(self, event):
        gc = wx.GraphicsContext.Create(dc)
        # Track background
        gc.SetBrush(gc.CreateBrush(wx.Brush(wx.Colour(34, 34, 34))))
        # Handle
        gc.SetBrush(gc.CreateBrush(wx.Brush(wx.Colour(0, 188, 212))))
```

**After**:
```python
from . import theme

class CustomSlider(wx.Panel):
    def on_paint(self, event):
        gc = wx.GraphicsContext.Create(dc)
        # Track background
        gc.SetBrush(gc.CreateBrush(wx.Brush(theme.BG_SURFACE)))
        # Handle
        gc.SetBrush(gc.CreateBrush(wx.Brush(theme.ACCENT_CYAN)))
```

### 2c — Map for all 13 custom controls

| Control | Inline colors to replace |
|---------|-------------------------|
| `CustomSlider` | track bg → `BG_SURFACE`, handle → `ACCENT_CYAN`, text → `TEXT_PRIMARY` |
| `CustomToggleButton` | active fill → `ACCENT_CYAN`, inactive → `BG_SURFACE`, text → varies |
| `CustomDropdown` / `DropdownPopup` | bg → `BG_INPUT`, border → `BORDER_DEFAULT`, text → `TEXT_PRIMARY` |
| `CustomButton` | primary fill → `ACCENT_CYAN`, ghost border → `BORDER_DEFAULT`, danger → `ACCENT_ORANGE` |
| `PresetCard` | bg → `BG_SURFACE`, selected border → `ACCENT_CYAN`, text → `TEXT_PRIMARY` |
| `SectionLabel` | text → `TEXT_SECONDARY`, line → `BORDER_DEFAULT` |
| `NumericDisplay` | bg → `BG_INPUT`, text → `TEXT_PRIMARY` |
| `NumericInput` | bg → `BG_INPUT`, focused border → `ACCENT_CYAN`, text → `TEXT_PRIMARY` |
| `CustomTextInput` | bg → `BG_INPUT`, placeholder → `TEXT_MUTED`, text → `TEXT_PRIMARY` |
| `ProjectFolderChip` | bg → `ACCENT_ORANGE`, text → `BG_PAGE` |
| `CustomColorPicker` | border → `BORDER_DEFAULT`, input bg → `BG_INPUT` |
| `PathInputControl` | bg → `BG_INPUT`, icon → `TEXT_SECONDARY` |

---

## Phase 3: Update `dialogs.py`

### 3a — Remove class-level color attributes

**Before** (`dialogs.py:17-20`):
```python
class BaseStyledDialog(wx.Dialog):
    BG_MODAL = wx.Colour(17, 17, 17)
    BORDER_DEFAULT = wx.Colour(51, 51, 51)
    ACCENT_YELLOW = wx.Colour(255, 214, 0)
    TEXT_PRIMARY = wx.Colour(224, 224, 224)
    SHADOW_SIZE = 16
```

**After**:
```python
from . import theme

class BaseStyledDialog(wx.Dialog):
    SHADOW_SIZE = 16   # layout constant, not a color
```

### 3b — Update all color references inside `BaseStyledDialog`

**Before**:
```python
self.main_container.SetBackgroundColour(self.BG_MODAL)
```

**After**:
```python
self.main_container.SetBackgroundColour(theme.BG_MODAL)
```

### 3c — Update paint/draw methods in all dialogs

Replace every `self.BG_MODAL`, `self.BORDER_DEFAULT`, `self.ACCENT_YELLOW`, `self.TEXT_PRIMARY` reference with `theme.*` equivalents:

| Old reference | New reference |
|---------------|---------------|
| `self.BG_MODAL` | `theme.BG_MODAL` |
| `self.BORDER_DEFAULT` | `theme.BORDER_MODAL` |
| `self.ACCENT_YELLOW` | `theme.ACCENT_YELLOW` |
| `self.TEXT_PRIMARY` | `theme.TEXT_PRIMARY` |

---

## Phase 4: Update `main_panel.py`

### 4a — Remove class-level color attributes

**Before** (`main_panel.py:77-88`):
```python
class SpinRenderPanel(wx.Panel):
    BG_PAGE = wx.Colour(18, 18, 18)
    BG_PANEL = wx.Colour(26, 26, 26)
    BG_INPUT = wx.Colour(13, 13, 13)
    BG_SURFACE = wx.Colour(34, 34, 34)
    TEXT_PRIMARY = wx.Colour(224, 224, 224)
    TEXT_SECONDARY = wx.Colour(119, 119, 119)
    TEXT_MUTED = wx.Colour(85, 85, 85)
    ACCENT_CYAN = wx.Colour(0, 188, 212)
    ACCENT_YELLOW = wx.Colour(255, 214, 0)
    ACCENT_GREEN = wx.Colour(76, 175, 80)
    ACCENT_ORANGE = wx.Colour(255, 107, 53)
    BORDER_DEFAULT = wx.Colour(31, 31, 31)
```

**After**:
```python
from . import theme   # add to existing import block

class SpinRenderPanel(wx.Panel):
    # Colors removed — use theme.* directly
```

### 4b — Global find/replace in `main_panel.py`

| Old | New |
|-----|-----|
| `self.BG_PAGE` | `theme.BG_PAGE` |
| `self.BG_PANEL` | `theme.BG_PANEL` |
| `self.BG_INPUT` | `theme.BG_INPUT` |
| `self.BG_SURFACE` | `theme.BG_SURFACE` |
| `self.TEXT_PRIMARY` | `theme.TEXT_PRIMARY` |
| `self.TEXT_SECONDARY` | `theme.TEXT_SECONDARY` |
| `self.TEXT_MUTED` | `theme.TEXT_MUTED` |
| `self.ACCENT_CYAN` | `theme.ACCENT_CYAN` |
| `self.ACCENT_YELLOW` | `theme.ACCENT_YELLOW` |
| `self.ACCENT_GREEN` | `theme.ACCENT_GREEN` |
| `self.ACCENT_ORANGE` | `theme.ACCENT_ORANGE` |
| `self.BORDER_DEFAULT` | `theme.BORDER_DEFAULT` |

---

## Phase 5: Update `ui/__init__.py`

Expose the theme module so external code can import it cleanly:

```python
# SpinRender/ui/__init__.py
from . import theme
```

---

## Complete Before/After: A Full Control Migration

Here is a complete before/after for `SectionLabel` as a representative simple widget:

### Before
```python
class SectionLabel(wx.Panel):
    def __init__(self, parent, label):
        super().__init__(parent)
        self.label = label
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetMinSize((-1, 24))
        self.Bind(wx.EVT_PAINT, self.on_paint)

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        w, h = self.GetSize()

        # Background
        gc.SetBrush(gc.CreateBrush(wx.Brush(wx.Colour(26, 26, 26))))
        gc.DrawRectangle(0, 0, w, h)

        # Label text
        gc.SetFont(get_custom_font(9, weight=wx.FONTWEIGHT_BOLD),
                   wx.Colour(119, 119, 119))
        tw, th = gc.GetTextExtent(self.label)
        gc.DrawText(self.label, 0, (h - th) / 2)

        # Divider line
        line_x = tw + 8
        gc.SetPen(gc.CreatePen(wx.GraphicsPenInfo(wx.Colour(31, 31, 31))))
        gc.StrokeLine(line_x, h / 2, w, h / 2)
```

### After
```python
from . import theme

class SectionLabel(wx.Panel):
    def __init__(self, parent, label):
        super().__init__(parent)
        self.label = label
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetMinSize((-1, 24))
        self.Bind(wx.EVT_PAINT, self.on_paint)

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        w, h = self.GetSize()

        gc.SetBrush(gc.CreateBrush(wx.Brush(theme.BG_PANEL)))
        gc.DrawRectangle(0, 0, w, h)

        gc.SetFont(get_custom_font(9, weight=wx.FONTWEIGHT_BOLD),
                   theme.TEXT_SECONDARY)
        tw, th = gc.GetTextExtent(self.label)
        gc.DrawText(self.label, 0, (h - th) / 2)

        line_x = tw + 8
        gc.SetPen(gc.CreatePen(wx.GraphicsPenInfo(theme.BORDER_DEFAULT)))
        gc.StrokeLine(line_x, h / 2, w, h / 2)
```

---

## Verification Checklist

After completing all phases, verify:

- [ ] `grep -r "wx.Colour(" SpinRender/ui/` returns only `theme.py`
- [ ] No `self.BG_*`, `self.TEXT_*`, `self.ACCENT_*`, `self.BORDER_*` references remain in any file
- [ ] `from . import theme` present in `custom_controls.py`, `dialogs.py`, `main_panel.py`
- [ ] Plugin loads without errors in KiCad
- [ ] All controls render with correct colors
- [ ] Dialogs open and display correctly
- [ ] Disabled state opacity still works (via `theme.disabled()`)

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| BG_MODAL value change (17→18) | Visual: dialog bg shifts 1 RGB unit | Imperceptible; intentional unification |
| Missed inline `wx.Colour()` call | Widget renders wrong color | Grep check post-migration |
| Import cycle | Import error at startup | `theme.py` has zero internal imports |
| Font constant rename | `get_custom_font()` breaks | `_JETBRAINS_MONO` etc remain as local aliases |

---

## Phase 6: Semantic Aliases (Optional Future Enhancement)

After initial migration, introduce semantic alias constants for better readability:

```python
# In theme.py, add:
ACCENT_PRIMARY = ACCENT_CYAN   # main interactive color
ACCENT_SECONDARY = ACCENT_YELLOW  # highlights
ACCENT_SUCCESS = ACCENT_GREEN   # success states
ACCENT_WARNING = ACCENT_ORANGE  # warnings, badges
```

Update controls to use semantic names where appropriate:
- Buttons (primary) → `ACCENT_PRIMARY`
- Selected states → `ACCENT_PRIMARY`
- Danger/warning → `ACCENT_WARNING`
- Success indicators → `ACCENT_SUCCESS`

**Benefits**: Code intent becomes clearer than raw color names.

**Migration**: Simple find/replace in `custom_controls.py`, `dialogs.py`, `main_panel.py` after tests pass with current theme API.

