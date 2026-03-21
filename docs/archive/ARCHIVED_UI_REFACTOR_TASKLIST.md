# UI Refactor Tasklist: V2 ID-Driven Alignment

This list tracks the migration of all custom components in `SpinRender/ui/custom_controls.py` to the "Convention over Configuration" pattern established in `docs/COMPONENT_CONVENTIONS.md`.

## 1. Input Consolidation (`CustomInput`)
- [x] Implement `CustomInput` class in `custom_controls.py`
    - [x] Support `type: "text" | "numeric" | "rich"` behaviors from YAML.
    - [x] Support `case: "upper" | "none"` transformations.
    - [x] Support `prefix`, `suffix`, and `unit` rendering.
    - [x] Integrate `ProjectFolderChip` for `type: "rich"`.
    - [x] Implement state-aware border coloring (Focus/Hover).
    - [x] Implement numeric filtering and arrow-key stepping logic.
- [x] Remove legacy classes:
    - [x] `NumericDisplay`
    - [x] `NumericInput`
    - [x] `CustomTextInput`
    - [x] `PathInputControl`

## 2. List Consolidation (`CustomListView`)
- [x] Implement `CustomListItem` in `custom_controls.py`
    - [x] Derive styling from `components.list.{id}.item`.
    - [x] Support labels, icons, and action buttons.
- [x] Implement `CustomListView` in `custom_controls.py`
    - [x] Manage a list of `CustomListItem` components.
    - [x] Support selection events and item removal.
- [x] Update `RecallPresetDialog` to use `CustomListView(id="custompresets")`.

## 3. Component Refactoring (V2 Alignment)
- [x] **CustomSlider**
    - [x] Move `track_h`, `thumb_w`, `thumb_h` to YAML lookups.
    - [x] Use `_theme.color()` with hover/enabled states for track and thumb.
- [x] **CustomToggleButton**
    - [x] Derive active/inactive segment colors from theme via ID.
    - [x] Resolve segment labels/icons from locale via ID.
- [x] **CustomDropdown**
    - [x] Refactor `DropdownPopup` to use theme for menu background and selection highlights.
    - [x] Unify open/closed border states.
- [x] **PresetCard**
    - [x] Remove hardcoded `role` logic; use `_theme.color(..., active=self.selected)`.
    - [x] Auto-resolve icon/label from locale if `id` is provided.
- [x] **CustomColorPicker**
    - [x] Update to use the new consolidated `CustomInput(id="hex")`.
    - [x] Pull preset swatches and borders from theme.

## 4. Call-Site Migration
- [x] **helpers.py**
    - [x] Update `create_numeric_input` to return `CustomInput`.
- [x] **controls_side_panel.py**
    - [x] Update all control initializations to use string `id` parameters.
- [x] **dialogs.py**
    - [x] Update `AdvancedOptionsDialog` and `SavePresetDialog` to use `CustomInput`.

## 5. Verification
- [x] Ensure "Pink Guard" (#FF00FF) is not visible in any control state.
- [x] Verify focus/tab-traversal works across all new `CustomInput` instances.
- [x] Confirm `ProjectFolderChip` toggles correctly in `input.path`.
