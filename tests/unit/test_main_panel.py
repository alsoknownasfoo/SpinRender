"""Focused tests for SpinRenderPanel settings hydration."""

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

# Mock OpenGL module to avoid dependency in tests
sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = MagicMock()
sys.modules['OpenGL.GLU'] = MagicMock()
sys.modules['OpenGL.GLUT'] = MagicMock()

from SpinRender.core.settings import RenderSettings


def test_spinrender_panel_restores_collapsed_section_state(monkeypatch):
    """Last-used collapsed section state should survive panel reload."""
    from SpinRender.ui import main_panel
    from SpinRender.core import presets as presets_module

    saved_settings = RenderSettings(
        board_tilt=15.0,
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
    monkeypatch.setattr(main_panel, 'BoardWorkspace', lambda board_path: SimpleNamespace(board_path=board_path))
    monkeypatch.setattr(main_panel, 'RenderController', MagicMock())
    monkeypatch.setattr(main_panel.SpinRenderPanel, 'build_ui', lambda self: None)

    panel = main_panel.SpinRenderPanel(parent=MagicMock(), board_path='/tmp/example.kicad_pcb')

    assert panel.settings.board_tilt == 15.0
    assert panel.settings.params_collapsed is False
    assert panel.settings.output_collapsed is True