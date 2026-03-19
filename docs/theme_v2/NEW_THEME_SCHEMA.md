# YAML:
# Theme/Color definitions go here
# Note: This file defines STYLING ONLY. All string literals (text, icon IDs) must be defined in the Localization file.

# ─────────────────────────────────────────────────────────────────
# SCALES (Global Design Tokens)
# ─────────────────────────────────────────────────────────────────
palette
    # Neutral Grays (Darkest -> Lightest)
    .gray-black:  "#0D0D0D"   # Deepest gray (input wells)
    .gray-dark:   "#121212"   # Base gray (page background)
    .gray-border: "#1F1F1F"   # Border gray (default dividers)
    .gray-medium: "#323232"   # Medium gray (scrollbar tracks)
    .gray-light:  "#646464"   # Light gray (subtle text/highlights)
    .gray-text:   "#777777"   # Text gray (secondary metadata)
    .gray-white:  "#E0E0E0"   # Near-white (primary text)
    
    # Semantic Accents
    .cyan:        "#00BCD4"   # Primary Brand
    .yellow:      "#FFD600"   # Warning/Highlight
    .green:       "#4CAF50"   # Success/Active
    .orange:      "#FF6B35"   # Warning/Badge
    .red:         "#FF3B30"   # Error/Danger
    .purple:      "#AA6BFF"   # Tertiary Brand
    .pink:        "#f240ff"   # Quaternary Brand
    
    .transparent: "rgba(0,0,0,0)"
    .black:       "#000000"
    .white:       "#FFFFFF"   # Pure white

theme
    .primary # ref: "palette.cyan"
    .secondary # ref: "palette.yellow"
    .tertiary # ref: "palette.purple"
    .quaternary # ref: "palette.pink"
    .ok # ref: "palette.green"
    .warning # ref: "palette.orange"
    .error # ref: "palette.red"

glyphs
    # Icon Unicode Aliases (e.g., check: "\U000F05E0")
    # This allows components to reference icons by name.
    .[name] # string (unicode)

spacing
    .0:   0
    .xs:  4    # Tight gaps
    .sm:  6    # Icon+label gap (toggle button)
    .md:  10   # Icon+label gap (standard button)
    .lg:  16   # Main layout section padding
    .xl:  24   # Section-to-section gap

radius
    .none: 0
    .sm:   4   # Toggles, sliders
    .md:   6   # Buttons, dropdowns
    .lg:   8   # Cards, panels
    .full: 9999

# ─────────────────────────────────────────────────────────────────
# PRIMITIVES (Core Types)
# ─────────────────────────────────────────────────────────────────
frame
    .width # int | "auto" | "expand" (default: "auto")
    .height # int | "auto" | "expand" (default: "auto")
    .bg # color obj (default: transparent)
    .border # border obj
    .shadow # shadow obj
    .padding 
        .horizontal # int | ref: "spacing.[name]"
        .vertical # int | ref: "spacing.[name]"
    .self_alignment # enum: ["left", "center", "right", "top", "bottom"]
    .content_alignment # enum: ["left", "center", "right", "top", "bottom", "space-between"]
    .cursor # enum: ["arrow", "hand", "text", "wait", "watch"] (default: "arrow")

font
    .size # int (point size)
    .typeface # string (e.g., "JetBrains Mono")
    .style # enum: ["normal", "italic", "oblique"] (default: "normal")
    .weight # int (100-900) (default: 400)

color
    .default # hex | rgba | color name | ref: "palette.[name]"
    .hover # hex | rgba | color name | ref: "palette.[name]"
    .active # hex | rgba | color name | ref: "palette.[name]" (mousedown, pressed, focus)
    .disabled # hex | rgba | color name | ref: "palette.[name]"

border
    .size # int (thickness in px)
    .radius # int | ref: "radius.[name]"
    .color # color obj

shadow
    .color # color obj
    .offset # [int, int] (x, y)
    .blur # int
    .spread # int

icon
    .id # string_name or string_hex | ref: "glyphs.[name]"
    .size # int (default: 14)
    .color # color obj

label 
    .font # font obj
    .color # color obj

# ─────────────────────────────────────────────────────────────────
# TYPOGRAPHY (Global Text Styles)
# ─────────────────────────────────────────────────────────────────
text
    .title
        .color # color obj
        .font # font obj
    .subtitle
        .color # color obj
        .font # font obj
    .header
        .color # color obj
        .font # font obj
    .subheader
        .color # color obj
        .font # font obj
    .body
        .color # color obj
        .font # font obj
    .links
        .color # color obj
        .font # font obj

# ─────────────────────────────────────────────────────────────────
# VIEWPORT (3D Renderer Styles)
# ─────────────────────────────────────────────────────────────────
viewport
    .bg # color obj (clear color)
    .grid # color obj
    .wireframe # color obj
    .axes
        .x # color obj
        .y # color obj
        .z # color obj

# ─────────────────────────────────────────────────────────────────
# COMPONENT DEFINITIONS
# ─────────────────────────────────────────────────────────────────
component.main
    .frame # frame obj
    .header
        .bg # color obj
        .logo # color obj
        .title # label obj
        .subtitle # label obj
    .leftpanel
        .bg # color obj
        .headers # label obj
        .subheaders # label obj
        .body # label obj
        .scrollbar # component ref (e.g., ref: "component.scrollbar")
    .rightpanel
        .bg # color obj
        .nav # label obj
        .title # label obj
        .info # label obj
    .status # component ref (e.g., ref: "component.status")

component.badge
    .frame # frame obj
    .icon # icon obj
    .label # label obj
    .gap # int | ref: "spacing.[name]"
    .vertical # boolean

component.preset_card.default
    .frame # frame obj
    .gap # int | ref: "spacing.[name]"
    .default
        .bg # color obj
        .border # border obj
        .icon # icon obj
        .label # label obj
    .selected
        .bg # color obj
        .border # border obj
        .icon # icon obj
        .label # label obj
    
component.preset_card.card1
component.preset_card.card2 
component.preset_card.card3 
component.preset_card.card4 

component.input.default
    .frame # frame obj
    .color # color obj (text color; active state is the focus color)
    .border # border obj
    .selection # color obj (highlight background)
    .prefix # component ref or null
    .suffix # component ref or null
    .multiline # boolean
    .error
        .color # color obj
        .border # border obj

component.input.path
component.input.parameters
        
component.slider.default
    .frame # frame obj
    .icon # icon obj
    .label # label obj
    .track
        .frame # frame obj
        .color # color obj
        .border # border obj
    .nub
        .width # int
        .height # int
        .border # border obj
        .color # color obj
    .input # component ref

component.slider.primary
component.slider.secondary
component.slider.tertiary
component.slider.quaternary

component.toggle.default
    .frame # frame obj
    .gap # int | ref: "spacing.[name]"
    .default
        .frame # frame obj
        .icon # icon obj
        .label # label obj    
    .selected
        .frame # frame obj
        .icon # icon obj
        .label # label obj

component.toggle.direction
component.toggle.lighting
component.toggle.logging

component.dropdown.default
    .frame # frame obj (main collapsed state)
    .bg # color obj
    .border # border obj
    .icon # icon obj (chevron)
    .open
        .border # border obj
        .icon # icon obj (e.g., rotated chevron)
    .menu
        .frame # frame obj (popup container state)
        .default
            .label # label obj
        .selected
            .bg # color obj
            .label # label obj

component.dropdown.format
component.dropdown.resolution

component.colorpicker.default
    .bg # color obj
    .border # border obj
    .default
        .border # border obj
    .selected
        .border # border obj
    .input # component ref

component.button.default
    .frame # frame obj
    .icon # icon obj
    .label # label obj
    .gap # int | ref: "spacing.[name]"
    .vertical # boolean

component.button.cancel
component.button.ok
component.button.close
component.button.options
component.button.browse
component.button.exit
component.button.render 

component.scrollbar
    .track # frame obj
    .thumb # frame obj

component.status
    .default
        .bg # color obj
        .label # label obj
    .progress
        .bg # color obj
        .label # label obj
    .complete
        .bg # color obj
        .label # label obj
    .error
        .bg # color obj
        .label # label obj

# ─────────────────────────────────────────────────────────────────
# LOCALIZATION & CONTENT DEFINITIONS (JSON or separate YAML dict)
# String definitions and icon references map directly to components here.
# ─────────────────────────────────────────────────────────────────
locale.en_US
    .component.button.render.label: "RENDER"
    .component.button.render.icon_ref: "glyphs.render-action"
    
    .component.button.cancel.label: "CLOSE"
    .component.button.cancel.icon_ref: "glyphs.exit-action"
    
    .component.rightpanel.nav.options: ["WIREFRAME", "SHADED", "BOTH"]
