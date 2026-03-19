#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""Unit tests for StatusBar component (V2 theme)."""
import pytest
from unittest.mock import MagicMock, patch

from SpinRender.core.theme import Theme
_theme = Theme.current()

from SpinRender.ui.status_bar import StatusBar
import wx


class TestStatusBar:
    """Test suite for StatusBar state management."""

    @pytest.fixture
    def parent(self):
        return MagicMock()

    @pytest.fixture
    def status_bar(self, parent):
        sb = StatusBar(parent)
        return sb

    def test_status_bar_creation(self, status_bar):
        assert status_bar is not None
        assert status_bar._msg == "READY"  # Locale default
        assert status_bar._prog == 0.0
        assert status_bar._fg_override is None
        assert status_bar._bar_color_override is None

    def test_set_status_updates_message(self, status_bar):
        status_bar.set_status("TESTING")
        assert status_bar._msg == "TESTING"

    def test_set_status_updates_color(self, status_bar):
        text_color = _theme.color("components.status.default.label.color")
        status_bar.set_status("TEST", fg_color=text_color)
        assert status_bar._fg_override.Red() == text_color.Red()
        assert status_bar._fg_override.Green() == text_color.Green()
        assert status_bar._fg_override.Blue() == text_color.Blue()

    def test_set_status_updates_progress(self, status_bar):
        status_bar.set_status("50%", progress=0.5)
        assert status_bar._prog == 0.5
        status_bar.set_status("100%", progress=1.0)
        assert status_bar._prog == 1.0

    def test_set_status_updates_bar_color(self, status_bar):
        progress_color = _theme.color("components.status.progress.bg")
        status_bar.set_status("COMPLETE", bar_color=progress_color)
        assert status_bar._bar_color_override.Red() == progress_color.Red()
        assert status_bar._bar_color_override.Green() == progress_color.Green()
        assert status_bar._bar_color_override.Blue() == progress_color.Blue()

    def test_reset_clears_to_ready(self, status_bar):
        status_bar._msg = "WORKING"
        status_bar._prog = 0.5
        status_bar._fg_override = "custom_color"
        status_bar._bar_color_override = "custom_bar"

        status_bar.reset()
        assert status_bar._msg == "READY"
        assert status_bar._prog == 0.0
        # reset() clears overrides by calling set_status without color arguments
        assert status_bar._fg_override is None
        assert status_bar._bar_color_override is None

    def test_set_error_sets_error_state(self, status_bar):
        error_color = _theme.color("components.status.error.label.color")
        status_bar.set_error("CONNECTION FAILED")
        assert "ERROR" in status_bar._msg or "FAILED" in status_bar._msg
        assert status_bar._fg_override.Red() == error_color.Red()
        assert status_bar._fg_override.Green() == error_color.Green()
        assert status_bar._fg_override.Blue() == error_color.Blue()
        assert status_bar._bar_color_override.Red() == error_color.Red()
        assert status_bar._bar_color_override.Green() == error_color.Green()
        assert status_bar._bar_color_override.Blue() == error_color.Blue()
        assert status_bar._prog == 0.0

    def test_set_complete_sets_success_state(self, status_bar):
        text_color = _theme.color("components.status.complete.label.color")
        status_bar.set_complete()
        assert status_bar._prog == 1.0
        assert "COMPLETE" in status_bar._msg or "COMPLETE" in status_bar._msg
        assert status_bar._fg_override.Red() == text_color.Red()
        assert status_bar._fg_override.Green() == text_color.Green()
        assert status_bar._fg_override.Blue() == text_color.Blue()
        assert status_bar._bar_color_override.Red() == text_color.Red()
        assert status_bar._bar_color_override.Green() == text_color.Green()
        assert status_bar._bar_color_override.Blue() == text_color.Blue()

    def test_refresh_called_on_state_change(self, status_bar):
        with patch.object(status_bar, 'Refresh') as mock_refresh:
            status_bar.set_status("NEW STATE")
            mock_refresh.assert_called_once()

    def test_progress_values(self, status_bar):
        status_bar.set_status("75%", progress=0.75)
        assert status_bar._prog == 0.75
        status_bar.set_status("25%", progress=0.25)
        assert status_bar._prog == 0.25

    def test_multiple_updates(self, status_bar):
        status_bar.set_status("Step 1", progress=0.25)
        assert status_bar._msg == "Step 1"
        status_bar.set_status("Step 2", progress=0.5)
        assert status_bar._msg == "Step 2"
        assert status_bar._prog == 0.5
        status_bar.reset()
        assert status_bar._msg == "READY"
        assert status_bar._prog == 0.0

    def test_initial_paint_handler_bound(self, status_bar):
        assert hasattr(status_bar, '_on_paint')

    def test_status_bar_is_panel(self, status_bar):
        assert isinstance(status_bar, wx.Panel)

    def test_set_status_with_all_parameters(self, status_bar):
        yellow = _theme.color("colors.yellow")
        orange = _theme.color("colors.orange")
        msg = "CUSTOM STATE"
        fg = yellow
        prog = 0.33
        bar = orange

        status_bar.set_status(msg, fg_color=fg, progress=prog, bar_color=bar)

        assert status_bar._msg == msg
        assert status_bar._fg_override.Red() == fg.Red()
        assert status_bar._fg_override.Green() == fg.Green()
        assert status_bar._fg_override.Blue() == fg.Blue()
        assert status_bar._prog == prog
        assert status_bar._bar_color_override.Red() == bar.Red()
        assert status_bar._bar_color_override.Green() == bar.Green()
        assert status_bar._bar_color_override.Blue() == bar.Blue()
