"""Tests for RenderSettings dataclass."""
import pytest
from dataclasses import asdict, fields
from SpinRender.core.settings import RenderSettings


def test_render_settings_default_instantiation():
    """Test RenderSettings can be instantiated with all defaults."""
    settings = RenderSettings()

    # Check all expected fields exist
    assert hasattr(settings, 'board_tilt')
    assert hasattr(settings, 'board_roll')
    assert hasattr(settings, 'spin_tilt')
    assert hasattr(settings, 'spin_heading')
    assert hasattr(settings, 'period')
    assert hasattr(settings, 'direction')
    assert hasattr(settings, 'lighting')
    assert hasattr(settings, 'bg_color')
    assert hasattr(settings, 'render_mode')
    assert hasattr(settings, 'format')
    assert hasattr(settings, 'resolution')
    assert hasattr(settings, 'preset')
    assert hasattr(settings, 'logging_level')


def test_render_settings_default_values():
    """Test all default values are correct."""
    settings = RenderSettings()

    assert settings.board_tilt == 0.0
    assert settings.board_roll == 0.0
    assert settings.spin_tilt == 0.0
    assert settings.spin_heading == 0.0
    assert settings.period == 10.0
    assert settings.direction == 'ccw'
    assert settings.lighting == 'studio'
    assert settings.bg_color == '#000000'
    assert settings.render_mode == 'both'
    assert settings.format == 'mp4'
    assert settings.resolution == '1920x1080'
    assert settings.preset == 'custom'
    assert settings.logging_level == 'info'


def test_render_settings_from_dict_valid():
    """Test from_dict() creates instance from dict with all keys."""
    from dataclasses import asdict

    data = {
        'board_tilt': 15.5,
        'board_roll': -30.0,
        'spin_tilt': 45.0,
        'spin_heading': 90.0,
        'period': 8.5,
        'direction': 'cw',
        'lighting': 'dramatic',
        'bg_color': '#FF0000',
        'render_mode': 'both',
        'format': 'gif',
        'resolution': '1280x720',
        'preset': 'preset1',
        'logging_level': 'debug'
    }
    settings = RenderSettings.from_dict(data)

    assert settings.board_tilt == 15.5
    assert settings.board_roll == -30.0
    assert settings.spin_tilt == 45.0
    assert settings.spin_heading == 90.0
    assert settings.period == 8.5
    assert settings.direction == 'cw'
    assert settings.lighting == 'dramatic'
    assert settings.bg_color == '#FF0000'
    assert settings.render_mode == 'both'
    assert settings.format == 'gif'
    assert settings.resolution == '1280x720'
    assert settings.preset == 'preset1'
    assert settings.logging_level == 'debug'


def test_render_settings_from_dict_partial():
    """Test from_dict() fills missing keys with defaults."""
    data = {
        'board_tilt': 20.0,
        'direction': 'cw'
    }
    settings = RenderSettings.from_dict(data)

    assert settings.board_tilt == 20.0
    assert settings.direction == 'cw'
    assert settings.period == 10.0  # default
    assert settings.bg_color == '#000000'  # default
    assert settings.board_roll == 0.0  # default


def test_render_settings_to_dict():
    """Test to_dict() converts settings back to dict."""
    settings = RenderSettings(board_tilt=30.0, direction='cw', period=12.5)
    data = settings.to_dict()

    assert isinstance(data, dict)
    assert data['board_tilt'] == 30.0
    assert data['direction'] == 'cw'
    assert data['period'] == 12.5
    # Check all required keys are present
    expected_keys = ['board_tilt', 'board_roll', 'spin_tilt', 'spin_heading', 'period',
                     'direction', 'lighting', 'bg_color', 'render_mode', 'format',
                     'resolution', 'preset', 'logging_level']
    for key in expected_keys:
        assert key in data


def test_render_settings_round_trip():
    """Test from_dict(to_dict()) produces identical settings."""
    original = RenderSettings(
        board_tilt=45.0,
        board_roll=-90.0,
        spin_tilt=30.0,
        spin_heading=180.0,
        period=15.5,
        direction='cw',
        lighting='dramatic',
        bg_color='#FF5500',
        render_mode='board',
        format='gif',
        resolution='3840x2160',
        preset='my preset',
        logging_level='debug'
    )
    data = original.to_dict()
    recreated = RenderSettings.from_dict(data)

    assert recreated.board_tilt == original.board_tilt
    assert recreated.board_roll == original.board_roll
    assert recreated.spin_tilt == original.spin_tilt
    assert recreated.spin_heading == original.spin_heading
    assert recreated.period == original.period
    assert recreated.direction == original.direction
    assert recreated.lighting == original.lighting
    assert recreated.bg_color == original.bg_color
    assert recreated.render_mode == original.render_mode
    assert recreated.format == original.format
    assert recreated.resolution == original.resolution
    assert recreated.preset == original.preset
    assert recreated.logging_level == original.logging_level


def test_render_settings_validation_board_tilt_out_of_range():
    """Test that invalid board_tilt raises ValueError."""
    with pytest.raises(ValueError, match="board_tilt"):
        RenderSettings(board_tilt=100.0)


def test_render_settings_validation_board_roll_out_of_range():
    """Test that invalid board_roll raises ValueError."""
    with pytest.raises(ValueError, match="board_roll"):
        RenderSettings(board_roll=200.0)


def test_render_settings_validation_spin_tilt_out_of_range():
    """Test that invalid spin_tilt raises ValueError."""
    with pytest.raises(ValueError, match="spin_tilt"):
        RenderSettings(spin_tilt=-100.0)


def test_render_settings_validation_spin_heading_out_of_range():
    """Test that invalid spin_heading raises ValueError."""
    with pytest.raises(ValueError, match="spin_heading"):
        RenderSettings(spin_heading=190.0)


def test_render_settings_validation_period_negative():
    """Test that negative period raises ValueError."""
    with pytest.raises(ValueError, match="period"):
        RenderSettings(period=-5.0)


def test_render_settings_from_dict_invalid_direction():
    """Test from_dict() with invalid direction still works (accepts any string)."""
    # The dataclass doesn't enforce enum constraints, just type=str
    data = {'direction': 'invalid_string'}
    settings = RenderSettings.from_dict(data)
    assert settings.direction == 'invalid_string'


def test_render_settings_backward_compatibility_old_preset_format():
    """Test RenderSettings works with old preset dict format (only core keys)."""
    old_format = {
        'board_tilt': 10.0,
        'board_roll': 20.0,
        'spin_tilt': 30.0,
        'spin_heading': 45.0,
        'period': 12.5,
        'direction': 'ccw',
        'lighting': 'studio',
        'bg_color': '#FFFFFF'
        # Missing optional keys should use defaults
    }
    settings = RenderSettings.from_dict(old_format)

    assert settings.board_tilt == 10.0
    assert settings.board_roll == 20.0
    assert settings.spin_tilt == 30.0
    assert settings.spin_heading == 45.0
    assert settings.period == 12.5
    assert settings.direction == 'ccw'
    assert settings.lighting == 'studio'
    assert settings.bg_color == '#FFFFFF'
    # Check defaults for missing fields
    assert settings.render_mode == 'both'
    assert settings.format == 'mp4'
    assert settings.resolution == '1920x1080'
    assert settings.preset == 'custom'
    assert settings.logging_level == 'info'


def test_render_settings_to_dict_matches_preset_structure():
    """Test to_dict() produces output compatible with preset JSON schema."""
    settings = RenderSettings(
        board_tilt=15.0,
        board_roll=-30.0,
        spin_tilt=45.0,
        spin_heading=90.0,
        period=8.5,
        direction='cw',
        lighting='dramatic',
        bg_color='#FF0000',
        render_mode='board',
        format='gif',
        resolution='1280x720',
        preset='my-preset',
        logging_level='debug'
    )
    data = settings.to_dict()

    # Should have all RenderSettings fields
    expected_keys = [
        'board_tilt', 'board_roll', 'spin_tilt', 'spin_heading',
        'period', 'direction', 'lighting', 'bg_color',
        'render_mode', 'format', 'resolution', 'preset',
        'logging_level', 'easing', 'output_auto', 'output_path',
        'cli_overrides', 'theme_mode'
    ]
    assert list(sorted(data.keys())) == sorted(expected_keys)


def test_render_settings_immutability_by_default():
    """Test that RenderSettings is mutable (not frozen) - allows changes."""
    settings = RenderSettings()
    # Should be mutable to allow real-time updates in UI
    settings.board_tilt = 45.0
    assert settings.board_tilt == 45.0
    settings.period = 20.0
    assert settings.period == 20.0


# --- PresetManager integration tests ---

def test_preset_manager_save_and_load_render_settings(tmp_path):
    """Test PresetManager can save and load RenderSettings objects."""
    from SpinRender.core.presets import PresetManager

    # Create manager with temp directory
    preset_dir = tmp_path / "presets"
    preset_dir.mkdir()
    manager = PresetManager()
    manager.global_presets_dir = str(preset_dir)
    manager.project_presets_dir = str(preset_dir)

    # Create render settings
    settings = RenderSettings(
        board_tilt=30.0,
        board_roll=-45.0,
        spin_tilt=60.0,
        spin_heading=120.0,
        period=15.0,
        direction='cw',
        lighting='dramatic',
        bg_color='#FF5500',
        render_mode='board',
        format='gif',
        resolution='1920x1080',
        preset='test_preset',
        logging_level='debug'
    )

    # Save preset
    success = manager.save_preset('test', settings)
    assert success is True

    # Load preset
    loaded = manager.load_preset('test')
    assert loaded is not None
    assert isinstance(loaded, RenderSettings)
    assert loaded.board_tilt == 30.0
    assert loaded.direction == 'cw'
    assert loaded.lighting == 'dramatic'
    assert loaded.bg_color == '#FF5500'


def test_preset_manager_save_and_load_dict_backward_compatibility(tmp_path):
    """Test PresetManager still works with plain dicts for backward compatibility."""
    from SpinRender.core.presets import PresetManager

    # Create manager with temp directory
    preset_dir = tmp_path / "presets"
    preset_dir.mkdir()
    manager = PresetManager()
    manager.global_presets_dir = str(preset_dir)
    manager.project_presets_dir = str(preset_dir)

    # Old-style dict
    old_settings = {
        'board_tilt': 25.0,
        'board_roll': 35.0,
        'spin_tilt': 45.0,
        'spin_heading': 55.0,
        'period': 8.0,
        'direction': 'ccw',
        'lighting': 'studio',
        'bg_color': '#000000'
    }

    # Save plain dict
    success = manager.save_preset('old', old_settings)
    assert success is True

    # Load returns RenderSettings
    loaded = manager.load_preset('old')
    assert isinstance(loaded, RenderSettings)
    assert loaded.board_tilt == 25.0
    assert loaded.period == 8.0
