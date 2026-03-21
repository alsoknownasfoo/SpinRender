# Theme Validation Guide (V2 Mastering Schema)

Ensure your theme YAML definitions match actual usage in code with the SpinRender Theme Validator.

---

## 1. Introduction

The Theme Validator is a static analysis tool that guarantees consistency between your theme YAML definitions and their usage in Python source code. It identifying three types of issues:

- **Missing tokens**: Used in code but not defined in YAML → Causes runtime errors
- **Unused tokens**: Defined in YAML but never referenced → Code bloat
- **Deprecated tokens**: Previously used but now orphaned → Candidates for removal

---

## 2. Terminology (Mastering Schema)

The validator uses terminal V2 hierarchical terminology:

| Category | Description | Examples |
|----------|-------------|----------|
| `palette` | Raw color values | `palette.cyan`, `palette.neutral-1` |
| `colors` | Semantic color aliases | `colors.primary`, `colors.bg.page` |
| `glyphs` | Unicode icon characters | `glyphs.render-action`, `glyphs.folder` |
| `text` | Font + Color composites | `text.body.font`, `text.body.color` |
| `spacing` | Pixel layout values | `spacing.lg`, `spacing.md` |
| `borders` | Shape and stroke properties | `borders.radius.md`, `borders.default.color` |
| `components` | Element-specific design | `components.button.ok.frame.bg` |

---

## 3. Basic Usage

### Run validation

```bash
python tools/validate_theme.py
```

Scans `SpinRender/` source code and validates against `SpinRender/resources/themes/dark.yaml`.

### Auto-Fixing

The validator can automatically add missing tokens with sensible placeholders:

```bash
python tools/validate_theme.py --add-missing
```

**V2 Placeholders**:
- `text.*.font` → Template with size 11, mono typeface
- `glyphs.*` → Unicode placeholder `\UXXXXXXXX`
- `colors.bg.*` → Reference to `palette.neutral-3`

---

## 4. CI/CD Integration

The tool exits with specific codes for pipeline integration:

- `0`: No issues
- `1`: **Missing tokens found** (Critical - blocks PR)
- `2`: Unused tokens found (Warning)
- `3`: Deprecated tokens found (Warning)

```bash
# Fail on any missing token
python tools/validate_theme.py --fail-on-missing
```

---

## 5. Troubleshooting

### Coverage < 100%
Ensure you are using the dot-path notation in code: `_theme.color("colors.bg.page")`. String literals passed to theme methods are extracted via AST.

### False Positives
The scanner only examines `.py` files. If a token is only used in a locale YAML or documentation, it will be marked as "Unused". This is intentional to ensure the Python API remains synchronized.

---

*Last updated: 2026-03-19*
