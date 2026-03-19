# SpinRender Master Locale Schema (V2)
# File: docs/theme_v2/MASTER_LOCALE_SCHEMA.md
#
# This file serves as the definitive technical contract for all SpinRender V2 localization files.
# Implementation must strictly separate Content (Text/Icon Refs) from Styling (YAML).

# ─────────────────────────────────────────────────────────────────
# 1. ROOT STRUCTURE
# ─────────────────────────────────────────────────────────────────
locale:
  .[language_code]: # e.g., en_US, ja_JP
    # Content sections defined below...

# ─────────────────────────────────────────────────────────────────
# 2. COMPONENT CONTENT
# ─────────────────────────────────────────────────────────────────

# APP HEADER
component.main.header:
  title: "string"
  subtitle: "string"
  logo_id: "path/to/asset.svg"

# BUTTONS: Labels and Icon references
# Note: icon_ref must point to a key in the Theme's 'glyphs' section.
component.button:
  .[button_id]:
    label: "string"
    icon_ref: "glyphs.[name]"

# PRESET CARDS
component.preset_card:
  .[card_id]:
    label: "string"
    icon_ref: "glyphs.[name]"

# STATUS MESSAGES: Supports {placeholder} formatting
component.status:
  .[status_id]: "string with {placeholders}"

# ─────────────────────────────────────────────────────────────────
# 3. GLOBAL UI STRINGS
# ─────────────────────────────────────────────────────────────────

# DIALOGS: Modal titles
dialog:
  .[dialog_id]:
    title: "string"

# SECTIONS: Side-panel header text
sections:
  .[section_id]: "string"

# ─────────────────────────────────────────────────────────────────
# 4. PARAMETERS & OUTPUT
# ─────────────────────────────────────────────────────────────────

# PARAMETERS: Labels, Units, and Option Lists
parameters:
  # Static Headings/Descriptions
  .[heading_id]: "string"
  
  # Specific Parameter Definitions
  .[param_id]:
    label: "string"
    icon_ref: "glyphs.[name]"
    unit: "string (e.g., °, sec)"
    desc: "string (optional hint text)"
    options:
      .[option_id]:
        label: "string"
        icon_ref: "glyphs.[name]"

# OUTPUT SETTINGS
output:
  auto_desc: "string"
  .[setting_id]:
    label: "string"
    options: ["list", "of", "strings"]

# ─────────────────────────────────────────────────────────────────
# 5. IMPLEMENTATION NOTES
# ─────────────────────────────────────────────────────────────────
# 1. ICON REFERENCES: Never use Unicode hex codes here. 
#    Always use 'icon_ref' pointing to 'glyphs.[name]' in the theme.
# 2. PLACEHOLDERS: Logic-driven strings (like status) use curly braces 
#    for variables injected by the Python controllers.
# 3. NO STYLING: Do not include colors, fonts, or sizes in this file.
