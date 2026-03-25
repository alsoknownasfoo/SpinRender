# UI/UX Audit: String Localization

**Date**: 2026-03-23
**Status**: In Progress
**Project**: SpinRender
**Auditor**: Claude Code

---

## Executive Summary

SpinRender has a **localization system in place** (`SpinRender/core/locale.py`) that loads YAML-based locale files. The system is actively used in many parts of the UI, but **several user-facing strings remain hardcoded** and need to be migrated to locale files for proper internationalization.

### Localization System Overview

- **Architecture**: Singleton `Locale` class with dot-path lookup
- **Storage**: YAML files in `resources/locale/`
- **Active Locale**: `en_US` (default)
- **Pattern**: `_locale.get("component.button.render.label", "RENDER")`
- **Existing Locale File**: `resources/locale/en_US.yaml` with comprehensive translations

---

## Hardcoded Strings Audit

### 1. Dialog Titles & Headers (Critical)

**File**: `SpinRender/ui/dialogs.py`

| Line | String | Context | Priority |
|------|--------|---------|----------|
| 159, 176 | `"Enter base filename"` | FilenameEntryDialog title & header | HIGH |
| 261 | `"Advanced Options"` | AdvancedOptionsDialog title | HIGH |
| 272 | `"Advanced options"` | AdvancedOptionsDialog header | HIGH |
| 317 | `"PARAMETER OVERRIDES"` | Section label in AdvancedOptionsDialog | HIGH |
| 354 | `"SYSTEM LOGGING"` | Section label in AdvancedOptionsDialog | HIGH |
| 441, 471 | `"Select output folder"` / `"Select Output Directory"` | DirDialog titles | HIGH |
| 451 | `"Select output folder"` | DirDialog for PNG sequence | HIGH |
| 502 | `"Save preset"` | SavePresetDialog title | HIGH |
| 522 | `"Save preset"` | SavePresetDialog header | HIGH |
| 594 | `"Select custom preset"` | RecallPresetDialog title | HIGH |
| 605 | `"Select custom preset"` | RecallPresetDialog header | HIGH |

### 2. Button Labels & Options

**File**: `SpinRender/ui/custom_controls.py`

| Line | String | Context | Priority |
|------|--------|---------|----------|
| 250 | `'OFF'`, `'ON'` | CustomToggleButton default options | HIGH |
| 536 | `"SELECT OPTION"` | CustomDropdown empty state fallback | HIGH |
| 620 | `"BUTTON"` | CustomButton fallback label | HIGH |
| 755 | `"PRESET"` | PresetCard fallback label | HIGH |
| 843 | `"Section"` | SectionLabel default | MEDIUM |

**File**: `SpinRender/ui/dialogs.py`

| Line | String | Context | Priority |
|------|--------|---------|----------|
| 360-362 | `'OFF'`, `'INFO'`, `'DEBUG'` | Logging toggle options | HIGH |

### 3. Static UI Text

**File**: `SpinRender/ui/custom_controls.py`

| Line | String | Context | Priority |
|------|--------|---------|----------|
| 1145 | `"PROJECT FOLDER"` | ProjectFolderChip label | HIGH |

**File**: `SpinRender/ui/main_panel.py`

| Line | String | Context | Priority |
|------|--------|---------|----------|
| 419, 442 | `"Preparing render..."` | Status bar message during render start | HIGH |
| 550 | `"ERROR: {error.upper()}"` | Error display formatting | HIGH |
| 566 | `"RENDER COMPLETE"` | Status bar on success | HIGH |
| 607 | `"Render stopped"` | Status bar on user cancel | HIGH |

### 4. URLs & External References

**File**: `SpinRender/ui/dialogs.py`

| Line | String | Context | Notes |
|------|--------|---------|-------|
| 345 | `"https://docs.kicad.org/master/en/cli/cli.html#pcb_render"` | Documentation link | Can stay hardcoded (external URL) |

### 5. Default Fallbacks That May Be User-Facing

These are fallback values when locale keys are missing. They should be added to locale files and the fallbacks can be removed or kept as safety nets.

**File**: `SpinRender/ui/controls_side_panel.py`

| Line | String | Locale Key | Priority |
|------|--------|------------|----------|
| 116 | `"SPINRENDER"` | `component.main.header.title` | HIGH |
| 119 | `"0.9 alpha"` | `component.main.header.subtitle` | HIGH |
| 167 | `"LOOP PRESETS"` | `sections.presets` | HIGH |
| 199 | `"PARAMETERS"` | `sections.parameters` | HIGH |
| 220 | `"ROTATION SETTINGS"` | `parameters.rotation_heading` | HIGH |
| 225 | `"BOARD TILT"` | `parameters.board_tilt.label` | HIGH |
| 232 | `"BOARD ROLL"` | `parameters.board_roll.label` | HIGH |
| 239 | `"SPIN TILT"` | `parameters.spin_tilt.label` | HIGH |
| 246 | `"SPIN HEADING"` | `parameters.spin_heading.label` | HIGH |
| 252 | `"BOARD: ORIENT ON SPINDLE | SPIN: ORIENT THE SPINDLE ITSELF"` | `parameters.rotation_desc` | HIGH |
| 328 | `"DIRECTION"` | `parameters.direction.label` | HIGH |
| 351 | `"LIGHTING"` | `parameters.lighting.label` | HIGH |
| 377 | `"SELECT WORKSPACE TO USE KICAD 3D VIEWER SETTINGS"` | `parameters.lighting_hint` | HIGH |
| 388 | `"OUTPUT SETTINGS"` | `sections.output` | HIGH |
| 395 | `"FORMAT"` | `parameters.format.label` | HIGH |
| 410 | `"RESOLUTION"` | `parameters.resolution.label` | HIGH |
| 428 | `"BACKGROUND COLOR"` | `parameters.bg_color.label` | HIGH |

### 6. Format & Resolution Choices

**File**: `SpinRender/ui/controls_side_panel.py`

| Line | String | Context | Priority |
|------|--------|---------|----------|
| 398-399 | `["MP4 (H.264)", "GIF", "PNG Sequence"]` | Format dropdown choices | HIGH |
| 413-414 | `["1920×1080 (1080P)", "1280×720 (720P)", "800×800 (Square)"]` | Resolution dropdown choices | HIGH |

These are dynamic choices that should also be localized (including the resolution names).

### 7. Wireframe Mode Toggle

**File**: `SpinRender/ui/preview_panel.py`

| Line | String | Locale Key | Priority |
|------|--------|------------|----------|
| 88-90 | `"WIREFRAME"`, `"SHADED"`, `"BOTH"` | `viewport.mode.*` | HIGH |

Note: These already have locale keys in `en_US.yaml` (lines 19-21) but are passed with fallbacks in the code.

---

## Files That Need Updates

### Priority 1: Complete `dialogs.py` localization

All dialog titles, headers, and section labels need to use `_locale.get()` with proper keys.

**Proposed locale keys structure**:

```yaml
dialog:
  filename:
    title: "Enter base filename"
    header: "Enter base filename"
  advanced:
    title: "Advanced Options"
    header: "Advanced options"
    section_output: "OUTPUT PATH"
    section_overrides: "PARAMETER OVERRIDES"
    section_logging: "SYSTEM LOGGING"
    see: "See "
    docs_link: "kicad-cli render options"
  preset:
    save:
      title: "Save preset"
      header: "Save preset"
    recall:
      title: "Select custom preset"
      header: "Select custom preset"
    no_presets: "No saved presets found."
dialogs:
  dir_select_output_folder: "Select output folder"
  dir_select_output_directory: "Select Output Directory"
```

### Priority 2: Complete `custom_controls.py` fallbacks

Replace default hardcoded strings with locale calls:

- Toggle button default labels: `OFF`/`ON`
- Dropdown empty state: `SELECT OPTION`
- Button fallback: `BUTTON`
- PresetCard fallback: `PRESET`
- SectionLabel default: `Section`

### Priority 3: Static UI text

- `"PROJECT FOLDER"` → Add to locale: `component.badge.label: "PROJECT FOLDER"`
- Status messages → Already have locale keys but need to use them consistently

### Priority 4: Format & Resolution choices

These should be in locale as arrays:

```yaml
output:
  format:
    options:
      - "MP4 (H.264)"
      - "GIF"
      - "PNG Sequence"
  resolution:
    options:
      - "1920×1080 (1080P)"
      - "1280×720 (720P)"
      - "800×800 (Square)"
```

---

## Action Plan

### Phase 1: Expand Locale File (en_US.yaml)

Add all missing keys to `resources/locale/en_US.yaml` with appropriate English values.

### Phase 2: Update Code

Replace hardcoded strings with `_locale.get("key")` calls throughout:

1. `dialogs.py` - All dialog titles and headers
2. `custom_controls.py` - All default fallback strings
3. `controls_side_panel.py` - All label fallbacks
4. `main_panel.py` - Status message literals

### Phase 3: Testing

- Verify all locale keys exist
- Test fallback behavior when keys are missing
- Ensure no regressions in UI appearance

---

## Compliance Status

| Category | Score | Notes |
|----------|-------|-------|
| **Coverage** | ~70% | Most strings localized, but gaps in dialogs |
| **Consistency** | Good | Pattern `_locale.get(key, fallback)` is established |
| **Maintainability** | Good | Single YAML file with clear hierarchy |
| **Fallback Strategy** | Good | Fallbacks provided, but should eventually be removed |

---

## Recommendations

1. **Add locale key validation** in development to catch missing keys early
2. **Remove fallback strings** once all keys are confirmed in locale files
3. **Consider locale file versioning** to track changes across releases
4. **Add pluralization support** if needed for future languages (currently not required)
5. **Document locale key naming conventions** for future contributors

---

## Next Steps

1. ✅ Create this audit report
2. 🔄 Generate updated `en_US.yaml` with all missing keys
3. 🔄 Update all Python files to use locale keys
4. 🔄 Run test suite to verify no breakage
5. 🔄 Validate with visual UI testing
6. 🔄 Update issue in vibe-kanban with completion status
