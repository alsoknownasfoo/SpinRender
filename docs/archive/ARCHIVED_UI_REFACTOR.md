# UI Design System & Refactor Intentions

This document outlines the core intentions and planned architectural decisions for the UI styling system. The primary objective is to transition from a fragmented, hardcoded approach to a centralized, semantic, and highly maintainable configuration engine.

## 1. Core Intentions

### 1.1. Manageable Design Space (Centralization)
The foundational goal is to consolidate **every** color and font definition into a single source of truth (`UITheme`).
- **Elimination of Leakage**: No component should define its own hex values or font parameters.
- **Maintenance**: Branding changes or theme corrections should be performed by modifying a single class in `custom_controls.py`.

### 1.2. Semantic Token System
The system will move away from literal color requests (e.g., "Cyan") to semantic part requests (e.g., `BUTTON_RENDER_FILL`).
- **Decoupling**: The *intent* of an element is decoupled from its *appearance*.
- **Consistency**: All components of a certain type (e.g., all axis sliders) stay perfectly synchronized by requesting the same semantic tokens.

### 1.3. Theme-Aware Engine (Dark/Light)
The plan is to introduce a prefix-based theme engine (`D_` for Dark, `L_` for Light).
- **Programmatic Mode Switching**: The engine should remove explicit `inverted` definitions from the codebase and instead switch between dark and light token variants programmatically.
- **Contrast Recovery**: When text over a background does not meet the minimum accessibility contrast threshold, the color lookup should retry using the opposite `L_` or `D_` token family before falling back to other generated adjustments.

### 1.4. External Configuration Strategy (YAML)
The configuration model should be designed from the outset to support moving all color and font definitions into an external YAML file.
- **Designer Access**: YAML should allow non-developers to adjust the look and feel without touching Python code.
- **Hot-Reloading**: Future implementations should be able to monitor the YAML file for changes, allowing real-time styling updates without restarting the plugin.
- **Architecture**: The planned `THEME_COMPONENT_TYPE_ELEMENT` naming convention should provide the structure needed for a clean YAML schema.
- **Schema Versioning**: The configuration format should include an explicit schema version so token definitions can evolve without silent breakage.
- **Validation**: Config files should be validated at load time, with clear errors for unknown tokens, malformed arrays, and invalid override shapes.

## 2. Architectural Features

### 2.1. Explicit Color State Arrays
To provide granular control over interaction feedback, color definitions should support a 5-element array pattern:
`VARIABLE = (DEFAULT, HOVER, ACTIVE, SELECTED, DISABLED)`
- **Index 0 (DEFAULT)**: The base resting color.
- **Index 1 (HOVER)**: Triggered when the mouse enters the component.
- **Index 2 (ACTIVE)**: Triggered when the component is pressed/clicked.
- **Index 3 (SELECTED)**: Triggered when the component is in a persistent "ON" or "active" state (e.g., a selected preset).
- **Index 4 (DISABLED)**: Triggered when `IsEnabled()` is false.
- **Array Contract**: Array-based definitions should have a fixed positional schema, and omitted entries should be treated as intentional gaps to be resolved by documented fallback behavior.

### 2.2. Programmatic State Generation
The `UITheme.get_color` engine should handle fallback logic intelligently. If an explicit color is missing from a state array (or if a single color is provided):
- **Hover**: Automatically shifts brightness up by 10%.
- **Active**: Automatically shifts brightness down by 10%.
- **Selected**: Defaults to the global `PRIMARY_HIGHLIGHT` (Cyan).
- **Disabled**: Automatically applies a 50% alpha transparency mask.
- **Accessibility Guardrail**: Generated states should preserve a minimum accessibility contrast ratio for text and iconography against their resolved backgrounds.
- **Dark/Light Retry**: If the initially resolved token fails the contrast check, the engine should attempt the paired dark or light token variant before applying generated fallback adjustments.

### 2.3. Structured Typography (`TextStyle`)
Font properties should be encapsulated in a dedicated `TextStyle` class.
- **Array-Based Definitions**: Font definitions should be represented as arrays so a single token can describe family, size, weight, formatting behavior, and color.
- **Override Precedence**: Component-level text style overrides should take precedence over the base `TextStyle` definition, which should take precedence over semantic token defaults and finally any generated fallback behavior.
- **Decoupling**: `CustomText` uses a `style` parameter for font selection and a `type` parameter for color roles.
- **Format Control**: Support for automatic case formatting (e.g., OSWALD headers always forcing uppercase).
- **Variable Weights**: Built-in support for the custom fonts (JetBrains Mono, Oswald) and their specific weights.

### 2.4. Interaction Integrity
The interaction model should include mouse event pass-through for non-interactive text components. Non-interactive labels should not intercept clicks intended for their parent containers (like `PresetCard`), ensuring a seamless user experience.

### 2.5. Unified Component Construction Pattern
All component creation functions should align on a single construction pattern so layout, styling, and interaction behavior are applied consistently across the UI.
- **Shared Build Sequence**: Component factories should follow the same order of operations when creating frames, applying theme tokens, instantiating text, and attaching mouse or interaction handlers.
- **Consistent Inputs**: Component builders should accept a predictable set of inputs for parent container, semantic style tokens, text styles, sizing, and event callbacks.
- **Composable Helpers**: Repeated setup logic such as frame initialization, text creation, spacing, and event wiring should be extracted into shared helpers rather than reimplemented per component.
- **Interaction Defaults**: Mouse event binding, pass-through behavior, hover state updates, and disabled handling should be applied through the same reusable pattern for every interactive component.
- **Structural Consistency**: Components that serve similar roles should produce similar internal hierarchies so future styling, testing, and refactoring can rely on predictable structure.

### 2.6. Validation and Testing
The design system should be backed by both structural validation and focused regression testing.
- **Token-Level Validation**: Tests should verify that every semantic token resolves correctly across dark and light variants, interactive states, and disabled states.
- **Contrast Coverage**: Tests should cover contrast-sensitive cases, including text over buttons, chips, cards, and highlighted surfaces, to verify automatic `L_`/`D_` switching.
- **Visual Regression Fixtures**: A small set of canonical UI fixtures should be captured for dark, light, selected, disabled, and high-contrast scenarios.
- **Failure Clarity**: Validation and tests should fail with enough context to identify the offending token, style array, or component override quickly.
- **Visual Reference**: Refer to docs/VISUAL_REFERENCE.jpg for how the UI should look.