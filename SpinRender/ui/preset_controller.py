"""
Preset Controller - manages preset selection, application, and persistence.

Responsibilities:
- Handle preset dropdown selection and custom preset dialog
- Apply preset settings to UI controls and viewport
- Track which preset matches current settings
- Save/load presets via PresetManager
- Persist last used settings

This component extracts preset-related logic from SpinRenderPanel,
providing a focused interface for preset management.
"""
import wx
from typing import Dict, Any, Optional

from SpinRender.core.settings import RenderSettings
from SpinRender.core.presets import PresetManager
from SpinRender.core.locale import Locale
_locale = Locale.current()

# Import dialogs for custom preset selection
try:
    from .dialogs import RecallPresetDialog, SavePresetDialog, ID_RESET
except ImportError:
    # For testing or standalone usage, these can be mocked
    RecallPresetDialog = SavePresetDialog = None
    ID_RESET = None


class PresetController:
    """
    Manages all preset-related operations: selection, application, saving.

    Args:
        parent: Parent wx.Window for dialog ownership
        board_path: Path to the board file (for PresetManager)
        settings: RenderSettings instance to modify
        controls: Dict containing references to UI control widgets:
            - preset_buttons: dict mapping preset_id -> wx control
            - bg_picker: color picker control
            - board_tilt_slider, board_tilt_input
            - board_roll_slider, board_roll_input
            - spin_tilt_slider, spin_tilt_input
            - spin_heading_slider, spin_heading_input
            - period_slider, period_input, frame_count label
            - dir_toggle: direction toggle control
            - light_toggle: lighting toggle control
            - light_options: list of lighting option dicts
        preview: PreviewPanel instance (for viewport and overlay updates)
    """

    def __init__(self, parent: wx.Window, board_path: str, settings: RenderSettings,
                 controls: Dict[str, Any], preview):
        self.parent = parent
        self.board_path = board_path
        self.settings = settings
        self.controls = controls
        self.preview = preview

        # Extract commonly used controls for convenience
        self.preset_buttons = controls.get('preset_buttons', {})
        self.bg_picker = controls.get('bg_picker')
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
        self.light_options = controls.get('light_options', [])
        self._custom_presets_cache = None  # Cached list_presets() result

    def on_preset_change(self, preset_id: str):
        """
        Handle preset combobox selection.

        For built-in presets: apply directly.
        For 'custom': open RecallPresetDialog to select a saved custom preset.
        """
        # Note: Rendering check is performed by caller (SpinRenderPanel) before invoking.
        # This allows UI-layer decision making.

        from SpinRender.core.renderer import RenderEngine
        presets = RenderEngine.PRESETS

        if preset_id == 'custom':
            if 'custom' in self.preset_buttons:
                self.preset_buttons['custom'].SetSelected(False)

            if RecallPresetDialog is None:
                return

            while True:
                # Pass currently selected custom name if active
                curr_name = None
                if 'custom' in self.preset_buttons and self.preset_buttons['custom'].IsSelected():
                    curr_name = self.preset_buttons['custom'].label
                
                dlg = RecallPresetDialog(self.parent, self.board_path, current_name=curr_name)
                result = dlg.ShowModal()
                if result == wx.ID_OK:
                    pd = dlg.GetSelectedSettings()
                    pn = dlg.GetSelectedName()
                    dlg.Destroy()
                    if pd:
                        if 'custom' in self.preset_buttons:
                            self.preset_buttons['custom'].SetLabel(pn)
                        self.apply_preset_data(pd, f"CUSTOM: {pn.upper()}")
                        top = self.parent.GetTopLevelParent()
                        if top:
                            top.Raise()
                    return
                else:
                    dlg.Destroy()
                    self.check_preset_match(manual_change=True)
                    top = self.parent.GetTopLevelParent()
                    if top:
                        top.Raise()
                    return

        if preset_id in presets:
            self.apply_preset_data(presets[preset_id], preset_id.replace('_', ' ').upper())

    def apply_preset_data(self, preset: Any, label: str):
        """
        Apply a preset (dict or RenderSettings) to settings and update all controls.

        Args:
            preset: Preset data with settings keys
            label: Display label for the preset (affects custom handling)
        """
        if not label.startswith("CUSTOM:"):
            if 'custom' in self.preset_buttons:
                self.preset_buttons['custom'].SetLabel(_locale.get("component.preset_card.card4.label", "SELECT CUSTOM"))

        # Determine keys to update
        keys = ['board_tilt', 'board_roll', 'spin_tilt', 'spin_heading', 'period', 'direction', 'lighting', 'bg_color']
        for k in keys:
            if hasattr(preset, k):
                setattr(self.settings, k, getattr(preset, k))
            elif isinstance(preset, dict) and k in preset:
                setattr(self.settings, k, preset[k])

        # Update background color control and viewport
        if hasattr(self.settings, 'bg_color') and self.bg_picker:
            self.bg_picker.SetColor(self.settings.bg_color)
            if hasattr(self.preview, 'viewport'):
                self.preview.viewport.set_background_color(self.settings.bg_color)

        # Update sliders and numeric inputs
        if self.board_tilt_slider:
            self.board_tilt_slider.SetValue(self.settings.board_tilt)
            if self.board_tilt_input:
                self.board_tilt_input.SetValue(self.settings.board_tilt)

        if self.board_roll_slider:
            self.board_roll_slider.SetValue(self.settings.board_roll)
            if self.board_roll_input:
                self.board_roll_input.SetValue(self.settings.board_roll)

        if self.spin_tilt_slider:
            self.spin_tilt_slider.SetValue(self.settings.spin_tilt)
            if self.spin_tilt_input:
                self.spin_tilt_input.SetValue(self.settings.spin_tilt)

        if self.spin_heading_slider:
            self.spin_heading_slider.SetValue(self.settings.spin_heading)
            if self.spin_heading_input:
                self.spin_heading_input.SetValue(self.settings.spin_heading)

        if self.period_slider:
            p = self.settings.period
            self.period_slider.SetValue(p)
            if self.period_input:
                self.period_input.SetValue(round(p, 1))
            if self.frame_count:
                self.frame_count.SetLabel(f"{int(p * 30)} f")

        if self.dir_toggle:
            self.dir_toggle.SetSelection(1 if self.settings.direction == 'cw' else 0)

        if self.light_toggle:
            idx = next((i for i, o in enumerate(self.light_options) if o['id'] == self.settings.lighting), 0)
            self.light_toggle.SetSelection(idx)

        # Update viewport
        if hasattr(self.preview, 'viewport'):
            self.preview.viewport.set_universal_joint_parameters(
                self.settings.board_tilt, self.settings.board_roll,
                self.settings.spin_tilt, self.settings.spin_heading
            )
            self.preview.viewport.set_period(self.settings.period)
            self.preview.viewport.set_direction(self.settings.direction)
            self.preview.viewport.set_lighting(self.settings.lighting)

        self.preview.update_preview_overlay()
        self.check_preset_match(manual_change=False)

    def check_preset_match(self, manual_change: bool = False):
        """
        Check if current settings match any preset (built-in or custom).
        Updates preset button selection states and settings.preset accordingly.
        """
        from SpinRender.core.renderer import RenderEngine
        from SpinRender.core.presets import PresetManager

        presets = RenderEngine.PRESETS
        manager = PresetManager(self.board_path)
        if self._custom_presets_cache is None:
            self._custom_presets_cache = manager.list_presets()
        custom_presets = self._custom_presets_cache

        matched_any = False

        # Check built-in presets
        for pid, btn in self.preset_buttons.items():
            if pid == 'custom':
                continue
            p = presets.get(pid)
            if not p:
                btn.SetSelected(False)
                continue

            # Convert p to dict if needed
            p_dict = p.to_dict() if hasattr(p, 'to_dict') else p
            is_match = all(
                abs(getattr(self.settings, k, 0) - p_dict.get(k, 0)) < 0.01
                for k in ['board_tilt', 'board_roll', 'spin_tilt', 'spin_heading', 'period']
            )
            is_match = is_match and getattr(self.settings, 'direction', '') == p_dict.get('direction', '')
            is_match = is_match and getattr(self.settings, 'lighting', '') == p_dict.get('lighting', '')

            btn.SetSelected(is_match)
            if is_match:
                matched_any = True
                self.settings.preset = pid
                if 'custom' in self.preset_buttons:
                    self.preset_buttons['custom'].SetLabel(_locale.get("component.preset_card.card4.label", "SELECT CUSTOM"))

        # Check custom presets if no built-in match
        cmn = None
        if not matched_any and not manual_change:
            for scope, name in custom_presets:
                pd = manager.load_preset(name, is_global=(scope == 'global'))
                if not pd:
                    continue
                pd_dict = pd.to_dict() if hasattr(pd, 'to_dict') else pd
                match = all(
                    abs(getattr(self.settings, k, 0) - pd_dict.get(k, 0)) < 0.01
                    for k in ['board_tilt', 'board_roll', 'spin_tilt', 'spin_heading', 'period']
                )
                match = match and getattr(self.settings, 'direction', '') == pd_dict.get('direction', '')
                match = match and getattr(self.settings, 'lighting', '') == pd_dict.get('lighting', '')

                if match:
                    cmn = name
                    matched_any = True
                    break

        if 'custom' in self.preset_buttons:
            if cmn:
                self.preset_buttons['custom'].SetLabel(cmn)
                self.preset_buttons['custom'].SetSelected(True)
                self.settings.preset = 'custom'
            else:
                self.preset_buttons['custom'].SetSelected(False)
                if not matched_any:
                    self.settings.preset = 'custom'
                if manual_change and not matched_any:
                    self.preset_buttons['custom'].SetLabel(_locale.get("component.preset_card.card4.label", "SELECT CUSTOM"))

        self.preview.update_preview_overlay()
        # self.check_preset_match(manual_change=False)

    def on_save_preset(self, event=None):
        """Handle Save Preset button click: open dialog and save."""
        if SavePresetDialog is None:
            return

        dlg = SavePresetDialog(self.parent, self.board_path)
        try:
            result = dlg.ShowModal()
            if result == wx.ID_OK:
                name = dlg.GetPresetName()
                if name:
                    manager = PresetManager(self.board_path)
                    if manager.save_preset(name, self.settings):
                        self._custom_presets_cache = None  # Invalidate cache
                        if 'custom' in self.preset_buttons:
                            self.preset_buttons['custom'].SetLabel(name)
                        self.check_preset_match(manual_change=False)
            
            # Ensure main window regains focus after dismissal
            top = self.parent.GetTopLevelParent()
            if top:
                top.Raise()
        finally:
            dlg.Destroy()
