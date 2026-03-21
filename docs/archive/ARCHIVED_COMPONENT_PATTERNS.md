# Component Construction Patterns

## Overview

This document defines the unified construction pattern for all custom controls in SpinRender. Following these patterns ensures consistency, maintainability, and reduces code duplication.

## Standard Construction Sequence

All custom controls should follow this canonical sequence in their `__init__` method:

1. **Initialize parent class** (`super().__init__(parent)`)
2. **Set instance properties** (size hints, min/max dimensions)
3. **Create main container** using `create_frame(self, style_token)`
4. **Build UI components** (sub-widgets, text, controls)
5. **Apply layout** (sizers, positioning)
6. **Bind events** using `bind_mouse_events()` and specific handlers
7. **Set initial state** (enabled/disabled, selected/unselected)

## Helper API Reference

### `create_frame(parent, style_token, **kwargs)`

Creates a themed panel with background color from theme module.

```python
def create_frame(parent: wx.Window, style_token: str, **kwargs) -> wx.Panel:
    """Create a themed panel.

    Args:
        parent: Parent wx.Window
        style_token: Theme token name (e.g., 'BG_INPUT', 'BG_SURFACE')
        **kwargs: Additional wx.Panel constructor args (style, pos, size, etc.)

    Returns:
        wx.Panel with background colour from theme token

    Raises:
        ValueError: If token is not recognized
    """
```

**Valid tokens:**
- Background: `BG_PAGE`, `BG_PANEL`, `BG_INPUT`, `BG_SURFACE`, `BG_MODAL`
- Borders: `BORDER_DEFAULT`, `BORDER_MODAL`, `BORDER_FOCUS`
- Accents: `ACCENT_CYAN`, `ACCENT_YELLOW`, `ACCENT_GREEN`, `ACCENT_ORANGE`, `ACCENT_RED`, `ACCENT_AMBER`, `ACCENT_BLUE`, `ACCENT_PURPLE`
- Text: `TEXT_PRIMARY`, `TEXT_SECONDARY`, `TEXT_MUTED`

### `create_text(parent, label, text_style, **kwargs)`

Creates a `wx.StaticText` with font and foreground colour from a `TextStyle`.

```python
def create_text(parent: wx.Window, label: str, text_style: TextStyle, **kwargs) -> wx.StaticText:
    """Create StaticText with TextStyle applied.

    Args:
        parent: Parent wx.Window
        label: Text to display
        text_style: TextStyle object with font/color specifications
        **kwargs: Additional wx.StaticText constructor args (style, pos, etc.)

    Returns:
        wx.StaticText with font and foreground colour set
    """
```

### `bind_mouse_events(widget, hover_handler=None, leave_handler=None, click_handler=None)`

Binds standard mouse event handlers to a widget.

```python
def bind_mouse_events(
    widget: wx.Window,
    hover_handler: Optional[Callable] = None,
    leave_handler: Optional[Callable] = None,
    click_handler: Optional[Callable] = None
) -> None:
    """Bind standard mouse event handlers.

    - EVT_ENTER_WINDOW → hover_handler
    - EVT_LEAVE_WINDOW → leave_handler
    - EVT_LEFT_DOWN → click_handler

    Only binds handlers that are provided (not None).
    """
```

### `apply_disabled_state(widget, is_enabled)`

Applies visual disabled state (50% opacity) to widget background using `theme.disabled()`.

```python
def apply_disabled_state(widget: wx.Window, is_enabled: bool) -> None:
    """Apply disabled state visual effect to widget background.

    Uses theme.disabled() to apply 50% opacity to the current background colour.

    Args:
        widget: wx.Window to modify
        is_enabled: True for normal state, False for disabled
    """
```

## Template: Simple Control

Simple controls have a single container and minimal child widgets.

**Example: CustomButton (simplified)**

```python
class CustomButton(wx.Panel):
    def __init__(self, parent, label, text_style, callback=None, size=None):
        super().__init__(parent)

        # 1. Size hints
        self.SetMinSize(size or (120, 40))

        # 2. Main container (themed background)
        self.main_frame = create_frame(self, 'BG_INPUT')

        # 3. Child components
        self.label = create_text(self.main_frame, label, text_style)

        # 4. Layout
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label, 1, wx.ALIGN_CENTER)
        self.main_frame.SetSizer(sizer)

        # 5. Event binding
        bind_mouse_events(
            self.main_frame,
            hover_handler=self._on_hover,
            click_handler=lambda e: callback() if callback else None
        )

        # 6. Initial state
        self._enabled = True
```

## Template: Compound Control

Compound controls have multiple sub-widgets, complex layouts, or subsidiary windows (popups).

**Example: CustomSlider structure**

```python
class CustomSlider(wx.Panel):
    def __init__(self, parent, min_val=0, max_val=100, value=50):
        super().__init__(parent)

        # 1. Main themed container
        self.main_frame = create_frame(self, 'BG_INPUT')

        # 2. Build sub-widgets
        self.track = wx.Panel(self.main_frame)  # custom painted
        self.thumb = wx.Panel(self.main_frame)  # draggable handle
        self.value_label = create_text(self.main_frame, str(value), TextStyles.numeric_value)

        # 3. Layout (could be absolute for custom paint, or sizers)
        self.track.SetPosition((10, 20))
        self.thumb.SetPosition((45, 18))
        self.value_label.SetPosition((60, 5))

        # 4. Event binding for each interactive element
        bind_mouse_events(self.track, click_handler=self._on_track_click)
        bind_mouse_events(self.thumb, hover_handler=self._on_thumb_hover, click_handler=self._on_thumb_drag)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_LEFT_UP, self.on_release)

        # 5. Initial state
        self.value = value
        self.enabled = True
```

## Event Binding Patterns

### Mouse Interactions

Use `bind_mouse_events()` for standard hover/click behavior:

```python
bind_mouse_events(
    widget=self.main_frame,
    hover_handler=self._on_enter,
    leave_handler=self._on_leave,
    click_handler=self._on_click
)
```

### Custom Paint

For controls that override `EVT_PAINT`, bind directly:

```python
self.Bind(wx.EVT_PAINT, self.on_paint)
```

### Focus/Keyboard

For focusable controls (inputs, buttons with keyboard shortcuts), bind directly:

```python
self.Bind(wx.EVT_SET_FOCUS, self.on_focus_gained)
self.Bind(wx.EVT_KILL_FOCUS, self.on_focus_lost)
self.Bind(wx.EVT_CHAR, self.on_char)  # key events
```

### Size Events

For responsive layouts:

```python
self.Bind(wx.EVT_SIZE, self.on_size)
```

## Disabled State Management

Apply disabled state using the helper:

```python
def set_enabled(self, enabled=True):
    self._enabled = enabled
    apply_disabled_state(self.main_frame, enabled)
    # Also apply to children if needed
    for child in [self.label, self.icon]:
        apply_disabled_state(child, enabled)
```

**Note:** `apply_disabled_state()` only modifies background colours. For more complex disabled states (e.g., greying out text, disabling event binding), extend as needed:

```python
def set_enabled(self, enabled=True):
    self._enabled = enabled
    apply_disabled_state(self.main_frame, enabled)
    if enabled:
        bind_mouse_events(self.main_frame, hover_handler=self._on_hover, click_handler=self._on_click)
    else:
        # Unbind by binding to a no-op or using a flag in handlers
        pass
```

## Migration Checklist

When refactoring existing controls to use helpers:

- [ ] Replace class-level color constants (e.g., `BG_INPUT = theme.BG_INPUT`) with direct `theme.*` usage
- [ ] Replace `_get_paint_color()` helper with direct `theme.disabled()` calls
- [ ] Use `create_frame(self, token)` for main container
- [ ] Use `create_text(parent, label, style)` for all StaticText creation
- [ ] Replace direct `Bind()` calls for mouse events with `bind_mouse_events()`
- [ ] Ensure all `wx.Panel` and `wx.StaticText` creations can accept the fake test doubles
- [ ] Verify color tokens are from the valid set (no hardcoded `wx.Colour(r,g,b)` anywhere)
- [ ] Update tests to verify usage of helpers (where relevant)

## Common Pitfalls

### Don't: Use class-level color constants

```python
class MyControl(wx.Panel):
    BG_COLOR = theme.BG_INPUT  # Unnecessary indirection
```

**Do:** Use `theme.BG_INPUT` directly in `create_frame()`.

### Don't: Reimplement `_get_paint_color()` logic

```python
def on_paint(self, event):
    if not self.enabled:
        brush = wx.Brush(wx.Colour(c.Red(), c.Green(), c.Blue(), 128))  # duplicate
```

**Do:** Use `theme.disabled(theme.BG_SURFACE)` directly.

### Don't: Forget to expose children for testing

If your control creates child widgets that need to be tested, store them as instance attributes (e.g., `self.label`, `self.icon`) rather than local variables.

## Example Migrations

### Before: CustomButton (old style)

```python
class CustomButton(wx.Panel):
    def __init__(self, parent, label, size=None, callback=None):
        super().__init__(parent)
        self.SetBackgroundColour(theme.BG_INPUT)
        self.text = wx.StaticText(self, label=label)
        self.text.SetFont(get_custom_font(11, weight=wx.FONTWEIGHT_NORMAL))
        self.text.SetForegroundColour(theme.TEXT_PRIMARY)
        self.Bind(wx.EVT_LEFT_DOWN, lambda e: callback() if callback else None)
```

### After: CustomButton (unified)

```python
class CustomButton(wx.Panel):
    def __init__(self, parent, label, text_style, callback=None, size=None):
        super().__init__(parent)
        self.SetMinSize(size or (120, 40))

        self.main_frame = create_frame(self, 'BG_INPUT')
        self.label = create_text(self.main_frame, label, text_style)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label, 1, wx.ALIGN_CENTER)
        self.main_frame.SetSizer(sizer)

        bind_mouse_events(
            self.main_frame,
            hover_handler=self._on_hover,
            click_handler=lambda e: callback() if callback else None
        )

        self._enabled = True
```

## Verification

After refactoring a control, verify:

- [ ] No hardcoded `wx.Colour(r, g, b)` calls remain (except in theme.py)
- [ ] No `_get_paint_color()` calls remain
- [ ] `get_custom_font()` not used (TextStyle only)
- [ ] Main container created with `create_frame()`
- [ ] All StaticText created with `create_text()`
- [ ] Mouse bindings use `bind_mouse_events()` (except special cases)
- [ ] Disabled state uses `apply_disabled_state()`
- [ ] Control renders identically to pre-migration version
- [ ] Unit tests still pass
- [ ] Integration tests updated (if needed)
