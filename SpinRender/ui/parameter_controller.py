"""
Parameter Controller - manages UI control value changes and their effects.

Handles all parameter adjustments from the controls side panel:
- Rotation parameters (board tilt, roll, spin tilt, spin heading)
- Period control
- Direction toggle
- Lighting selection
- Output format and resolution
- Background color

Responsible for:
- Updating RenderSettings when controls change
- Syncing paired controls (slider ↔ input)
- Notifying preview viewport of parameter updates
- Triggering preset match check via PresetController
"""
from typing import Dict, Any, Callable, Optional

import wx

from SpinRender.core.settings import RenderSettings
from .helpers import update_text


class ParameterController:
    """
    Manages parameter changes from UI controls.

    Args:
        settings: RenderSettings instance to update
        controls: Dict containing references to all control widgets
        preview: PreviewPanel instance for viewport updates
        preset_controller: PresetController for preset matching
        schedule_save: Callable that schedules a debounced settings persist
    """

    def __init__(self, settings: RenderSettings, controls: Dict[str, Any],
                 preview, preset_controller, schedule_save: Optional[Callable] = None):
        self.settings = settings
        self.controls = controls
        self.preview = preview
        self.preset_controller = preset_controller
        self.schedule_save = schedule_save or (lambda: None)

        # Extract controls for convenience
        self.board_tilt_slider = controls.get('board_tilt_slider')
        self.board_tilt_input = controls.get('board_tilt_input')
        self.board_roll_slider = controls.get('board_roll_slider')
        self.board_roll_input = controls.get('board_roll_input')
        self.spin_tilt_slider = controls.get('spin_tilt_slider')
        self.spin_tilt_input = controls.get('spin_tilt_input')
        self.spin_heading_slider = controls.get('spin_heading_slider')
        self.spin_heading_input = controls.get('spin_heading_input')
        self.period_slider = controls.get('period_slider')
        self.period_input = controls.get('period_input')
        self.frame_count = controls.get('frame_count')
        self.dir_toggle = controls.get('dir_toggle')
        self.light_toggle = controls.get('light_toggle')
        self.format_choice = controls.get('format_choice')
        self.format_ids = controls.get('format_ids', [])
        self.res_choice = controls.get('res_choice')
        self.res_ids = controls.get('res_ids', [])
        self.hide_vias_checkbox = controls.get('hide_vias_checkbox')
        self.hide_components_checkbox = controls.get('hide_components_checkbox')
        self.hide_test_points_checkbox = controls.get('hide_test_points_checkbox')
        self.controls_side_panel = controls.get('controls_side_panel')

    # Rotation handlers
    def on_board_tilt_change(self, event):
        val = float(self.board_tilt_slider.GetValue())
        self.settings.board_tilt = val
        self.board_tilt_input.SetValue(val)
        self._update_viewport_rotation()
        self.preset_controller.check_preset_match(manual_change=True)
        self.schedule_save()

    def on_board_tilt_input(self, event):
        val = float(self.board_tilt_input.GetValue())
        self.settings.board_tilt = val
        self.board_tilt_slider.SetValue(val)
        self._update_viewport_rotation()
        self.preset_controller.check_preset_match(manual_change=True)
        self.schedule_save()

    def on_board_roll_change(self, event):
        val = float(self.board_roll_slider.GetValue())
        self.settings.board_roll = val
        self.board_roll_input.SetValue(val)
        self._update_viewport_rotation()
        self.preset_controller.check_preset_match(manual_change=True)
        self.schedule_save()

    def on_board_roll_input(self, event):
        val = float(self.board_roll_input.GetValue())
        self.settings.board_roll = val
        self.board_roll_slider.SetValue(val)
        self._update_viewport_rotation()
        self.preset_controller.check_preset_match(manual_change=True)
        self.schedule_save()

    def on_spin_tilt_change(self, event):
        val = float(self.spin_tilt_slider.GetValue())
        self.settings.spin_tilt = val
        self.spin_tilt_input.SetValue(val)
        self._update_viewport_rotation()
        self.preset_controller.check_preset_match(manual_change=True)
        self.schedule_save()

    def on_spin_tilt_input(self, event):
        val = float(self.spin_tilt_input.GetValue())
        self.settings.spin_tilt = val
        self.spin_tilt_slider.SetValue(val)
        self._update_viewport_rotation()
        self.preset_controller.check_preset_match(manual_change=True)
        self.schedule_save()

    def on_spin_heading_change(self, event):
        val = float(self.spin_heading_slider.GetValue())
        self.settings.spin_heading = val
        self.spin_heading_input.SetValue(val)
        self._update_viewport_rotation()
        self.preset_controller.check_preset_match(manual_change=True)
        self.schedule_save()

    def on_spin_heading_input(self, event):
        val = float(self.spin_heading_input.GetValue())
        self.settings.spin_heading = val
        self.spin_heading_slider.SetValue(val)
        self._update_viewport_rotation()
        self.preset_controller.check_preset_match(manual_change=True)
        self.schedule_save()

    def _update_viewport_rotation(self):
        """Update viewport universal joint parameters."""
        if hasattr(self.preview, 'viewport'):
            self.preview.viewport.set_universal_joint_parameters(
                self.settings.board_tilt,
                self.settings.board_roll,
                self.settings.spin_tilt,
                self.settings.spin_heading
            )
        self.preview.update_preview_overlay()

    # Period handler
    def on_period_change(self, event):
        val = round(float(self.period_slider.GetValue()), 1)
        self.settings.period = val
        self.period_input.SetValue(val)
        if self.frame_count:
            update_text(self.frame_count, f"{int(val * 30)} f")
        if hasattr(self.preview, 'viewport'):
            self.preview.viewport.set_period(val)
        self.preview.update_preview_overlay()
        self.preset_controller.check_preset_match(manual_change=True)
        self.schedule_save()

    def on_period_input_change(self, event):
        val = round(float(self.period_input.GetValue()), 1)
        self.settings.period = val
        self.period_slider.SetValue(val)
        if self.frame_count:
            update_text(self.frame_count, f"{int(val * 30)} f")
        if hasattr(self.preview, 'viewport'):
            self.preview.viewport.set_period(val)
        self.preview.update_preview_overlay()
        self.preset_controller.check_preset_match(manual_change=True)
        self.schedule_save()

    # Direction handler
    def on_direction_change(self, event):
        self.settings.direction = 'cw' if self.dir_toggle.GetSelection() == 1 else 'ccw'
        if hasattr(self.preview, 'viewport'):
            self.preview.viewport.set_direction(self.settings.direction)
        self.preview.update_preview_overlay()
        self.preset_controller.check_preset_match(manual_change=True)
        self.schedule_save()

    # Lighting handler
    def on_lighting_change(self, event):
        idx = self.light_toggle.GetSelection()
        if 0 <= idx < len(self.controls.get('light_options', [])):
            preset_id = self.controls['light_options'][idx]['id']
            self.settings.lighting = preset_id
            if hasattr(self.preview, 'viewport'):
                self.preview.viewport.set_lighting(preset_id)
            self.preview.update_preview_overlay()
            self.preset_controller.check_preset_match(manual_change=True)
            self.schedule_save()

    # Output format handler
    def on_format_change(self, event):
        idx = self.format_choice.GetSelection()
        if 0 <= idx < len(self.format_ids):
            self.settings.format = self.format_ids[idx]
        self.preview.update_preview_overlay()
        self.schedule_save()

    # Resolution handlers
    def _apply_resolution_aspect(self, res_id):
        """Update settings + viewport aspect ratio from a 'WxH' id."""
        self.settings.resolution = res_id
        try:
            w, h = map(int, res_id.split('x'))
            if hasattr(self.preview, 'viewport'):
                self.preview.viewport.set_aspect_ratio(w, h)
        except Exception:
            pass

    def _live_res_ids(self):
        """Current dropdown id list (built-ins + customs), preferring the live
        list on the side panel over the snapshot captured at construction."""
        csp = self.controls_side_panel
        if csp is not None and getattr(csp, 'res_ids', None):
            return csp.res_ids
        return self.res_ids

    def on_resolution_change(self, event):
        idx = self.res_choice.GetSelection()
        ids = self._live_res_ids()
        if 0 <= idx < len(ids):
            self._apply_resolution_aspect(ids[idx])
        self.preview.update_preview_overlay()
        self.schedule_save()

    def on_hide_vias_change(self, event):
        self.settings.hide_vias = bool(self.hide_vias_checkbox.GetValue())
        self.preview.update_preview_overlay()
        self.schedule_save()

    def on_hide_components_change(self, event):
        self.settings.hide_components = bool(self.hide_components_checkbox.GetValue())
        self.preview.update_preview_overlay()
        self.schedule_save()

    def on_hide_test_points_change(self, event):
        self.settings.hide_test_points = bool(self.hide_test_points_checkbox.GetValue())
        self.preview.update_preview_overlay()
        self.schedule_save()

    def on_open_custom_resolutions(self, event=None):
        """Open the Custom Resolutions dialog (gear icon). The dialog manages the
        custom-resolution list in-place; on close we rebuild the dropdown and
        apply any picked resolution, falling back if the active one was deleted."""
        from .dialogs import CustomResolutionsDialog
        from .controls_side_panel import BUILTIN_RESOLUTIONS

        csp = self.controls_side_panel
        parent = self.res_choice.GetTopLevelParent()
        dlg = CustomResolutionsDialog(parent, self.settings)
        try:
            result = dlg.ShowModal()
            selected = dlg.GetSelectedResolution()
        finally:
            dlg.Destroy()

        valid_ids = [rid for _, rid in BUILTIN_RESOLUTIONS] + list(
            getattr(self.settings, 'custom_resolutions', None) or []
        )
        if result == wx.ID_OK and selected and selected in valid_ids:
            self._apply_resolution_aspect(selected)
        elif self.settings.resolution not in valid_ids:
            # The active resolution was deleted in the dialog; fall back.
            self._apply_resolution_aspect('1920x1080')

        if csp:
            csp.rebuild_resolution_items(selected_id=self.settings.resolution)
        self.preview.update_preview_overlay()
        self.schedule_save()
        if parent:
            parent.Raise()

    # Background color handler (takes color_hex directly)
    def on_bg_color_change(self, color_hex):
        self.settings.bg_color = color_hex
        if hasattr(self.preview, 'viewport'):
            self.preview.viewport.set_background_color(color_hex)
        self.preview.update_preview_overlay()
        self.schedule_save()
