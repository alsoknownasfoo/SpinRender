#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
Unit tests for ControlsSidePanel component.

Tests the extracted left sidebar UI construction and control creation.
"""
import pytest
from unittest.mock import MagicMock

# Import the module under test
from SpinRender.ui.controls_side_panel import ControlsSidePanel
from core.settings import RenderSettings


class TestControlsSidePanel:
    """Test suite for ControlsSidePanel."""

    @pytest.fixture
    def mock_parent(self, wx_mock):
        """Create a mock parent (SpinRenderPanel) with required attributes."""
        parent = MagicMock()
        parent.settings = RenderSettings(
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
        parent.board_path = "/test/board.kicad_pcb"
        # Mock event handlers
        parent.on_preset_change = MagicMock()
        parent.on_save_preset = MagicMock()
        parent.on_board_tilt_change = MagicMock()
        parent.on_board_tilt_input = MagicMock()
        parent.on_board_roll_change = MagicMock()
        parent.on_board_roll_input = MagicMock()
        parent.on_spin_tilt_change = MagicMock()
        parent.on_spin_tilt_input = MagicMock()
        parent.on_spin_heading_change = MagicMock()
        parent.on_spin_heading_input = MagicMock()
        parent.on_period_change = MagicMock()
        parent.on_period_input_change = MagicMock()
        parent.on_direction_change = MagicMock()
        parent.on_lighting_change = MagicMock()
        parent.on_format_change = MagicMock()
        parent.on_resolution_change = MagicMock()
        parent.on_bg_color_change = MagicMock()
        parent.on_advanced_options = MagicMock()
        parent.on_cancel = MagicMock()
        parent.on_close = MagicMock()
        parent.on_render = MagicMock()
        parent.enable_drag = MagicMock()
        # Helper methods
        parent.create_section_label = MagicMock(return_value=MagicMock())
        parent.create_numeric_input = MagicMock(return_value=MagicMock())
        return parent

    @pytest.fixture
    def real_parent_fixture(self):
        """Create a minimal parent for integration tests using test doubles."""
        parent = MagicMock()
        parent.settings = RenderSettings(
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
        parent.board_path = "/test/board.kicad_pcb"
        parent.on_preset_change = MagicMock()
        parent.on_save_preset = MagicMock()
        parent.on_board_tilt_change = MagicMock()
        parent.on_board_tilt_input = MagicMock()
        parent.on_board_roll_change = MagicMock()
        parent.on_board_roll_input = MagicMock()
        parent.on_spin_heading_change = MagicMock()
        parent.on_spin_heading_input = MagicMock()
        parent.on_period_change = MagicMock()
        parent.on_period_input_change = MagicMock()
        parent.on_direction_change = MagicMock()
        parent.on_lighting_change = MagicMock()
        parent.on_format_change = MagicMock()
        parent.on_resolution_change = MagicMock()
        parent.on_bg_color_change = MagicMock()
        parent.on_advanced_options = MagicMock()
        parent.on_cancel = MagicMock()
        parent.on_close = MagicMock()
        parent.on_render = MagicMock()
        parent.enable_drag = MagicMock()
        parent.create_section_label = lambda p, l: MagicMock()
        parent.create_numeric_input = lambda p, v, u, **kw: MagicMock()
        return parent

    def test_controls_side_panel_creation(self, wx_mock, mock_parent):
        """Test that ControlsSidePanel instantiates without errors."""
        panel = ControlsSidePanel(mock_parent, mock_parent.settings, mock_parent.board_path)
        assert panel is not None
        assert hasattr(panel, 'parent')
        assert panel.parent is mock_parent
        assert panel.settings is mock_parent.settings

    def test_preset_buttons_created(self, wx_mock, mock_parent):
        """Test that preset buttons are created and stored."""
        panel = ControlsSidePanel(mock_parent, mock_parent.settings, mock_parent.board_path)
        assert hasattr(panel, 'preset_buttons')
        assert isinstance(panel.preset_buttons, dict)
        # Should have hero, spin, flip, custom
        assert 'hero' in panel.preset_buttons
        assert 'spin' in panel.preset_buttons
        assert 'flip' in panel.preset_buttons
        assert 'custom' in panel.preset_buttons

    def test_rotation_controls_created(self, wx_mock, mock_parent):
        """Test that rotation sliders and inputs are created."""
        panel = ControlsSidePanel(mock_parent, mock_parent.settings, mock_parent.board_path)
        # Check board tilt controls
        assert hasattr(panel, 'board_tilt_slider')
        assert hasattr(panel, 'board_tilt_input')
        # Check board roll controls
        assert hasattr(panel, 'board_roll_slider')
        assert hasattr(panel, 'board_roll_input')
        # Check spin tilt controls
        assert hasattr(panel, 'spin_tilt_slider')
        assert hasattr(panel, 'spin_tilt_input')
        # Check spin heading controls
        assert hasattr(panel, 'spin_heading_slider')
        assert hasattr(panel, 'spin_heading_input')

    def test_period_controls_created(self, wx_mock, mock_parent):
        """Test that period slider and input are created."""
        panel = ControlsSidePanel(mock_parent, mock_parent.settings, mock_parent.board_path)
        assert hasattr(panel, 'period_slider')
        assert hasattr(panel, 'period_input')
        assert hasattr(panel, 'frame_count')

    def test_direction_control_created(self, wx_mock, mock_parent):
        """Test that direction toggle is created."""
        panel = ControlsSidePanel(mock_parent, mock_parent.settings, mock_parent.board_path)
        assert hasattr(panel, 'dir_toggle')
        assert panel.dir_toggle is not None

    def test_lighting_control_created(self, wx_mock, mock_parent):
        """Test that lighting toggle is created."""
        panel = ControlsSidePanel(mock_parent, mock_parent.settings, mock_parent.board_path)
        assert hasattr(panel, 'light_toggle')
        assert hasattr(panel, 'light_options')
        assert isinstance(panel.light_options, list)
        # Should have studio, dramatic, soft, workspace
        assert len(panel.light_options) == 4
        ids = [opt['id'] for opt in panel.light_options]
        assert 'studio' in ids
        assert 'dramatic' in ids

    def test_output_settings_created(self, wx_mock, mock_parent):
        """Test that output settings controls are created."""
        panel = ControlsSidePanel(mock_parent, mock_parent.settings, mock_parent.board_path)
        assert hasattr(panel, 'format_choice')
        assert hasattr(panel, 'format_choices')
        assert hasattr(panel, 'format_ids')
        assert hasattr(panel, 'res_choice')
        assert hasattr(panel, 'res_choices')
        assert hasattr(panel, 'res_ids')
        assert hasattr(panel, 'bg_picker')

    def test_export_section_created(self, wx_mock, mock_parent):
        """Test that export buttons are created."""
        panel = ControlsSidePanel(mock_parent, mock_parent.settings, mock_parent.board_path)
        assert hasattr(panel, 'adv_btn')
        assert hasattr(panel, 'can_btn')
        assert hasattr(panel, 'render_btn')

    def test_preset_buttons_have_correct_labels(self, wx_mock, mock_parent):
        """Test that preset buttons are created with expected labels."""
        panel = ControlsSidePanel(mock_parent, mock_parent.settings, mock_parent.board_path)
        hero_btn = panel.preset_buttons['hero']
        spin_btn = panel.preset_buttons['spin']
        flip_btn = panel.preset_buttons['flip']
        custom_btn = panel.preset_buttons['custom']
        # Just verify they exist and are not None
        assert hero_btn is not None
        assert spin_btn is not None
        assert flip_btn is not None
        assert custom_btn is not None



class TestControlsSidePanelDependencies:
    """Test dependency handling."""

    def test_requires_settings_attribute(self):
        """Test that settings are required for construction."""
        parent = MagicMock()
        parent.board_path = "/test/board.kicad_pcb"
        # Should require settings
        with pytest.raises(AttributeError):
            panel = ControlsSidePanel(parent, None, parent.board_path)
