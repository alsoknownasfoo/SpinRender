# SpinRender Theme Schema

YAML-based theme system to replace 60+ hardcoded `wx.Colour(...)` calls across
`custom_controls.py` and `main_panel.py`.

---

## Color Inventory (Current Hardcoded Values)

All unique colors discovered, normalized to hex:

| Hex       | RGB              | Current Name(s)                              | Uses             |
|-----------|------------------|----------------------------------------------|------------------|
| `#0A0A0A` | (10, 10, 10)     | —                                            | Output preview bg |
| `#0D0D0D` | (13, 13, 13)     | `BG_INPUT`, `BG_COLOR`                      | Inputs, deep bg  |
| `#121212` | (18, 18, 18)     | `BG_PAGE`                                    | Page/window bg   |
| `#171717` | (23, 23, 23)     | —                                            | Color picker bg  |
| `#1A1A1A` | (26, 26, 26)     | `BG_PANEL`                                   | Panel containers |
| `#1E1E1E` | (30, 30, 30)     | —                                            | Inner surfaces   |
| `#1F1F1F` | (31, 31, 31)     | `BORDER_DEFAULT`, `border_color`             | Default borders  |
| `#222222` | (34, 34, 34)     | `BG_SURFACE`, `bg_color`                    | Cards, surfaces  |
| `#323232` | (50, 50, 50)     | —                                            | Hover state bg   |
| `#333333` | (51, 51, 51)     | `TRACK_COLOR`, `BORDER_COLOR`               | Slider track, borders |
| `#555555` | (85, 85, 85)     | `TEXT_MUTED`, `PLACEHOLDER_COLOR`           | Placeholders, dim text |
| `#646464` | (100, 100, 100)  | —                                            | Scrollbar, minor UI |
| `#777777` | (119, 119, 119)  | `TEXT_SECONDARY`                             | Secondary labels |
| `#E0E0E0` | (224, 224, 224)  | `TEXT_PRIMARY`                               | Primary body text |
| `#FFFFFF` | (255, 255, 255)  | —                                            | Danger button text |
| `#00BCD4` | (0, 188, 212)    | `ACCENT_CYAN`, `BORDER_FOCUS`, `fill_color` | Primary accent   |
| `#FFD600` | (255, 214, 0)    | `ACCENT_YELLOW`                              | Light toggle accent |
| `#4CAF50` | (76, 175, 80)    | `ACCENT_GREEN`, `DEFAULT_ACTIVE_BG`         | Success, active  |
| `#FF6B35` | (255, 107, 53)   | `ACCENT_ORANGE`                              | Warnings, badges |
| `#8C0000` | (140, 0, 0)      | —                                            | Danger pressed   |
| `#B40000` | (180, 0, 0)      | —                                            | Danger button bg |
| `#DC1414` | (220, 20, 20)    | —                                            | Danger hover     |
| `#FF6B6B` | (255, 107, 107)  | —                                            | Preset card: red |
| `#FFB46B` | (255, 180, 107)  | —                                            | Preset card: amber |
| `#4D96FF` | (77, 150, 255)   | —                                            | Preset card: blue |
| `#AA6BFF` | (170, 107, 255)  | —                                            | Preset card: purple |
| `rgba(255,255,255,0.08)` | a=20 | — | Faint hover overlay |
| `rgba(255,255,255,0.16)` | a=40 | — | Hover overlay |
| `rgba(255,255,255,0.27)` | a=68 | — | Pressed/focus overlay |
| `rgba(0,0,0,0)`          | —    | — | Transparent (ghost button bg) |

---

## YAML Theme Schema

```yaml
# SpinRender Theme — Dark (default)
# File: SpinRender/resources/themes/dark.yaml
#
# This file is the single source of truth for all visual tokens.
# Load with: from core.theme import Theme; t = Theme.load("dark")

meta:
  name: "Dark"
  version: "1.0.0"
  description: "Default dark theme matching the SpinRender design system"

# ─────────────────────────────────────────────
# 1. RAW PALETTE
#    Low-level color definitions. Do NOT use these directly in
#    components — use semantic tokens below instead.
# ─────────────────────────────────────────────
palette:
  # Neutrals (darkest → lightest)
  neutral-1:  "#0A0A0A"   # near-black
  neutral-2:  "#0D0D0D"   # input wells
  neutral-3:  "#121212"   # page background
  neutral-4:  "#171717"   # very dark surface
  neutral-5:  "#1A1A1A"   # panel background
  neutral-6:  "#1E1E1E"   # inner surface
  neutral-7:  "#1F1F1F"   # border default
  neutral-8:  "#222222"   # card surface
  neutral-9:  "#323232"   # hover tint
  neutral-10: "#333333"   # track / strong border
  neutral-11: "#555555"   # muted / placeholder
  neutral-12: "#646464"   # subtle UI
  neutral-13: "#777777"   # secondary text
  neutral-14: "#E0E0E0"   # primary text
  neutral-15: "#FFFFFF"   # white

  # Brand accents
  cyan:       "#00BCD4"
  yellow:     "#FFD600"
  green:      "#4CAF50"
  orange:     "#FF6B35"

  # Semantic state
  danger:     "#B40000"
  danger-hover: "#DC1414"
  danger-pressed: "#8C0000"

  # Preset card palette
  preset-red:    "#FF6B6B"
  preset-amber:  "#FFB46B"
  preset-blue:   "#4D96FF"
  preset-purple: "#AA6BFF"
  preset-pink:   "#FF6BFF"

  # Overlays (RGBA as hex with alpha)
  overlay-faint:  "rgba(255,255,255,0.08)"
  overlay-light:  "rgba(255,255,255,0.16)"
  overlay-medium: "rgba(255,255,255,0.27)"
  transparent:    "rgba(0,0,0,0)"
  black-solid:    "#000000"


# ─────────────────────────────────────────────
# 2. SEMANTIC COLOR TOKENS
#    Purpose-named aliases over the raw palette.
#    These are what components should reference.
# ─────────────────────────────────────────────
colors:

  # — Backgrounds —
  bg:
    page:       {ref: "palette.neutral-3"}   # Window/outermost container
    panel:      {ref: "palette.neutral-5"}   # Side panels, sections
    surface:    {ref: "palette.neutral-8"}   # Cards, elevated surfaces
    input:      {ref: "palette.neutral-2"}   # Text fields, numeric inputs
    inner:      {ref: "palette.neutral-6"}   # Nested surfaces
    overlay:    {ref: "palette.neutral-4"}   # Color picker, popups
    track:      {ref: "palette.neutral-10"}  # Slider track fill area
    hover:      {ref: "palette.neutral-9"}   # Generic hover state
    output:     {ref: "palette.neutral-1"}   # GL/video preview backdrop

  # — Text —
  text:
    primary:    {ref: "palette.neutral-14"}  # Body copy, labels
    secondary:  {ref: "palette.neutral-13"}  # Dimmed labels, captions
    muted:      {ref: "palette.neutral-11"}  # Placeholder, hint text
    on-accent:  {ref: "palette.neutral-2"}   # Text over cyan accent bg
    on-danger:  {ref: "palette.neutral-15"}  # Text over danger bg

  # — Borders —
  border:
    default:    {ref: "palette.neutral-7"}   # Panels, cards
    subtle:     {ref: "palette.neutral-10"}  # Toggles, dropdowns
    focus:      {ref: "palette.cyan"}        # Focused inputs
    strong:     {ref: "palette.neutral-10"}  # Strong dividers

  # — Accent (primary brand color) —
  accent:
    primary:    {ref: "palette.cyan"}
    secondary:  {ref: "palette.yellow"}
    success:    {ref: "palette.green"}
    warning:    {ref: "palette.orange"}

  # — Interactive states —
  state:
    danger:         {ref: "palette.danger"}
    danger-hover:   {ref: "palette.danger-hover"}
    danger-pressed: {ref: "palette.danger-pressed"}
    active:         {ref: "palette.green"}      # toggle/option active bg
    hover-overlay:  {ref: "palette.overlay-light"}
    pressed-overlay:{ref: "palette.overlay-medium"}
    ghost-overlay:  {ref: "palette.overlay-faint"}

  # — Preset card colors —
  preset:
    - {ref: "palette.preset-red"}
    - {ref: "palette.preset-amber"}
    - {ref: "palette.preset-blue"}
    - {ref: "palette.preset-purple"}


# ─────────────────────────────────────────────
# 3. TYPOGRAPHY
# ─────────────────────────────────────────────
typography:

  # Font family stacks
  families:
    mono:    "JetBrains Mono"   # Primary UI font (monospaced)
    display: "Oswald"           # Headings, panel titles
    icon:    "Material Design Icons"  # MDI icon glyph font

  # Scale (px-equivalent sizes passed to wx.Font)
  scale:
    xs:    8    # Tick marks, graph labels
    sm:    9    # Icon labels on preset cards
    base:  11   # Default body / button text        ← DEFAULT
    md:    13   # Numeric display values, section headings
    lg:    14   # MDI icon default size
    xl:    18   # Panel title (Oswald)
    icon:  14   # MDI icons (same as lg, aliased for clarity)
    icon-lg: 20 # Large icon buttons

  # Weight aliases (map to wx.FONTWEIGHT_*)
  weights:
    normal:   400   # wx.FONTWEIGHT_NORMAL
    semibold: 600   # wx.FONTWEIGHT_SEMIBOLD
    bold:     700   # wx.FONTWEIGHT_BOLD

  # Composite presets — (family, size, weight)
  presets:
    body:
      family: {ref: "typography.families.mono"}
      size:   {ref: "typography.scale.base"}
      weight: {ref: "typography.weights.normal"}

    body-strong:
      family: {ref: "typography.families.mono"}
      size:   {ref: "typography.scale.base"}
      weight: {ref: "typography.weights.semibold"}

    label-sm:
      family: {ref: "typography.families.mono"}
      size:   {ref: "typography.scale.sm"}
      weight: {ref: "typography.weights.semibold"}

    label-xs:
      family: {ref: "typography.families.mono"}
      size:   {ref: "typography.scale.xs"}
      weight: {ref: "typography.weights.bold"}

    numeric-value:
      family: {ref: "typography.families.mono"}
      size:   {ref: "typography.scale.md"}
      weight: {ref: "typography.weights.semibold"}

    numeric-unit:
      family: {ref: "typography.families.mono"}
      size:   {ref: "typography.scale.base"}
      weight: {ref: "typography.weights.normal"}

    section-heading:
      family: {ref: "typography.families.display"}
      size:   {ref: "typography.scale.md"}
      weight: {ref: "typography.weights.semibold"}

    panel-title:
      family: {ref: "typography.families.display"}
      size:   {ref: "typography.scale.xl"}
      weight: {ref: "typography.weights.bold"}

    icon:
      family: {ref: "typography.families.icon"}
      size:   {ref: "typography.scale.icon"}
      weight: {ref: "typography.weights.normal"}

    icon-lg:
      family: {ref: "typography.families.icon"}
      size:   {ref: "typography.scale.icon-lg"}
      weight: {ref: "typography.weights.normal"}


# ─────────────────────────────────────────────
# 4. SPACING
#    All layout/padding/gap values in pixels.
# ─────────────────────────────────────────────
spacing:
  0:   0
  xs:  4    # Tight gaps
  sm:  6    # Icon+label gap (toggle button)
  md:  10   # Icon+label gap (standard button)
  lg:  16   # Main layout section padding
  xl:  24   # Section-to-section gap (future)


# ─────────────────────────────────────────────
# 5. BORDER & SHAPE
# ─────────────────────────────────────────────
borders:
  radius:
    none:   0
    sm:     2   # Subtle rounding (tracks, tags)
    md:     4   # Standard controls (inputs, toggles)
    lg:     8   # Cards, panels
    full:   999 # Pills, circular elements

  width:
    thin:   1
    medium: 2


# ─────────────────────────────────────────────
# 6. COMPONENT TOKENS
#    Per-component design decisions. Each entry
#    references semantic tokens above.
# ─────────────────────────────────────────────
components:

  # ── Slider ──────────────────────────────────
  slider:
    height:         18
    track:
      color:        {ref: "colors.bg.track"}
      height:       4
      radius:       {ref: "borders.radius.sm"}
    fill:
      color:        {ref: "colors.accent.primary"}
      radius:       {ref: "borders.radius.sm"}
    thumb:
      color:        {ref: "colors.accent.primary"}
      radius:       8    # half of 16px diameter = circular
      width:        16
      height:       16

  # ── Toggle Button (segmented control) ───────
  toggle:
    height:         32
    bg:             {ref: "colors.bg.input"}
    border:         {ref: "colors.border.subtle"}
    radius:         {ref: "borders.radius.md"}
    option:
      text:         {ref: "colors.text.secondary"}
      font:         {ref: "typography.presets.body-strong"}
      icon_gap:     {ref: "spacing.sm"}
    active:
      bg:           {ref: "colors.state.active"}   # default green; overridable
      text:         {ref: "colors.text.on-accent"}
      font:         {ref: "typography.presets.body-strong"}

  # ── Dropdown ────────────────────────────────
  dropdown:
    height:         32
    bg:             {ref: "colors.bg.input"}
    border:         {ref: "colors.border.default"}
    border-focus:   {ref: "colors.border.focus"}
    radius:         {ref: "borders.radius.md"}
    text:           {ref: "colors.text.primary"}
    text-muted:     {ref: "colors.text.muted"}
    font:           {ref: "typography.presets.body-strong"}
    popup:
      bg:           {ref: "colors.bg.inner"}
      hover:        {ref: "colors.bg.hover"}

  # ── Button ──────────────────────────────────
  button:
    height:         36
    radius:         {ref: "borders.radius.md"}
    font:           {ref: "typography.presets.body-strong"}
    icon_gap:       {ref: "spacing.md"}

    primary:
      bg:           {ref: "colors.accent.primary"}
      text:         {ref: "colors.text.on-accent"}
      hover:        {ref: "colors.state.hover-overlay"}
      pressed:      {ref: "colors.state.pressed-overlay"}

    secondary:
      bg:           {ref: "colors.bg.surface"}
      text:         {ref: "colors.text.primary"}
      border:       {ref: "colors.border.default"}
      hover:        {ref: "colors.state.hover-overlay"}

    ghost:
      bg:           {ref: "palette.transparent"}
      text:         {ref: "colors.text.primary"}
      hover:        {ref: "colors.state.ghost-overlay"}

    danger:
      bg:           {ref: "colors.state.danger"}
      text:         {ref: "colors.text.on-danger"}
      hover-bg:     {ref: "colors.state.danger-hover"}
      pressed-bg:   {ref: "colors.state.danger-pressed"}

  # ── Preset Card ─────────────────────────────
  preset_card:
    bg:             {ref: "colors.bg.surface"}
    border:         {ref: "colors.border.default"}
    radius:         {ref: "borders.radius.lg"}
    accent:         {ref: "colors.accent.primary"}
    text:           {ref: "colors.text.primary"}
    text-muted:     {ref: "colors.text.muted"}
    font-label:     {ref: "typography.presets.label-sm"}
    font-icon:      {ref: "typography.presets.icon"}
    # Overridden per-preset via `colors.preset[n]`
    palette:        {ref: "colors.preset"}

  # ── Section Label ────────────────────────────
  section_label:
    bg:             {ref: "colors.bg.input"}
    border:         {ref: "colors.border.subtle"}
    text:           {ref: "colors.text.primary"}
    text-secondary: {ref: "colors.text.secondary"}
    accent:         {ref: "colors.accent.primary"}
    font:           {ref: "typography.presets.section-heading"}

  # ── Numeric Display ─────────────────────────
  numeric_display:
    bg:             {ref: "colors.bg.input"}
    border:         {ref: "colors.border.default"}
    text-value:     {ref: "colors.text.primary"}
    text-unit:      {ref: "colors.text.secondary"}
    font-value:     {ref: "typography.presets.numeric-value"}
    font-unit:      {ref: "typography.presets.numeric-unit"}

  # ── Numeric Input ────────────────────────────
  numeric_input:
    bg:             {ref: "colors.bg.input"}
    border:         {ref: "colors.border.default"}
    border-focus:   {ref: "colors.border.focus"}
    text:           {ref: "colors.text.primary"}
    placeholder:    {ref: "colors.text.muted"}
    font:           {ref: "typography.presets.body"}

  # ── Color Picker ─────────────────────────────
  color_picker:
    bg:             {ref: "colors.bg.overlay"}
    border:         {ref: "colors.border.default"}
    swatch-border:  {ref: "colors.border.subtle"}
    overlay-fg:     {ref: "palette.overlay-medium"}

  # ── Main Panel / Header ──────────────────────
  panel:
    bg:             {ref: "colors.bg.page"}
    header-bg:      {ref: "colors.bg.panel"}
    header-border:  {ref: "colors.border.default"}
    title-font:     {ref: "typography.presets.panel-title"}
    close-icon:     {ref: "colors.text.muted"}
    padding:        {ref: "spacing.lg"}
    section-gap:    {ref: "spacing.lg"}

  # ── Status / Badge ───────────────────────────
  badge:
    bg:             {ref: "colors.accent.warning"}   # orange
    text:           {ref: "colors.text.on-accent"}
    font:           {ref: "typography.presets.label-xs"}
    radius:         {ref: "borders.radius.full"}
```

---

## Proposed File Layout

```
SpinRender/
├── resources/
│   └── themes/
│       ├── dark.yaml       ← default (schema above)
│       └── light.yaml      ← future
├── core/
│   └── theme.py            ← Theme loader / token resolver
└── ui/
    ├── custom_controls.py  ← consume Theme singleton
    └── main_panel.py       ← consume Theme singleton
```

## Theme Loader API (sketch)

```python
# core/theme.py
import yaml
from pathlib import Path

class Theme:
    _instance: "Theme | None" = None

    def __init__(self, data: dict):
        self._data = data

    @classmethod
    def load(cls, name: str = "dark") -> "Theme":
        path = Path(__file__).parent.parent / "resources" / "themes" / f"{name}.yaml"
        with open(path) as f:
            cls._instance = cls(yaml.safe_load(f))
        return cls._instance

    @classmethod
    def current(cls) -> "Theme":
        if cls._instance is None:
            cls.load()
        return cls._instance

    def colour(self, token: str) -> "wx.Colour":
        """Resolve a dot-path token to a wx.Colour. e.g. 'colors.accent.primary'"""
        import wx
        value = self._resolve(token)
        return self._parse_colour(value)

    def _resolve(self, path: str):
        node = self._data
        for key in path.split("."):
            if isinstance(node, dict):
                node = node[key]
            else:
                raise KeyError(f"Cannot traverse into {type(node)} at '{key}' in '{path}'")
        if isinstance(node, dict) and "ref" in node:
            return self._resolve(node["ref"])
        return node

    def _parse_colour(self, value: str) -> "wx.Colour":
        import wx, re
        if value.startswith("rgba("):
            parts = re.findall(r"[\d.]+", value)
            r, g, b, a_f = int(parts[0]), int(parts[1]), int(parts[2]), float(parts[3])
            return wx.Colour(r, g, b, int(a_f * 255))
        value = value.lstrip("#")
        r, g, b = int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)
        return wx.Colour(r, g, b)

    def size(self, token: str) -> int:
        return int(self._resolve(token))

    def font(self, preset: str) -> "wx.Font":
        import wx
        from ui.custom_controls import get_custom_font, get_mdi_font
        p = self._resolve(f"typography.presets.{preset}")
        family = self._resolve(p["family"]) if isinstance(p.get("family"), dict) else p["family"]
        size = self._resolve(p["size"]) if isinstance(p.get("size"), dict) else p["size"]
        weight_val = self._resolve(p["weight"]) if isinstance(p.get("weight"), dict) else p.get("weight", 400)
        wx_weight = {400: wx.FONTWEIGHT_NORMAL, 600: wx.FONTWEIGHT_SEMIBOLD, 700: wx.FONTWEIGHT_BOLD}.get(weight_val, wx.FONTWEIGHT_NORMAL)
        return get_custom_font(size=int(size), family_name=family, weight=wx_weight)
```

## Migration Example

**Before:**
```python
# custom_controls.py — NumericInput
BG_COLOR  = wx.Colour(13, 13, 13)
BORDER_FOCUS = wx.Colour(0, 188, 212)
TEXT_COLOR = wx.Colour(224, 224, 224)
PLACEHOLDER_COLOR = wx.Colour(85, 85, 85)
```

**After:**
```python
from core.theme import Theme

class NumericInput(wx.Panel):
    def _colours(self):
        t = Theme.current()
        return {
            "bg":          t.colour("components.numeric_input.bg"),
            "border":      t.colour("components.numeric_input.border"),
            "border_focus":t.colour("components.numeric_input.border-focus"),
            "text":        t.colour("components.numeric_input.text"),
            "placeholder": t.colour("components.numeric_input.placeholder"),
        }
```
