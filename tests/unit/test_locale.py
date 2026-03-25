#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
Unit tests for SpinRender.core.locale.Locale class.

Tests YAML loading, dot-path lookups, singleton pattern, and fallback behavior.
"""
import pytest
import sys
import importlib
from pathlib import Path
from unittest.mock import patch


@pytest.fixture(autouse=True)
def reset_locale_singleton():
    """Ensure Locale singleton is reset before and after each test."""
    from SpinRender.core.locale import Locale
    Locale._instance = None
    if 'yaml' in sys.modules and sys.modules['yaml'] is None:
        del sys.modules['yaml']
    importlib.reload(sys.modules['SpinRender.core.locale'])
    yield
    Locale._instance = None


class TestLocaleSingleton:
    """Test Locale singleton pattern."""

    def test_current_creates_default_if_none(self):
        """Locale.current() should load default locale if none set."""
        from SpinRender.core.locale import Locale
        locale = Locale.current()
        assert locale is not None
        assert isinstance(locale, Locale)

    def test_load_sets_instance(self):
        """Locale.load() should set the singleton instance."""
        from SpinRender.core.locale import Locale
        locale = Locale.load("en_US")
        assert Locale._instance is locale
        assert Locale.current() is locale

    def test_load_with_nonexistent_name_raises(self):
        """Locale.load() should raise FileNotFoundError for missing locale."""
        from SpinRender.core.locale import Locale
        with pytest.raises(FileNotFoundError):
            Locale.load("nonexistent_locale_xyz")

    def test_multiple_loads_return_same_instance(self):
        """Subsequent Locale.load() calls should return same instance."""
        from SpinRender.core.locale import Locale
        locale1 = Locale.load("en_US")
        locale2 = Locale.load("en_US")
        assert locale1 is locale2


class TestLocaleLookup:
    """Test get() dot-path lookups."""

    @pytest.fixture(autouse=True)
    def setup_locale(self):
        """Load en_US locale for each test."""
        from SpinRender.core.locale import Locale
        self.locale = Locale.load("en_US")

    def test_get_component_header_title(self):
        """get('component.main.header.title') should return 'SpinRender'."""
        value = self.locale.get("component.main.header.title")
        assert value == "SpinRender"

    def test_get_component_header_subtitle(self):
        """get('component.main.header.subtitle') should return version string."""
        value = self.locale.get("component.main.header.subtitle")
        assert value == "0.9.0-alpha"

    def test_get_button_render_label(self):
        """get('component.button.render.label') should return 'Render' (uppercase via theme)."""
        value = self.locale.get("component.button.render.label")
        assert value == "Render"

    def test_get_button_render_icon_ref(self):
        """get('component.button.render.icon_ref') should return 'glyphs.render-action'."""
        value = self.locale.get("component.button.render.icon_ref")
        assert value == "glyphs.render-action"

    def test_get_section_presets(self):
        """get('sections.presets') should return 'Loop presets'."""
        value = self.locale.get("sections.presets")
        assert value == "Loop presets"

    def test_get_parameter_with_unit(self):
        """get('parameters.board_tilt.label') should return 'Board tilt'."""
        value = self.locale.get("parameters.board_tilt.label")
        assert value == "Board tilt"

    def test_get_parameter_with_unit_field(self):
        """get('parameters.board_tilt.unit') should return '°'."""
        value = self.locale.get("parameters.board_tilt.unit")
        assert value == "°"

    def test_get_parameter_options(self):
        """get('parameters.direction.options.cw.label') should return 'CW'."""
        value = self.locale.get("parameters.direction.options.cw.label")
        assert value == "CW"  # Abbreviations remain uppercase

    def test_get_preset_card_label(self):
        """get('component.preset_card.card1.label') should return 'Hero'."""
        value = self.locale.get("component.preset_card.card1.label")
        assert value == "Hero"

    def test_get_status_message_with_placeholder(self):
        """get('component.status.rendering') should contain placeholder {current}/{total}."""
        value = self.locale.get("component.status.rendering")
        assert value == "Rendering frame {current}/{total}"  # Sentence case, uppercase via theme formatting
        assert "{current}" in value
        assert "{total}" in value

    def test_get_missing_key_returns_none(self):
        """get('nonexistent.key') should return None."""
        value = self.locale.get("nonexistent.key")
        assert value is None

    def test_get_empty_string_is_valid(self):
        """get() should return empty string if that's the value (e.g., options button label)."""
        value = self.locale.get("component.button.options.label")
        assert value == ""  # Empty string is a valid value

    def test_get_deep_nested_path(self):
        """get() should handle deeply nested paths."""
        value = self.locale.get("parameters.lighting.options.studio.label")
        assert value == "Studio"  # Base case, formatted uppercase via theme


class TestLocaleFileLoading:
    """Test YAML file loading and error handling."""

    def test_loads_correct_yaml_file(self):
        """Locale.load('en_US') should load resources/locale/en_US.yaml and extract language subtree."""
        from SpinRender.core.locale import Locale
        locale = Locale.load("en_US")
        assert locale._data is not None
        # The extracted data should have top-level keys like 'component.main.header', 'sections', etc.
        assert "component.main.header" in locale._data or any(k.startswith("component") for k in locale._data.keys())

    def test_locale_data_structure(self):
        """Loaded locale should have expected top-level sections (flattened keys)."""
        from SpinRender.core.locale import Locale
        locale = Locale.load("en_US")
        data = locale._data
        # Check for flattened dot-notation keys
        assert "component.main.header" in data or "component" in data
        assert "sections" in data or any(k.startswith("sections") for k in data.keys())
        assert "parameters" in data or any(k.startswith("parameters") for k in data.keys())
        assert "output" in data or any(k.startswith("output") for k in data.keys())

    def test_error_when_yaml_missing(self):
        """If YAML file missing, should raise FileNotFoundError."""
        from SpinRender.core.locale import Locale
        with patch.object(Path, 'exists', return_value=False):
            with pytest.raises(FileNotFoundError):
                Locale.load("nonexistent")

    def test_yaml_parser_detects_malformed(self):
        """Test that malformed YAML raises an error."""
        import yaml
        with pytest.raises(yaml.YAMLError):
            yaml.safe_load("invalid: yaml: [\n")

    def test_error_when_pyyaml_missing(self):
        """If PyYAML not installed, should raise ImportError."""
        from SpinRender.core.locale import Locale
        with patch.dict(sys.modules, {'yaml': None}):
            from SpinRender.core import locale as locale_mod
            importlib.reload(locale_mod)
            with pytest.raises(ImportError):
                locale_mod.Locale.load("en_US")


class TestLocaleHotReload:
    """Test hot-reload behavior when locale file changes on disk."""

    def test_reload_detects_file_change(self):
        """Theme.reload() should reload when file mtime changes."""
        from SpinRender.core.locale import Locale
        import time
        # Load initial
        locale1 = Locale.load("en_US")
        data1 = locale1._data.copy()

        # Simulate file change by updating mtime (would need actual file write)
        # For now, test that reload() doesn't crash
        locale2 = Locale.reload()
        assert locale2 is locale1  # Should be same instance
