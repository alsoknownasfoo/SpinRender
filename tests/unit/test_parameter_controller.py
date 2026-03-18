#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
Unit tests for ParameterController.

Tests the extracted parameter change logic from SpinRenderPanel.
"""
import pytest
from unittest.mock import MagicMock, PropertyMock

from SpinRender.ui.parameter_controller import ParameterController
from SpinRender.core.settings import RenderSettings


class TestParameterController:
    """Test suite for ParameterController."""

    @pytest.fixture
    def mock_settings(self):
        """Create fresh RenderSettings for each test."""
        return RenderSettings(
            preset='hero',
            board_tilt=0.0,
            board_roll=-45.0,
            spin_tilt=90.0,
            spin_heading=90.0,
            period=10.0,
            direction='ccw',
            lighting='studio',
            format='mp4',
            resolution='1920x1080',
            bg_color='#000000'
        )

    @pytest.fixture
    def mock_controls(self):
        """Create mock control widgets dict with proper MagicMock setup."""
        controls = {}
        # Sliders
        for name in ['board_tilt_slider', 'board_roll_slider', 'spin_tilt_slider',
                     'spin_heading_slider', 'period_slider']:
            slider = MagicMock()
            slider.GetValue = MagicMock(return_value=0.0)
            slider.SetValue = MagicMock()
            controls[name] = slider

        # Text inputs
        for name in ['board_tilt_input', 'board_roll_input', 'spin_tilt_input',
                     'spin_heading_input', 'period_input']:
            inp = MagicMock()
            inp.GetValue = MagicMock(return_value="0.0")
            inp.SetValue = MagicMock()
            controls[name] = inp

        # Toggles
        dir_toggle = MagicMock()
        dir_toggle.GetSelection = MagicMock(return_value=0)  # CCW
        controls['dir_toggle'] = dir_toggle

        light_toggle = MagicMock()
        light_toggle.GetSelection = MagicMock(return_value=0)  # studio
        controls['light_toggle'] = light_toggle
        controls['light_options'] = [
            {'id': 'studio', 'label': 'STUDIO'},
            {'id': 'dramatic', 'label': 'DRAMATIC'}
        ]

        # Dropdowns
        format_choice = MagicMock()
        format_choice.GetSelection = MagicMock(return_value=0)
        controls['format_choice'] = format_choice
        controls['format_ids'] = ['mp4', 'gif', 'png_sequence']

        res_choice = MagicMock()
        res_choice.GetSelection = MagicMock(return_value=0)
        controls['res_choice'] = res_choice
        controls['res_ids'] = ['1920x1080', '1280x720']

        # Color picker
        bg_picker = MagicMock()
        bg_picker.GetValue.return_value = '#000000'
        controls['bg_picker'] = bg_picker

        return controls

    @pytest.fixture
    def mock_preview(self):
        """Create a mock preview with viewport."""
        preview = MagicMock()
        preview.viewport = MagicMock()
        preview.viewport.set_universal_joint_parameters = MagicMock()
        preview.viewport.set_period = MagicMock()
        preview.viewport.set_direction = MagicMock()
        preview.viewport.set_lighting = MagicMock()
        preview.viewport.set_aspect_ratio = MagicMock()
        preview.viewport.set_background_color = MagicMock()
        preview.viewport.set_render_mode = MagicMock()
        preview.update_preview_overlay = MagicMock()
        return preview

    @pytest.fixture
    def mock_preset_controller(self):
        """Create a mock preset controller."""
        pc = MagicMock()
        pc.check_preset_match = MagicMock()
        return pc

    @pytest.fixture
    def controller(self, mock_settings, mock_controls, mock_preview, mock_preset_controller):
        """Create a ParameterController instance for testing."""
        return ParameterController(
            settings=mock_settings,
            controls=mock_controls,
            preview=mock_preview,
            preset_controller=mock_preset_controller
        )

    def test_controller_initialization(self, controller, mock_settings, mock_controls, mock_preview, mock_preset_controller):
        """Test ParameterController stores references correctly."""
        assert controller.settings is mock_settings
        assert controller.controls is mock_controls
        assert controller.preview is mock_preview
        assert controller.preset_controller is mock_preset_controller

        # Verify controls extracted
        assert controller.board_tilt_slider is mock_controls['board_tilt_slider']
        assert controller.dir_toggle is mock_controls['dir_toggle']

    def test_on_board_tilt_change_slider(self, controller, mock_controls, mock_preview):
        """Test board tilt change from slider updates settings and viewport."""
        mock_controls['board_tilt_slider'].GetValue.return_value = 15.0
        controller.on_board_tilt_change(None)

        assert controller.settings.board_tilt == 15.0
        mock_controls['board_tilt_input'].SetValue.assert_called_with(15.0)
        mock_preview.viewport.set_universal_joint_parameters.assert_called_once()
        mock_preview.update_preview_overlay.assert_called_once()
        controller.preset_controller.check_preset_match.assert_called_with(manual_change=True)

    def test_on_board_tilt_change_input(self, controller, mock_controls, mock_preview):
        """Test board tilt change from input updates settings and viewport."""
        mock_controls['board_tilt_input'].GetValue.return_value = "30.0"
        controller.on_board_tilt_input(None)

        assert controller.settings.board_tilt == 30.0
        mock_controls['board_tilt_slider'].SetValue.assert_called_with(30.0)
        mock_preview.viewport.set_universal_joint_parameters.assert_called_once()
        controller.preset_controller.check_preset_match.assert_called_with(manual_change=True)

    def test_on_board_roll_change(self, controller, mock_controls, mock_preview):
        """Test board roll change updates all expected components."""
        mock_controls['board_roll_slider'].GetValue.return_value = -90.0
        controller.on_board_roll_change(None)

        assert controller.settings.board_roll == -90.0
        mock_controls['board_roll_input'].SetValue.assert_called_with(-90.0)
        mock_preview.viewport.set_universal_joint_parameters.assert_called_once()

    def test_on_spin_tilt_change(self, controller, mock_controls, mock_preview):
        """Test spin tilt change."""
        mock_controls['spin_tilt_slider'].GetValue.return_value = 45.0
        controller.on_spin_tilt_change(None)

        assert controller.settings.spin_tilt == 45.0
        mock_controls['spin_tilt_input'].SetValue.assert_called_with(45.0)
        mock_preview.viewport.set_universal_joint_parameters.assert_called_once()

    def test_on_spin_heading_change(self, controller, mock_controls, mock_preview):
        """Test spin heading change."""
        mock_controls['spin_heading_slider'].GetValue.return_value = 180.0
        controller.on_spin_heading_change(None)

        assert controller.settings.spin_heading == 180.0
        mock_controls['spin_heading_input'].SetValue.assert_called_with(180.0)
        mock_preview.viewport.set_universal_joint_parameters.assert_called_once()

    def test_on_period_change_slider(self, controller, mock_controls, mock_preview):
        """Test period change from slider."""
        mock_controls['period_slider'].GetValue.return_value = 20.0
        controller.on_period_change(None)

        assert controller.settings.period == 20.0
        mock_controls['period_input'].SetValue.assert_called_with(20.0)
        mock_preview.viewport.set_period.assert_called_once_with(20.0)
        mock_preview.update_preview_overlay.assert_called_once()
        controller.preset_controller.check_preset_match.assert_called_with(manual_change=True)

    def test_on_period_change_input(self, controller, mock_controls, mock_preview):
        """Test period change from input."""
        mock_controls['period_input'].GetValue.return_value = "15.5"
        controller.on_period_input_change(None)

        assert controller.settings.period == 15.5
        mock_controls['period_slider'].SetValue.assert_called_with(15.5)
        mock_preview.viewport.set_period.assert_called_once_with(15.5)

    def test_on_direction_change(self, controller, mock_controls, mock_preview):
        """Test direction toggle changes."""
        # CCW (index 0) -> CW (index 1)
        mock_controls['dir_toggle'].GetSelection.return_value = 1
        controller.on_direction_change(None)

        assert controller.settings.direction == 'cw'
        mock_preview.viewport.set_direction.assert_called_once_with('cw')
        controller.preset_controller.check_preset_match.assert_called_with(manual_change=True)

    def test_on_lighting_change(self, controller, mock_controls, mock_preview):
        """Test lighting toggle changes."""
        # Select 'dramatic' (index 1)
        mock_controls['light_toggle'].GetSelection.return_value = 1
        controller.on_lighting_change(None)

        assert controller.settings.lighting == 'dramatic'
        mock_preview.viewport.set_lighting.assert_called_once_with('dramatic')
        controller.preset_controller.check_preset_match.assert_called_with(manual_change=True)

    def test_on_format_change(self, controller, mock_controls, mock_preview):
        """Test output format change."""
        mock_controls['format_choice'].GetSelection.return_value = 1  # GIF
        controller.on_format_change(None)

        assert controller.settings.format == 'gif'
        mock_preview.update_preview_overlay.assert_called_once()

    def test_on_resolution_change(self, controller, mock_controls, mock_preview):
        """Test resolution change."""
        mock_controls['res_choice'].GetSelection.return_value = 1  # 1280x720
        controller.on_resolution_change(None)

        assert controller.settings.resolution == '1280x720'
        mock_preview.viewport.set_aspect_ratio.assert_called_once_with(1280, 720)
        mock_preview.update_preview_overlay.assert_called_once()

    def test_on_bg_color_change(self, controller, mock_controls, mock_preview):
        """Test background color change."""
        controller.on_bg_color_change('#FF0000')

        assert controller.settings.bg_color == '#FF0000'
        mock_preview.viewport.set_background_color.assert_called_once_with('#FF0000')
        mock_preview.update_preview_overlay.assert_called_once()
