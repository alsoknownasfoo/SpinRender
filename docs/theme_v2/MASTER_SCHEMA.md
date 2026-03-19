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
  .[name]: "hex | rgba string"
  
  # Semantic Roles (Theme) - Logic-level aliases
  primary: "@colors.[palette_key]"
  secondary: "@colors.[palette_key]"
  tertiary: "@colors.[palette_key]"
  quaternary: "@colors.[palette_key]"
  ok: "@colors.[palette_key]"
  warning: "@colors.[palette_key]"
  error: "@colors.[palette_key]"

# RADIUS: Global rounding scale (px)
radius:
  .[name]: int (e.g., none: 0, sm: 4, md: 6, lg: 8, full: 9999)

# BORDERS: Line thickness scale and semantic roles
borders:
  width:
    .[name]: int (e.g., none: 0, thin: 1, medium: 2)
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
    header: frame roles
    leftpanel: frame roles (headers, subheaders, body, scrollbar)
    rightpanel: frame roles (nav, title, info)
    status: ref: component.status

  component.badge:
    frame: frame
    icon: "@text.icon"
    label:
      font: "@typography.scale.[name]"
      color: "@colors.[path]"
    gap: "@typography.spacing.[name]"
    vertical: boolean

  component.preset_card:
    default:
      frame: frame
      gap: int
      default: (bg, border, icon, label)
      selected: (bg, border, icon, label)
    .[card_id]: ref: component.preset_card.default

  component.input:
    default:
      frame: frame
      color: (default, active, disabled)
      border: border
      selection: color
      prefix: text_role
      suffix: text_role
      multiline: boolean
      error: (color, border)
    .[input_id]: ref: component.input.default

  component.slider:
    default:
      frame: frame
      icon: text_role
      label: text_role
      track: (frame, color, border)
      nub: (width, height, border, color)
      input: ref: component.input.parameters
    .[slider_id]: ref: component.slider.default

  component.toggle:
    default:
      frame: frame
      gap: "@typography.spacing.[name]"
      default: (frame, icon, label)
      selected: (frame, icon, label)
    .[toggle_id]: ref: component.toggle.default

  component.dropdown:
    default:
      frame: frame
      bg: color
      border: border
      icon: text_role
      open: (border, icon)
      menu: (frame, default_label, selected_label)
    .[dropdown_id]: ref: component.dropdown.default

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
      vertical: boolean
    .[button_id]: ref: component.button.default

  component.scrollbar:
    track: frame
    thumb: frame

  component.status:
    default: (bg, label)
    progress: (bg, label)
    complete: (bg, label)
    error: (bg, label)
