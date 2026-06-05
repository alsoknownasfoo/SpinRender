"""Focused tests for SpinRenderPanel settings hydration."""

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

# Mock optional preview dependencies to keep these tests headless.
sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = MagicMock()
sys.modules['OpenGL.GLU'] = MagicMock()
sys.modules['OpenGL.GLUT'] = MagicMock()
sys.modules['trimesh'] = MagicMock()

from SpinRender.core.settings import RenderSettings


def test_spinrender_panel_restores_collapsed_section_state(monkeypatch):
    """Last-used collapsed section state should survive panel reload."""
    from SpinRender.ui import main_panel
    from SpinRender.core import presets as presets_module

    saved_settings = RenderSettings(
        board_tilt=15.0,
        hide_vias=False,
        hide_components=False,
        hide_test_points=False,
        params_collapsed=False,
        output_collapsed=True,
    )

    class FakePresetManager:
        def __init__(self, board_path):
            self.board_path = board_path

        def get_last_used_settings(self):
            return saved_settings

    monkeypatch.setattr(presets_module, 'PresetManager', FakePresetManager)
    monkeypatch.setattr(main_panel, '_apply_theme_mode', lambda mode: None)
    monkeypatch.setattr(main_panel, 'BoardWorkspace', lambda board_path: SimpleNamespace(board_path=board_path, cleanup=lambda: None))
    monkeypatch.setattr(main_panel, 'RenderController', MagicMock())
    monkeypatch.setattr(main_panel.SpinRenderPanel, 'build_ui', lambda self: None)

    panel = main_panel.SpinRenderPanel(parent=MagicMock(), board_path='/tmp/example.kicad_pcb')

    assert panel.settings.board_tilt == 15.0
    assert panel.settings.hide_vias is True
    assert panel.settings.hide_components is True
    assert panel.settings.hide_test_points is True
    assert panel.settings.params_collapsed is False
    assert panel.settings.output_collapsed is True


def test_spinrender_panel_prepares_render_board_with_render_filters(monkeypatch):
    """Render preparation should invert selected render options into removal filters."""
    from SpinRender.ui import main_panel
    from SpinRender.core import presets as presets_module

    class FakePresetManager:
        def __init__(self, board_path):
            self.board_path = board_path

        def get_last_used_settings(self):
            return None

    initial_workspace = SimpleNamespace(board_path='/tmp/example.spinrender.kicad_pcb', cleanup=lambda: None)
    calls = []

    monkeypatch.setattr(presets_module, 'PresetManager', FakePresetManager)
    monkeypatch.setattr(main_panel, '_apply_theme_mode', lambda mode: None)
    monkeypatch.setattr(main_panel, 'BoardWorkspace', lambda board_path: initial_workspace)
    monkeypatch.setattr(main_panel, 'RenderController', MagicMock())
    monkeypatch.setattr(main_panel.SpinRenderPanel, 'build_ui', lambda self: None)

    panel = main_panel.SpinRenderPanel(parent=MagicMock(), board_path='/tmp/example.kicad_pcb')
    panel.workspace = SimpleNamespace(
        board_path='/tmp/example.spinrender.kicad_pcb',
        prepare_for_render=lambda **kwargs: calls.append(kwargs) or '/tmp/example.spinrender.kicad_pcb',
        cleanup=lambda: None,
    )
    panel.settings.hide_vias = True
    panel.settings.hide_components = True
    panel.settings.hide_test_points = True

    render_board_path = panel._prepare_render_board_path()

    assert render_board_path == '/tmp/example.spinrender.kicad_pcb'
    assert calls == [{
        'hide_vias': False,
        'hide_components': False,
        'hide_test_points': False,
    }]


def test_spinrender_panel_prepares_render_board_with_unselected_options_removed(monkeypatch):
    """Unchecked render options should map to removal filters for the workspace copy."""
    from SpinRender.ui import main_panel
    from SpinRender.core import presets as presets_module

    class FakePresetManager:
        def __init__(self, board_path):
            self.board_path = board_path

        def get_last_used_settings(self):
            return None

    initial_workspace = SimpleNamespace(board_path='/tmp/example.spinrender.kicad_pcb', cleanup=lambda: None)
    calls = []

    monkeypatch.setattr(presets_module, 'PresetManager', FakePresetManager)
    monkeypatch.setattr(main_panel, '_apply_theme_mode', lambda mode: None)
    monkeypatch.setattr(main_panel, 'BoardWorkspace', lambda board_path: initial_workspace)
    monkeypatch.setattr(main_panel, 'RenderController', MagicMock())
    monkeypatch.setattr(main_panel.SpinRenderPanel, 'build_ui', lambda self: None)

    panel = main_panel.SpinRenderPanel(parent=MagicMock(), board_path='/tmp/example.kicad_pcb')
    panel.workspace = SimpleNamespace(
        board_path='/tmp/example.spinrender.kicad_pcb',
        prepare_for_render=lambda **kwargs: calls.append(kwargs) or '/tmp/example.spinrender.kicad_pcb',
        cleanup=lambda: None,
    )
    panel.settings.hide_vias = False
    panel.settings.hide_components = False
    panel.settings.hide_test_points = False

    render_board_path = panel._prepare_render_board_path()

    assert render_board_path == '/tmp/example.spinrender.kicad_pcb'
    assert calls == [{
        'hide_vias': True,
        'hide_components': True,
        'hide_test_points': True,
    }]


def test_spinrender_panel_saves_render_filters_as_default_on(monkeypatch):
    """Render filters should not stick between launches."""
    from SpinRender.ui import main_panel
    from SpinRender.core import presets as presets_module

    class FakePresetManager:
        def __init__(self, board_path):
            self.board_path = board_path
            self.saved_settings = None

        def get_last_used_settings(self):
            return None

        def save_last_used_settings(self, settings):
            self.saved_settings = settings

    manager = FakePresetManager('/tmp/example.kicad_pcb')

    monkeypatch.setattr(presets_module, 'PresetManager', lambda board_path=None: manager)
    monkeypatch.setattr(main_panel, '_apply_theme_mode', lambda mode: None)
    monkeypatch.setattr(main_panel, 'BoardWorkspace', lambda board_path: SimpleNamespace(board_path=board_path, cleanup=lambda: None))
    monkeypatch.setattr(main_panel, 'RenderController', MagicMock())
    monkeypatch.setattr(main_panel.SpinRenderPanel, 'build_ui', lambda self: None)

    panel = main_panel.SpinRenderPanel(parent=MagicMock(), board_path='/tmp/example.kicad_pcb')
    panel.settings.hide_vias = False
    panel.settings.hide_components = False
    panel.settings.hide_test_points = False

    panel.save_settings()

    assert manager.saved_settings.hide_vias is True
    assert manager.saved_settings.hide_components is True
    assert manager.saved_settings.hide_test_points is True
