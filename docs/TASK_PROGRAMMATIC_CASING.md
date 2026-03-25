# Task: Move Uppercase from Locale to Theme Formatting

## Current Situation

The locale files currently contain hardcoded uppercase strings (e.g., "RENDER", "STOP", "RENDERING FRAME"). These should be stored in base-case in the locale, with uppercase applied via `formatting: "uppercase"` in the theme's text styles.

## Existing Infrastructure

- **TextStyle** (`ui/text_styles.py`) already supports `formatting: "uppercase|lowercase|capitalize"`
- **Theme** (`resources/themes/dark.yaml`) defines text styles with optional `formatting` field
- **create_text()** applies formatting automatically via `style.format_text(label)`
- Current uppercase styles in theme:
  - `text.title`: formatting: uppercase
  - `text.header`: formatting: uppercase
  - `text.subheader`: formatting: uppercase
  - `text.metadata`: formatting: uppercase
  - `text.status`: formatting: uppercase

## Required Changes

### 1. Add uppercase formatting to theme styles:

**File:** `SpinRender/resources/themes/dark.yaml` (and light.yaml if needed)

```yaml
text:
  button:
    color:
      default: "@colors.gray-light"
      hover: "@colors.primary"
    font:
      typeface: "@typography.families.mono"
      size: "@typography.scale.base"
      weight: "@typography.weights.semibold"
    formatting: "uppercase"  # ADD THIS

  label:
    color: "@colors.gray-text"
    font:
      typeface: "@typography.families.mono"
      size: "@typography.scale.sm"
      weight: "@typography.weights.semibold"
    formatting: "uppercase"  # ADD THIS
```

Also add to `components.preset_card.default.label` style if it uses a separate style override? Actually preset_card.label uses `ref: "@text.label"` so inherits label formatting.

For toggle labels, check if they use `label` style (they do from custom_controls.py), so adding uppercase to `text.label` covers them.

For dialog_description style (used for helper text, log_info, etc.), that should be `text.metadata` which already has uppercase? Wait, metadata has uppercase but helper text like "Frames are saved as..." should NOT be uppercase. So we need to be careful. Actually dialog_description maps to what? Looking at helpers.py create_text calls, `dialog_description` maps to `@text.metadata` in the theme? Wait that's in the dialog layout. But in custom code, `dialog_description` is likely a custom role. Need to check.

Looking at the mapping in TextStyles._ALIASES:
- "dialog_description": "layout.dialogs.default.body.description"

That points to theme token. In dark.yaml line 373:
```yaml
layout:
  dialogs:
    default:
      body:
        description: "@text.metadata"
```

So dialog_description uses `text.metadata` which has uppercase. But is that correct? The helper text "Frames are saved as name_00001.png..." is currently NOT uppercase in the locale (it's normal sentence case). So we DON'T want that to be uppercase. This suggests that either:
- dialog_description should map to a style without uppercase (like `text.body`)
- OR we need to create a new role like `text.helper` that doesn't have uppercase.

Let me check the actual usage: `dialog.filename.helper` is used with style "dialog_description" in dialogs.py? Looking at dialogs.py, the helper text is created with:

```python
self.helper = create_text(body, _locale.get("dialog.filename.helper"), "description")
```

Wait the style_name is "description", not "dialog_description". Let me check TextStyles._ALIASES... I don't see "description" there. So "description" would resolve to `layout.dialogs.default.body.description`? Let's trace:

TextStyles.__getattr__ uses _ALIASES. If name not in _ALIASES, uses name itself. So "description" → tries to resolve "description" as a theme role. That would likely fail. Hmm.

Actually let me re-check. In TextStyles._ALIASES we have:
- "dialog_description": "layout.dialogs.default.body.description"

So to use that, code should call with style_name="dialog_description". The code in dialogs.py uses "description". That's an alias for something else?

Let me search for create_text with style "description". I'll need to grep.

But to keep this task focused, I'll identify exactly which locale keys need to be base-case and which styles they use. Then we'll adjust theme formatting appropriately.

### 2. List of Locale Keys to Convert to Base-Case

These keys are currently uppercase in en_US.yaml. They should be changed to mixed/sentence case:

**Dialogs:**
- dialog.filename.title → "Enter base filename" (already ok)
- dialog.filename.header → "Enter base filename" (already ok)
- dialog.advanced.title → "Advanced Options" (title case ok)
- dialog.advanced.header → "Advanced options" (sentence case ok)
- dialog.advanced.section_output → "OUTPUT PATH" → base case: "Output path" or "Output Path"
- dialog.advanced.section_overrides → "PARAMETER OVERRIDES" → "Parameter overrides"
- dialog.advanced.section_logging → "SYSTEM LOGGING" → "System logging"
- dialog.preset.save.title → "Save preset" (ok)
- dialog.preset.save.header → "Save preset" (ok)
- dialog.preset.recall.title → "Select custom preset" (ok)
- dialog.preset.recall.header → "Select custom preset" (ok)
- dialog.title.render_error → "Render Error" (title case ok)
- dialog.advanced.overrides_placeholder → "e.g. --color-theme=theme" (ok)
- dialog.advanced.see → "See " (ok)
- dialog.advanced.docs_link → "kicad-cli render options" (ok)
- dialog.advanced.auto_desc → "Automatically save to time-stamped directories." (sentence case ok)
- dialog.advanced.log_info → "Logs are kept for 30 days..." (sentence case ok)
- dialog.advanced.open_logs → "OPEN LOGS FOLDER" → "Open logs folder"
- dialog.filename.helper → "Frames are saved as name_00001.png, name_00002.png, …" (sentence case ok)

**Sections (side panel):**
- sections.presets → "Loop presets" (ok)
- sections.parameters → "Parameters" (capitalized ok)
- sections.output → "Output settings" (ok)

**Parameters:**
- parameters.rotation_heading → "Rotation settings" (ok)
- parameters.rotation_desc → "Board: orient on spindle | Spin: orient the spindle itself" (sentence case, ok)
- parameters.lighting_hint → "Select workspace to use KiCad 3D viewer settings" (sentence case ok)
- parameters.open_logs → "OPEN LOGS FOLDER" → "Open logs folder"
- parameters.period.label → "Rotation period" (ok)
- parameters.period.desc → "Speed of 360° spin" (sentence case ok)
- parameters.direction.label → "Direction" (ok)
- parameters.direction.options.cw.label → "CW" (abbreviation, stays uppercase)
- parameters.direction.options.ccw.label → "CCW" (abbreviation, stays uppercase)
- parameters.lighting.label → "Lighting" (ok)
- parameters.lighting.options.studio.label → "STUDIO" → "Studio"
- parameters.lighting.options.dramatic.label → "DRAMATIC" → "Dramatic"
- parameters.lighting.options.soft.label → "SOFT" → "Soft"
- parameters.lighting.options.workspace.label → "WORKSPACE" → "Workspace"
- parameters.board_tilt.label → "BOARD TILT" → "Board tilt"
- parameters.board_roll.label → "BOARD ROLL" → "Board roll"
- parameters.spin_tilt.label → "SPIN TILT" → "Spin tilt"
- parameters.spin_heading.label → "SPIN HEADING" → "Spin heading"
- parameters.bg_color.label → "Background color" (ok)
- parameters.format.label → "Format" (ok)
- parameters.resolution.label → "Resolution" (ok)

**Output:**
- output.auto_desc → already sentence case
- output.format.options: ["MP4 (H.264)", "GIF", "PNG Sequence"] - these should stay as-is (proper nouns/standards)
- output.resolution.options: ["1920×1080 (1080P)", "1280×720 (720P)", "800×800 (Square)"] - keep as-is

**Buttons:**
- component.button.render.label → "RENDER" → "Render"
- component.button.stop.label → "STOP" → "Stop"
- component.button.cancel.label → "CANCEL" → "Cancel"
- component.button.ok.label → "OK" → "Ok" (or keep "OK" as abbreviation? Convention often uses "OK")
- component.button.save.label → "SAVE" → "Save"
- component.button.overwrite.label → "OVERWRITE" → "Overwrite"
- component.button.close.label → "CLOSE" → "Close"
- component.button.closepreview.label → "CLOSE PREVIEW" → "Close preview"
- component.button.options.label → "" (empty, ok)
- component.button.save_preset.label → "+ PRESET" → "+ Preset" or "+ preset"
- component.button.browse.label → "BROWSE" → "Browse"
- component.button.exit.label → "EXIT" → "Exit"
- component.button.trash.label → "" (empty, ok)

**Status:**
- component.status.rendering → "RENDERING FRAME {current}/{total}" → "Rendering frame {current}/{total}"
- component.status.complete → "Render complete" (ok)
- component.status.stopped → "Render stopped" (ok)
- component.status.stopping → "Stopping render..." (ok)
- component.status.error → "Error: {message}" (ok)
- component.status.no_presets → "No saved presets found." (ok)
- component.status.preparing → "Preparing render..." (ok)
- component.status.ready → "Ready" (ok)

**Preset Cards:**
- component.preset_card.card1.label → "HERO" → "Hero"
- component.preset_card.card2.label → "SPIN" → "Spin"
- component.preset_card.card3.label → "FLIP" → "Flip"
- component.preset_card.card4.label → "SELECT CUSTOM" → "Select custom"

**Badge:**
- component.badge.label → "PROJECT FOLDER" → "Project folder"

**System Controls (defaults for CustomDropdown, CustomToggleButton, etc.):**
- system.controls.toggle_off → "OFF" → "Off" (but toggle might want uppercase? Actually toggle buttons use `label` style which we'll make uppercase, so base can be "Off")
- system.controls.toggle_on → "ON" → "On"
- system.controls.toggle_info → "INFO" → "Info"
- system.controls.toggle_debug → "DEBUG" → "Debug"
- system.controls.dropdown_placeholder → "SELECT OPTION" → "Select option"
- system.controls.section_default → "Section" (already ok)

**Components defaults:**
- components.button.default.label → "BUTTON" → "Button"
- components.dropdown.default.label → "SELECT OPTION" → "Select option"
- components.preset_card.default.label → "PRESET" → "Preset"
- components.section.default.label → "Section" (ok)
- components.badge.label → "PROJECT FOLDER" → "Project folder"

**Dir Dialogs:**
- dir_dialog.select_output_folder → "Select output folder" (ok)
- dir_dialog.select_output_directory → "Select Output Directory" → "Select output directory"

**Viewport modes:**
- viewport.mode.wireframe → "WIREFRAME" → "Wireframe"
- viewport.mode.shaded → "SHADED" → "Shaded"
- viewport.mode.both → "BOTH" → "Both"

### 3. Action Items

1. Update `dark.yaml` (and `light.yaml` if exists) to add `formatting: "uppercase"` to:
   - `text.button`
   - `text.label`
   - (maybe create separate `text.toggle` if needed, but label covers it)

   Note: `text.metadata` should NOT have uppercase if used for long descriptions. Let's verify: which roles use metadata?
   - parameters.lighting_hint → metadata style
   - parameters.period.desc → metadata
   - parameters.rotation_desc → metadata
   - dialog.filename.helper → dialog_description → currently points to metadata? Might need to change to body.

   The metadata style currently has uppercase (line 206 in dark.yaml). That seems wrong for metadata which is typically small/caps but not uppercase? Actually looking at line 176: subheader has uppercase; line 206: metadata has uppercase. But metadata text like "Speed of 360° spin" shouldn't be all uppercase. So we probably need to remove uppercase from metadata.

   Let's check what's actually uppercase in the current UI based on the styles. From the theme:
   - title: uppercase
   - header: uppercase
   - subheader: uppercase
   - metadata: uppercase (currently)
   - button: none (should be uppercase)
   - label: none (should be uppercase)
   - status: uppercase

   But in the current locale, metadata strings like "Speed of 360° spin" are NOT uppercase. They would be rendered with metadata style which has uppercase, so they would appear uppercase. That might be a bug in the current theme! Let's check the actual test expectations. In test_locale.py, test_get_parameter_with_unit_field expects "°" which is fine.

   Actually wait, I'm confused about what's currently in the UI. The locale values are hardcoded uppercase for many strings. So even if metadata style is uppercase, the locale value might be mixed case? Let's check the original en_US.yaml for period.desc: line 89 shows `desc: "Speed of 360° spin"` - that's mixed case. So if metadata style applies uppercase, that text would become "SPEED OF 360° SPIN". That might be intentional? But the user didn't want mixed-case text to be uppercase via style? Hmm.

   The core principle: Stylistic formatting (uppercase) should be specified in the theme, not in the locale source strings. So the locale should contain the "natural" casing (e.g., "Speed of 360° spin" sentence case) and the theme style should apply uppercase if desired.

   Currently, many strings are uppercase in locale AND the theme style may or may not apply uppercase. That's redundant or inconsistent.

   So our task: Ensure theme styles have correct formatting, then revert locale strings to base-case.

   Steps:
   a) Determine for each TextStyles role whether uppercase should be applied.
   b) Update dark.yaml and light.yaml accordingly.
   c) Change all uppercase locale strings to base-case (title/sentence case as appropriate).
   d) Test to ensure visual output matches (i.e., uppercase still appears uppercase, but now via style).

   This is a design decision that needs user input: Which roles should be uppercase?

   Based on typical UI design and existing uppercase strings:
   - title: uppercase (already)
   - header: uppercase (already)
   - subheader: uppercase (already)
   - button: should be uppercase (currently not)
   - label: should be uppercase (currently not)
   - status: uppercase (already)
   - metadata: **should NOT be uppercase** (currently is) - because metadata are descriptive hints, not labels
   - dialog_description: probably NOT uppercase (check mapping)

   Let's verify what "metadata" is used for:
   - parameters.lighting_hint: "Select workspace to use KiCad 3D viewer settings" - this is a hint, shouldn't be uppercase
   - parameters.period.desc: "Speed of 360° spin" - shouldn't be uppercase
   - parameters.rotation_desc: "Board: orient on spindle | Spin: orient the spindle itself" - shouldn't be uppercase
   - dialog.filename.helper: "Frames are saved as name_00001.png..." - shouldn't be uppercase
   - output.auto_desc: "Automatically save to time-stamped directories." - shouldn't be uppercase

   So the current theme has `text.metadata` with `formatting: "uppercase"` which is likely **incorrect**. That would make all those hint texts uppercase, which doesn't match typical UI (hints are usually sentence case). But maybe they want uppercase for all small text? Unclear.

   I need to check the test expectations: In test_locale.py, there is no assertion about case for these. So tests won't catch this.

   Given the original design and the fact that user is implementing a proper separation, I'll assume that uppercase formatting should only be applied to labels/buttons/status/etc. that are meant to be stylistically uppercase. Metadata/hints should be normal case.

   Therefore plan:
   - Remove `formatting: "uppercase"` from `text.metadata` in theme.
   - Add `formatting: "uppercase"` to `text.button` and `text.label`.
   - Verify that `text.status` remains uppercase.
   - Ensure that any other roles used for uppercase UI elements (maybe a specific component label role) have uppercase.

   Also check `components.badge.label` style - currently uses inline style (lines 434-439) with no formatting. We need to add `formatting: "uppercase"` there as well, because badge label should be uppercase. Alternatively, we could have it use `ref: "@text.label"` and rely on label's uppercase. But currently it defines its own font and color. We could either:
   - Add formatting to that inline style: add `formatting: "uppercase"` under the label section.
   - OR change to use ref: "@text.label" and override only necessary properties.

   Simpler: add `formatting: "uppercase"` to the inline component style.

   Similarly, `components.toggle.items.label` uses `ref: "@text.label"` (line 621-626), so inherits label formatting. That's good.

   Also check `components.preset_card.default.label` (line 468-473) uses `ref: "@text.label"`. Good.

   So changes needed in dark.yaml (and light.yaml if exists):

   1. In `text` section:
      - For `metadata`: remove `formatting: "uppercase"` (or set to null)
      - For `button`: add `formatting: "uppercase"`
      - For `label`: add `formatting: "uppercase"`

   2. In `components.badge.label`: add `formatting: "uppercase"`

   3. In `components.button.closepreview.label` (line 753-755) - it overrides font to metadata, but doesn't specify formatting. It should probably be uppercase? The label is "CLOSE PREVIEW". Since it uses metadata font, we need to either:
      - Switch it to use `ref: "@text.button"` (which now has uppercase)
      - Or add formatting to the override: `label: { ref: "@text.metadata", formatting: "uppercase" }` - but formatting can't be applied via ref? Actually the ref resolves to a TextStyle which includes formatting. If we override just font, we can also add formatting. Looking at how text_styles resolves: it gets spec = self.theme.text_style(role). So for "button.closepreview.label", it will get that spec which may be a dict. The spec can include `formatting`. So we can add formatting there.

   Let's check: In TextStyles._get_style, it gets spec = self.theme.text_style(role). Then formatting = spec.get("formatting") if dict. So yes, we can add `formatting: "uppercase"` to the closepreview label spec.

   3. Also check any other inline styles that need uppercase:
   - `components.button.closepreview.label`
   - `components.list.default.label` - should that be uppercase? Probably yes. It uses `color` but no font/formatting defined. It likely inherits from something? Actually it's an inline dict with only color. It doesn't have `ref` so it won't inherit formatting. Let's see the structure:
     ```yaml
     label:
       color:
         default: "@colors.gray-white"
         hover: "@colors.primary"
     ```
     This is a full spec, not a ref. It doesn't have formatting. So it needs `formatting: "uppercase"` if the label should be uppercase.

   Actually looking at the component structure, many components define their label as a role reference: `ref: "@text.label"`. That's what we want. But some inline specs might override the ref. We should ensure all label specs that are meant to be uppercase include formatting: "uppercase" or inherit from a role that has it.

   To keep things manageable, we should refactor to use ref inheritance rather than duplicating formatting. But as a first pass, we can add uppercase formatting to the commonly used roles and ensure consistency.

   Given complexity, perhaps a better approach is to systematically:
   - Identify all TextStyles roles that are used in the code via create_text(..., style_name)
   - For each role, determine desired uppercase behavior.
   - Update theme accordingly.

   From the list we extracted, the style names used are:
   - title (already uppercase)
   - version (what is version? It's subtitle role probably? In _ALIASES: "version": "layout.main.header.subtitle" → that's subtitle, which currently has NO uppercase in theme? Let's check: subtitle in dark.yaml line 162-167: no formatting. So subtitle currently no uppercase. But `component.main.header.subtitle` is "0.9.0-alpha" - that shouldn't be uppercase anyway. So it's fine.
   - subheader (already uppercase)
   - metadata (currently uppercase but should not be - will change)
   - label (no uppercase currently, we'll add)
   - closepreview (this maps to? In _ALIASES line 79: "closepreview": "components.button.closepreview.label". That is an inline component spec. We'll need to update that spec to have uppercase.)
   - dialog_description (maps to "layout.dialogs.default.body.description" which is `@text.metadata` currently. Since we'll remove uppercase from metadata, this will become non-uppercase. That's correct for description text.)

   So the roles we need to address:
   - Add uppercase to `text.label`
   - Add uppercase to `components.button.closepreview.label` spec
   - Add uppercase to `components.list.default.label` if it's uppercase in design
   - Add uppercase to `components.badge.label` inline spec
   - Remove uppercase from `text.metadata`

   Then adjust locale strings to base-case.

   This is a substantial change. I should document it all in the task and provide implementation plan.

## Summary

This is a multi-step refactoring to properly separate text content casing from content strings. It requires:

- Update theme files (dark.yaml, light.yaml)
- Update all locale YAMLs (en_US.yaml, en_US_COMPLETE.yaml) to base-case
- Verify tests pass (test_locale.py expects base-case now)

Created sub-issue ALS-26 to track this work.
