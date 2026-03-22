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

from SpinRender.core.settings import RenderSettings


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
            self.frame_count.SetLabel(f"{int(val * 30)} f")
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
            self.frame_count.SetLabel(f"{int(val * 30)} f")
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

    # Resolution handler
    def on_resolution_change(self, event):
        idx = self.res_choice.GetSelection()
        if 0 <= idx < len(self.res_ids):
            self.settings.resolution = self.res_ids[idx]
            try:
                w, h = map(int, self.settings.resolution.split('x'))
                if hasattr(self.preview, 'viewport'):
                    self.preview.viewport.set_aspect_ratio(w, h)
            except Exception:
                pass
        self.preview.update_preview_overlay()
        self.schedule_save()

    # Background color handler (takes color_hex directly)
    def on_bg_color_change(self, color_hex):
        self.settings.bg_color = color_hex
        if hasattr(self.preview, 'viewport'):
            self.preview.viewport.set_background_color(color_hex)
        self.preview.update_preview_overlay()
        self.schedule_save()
