"""Focused layout checks for Output Settings source structure."""

import inspect

from SpinRender.ui.controls_side_panel import ControlsSidePanel


def test_output_settings_places_render_options_before_format_row():
    """Render options should be declared before the format/resolution row."""
    source = inspect.getsource(ControlsSidePanel.create_output_settings_section)

    assert 'wx.FlexGridSizer(0, 3, self.FromDIP(8), self.FromDIP(12))' in source
    assert 'self.render_options_grid.Add(self.hide_vias_row, 0, wx.EXPAND)' in source
    assert 'self.render_options_grid.Add(self.hide_components_row, 0, wx.EXPAND)' in source
    assert 'self.render_options_grid.Add(self.hide_test_points_row, 0, wx.EXPAND)' in source
    assert source.index('sizer.Add(board_options_col, 0, wx.EXPAND | wx.BOTTOM, self.FromDIP(12))') < source.index('sizer.Add(cols_panel, 0, wx.EXPAND | wx.BOTTOM, self.FromDIP(12))')


def test_output_settings_tracks_render_options_before_other_output_content():
    """Collapsed-state bookkeeping should preserve render options as the first output block."""
    source = inspect.getsource(ControlsSidePanel.create_output_settings_section)

    assert 'self._output_content = [board_options_col, cols_panel]' in source


def test_output_settings_places_transparent_toggle_in_background_heading():
    """The TRANSPARENT toggle shares the BACKGROUND COLOR heading row."""
    source = inspect.getsource(ControlsSidePanel.create_output_settings_section)

    assert 'option_id="transparent_bg"' in source
    assert 'bg_head_sizer.Add(self.transparent_bg_row, 0, wx.ALIGN_CENTER_VERTICAL)' in source
    assert source.index('self.bg_heading = ') < source.index('option_id="transparent_bg"') < source.index('self.bg_picker = ')


def _sync_background(fmt, transparent):
    from types import SimpleNamespace
    from unittest.mock import MagicMock
    from SpinRender.core.settings import RenderSettings

    panel = SimpleNamespace(
        settings=RenderSettings(format=fmt, transparent_bg=transparent),
        transparent_bg_checkbox=MagicMock(),
        bg_picker=MagicMock(),
    )
    ControlsSidePanel.sync_background_controls(panel)
    return panel.transparent_bg_checkbox.Enable.call_args.args[0], panel.bg_picker.Enable.call_args.args[0]


def test_sync_background_controls_greys_out_what_does_not_apply():
    # (toggle enabled, colour picker enabled)
    assert _sync_background('gif', False) == (True, True)
    assert _sync_background('gif', True) == (True, False)
    assert _sync_background('webp', True) == (True, False)
    assert _sync_background('png_sequence', True) == (True, False)
    # MP4 has no alpha: toggle unavailable, colour always used
    assert _sync_background('mp4', True) == (False, True)
