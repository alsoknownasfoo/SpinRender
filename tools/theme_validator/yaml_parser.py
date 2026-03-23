#!/usr/bin/env python3
"""
Theme YAML Parser — Extract token paths from theme configuration.

Parses a theme YAML file and returns categorized sets of token paths.
"""
from pathlib import Path
from typing import Any, Dict, Set

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    yaml = None
    _YAML_AVAILABLE = False

# Custom exception for theme validator errors


# Embedded fallback theme data for default dark theme (used when PyYAML is not available)
# This is a Python representation of SpinRender/resources/themes/dark.yaml
_FALLBACK_DARK_THEME = {
    "meta": {
        "name": "Dark",
        "version": "1.0.0",
        "description": "Default dark theme matching the SpinRender design system"
    },
    "palette": {
        "neutral-1": "#0A0A0A",
        "neutral-2": "#0D0D0D",
        "neutral-3": "#121212",
        "neutral-4": "#1A1A1A",
        "neutral-5": "#1A1A1A",
        "neutral-6": "#222222",
        "neutral-7": "#1F1F1F",
        "neutral-8": "#222222",
        "neutral-9": "#2A2A2A",
        "neutral-10": "#323232",
        "neutral-11": "#777777",
        "neutral-12": "#555555",
        "neutral-13": "#CCCCCC",
        "neutral-14": "#E0E0E0",
        "neutral-15": "#FFFFFF",
        "neutral-16": "#333333",
        "neutral-17": "#787878",
        "neutral-18": "#646464",
        "cyan": "#00BCD4",
        "yellow": "#FFD600",
        "green": "#4CAF50",
        "orange": "#FF6B35",
        "red": "#FF3B30",
        "purple": "#AA6BFF",
        "pink": "#FF4081",
        "preset-red": "#FF6B6B",
        "preset-amber": "#FFB46B",
        "preset-blue": "#4D96FF",
        "preset-purple": "#AA6BFF",
        "danger-dark": "#8C0000",
        "danger-hover": "#DC1414",
        "danger-medium": "#B40000",
        "overlay-faint": "rgba(255,255,255,0.08)",
        "overlay-light": "rgba(255,255,255,0.16)",
        "overlay-medium": "rgba(255,255,255,0.27)",
        "transparent": "rgba(0,0,0,0)",
        "black-solid": "#000000"
    },
    "colors": {
        "bg": {
            "page": {"ref": "palette.neutral-3"},
            "panel": {"ref": "palette.neutral-5"},
            "surface": {"ref": "palette.neutral-8"},
            "input": {"ref": "palette.neutral-2"},
            "inner": {"ref": "palette.neutral-6"},
            "overlay": {"ref": "palette.neutral-4"},
            "track": {"ref": "palette.neutral-10"},
            "hover": {"ref": "palette.neutral-9"},
            "output": {"ref": "palette.neutral-1"}
        },
        "text": {
            "primary": {"ref": "palette.neutral-14"},
            "secondary": {"ref": "palette.neutral-11"},
            "muted": {"ref": "palette.neutral-12"},
            "on-accent": {"ref": "palette.neutral-2"},
            "on-danger": {"ref": "palette.neutral-15"}
        },
        "accent": {
            "primary": {"ref": "palette.cyan"},
            "secondary": {"ref": "palette.yellow"},
            "success": {"ref": "palette.green"},
            "warning": {"ref": "palette.orange"}
        },
        "border": {
            "default": {"ref": "palette.neutral-7"},
            "subtle": {"ref": "palette.neutral-10"},
            "focus": {"ref": "palette.cyan"},
            "strong": {"ref": "palette.neutral-10"}
        },
        "preset": [
            {"ref": "palette.preset-red"},
            {"ref": "palette.preset-amber"},
            {"ref": "palette.preset-blue"},
            {"ref": "palette.preset-purple"}
        ],
        "state": {
            "hover-overlay": {"ref": "palette.overlay-light"},
            "pressed-overlay": {"ref": "palette.overlay-medium"},
            "ghost-overlay": {"ref": "palette.overlay-faint"},
            "active": {"ref": "palette.green"},
            "danger": {"ref": "palette.danger-medium"},
            "danger-hover": {"ref": "palette.danger-hover"},
            "danger-pressed": {"ref": "palette.danger-dark"}
        }
    },
    "typography": {
        "families": {
            "mono": "JetBrains Mono",
            "display": "Oswald",
            "icon": "Material Design Icons",
            "inter": "Inter"
        },
        "scale": {
            "xs": 8,
            "sm": 9,
            "base": 11,
            "md": 13,
            "lg": 14,
            "xl": 18,
            "icon": 14,
            "icon-lg": 20
        },
        "weights": {
            "normal": 400,
            "semibold": 600,
            "bold": 700
        },
        "presets": {
            "body": {
                "family": {"ref": "typography.families.mono"},
                "size": {"ref": "typography.scale.base"},
                "weight": {"ref": "typography.weights.normal"}
            },
            "body_strong": {
                "family": {"ref": "typography.families.mono"},
                "size": {"ref": "typography.scale.base"},
                "weight": {"ref": "typography.weights.semibold"}
            },
            "label_sm": {
                "family": {"ref": "typography.families.mono"},
                "size": {"ref": "typography.scale.sm"},
                "weight": {"ref": "typography.weights.semibold"}
            },
            "label_xs": {
                "family": {"ref": "typography.families.mono"},
                "size": {"ref": "typography.scale.xs"},
                "weight": {"ref": "typography.weights.bold"}
            },
            "numeric_value": {
                "family": {"ref": "typography.families.mono"},
                "size": {"ref": "typography.scale.md"},
                "weight": {"ref": "typography.weights.semibold"}
            },
            "numeric_unit": {
                "family": {"ref": "typography.families.mono"},
                "size": {"ref": "typography.scale.base"},
                "weight": {"ref": "typography.weights.normal"}
            },
            "section_heading": {
                "family": {"ref": "typography.families.display"},
                "size": {"ref": "typography.scale.md"},
                "weight": {"ref": "typography.weights.semibold"}
            },
            "panel_title": {
                "family": {"ref": "typography.families.display"},
                "size": {"ref": "typography.scale.xl"},
                "weight": {"ref": "typography.weights.bold"}
            },
            "icon": {
                "family": {"ref": "typography.families.icon"},
                "size": {"ref": "typography.scale.icon"},
                "weight": {"ref": "typography.weights.normal"}
            },
            "icon_lg": {
                "family": {"ref": "typography.families.icon"},
                "size": {"ref": "typography.scale.icon-lg"},
                "weight": {"ref": "typography.weights.normal"}
            }
        }
    },
    "spacing": {
        "0": 0,
        "xs": 4,
        "sm": 6,
        "md": 10,
        "lg": 16,
        "xl": 24
    },
    "borders": {
        "radius": {
            "sm": 4,
            "md": 6,
            "lg": 8,
            "full": 9999
        }
    },
    "components": {
        "numeric_display": {
            "bg": ["colors.bg.input"],
            "border": ["colors.border.default"],
            "text-value": ["colors.text.primary"],
            "text-unit": ["colors.text.secondary"],
            "font-value": {"ref": "typography.presets.numeric-value"},
            "font-unit": {"ref": "typography.presets.numeric-unit"}
        },
        "numeric_input": {
            "bg": ["colors.bg.input"],
            "border": ["colors.border.default"],
            "border-focus": ["colors.border.focus"],
            "text": ["colors.text.primary"],
            "placeholder": ["colors.text.muted"],
            "font": {"ref": "typography.presets.body"}
        },
        "color_picker": {
            "bg": ["colors.bg.overlay"],
            "border": ["colors.border.default"],
            "swatch-border": ["colors.border.subtle"],
            "overlay-fg": ["palette.overlay-medium"],
            "radius": {"ref": "borders.radius.md"}
        },
        "panel": {
            "bg": ["colors.bg.page"],
            "header-bg": ["colors.bg.panel"],
            "header-border": ["colors.border.default"],
            "padding": {"ref": "spacing.lg"},
            "section-gap": {"ref": "spacing.lg"}
        },
        "slider": {
            "height": 18,
            "track": {
                "color": ["colors.bg.track"],
                "height": 4,
                "radius": {"ref": "borders.radius.sm"}
            },
            "fill": {
                "color": ["colors.primary"],
                "radius": {"ref": "borders.radius.sm"}
            }
        },
        "toggle": {
            "bg": ["colors.bg.input"],
            "border": ["colors.border.subtle"],
            "radius": {"ref": "borders.radius.md"},
            "option": {
                "text": ["colors.text.secondary"],
                "font": {"ref": "typography.presets.body-strong"},
                "icon_gap": {"ref": "spacing.sm"}
            },
            "active": {
                "bg": ["colors.state.active"],
                "text": ["colors.text.on-accent"],
                "font": {"ref": "typography.presets.body-strong"}
            }
        },
        "dropdown": {
            "height": 32,
            "bg": ["colors.bg.input"],
            "border": ["colors.border.default"],
            "border-focus": ["colors.border.focus"],
            "radius": {"ref": "borders.radius.md"},
            "text": ["colors.text.primary"],
            "text-muted": ["colors.text.muted"],
            "font": {"ref": "typography.presets.body-strong"},
            "popup": {
                "bg": ["colors.bg.inner"],
                "hover": ["colors.bg.hover"]
            }
        },
        "button": {
            "height": 36,
            "radius": {"ref": "borders.radius.md"},
            "font": {"ref": "typography.presets.body-strong"},
            "icon_gap": {"ref": "spacing.md"},
            "primary": {
                "bg": ["colors.primary"],
                "text": ["colors.text.on-accent"],
                "hover": ["colors.state.hover-overlay"],
                "pressed": ["colors.state.pressed-overlay"]
            },
            "secondary": {
                "bg": ["colors.bg.surface"],
                "text": ["colors.text.primary"],
                "border": ["colors.border.default"],
                "hover": ["colors.state.hover-overlay"]
            },
            "ghost": {
                "bg": ["palette.transparent"],
                "text": ["colors.text.primary"],
                "hover": ["colors.state.ghost-overlay"],
                "border": ["palette.transparent"],
                "radius": {"ref": "borders.radius.md"}
            },
            "danger": {
                "bg": ["colors.state.danger"],
                "text": ["colors.text.on-danger"],
                "hover-bg": ["colors.state.danger-hover"],
                "pressed-bg": ["colors.state.danger-pressed"]
            },
            "close": {"ref": "components.button.ghost"}
        },
        "preset_card": {
            "bg": ["colors.bg.surface"],
            "border": ["colors.border.default"],
            "accent": ["colors.primary"]
        },
        "badge": {
            "bg": ["colors.warning"],
            "text": ["colors.text.on-accent"]
        }
    }
}

class ThemeValidatorError(Exception):
    """Base exception for theme validator errors."""
    pass


# Top-level categories we care about (Mastering Schema)
CATEGORIES = ['palette', 'colors', 'glyphs', 'text', 'spacing', 'borders', 'components']


def collect_tokens(data: dict, prefix: str = '') -> Set[str]:
    """Recursively collect token paths from YAML data.

    Only leaf tokens (actual defined tokens) are collected; container
    namespaces (dicts that group tokens) are not considered tokens themselves.

    A dict is considered a leaf if all its keys are known attribute keys
    (e.g., 'ref', 'family', 'size', 'weight'). Otherwise it's a container.
    """
    tokens = set()

    if not isinstance(data, dict):
        return tokens

    # Keys that indicate a dict is a leaf value (not a container)
    LEAF_VALUE_KEYS = {
        'ref', 'family', 'size', 'weight', 'fallback', 'transform', 'value',
        'typeface', 'font', 'color', 'bg', 'radius', 'width', 'height'
    }

    for key, value in data.items():
        current_path = f"{prefix}.{key}" if prefix else key

        # Determine if this key's value is a container dict
        is_container = False
        if isinstance(value, dict):
            if value:
                # If all keys are leaf-value keys, it's a leaf; otherwise container
                all_leaf = all(k in LEAF_VALUE_KEYS for k in value.keys())
                is_container = not all_leaf
            else:
                # Empty dict, treat as container (unlikely)
                is_container = False
        # Non-dict values are leaves; containers are only dicts with non-leaf keys

        if not is_container:
            tokens.add(current_path)

        if is_container:
            tokens.update(collect_tokens(value, current_path))

    return tokens


def categorize_tokens(all_tokens: Set[str]) -> Dict[str, Set[str]]:
    """Categorize tokens by top-level section.

    Args:
        all_tokens: Set of all token paths

    Returns:
        Dict with keys for each category and 'all'
    """
    result = {cat: set() for cat in CATEGORIES}
    result['all'] = all_tokens.copy()

    for token in all_tokens:
        # Top-level category is first segment before dot
        top_level = token.split('.')[0]
        if top_level in result:
            result[top_level].add(token)

    return result




def _is_default_dark_theme(yaml_path: str) -> bool:
    """Check if the given path points to the default dark theme."""
    path = Path(yaml_path).resolve()
    default_path = (Path(__file__).parent.parent.parent / "SpinRender" / "resources" / "themes" / "dark.yaml").resolve()
    return path == default_path

def parse_yaml(yaml_path: str) -> dict:
    """Parse theme YAML and return categorized token sets.

    Args:
        yaml_path: Path to the YAML theme file

    Returns:
        Dictionary with categorized token sets:
        {
            'palette': set([...]),
            'colors': set([...]),
            'typography': set([...]),
            'spacing': set([...]),
            'borders': set([...]),
            'components': set([...]),
            'all': set([...])
        }

    Raises:
        FileNotFoundError: If YAML file doesn't exist
        yaml.YAMLError: If YAML parsing fails
    """
    path = Path(yaml_path)

    if not path.exists():
        raise FileNotFoundError(f"Theme YAML not found: {yaml_path}")

    # Check if PyYAML is available
    if not _YAML_AVAILABLE:
        # If this is the default dark theme, we can use built-in fallback data
        if _is_default_dark_theme(yaml_path):
            import sys
            print("WARNING: PyYAML is not installed. Using built-in fallback data for default dark theme.", file=sys.stderr)
            print("         Install PyYAML for custom theme validation: pip install pyyaml", file=sys.stderr)
            # Use embedded fallback data (same structure as dark.yaml)
            data = _FALLBACK_DARK_THEME
        else:
            # Custom theme requires PyYAML
            error_msg = (
                f"ERROR: PyYAML is required to validate custom theme: {yaml_path}\n"
                "Install it with: pip install pyyaml\n"
                "Or if using KiCad Python: /path/to/kicad/python -m pip install pyyaml"
            )
            import sys
            print(error_msg, file=sys.stderr)
            raise ThemeValidatorError(error_msg)
    else:
        # Normal case: PyYAML is available
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

    if data is None:
        # Empty YAML file
        return {cat: set() for cat in CATEGORIES + ['all']}

    # Ensure data is a dict
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a dictionary, got {type(data).__name__}")

    # Collect all tokens recursively
    all_tokens = collect_tokens(data)

    # Categorize by top-level section
    categorized = categorize_tokens(all_tokens)

    return categorized


# Enable command-line testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = parse_yaml(sys.argv[1])
        print("Token counts per category:")
        for category in CATEGORIES + ['all']:
            print(f"  {category}: {len(result[category])}")
    else:
        print("Usage: python yaml_parser.py <path-to-theme.yaml>")
