#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""Unit tests for UI validation module."""
import pytest
import sys

# wx is already mocked by conftest
import wx

# Mock wx.Colour with a proper test double
class ColourMock:
    def __init__(self, r=0, g=0, b=0, a=None):
        self._r = r
        self._g = g
        self._b = b
        self._a = a if a is not None else 255  # Default opaque

    def Red(self):
        return self._r

    def Green(self):
        return self._g

    def Blue(self):
        return self._b

    def Alpha(self):
        return self._a

    def __eq__(self, other):
        if isinstance(other, ColourMock):
            return (self._r, self._g, self._b, self._a) == (other._r, other._g, other._b, other._a)
        return False

# Replace wx.Colour globally in this test module
original_Colour = wx.Colour
wx.Colour = ColourMock

from SpinRender.ui.validation import validate_all_tokens, ContrastChecker, validate_theme_schema
from SpinRender.ui.helpers import VALID_BG_TOKENS, VALID_TEXT_TOKENS, ALL_VALID_TOKENS


class TestValidateAllTokens:
    """Test validate_all_tokens function."""

    def test_passes_with_all_tokens_present(self, monkeypatch):
        """Should return empty list when all required tokens exist and are valid."""
        mock_theme = {}
        for token in ALL_VALID_TOKENS:
            mock_theme[token] = ColourMock(100, 100, 100)

        class MockTheme:
            def __getattr__(self, name):
                if name in mock_theme:
                    return mock_theme[name]
                raise AttributeError(f"no attribute {name}")

        monkeypatch.setattr('SpinRender.ui.validation.theme', MockTheme())
        errors = validate_all_tokens()
        assert errors == []

    def test_detects_missing_token(self, monkeypatch):
        """Should report missing token."""
        mock_theme = {
            'BG_PAGE': ColourMock(18, 18, 18),
            'BG_PANEL': ColourMock(26, 26, 26),
        }

        class MockTheme:
            def __getattr__(self, name):
                if name in mock_theme:
                    return mock_theme[name]
                raise AttributeError(f"no attribute {name}")

        monkeypatch.setattr('SpinRender.ui.validation.theme', MockTheme())
        errors = validate_all_tokens()
        assert len(errors) > 0
        assert any("Missing required theme token" in e for e in errors)

    def test_detects_non_wx_colour_type(self, monkeypatch):
        """Should flag token that is not a wx.Colour."""
        mock_theme = {token: ColourMock(100, 100, 100) for token in ALL_VALID_TOKENS}
        mock_theme['BG_PAGE'] = "not a colour"

        class MockTheme:
            def __getattr__(self, name):
                return mock_theme.get(name, ColourMock())

        monkeypatch.setattr('SpinRender.ui.validation.theme', MockTheme())
        errors = validate_all_tokens()
        assert any("is not a wx.Colour" in e for e in errors)

    def test_detects_rgb_out_of_range(self, monkeypatch):
        """Should flag RGB values outside 0-255."""
        mock_theme = {token: ColourMock(100, 100, 100) for token in ALL_VALID_TOKENS}
        mock_theme['BG_PAGE'] = ColourMock(300, -10, 128)

        class MockTheme:
            def __getattr__(self, name):
                return mock_theme.get(name, ColourMock())

        monkeypatch.setattr('SpinRender.ui.validation.theme', MockTheme())
        errors = validate_all_tokens()
        assert any("outside 0-255 range" in e for e in errors)

    def test_detects_alpha_out_of_range(self, monkeypatch):
        """Should flag alpha values outside 0-255."""
        mock_theme = {token: ColourMock(100, 100, 100, 200) for token in ALL_VALID_TOKENS}
        mock_theme['BG_PAGE'] = ColourMock(100, 100, 100, 300)

        class MockTheme:
            def __getattr__(self, name):
                return mock_theme.get(name, ColourMock(100, 100, 100, 200))

        monkeypatch.setattr('SpinRender.ui.validation.theme', MockTheme())
        errors = validate_all_tokens()
        assert any("alpha value 300 outside 0-255 range" in e for e in errors)

    def test_valid_alpha_is_accepted(self, monkeypatch):
        """Should accept alpha in range 0-255."""
        mock_theme = {token: ColourMock(100, 100, 100, 128) for token in ALL_VALID_TOKENS}

        class MockTheme:
            def __getattr__(self, name):
                return mock_theme.get(name, ColourMock(100, 100, 100, 128))

        monkeypatch.setattr('SpinRender.ui.validation.theme', MockTheme())
        errors = validate_all_tokens()
        assert errors == []


class TestContrastChecker:
    """Test ContrastChecker class."""

    def test_relative_luminance_black(self):
        """Black (0,0,0) luminance should be 0.0."""
        black = ColourMock(0, 0, 0)
        lum = ContrastChecker.relative_luminance(black)
        assert lum == 0.0

    def test_relative_luminance_white(self):
        """White (255,255,255) luminance should be 1.0."""
        white = ColourMock(255, 255, 255)
        lum = ContrastChecker.relative_luminance(white)
        assert abs(lum - 1.0) < 0.001

    def test_contrast_ratio_black_on_white(self):
        """Black on white should be 21:1."""
        black = ColourMock(0, 0, 0)
        white = ColourMock(255, 255, 255)
        ratio = ContrastChecker.contrast_ratio(black, white)
        assert abs(ratio - 21.0) < 0.1  # Allow floating point tolerance

    def test_contrast_ratio_white_on_black(self):
        """White on black should also be 21:1 (order independent)."""
        black = ColourMock(0, 0, 0)
        white = ColourMock(255, 255, 255)
        ratio = ContrastChecker.contrast_ratio(white, black)
        assert abs(ratio - 21.0) < 0.1

    def test_contrast_ratio_grey_on_white(self):
        """Mid-grey on white has lower contrast."""
        grey = ColourMock(128, 128, 128)
        white = ColourMock(255, 255, 255)
        ratio = ContrastChecker.contrast_ratio(grey, white)
        # Expected around 3.95
        assert 3.8 < ratio < 4.2

    def test_meets_aa_normal_text_threshold(self):
        """4.5:1 should pass, 4.4:1 should fail for normal text."""
        assert ContrastChecker.meets_aa(4.5, large_text=False) is True
        assert ContrastChecker.meets_aa(4.49, large_text=False) is False

    def test_meets_aa_large_text_threshold(self):
        """3.0:1 should pass, 2.9:1 should fail for large text."""
        assert ContrastChecker.meets_aa(3.0, large_text=True) is True
        assert ContrastChecker.meets_aa(2.99, large_text=True) is False

    def test_check_contrast_returns_tuple(self):
        """Should return (passes, ratio, message) tuple."""
        fg = ColourMock(255, 255, 255)
        bg = ColourMock(0, 0, 0)
        passes, ratio, msg = ContrastChecker.check_contrast(fg, bg)
        assert passes is True
        assert ratio > 20.0
        assert "PASS" in msg
        assert "contrast ratio" in msg

    def test_check_contrast_fails_with_low_contrast(self):
        """Should indicate failure for insufficient contrast."""
        fg = ColourMock(150, 150, 150)
        bg = ColourMock(100, 100, 100)
        passes, ratio, msg = ContrastChecker.check_contrast(fg, bg)
        assert passes is False
        assert "FAIL" in msg

    def test_check_contrast_large_text_flag(self):
        """Large text uses 3:1 threshold, normal uses 4.5:1."""
        fg = ColourMock(180, 180, 180)
        bg = ColourMock(80, 80, 80)
        ratio = ContrastChecker.contrast_ratio(fg, bg)
        assert 3.0 < ratio < 4.5  # Should be borderline

        passes_normal, _, _ = ContrastChecker.check_contrast(fg, bg, large_text=False)
        passes_large, _, _ = ContrastChecker.check_contrast(fg, bg, large_text=True)

        # For a ratio between 3 and 4.5:
        # - large_text=True should pass (≥3.0)
        # - large_text=False should fail (<4.5)
        assert passes_large is True
        assert passes_normal is False


class TestValidateThemeSchema:
    """Test YAML theme schema validation."""

    def test_valid_minimal_schema(self):
        """Should accept a minimal valid theme."""
        valid = {
            'meta': {'name': 'Test', 'version': '1.0'},
            'palette': {
                'neutral-1': '#0A0A0A',
                'neutral-3': '#121212',
            },
            'colors': {
                'bg': {
                    'page': {'ref': 'palette.neutral-3'}
                }
            },
            'typography': {
                'families': {'mono': 'JetBrains Mono'},
                'scale': {'base': 11},
                'weights': {'normal': 400},
                'presets': {
                    'body': {
                        'family': {'ref': 'typography.families.mono'},
                        'size': {'ref': 'typography.scale.base'},
                        'weight': 400
                    }
                }
            },
            'spacing': {'sm': 6},
            'borders': {'radius': {'sm': 2}}
        }
        errors = validate_theme_schema(valid)
        assert errors == []

    def test_missing_required_key(self):
        """Should report missing top-level key."""
        incomplete = {
            'palette': {},
            'colors': {},
            'typography': {},
            'spacing': {},
            'borders': {}
            # Missing 'meta'
        }
        errors = validate_theme_schema(incomplete)
        assert any("Missing required top-level key: meta" in e for e in errors)

    def test_invalid_palette_format(self):
        """Palette entries must be strings (hex or rgba)."""
        bad = {
            'meta': {'name': 'Test', 'version': '1.0'},
            'palette': {'neutral-1': 12345},  # Should be string
            'colors': {},
            'typography': {
                'families': {},
                'scale': {},
                'weights': {},
                'presets': {}
            },
            'spacing': {},
            'borders': {'radius': {}}
        }
        errors = validate_theme_schema(bad)
        assert any("must be a string" in e for e in errors)

    def test_invalid_ref_structure(self):
        """Semantic colors must use {ref: 'palette.xxx'} structure."""
        bad = {
            'meta': {'name': 'Test', 'version': '1.0'},
            'palette': {'neutral-1': '#0A0A0A'},
            'colors': {
                'bg': {
                    'page': '#121212'  # Should be {'ref': 'palette.neutral-3'}
                }
            },
            'typography': {
                'families': {},
                'scale': {},
                'weights': {},
                'presets': {}
            },
            'spacing': {},
            'borders': {'radius': {}}
        }
        errors = validate_theme_schema(bad)
        # Should detect that a plain string is not a {ref: ...} structure
        assert any("expected {ref:" in e for e in errors)

    def test_missing_typography_preset_fields(self):
        """Typography presets require family, size, weight."""
        incomplete = {
            'meta': {'name': 'Test', 'version': '1.0'},
            'palette': {},
            'colors': {},
            'typography': {
                'families': {'mono': 'JetBrains Mono'},
                'scale': {'base': 11},
                'weights': {'normal': 400},
                'presets': {
                    'body': {
                        'family': {'ref': 'typography.families.mono'}
                        # Missing 'size' and 'weight'
                    }
                }
            },
            'spacing': {},
            'borders': {'radius': {}}
        }
        errors = validate_theme_schema(incomplete)
        assert any("missing 'size'" in e for e in errors)
        assert any("missing 'weight'" in e for e in errors)

    def test_preset_list_structure(self):
        """Preset lists in components should be validated as list of refs."""
        # This is a more complex schema check - for now just ensure no crash
        valid = {
            'meta': {'name': 'Test', 'version': '1.0'},
            'palette': {},
            'colors': {},
            'typography': {
                'families': {},
                'scale': {},
                'weights': {},
                'presets': {}
            },
            'spacing': {},
            'borders': {'radius': {}},
            'components': {
                'preset_card': {
                    'palette': [{'ref': 'colors.preset.red'}]
                }
            }
        }
        errors = validate_theme_schema(valid)
        # Should be OK
        assert errors == []
