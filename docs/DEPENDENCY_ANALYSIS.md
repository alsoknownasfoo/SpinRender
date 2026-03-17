# Dependency Analysis Report

**Date:** 2026-03-17
**Phase:** Phase 2 - Dependency Inversion & State Management
**Task:** 2.1 - Analyze utils → ui dependency direction

---

## Executive Summary

**Finding:** There is a **circular dependency** between `utils/dependencies.py` and `ui/custom_controls.py`.

- `utils/dependencies.py` imports from `ui.custom_controls` at **3 locations**
- `spinrender_plugin.py` imports from `utils.dependencies`
- `ui/custom_controls.py` currently does NOT import from `utils`, so the cycle is not yet manifest
- **Risk:** As soon as `ui/custom_controls.py` (or any `ui/` module) needs to import from `utils/`, a circular import will break the application

**Root Cause:** `utils/dependencies.py` is not pure utility code—it contains UI components (`DependencyCheckDialog`) and depends on UI data/classes (`CustomButton`, `get_mdi_font`, font constants).

**Dependency Direction (Current):**

```
spinrender_plugin.py
        ↓
utils/dependencies.py ──────→ ui/custom_controls.py
        │                               │
        └─────────────────────┬─────────┘
                              │ (potential future)
                              ↓
                          utils/logger.py or other utils
```

---

## Detailed Analysis

### 2.1.1 Module Import Survey

#### `utils/dependencies.py` imports from UI:

| Line | Import | Usage |
|------|--------|-------|
| 14 | `from ui.custom_controls import CustomButton, get_mdi_font` | Used in `DependencyCheckDialog.build_ui()` (lines 452, 457) |
| 197 | `from ui.custom_controls import _JETBRAINS_MONO, _MDI_FONT_FAMILY, _OSWALD` | Used in `_ensure_macos_fonts()` to check font availability |
| 452 | `from ui.custom_controls import CustomButton` (inside method) | Used to access `CustomButton.ICONS` dict for status icons |

#### `ui/custom_controls.py` imports from utils:

**None currently detected.** This prevents a manifest circular import, but the dependency is inverted.

#### Other UI modules importing from utils:

**None detected.** Search: `grep -r "from utils" SpinRender/ui/*.py` returns no matches.

---

### 2.1.2 Problem Classification

According to `docs/ARCHITECTURE_IMPLEMENTATION.md` Section 5:

> The intent is a **one-way dependency flow**: `ui` may import from `utils` and `core`, but `utils` and `core` must NOT import from `ui`.

**Violation:** `utils/dependencies.py` → `ui/custom_controls.py` ❌

**Why it's problematic:**
1. **Circular import risk:** If any `ui/` module later imports from `utils/` (e.g., for logging, config), Python will raise `ImportError` due to partial module initialization.
2. **Layering violation:** `utils` should contain UI-agnostic utilities. Importing UI components makes it impossible to use `utils` from non-UI contexts (e.g., CLI tools, tests without display).
3. **Testability:** `DependencyChecker` and `DependencyCheckDialog` are tightly coupled to wx and custom controls, making unit testing difficult without importing the entire UI stack.
4. **Maintainability:** Changes to `custom_controls.py` can break `dependencies.py` even if the change is unrelated, due to import side-effects.

---

### 2.1.3 What's in `dependencies.py`?

Two distinct concerns:

1. **`DependencyChecker`** (lines 16-351) - Pure logic class
   - Checks for external commands (`kicad-cli`, `ffmpeg`)
   - Checks for Python packages (`PyOpenGL`, `numpy`, `trimesh`)
   - Platform-specific executable discovery
   - Installation orchestration
   - **Dependencies:** `subprocess`, `platform`, `os`, `sys`, `wx` (only for `wx.MessageDialog` and `wx.ProgressDialog` in `check_and_prompt()`)

2. **`DependencyCheckDialog`** (lines 354-606) - wx.Dialog subclass
   - UI for displaying missing dependencies
   - Uses `CustomButton`, `get_mdi_font`, font constants, icon dict
   - Hardcoded theme colors (still using raw wx.Colour, pre-theme-migration cleanup needed)
   - **Dependencies:** `wx`, `CustomButton`, `get_mdi_font`, font name constants

---

### 2.1.4 Why These Dependencies Exist

| Dependency | Why It's Used | Can It Be Removed? |
|------------|---------------|-------------------|
| `CustomButton` | For styled EXIT/INSTALL buttons and consistent UI | Yes - replace with `wx.Button` or move dialog to UI package where CustomButton is naturally available |
| `get_mdi_font()` | To display Material Design Icons status symbols | Yes - inline the font creation or use a helper from `foundation/typography.py` |
| `_JETBRAINS_MONO`, etc. | To check if fonts are installed on system | Yes - move these string constants to `utils/fonts.py` or `foundation/fonts.py` |
| `CustomButton.ICONS` | To get icon glyphs for status indicators | Yes - extract the `ICONS` dict to a shared module |

---

### 2.1.5 Impact on Architecture

The circular dependency issue is **blocking** because:
- **Phase 2** requires refining `utils/dependencies.py` to remove UI imports
- **Phase 7** (God Class Extraction) will likely require `ui/main_panel.py` to import from `utils` for helper functions; if the cycle exists, that refactor will break
- **Future** `settings` dataclass (Phase 2.3) might live in `core/` and be used by both `ui/` and `utils/`; cycles would prevent this

**Conclusion:** Fixing the dependency inversion is a **P0 prerequisite** for all subsequent phases.

---

## Recommended Break Strategy

### Principle: Separate Concerns by Layer

```
foundation/          # Zero UI dependencies (pure data/utilities)
  ├── fonts.py       # Font name constants (JetBrains Mono, MDI, Oswald)
  ├── icons.py       # Icon mappings (mdi-check-circle, etc.)
  └── widgets.py     # Pure widget specs (no wx imports)

utils/               # No imports from ui/, core/, or foundation/
  ├── dependencies.py  # DependencyChecker only (pure logic)
  ├── logger.py        # Logging utilities (needs checking)
  └── ...

core/                # Business logic, can import from foundation/utils
  ├── presets.py
  ├── renderer.py
  ├── preview.py
  └── ...

ui/                  # UI layer, imports from all lower layers
  ├── theme.py
  ├── custom_controls.py
  ├── dialogs.py          # ← DependencyCheckDialog moves here
  ├── main_panel.py
  ├── dependency_dialog.py (new, or just put in dialogs.py)
  └── ...
```

### Step-by-Step Migration

#### **Action 1: Extract font constants to `foundation/fonts.py`**

```python
# foundation/fonts.py
"""Font name constants used throughout the application.

These are pure string constants with no wx dependencies.
"""
JETBRAINS_MONO = "JetBrains Mono"
MDI_FONT_FAMILY = "Material Design Icons"
OSWALD = "Oswald"
INTER = "Inter"
```

Update `utils/dependencies.py`:
```python
# Remove:
# from ui.custom_controls import _JETBRAINS_MONO, _MDI_FONT_FAMILY, _OSWALD

# Add:
from foundation.fonts import JETBRAINS_MONO, MDI_FONT_FAMILY, OSWALD
```

Also update any `ui/` modules that reference these private constants to import from `foundation.fonts` instead.

#### **Action 2: Extract icon mappings to `foundation/icons.py`**

```python
# foundation/icons.py
"""Static icon glyph mappings for UI.

These map semantic icon names to their Unicode/char representation.
"""
STATUS_ICONS = {
    "mdi-check-circle": "✓",  # or actual MDI glyph
    "mdi-close-circle": "✗",
}
```

If `CustomButton.ICONS` contains these, extract them to this module.

Then in `utils/dependencies.py`:
```python
# Remove:
# from ui.custom_controls import CustomButton
# icon_char = CustomButton.ICONS.get(status_symbol, "")

# Add:
from foundation.icons import STATUS_ICONS
icon_char = STATUS_ICONS.get(status_symbol, "")
```

#### **Action 3: Move `DependencyCheckDialog` to `ui/dialogs.py` or `ui/dependency_dialog.py`**

- This is a **UI dialog**, so it belongs in the UI layer
- It should import `CustomButton` and theme colors from `ui.theme` (will need theme migration cleanup)
- Move the entire class definition (lines 354-606) to a new file or existing `dialogs.py`
- In `dependencies.py`, keep only `DependencyChecker` class; remove the dialog class
- Update `DependencyChecker.check_and_prompt()` to import `DependencyCheckDialog` from its new UI location:
  ```python
  # Old (inline class, no import needed)
  # dialog = DependencyCheckDialog(...)

  # New (dialog in ui.dialogs)
  from ui.dialogs import DependencyCheckDialog
  dialog = DependencyCheckDialog(...)
  ```

**Critical:** This creates a dependency `utils/dependencies.py` → `ui/dialogs.py`. Is this allowed?

#### **Action 4: Evaluate `utils` → `ui` imports after cleanup**

After moving `DependencyCheckDialog` to `ui/`, `utils/dependencies.py` will still import it for `check_and_prompt()`.

**Allowed?** According to the architecture document, the ideal direction is:
- `ui` may import from `utils` and `core` ✓
- `utils` should NOT import from `ui` ✗

So even after moving the dialog to `ui`, `DependencyChecker` (in `utils`) importing `DependencyCheckDialog` (in `ui`) is still an inverted dependency.

**Solutions:**

**Option A (Interface-based):** Define an abstract dialog interface in `utils/interfaces.py`, implement it in `ui/dialogs.py`, and inject the dialog class into `DependencyChecker`:

```python
# utils/dependencies.py
class DependencyChecker:
    def __init__(self, dialog_class=None):
        self.dialog_class = dialog_class or DependencyCheckDialog  # Problem: still imports

    def check_and_prompt(self):
        if self.dialog_class:
            dialog = self.dialog_class(...)
```

But we still need to import the default dialog class somewhere. Better: `spinrender_plugin.py` constructs the checker with the UI dialog class:

```python
# spinrender_plugin.py
from ui.dialogs import DependencyCheckDialog
from utils.dependencies import DependencyChecker

checker = DependencyChecker(dialog_class=DependencyCheckDialog)
```

And in `utils/dependencies.py`, remove any direct import of the dialog class:

```python
# utils/dependencies.py
class DependencyChecker:
    def __init__(self, dialog_factory=None):
        self.dialog_factory = dialog_factory

    def check_and_prompt(self):
        if self.dialog_factory:
            dialog = self.dialog_factory(self, ...)
            ...
```

This is **dependency injection** - `DependencyChecker` doesn't know about the UI; it receives a callable that creates the dialog.

**Option B (Relocate DependencyChecker):** Move `DependencyChecker` to `ui/dependencies.py` since it's tightly coupled to wx and UI dialogs. Then `utils/` no longer needs this module at all.
- Problem: `spinrender_plugin.py` currently imports from `utils.dependencies`; would need to change import
- This might be cleanest: `DependencyChecker` is an **UI helper**, not a general utility

**Option C (Split `dependencies.py`):**
- Keep pure logic (command checking, package detection) in `utils/dependency_checks.py`
- Move UI-related `DependencyChecker.check_and_prompt()` and `DependencyCheckDialog` to `ui/dependencies.py`
- `spinrender_plugin` imports from `ui.dependencies` for the full checker + dialog

**Recommendation:** **Option C (Split)** because:
- The "dependency checker" concept is inherently UI-related (it shows dialogs)
- Pure functions like `check_dependency()`, `check_python_package()` could be useful in non-UI contexts (e.g., CLI setup script)
- Splitting honors single responsibility: `utils/` has the pure checking logic, `ui/` has the interactive prompt

---

### 2.1.6 Additional Issues to Address

1. **`utils/logger.py` may import from UI** - Need to verify:
   ```bash
   grep -n "from ui" utils/logger.py
   ```
   If it does, apply similar extraction.

2. **`ui/custom_controls.py` uses private font constants from itself**:
   - Lines with `_JETBRAINS_MONO`, `_MDI_FONT_FAMILY`, `_OSWALD` should switch to `foundation.fonts` after extraction
   - This needs to be done in a separate PR to avoid breaking builds

3. **Theme migration cleanup:** `DependencyCheckDialog` still has hardcoded `wx.Colour` calls (lines 372-380). After moving to `ui/dialogs.py`, these should be migrated to use `theme.*` tokens in a follow-up task (Phase 1 verification missed this file!).
   - `dependencies.py` is NOT listed in `MIGRATION_STRATEGY.md` or `PROJECT_PLAN.md` Phase 1, but it contains a UI dialog that should be themed.

---

## Proposed Task 2.2 Workplan (Based on Analysis)

### Refactor: Split `dependencies.py` and eliminate UI imports from `utils/`

#### Subtask A: Create `foundation/` package and move constants
1. Create `SpinRender/foundation/__init__.py` (empty)
2. Create `SpinRender/foundation/fonts.py` with font name constants
3. Create `SpinRender/foundation/icons.py` with icon glyph mappings
4. Update `ui/custom_controls.py` to use `foundation.fonts` instead of private `_JETBRAINS_MONO` etc.
5. Update `utils/dependencies.py` to import from `foundation.fonts` and `foundation.icons`

#### Subtask B: Split `dependencies.py`
1. In `utils/`:
   - Rename current file to `utils/_dependencies_ui.py` (temporary)
   - Create new `utils/dependencies.py` with only pure logic:
     - `REQUIRED_DEPS` dict
     - `DependencyChecker` methods: `__init__`, `_get_python_executable`, `check_dependency`, `check_python_package`, `check_all`, `install_dependency`
     - Keep `DependencyChecker` class but **remove** `check_and_prompt()` and `_ensure_macos_fonts()` (UI-specific)
2. In `ui/`:
   - Create `ui/dependencies.py` or add to `ui/dialogs.py`:
     - `DependencyCheckDialog` class (moved from `utils/_dependencies_ui.py`)
     - Modified `DependencyChecker` subclass or wrapper that includes UI methods:
       - `check_and_prompt(self)` - uses dialog
       - `_ensure_macos_fonts(self)` - uses UI prompts
   - Or: Keep `DependencyChecker` in `utils/` but make `check_and_prompt()` accept a dialog factory (dependency injection)

#### Subtask C: Update `spinrender_plugin.py`
Change imports:
```python
# Before:
from utils.dependencies import DependencyChecker

# After (Option C - UI-layer checker):
from ui.dependencies import DependencyChecker
# OR (if using dependency injection):
from utils.dependency_checks import DependencyChecker
from ui.dialogs import DependencyCheckDialog
checker = DependencyChecker(dialog_factory=DependencyCheckDialog)
```

#### Subtask D: Update tests
- Update any test files that import from `utils.dependencies` to match new structure
- Add `__init__.py` files as needed for package structure

#### Subtask E: Theme migration for `DependencyCheckDialog`
- After it's in `ui/dialogs.py`, replace hardcoded colors with `theme.*` imports
- This should follow the same pattern as `BaseStyledDialog` migration (Task 1.6)

---

## Verification Checklist

- [ ] No `utils/*.py` file imports from `ui/`, `core/`, or `foundation/`
- [ ] `ui/*.py` can import from `utils/`, `core/`, `foundation/` freely
- [ ] All font name constants defined in `foundation/fonts.py`
- [ ] All icon mappings defined in `foundation/icons.py` (or similar)
- [ ] `DependencyChecker` pure logic separated from UI logic
- [ ] `spinrender_plugin.py` imports correctly and runs without circular import errors
- [ ] Unit tests pass after restructuring
- [ ] `DependencyCheckDialog` themed consistently with `BaseStyledDialog` (uses `theme.*`)

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing plugin startup flow | High | Test in KiCad after each step; have rollback plan |
| Moving `DependencyChecker` changes public API | Medium | Update `spinrender_plugin.py` in same commit; no external users |
| Font constant references missed in migration | Low | Grep for `_JETBRAINS_MONO` etc. after change |
| Test imports need updating | Low | Run tests immediately; fix import errors |

---

## Conclusion

**Task 2.1 Deliverable:** This analysis document.

**Next Step:** Approve the break strategy and proceed to **Task 2.2** with the workplan outlined in Section 6.

**Estimated Effort:** 1.5 days (slightly higher than original 1.5d due to `foundation/` creation and dialog theming follow-up).

---

**Appendix: Raw Import Data**

```bash
$ grep -rn "from ui.custom_controls" SpinRender/utils/
SpinRender/utils/dependencies.py:14:from ui.custom_controls import CustomButton, get_mdi_font
SpinRender/utils/dependencies.py:197:from ui.custom_controls import _JETBRAINS_MONO, _MDI_FONT_FAMILY, _OSWALD
SpinRender/utils/dependencies.py:452:from ui.custom_controls import CustomButton

$ grep -rn "from utils" SpinRender/ui/
# (none found - good)
```
