# Refactor: Layouts and CustomListView

## Objective
Transition the application architecture to a pure layout-driven and component-based system. This involves restructuring the YAML theme to separate layout concerns from atomic components and introducing a reusable `CustomListView` for structured data displays.

## Key Files & Context
- `SpinRender/resources/themes/dark.yaml`: Restructure to top-level `layout` and add `components.list`.
- `SpinRender/ui/custom_controls.py`: Add `CustomListView` and `CustomListItem`.
- `SpinRender/ui/dialogs.py`: Refactor all dialogs to use the new layout engine and list control.

## Implementation Steps

### 1. YAML Restructuring (`dark.yaml`)
- **Create `layout` node**: Move `main` and `dialogs` from `components` to `layout`.
- **Enhance `layout.dialogs`**: Add explicit `shadow`, `header`, `body`, and `footer` definitions with heights and paddings.
- **Add `components.list`**:
    - `default`: Base styling for list items (height, hover, label).
    - `custompresets`: Extension with specific actions (delete, confirm, cancel).

### 2. Custom Control Implementation (`custom_controls.py`)
- **`CustomListItem`**:
    - A stateful panel handling hover (`bind_mouse_events`).
    - Resolves styling from `components.list.{id}.item`.
    - Supports dynamic actions (icons on the right with toggleable states).
- **`CustomListView`**:
    - A `ScrolledPanel` that manages a collection of `CustomListItem` objects.
    - Provides a clean API for adding/removing items and handling selection events.

### 3. Dialog Refactoring (`dialogs.py`)
- **`BaseStyledDialog`**: 
    - Pull `SHADOW_SIZE` and colors from `layout.dialogs.default.shadow`.
    - Use `layout.dialogs.default.frame` for bg and radius.
    - Update `create_header` to use `layout.dialogs.default.header.height`.
- **`AdvancedOptionsDialog`**:
    - Use `layout.dialogs.options` for specific width/height.
    - Replace all manual `TextStyle` and `wx.ALL, 24` with theme tokens.
- **`SavePresetDialog`**:
    - Use `layout.dialogs.addpreset`.
- **`RecallPresetDialog`**:
    - Use `layout.dialogs.presets`.
    - Replace `create_preset_item` with `CustomListView(id="custompresets")`.

## Verification & Testing
- **Visual Validation**: Ensure dialog shadows, header heights, and list item spacing match the Pencil design exactly.
- **Interaction Check**: Verify that "Trash -> Confirm" workflow in the preset list still functions correctly with the new control.
- **Theme Resilience**: Verify that changing `layout.dialogs.default.shadow.size` in YAML correctly updates all dialogs.
- **Unit Tests**: Add tests for `CustomListView` selection and action events.
