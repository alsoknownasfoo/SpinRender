# ID-Driven Component Mapping System (V2)

## Overview

SpinRender uses a "Convention over Configuration" approach for UI components. By leveraging unique identifiers (`id`), components automatically derive their content from the **Locale** system and their visual styling from the **Theme** system.

This approach enforces the **"YAML is Truth"** principle: code should describe *what* a component is (its ID and purpose), while YAML defines *how* it looks and what it says.

---

## The ID-Driven Pattern

When a component (like `CustomButton`) is initialized with a string ID, it performs a dual-resolution:

1.  **Content Resolution (Locale)**:
    -   Label: `component.button.{id}.label`
    -   Icon: `component.button.{id}.icon_ref`
2.  **Style Resolution (Theme)**:
    -   Token Base: `components.button.{id}`
    -   Derives: `frame.bg`, `frame.border.color`, `label.color` (including hover/pressed states).

### Example: The Render Button

**Code:**
```python
self.render_btn = CustomButton(parent, id="render")
```

**Locale (`en.yaml`):**
```yaml
component.button:
  render:
    label: "RENDER"
    icon_ref: "glyphs.render-action"
```

**Theme (`dark.yaml`):**
```yaml
components:
  button:
    render:
      ref: "@components.button.ok"  # Inherits from primary button style
      frame:
        bg: "@colors.gray-dark" # Single variable override
        
```
OR
```yaml
components:
  button:
    render:
      ref: "@components.button.ok"  # Inherits from primary button style
      frame:
        bg: 
            default: "@colors.gray-dark" # Overrides as individual callouts
            hover: "@colors.primary" 
        
```


---

## Constructor Logic

The simplified constructor supports both legacy manual overrides and the new automated pattern.

```python
def __init__(self, parent, label=None, icon=None, ..., id=wx.ID_ANY):
    if isinstance(id, str):
        self.style_id = id  # "render", "save", "cancel"
        # 1. Fetch Label from locale if not provided
        # 2. Fetch Icon reference from locale if not provided
```

### Manual Overrides
You can still override specific properties while keeping the base style:
```python
# Uses "ok" colors/border but custom text
btn = CustomButton(parent, id="ok", label="PROCEED") 
```

---

## Dynamic State Management

Components can switch their entire visual and content profile at runtime using `SetStyle`.

### Example: Render vs. Stop State

When the user clicks "Render", the button transforms into a "Stop" button. Instead of manually changing colors, icons, and labels, we simply switch the style ID.

```python
# Switch to "exit" style (red/danger) but keep custom "STOP" label
self.render_btn.SetStyle("exit", update_content=False)
self.render_btn.SetLabel("STOP")

# Switch back to default "render" style
self.render_btn.SetStyle("render")
```

### Example: Save vs. Overwrite State

In the `SavePresetDialog`, the button detects if a name conflict exists:

```python
if is_overwrite:
    # Use "exit" theme tokens for red warning look
    self.save_btn.SetStyle("exit", update_content=False)
    self.save_btn.SetLabel("OVERWRITE")
else:
    # Revert to standard "save" style
    self.save_btn.SetStyle("save")
```

---

## Benefits

1.  **Reduced Boilerplate**: Constructor calls are reduced from 5-8 lines down to 1 line.
2.  **Centralized Control**: Changing a button's color or icon across the entire app happens in a single YAML file.
3.  **State Consistency**: Hover and pressed states are automatically managed by the `Theme` singleton using the resolved `token` path.
4.  **Cleaner Code**: UI logic focuses on *intent* (switching to an "exit" style) rather than *implementation* (setting background to `#FF3B30`).

---

## Implementation Checklist

When adding a new button ID:

1.  **Locale**: Add `label` and `icon_ref` under `component.button.{id}`.
2.  **Theme**: Add entry under `components.button.{id}`. Use `ref` to inherit from `ok`, `cancel`, `close`, or `default` to avoid duplication.
3.  **Code**: Instantiate using `CustomButton(parent, id="id")`.

## Stateful Color Resolution

SpinRender uses `Theme.color_states(token, states=3)` to resolve interactive colors. This function ensures that components always have feedback, even if the theme only defines a single base color.

### Resolution Logic

1.  **Explicit List**: If the token is a list, it uses the elements as `[normal, hover, active, disabled]`.
    ```yaml
    bg: ["@colors.gray-black", "@colors.gray-medium", "@colors.gray-dark", "@colors.gray-light"]
    ```
2.  **Explicit Dictionary**: If the token is a dict with `hover` or `active` keys, it maps them accordingly.
    ```yaml
    frame:
      bg: "@colors.primary"
      hover: "rgba(0, 188, 212, 0.8)"
      active: "@colors.cyan-dark"
    ```
3.  **Sibling Lookup**: If you request `...frame.bg`, the system automatically checks for `...frame.hover` and `...frame.active` in the same parent node.
4.  **Auto-Generation (The Fallback)**: If only one color is found, the system auto-generates the other states:
    -   **Hover**: Base color shifted +10 RGB (brighter).
    -   **Active/Pressed/Selected**: Base color shifted -10 RGB (darker).
    -   **Disabled**: Alpha is shifted to 50%.

### Best Practice
When migrating, use `_theme.color_states(token)` and store the resulting list. Then, in `on_paint`, select the color based on component state:

```python
colors = _theme.color_states("components.button.ok.frame.bg")
if self.disabled: bg = colors[3]
elif self.active: bg = colors[2]
elif self.hovered: bg = colors[1]
else: bg = colors[0]
```

---

## Core Component Patterns (Migration Guide)

When migrating other complex components (Sliders, Toggles, Inputs) to the V2 pattern, ensure the following behaviors are preserved:

### 1. Mouse Event Handling
*   **Helper Usage**: Use `bind_mouse_events(self, ...)` in the constructor for standard hover/click logic.
*   **Direct Bindings**: For drag-and-drop or complex motion (e.g., `CustomSlider`), bind `wx.EVT_MOTION` and `wx.EVT_LEFT_UP` directly to the panel.
*   **Event Capture**: Components that track mouse movement outside their bounds (like Sliders during drag) **MUST** call `self.CaptureMouse()` on down-click and `self.ReleaseMouse()` on up-click to prevent "lost" mouse events.
*   **Propagation**: Interactive labels or icons inside a container should use `event.Skip()` or be created via `create_text()` (which handles pass-through) so clicks reach the parent container.

### 2. Focus & Keyboard
*   **Focusable Controls**: Inputs (`NumericInput`, `CustomTextInput`) must set `self.SetCanFocus(True)` and `AcceptsFocus()` to return `self.IsEnabled()`.
*   **Passive Controls**: Buttons and Sliders should return `False` for `AcceptsFocus()` to maintain the "HUD" feel of the side panel, where focus shouldn't get "stuck" on a button.
*   **Tab Traversal**: Containers with multiple inputs should include `wx.TAB_TRAVERSAL` in their window style. Each component should only have 1.

### 3. Painting Conventions
*   **Flicker-Free**: Always use `wx.AutoBufferedPaintDC(self)` inside `on_paint`.
*   **State-Aware Colors**: Always check `self.IsEnabled()` and apply `_theme.disabled(color)` to both backgrounds and text/icons if disabled.
*   **GraphicsContext**: Use `wx.GraphicsContext.Create(dc)` for high-quality anti-aliased drawing of rounded rectangles and text.

### 4. Size Hints
*   **Fixed Heights**: Most SpinRender controls have a fixed height (typically 18, 28, 32, or 36) defined in the theme. Use `self.SetMinSize` or `self.SetSize` in the constructor to enforce the design grid.
*   **Width Flexibility**: Use `(-1, height)` for size hints to allow components to expand horizontally in sizers while maintaining vertical consistency.

## Migration Pitfalls

*   **Hardcoded Fallbacks**: Avoid `wx.Colour(30, 30, 30)`. If a color isn't in the theme, prompt user for direction.
*   **Ghost States**: Remove ghost states.
*   **Missing Refresh**: Any state change (`hovered`, `pressed`, `selection`) **MUST** be followed by `self.Refresh(); self.Update()` to trigger a repaint.
*   **Icon Scaling**: Use `TextStyles.icon` for standard 16px icons and `TextStyles.icon_lg` for 20px preset/header icons. Don't manually set icon font sizes in the component code.
*   **No Hardcoded Styling**: Never hardcode colors, margins, padding, borders, or font sizes directly in component code. All styling values must come from the YAML theme files. If a visual property isn't available in the theme, stop and prompt the user or team lead: "This component needs a new theme token at `components.{component_type}.{id}.{property}`. Should we add it?"

