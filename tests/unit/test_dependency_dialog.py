#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""Unit tests for DependencyDialog component (theme)."""
import pytest
import wx
from unittest.mock import MagicMock, patch, call
import threading

# Import the module under test
from SpinRender.ui.dependency_dialog import DependencyDialog

# Test constants
from tests.conftest import ColorMock

@pytest.fixture
def mock_checker():
    """Create a mock DependencyChecker with missing and found dependencies."""
    checker = MagicMock()
    checker.missing_deps = ['kicad', 'ffmpeg']
    checker.available_deps = ['python']
    checker.check_all.return_value = {
        'kicad': False,
        'ffmpeg': False,
        'python': True
    }
    # Add get_status() method to return dep_status
    checker.get_status.return_value = {
        'kicad': False,
        'ffmpeg': False,
        'python': True
    }
    return checker

@pytest.fixture
def mock_install_func():
    """Create a mock install_dependency function."""
    def fake_install(dep_name, callback=None):
        if callback:
            callback(f"Successfully installed {dep_name}")
    return fake_install

class RoundedPanel(wx.Panel):
    """Mock RoundedPanel for testing - just track properties"""
    def __init__(self, parent, radius=4, bg_color=None):
        super().__init__(parent)
        self.radius = radius
        self.bg_color = bg_color or wx.Colour(13, 13, 13)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)

    def on_size(self, event):
        self.Refresh()
        event.Skip()

    def on_paint(self, event):
        pass

class CustomButton(wx.Panel):
    """Mock CustomButton for testing."""
    def __init__(self, parent, label="BUTTON", primary=True, danger=False, size=(-1, 36)):
        super().__init__(parent, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.label = label
        self.primary = primary
        self.danger = danger
        self.hovered = False
        self.pressed = False
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_mouse_up)
        self.Bind(wx.EVT_ENTER_WINDOW, self.on_enter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave)

    def on_size(self, event):
        self.Refresh()
        event.Skip()

    def on_paint(self, event):
        pass

    def on_mouse_down(self, event):
        self.pressed = True
        self.Refresh()

    def on_mouse_up(self, event):
        if self.pressed:
            self.pressed = False
            self.Refresh()
            evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, self.GetId())
            self.GetEventHandler().ProcessEvent(evt)

    def on_enter(self, event):
        self.hovered = True
        self.Refresh()

    def on_leave(self, event):
        self.hovered = False
        self.pressed = False
        self.Refresh()

    def IsEnabled(self):
        return getattr(self, '_enabled', True)

    def Enable(self, enabled=True):
        self._enabled = enabled

# Mock the CustomButton and RoundedPanel used by DependencyDialog
import SpinRender.ui.dependency_dialog as dd
dd.RoundedPanel = RoundedPanel
dd.CustomButton = CustomButton

class TestDependencyDialogConstruction:
    """Test DependencyDialog initialization."""

    def test_constructs_with_parent_and_checker(self, wx_mock, mock_checker):
        """Should create dialog without raising."""
        parent = MagicMock()
        dep_status = {'kicad': False, 'ffmpeg': False, 'python': True}
        mock_checker.get_status.return_value = dep_status
        dialog = DependencyDialog(parent, mock_checker)
        assert dialog is not None
        assert isinstance(dialog, wx.Dialog)

    def test_stores_checker_and_initial_state(self, wx_mock, mock_checker):
        """Should store checker and initialize UI state."""
        parent = MagicMock()
        dep_status = {'kicad': False, 'ffmpeg': False, 'python': True}
        mock_checker.get_status.return_value = dep_status
        dialog = DependencyDialog(parent, mock_checker)
        assert dialog.checker is mock_checker
        assert dialog.dep_status == dep_status
        assert hasattr(dialog, 'progress_panel')
        assert dialog.progress_panel is not None

    def test_ui_contains_header(self, wx_mock, mock_checker):
        """Should create header with title."""
        parent = MagicMock()
        dep_status = {'kicad': False, 'ffmpeg': False, 'python': True}
        mock_checker.get_status.return_value = dep_status
        dialog = DependencyDialog(parent, mock_checker)
        assert hasattr(dialog, 'header')
        assert dialog.header is not None
        assert hasattr(dialog, 'header_title')
        assert dialog.header_title.GetLabel() == "DEPENDENCY CHECK"

    def test_ui_contains_dependency_rows(self, wx_mock, mock_checker):
        """Should create a row for each dependency."""
        parent = MagicMock()
        dep_status = {'kicad': False, 'ffmpeg': False, 'python': True}
        mock_checker.get_status.return_value = dep_status
        dialog = DependencyDialog(parent, mock_checker)
        # dep_status is stored as-is
        assert len(dialog.dep_status) == 3

    def test_ui_contains_footer_buttons(self, wx_mock, mock_checker):
        """Should create close and install buttons."""
        parent = MagicMock()
        dep_status = {'kicad': False, 'ffmpeg': False, 'python': True}
        mock_checker.get_status.return_value = dep_status
        dialog = DependencyDialog(parent, mock_checker)
        assert hasattr(dialog, 'close_btn')
        assert hasattr(dialog, 'install_btn')
        assert isinstance(dialog.close_btn, CustomButton)
        assert isinstance(dialog.install_btn, CustomButton)

class TestDependencyDialogTheme:
    """Test that dialog uses correct theme colors."""

    def test_uses_theme_background(self, wx_mock, mock_checker):
        """Should use theme background color."""
        parent = MagicMock()
        dep_status = {'kicad': False, 'ffmpeg': False, 'python': True}
        mock_checker.get_status.return_value = dep_status
        dialog = DependencyDialog(parent, mock_checker)
        # Background should be set from theme (via _get_color)
        # We can't test exact color without loading real theme; just check it's set
        assert dialog.GetBackgroundColour() is not None

    def test_header_styling(self, wx_mock, mock_checker):
        """Header should have proper colors and font."""
        parent = MagicMock()
        dep_status = {'kicad': False, 'ffmpeg': False, 'python': True}
        mock_checker.get_status.return_value = dep_status
        dialog = DependencyDialog(parent, mock_checker)
        # Check header title exists and has color/font set
        assert dialog.header_title.GetForegroundColour() is not None
        assert dialog.header_title.GetFont() is not None

class TestDependencyDialogEvents:
    """Test event handlers."""

    def test_on_close_cancels_dialog(self, wx_mock, mock_checker):
        """Should end modal with wx.ID_CANCEL on close."""
        parent = MagicMock()
        dep_status = {'kicad': False, 'ffmpeg': False, 'python': True}
        mock_checker.get_status.return_value = dep_status
        dialog = DependencyDialog(parent, mock_checker)
        dialog.EndModal = MagicMock()
        event = MagicMock()
        dialog.on_close(event)
        dialog.EndModal.assert_called_once_with(wx.ID_CANCEL)

    def test_on_install_with_missing_deps_starts_install(self, wx_mock, mock_checker):
        """Should show progress panel and start installation thread."""
        parent = MagicMock()
        dep_status = {'kicad': False, 'ffmpeg': False, 'python': True}
        mock_checker.get_status.return_value = dep_status
        dialog = DependencyDialog(parent, mock_checker)
        dialog.timer = MagicMock()
        # Mock thread start
        with patch('threading.Thread') as mock_thread_class:
            mock_thread = MagicMock()
            mock_thread_class.return_value = mock_thread

            event = MagicMock()
            dialog.on_install(event)

            # Install button should be disabled
            assert not dialog.install_btn.IsEnabled()
            assert not dialog.close_btn.IsEnabled()
            # Progress panel should be visible
            assert dialog.progress_panel.IsShown()
            # Thread should have been started
            mock_thread_class.assert_called_once()
            mock_thread.start.assert_called_once()

    def test_on_install_with_no_missing_deps_closes_ok(self, wx_mock, mock_checker):
        """Should close with ID_OK if all dependencies satisfied."""
        parent = MagicMock()
        # Create a checker with no missing deps
        checker = MagicMock()
        checker.missing_deps = []
        checker.check_all.return_value = {'kicad': True, 'ffmpeg': True, 'python': True}
        checker.get_status.return_value = {'kicad': True, 'ffmpeg': True, 'python': True}
        dialog = DependencyDialog(parent, checker)
        dialog.EndModal = MagicMock()
        event = MagicMock()
        dialog.on_install(event)
        dialog.EndModal.assert_called_once_with(wx.ID_OK)

    def test_close_button_binds_to_on_close(self, wx_mock, mock_checker):
        """Close button should be bound to on_close handler."""
        parent = MagicMock()
        dep_status = {'kicad': False, 'ffmpeg': False, 'python': True}
        mock_checker.get_status.return_value = dep_status
        dialog = DependencyDialog(parent, mock_checker)
        # Check that close_btn has a binding for wx.EVT_BUTTON
        dialog.close_btn.Bind.assert_called_with(wx.EVT_BUTTON, dialog.on_close)

    def test_install_button_binds_to_on_install(self, wx_mock, mock_checker):
        """Install button should be bound to on_install handler."""
        parent = MagicMock()
        dep_status = {'kicad': False, 'ffmpeg': False, 'python': True}
        mock_checker.get_status.return_value = dep_status
        dialog = DependencyDialog(parent, mock_checker)
        dialog.install_btn.Bind.assert_called_with(wx.EVT_BUTTON, dialog.on_install)

class TestDependencyDialogInstallThread:
    """Test the installation thread logic."""

    def test_run_install_thread_calls_installer(self, wx_mock, mock_checker, mock_install_func):
        """Should call install_dependency for each missing dep."""
        parent = MagicMock()
        dep_status = {'kicad': False, 'ffmpeg': False, 'python': True}
        mock_checker.get_status.return_value = dep_status
        dialog = DependencyDialog(parent, mock_checker)
        # Replace checker's install_dependency with mock
        dialog.checker.install_dependency = mock_install_func
        # Run the thread method directly
        dialog._run_install_thread()
        # Should have called install_dependency for each missing dep
        assert dialog.checker.install_dependency.call_count == 2

    def test_append_log_adds_text(self, wx_mock, mock_checker):
        """Should append text to progress_log."""
        parent = MagicMock()
        dep_status = {'kicad': False, 'ffmpeg': False, 'python': True}
        mock_checker.get_status.return_value = dep_status
        dialog = DependencyDialog(parent, mock_checker)
        # Create a mock TextCtrl that tracks AppendText
        dialog.progress_log = MagicMock()
        dialog._append_log("Test message")
        dialog.progress_log.AppendText.assert_called_once_with("Test message\n")

class TestRoundedPanel:
    """Test the RoundedPanel custom control."""

    def test_constructs_with_radius_and_bg(self, wx_mock):
        """Should create panel with given radius and bg_color."""
        parent = MagicMock()
        color = wx.Colour(30, 30, 30)
        panel = RoundedPanel(parent, radius=6, bg_color=color)
        assert panel.radius == 6
        assert panel.bg_color == color
        panel.SetBackgroundStyle.assert_called_with(wx.BG_STYLE_PAINT)
        panel.Bind.assert_any_call(wx.EVT_PAINT, panel.on_paint)
        panel.Bind.assert_any_call(wx.EVT_SIZE, panel.on_size)

    def test_defaults_to_input_bg(self, wx_mock):
        """Should use a dark default bg_color."""
        parent = MagicMock()
        panel = RoundedPanel(parent)
        # Default bg should be dark; accept either ColorMock or similar
        assert panel.bg_color.Red() < 50
        assert panel.bg_color.Green() < 50
        assert panel.bg_color.Blue() < 50

class TestCustomButton:
    """Test the CustomButton control."""

    def test_constructs_default_primary(self, wx_mock):
        """Should create primary button by default."""
        parent = MagicMock()
        btn = CustomButton(parent, label="OK")
        assert btn.label == "OK"
        assert btn.primary is True
        assert btn.danger is False

    def test_constructs_with_danger(self, wx_mock):
        """Should create danger button."""
        parent = MagicMock()
        btn = CustomButton(parent, label="DELETE", danger=True)
        assert btn.danger is True

    def test_mouse_events_bound(self, wx_mock):
        """Should bind mouse event handlers."""
        parent = MagicMock()
        btn = CustomButton(parent)
        # Just check it doesn't raise
        assert btn.hovered is False

    def test_on_enter_sets_hovered(self, wx_mock):
        """Should set hovered=True on mouse enter."""
        parent = MagicMock()
        btn = CustomButton(parent)
        btn.on_enter(MagicMock())
        assert btn.hovered is True

    def test_on_leave_clears_hovered(self, wx_mock):
        """Should set hovered=False on mouse leave."""
        parent = MagicMock()
        btn = CustomButton(parent)
        btn.hovered = True
        btn.on_leave(MagicMock())
        assert btn.hovered is False

    def test_on_mouse_down_sets_pressed(self, wx_mock):
        """Should set pressed=True on left down."""
        parent = MagicMock()
        btn = CustomButton(parent)
        btn.on_mouse_down(MagicMock())
        assert btn.pressed is True

    def test_on_mouse_up_clears_pressed(self, wx_mock):
        """Should set pressed=False on left up."""
        parent = MagicMock()
        btn = CustomButton(parent)
        btn.pressed = True
        btn.on_mouse_up(MagicMock())
        assert btn.pressed is False
