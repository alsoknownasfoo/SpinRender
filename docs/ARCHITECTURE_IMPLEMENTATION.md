# Comprehensive Architecture Implementation Plan

**Non-Theme Refactoring for SpinRender UI**
_Aligns with UI_REFACTOR.md and integrates with MIGRATION_STRATEGY.md_

---

## Executive Summary

This plan addresses eight critical architectural improvements that complement the theme system migration. The theme migration (docs/MIGRATION_STRATEGY.md) should be completed **first** as it provides the foundation for these refactorings. All non-theme work can proceed in parallel with or after theme migration, with dependencies clearly noted.

**Total Estimated Scope:** ~2000 lines of refactoring across 8 subsystems
**Priority Order:** Based on dependency chain and risk profile

---

## 1. Typography System

**Status:** Post-theme-migration enhancement
**Dependencies:** Theme system (for font definitions), custom_controls.py
**Risk:** LOW | **Impact:** HIGH

### Objective

Replace ad-hoc font creation with a `TextStyle` class that encapsulates family, size, weight, and formatting behavior. Support semantic token resolution, override precedence, and automatic case transformation.

### Current State

- Fonts created inline via `get_custom_font(size, weight, family)` throughout 13 custom controls
- Duplicate font specifications (e.g., `wx.Font(9, ..., "JetBrains Mono")` in multiple places)
- No centralized control of font scales or weight mappings
- Manual uppercase transformation in some headers

### Proposed Design

```python
# ui/text_styles.py (new module)
from dataclasses import dataclass
from typing import Optional, Callable
from .theme import Theme

@dataclass(frozen=True)
class TextStyle:
    """Immutable text style specification."""
    family: str
    size: int
    weight: int  # wx.FONTWEIGHT_*
    italic: bool = False
    transform: Optional[Callable[[str], str]] = None  # e.g., str.upper

    def apply(self, text: str) -> str:
        """Apply formatting transformation if specified."""
        return self.transform(text) if self.transform else text

    def to_wx_font(self) -> wx.Font:
        """Create wx.Font instance."""
        from .custom_controls import get_custom_font
        return get_custom_font(
            size=self.size,
            family_name=self.family,
            weight=self.weights
        )

class TextStyleResolver:
    """Resolves text styles from semantic tokens with override precedence."""

    PRECEDENCE_ORDER = [
        "component_override",  # passed to component constructor
        "theme_preset",         # from theme.yaml typography.presets
        "theme_default",        # theme fallback
        "system_default"        # last resort
    ]

    def __init__(self, theme: Theme):
        self.theme = theme
        self._cache = {}

    def resolve(self, token: str, override: Optional[TextStyle] = None) -> TextStyle:
        """Resolve style with precedence: override > token > default."""
        if override:
            return override

        # Token format: "typography.presets.body"
        if token in self._cache:
            return self._cache[token]

        spec = self.theme.resolve_font_spec(token)
        style = TextStyle(
            family=spec['family'],
            size=spec['size'],
            weight=spec['weight']
        )
        self._cache[token] = style
        return style
```

### Implementation Phases

#### Phase 1: Create `ui/text_styles.py`

**File:** `/Users/foo/Code/SpinRender_claude/SpinRender/ui/text_styles.py`

**Changes:**
1. Define `TextStyle` dataclass
2. Implement `TextStyleResolver` with token resolution
3. Add built-in transformations: `uppercase()`, `lowercase()`, `capitalize()`
4. Create default style registry (maps common tokens to styles)

**Before/After Example:**

**Before (`custom_controls.py` - SectionLabel):**
```python
class SectionLabel(wx.Panel):
    def on_paint(self, event):
        gc.SetFont(get_custom_font(9, weight=wx.FONTWEIGHT_BOLD),
                   wx.Colour(119, 119, 119))
        gc.DrawText(self.label.upper(), ...)  # manual uppercase
```

**After:**
```python
from .text_styles import TextStyleResolver, uppercase

class SectionLabel(wx.Panel):
    def __init__(self, parent, label, style_token="typography.presets.label-sm"):
        super().__init__(parent)
        self.label_text = label
        self.style_resolver = TextStyleResolver(Theme.current())
        self.style_token = style_token
        self.text_transform = uppercase  # declarative

    def on_paint(self, event):
        style = self.style_resolver.resolve(self.style_token)
        font = style.to_wx_font()
        gc.SetFont(font, theme.TEXT_SECONDARY)
        display_text = style.apply(self.label_text)
        gc.DrawText(display_text, ...)
```

#### Phase 2: Update Custom Controls (All 13)

**Modification Order:**

1. **CustomSlider** (simple, ~150 lines)
   - Add `style_token` parameter for tick label style
   - Replace `get_custom_font(9)` with `resolver.resolve("typography.presets.label-xs")`

2. **CustomToggleButton** (~200 lines)
   - Add style tokens for option labels and icons
   - Use `label-sm` for option text

3. **CustomDropdown** (~250 lines)
   - Apply `body` style to dropdown items
   - Use `label-sm` for placeholder

4. **PresetCard** (~180 lines)
   - `label-sm` for card title
   - `icon` for preset icon

5. **NumericDisplay** (~120 lines)
   - `numeric-value` for value text
   - `numeric-unit` for unit label

6. **NumericInput** (~200 lines)
   - `body` for input text

7. **CustomButton** (~300 lines)
   - `body-strong` for button label
   - Support optional `style_override` param

8. **SectionLabel** (~80 lines)
   - `label-sm` base
   - Built-in uppercase transformation

9. **PathInputControl** (~100 lines)
   - `body` for path text
   - `label-sm` for placeholder

10. **ProjectFolderChip** (~60 lines)
    - `label-xs` for chip text (bold)

11. **CustomColorPicker** (~150 lines)
    - No text changes needed

12. **CustomTextInput** (~150 lines)
    - `body` for input
    - `label-sm` for placeholder

13. **DropShadowFrame** (utility, ~50 lines)
    - No font changes

**Mapping Table:**

| Control | Token for Primary Text | Token for Labels/Icons | Transformation |
|---------|----------------------|-----------------------|----------------|
| CustomSlider | N/A (painted) | `label-xs` (tick marks) | None |
| CustomToggleButton | N/A (painted) | `label-sm` (option text) | None |
| CustomDropdown | `body` (selected) | `label-sm` (items) | None |
| CustomButton | `body-strong` | N/A | None |
| PresetCard | `label-sm` (title) | `icon` (icon) | None |
| SectionLabel | `label-sm` | N/A | `uppercase` |
| NumericDisplay | `numeric-value` | `numeric-unit` | None |
| NumericInput | `body` | N/A | None |
| CustomTextInput | `body` | `label-sm` (placeholder) | None |
| PathInputControl | `body` | `label-sm` (icon) | None |
| ProjectFolderChip | `label-xs` | N/A | `uppercase` |

#### Phase 3: Integration with Theme YAML

Update `docs/THEME_SCHEMA.md` to include font preset definitions (already present in Section 3). Validate that all references resolve correctly.

**Theme Schema Extension (if needed):**
```yaml
typography:
  presets:
    body: {family: "JetBrains Mono", size: 11, weight: 400}
    body-strong: {family: "JetBrains Mono", size: 11, weight: 600}
    # ... existing definitions
```

### Dependencies & Order

- **Requires:** Theme migration (Phase 1-5) to be complete
- **Blocks:** None (standalone enhancement)
- **Parallel with:** State Management, Component Construction, God Class Extraction

### Validation Checklist

- [ ] `TextStyle` instances are immutable
- [ ] All font creation goes through `TextStyle.to_wx_font()`
- [ ] Theme token resolution fails gracefully with clear error messages
- [ ] Override precedence tests pass (override > preset > default)
- [ ] Case transformation applied correctly (uppercase headers)
- [ ] No duplicate `get_custom_font()` calls with hardcoded values
- [ ] Font cache in TextStyleResolver improves performance

---

## 2. Component Construction Alignment

**Status:** Post-theme refactor
**Dependencies:** Theme system complete
**Risk:** MEDIUM | **Impact:** HIGH

### Objective

Establish a unified construction pattern for all custom controls to ensure consistency in layout, styling, event wiring, and structural hierarchy. Extract shared helpers to reduce duplication.

### Current Problems

1. **Inconsistent initialization signatures:** Some controls take `parent` only, others take `value`, `placeholder`, `options`
2. **Scattered helper patterns:** Each control reimplements `_setup_sizer()`, `_bind_events()`, `_apply_theme()`
3. **Event binding location:** Some bind in `__init__`, some in separate methods, some inline
4. **Structural variance:** Similar components (CustomButton vs CustomDropdown) have different internal hierarchies
5. **No composition standard:** Child widget creation order varies wildly

### Proposed Solution

#### Extract Shared Base Classes

```python
# ui/base_components.py (new module)

class ThemedControl(wx.Panel):
    """
    Base class for all themed custom controls.
    Provides: theme integration, sizer management, event wiring template.
    """
    def __init__(self, parent, size=wx.DefaultSize, style_token=None):
        super().__init__(parent, size=size, style=wx.BORDER_NONE)
        self._style_token = style_token
        self._theme = Theme.current()
        self._primary_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self._primary_sizer)
        self._setup_structure()
        self._apply_theme()

    def _setup_structure(self) -> None:
        """Override: Build internal widget hierarchy."""
        raise NotImplementedError

    def _apply_theme(self) -> None:
        """Override: Apply theme colors/fonts to child widgets."""
        pass

    def _bind_events(self) -> None:
        """Override: Wire up event handlers."""
        pass

    def enable(self, enabled: bool = True) -> None:
        """Unified enable/disable with visual feedback."""
        super().Enable(enabled)
        self._update_enabled_state(enabled)

    def _update_enabled_state(self, enabled: bool) -> None:
        """Override: dim colors when disabled."""
        pass

class InteractiveControl(ThemedControl):
    """
    Mixin for controls that respond to mouse hover/click.
    Provides: hover state tracking, mouse capture, visual feedback.
    """
    def __init__(self, *args, **kwargs):
        self._hover = False
        self._pressed = False
        super().__init__(*args, **kwargs)
        self._bind_mouse_events()

    def _bind_mouse_events(self) -> None:
        self.Bind(wx.EVT_ENTER_WINDOW, self._on_enter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self._on_leave)
        self.Bind(wx.EVT_LEFT_DOWN, self._on_left_down)
        self.Bind(wx.EVT_LEFT_UP, self._on_left_up)

    def _on_enter(self, event):
        self._hover = True
        self._update_hover_state(True)
        event.Skip()

    def _on_leave(self, event):
        self._hover = False
        self._pressed = False
        self._update_hover_state(False)
        event.Skip()

    def _on_left_down(self, event):
        self._pressed = True
        self._update_pressed_state(True)
        event.Skip()

    def _on_left_up(self, event):
        self._pressed = False
        self._update_hover_state(self._hover)
        event.Skip()

    def _update_hover_state(self, hover: bool) -> None:
        """Override: change background on hover."""
        pass

    def _update_pressed_state(self, pressed: bool) -> None:
        """Override: change background on press."""
        pass
```

#### Standardize Constructor Signatures

| Control | Current Signature | Proposed Signature |
|---------|------------------|-------------------|
| `CustomSlider` | `(parent, min, max, value, ...)` | `(parent, value, **kwargs)` + `range=(min,max)` kwarg |
| `CustomToggleButton` | `(parent, options, selection)` | `(parent, options, value=None)` |
| `CustomDropdown` | `(parent, options, selection)` | `(parent, options, value=None, placeholder=None)` |
| `CustomButton` | `(parent, label, icon, primary)` | `(parent, label, icon=None, primary=True, **kwargs)` |
| `PresetCard` | `(parent, preset)` | `(parent, preset, on_select, on_delete)` |
| `NumericDisplay` | `(parent, value, unit)` | `(parent, value="", unit="", **kwargs)` |
| `NumericInput` | `(parent, value, min, max)` | `(parent, value=None, range=None, **kwargs)` |
| `SectionLabel` | `(parent, label)` | `(parent, label, **kwargs)` |
| `CustomTextInput` | `(parent, value, placeholder)` | `(parent, value="", placeholder="", multiline=False)` |
| `PathInputControl` | `(parent, path)` | `(parent, value="", **kwargs)` |
| `ProjectFolderChip` | `(parent, folder_name)` | `(parent, label, **kwargs)` |
| `CustomColorPicker` | `(parent, color)` | `(parent, value=None, **kwargs)` |

**Common kwargs:** `size`, `style_token`, `on_change` (callback)

### Implementation Plan

#### Phase 1: Create Base Classes

**Files to create:**
- `SpinRender/ui/base_components.py` — `ThemedControl`, `InteractiveControl`
- `SpinRender/ui/component_factory.py` — Factory helpers for common patterns

**Factory helpers (examples):**

```python
# component_factory.py
def create_button(parent, label, icon=None, primary=True, **kwargs):
    """Standardized button construction."""
    btn = CustomButton(parent, label=label, icon=icon, primary=primary, **kwargs)
    btn.SetMinSize((kwargs.get('min_width', 100), kwargs.get('height', 36)))
    return btn

def create_slider(parent, value=0, range=(0, 100), **kwargs):
    """Standardized slider with theme token support."""
    slider = CustomSlider(parent, value=value, range=range, **kwargs)
    slider.SetMinSize((kwargs.get('width', -1), kwargs.get('height', 18)))
    return slider
```

#### Phase 2: Refactor Controls Incrementally

**Order (least to most complex):**

1. **SectionLabel** (simplest, no interaction)
   - Inherit from `ThemedControl`
   - Move theme color references to `_apply_theme()`

2. **ProjectFolderChip** (static, but colored)
   - Inherit from `ThemedControl`
   - Minimal changes

3. **NumericDisplay** (read-only, has text)
   - Inherit from `ThemedControl`
   - Extract text widget creation to `_setup_structure()`

4. **PathInputControl** (composite, no interaction)
   - Inherit from `ThemedControl`
   - Standardize child widget creation

5. **CustomColorPicker** (complex internal state)
   - Inherit from `ThemedControl`
   - Refactor event binding to `_bind_events()`

6. **CustomTextInput** (text editing)
   - Inherit from `ThemedControl`
   - Add focus handling to `_bind_events()`

7. **NumericInput** (spinner control)
   - Inherit from `InteractiveControl` (buttons interactive)
   - Standardize up/down button creation

8. **CustomSlider** (full interaction + painting)
   - Inherit from `InteractiveControl`
   - Refactor paint handler to use theme tokens

9. **CustomToggleButton** (segmented control)
   - Inherit from `InteractiveControl`
   - Unify option button creation loop

10. **CustomDropdown** (popup interaction)
    - Inherit from `InteractiveControl`
    - Refactor popup creation pattern

11. **CustomButton** (all variants)
    - Inherit from `InteractiveControl`
    - Centralize variant logic in `_apply_theme()`

12. **PresetCard** (composite interactive)
    - Inherit from `InteractiveControl`
    - Standardize card layout pattern

#### Phase 3: Update main_panel.py and dialogs.py

**Tasks:**
1. Search for all control instantiations
2. Update to use new unified signatures
3. Replace direct `wx.Panel` layout code with factory helpers where appropriate
4. Remove redundant setup code (e.g., manual `SetMinSize`, repeated sizer patterns)

**Before/After Example (main_panel.py):**

**Before:**
```python
# Inconsistent patterns
self.slice_toggle = CustomToggleButton(panel, options=slice_modes, selection=0)
self.slice_toggle.SetMinSize((200, 32))
self.slice_toggle.Bind(wx.EVT_TOGGLEBUTTON, self.on_slice_mode)

self.render_btn = CustomButton(btn_panel, label="RENDER", icon="mdi-play", primary=True, size=(140, 40))
```

**After:**
```python
from ui.component_factory import create_toggle, create_button

# Consistent patterns
self.slice_toggle = create_toggle(panel, options=slice_modes, value=0,
                                 on_change=self.on_slice_mode,
                                 size=(200, 32))

self.render_btn = create_button(btn_panel, label="RENDER", icon="mdi-play",
                                primary=True, min_width=140, height=40)
```

### Structural Consistency Guidelines

After refactor, all components must follow these rules:

1. **Two-phase init pattern:**
   - `__init__`: store params, call `super().__init__()`
   - `_setup_structure()`: create child widgets
   - `_bind_events()`: attach handlers
   - `_apply_theme()`: apply colors/fonts (called last)

2. **No direct color numbers in paint handlers:**
   - All colors come from `self._theme.colour(token)` or cached in `__init__`

3. **Event binding through methods:**
   - Never inline `Bind()` calls in `_setup_structure()`
   - All bindings in `_bind_events()` for visibility

4. **Visual state updates through dedicated methods:**
   - `_update_hover_state(bool)`
   - `_update_pressed_state(bool)`
   - `_update_enabled_state(bool)`

5. **Minimum size in constructor or `_setup_structure()`:**
   - Never set min size after construction

6. **Theme token naming convention:**
   - Use `components.{control_name}.{element}` format
   - Example: `components.custom_button.bg.primary`

### Dependencies & Order

- **Requires:** Theme migration (colors/fonts from theme)
- **Can proceed in parallel with:** Typography, Interaction Integrity, God Class Extraction
- **Blocks:** None (but enables easier future refactoring)

### Migration Path (Non-Breaking)

To maintain compatibility during transition:

1. Keep old signatures as **backwards-compatible wrappers**:
```python
class CustomButton(InteractiveControl):
    def __init__(self, parent, label="", icon=None, primary=True,
                 min_width=100, height=36, **kwargs):
        # Convert old signature to new kwarg format
        kwargs.setdefault('size', (min_width, height))
        super().__init__(parent, **kwargs)
        self._label = label
        self._icon = icon
        self._primary = primary
        # ... rest of initialization
```

2. Deploy in phases: update one control at a time, verify in KiCad
3. Update calling code incrementally (main_panel.py first, then dialogs.py)
4. Remove legacy parameter support only after all call sites updated

### Validation Checklist

- [ ] All custom controls inherit from `ThemedControl` or `InteractiveControl`
- [ ] `_setup_structure()`, `_bind_events()`, `_apply_theme()` present on all
- [ ] No `wx.Colour(r,g,b)` literals in any control file
- [ ] All colors from `Theme.current().colour()` or cached in `__init__`
- [ ] Event bindings only in `_bind_events()` (no inline `Bind()` in `_setup_structure()`)
- [ ] Minimum sizes set in `__init__` or `_setup_structure()`
- [ ] All controls have consistent `enable()` behavior
- [ ] Hover/pressed states work identically across all interactive controls
- [ ] No duplicate font creation code

---

## 3. Interaction Integrity

**Status:** Can begin immediately (low theme dependency)
**Dependencies:** Component Construction recommended first
**Risk:** LOW | **Impact:** MEDIUM

### Objective

Fix mouse event pass-through for non-interactive labels to prevent them from blocking clicks to parent containers. Ensure click propagation works correctly for composite controls.

### Problem Statement

Non-interactive `wx.StaticText` and painted text labels currently intercept mouse events, preventing click handlers on parent containers from firing. This affects:

- `PresetCard`: Click on label area should trigger card selection but doesn't
- `NumericDisplay`: Background click should propagate
- Painted labels in `CustomSlider` and `SectionLabel`: Should not capture mouse

### Root Cause

wxPython's default behavior: child windows capture mouse events unless explicitly configured to pass through. `wx.StaticText` has no built-in pass-through mechanism.

### Solution Architecture

```python
# ui/event_utils.py (new module)

def enable_mouse_pass_through(window: wx.Window) -> None:
    """
    Configure a window to pass mouse events to its parent.
    Child receives EVT_MOUSE_EVENTS but calls event.Skip() to allow propagation.
    """
    window.Bind(wx.EVT_LEFT_DOWN, lambda e: e.Skip())
    window.Bind(wx.EVT_LEFT_UP, lambda e: e.Skip())
    window.Bind(wx.EVT_MOTION, lambda e: e.Skip())
    window.Bind(wx.EVT_ENTER_WINDOW, lambda e: e.Skip())
    window.Bind(wx.EVT_LEAVE_WINDOW, lambda e: e.Skip())

def disable_mouse_pass_through(window: wx.Window) -> None:
    """Restore default mouse capture (for interactive controls)."""
    # Unbind pass-through handlers if tracked; otherwise no-op
    pass
```

```python
# ui/transparent_label.py (new module)

class TransparentLabel(wx.StaticText):
    """
    StaticText that passes all mouse events to parent.
    Use for labels inside clickable containers where label itself is not interactive.
    """
    def __init__(self, parent, label="", **kwargs):
        super().__init__(parent, label=label, **kwargs)
        enable_mouse_pass_through(self)
```

### Implementation Plan

#### Phase 1: Create Utilities

**Files:**
- `SpinRender/ui/event_utils.py` — Pass-through helper functions
- `SpinRender/ui/transparent_label.py` — `TransparentLabel` class

**TransparentLabel complete implementation:**
```python
# ui/transparent_label.py
import wx
from .event_utils import enable_mouse_pass_through

class TransparentLabel(wx.StaticText):
    """
    StaticText that doesn't capture mouse events.
    Clicks pass through to parent container.
    """
    def __init__(self, parent, label="", **kwargs):
        # Ensure style doesn't include any mouse-interactive flags
        kwargs.setdefault('style', wx.BORDER_NONE)
        super().__init__(parent, label=label, **kwargs)
        enable_mouse_pass_through(self)
```

#### Phase 2: Apply to Affected Controls

**Affected controls identified:**

1. **PresetCard** (dialogs.py)
   - **Problem:** `wx.StaticText` label intercepts clicks
   - **Fix:** Replace with `TransparentLabel`
   - **Files:** `dialogs.py:444-447`

   **Before:**
   ```python
   label = wx.StaticText(panel, label=name.upper())
   label.SetForegroundColour(self.TEXT_PRIMARY)
   label.SetFont(get_custom_font(11))
   sizer.Add(label, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 12)
   panel.Bind(wx.EVT_LEFT_DOWN, lambda e: self.on_select(name, scope))
   label.Bind(wx.EVT_LEFT_DOWN, lambda e: self.on_select(name, scope))  # redundant!
   ```

   **After:**
   ```python
   from .transparent_label import TransparentLabel
   label = TransparentLabel(panel, label=name.upper())
   # ... styling
   sizer.Add(label, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 12)
   panel.Bind(wx.EVT_LEFT_DOWN, lambda e: self.on_select(name, scope))
   # label binding removed (pass-through handles it)
   ```

2. **SectionLabel** (custom_controls.py)
   - **Problem:** Painted label intercepts clicks (not intended to be interactive)
   - **Fix:** Add pass-through to `on_paint` context or set window style
   - **Simpler:** Bind mouse events in `__init__` to call `event.Skip()`

   ```python
   class SectionLabel(wx.Panel):
       def __init__(self, parent, label):
           super().__init__(parent)
           # ...
           # Add pass-through for all mouse events
           for event_type in [wx.EVT_LEFT_DOWN, wx.EVT_LEFT_UP,
                              wx.EVT_MOTION, wx.EVT_ENTER_WINDOW,
                              wx.EVT_LEAVE_WINDOW]:
               self.Bind(event_type, lambda e: e.Skip())
   ```

3. **CustomSlider** tick labels (if present)
   - Currently drawn directly in paint handler (not separate window)
   - **Fix:** No action needed — painted elements don't capture mouse
   - **Verify:** Ensure no invisible child windows over track

4. **NumericDisplay** (custom_controls.py)
   - **Problem:** `wx.StaticText` children might need pass-through if background clickable
   - **Decision:** If display should be non-interactive, apply pass-through to text widgets
   - **Implementation:**
   ```python
   class NumericDisplay(wx.Panel):
       def _setup_structure(self):
           # ...
           self.value_label = TransparentLabel(self, label="")
           self.unit_label = TransparentLabel(self, label="")
   ```

5. **RecallPresetDialog** trash/confirm icons (dialogs.py:456-464)
   - **Problem:** Icons require individual bindings; could use pass-through on container
   - **Fix:** Keep explicit bindings (complex interaction logic)
   - **No change needed:** These *are* interactive elements

#### Phase 3: Review Composite Controls

Audit all controls that contain child labels to verify pass-through:

| Control | Child Labels | Interactive? | Action |
|---------|--------------|--------------|--------|
| PresetCard | title (StaticText) | No (card is interactive) | Replace with TransparentLabel |
| SectionLabel | None (painted) | No | Add mouse pass-through in __init__ |
| CustomButton | None (painted) | Yes (button interactive) | No change |
| NumericDisplay | value, unit | No | Replace with TransparentLabel |
| PathInputControl | path (StaticText) | No (button interactive) | Replace with TransparentLabel |
| CustomTextInput | placeholder | No (input captures clicks) | No change (input handles focus) |
| DropShadowFrame | None (painted) | No | Already transparent |

#### Phase 4: Testing

**Manual test checklist:**
1. Open `RecallPresetDialog`: click preset name (not card) → preselects
2. Click preset card background (avoiding trash/confirm) → preselects
3. Click `NumericDisplay` background → no action expected (non-interactive)
4. Click `SectionLabel` → no action expected
5. All buttons still functional after pass-through changes

**Automated test hook (optional):**
```python
# test/test_interaction_integrity.py
def test_preset_card_click_through_label():
    """Verify clicking label triggers same event as clicking card."""
    card = PresetCard(parent, preset)
    label_clicked = []
    card.Bind(wx.EVT_LEFT_DOWN, lambda e: label_clicked.append(True))

    # Simulate click on label
    label = card.GetChildren()[0]  # assuming label is first child
    event = wx.MouseEvent(wx.wxEVT_LEFT_DOWN)
    event.SetEventObject(label)
    label.ProcessEvent(event)

    assert len(label_clicked) == 1, "Click did not propagate to parent"
```

### Dependencies & Order

- **Requires:** Component Construction (to identify which labels need pass-through)
- **Can be done in parallel with:** Typography, Validation Layer
- **Blocks:** None

### Risk Mitigation

- **Risk:** Pass-through might break intentional label interaction (unlikely)
- **Mitigation:** Only apply to labels in clearly non-interactive contexts
- **Rollback:** Replace `TransparentLabel` with `wx.StaticText` if issues arise

---

## 4. Validation Layer

**Status:** After core refactors (theme + component construction)
**Dependencies:** Theme system, TextStyle, State Management
**Risk:** MEDIUM | **Impact:** HIGH

### Objective

Implement runtime validation for:
1. Theme token resolution (missing tokens, circular refs)
2. Contrast checking (text vs background accessibility)
3. Configuration schema versioning
4. Settings object validation at load time

### Problem Statement

Current system:
- No validation if theme token path is misspelled → silent failures or KeyError
- No accessibility checks → low-contrast text possible
- Settings saved as raw dicts → no type safety or schema enforcement
- Configuration format cannot evolve without breaking changes

### Proposed Architecture

```python
# core/validation.py (new module)
from dataclasses import dataclass, fields
from typing import get_type_hints
import re

class ValidationError(Exception):
    """Raised when configuration or theme validation fails."""
    pass

class TokenResolver:
    """
    Validates theme token references and resolves them with error reporting.
    Detects: missing keys, type mismatches, circular references.
    """
    def __init__(self, theme_data: dict):
        self._data = theme_data
        self._resolved_cache = {}
        self._ resolv_path_stack = []  # for circular ref detection

    def resolve(self, path: str) -> any:
        """Resolve dot-path with validation."""
        if path in self._resolved_cache:
            return self._resolved_cache[path]

        if path in self._resolving_stack:
            cycle = ' -> '.join(self._resolving_stack + [path])
            raise ValidationError(f"Circular reference in theme: {cycle}")

        self._resolving_stack.append(path)
        try:
            value = self._traverse(path.split('.'), self._data)
            self._resolved_cache[path] = value
            return value
        except KeyError as e:
            raise ValidationError(f"Missing theme token: '{path}'. {e}")
        finally:
            self._resolving_stack.pop()

    def _traverse(self, keys: list, node: dict) -> any:
        for key in keys:
            if not isinstance(node, dict):
                raise ValidationError(f"Cannot traverse into {type(node).__name__} at '{key}' in '{'.'.join(keys)}'")
            if key not in node:
                available = ', '.join(sorted(node.keys()))
                raise ValidationError(f"Key '{key}' not found. Available: {available}")
            node = node[key]
        return node

class ContrastChecker:
    """
    Validates text/background color contrast per WCAG 2.1 AA standards.
    Minimum: 4.5:1 for normal text, 3:1 for large text (≥18pt or 14pt bold).
    """
    @staticmethod
    def calculate_luminance(r: int, g: int, b: int) -> float:
        """Calculate relative luminance per WCAG spec."""
        rs = r / 255
        gs = g / 255
        bs = b / 255
        def channel(c):
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        return 0.2126 * channel(rs) + 0.7152 * channel(gs) + 0.0722 * channel(bs)

    @staticmethod
    def ratio(lum1: float, lum2: float) -> float:
        """Calculate contrast ratio (1-21)."""
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)
        return (lighter + 0.05) / (darker + 0.05)

    @staticmethod
    def check(text_color: wx.Colour, bg_color: wx.Colour,
              font_size: int, font_weight: int) -> bool:
        """
        Returns True if contrast meets WCAG AA for given font size/weight.
        Large text threshold: 18pt normal OR 14pt bold.
        """
        lum_text = ContrastChecker.calculate_luminance(text_color.Red(),
                                                        text_color.Green(),
                                                        text_color.Blue())
        lum_bg = ContrastChecker.calculate_luminance(bg_color.Red(),
                                                     bg_color.Green(),
                                                     bg_color.Blue())
        ratio = ContrastChecker.ratio(lum_text, lum_bg)

        is_large = (font_size >= 18) or (font_size >= 14 and font_weight >= wx.FONTWEIGHT_BOLD)
        required = 3.0 if is_large else 4.5
        return ratio >= required

class SchemaValidator:
    """
    Validates settings objects against type definitions.
    Uses dataclass annotations or manual schema.
    """
    @staticmethod
    def validate(obj: object, schema: dict) -> list[str]:
        """
        Validate object attributes against schema.
        Returns list of error messages (empty if valid).
        """
        errors = []
        for field, expected_type in schema.items():
            if not hasattr(obj, field):
                errors.append(f"Missing required field: {field}")
                continue
            value = getattr(obj, field)
            if not isinstance(value, expected_type):
                errors.append(f"Field '{field}' expected {expected_type.__name__}, got {type(value).__name__}")
        return errors
```

### Theme Token Validation Implementation

```python
# core/theme.py (extended)
import yaml

class Theme:
    SCHEMA_VERSION = "1.0.0"

    def __init__(self, data: dict):
        self._data = data
        self._validator = TokenResolver(data)
        self._validate_schema()
        self._validate_references()

    def _validate_schema(self):
        """Ensure theme has required top-level keys."""
        required = ['palette', 'colors', 'typography', 'spacing', 'borders', 'components']
        for key in required:
            if key not in self._data:
                raise ValidationError(f"Theme missing required key: '{key}'")

    def _validate_references(self):
        """Walk all component tokens and validate refs resolve."""
        for comp_name, comp_spec in self._data.get('components', {}).items():
            for elem, token_ref in comp_spec.items():
                if isinstance(token_ref, dict) and 'ref' in token_ref:
                    try:
                        self._validator.resolve(token_ref['ref'])
                    except ValidationError as e:
                        raise ValidationError(f"Component '{comp_name}.{elem}' has invalid reference: {e}")

    @classmethod
    def load(cls, name: str = "dark") -> "Theme":
        """Load and validate theme from YAML."""
        import wx  # Deferred to avoid circular imports
        path = Path(__file__).parent.parent / "resources" / "themes" / f"{name}.yaml"
        with open(path) as f:
            data = yaml.safe_load(f)

        # Version check
        version = data.get('meta', {}).get('version')
        if version != cls.SCHEMA_VERSION:
            raise ValidationError(f"Theme schema version mismatch: file={version}, expected={cls.SCHEMA_VERSION}")

        return cls(data)

    def colour(self, token: str) -> wx.Colour:
        """Resolve and parse color token with full validation."""
        value = self._validator.resolve(token)
        return self._parse_colour(value)

    def validate_contrast(self, text_token: str, bg_token: str,
                         font_size: int, font_weight: int) -> bool:
        """Check that text on background meets WCAG AA."""
        text_color = self.colour(text_token)
        bg_color = self.colour(bg_token)
        return ContrastChecker.check(text_color, bg_color, font_size, font_weight)
```

### Settings Schema Implementation

```python
# core/settings.py (new module)
from dataclasses import dataclass, asdict
from typing import Optional
from pathlib import Path
import json

@dataclass
class RenderSettings:
    """
    Typed settings object with validation.
    Replaces raw dict self.settings in SpinRenderPanel and AdvancedOptionsDialog.
    """
    # Output settings
    output_auto: bool = True
    output_path: str = ""
    format: str = "mp4"

    # CLI overrides
    cli_overrides: str = ""

    # Logging
    logging_level: str = "simple"

    # Render parameters (add as needed)
    frame_rate: int = 30
    resolution: str = "1920x1080"

    @classmethod
    def default(cls) -> "RenderSettings":
        return cls()

    @classmethod
    def from_dict(cls, data: dict) -> "RenderSettings":
        """Create from raw dict, filling defaults for missing keys."""
        field_names = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in field_names}
        return cls(**filtered)

    def to_dict(self) -> dict:
        """Export to plain dict."""
        return asdict(self)

    def save(self, path: Path) -> None:
        """Persist to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Path) -> "RenderSettings":
        """Load from JSON file with validation."""
        if not path.exists():
            return cls.default()

        with open(path) as f:
            data = json.load(f)

        # Validate required fields exist
        instance = cls.from_dict(data)
        return instance

    def validate(self) -> list[str]:
        """Validate field values. Returns error list."""
        errors = []

        if self.format not in ["mp4", "gif", "png"]:
            errors.append(f"Invalid format: {self.format}")

        if self.logging_level not in ["off", "simple", "verbose"]:
            errors.append(f"Invalid logging level: {self.logging_level}")

        if self.frame_rate < 1 or self.frame_rate > 120:
            errors.append(f"Frame rate must be 1-120, got {self.frame_rate}")

        # Validate resolution pattern WxH
        import re
        if not re.match(r'^\d+x\d+$', self.resolution):
            errors.append(f"Resolution must be WxH format, got {self.resolution}")

        return errors
```

### Implementation Plan

#### Phase 1: Core Validation Module

**File:** `SpinRender/core/validation.py`
- Implement `TokenResolver`, `ContrastChecker`, `SchemaValidator`
- Add comprehensive docstrings and examples
- Unit test each class (target: 90% coverage)

#### Phase 2: Integrate into Theme

**Modify:** `SpinRender/core/theme.py`
- Add version constant `SCHEMA_VERSION = "1.0.0"`
- Add `_validate_schema()` and `_validate_references()`
- Call validation in `__init__()` (raises `ValidationError` on failure)
- Add public `validate_contrast()` method

**Test:** Load all theme files in `resources/themes/` — should pass validation

#### Phase 3: Replace Settings Dict

**Modify:** `SpinRender/ui/main_panel.py`
1. Import: `from core.settings import RenderSettings`
2. Replace `self.settings: dict = {}` with `self.settings: RenderSettings = RenderSettings.default()`
3. Update all settings access:
   - `self.settings.get('output_auto', True)` → `self.settings.output_auto`
   - `self.settings['output_auto'] = val` → `self.settings.output_auto = val`
4. Load/save via `RenderSettings.load()` and `.save()` methods

**Modify:** `SpinRender/ui/dialogs.py` (AdvancedOptionsDialog)
1. Pass `RenderSettings` object to dialog constructor
2. Update UI fields to read/write typed attributes
3. Validate on OK: `errors = self.settings.validate(); if errors: show_error()`

**Example:**

**Before (dialogs.py:336-340):**
```python
def on_ok(self, event):
    self.settings['cli_overrides'] = self.override_input.GetValue()
    self.settings['output_auto'] = self.auto_toggle.GetValue()
    self.settings['logging_level'] = self.log_opts[self.log_toggle.GetSelection()]['id']
    self.EndModal(wx.ID_OK)
```

**After:**
```python
def on_ok(self, event):
    self.settings.cli_overrides = self.override_input.GetValue()
    self.settings.output_auto = self.auto_toggle.GetValue()
    self.settings.logging_level = self.log_opts[self.log_toggle.GetSelection()]['id']

    errors = self.settings.validate()
    if errors:
        wx.MessageBox("\n".join(errors), "Validation Error", wx.OK | wx.ICON_ERROR)
        return

    self.EndModal(wx.ID_OK)
```

#### Phase 4: Runtime Validation Hooks

Add validation on settings load (plugin startup):

```python
# spinrender_plugin.py
def setup(self):
    settings_path = Path(self.settings_path)
    self.settings = RenderSettings.load(settings_path)

    errors = self.settings.validate()
    if errors:
        logger.warning(f"Settings validation failed: {errors}")
        self.settings = RenderSettings.default()  # fallback
```

Add contrast validation in theme loader (optional, can be opt-in):

```python
# core/theme.py (optional method)
def validate_all_contrasts(self, warn_only=True):
    """Validate all text-on-background combinations defined in components."""
    failures = []
    for comp_name, comp_spec in self._data['components'].items():
        text_token = comp_spec.get('text')
        bg_token = comp_spec.get('bg')
        if text_token and bg_token:
            # Assume typical font size/weight based on component
            size = 11  # default
            weight = wx.FONTWEIGHT_NORMAL
            if not self.validate_contrast(text_token, bg_token, size, weight):
                failures.append(f"{comp_name}: {text_token} on {bg_token}")

    if failures and not warn_only:
        raise ValidationError(f"Contrast failures: {', '.join(failures)}")
    return failures
```

### Dependencies & Order

- **Requires:** Theme migration complete, TextStyle optional but helpful
- **Parallel with:** State Management (both touch settings)
- **Blocks:** None (can be developed incrementally)

### Testing Strategy

**Unit tests (test/core/test_validation.py):**
1. `test_token_resolver_valid_path()` — resolve `colors.accent.primary`
2. `test_token_resolver_missing_key()` — raises ValidationError
3. `test_token_resolver_circular_ref()` — detects cycle
4. `test_contrast_checker_aa_compliance()` — known good/bad pairs
5. `test_settings_validation_valid()` — default settings pass
6. `test_settings_validation_invalid_format()` — fails appropriately

**Integration test:**
- Load theme YAML, validate all component token refs
- Verify no validation errors in default theme

### Validation Checklist

- [ ] All theme tokens resolve without errors
- [ ] Circular reference detection works
- [ ] Missing token errors include helpful suggestions (available keys)
- [ ] Contrast checker correctly identifies WCAG AA failures
- [ ] Settings dataclass validates all field types
- [ ] Unknown fields rejected (or warned and ignored)
- [ ] Settings.load() provides defaults for missing files
- [ ] Settings.validate() catches all invalid combinations
- [ ] Error messages are user-actionable

---

## 5. Dependency Fix: utils → ui Inversion

**Status:** Early in refactor sequence
**Dependencies:** None (can start immediately)
**Risk:** HIGH | **Impact:** HIGH

### Problem Statement

Current dependency: `ui/custom_controls.py` → imports from `utils/logger.py`

Desired direction: `utils` should be foundational, not depend on UI. Current structure may already be correct (utils → ui). Need to verify and document.

### Analysis Required

**Investigate:**
1. What does `custom_controls.py` import from `utils`?
2. Does `utils/logger.py` import from `ui`? (creates cycle)
3. Are there other inverted dependencies (ui → core → ui)?

**Search strategy:**
```bash
cd /Users/foo/Code/SpinRender_claude
grep -r "from utils" SpinRender/ui/*.py
grep -r "from ui" SpinRender/utils/*.py
grep -r "import SpinRender" SpinRender/utils/*.py  # absolute import cycle risk
```

### Current File Structure

```
SpinRender/
├── ui/
│   ├── custom_controls.py  ← imports from utils?
│   ├── dialogs.py
│   ├── main_panel.py
│   └── theme.py (planned)
├── utils/
│   ├── logger.py
│   └── dependencies.py
└── core/
    ├── renderer.py
    ├── presets.py
    ├── preview.py
    └── theme.py (planned)
```

### Dependency Matrix (Current State)

After research, document the actual imports:

| File | Imports From | Circular? |
|------|--------------|-----------|
| custom_controls.py | utils.logger? utils.dependencies? | |
| dialogs.py | utils.logger? | |
| main_panel.py | utils.logger? | |
| utils/logger.py | (might import wx, no ui) | |
| utils/dependencies.py | (likely standalone) | |

### If Cycle Found: Break Strategy

#### Option A: Extract Shared Abstractions

Create new layer `SpinRender/foundation/` or `SpinRender/common/`:

```
foundation/
├── event_bus.py    # pubsub if needed
├── config.py       # settings schema
└── validation.py   # validation utilities
```

Move cycle-causing code to `foundation/`, then:
- `utils/` → `foundation/` (no deps on UI)
- `core/` → `foundation/` or keep (depends on UI? check)
- `ui/` → imports from `foundation/` (one-way)

#### Option B: Dependency Injection

If `utils.logger` needs UI context, inject it instead of importing:

```python
# Before (utils/logger.py):
from ui.some_module import get_log_path  # ❌ cycle!
LOG_DIR = get_log_path()

# After:
class Logger:
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir

# In ui/main_panel.py:
from utils.logger import Logger
self.logger = Logger(log_dir=Path(self.settings.log_path))
```

#### Option C: Interface Segregation

Split `utils` into:
- `utils/platform.py` — no UI deps (safe for any layer)
- `utils/ui_logger.py` — imports UI-specific paths (UI layer only)

```python
# ui/main_panel.py
from utils.ui_logger import UILogger  # knows about UI paths

# core/renderer.py
from utils.platform import system_info  # no UI deps
```

### Implementation Plan

#### Phase 1: Audit

Run analysis commands, produce dependency graph:

```bash
# Generate import graph
cd SpinRender
find . -name "*.py" -exec grep -H "^from \|^import " {} \; | sort > import_graph.txt
```

Document findings in a short report.

#### Phase 2: Propose Reorganization

Based on findings, choose A, B, or C. Document:

- New directory structure
- File moves (if any)
- Import changes required
- Risk assessment

#### Phase 3: Execute Refactor

1. Create new module(s) with extracted code
2. Update imports in dependent files
3. Remove circular references
4. Verify: `python -m pyflakes SpinRender/` shows no cycle warnings
5. Run plugin, verify logging still works

#### Phase 4: Document New Architecture

Update `docs/ARCHITECTURE.md` (or create it) with dependency diagram.

### Success Criteria

- No circular imports (`A imports B, B imports A`)
- Dependency direction: `foundation → utils → core → ui` (unidirectional)
- All unit tests pass
- Plugin loads and functions in KiCad
- Logger output unchanged

### Dependencies & Order

- **Should be done early** (before major refactors to minimize merge pain)
- **Blocks:** None, but facilitates other refactors
- **Parallel with:** None (audit first, then execute)

---

## 6. God Class Extraction: SpinRenderPanel (1542 lines)

**Status:** Largest refactor, require careful planning
**Dependencies:** State Management (to centralize state first)
**Risk:** HIGH | **Impact:** VERY HIGH

### Problem Statement

`SpinRenderPanel` is a 1542-line monolithic class violating Single Responsibility Principle. Responsibilities mixed:

- UI layout and painting (600 lines)
- Render execution and threading (400 lines)
- Settings management and persistence (200 lines)
- Logging and status updates (150 lines)
- Preset management UI (192 lines)

### Extraction Targets

Proposed module breakdown:

```
SpinRender/ui/
├── main_panel.py          ← Thin coordination layer (~300 lines)
├── render_executor.py     ← Render thread/queue management (~200 lines)
├── settings_manager.py    ← Settings load/save/validation (~150 lines)
├── status_panel.py        ← Status display and logging (~200 lines)
├── preset_panel.py        ← Preset management UI (~200 lines)
├── preview_panel.py       ← GL/WxImage preview (~150 lines)
└── layout_constants.py    ← Sizer sizes, spacing constants (~100 lines)
```

### Responsibility Allocation

| Module | Responsibility | Exports | Depends On |
|--------|----------------|---------|------------|
| `main_panel.py` | Coordinate sub-panels, handle top-level events | `SpinRenderPanel` (thin) | All below |
| `render_executor.py` | Render thread pool, queue, cancellation, process monitoring | `RenderExecutor` | `utils.logger`, `core.renderer` |
| `settings_manager.py` | Load/save `RenderSettings`, migration, defaults | `SettingsManager` | `core.settings` |
| `status_panel.py` | Status bar, log tail viewer, spinner | `StatusPanel` | `utils.logger` |
| `preset_panel.py` | Preset recall/save/delete UI | `PresetPanel` | `core.presets` |
| `preview_panel.py` | Image/GL preview widget | `PreviewPanel` | `core.preview` |
| `layout_constants.py` | Magic numbers: panel heights, sizer gaps, min sizes | Constants | None |

### Detailed Module Specs

#### 1. render_executor.py

**Extract from:** `main_panel.py:500-900` (render button callbacks, threading)

```python
# ui/render_executor.py
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from pathlib import Path
from utils.logger import SpinLogger
from core.renderer import RenderEngine

class RenderExecutor:
    """
    Manages render execution in background thread.
    Provides: queue, cancellation, progress callbacks, completion handler.
    """
    def __init__(self, max_workers=1):
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._current_future: Optional[Future] = None
        self._lock = threading.Lock()

    def render_async(self, settings: RenderSettings,
                     board_path: Path,
                     progress_cb: callable,
                     completion_cb: callable) -> None:
        """Queue render job."""
        if self._current_future and not self._current_future.done():
            self.cancel()

        self._current_future = self._executor.submit(
            self._render_worker,
            settings, board_path, progress_cb
        )
        self._current_future.add_done_callback(
            lambda f: completion_cb(f.exception())
        )

    def _render_worker(self, settings, board_path, progress_cb):
        """Thread entry point."""
        engine = RenderEngine(board_path, settings)
        # ... detailed render loop with progress updates
        pass

    def cancel(self):
        """Request cancellation of current render."""
        with self._lock:
            if self._current_future:
                self._current_future.cancel()

    @property
    def is_rendering(self) -> bool:
        return self._current_future and not self._current_future.done()
```

**Lines extracted:** ~400 → **200 lines** (simplify)

#### 2. settings_manager.py

**Extract from:** `main_panel.py:200-300, 1400-1542` (settings save/load, file paths)

```python
# ui/settings_manager.py
from pathlib import Path
import json
from core.settings import RenderSettings

class SettingsManager:
    """
    Manages RenderSettings lifecycle: load, save, migration, defaults.
    Hides file format details from main panel.
    """
    SETTINGS_FILENAME = "spinrender_settings.json"

    def __init__(self, board_dir: Path):
        self.board_dir = board_dir
        self._settings: Optional[RenderSettings] = None

    @property
    def settings(self) -> RenderSettings:
        if self._settings is None:
            self.load()
        return self._settings

    def load(self) -> RenderSettings:
        """Load from board directory or fall back to defaults."""
        path = self.board_dir / self.SETTINGS_FILENAME
        self._settings = RenderSettings.load(path)
        return self._settings

    def save(self) -> None:
        """Persist current settings."""
        path = self.board_dir / self.SETTINGS_FILENAME
        self.settings.save(path)

    def reset_to_defaults(self) -> None:
        """Restore factory settings."""
        self._settings = RenderSettings.default()
```

**Lines extracted:** ~150 → **80 lines**

#### 3. status_panel.py

**Extract from:** `main_panel.py:1200-1400` (status bar, logging)

```python
# ui/status_panel.py
import wx
from utils.logger import SpinLogger

class StatusPanel(wx.Panel):
    """
    Bottom panel showing render status and logging tail.
    Features: status text, progress bar, log viewer button.
    """
    def __init__(self, parent):
        super().__init__(parent, size=(-1, 80))
        self._build_ui()
        self._bind_logger()

    def _build_ui(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.status_label = wx.StaticText(self, label="Ready")
        sizer.Add(self.status_label, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 16)

        self.progress = wx.Gauge(self, range=100, size=(200, 16))
        sizer.Add(self.progress, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 16)

        logs_btn = CustomButton(self, label="LOGS", primary=False, size=(80, 28))
        logs_btn.Bind(wx.EVT_BUTTON, self.on_open_logs)
        sizer.Add(logs_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 16)

        self.SetSizer(sizer)

    def _bind_logger(self):
        """Hook into logger for real-time updates."""
        SpinLogger.add_ui_callback(self.on_log_message)

    def on_log_message(self, message: str):
        """Callback from logger."""
        wx.CallAfter(self._update_status, message)

    def _update_status(self, message: str):
        self.status_label.SetLabel(message)
        self.Layout()
```

**Lines extracted:** ~200 → **120 lines**

#### 4. preset_panel.py

**Extract from:** `main_panel.py:900-1100` (preset cards area)

```python
# ui/preset_panel.py
import wx
from core.presets import PresetManager
from .custom_controls import PresetCard

class PresetPanel(wx.Panel):
    """
    Panel displaying preset cards with recall/save/delete buttons.
    """
    def __init__(self, parent, board_path: Path, on_preset_selected: callable):
        super().__init__(parent)
        self.board_path = board_path
        self.on_preset_selected = on_preset_selected
        self.manager = PresetManager(board_path)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.cards_container = wx.Panel(self)
        self.cards_sizer = wx.WrapSizer(wx.HORIZONTAL)
        self.cards_container.SetSizer(self.cards_sizer)

        sizer.Add(self.cards_container, 1, wx.EXPAND | wx.ALL, 16)
        self.SetSizer(sizer)

    def refresh(self):
        """Reload preset list from disk."""
        self.cards_sizer.Clear(delete_windows=True)

        for scope, name, settings in self.manager.list_presets_detailed():
            card = PresetCard(
                self.cards_container,
                preset=(scope, name, settings),
                on_select=self._on_card_click,
                on_delete=self._on_card_delete
            )
            self.cards_sizer.Add(card, 0, wx.ALL, 8)

        self.cards_container.Layout()
        self.Layout()

    def _on_card_click(self, preset):
        self.on_preset_selected(preset)

    def _on_card_delete(self, preset):
        # confirm, delete, refresh
        pass
```

**Lines extracted:** ~200 → **120 lines**

#### 5. preview_panel.py

**Extract from:** `main_panel.py:1100-1200` (preview widget)

```python
# ui/preview_panel.py
import wx
from core.preview import GLPreviewRenderer

class PreviewPanel(wx.Panel):
    """
    Panel hosting wxGLCanvas or wxStaticBitmap for render preview.
    Handles resize, aspect ratio, background color.
    """
    def __init__(self, parent):
        super().__init__(parent, size=(-1, 400))
        self._renderer = GLPreviewRenderer()
        self._build_ui()

    def _build_ui(self):
        # Setup GL canvas or static bitmap
        self.canvas = wx.wxGLCanvas(self)
        self._renderer.init_gl(self.canvas)

    def update_preview(self, image_path: Path):
        """Refresh preview from rendered image."""
        self._renderer.load_image(image_path)
        self.canvas.Refresh()

    def clear(self):
        """Clear preview."""
        self._renderer.clear()
        self.canvas.Refresh()
```

**Lines extracted:** ~150 → **80 lines**

#### 6. layout_constants.py

**Extract magic numbers from:** throughout `main_panel.py`

```python
# ui/layout_constants.py
"""Physical layout constants for SpinRender UI."""

# Panel heights
STATUS_BAR_HEIGHT = 80
PREVIEW_HEIGHT = 400
PRESET_CARD_WIDTH = 280
PRESET_CARD_HEIGHT = 120
HEADER_HEIGHT = 48

# Sizer gaps
SECTION_GAP = 24
ITEM_SPACING = 16
BUTTON_GAP = 12
CARD_SPACING = 8

# Minimum sizes
SLIDER_HEIGHT = 18
TOGGLE_HEIGHT = 32
BUTTON_HEIGHT = 36
INPUT_HEIGHT = 36

# Padding
PANEL_PADDING = 16
DIALOG_PADDING = 24

# Shadow
SHADOW_SIZE = 16
```

### Refactoring Strategy

**Step 1: Extract without deleting (safe migration)**

For each module:
1. Create new file with class definition
2. Copy relevant methods from `main_panel.py`
3. Update imports (use relative imports from `ui/` package)
4. Add `__init__.py` exports
5. Do NOT delete old code yet
6. Update `main_panel.py` to import and delegate:

```python
# main_panel.py (after extraction)
from .render_executor import RenderExecutor
from .settings_manager import SettingsManager
from .status_panel import StatusPanel
from .preset_panel import PresetPanel
from .preview_panel import PreviewPanel

class SpinRenderPanel(wx.Panel):
    def __init__(self, parent, plugin):
        super().__init__(parent)

        # Extract managers
        self._executor = RenderExecutor()
        self._settings_mgr = SettingsManager(plugin.board_path)
        self.settings = self._settings_mgr.settings  # property access

        # Build UI from sub-panels
        self._build_layout()

        # Extract status panel
        self.status_panel = StatusPanel(self)
        # ... etc
```

**Step 2: Verify extraction completeness**

- Run plugin, exercise all features
- Ensure no missing attributes or methods
- All tests pass (if any)

**Step 3: Remove dead code**

- Delete extracted methods/properties from `main_panel.py`
- Remove unused imports
- Verify line count: `main_panel.py` should drop from 1542 → ~300 lines

**Step 4: Document new structure**

Update `docs/ARCHITECTURE.md` with:
- Module diagram
- Data flow between components
- Public API of each module

### Implementation Phases

#### Phase 1: Preparation (Them Complete)

- Complete theme migration (colors no longer hardcoded)
- Complete Settings Validation Layer (typed settings)
- This simplifies extraction: settings moved to `SettingsManager` with type hints

#### Phase 2: Extract Layout Constants (Low Risk)

1. Create `layout_constants.py`
2. Search/replace magic numbers in `main_panel.py`:
   - `size=(-1, 48)` → `size=(-1, HEADER_HEIGHT)`
   - `wx.ALL, 16` → `wx.ALL, PANEL_PADDING`
   - Do this **incrementally** with git commits per constant group
3. Run frequently to catch layout breaking

**Order of replacement:**
1. Panel heights (STATUS_BAR_HEIGHT, PREVIEW_HEIGHT, etc.)
2. Sizer gaps (SECTION_GAP, ITEM_SPACING, etc.)
3. Minimum sizes (BUTTON_HEIGHT, SLIDER_HEIGHT, etc.)
4. Padding values (PANEL_PADDING, CARD_SPACING)

**Verification:** Screenshot comparison after each batch

#### Phase 3: Low-Risk Extractions (Independent)

Extract in this order (least coupling):

1. **PreviewPanel** — single dependency on `core.preview`
2. **StatusPanel** — single dependency on `utils.logger`
3. **SettingsManager** — single dependency on `core.settings`

Procedure for each:
- Create file
- Copy relevant code, fix imports
- Instantiate in `main_panel.__init__`
- Replace old code with delegation
- Test that feature works
- Delete old code from `main_panel.py`
- Commit small increments

#### Phase 4: Medium-Risk Extractions (Some Coupling)

4. **PresetPanel** — depends on `core.presets` and `custom_controls`
   - More complex: `refresh()` method rebuilds UI
   - Must preserve scroll behavior, selection logic

5. **RenderExecutor** — depends on `core.renderer`, threading
   - Critical path: render execution must work exactly as before
   - Comprehensive testing: start render, cancel, errors

#### Phase 5: High-Risk Integration (Final)

6. Remove remaining `main_panel.py` code
7. Verify all event handlers still wired correctly
8. Comprehensive UI test checklist (see below)

### Testing Checklist

**Functional verification per extracted panel:**

| Panel | Test Cases |
|-------|------------|
| PreviewPanel | Load image, clear, resize window, dark/light themes |
| StatusPanel | Status updates, progress bar, log button opens folder |
| SettingsManager | Load/save, defaults, missing file handling |
| PresetPanel | List presets, recall, save, delete, refresh |
| RenderExecutor | Start render, cancel mid-render, concurrent renders blocked, error handling |

**Integration tests:**
- [ ] Full render workflow: adjust settings → click render → preview appears → status updates
- [ ] Save preset, recall preset, delete preset
- [ ] Toggle logging level, restart plugin, persists
- [ ] Open dialogs, change settings, OK/Cancel behavior
- [ ] All buttons clickable, sliders drag, toggles work

**Regression:**
- Screenshot comparison against baseline (before refactor)
- Verify no visual regressions in spacing, colors, alignment

### Risk Mitigation

**Risk:** Extraction breaks subtle state sharing between methods
**Mitigation:**
- Keep all instance attributes **in main_panel** initially, pass explicitly to sub-panels
- Only extract persistent state to sub-panels after coordination proven to work
- Use `@property` for computed state access, not stored in multiple places

**Risk:** Event handlers lose binding context
**Mitigation:**
- Before extraction: grep for all `self.Bind(` in `main_panel.py`
- After extraction: verify ALL bindings still present (in `main_panel` or sub-panels)
- `main_panel` can bind to sub-panel events via sub-panel's custom events

**Risk:** Layout breaks after constant extraction
**Mitigation:**
- Use `layout_constants.py` as single source of truth
- No magic numbers anywhere post-refactor
- Run `grep -r "size=.*[0-9]" SpinRender/ui/main_panel.py` to find stragglers

### Dependencies & Order

- **Requires:** Theme migration (for color tokens), Settings Validation (for typed settings)
- **Blocks:** None (standalone large refactor)
- **Parallel with:** State Management (helps centralize state before extraction)
- **Recommended order:** State Management → Extract constants → Extract panels one-by-one

### Success Metrics

- `main_panel.py` line count: **≤ 400 lines** (from 1542)
- Each extracted module: **≤ 250 lines**
- Zero circular imports
- All 60+ unit/integration tests pass (if present)
- Zero regressions in manual KiCad testing

---

## 7. State Management Unification

**Status:** Early refactor (before God Class Extraction)
**Dependencies:** None (theme-independent)
**Risk:** HIGH | **Impact:** HIGH

### Problem Statement

State scattered across five storage mechanisms:

| Mechanism | Examples | Issues |
|-----------|----------|--------|
| Class constants | `SpinRenderPanel.BG_PAGE` (theme migration addresses) | Hardcoded, no runtime change |
| Instance attributes | `self.current_render`, `self.selected_preset` (main_panel) | Disorganized, no lifecycle management |
| Module globals | `_LOAD_ATTEMPTED` in custom_controls.py | Hidden coupling, testing difficulty |
| Singleton pattern | `Theme.current()` singleton | Global state, testing pain |
| JSON persistence | `settings.json` | No schema, type unsafe |

### Unification Strategy

Adopt **explicit state container** pattern:

```python
# ui/state_container.py (new module)
from dataclasses import dataclass, field
from typing import Any
from contextlib import contextmanager

@dataclass
class StateContainer:
    """
    Centralized mutable state with change tracking and scoping.
    Replaces ad-hoc self attributes and module globals.
    """
    _data: dict[str, Any] = field(default_factory=dict)
    _listeners: dict[str, list[callable]] = field(default_factory=lambda: defaultdict(list))

    def get(self, key: str, default=None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any, notify=True) -> None:
        old = self._data.get(key)
        self._data[key] = value
        if notify and old != value:
            self._notify(key, old, value)

    def subscribe(self, key: str, callback: callable) -> None:
        """Subscribe to changes on a specific key."""
        self._listeners[key].append(callback)

    def _notify(self, key: str, old: Any, new: Any):
        for cb in self._listeners.get(key, []):
            try:
                cb(key, old, new)
            except Exception as e:
                logger.error(f"State listener error: {e}")

    @contextmanager
    def transaction(self):
        """Batch updates without intermediate notifications."""
        old_notify = self._listeners.copy()
        self._listeners.clear()
        try:
            yield
        finally:
            self._listeners = old_notify

    def snapshot(self) -> dict:
        """Return immutable copy of current state."""
        return MappingProxyType(self._data.copy())

    def clear(self):
        """Reset all state."""
        self._data.clear()
```

**Usage:**

```python
# main_panel.py
from .state_container import StateContainer

class SpinRenderPanel(wx.Panel):
    def __init__(self, parent, plugin):
        super().__init__(parent)
        self.state = StateContainer()

        # Define initial state
        self.state.set('is_rendering', False)
        self.state.set('current_preset', None)
        self.state.set('log_buffer', [])

        # Subscribe to state changes
        self.state.subscribe('is_rendering', self.on_rendering_changed)

    def on_render_click(self, event):
        self.state.set('is_rendering', True)  # triggers on_rendering_changed

    def on_rendering_changed(self, key, old, new):
        self.status_panel.set_rendering(new)
```

### Migration Plan

#### Phase 1: Audit Current State

Document all state locations in `main_panel.py`:

```bash
grep -n "self\." main_panel.py | grep -E "=" | head -50
```

Create inventory:

| Attribute | Line | Category | Should be in StateContainer? |
|-----------|------|----------|----------------------------|
| `self.current_render` | ~450 | render state | Yes |
| `self.selected_preset` | ~950 | selection | Yes |
| `self.board_path` | ~100 | config | Maybe (read-only) |
| `self._last_export_dir` | ~200 | cache | Yes |
| `self.settings` | ~150 | config | Keep (moved to SettingsManager) |
| ... | ~50 more | | |

#### Phase 2: Categorize State

**Categorization schema:**

1. **Configuration** (read-only after init): board_path, plugin reference
   - → Keep as instance attributes
2. **Transient UI state**: is_rendering, selected_preset, slider_values
   - → Move to StateContainer
3. **Settings** → Move to SettingsManager (separate refactor)
4. **Cache**: recently used paths, loaded images
   - → Move to StateContainer (with TTL if needed)

#### Phase 3: Incremental Migration

**Step 1: Create StateContainer, replace smallest attributes first**

Example: `_last_export_dir` cache

**Before:**
```python
class SpinRenderPanel:
    def __init__(self, ...):
        self._last_export_dir = None
    def on_browse(self, event):
        start_dir = self._last_export_dir or default
```

**After:**
```python
class SpinRenderPanel:
    def __init__(self, ...):
        self.state = StateContainer()
        self.state.set('last_export_dir', None)
    def on_browse(self, event):
        start_dir = self.state.get('last_export_dir') or default
```

**Step 2: Migrate flags with observers**

Example: `is_rendering` triggers UI updates

**Before:**
```python
self.is_rendering = False
# ...
def start_render(self):
    self.is_rendering = True
    self.status_panel.set_rendering(True)
```

**After:**
```python
self.state.set('is_rendering', False)
self.state.subscribe('is_rendering', self._on_is_rendering_changed)
# ...
def start_render(self):
    self.state.set('is_rendering', True)  # callback fires
def _on_is_rendering_changed(self, key, old, new):
    self.status_panel.set_rendering(new)
```

**Step 3: Group related state**

Example: preset selection state

```python
# Before: self.selected_preset, self.selected_name
# After:
self.state.set('preset.selected', None)
self.state.set('preset.name', None)
# or nested:
self.state.set('preset', {'data': None, 'name': None})
```

#### Phase 4: Remove Module Globals

**Target:** `custom_controls.py:_LOAD_ATTEMPTED`

**Before:**
```python
_LOAD_ATTEMPTED = False
def ensure_fonts_loaded():
    global _LOAD_ATTEMPTED
    if _LOAD_ATTEMPTED: return
    _LOAD_ATTEMPTED = True
    # load fonts
```

**After:**
```python
class FontLoader:
    _attempted = False
    @classmethod
    def ensure(cls):
        if cls._attempted: return
        cls._attempted = True
        # load fonts

def ensure_fonts_loaded():
    FontLoader.ensure()
```

Or use function attribute:
```python
def ensure_fonts_loaded():
    if getattr(ensure_fonts_loaded, 'attempted', False):
        return
    ensure_fonts_loaded.attempted = True
    # load fonts
```

Better: Turn into class with explicit state:
```python
class FontManager:
    def __init__(self):
        self._loaded = False

    def ensure_loaded(self):
        if self._loaded:
            return
        # load fonts
        self._loaded = True

# Global singleton (explicit)
font_manager = FontManager()

def ensure_fonts_loaded():
    font_manager.ensure_loaded()
```

**This is a singleton but with explicit state** — acceptable for font loading.

#### Phase 5: Integrate with Settings

`SettingsManager` should store settings in StateContainer?

**Decision:** No — SettingsManager owns `RenderSettings` instance. StateContainer holds transient runtime state only.

```
SpinRenderPanel
├── state: StateContainer          # transient UI state
├── settings_mgr: SettingsManager  # persistent settings
└── executor: RenderExecutor       # runtime executor
```

### Validation & Testing

**Unit tests for StateContainer:**

```python
def test_state_set_and_get():
    c = StateContainer()
    c.set('key', 'value')
    assert c.get('key') == 'value'

def test_state_subscribe():
    c = StateContainer()
    changes = []
    c.subscribe('key', lambda k, o, n: changes.append((k, n)))
    c.set('key', 'a')
    c.set('key', 'b')
    assert changes == [('key', 'a'), ('key', 'b')]

def test_state_transaction():
    c = StateContainer()
    changes = []
    c.subscribe('key', lambda k, o, n: changes.append((k, n)))
    with c.transaction():
        c.set('key', 'a')
        c.set('key', 'b')  # only final notifies
    assert changes == [('key', 'b')]
```

**Integration test:**
- Replace `self.is_rendering` with `self.state.set('rendering', ...)`
- Verify status panel updates automatically via subscription
- Verify multiple subscribers can listen to same key

### Dependencies & Order

- **Can start immediately** (no theme dependency)
- **Required before God Class Extraction** (to keep extracted modules clean)
- **Parallel with:** Dependency Fix (both touch globals)
- **Blocks:** God Class Extraction (to provide clean state management in sub-panels)

### Success Criteria

- [ ] All module globals eliminated or encapsulated in classes
- [ ] >80% of `main_panel` instance attributes moved to `StateContainer`
- [ ] Zero direct attribute assignments for state (use `state.set()`)
- [ ] All state changes observable (via subscriptions)
- [ ] No circular dependencies on StateContainer (it's foundational)
- [ ] StateContainer has unit tests (80%+ coverage)

---

## 8. Settings Schema (Typed Settings)

**Status:** Covered in Section 4 (Validation Layer) — implementation as `RenderSettings` dataclass

**Note:** This is part of the Validation Layer work, not a separate effort.

---

## Integration with Theme Migration (MIGRATION_STRATEGY.md)

### Dependency Graph (Combined)

```
Phase 1: Theme Migration (MIGRATION_STRATEGY.md)
  1. Create ui/theme.py
  2. Update custom_controls.py
  3. Update dialogs.py
  4. Update main_panel.py
  5. Update ui/__init__.py

Phase 2: Parallel Refactors (can start after Phase 1 or interleaved)
  A. Dependency Fix (utils → ui inversion)
     - 0. Audit current imports
     - 1. Create foundation/ if needed
     - 2. Move cycle-causing code
     - 3. Update imports

  B. State Management Unification
     - 1. Create state_container.py
     - 2. Migrate main_panel attributes incrementally
     - 3. Remove module globals

  C. Typography System
     - 1. Create text_styles.py
     - 2. Update theme.yaml with font presets (if not already)
     - 3. Refactor custom controls one-by-one

  D. Component Construction Alignment
     - 1. Create base_components.py, component_factory.py
     - 2. Refactor controls in dependency order (simple→complex)
     - 3. Update main_panel/dialogs instantiation patterns

  E. Interaction Integrity
     - 1. Create event_utils.py, transparent_label.py
     - 2. Apply pass-through to affected controls

  F. Validation Layer
     - 1. Create core/validation.py
     - 2. Enhance core/theme.py with validation
     - 3. Implement RenderSettings in core/settings.py
     - 4. Update main_panel & dialogs to use typed settings

  G. God Class Extraction (requires B + D + F)
     - 1. Extract layout_constants.py (string replacements)
     - 2. Extract preview, status, settings mgr, preset panel, render executor
     - 3. Reduce main_panel.py to ~300 lines

Phase 3: Final Polish
  - Run full test suite
  - Visual regression testing
  - Documentation updates
  - Performance profiling
```

### Phase Ordering Rationale

**Theme migration first** — provides the color/font tokens that all other refactors consume. Doing this first prevents massive merge conflicts.

**Dependency fix early** — cleans architecture before large refactors spread.

**State management before God Class** — extracted panels need clean state container.

**Typography after theme** — depends on font token definitions.

**Component construction before/parallel with typography** — both touch controls; doing together has synergy.

**Validation layer late** — depends on synthesized understanding from other refactors (what needs validating).

**God class last** — largest, riskiest, benefits from all other improvements.

### Parallel Execution Plan

Teams (or sequential agents) can work simultaneously on:

- **Team A:** Theme migration (docs/MIGRATION_STRATEGY.md)
- **Team B:** Dependency fix + State management
- **Team C:** Typography + Component construction
- **Team D:** Interaction integrity + Validation layer

**Merge coordination:**
1. Theme migration merged first to `main`
2. Other branches rebased on `main` after theme merge
3. Resolution of conflicts in `custom_controls.py` (all branches touch it)
4. Sequential merges with extensive testing between each

---

## File Modification Order (Complete List)

### New Files to Create

1. `SpinRender/ui/text_styles.py`
2. `SpinRender/ui/base_components.py`
3. `SpinRender/ui/component_factory.py`
4. `SpinRender/ui/event_utils.py`
5. `SpinRender/ui/transparent_label.py`
6. `SpinRender/core/validation.py`
7. `SpinRender/core/settings.py`
8. `SpinRender/ui/render_executor.py`
9. `SpinRender/ui/settings_manager.py`
10. `SpinRender/ui/status_panel.py`
11. `SpinRender/ui/preset_panel.py`
12. `SpinRender/ui/preview_panel.py`
13. `SpinRender/ui/layout_constants.py`
14. `SpinRender/ui/state_container.py`
15. `test/core/test_validation.py`
16. `test/ui/test_text_styles.py`
17. `test/ui/test_state_container.py`

### Existing Files to Modify

1. **Theme Migration:**
   - `SpinRender/ui/theme.py` (create)
   - `SpinRender/ui/custom_controls.py` (replace colors)
   - `SpinRender/ui/dialogs.py` (replace colors)
   - `SpinRender/ui/main_panel.py` (replace colors)
   - `SpinRender/ui/__init__.py` (expose theme)

2. **Typography:**
   - All 13 custom controls (add style parameters, use TextStyle)

3. **Component Construction:**
   - All 13 custom controls (inherit from base classes)
   - `SpinRender/ui/main_panel.py` (use factory functions)
   - `SpinRender/ui/dialogs.py` (use base classes, factory functions)

4. **Interaction Integrity:**
   - `SpinRender/ui/dialogs.py` (PresetCard → TransparentLabel)
   - `SpinRender/ui/custom_controls.py` (SectionLabel, NumericDisplay)

5. **Validation:**
   - `SpinRender/core/theme.py` (add validation)
   - `SpinRender/ui/main_panel.py` (use RenderSettings)
   - `SpinRender/ui/dialogs.py` (use RenderSettings)
   - `SpinRender/spinrender_plugin.py` (load validated settings)

6. **State Management:**
   - `SpinRender/ui/main_panel.py` (replace attrs with StateContainer)

7. **God Class Extraction:**
   - `SpinRender/ui/main_panel.py` (massive reduction)
   - Plus all extracted modules (see New Files)

---

## Estimated Effort (in developer days)

| Task | Owner | Complexity | Est. Days |
|------|-------|------------|-----------|
| Theme migration (MIGRATION_STRATEGY.md) | A | Medium | 2-3 |
| Dependency fix | B | High | 2-3 |
| State management | B | Medium | 1-2 |
| Typography system | C | Medium | 2-3 |
| Component construction | C | High | 3-4 |
| Interaction integrity | D | Low | 1 |
| Validation layer | D | Medium | 2-3 |
| God class extraction | E | Very High | 4-5 |
| Testing & integration | All | Medium | 3-4 |
| **Total** | | | **~18-25 days** |

Assuming 2-3 developers working in parallel: **~2-3 weeks** to complete all non-theme refactoring.

---

## Key Risks and Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Circular dependencies after extraction | High | High | Run `pyflakes`/`mypy` after each file move; enforce one-way dependency rule |
| Visual regressions (spacing, colors) | Medium | High | Screenshot baseline; pixel-diff after each phase |
| Lost state during God class extraction | Medium | High | Comprehensive state inventory first; integration tests |
| Breaking existing plugin functionality | Medium | Very High | Deploy to test KiCad instance after each phase; manual QA checklist |
| Theme token resolution errors at runtime | Medium | Medium | Validate all tokens in CI; fail fast with clear errors |
| Threading issues in RenderExecutor | Low | High | Extensive cancellation and error path testing |
| Contrast checker false positives | Low | Low | Make validation opt-in initially; tune thresholds |

---

## Conclusion

This plan provides a comprehensive roadmap for transforming the SpinRender UI from a tightly-coupled monolith into a well-architected, maintainable system. Success depends on:

1. **Theme migration completed first** — establishes single source of truth
2. **Incremental, verifiable steps** — no giant refactors; test after each
3. **Parallelization** — multiple workstreams after theme
4. **Continuous integration** — automated validation, type checking, tests
5. **Risk-aware sequencing** — high-risk work (God class) done after foundations solid

**Next steps:**
1. Create task list from this document (use `TaskCreate` for each major phase)
2. Assign team members or schedule sequential agent execution
3. Begin with theme migration (already documented in docs/MIGRATION_STRATEGY.md)
4. After theme merge, start parallel refactors: Dependency Fix + State Management

**Deliverables:** This document + supporting code files in `SpinRender/` implementing each phase.

---

**Document Version:** 1.0
**Date:** 2026-03-13
**Related Documents:**
- docs/UI_REFACTOR.md
- docs/MIGRATION_STRATEGY.md
- docs/THEME_SCHEMA.md
