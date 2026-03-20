#!/usr/bin/env python3
"""
Test suite for YAML layout structure validation.

These tests verify that the theme dark.yaml has been properly restructured
with a top-level 'layout' node containing 'dialogs' and 'main' sections.

This is Phase 0-1 of the Layout Refactoring TDD plan.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from SpinRender.core.theme import Theme


@pytest.fixture(scope="function", autouse=True)
def reset_theme():
    """Reset theme singleton before each test."""
    Theme._instance = None
    yield
    Theme._instance = None


class TestLayoutYamlStructure:
    """Validate dark.yaml has proper layout node structure."""

    def test_layout_node_exists(self):
        """YAML must have top-level 'layout' section."""
        theme = Theme.current()
        layout = theme._get_raw("layout")
        assert layout is not None, "Missing top-level 'layout' node in dark.yaml"

    def test_layout_has_dialogs(self):
        """layout.dialogs must exist."""
        theme = Theme.current()
        dialogs = theme._get_raw("layout.dialogs")
        assert dialogs is not None, "Missing 'layout.dialogs' section"

    def test_layout_dialogs_has_default(self):
        """layout.dialogs.default must exist."""
        theme = Theme.current()
        default = theme._get_raw("layout.dialogs.default")
        assert default is not None, "Missing 'layout.dialogs.default'"

    def test_layout_dialogs_default_has_shadow(self):
        """layout.dialogs.default.frame.shadow must exist with size and color."""
        theme = Theme.current()
        shadow = theme._get_raw("layout.dialogs.default.frame.shadow")
        assert shadow is not None, "Missing 'layout.dialogs.default.frame.shadow'"
        assert isinstance(shadow, dict), "shadow should be a dict"
        assert "size" in shadow, "shadow must have 'size'"
        assert "color" in shadow, "shadow must have 'color'"

    def test_layout_dialogs_default_has_header(self):
        """layout.dialogs.default.header must exist with height."""
        theme = Theme.current()
        header = theme._get_raw("layout.dialogs.default.header")
        assert header is not None, "Missing 'layout.dialogs.default.header'"
        assert "height" in header, "header must have 'height'"

    def test_layout_dialogs_default_has_body(self):
        """layout.dialogs.default.body must exist with padding."""
        theme = Theme.current()
        body = theme._get_raw("layout.dialogs.default.body")
        assert body is not None, "Missing 'layout.dialogs.default.body'"
        assert "padding" in body, "body must have 'padding'"

    def test_layout_dialogs_default_has_controls(self):
        """layout.dialogs.default.controls must exist."""
        theme = Theme.current()
        controls = theme._get_raw("layout.dialogs.default.controls")
        assert controls is not None, "Missing 'layout.dialogs.default.controls'"

    def test_layout_dialogs_presets_exists(self):
        """layout.dialogs.presets must exist and reference default."""
        theme = Theme.current()
        presets = theme._get_raw("layout.dialogs.presets")
        assert presets is not None, "Missing 'layout.dialogs.presets'"
        # Check it references default
        ref = theme._get_raw("layout.dialogs.presets.ref")
        assert ref == "@layout.dialogs.default", "presets should ref '@layout.dialogs.default'"

    def test_layout_dialogs_options_exists(self):
        """layout.dialogs.options must exist with frame.width."""
        theme = Theme.current()
        options = theme._get_raw("layout.dialogs.options")
        assert options is not None, "Missing 'layout.dialogs.options'"
        width = theme._get_raw("layout.dialogs.options.frame.width")
        assert width is not None, "options must have frame.width"

    def test_layout_dialogs_addpreset_exists(self):
        """layout.dialogs.addpreset must exist."""
        theme = Theme.current()
        addpreset = theme._get_raw("layout.dialogs.addpreset")
        assert addpreset is not None, "Missing 'layout.dialogs.addpreset'"

    def test_layout_has_main(self):
        """layout.main must exist with frame, header, leftpanel, rightpanel."""
        theme = Theme.current()
        main = theme._get_raw("layout.main")
        assert main is not None, "Missing 'layout.main' section"
        # Check key subsections exist
        assert theme._get_raw("layout.main.frame") is not None, "layout.main missing frame"
        assert theme._get_raw("layout.main.header") is not None, "layout.main missing header"
        assert theme._get_raw("layout.main.leftpanel") is not None, "layout.main missing leftpanel"
        assert theme._get_raw("layout.main.rightpanel") is not None, "layout.main missing rightpanel"

    def test_components_list_unchanged(self):
        """components.list.default and components.list.custompresets must still exist."""
        theme = Theme.current()
        assert theme._get_raw("components.list") is not None, "components.list missing"
        assert theme._get_raw("components.list.default") is not None, "components.list.default missing"
        assert theme._get_raw("components.list.custompresets") is not None, "components.list.custompresets missing"

    def test_no_dialogs_in_components(self):
        """components.dialogs should NOT exist after migration."""
        theme = Theme.current()
        components_dialogs = theme._get_raw("components.dialogs")
        assert components_dialogs is None, "components.dialogs should be removed (use layout.dialogs)"

    def test_no_main_in_components(self):
        """components.main should NOT exist after migration."""
        theme = Theme.current()
        components_main = theme._get_raw("components.main")
        assert components_main is None, "components.main should be removed (use layout.main)"
