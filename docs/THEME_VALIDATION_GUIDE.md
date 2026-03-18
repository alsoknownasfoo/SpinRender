# Theme Validation Guide

Ensure your theme YAML definitions match actual usage in code with the SpinRender Theme Validator.

---

## 1. Introduction

The Theme Validator is a static analysis tool that guarantees consistency between your theme YAML definitions and their usage in Python source code. It identifies three types of issues:

- **Missing tokens**: Used in code but not defined in YAML → Causes runtime errors
- **Unused tokens**: Defined in YAML but never referenced → Code bloat
- **Deprecated tokens**: Previously used but now orphaned → Candidates for removal

This is essential for maintaining a clean, consistent theme system as your application evolves.

---

## 2. Installation

The validator requires standard library modules plus PyYAML:

```bash
pip install pyyaml
```

For best results preserving YAML formatting and comments, also install ruamel.yaml:

```bash
pip install ruamel.yaml
```

---

## 3. Basic Usage

### Default validation

```bash
python tools/validate_theme.py
```

Scans `SpinRender/` source code and validates against `SpinRender/resources/themes/dark.yaml`.

### Custom paths

```bash
python tools/validate_theme.py --yaml path/to/theme.yaml --src path/to/code/
```

### Output formats

Choose between `text` (human-readable), `json` (machine-readable), or `markdown` (for documentation):

```bash
python tools/validate_theme.py --output json
python tools/validate_theme.py --output markdown > VALIDATION.md
```

---

## 4. Output Formats

### Text format (default)

```
Theme Validation Report
============================================================

Coverage: 87.3% (138/158 used tokens defined)
Used tokens: 158
Defined tokens: 186
  ❌ Missing: 12
  ⚠️  Unused: 30

❌ Missing Tokens (12)
  colors.bg.modal
    → ADD: Define colors.bg.modal = {ref: 'palette.neutral-3'} or similar
  fonts.body
    → ADD: Define in YAML under fonts.body

⚠️  Unused Definitions (30)
  palette.unused-color-1
  palette.unused-color-2
  colors.text.disabled
  ...
```

### JSON format

```json
{
  "coverage": 87.3,
  "used_count": 158,
  "defined_count": 186,
  "missing": {
    "count": 12,
    "tokens": [
      "colors.bg.modal",
      "fonts.body"
    ]
  },
  "unused": {
    "count": 30,
    "tokens": [
      "palette.unused-color-1",
      "colors.text.disabled"
    ]
  }
}
```

### Markdown format

```markdown
# Theme Validation Report

## Summary

| Metric | Value |
|--------|-------|
| Coverage | 87.3% |
| Used tokens | 158 |
| Defined tokens | 186 |
| Missing | 12 |
| Unused | 30 |

## Missing Tokens

### colors
- `colors.bg.modal`
- `colors.text.error`

### fonts
- `fonts.body`
- `fonts.heading`

## Unused Definitions

### palette
- `palette.old-color`
- `palette.unused-accent`
```

---

## 5. Interpreting Results

### Coverage Percentage

```
coverage = (used_tokens ∩ defined_tokens) / used_tokens × 100%
```

- **100%**: All tokens used in code are defined. Perfect.
- **< 100%**: Some tokens are missing. Coverage shows gap severity.
- **0%**: No used tokens are defined (completely out of sync).

### Missing Tokens

These are referenced in code but absent from YAML. They will cause runtime errors when the theme system tries to resolve them.

Each missing token comes with a **suggestion** based on its category:

- `colors.bg.modal` → Define in `colors` section with semantic reference to `palette`
- `typography.presets.body` → Copy from existing preset, adjust family/size/weight
- `palette.brand-blue` → Add raw hex color in `palette` section

### Unused Tokens

These are defined in YAML but never referenced in code. While not errors, they increase file size and maintenance burden.

**When to remove**: If truly orphaned (no future plans), use `--purge-unused`.
**When to keep**: If preparing for upcoming features, leave as-is or consider `--deprecate`.

### Deprecated Tokens

Tokens that were used in a previous baseline but are now unused. They're flagged as candidates for removal.

---

## 6. Auto-Fixing

The validator can automatically fix certain issues. **Always use `--dry-run` first** to preview changes.

### Add missing tokens (`--add-missing`)

Auto-adds all missing tokens with sensible placeholder values:

```bash
python tools/validate_theme.py --add-missing --dry-run
```

**What gets added**:

| Token type | Placeholder |
|------------|-------------|
| `colors.bg.*` | `{ref: 'palette.neutral-3'}` |
| `colors.text.*` | `{ref: 'palette.neutral-14'}` |
| `colors.accent.*` | `{ref: 'palette.cyan'}` |
| `colors.state.*` | `{ref: 'palette.green'}` |
| `palette.*` | `#XXXXXX` (hex placeholder) |
| `typography.scale.*` | `11` (pixels) |
| `typography.presets.*` | Full preset template |
| `spacing.*` | `10` (pixels) |
| `borders.radius.*` | `4` (pixels) |
| `components.*` | Type-appropriate structure |

**After adding**: Rerun validation to confirm 100% coverage.

### Remove unused tokens (`--purge-unused`)

Deletes unused token definitions from YAML:

```bash
python tools/validate_theme.py --purge-unused --dry-run
```

**What gets removed**: All tokens in the `unused` set.

**Caveats**:
- Tokens may be referenced in non-Python files (CSS, JS) → verify manually.
- Component arrays that reference removed `palette` or `colors` tokens are automatically cleaned up.

**Safety**: Backups are created by default (`theme.yaml.bak`). Use `--no-backup` to skip.

### Deprecate instead of purge (`--deprecate`)

Comments out unused tokens instead of deleting them:

```bash
python tools/validate_theme.py --deprecate --dry-run
```

Result:

```yaml
# DEPRECATED: unused since 2025-03-18 - palette.unused-color: "#FF0000"
palette:
  unused-color: "#FF0000"  # ← Entire line commented
```

All child tokens are also commented. This preserves history while signaling intent.

**When to deprecate**: For large cleanups or when unsure if tokens might be needed later.

---

## 7. Baseline Tracking

Baselines track the "known good" state of your theme across time. They enable drift detection: what changed since last release?

### Establish a baseline

```bash
python tools/validate_theme.py --baseline-mode
```

Saves `tests/theme_token_inventory.json` (or custom path via `--baseline`) with:

```json
{
  "theme_file": "dark.yaml",
  "yaml_hash": "sha256:...",
  "generated_at": "2025-03-18T12:00:00Z",
  "tokens": {
    "used": [...],
    "defined": [...],
    "missing": [...],
    "unused": [...]
  }
}
```

### Compare against baseline

```bash
python tools/validate_theme.py --compare-baseline
```

Adds these sections to the report:

```
📈 Changes Since Baseline
  Newly missing: 3
  Newly unused: 5
  Newly added to code: 12
  Removed from code: 2
```

**Interpretation**:
- **Newly missing**: Used now but weren't before → urgent (breaks new code)
- **Newly unused**: Were used before but now aren't → review for deprecation
- **Newly added to code**: New token references appeared
- **Removed from code**: Token usage deleted (may create unused definitions)

---

## 8. CI/CD Integration

Use the validator in GitHub Actions to enforce theme consistency:

```yaml
name: Theme Validation
on:
  - push
  - pull_request

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install pyyaml
      - run: python tools/validate_theme.py --strict
```

### Exit codes

The tool exits with:

- `0`: No issues
- `1`: Missing tokens found
- `2`: Unused tokens found
- `3`: Deprecated tokens found

Use flags to customize:

```bash
python tools/validate_theme.py --fail-on-missing     # Fail on missing only
python tools/validate_theme.py --fail-on-unused      # Fail on unused only
python tools/validate_theme.py --strict             # Fail on any issue
```

---

## 9. Troubleshooting

### "Syntax error in file.py" warnings

The scanner skips files with syntax errors. Fix Python syntax issues before validation.

### False positives: token used in non-Python files

The scanner only examines `.py` files. If tokens appear in CSS, JS, or config files, they won't be counted as "used". Either:
- Add those references to code, or
- Use `--purge-unused` selectively after manual review.

### YAML parsing errors

Ensure YAML is valid (use `yamllint`). The validator uses `yaml.safe_load()`.

### Placeholders are wrong

The placeholder generator uses heuristics. After `--add-missing`, review all added tokens and adjust values appropriately. The tool adds comments like `# AUTO-ADDED: verify this value` when ruamel.yaml is available.

### ruamel.yaml not detected

Install it: `pip install ruamel.yaml`. Without it, YAML formatting/comments may be lost on writes.

### Coverage < 100% but no missing tokens shown

Coverage = (intersection / used tokens). If `used == 0`, coverage is 0. Also check that token paths match exactly (extracted tokens use dot notation: `colors.bg.page`).

---

## 10. Token Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                    TOKEN LIFECYCLE                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [DEFINED + USED] ──────────┐                               │
│    ✓ Covered, active token   │                               │
│                               ↓                               │
│  [UNUSED] ─────────────┐      │   (code removed but token  │
│    ⚠️  Orphaned        │      │    still in YAML)           │
│       Warning → consider deprecate or purge               │
│                         ↓      │                               │
│  [DEPRECATED] ─────┐   │      │   (explicitly marked)       │
│    🏴‍☠️  Candidate   │   │      │                               │
│       for removal   │   ↓      │                               │
│                      │ [MISSING]                               │
│                      │   ❌ Critical                            │
│                      │   Breakage: used in code but not       │
│                      │   defined in YAML                       │
│                      ↓                                         │
│                 [REMOVED]                                    │
│                   ✗ Gone                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Transitions**:

1. **Defined+Used → Unused**: Code changes remove token references. Run validator to identify.
2. **Unused → Deprecated**: Use `--deprecate` to mark with comment.
3. **Unused → Removed**: Use `--purge-unused` to delete.
4. **Defined+Used → Missing**: YAML changes remove token. Must re-add or revert code.
5. **Missing → Defined+Used**: Use `--add-missing` to re-create definition.

---

## 11. Advanced Usage

### Scanning custom modules

If code imports `theme` from a non-standard location, the scanner still works (it's pure AST). Just ensure the file path is under `--src`.

### Custom token categories

The validator recognizes categories based on token prefix:

- `colors.*`, `palette.*` → Color tokens
- `spacing.*`, `typography.scale.*` → Size tokens  
- `typography.*` (non-scale) → Font tokens (categorized as 'fonts')
- `components.*` → Component tokens
- Everything else → 'fonts' (fallback)

If your theme uses different prefixes, extend `_categorize_tokens()` in `scanner.py`.

---

## 12. Real-World Example

Running on the SpinRender codebase:

```bash
$ python tools/validate_theme.py --output text

Theme Validation Report
============================================================

📊 Summary
  Coverage: 91.2% (142/156 used tokens defined)
  Used tokens: 156
  Defined tokens: 185
  ❌ Missing: 14
  ⚠️  Unused: 33

❌ Missing Tokens (14)
  colors.bg.modal
    → ADD: Define colors.bg.modal = {ref: 'palette.neutral-3'}
  colors.state.hover
    → ADD: Define state overlay color in colors.state or colors.accent
  typography.presets.code
    → ADD: Copy from existing preset, adjust family/size/weight

⚠️  Unused Definitions (33)
  palette.unused-shade-1
  palette.unused-shade-2
  colors.hover.overlay
  ...

Recommendations:
  - Add missing tokens to theme YAML (see suggestions above)
  - Consider removing unused definitions to reduce file size
```

Apply fixes:

```bash
$ python tools/validate_theme.py --add-missing --dry-run
[DRY RUN] Preview of changes:
  Would add 14 missing tokens:
    - colors.bg.modal -> {'ref': 'palette.neutral-3'}
    - colors.state.hover -> {'ref': 'palette.overlay-light'}
    ...

$ python tools/validate_theme.py --add-missing
Changes applied successfully!
Backup saved: SpinRender/resources/themes/dark.yaml.bak
```

Re-run to verify:

```bash
$ python tools/validate_theme.py
...
Coverage: 100.0% (156/156 used tokens defined)
✅ Perfect coverage!
```

---

## 13. Frequently Asked Questions

**Q: Can the validator detect tokens used in Jinja2 or string formatting?**

A: No, it's pure AST analysis of Python code. It only detects `theme.color("token")` literal strings. Dynamic construction like `theme.color(f"colors.{var}")` is not detected.

**Q: What about `Theme.current().color()` vs `theme.color()`?**

A: Both are supported. The visitor recognizes `Theme.current().color()` pattern as well.

**Q: Can I exclude certain directories?**

A: Not currently. The scanner recurses under `--src`. Create a wrapper script that moves code you want excluded out of the scan tree.

**Q: How do I handle tokens used in tests?**

A: Test files are `.py` files and will be scanned. If tests reference tokens not used in production, those tokens will be marked as "missing" unless defined. Either:
- Define test-only tokens in YAML (they're harmless), or
- Refactor tests to use mock themes.

**Q: Why does `--add-missing` add weird placeholder values?**

A: The heuristics are best-effort. Always review the generated YAML and adjust values to match your design system.

**Q: Can the validator work with multiple theme YAMLs?**

A: Not in the current CLI. Run separately per theme variant if you have `dark.yaml`, `light.yaml`, etc.

---

## 14. Contributing

The validator is located in `tools/theme_validator/`:

- `scanner.py` — AST-based token extraction
- `yaml_parser.py` — YAML parsing and token collection
- `comparator.py` — Set operations and report generation
- `fixer.py` — Automated fix operations

Tests: `tests/unit/test_validate_theme.py`

---

*Last updated: 2025-03-18*
