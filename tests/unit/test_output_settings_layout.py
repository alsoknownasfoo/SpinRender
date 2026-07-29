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
