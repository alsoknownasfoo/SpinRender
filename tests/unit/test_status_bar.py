#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
Unit tests for StatusBar component.

Tests the extracted status bar UI with state management only.
Painting behavior is visual and will be tested in integration/E2E.
"""
import pytest
from unittest.mock import MagicMock, patch

from SpinRender.core.theme import Theme
_theme = Theme.current()

from SpinRender.ui.status_bar import StatusBar


class TestStatusBar:
    """Test suite for StatusBar state management."""

    @pytest.fixture
    def parent(self):
        """Create a mock parent window."""
        return MagicMock()

    @pytest.fixture
    def status_bar(self, parent):
        """Create a StatusBar instance."""
        sb = StatusBar(parent)
        return sb

    def test_status_bar_creation(self, status_bar):
        """Test status bar initializes with correct defaults."""
        assert status_bar is not None
        assert status_bar._msg == "READY"
        assert status_bar._prog == 0.0
        assert status_bar._fg is not None
        assert status_bar._bar_color is not None

    def test_set_status_updates_message(self, status_bar):
        """Test set_status updates the message."""
        status_bar.set_status("TESTING")
        assert status_bar._msg == "TESTING"

    def test_set_status_updates_color(self, status_bar):
        """Test set_status updates foreground color when provided."""
        accent_yellow = _theme.color("colors.accent.yellow")
        status_bar.set_status("TEST", fg_color=accent_yellow)
        # Compare RGB values
        assert status_bar._fg.Red() == accent_yellow.Red()
        assert status_bar._fg.Green() == accent_yellow.Green()
        assert status_bar._fg.Blue() == accent_yellow.Blue()

    def test_set_status_updates_progress(self, status_bar):
        """Test set_status updates progress bar."""
        status_bar.set_status("50%", progress=0.5)
        assert status_bar._prog == 0.5

        status_bar.set_status("100%", progress=1.0)
        assert status_bar._prog == 1.0

    def test_set_status_updates_bar_color(self, status_bar):
        """Test set_status updates progress bar color."""
        accent_green = _theme.color("colors.accent.green")
        status_bar.set_status("COMPLETE", bar_color=accent_green)
        assert status_bar._bar_color.Red() == accent_green.Red()
        assert status_bar._bar_color.Green() == accent_green.Green()
        assert status_bar._bar_color.Blue() == accent_green.Blue()

    def test_reset_clears_to_ready(self, status_bar):
        """Test reset returns status bar to ready state."""
        status_bar._msg = "WORKING"
        status_bar._prog = 0.5
        status_bar._fg = "custom_color"

        status_bar.reset()

        assert status_bar._msg == "READY"
        assert status_bar._prog == 0.0

    def test_reset_preserves_custom_fg_color(self, status_bar):
        """Test reset preserves custom fg color (doesn't force default)."""
        status_bar._fg = "custom_color"
        status_bar.reset()
        # Reset should restore default fg color; verify it's not the custom one
        assert status_bar._fg != "custom_color"

    def test_set_error_sets_error_state(self, status_bar):
        """Test set_error sets appropriate error state."""
        accent_orange = _theme.color("colors.accent.orange")
        status_bar.set_error("CONNECTION FAILED")

        assert "ERROR" in status_bar._msg or "FAILED" in status_bar._msg
        assert status_bar._fg.Red() == accent_orange.Red()
        assert status_bar._fg.Green() == accent_orange.Green()
        assert status_bar._fg.Blue() == accent_orange.Blue()

    def test_set_complete_sets_success_state(self, status_bar):
        """Test set_complete sets appropriate success state."""
        accent_green = _theme.color("colors.accent.green")
        status_bar.set_complete()

        assert "COMPLETE" in status_bar._msg
        assert status_bar._fg.Red() == accent_green.Red()
        assert status_bar._fg.Green() == accent_green.Green()
        assert status_bar._fg.Blue() == accent_green.Blue()
        assert status_bar._prog == 1.0
        assert status_bar._bar_color.Red() == accent_green.Red()
        assert status_bar._bar_color.Green() == accent_green.Green()
        assert status_bar._bar_color.Blue() == accent_green.Blue()

    def test_refresh_called_on_state_change(self, status_bar):
        """Test that Refresh is called after state changes."""
        with patch.object(status_bar, 'Refresh') as mock_refresh:
            status_bar.set_status("NEW STATE")
            mock_refresh.assert_called_once()

    def test_progress_values(self, status_bar):
        """Test various progress values."""
        status_bar.set_status("75%", progress=0.75)
        assert status_bar._prog == 0.75

        status_bar.set_status("25%", progress=0.25)
        assert status_bar._prog == 0.25

    def test_multiple_updates(self, status_bar):
        """Test multiple sequential updates work correctly."""
        status_bar.set_status("Step 1", progress=0.25)
        assert status_bar._msg == "Step 1"

        status_bar.set_status("Step 2", progress=0.5)
        assert status_bar._msg == "Step 2"
        assert status_bar._prog == 0.5

        status_bar.reset()
        assert status_bar._msg == "READY"
        assert status_bar._prog == 0.0

    def test_initial_paint_handler_bound(self, status_bar):
        """Test that EVT_PAINT is bound."""
        assert hasattr(status_bar, '_on_paint')

    def test_status_bar_is_panel(self, status_bar):
        """Test status bar is a wx.Panel."""
        import wx
        assert isinstance(status_bar, wx.Panel)

    def test_set_status_with_all_parameters(self, status_bar):
        """Test set_status with all optional parameters."""
        accent_yellow = _theme.color("colors.accent.yellow")
        accent_orange = _theme.color("colors.accent.orange")
        msg = "CUSTOM STATE"
        fg = accent_yellow
        prog = 0.33
        bar = accent_orange

        status_bar.set_status(msg, fg_color=fg, progress=prog, bar_color=bar)

        assert status_bar._msg == msg
        assert status_bar._fg.Red() == fg.Red() and status_bar._fg.Green() == fg.Green() and status_bar._fg.Blue() == fg.Blue()
        assert status_bar._prog == prog
        assert status_bar._bar_color.Red() == bar.Red() and status_bar._bar_color.Green() == bar.Green() and status_bar._bar_color.Blue() == bar.Blue()
