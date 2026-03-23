# SpinRender Master Theme Schema (V2)
# File: docs/theme_v2/MASTER_SCHEMA.md
#
# This file serves as the definitive technical contract for all SpinRender V2 themes.
# Implementation must strictly separate Styling (YAML) from Content (Locale).

# ─────────────────────────────────────────────────────────────────
# 1. SCALES (Global Design Tokens)
# ─────────────────────────────────────────────────────────────────

# COLORS: Design Tokens & Semantic Roles
colors:
  # Base Palette (Primes) - Raw hex/rgba values
  # e.g., gray-black: "#0D0D0D"
  .[name]: "hex | rgba string"
  
  # Semantic Roles (Theme) - Logic-level aliases
  # e.g., primary: "@colors.cyan"
  primary: "@colors.[palette_key]"
  secondary: "@colors.[palette_key]"
  tertiary: "@colors.[palette_key]"
  quaternary: "@colors.[palette_key]"
  ok: "@colors.[palette_key]"
  warning: "@colors.[palette_key]"
  error: "@colors.[palette_key]"

# RADIUS: Global rounding scale (px)
# e.g., md: 6
radius:
  .[name]: int

# BORDERS: Line thickness scale and semantic roles
borders:
  width:
    .[name]: int
  # Semantic Roles - Standardized line styles
  default:
    size: "@borders.width.[name]"
    color: "@colors.[path]"
  subtle:
    size: "@borders.width.[name]"
    color: "@colors.[path]"
  focus:
    size: "@borders.width.[name]"
    color: "@colors.[path]"
  strong:
    size: "@borders.width.[name]"
    color: "@colors.[path]"

# DIVIDERS: Separator lines between sections
dividers:
  width:
    .[name]: int
  # Semantic Roles - Separator lines (lighter than borders for visual hierarchy)
  default:
    size: "@dividers.width.[name]"
    color: "@colors.[path]"

# TYPOGRAPHY: Scale, spacing, and families
typography:
  families:
    mono: "string (Face Name)"
    display: "string (Face Name)"
    icon: "string (Face Name)"
  scale:
    sm: int (px)
    base: int (px)
    md: int (px)
    lg: int (px)
  spacing:
    none: 0
    sm: int (px)
    base: int (px)
    md: int (px)
    lg: int (px)

# GLYPHS: Icon Unicode Aliases
# Links semantic names to font-specific hex codes
glyphs:
  .[name]: "unicode string (e.g., \U000F0A1C)"

# ─────────────────────────────────────────────────────────────────
# 2. PRIMITIVES (Core Object Types)
# ─────────────────────────────────────────────────────────────────

# FONT: Basic text properties
font:
  typeface: "@typography.families.[name]"
  size: "@typography.scale.[name]"
  weight: int (100-900)

# TEXT ROLE: Combined color and font object
# Directly referenced by components
text_role:
  color: "color_string | @colors.[path]"
  font: font object

# FRAME: The primary container primitive
frame:
  width: int | null
  height: int | null
  bg: "color_string | @colors.[path]"
  radius: "@radius.[name]"
  border: "@borders.[role]"
  shadow: object | null
  padding:
    horizontal: "@typography.spacing.[name]"
    vertical: "@typography.spacing.[name]"
  self_alignment: "enum: [left, center, right, top, bottom]"
  content_alignment: "enum: [left, center, right, top, bottom, space-between]"
  cursor: "string: [hand, arrow, text, wait, watch]"

# ─────────────────────────────────────────────────────────────────
# 3. GLOBAL ROLES
# ─────────────────────────────────────────────────────────────────

# TEXT: Master list of typographic roles used across the UI
text:
  title: text_role
  subtitle: text_role
  header: text_role
  subheader: text_role
  body: text_role
  links: text_role
  metadata: text_role
  metadata_active: text_role
  label: text_role
  button: text_role
  nav: text_role
  nav_active: text_role
  icon: text_role
  icon_lg: text_role

# VIEWPORT: 3D Renderer environment styles
viewport:
  bg: "@colors.[path]"
  grid: "@colors.[path]"
  wireframe: "@colors.[path]"
  axes:
    x: "@colors.[path]"
    y: "@colors.[path]"
    z: "@colors.[path]"

# ─────────────────────────────────────────────────────────────────
# 4. COMPONENT IDENTIFIERS
# ─────────────────────────────────────────────────────────────────
components:
  component.main:
    frame: frame
    header: (bg, logo, title, subtitle)
    leftpanel: (bg, headers, subheaders, body, border, scrollbar)
    divider: (bg, size)
    rightpanel: (bg, nav, nav_active, title, info, info_active)
    status: ref: component.status

  component.badge:
    frame: frame
    icon: "@text.icon"
    label: (font, color)
    gap: "@typography.spacing.[name]"

  component.preset_card:
    default:
      frame: frame
      gap: int
      default: (bg, border, icon, label)
      selected: (bg, border, icon, label)
    card1: ref: component.preset_card.default
    card2: ref: component.preset_card.default
    card3: ref: component.preset_card.default
    card4: ref: component.preset_card.default

  component.input:
    default:
      frame: frame
      color: (default, active, disabled)
      border: border
      selection: color
      font: "@text.body.font"
      error: (color, border)
    path: ref: component.input.default
    parameters: ref: component.input.default

  component.slider:
    default:
      frame: frame
      icon: text_role
      label: text_role
      track: (frame, color, border)
      nub: (width, height, border, color)
      input: ref: component.input.parameters
    primary: ref: component.slider.default
    secondary: ref: component.slider.default
    tertiary: ref: component.slider.default
    quaternary: ref: component.slider.default

  component.toggle:
    default:
      frame: frame
      gap: "@typography.spacing.[name]"
      default: (frame, icon, label)
      selected: (frame, icon, label)
    direction: ref: component.toggle.default
    lighting: ref: component.toggle.default
    logging: ref: component.toggle.default

  component.dropdown:
    default:
      frame: frame
      bg: color
      border: border
      icon: text_role
      open: (border, icon)
      menu: (frame, default_label, selected_label)
    format: ref: component.dropdown.default
    resolution: ref: component.dropdown.default

  component.colorpicker:
    default:
      bg: color
      border: border
      radius: radius
      default: border
      selected: border
      input: ref: component.input.parameters

  component.button:
    default:
      frame: frame
      icon: text_role
      label: text_role
      gap: "@typography.spacing.[name]"
    cancel: ref: component.button.default
    ok: ref: component.button.default
    close: ref: component.button.default
    options: ref: component.button.default
    browse: ref: component.button.default
    exit: ref: component.button.default
    render: ref: component.button.ok

  component.scrollbar:
    track: frame
    thumb: frame

  component.status:
    default: (bg, label)
    progress: (bg, label)
    complete: (bg, label)
    error: (bg, label)
