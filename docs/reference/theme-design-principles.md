# SpinRender Theme Schema (V2 Mastering)

SpinRender uses a 100% data-driven theme system. All visual properties (colors, fonts, spacing, icons) are defined in YAML and consumed via the `Theme` singleton.

---

## Architectural Principles

1.  **YAML is Truth**: Code must never hardcode colors or Unicode glyphs. If it's visual, it's in the YAML.
2.  **Strict Hierarchy**: Tokens follow a rigid path: `[category].[name].[property]`.
3.  **Ref System**: Tokens can reference other tokens using `ref: "path.to.token"` (V1) or `"@path.to.token"` (V2).
4.  **Decoupled Content**: The **Locale** file determines *which* glyph to use (e.g., `icon_ref: "glyphs.render"`), while the **Theme** file determines *what* that glyph looks like (e.g., `render: "\U000F0A1C"`).

---

## Core Categories

### 1. Palette
Raw hex and RGBA values. Never used directly by components.
```yaml
palette:
  neutral-1: "#0A0A0A"
  cyan:      "#00BCD4"
  transparent: "rgba(0,0,0,0)"
```

### 2. Colors
Semantic aliases over the palette.
```yaml
colors:
  primary:   "@palette.cyan"
  bg:
    page:    "@palette.neutral-3"
  text:
    body:    "@palette.neutral-14"
```

### 3. Glyphs
Unicode character mappings for icons (Material Design Icons).
```yaml
glyphs:
  render-action: "\U000F0A1C"
  folder:        "\U000F024B"
  chevron-down:  "\U000F0140"
```

### 4. Text
Composite font + color specifications. An optional `formatting` key drives
programmatic text transformation at render time — locale strings are stored
in sentence case and transformed by `TextStyle.format_text()`.
```yaml
text:
  body:
    font:
      typeface: "@typography.families.mono"
      size:     "@typography.scale.base"
      weight:   400
    color: "@colors.text.body"
  subheader:
    font: ...
    color: ...
    formatting: "uppercase"   # "uppercase" | "lowercase" | "capitalize"
```
All `wx.StaticText` must be created via `helpers.create_text()` so formatting
and hot-reload registration happen automatically.
For `create_text(style_name=...)`, prefer a `TextStyles` alias key instead of
passing raw `layout.*` or `components.*` theme paths directly.

### 5. Components
Terminal design decisions for specific UI elements.
```yaml
components:
  button:
    ok:
      frame:
        bg: "@colors.primary"
        radius: "@radius.md"
      label:
        color: "@colors.gray-black"
```

---

## Technical Contract (The "Mastering Schema")

The following paths are considered terminal and must be present in every theme:

| Path | Type | Description |
|------|------|-------------|
| `colors.primary` | Color | Primary brand accent color |
| `colors.bg.page` | Color | Outermost window background |
| `text.body.color` | Color | Primary text color |
| `glyphs.render-action` | String | Unicode for play/render icon |
| `borders.default.color` | Color | Standard 1px border color |
| `spacing.lg` | Integer | Standard container padding |

---

## Theme Loader API

Access tokens via the `Theme` singleton:

```python
from SpinRender.core.theme import Theme
t = Theme.current()

# Direct color lookup (returns wx.Colour)
bg = t.color("colors.bg.page")

# State-aware color lookup (returns [normal, hover, pressed])
states = t.color_states("components.button.ok.frame.bg")

# Glyph lookup (returns Unicode string)
icon = t.glyph("render-action")

# Spacing lookup (returns int)
padding = t.size("spacing.lg")
```
