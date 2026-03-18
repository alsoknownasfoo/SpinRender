#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""Unit tests for PreviewPanel component (TDD)."""
import pytest
from unittest.mock import MagicMock, patch
import os
import wx  # Import the mocked wx module from conftest

# Define test doubles for wx.StaticText and wx.Timer
class FakeStaticText:
    """Test double for wx.StaticText that stores label and supports color/font changes."""
    def __init__(self, parent, label="", **kwargs):
        self.parent = parent
        self._label = label
        self._font = None
        self._fg_color = None
        self._bg_color = None
        self._bindings = {}
        self._visible = True

    def SetLabel(self, text):
        self._label = text

    def GetLabel(self):
        return self._label

    @property
    def label(self):
        return self._label

    def SetFont(self, font):
        self._font = font

    def SetForegroundColour(self, color):
        self._fg_color = color

    def SetBackgroundColour(self, color):
        self._bg_color = color

    def SetCursor(self, cursor):
        self._cursor = cursor

    def SetWindowStyle(self, style):
        """Accept any style flags; no-op."""
        self._window_style = style

    def Hide(self):
        self._visible = False

    def Show(self):
        self._visible = True

    def Bind(self, event_type, handler):
        self._bindings[event_type] = handler

    def Refresh(self):
        pass


class FakeTimer:
    """Test double for wx.Timer with proper running state."""
    def __init__(self, parent=None):
        self._parent = parent
        self._running = False

    def Start(self, ms=0):
        self._running = True

    def Stop(self):
        self._running = False

    def IsRunning(self):
        return self._running

    def Bind(self, event_type, handler):
        pass

# Patch wx classes globally for this test module
wx.StaticText = FakeStaticText
wx.Timer = FakeTimer

# Now import the module under test
from SpinRender.ui.preview_panel import PreviewPanel
from SpinRender.core.theme import Theme
_theme = Theme.current()


@pytest.fixture(autouse=True)
def mock_gl_preview():
    """Replace GLPreviewRenderer with a mock for all tests."""
    with patch('SpinRender.ui.preview_panel.GLPreviewRenderer') as mock:
        yield mock


@pytest.fixture
def mock_settings():
    """Create a mock RenderSettings object with all required fields."""
    settings = MagicMock()
    settings.preset = 'hero'
    settings.board_tilt = 0.0
    settings.board_roll = -45.0
    settings.spin_tilt = 90.0
    settings.spin_heading = 90.0
    settings.period = 10.0
    settings.direction = 'ccw'
    settings.render_mode = 'both'
    settings.bg_color = '#000000'
    settings.resolution = '1920x1080'
    settings.lighting = 'studio'
    return settings


@pytest.fixture(autouse=True)
def patch_wx_widgets(monkeypatch):
    """Patch wx.StaticText and wx.Timer with our test doubles."""
    monkeypatch.setattr('wx.StaticText', FakeStaticText)
    monkeypatch.setattr('wx.Timer', FakeTimer)


class TestPreviewPanelConstruction:
    """Test PreviewPanel construction and initial state."""

    def test_constructs_with_parent_and_settings(self, wx_mock, mock_settings, mock_gl_preview):
        """Should create PreviewPanel without raising."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        assert preview is not None

    def test_creates_viewport(self, wx_mock, mock_settings, mock_gl_preview):
        """Should create GLPreviewRenderer viewport."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        assert hasattr(preview, 'viewport')
        assert preview.viewport is mock_gl_preview.return_value

    def test_creates_overlay_widgets(self, wx_mock, mock_settings, mock_gl_preview):
        """Should create all overlay text widgets."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        assert hasattr(preview, 'ov_top_left')
        assert hasattr(preview, 'ov_top_right')
        assert hasattr(preview, 'ov_bottom_left')
        assert hasattr(preview, 'ov_bottom_center')
        assert hasattr(preview, 'ov_bottom_right')

    def test_creates_render_preview_panel(self, wx_mock, mock_settings, mock_gl_preview):
        """Should create overlay panel for rendered frames."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        assert hasattr(preview, 'render_preview_panel')

    def test_initializes_playback_timer(self, wx_mock, mock_settings, mock_gl_preview):
        """Should create and bind playback timer."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        assert hasattr(preview, 'playback_timer')
        assert preview.playback_frames == []
        assert preview.playback_index == 0

    def test_initial_state_flags(self, wx_mock, mock_settings, mock_gl_preview):
        """Should set initial state flags correctly."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        assert preview.render_preview_active is False
        assert preview.preview_manually_closed is False
        assert preview.final_output_type is None
        assert preview.render_preview_bitmap is None


class TestPreviewPanelOverlay:
    """Test overlay update logic."""

    def test_update_overlay_shows_preset_name_when_not_custom(self, wx_mock, mock_settings, mock_gl_preview):
        """Should display preset name in top-left when preset is not 'custom'."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        preview.update_preview_overlay()
        assert preview.ov_top_left.label == 'HERO'

    def test_update_overlay_shows_parameters_when_custom(self, wx_mock, mock_settings, mock_gl_preview):
        """Should display raw parameters when preset is 'custom'."""
        mock_settings.preset = 'custom'
        mock_settings.board_tilt = 30.0
        mock_settings.board_roll = -10.0
        mock_settings.spin_tilt = 15.0
        mock_settings.spin_heading = 45.0
        mock_settings.period = 4.5

        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        preview.update_preview_overlay()

        label = preview.ov_top_left.label
        assert 'BT:30°' in label
        assert 'BR:-10°' in label
        assert 'ST:15°' in label
        assert 'SH:45°' in label
        assert '4.5s' in label

    def test_update_overlay_shows_lighting_and_bg(self, wx_mock, mock_settings, mock_gl_preview):
        """Should display lighting and background in bottom-left."""
        mock_settings.lighting = 'dramatic'
        mock_settings.bg_color = '#FF0000'

        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        preview.update_preview_overlay()

        assert 'DRAMATIC' in preview.ov_bottom_left.label
        assert '#FF0000' in preview.ov_bottom_left.label

    def test_update_overlay_shows_resolution_info(self, wx_mock, mock_settings, mock_gl_preview):
        """Should display resolution, aspect ratio, and FPS in bottom-center."""
        mock_settings.resolution = '1920x1080'

        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        preview.update_preview_overlay()

        label = preview.ov_bottom_center.label
        assert '1920 × 1080' in label
        assert '16:9' in label
        assert '30fps' in label

    def test_update_overlay_calculates_4_by_3_aspect(self, wx_mock, mock_settings, mock_gl_preview):
        """Should correctly calculate 4:3 aspect ratio."""
        mock_settings.resolution = '1280x960'  # 4:3

        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        preview.update_preview_overlay()

        label = preview.ov_bottom_center.label
        assert '4:3' in label

    def test_update_overlay_calculates_1_by_1_aspect(self, wx_mock, mock_settings, mock_gl_preview):
        """Should correctly calculate 1:1 aspect ratio."""
        mock_settings.resolution = '1000x1000'  # 1:1

        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        preview.update_preview_overlay()

        label = preview.ov_bottom_center.label
        assert '1:1' in label

    def test_update_overlay_hides_close_button_when_preview_inactive(self, wx_mock, mock_settings, mock_gl_preview):
        """Should hide close button when preview not active."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        preview.render_preview_active = False
        preview.preview_manually_closed = False
        preview.is_rendering = False
        preview.ov_top_right = MagicMock()
        preview.render_mode_sizer = MagicMock()

        preview.update_preview_overlay()

        preview.ov_top_right.Hide.assert_called()
        preview.render_mode_sizer.ShowItems.assert_called_with(True)

    def test_update_overlay_shows_close_button_when_preview_active(self, wx_mock, mock_settings, mock_gl_preview):
        """Should show close button when render preview active."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        preview.render_preview_active = True
        preview.preview_manually_closed = False
        preview.is_rendering = False
        preview.final_output_type = None
        preview.ov_top_right = MagicMock()
        preview.render_mode_sizer = MagicMock()

        preview.update_preview_overlay()

        preview.ov_top_right.Show.assert_called()
        preview.render_mode_sizer.ShowItems.assert_called_with(False)

    def test_update_overlay_shows_frame_count_when_rendering(self, wx_mock, mock_settings, mock_gl_preview):
        """Should show frame count in bottom-right during render preview."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        preview.render_preview_active = True
        preview.preview_manually_closed = False
        preview.current_render_frame = 42
        preview.total_render_frames = 150

        preview.update_preview_overlay()

        assert 'FRAME 42 / 150' in preview.ov_bottom_right.label

    def test_update_overlay_shows_output_type_when_available(self, wx_mock, mock_settings, mock_gl_preview):
        """Should show output type (MP4/GIF) in bottom-right."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        preview.render_preview_active = True
        preview.preview_manually_closed = False
        preview.final_output_type = 'mp4'
        # ov_bottom_right is already a FakeStaticText; no need to replace

        preview.update_preview_overlay()

        assert 'MP4 OUTPUT' in preview.ov_bottom_right.label


class TestPreviewPanelPlayback:
    """Test playback functionality."""

    def test_start_playback_initializes_timer(self, wx_mock, mock_settings, mock_gl_preview, tmp_path):
        """Should start playback timer with frame list."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')

        # Create fake frame files
        frame_dir = tmp_path / "frames"
        frame_dir.mkdir()
        for i in range(5):
            (frame_dir / f"frame{i:04d}.png").write_text("fake")

        preview.start_playback(str(frame_dir), 5)

        assert len(preview.playback_frames) == 5
        assert preview.playback_index == 0
        assert preview.playback_timer._running is True
        assert preview.last_frame_dir == str(frame_dir)

        preview.stop_playback()

    def test_stop_playback_clears_state(self, wx_mock, mock_settings, mock_gl_preview):
        """Should stop timer and clear frame list."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        preview.playback_frames = ['/fake/frame0.png']
        preview.playback_index = 2
        preview.playback_timer._running = True

        preview.stop_playback()

        assert preview.playback_frames == []
        assert preview.playback_index == 0
        assert preview.playback_timer._running is False

    def test_start_playback_with_invalid_dir_does_nothing(self, wx_mock, mock_settings, mock_gl_preview):
        """Should return early for nonexistent frame dir."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        preview.playback_timer._running = False

        preview.start_playback('/nonexistent_dir', 5)
        assert preview.playback_timer._running is False
        assert preview.playback_frames == []

    def test_start_playback_with_zero_count_does_nothing(self, wx_mock, mock_settings, mock_gl_preview):
        """Should return early for zero frame count."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        preview.playback_timer._running = False

        preview.start_playback('/tmp', 0)
        assert preview.playback_timer._running is False
        assert preview.playback_frames == []

    def test_on_playback_timer_advances_frame(self, wx_mock, mock_settings, mock_gl_preview, tmp_path):
        """Timer should cycle through frames."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')

        # Create fake frames
        frame_dir = tmp_path / "frames"
        frame_dir.mkdir()
        for i in range(3):
            (frame_dir / f"frame{i:04d}.png").write_text("fake")

        preview.start_playback(str(frame_dir), 3)

        # Simulate two timer ticks
        initial_index = preview.playback_index
        preview.on_playback_timer(None)
        assert preview.playback_index == (initial_index + 1) % 3
        preview.on_playback_timer(None)
        assert preview.playback_index == (initial_index + 2) % 3

        preview.stop_playback()

    def test_on_playback_timer_stops_if_no_frames(self, wx_mock, mock_settings, mock_gl_preview):
        """Should stop playback if frame list becomes empty."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        preview.playback_timer._running = True
        preview.playback_frames = []

        preview.on_playback_timer(None)

        assert preview.playback_timer._running is False


class TestPreviewPanelRenderPreview:
    """Test render preview overlay functionality."""

    def test_show_overlay_shows_panel(self, wx_mock, mock_settings, mock_gl_preview):
        """Should call Show on render preview panel."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        preview.render_preview_panel.Show = MagicMock()

        preview.show_overlay()

        preview.render_preview_panel.Show.assert_called_once()

    def test_hide_overlay_hides_panel(self, wx_mock, mock_settings, mock_gl_preview):
        """Should call Hide on render preview panel."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        preview.render_preview_panel.Hide = MagicMock()

        preview.hide_overlay()

        preview.render_preview_panel.Hide.assert_called_once()


class TestPreviewPanelClose:
    """Test close preview functionality."""

    def test_on_close_render_preview_resets_state(self, wx_mock, mock_settings, mock_gl_preview):
        """Should stop playback, hide overlay, reset flags."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        preview.playback_timer = MagicMock()
        preview.render_preview_active = True
        preview.preview_manually_closed = False
        preview.final_output_type = 'mp4'
        preview.render_preview_panel = MagicMock()
        preview.update_preview_overlay = MagicMock()

        preview.on_close_render_preview(None)

        assert preview.render_preview_active is False
        assert preview.preview_manually_closed is True
        assert preview.final_output_type is None
        preview.render_preview_panel.Hide.assert_called_once()
        preview.playback_timer.Stop.assert_called_once()
        preview.update_preview_overlay.assert_called_once()


class TestPreviewPanelState:
    """Test state management and viewport updates."""

    def test_set_rotation_updates_viewport(self, wx_mock, mock_settings, mock_gl_preview):
        """Should update viewport rotation parameters."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        preview.viewport = MagicMock()
        preview.update_preview_overlay = MagicMock()

        preview.set_rotation(30, 10, 45, 180)

        preview.viewport.set_universal_joint_parameters.assert_called_once_with(30, 10, 45, 180)
        preview.update_preview_overlay.assert_called_once()

    def test_set_period_updates_viewport(self, wx_mock, mock_settings, mock_gl_preview):
        """Should update viewport period."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        preview.viewport = MagicMock()

        preview.set_period(5.0)

        preview.viewport.set_period.assert_called_once_with(5.0)

    def test_set_direction_updates_viewport(self, wx_mock, mock_settings, mock_gl_preview):
        """Should update viewport direction."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        preview.viewport = MagicMock()

        preview.set_direction('cw')

        preview.viewport.set_direction.assert_called_once_with('cw')

    def test_set_render_mode_updates_viewport(self, wx_mock, mock_settings, mock_gl_preview):
        """Should update viewport render mode."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        preview.viewport = MagicMock()

        preview.set_render_mode('wireframe')

        preview.viewport.set_render_mode.assert_called_once_with('wireframe')

    def test_set_background_color_updates_viewport(self, wx_mock, mock_settings, mock_gl_preview):
        """Should update viewport background color."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        preview.viewport = MagicMock()

        preview.set_background_color('#FF0000')

        preview.viewport.set_background_color.assert_called_once_with('#FF0000')

    def test_set_aspect_ratio_updates_viewport(self, wx_mock, mock_settings, mock_gl_preview):
        """Should update viewport aspect ratio."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        preview.viewport = MagicMock()

        preview.set_aspect_ratio(1280, 720)

        preview.viewport.set_aspect_ratio.assert_called_once_with(1280, 720)

    def test_set_rotation_triggers_overlay_update(self, wx_mock, mock_settings, mock_gl_preview):
        """Should call update_preview_overlay after setting rotation."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        preview.viewport = MagicMock()
        preview.update_preview_overlay = MagicMock()

        preview.set_rotation(30, 10, 45, 180)

        preview.update_preview_overlay.assert_called_once()

    def test_update_render_mode_ui_changes_button_colors(self, wx_mock, mock_settings, mock_gl_preview):
        """Should update render mode button colors."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        # Mock the buttons
        preview.render_mode_btns = {
            'wireframe': MagicMock(),
            'shaded': MagicMock(),
            'both': MagicMock()
        }

        preview.update_render_mode_ui('shaded')

        preview.render_mode_btns['shaded'].SetForegroundColour.assert_called_with(_theme.color("colors.accent.cyan"))
        for mode, btn in preview.render_mode_btns.items():
            if mode != 'shaded':
                btn.SetForegroundColour.assert_called_with(_theme.GREY_100)


class TestPreviewPanelIntegration:
    """Integration checks with expected behavior from main_panel."""

    def test_viewport_initialized_with_correct_parameters(self, wx_mock, mock_gl_preview):
        """Should initialize viewport with settings values."""
        # Use a simple settings object to avoid MagicMock attribute issues
        class SimpleSettings:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)
        settings = SimpleSettings(
            board_tilt=30.0,
            board_roll=-15.0,
            spin_tilt=45.0,
            spin_heading=180.0,
            period=8.5,
            direction='cw',
            render_mode='shaded',
            bg_color='#123456',
            resolution='1280x720',
            preset='hero',
            lighting='studio'
        )
        parent = MagicMock()
        preview = PreviewPanel(parent, settings, '/fake/board.kicad_pcb')
        viewport = mock_gl_preview.return_value
        viewport.set_universal_joint_parameters.assert_called_once_with(30.0, -15.0, 45.0, 180.0)
        viewport.set_period.assert_called_once_with(8.5)
        viewport.set_direction.assert_called_once_with('cw')
        viewport.set_render_mode.assert_called_once_with('shaded')
        viewport.set_background_color.assert_called_once_with('#123456')
        viewport.set_aspect_ratio.assert_called_once_with(1280, 720)
        viewport.start_preview.assert_called_once()

    def test_overlay_visibility_logic_with_render_mode_sizer(self, wx_mock, mock_settings, mock_gl_preview):
        """Test overlay close button show/hide logic."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        preview.ov_top_right = MagicMock()
        preview.render_mode_sizer = MagicMock()

        # Case: render active, not manual closed, not rendering -> show close, hide mode
        preview.render_preview_active = True
        preview.preview_manually_closed = False
        preview.is_rendering = False
        preview.update_preview_overlay()
        preview.ov_top_right.Show.assert_called()
        preview.render_mode_sizer.ShowItems.assert_called_with(False)

        # Case: render inactive -> hide close, show mode
        preview.render_preview_active = False
        preview.update_preview_overlay()
        preview.ov_top_right.Hide.assert_called()
        preview.render_mode_sizer.ShowItems.assert_called_with(True)

    def test_overlay_does_not_fail_when_render_mode_sizer_missing(self, wx_mock, mock_settings, mock_gl_preview):
        """Should handle gracefully if render_mode_sizer doesn't exist."""
        parent = MagicMock()
        preview = PreviewPanel(parent, mock_settings, '/fake/board.kicad_pcb')
        preview.ov_top_right = MagicMock()
        # Ensure render_mode_sizer doesn't exist
        if hasattr(preview, 'render_mode_sizer'):
            delattr(preview, 'render_mode_sizer')

        # Should not raise
        preview.render_preview_active = True
        preview.preview_manually_closed = False
        preview.is_rendering = False
        preview.update_preview_overlay()
