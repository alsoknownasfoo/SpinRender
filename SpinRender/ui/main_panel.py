"""
SpinRender Main UI Panel
"""
import wx
import wx.svg
import wx.lib.scrolledpanel as scrolled
import os
import json
import time
import threading
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger("SpinRender")

# Use absolute imports from the plugin root for KiCad compatibility
from ui.custom_controls import (
    CustomSlider, CustomToggleButton, CustomButton,
    PresetCard, SectionLabel, NumericDisplay, NumericInput
)
from .text_styles import TextStyle, TextStyles

# Import preview renderers
from core.preview import GLPreviewRenderer

# Import theme module for centralized colors
from . import theme
from .preview_panel import PreviewPanel

# Import RenderSettings
from core.settings import RenderSettings
from .preset_controller import PresetController
from core.render_controller import RenderController
from .controls_side_panel import ControlsSidePanel


class SpinRenderPanel(wx.Panel):
    """
    Main SpinRender UI panel with two-panel layout
    """

    def __init__(self, parent, board_path):
        super().__init__(parent)
        self.board_path = board_path
        self.board_dir = os.path.dirname(board_path)
        
        # Default settings
        self.settings = RenderSettings(
            preset='hero',
            board_tilt=0.0,
            board_roll=-45.0,
            spin_tilt=90.0,
            spin_heading=90.0,
            period=10.0,
            easing='linear',
            direction='ccw',
            lighting='studio',
            format='mp4',
            resolution='1920x1080',
            bg_color='#000000',
            output_auto=True,
            output_path='',
            cli_overrides='',
            render_mode='both',
            logging_level='simple'
        )
        
        # Attempt to load last used settings
        from core.presets import PresetManager
        manager = PresetManager(self.board_path)
        last_settings = manager.get_last_used_settings()
        if last_settings:
            # Merge last settings into current settings
            if isinstance(last_settings, RenderSettings):
                # Update individual attributes
                for field in ['board_tilt', 'board_roll', 'spin_tilt', 'spin_heading',
                              'period', 'direction', 'lighting', 'bg_color',
                              'render_mode', 'format', 'resolution', 'preset',
                              'logging_level', 'easing', 'output_auto', 'output_path',
                              'cli_overrides']:
                    if hasattr(last_settings, field):
                        setattr(self.settings, field, getattr(last_settings, field))
            
        # Initialize logging level from settings
        from utils.logger import SpinLogger
        SpinLogger.setup(level=getattr(self.settings, 'logging_level', 'simple'))
            
        self.SetBackgroundColour(theme.BG_PAGE)
        self.drag_start_pos = None
        self.frame_start_pos = None
        self.render_controller = RenderController()
        self.avg_frame_time = None
        self.frame_times = []
        
        # Status state for custom paint
        self.status_msg = "READY"
        self.status_fg = theme.ACCENT_GREEN
        self.status_prog = 0.0
        self.status_bar_color = theme.ACCENT_CYAN

        self.build_ui()

    def build_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        top_panel = wx.Panel(self)
        top_panel.SetBackgroundColour(theme.BG_PAGE)
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Left: Controls panel - instantiate ControlsSidePanel
        self.controls_side_panel = ControlsSidePanel(top_panel, self.settings, self.board_path)
        top_sizer.Add(self.controls_side_panel, 0, wx.EXPAND)
        # Expose commonly accessed controls from side panel
        self.render_btn = self.controls_side_panel.render_btn
        self.adv_btn = self.controls_side_panel.adv_btn
        self.can_btn = self.controls_side_panel.can_btn
        self.header_close_btn = self.controls_side_panel.header_close_btn
        self.preset_buttons = self.controls_side_panel.preset_buttons

        # Center Divider
        divider = wx.Panel(top_panel, size=(1, -1))
        divider.SetBackgroundColour(theme.BORDER_DEFAULT)
        top_sizer.Add(divider, 0, wx.EXPAND)

        # Right: Preview panel
        self.preview_panel = self.create_preview_panel(top_panel)
        top_sizer.Add(self.preview_panel, 0, wx.EXPAND | wx.FIXED_MINSIZE)

        top_panel.SetSizer(top_sizer)
        top_sizer.Fit(top_panel)
        main_sizer.Add(top_panel, 1, wx.EXPAND)

        status_divider = wx.Panel(self, size=(-1, 1))
        status_divider.SetBackgroundColour(theme.BORDER_DEFAULT)
        main_sizer.Add(status_divider, 0, wx.EXPAND)

        self.status_bar_panel = self.create_status_bar(self)
        main_sizer.Add(self.status_bar_panel, 0, wx.EXPAND)

        self.SetSizer(main_sizer)

        main_sizer.Layout()
        min_size = main_sizer.CalcMin()
        self.SetMinSize(min_size)

        parent_frame = self.GetTopLevelParent()
        if parent_frame:
            main_sizer.SetSizeHints(parent_frame)

        # Initialize preset controller after UI is built (controls exist)
        self._init_preset_controller()

        # Perform initial preset match check (now via controller)
        self.preset_controller.check_preset_match(manual_change=False)

    def _init_preset_controller(self):
        """Collect control references and instantiate PresetController."""
        # Controls are now on self.controls_side_panel
        csp = self.controls_side_panel
        controls = {
            'preset_buttons': getattr(csp, 'preset_buttons', {}),
            'bg_picker': getattr(csp, 'bg_picker', None),
            'board_tilt_slider': getattr(csp, 'board_tilt_slider', None),
            'board_tilt_input': getattr(csp, 'board_tilt_input', None),
            'board_roll_slider': getattr(csp, 'board_roll_slider', None),
            'board_roll_input': getattr(csp, 'board_roll_input', None),
            'spin_tilt_slider': getattr(csp, 'spin_tilt_slider', None),
            'spin_tilt_input': getattr(csp, 'spin_tilt_input', None),
            'spin_heading_slider': getattr(csp, 'spin_heading_slider', None),
            'spin_heading_input': getattr(csp, 'spin_heading_input', None),
            'period_slider': getattr(csp, 'period_slider', None),
            'period_input': getattr(csp, 'period_input', None),
            'frame_count': getattr(csp, 'frame_count', None),
            'dir_toggle': getattr(csp, 'dir_toggle', None),
            'light_toggle': getattr(csp, 'light_toggle', None),
            'light_options': getattr(csp, 'light_options', []),
        }

        self.preset_controller = PresetController(
            parent=self,
            board_path=self.board_path,
            settings=self.settings,
            controls=controls,
            preview=self.preview
        )

    def create_preview_panel(self, parent):
        """Create the preview panel using the extracted PreviewPanel component."""
        # Create the PreviewPanel component
        self.preview = PreviewPanel(parent, self.settings, self.board_path)

        # Expose preset_buttons for overlay label overrides
        self.preview.preset_buttons = self.preset_buttons

        # Bind close button to handler
        self.preview.ov_top_right.Bind(wx.EVT_LEFT_DOWN, self.on_close_render_preview)

        # Bind render mode buttons
        for mode_id, btn in self.preview.render_mode_btns.items():
            btn.Bind(wx.EVT_LEFT_DOWN, lambda e, m=mode_id: self.on_render_mode_change(m))

        # Enable drag on preview panel and its overlay widgets (excluding close button which handles its own clicks)
        self.enable_drag(self.preview)
        self.enable_drag(self.preview.ov_top_left)
        self.enable_drag(self.preview.ov_bottom_left)
        self.enable_drag(self.preview.ov_bottom_center)
        self.enable_drag(self.preview.ov_bottom_right)

        # Initial overlay update will be called by PreviewPanel constructor
        return self.preview


    def enable_left_panel_controls(self, enable=True):
        """Recursively enable or disable controls in the left panel and manage preview-closing bindings"""
        from ui.custom_controls import CustomSlider, CustomButton, CustomToggleButton, NumericInput, PresetCard, CustomDropdown, CustomTextInput
        
        def process_widget(widget):
            # Skip the render button so we can still click STOP
            if widget == self.render_btn:
                return
                
            is_control = isinstance(widget, (CustomSlider, CustomButton, CustomToggleButton, NumericInput, PresetCard, CustomDropdown, CustomTextInput, wx.Choice))
            
            # Special case for Save Preset button which is a CustomButton
            if isinstance(widget, CustomButton) and widget.GetLabel() == "+ SAVE PRESET":
                is_control = True

            if is_control:
                widget.Enable(enable)
                
                # Bind click interaction to close preview only if control is enabled
                if enable:
                    # Bind our specific handler
                    widget.Bind(wx.EVT_LEFT_DOWN, self.on_left_panel_interaction)
                else:
                    # ONLY unbind our specific handler to avoid breaking internal control logic
                    widget.Unbind(wx.EVT_LEFT_DOWN, handler=self.on_left_panel_interaction)
            
            for child in widget.GetChildren():
                process_widget(child)
        
        process_widget(self.controls_side_panel)
        
        # Header close button should NEVER be disabled
        if hasattr(self, 'header_close_btn'):
            self.header_close_btn.Enable(True)
        
        # Force a refresh of all controls to update their visual state
        self.controls_side_panel.Refresh()





    def on_left_panel_interaction(self, event):
        """Handle clicks on active controls in left panel to close preview"""
        # Only close if the control we clicked is actually enabled
        obj = event.GetEventObject()
        if obj and obj.IsEnabled():
            self.reset_status_bar()
        event.Skip()

    def _on_render_preview_paint(self, _event):
        """Paint handler for render preview overlay using GraphicsContext for high-DPI sharpness"""
        dc = wx.AutoBufferedPaintDC(self.preview.render_preview_panel)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        w, h = self.preview.render_preview_panel.GetSize()
        
        # 1. Get current background color
        bg_hex = self.settings.bg_color
        if bg_hex == 'opaque': bg_hex = '#000000'
        bg_color = wx.Colour(bg_hex)
        
        # 2. Fill background with selected color
        gc.SetBrush(wx.Brush(bg_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRectangle(0, 0, w, h)

        if self.render_preview_bitmap and self.render_preview_bitmap.IsOk():
            bmp_width = self.render_preview_bitmap.GetWidth()
            bmp_height = self.render_preview_bitmap.GetHeight()
            if w <= 0 or h <= 0 or bmp_width <= 0 or bmp_height <= 0: return
            panel_aspect = w / h
            bmp_aspect = bmp_width / bmp_height
            if bmp_aspect > panel_aspect:
                display_width = w
                display_height = w / bmp_aspect
                x_offset = 0
                y_offset = (h - display_height) / 2
            else:
                display_height = h
                display_width = h * bmp_aspect
                x_offset = (w - display_width) / 2
                y_offset = 0
            
            # Note: We already filled the whole panel with bg_color, 
            # but we could also specifically fill just the bitmap rect if needed.
            
            gc.SetInterpolationQuality(wx.INTERPOLATION_BEST)
            gc.DrawBitmap(self.render_preview_bitmap, x_offset, y_offset, display_width, display_height)
            
            # Draw faint gray outline around the render
            gc.SetBrush(wx.TRANSPARENT_BRUSH)
            gc.SetPen(wx.Pen(theme.WHITE_ALPHA_30, 1))
            gc.DrawRectangle(x_offset, y_offset, display_width, display_height)
        else:
            # Draw empty outline matching resolution if no bitmap yet
            # Calculate Display Dimensions based on current settings resolution
            try:
                parts = self.settings.resolution.split('x')
                bw, bh = map(int, parts)
                panel_aspect = w / h
                bmp_aspect = bw / bh
                if bmp_aspect > panel_aspect:
                    dw, dh = w, w / bmp_aspect
                    ox, oy = 0, (h - dh) / 2
                else:
                    dh, dw = h, h * bmp_aspect
                    ox, oy = (w - dw) / 2, 0
                
                gc.SetBrush(wx.TRANSPARENT_BRUSH)
                gc.SetPen(wx.Pen(theme.WHITE_ALPHA_30, 1))
                gc.DrawRectangle(ox, oy, dw, dh)
            except: pass

    def create_status_bar(self, parent):
        panel = wx.Panel(parent, size=(-1, 25))
        panel.SetBackgroundColour(theme.BG_PANEL)
        panel.SetMinSize((-1, 25))
        panel.SetMaxSize((-1, 25))
        panel.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        panel.Bind(wx.EVT_PAINT, self.on_paint_status)
        return panel

    def on_paint_status(self, event):
        win = event.GetEventObject()
        dc = wx.AutoBufferedPaintDC(win)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return
        w, h = win.GetSize()
        gc.SetBrush(wx.Brush(theme.BG_PANEL))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRectangle(0, 0, w, h)
        font = TextStyle(family=theme.FONT_MONO, size=8, weight=400).create_font()
        gc.SetFont(font, self.status_fg)
        tw, th = gc.GetTextExtent(self.status_msg)
        tx, ty = 10, (h - th) / 2
        gc.DrawText(self.status_msg, tx, ty)
        fill_w = int(w * self.status_prog)
        if fill_w > 0:
            gc.SetBrush(wx.Brush(self.status_bar_color))
            gc.DrawRectangle(0, 0, fill_w, h)
            gc.Clip(0, 0, fill_w, h)
            gc.SetFont(font, theme.BG_INPUT)
            gc.DrawText(self.status_msg, tx, ty)
            gc.ResetClip()

    def reset_status_bar(self):
        """Resets the status bar to ready state if not currently rendering."""
        if self.render_controller.is_rendering():
            return
        
        # Any adjustment closes render preview
        if self.render_preview_active:
            self.render_preview_active = False
            self.final_output_type = None
            if hasattr(self, 'render_preview_panel'):
                self.preview.render_preview_panel.Hide()
            self.preview.update_preview_overlay()

        if self.status_msg == "READY" and self.status_prog == 0.0: return
        self.status_msg = "READY"
        self.status_fg = theme.ACCENT_GREEN
        self.status_prog = 0.0
        self.status_bar_color = theme.ACCENT_CYAN
        if hasattr(self, 'status_bar_panel'):
            self.status_bar_panel.Refresh()

    def create_section_label(self, parent, text):
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(panel, label=text)
        label.SetForegroundColour(theme.ACCENT_CYAN)
        label.SetFont(TextStyle(family=theme.FONT_DISPLAY, size=13, weight=600).create_font())
        sizer.Add(label, 0, wx.ALIGN_CENTER_VERTICAL)
        line = wx.Panel(panel, size=(60, 1))
        line.SetBackgroundColour(theme.BORDER_DEFAULT)
        sizer.Add(line, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 8)
        panel.SetSizerAndFit(sizer)
        return panel

    def create_numeric_input(self, parent, value, unit, editable=True, min_val=None, max_val=None):
        v = float(value) if isinstance(value, str) else value
        if editable: return NumericInput(parent, value=v, unit=unit, min_val=min_val, max_val=max_val, size=(100, 32))
        else: return NumericDisplay(parent, value=v, unit=unit, size=(100, 32))

    def on_preset_change(self, preset_id):
        """Delegates to PresetController."""
        if self.render_controller.is_rendering():
            return
        self.reset_status_bar()
        self.preset_controller.on_preset_change(preset_id)

    def on_board_tilt_change(self, event):
        self.reset_status_bar()
        self.settings.board_tilt = float(self.controls_side_panel.board_tilt_slider.GetValue())
        self.controls_side_panel.board_tilt_input.SetValue(self.settings.board_tilt)
        self._update_viewport_rotation()
        self.check_preset_match(manual_change=True)

    def on_board_tilt_input(self, event):
        self.reset_status_bar()
        self.settings.board_tilt = float(self.controls_side_panel.board_tilt_input.GetValue())
        self.controls_side_panel.board_tilt_slider.SetValue(self.settings.board_tilt)
        self._update_viewport_rotation()
        self.check_preset_match(manual_change=True)

    def on_board_roll_change(self, event):
        self.reset_status_bar()
        self.settings.board_roll = float(self.controls_side_panel.board_roll_slider.GetValue())
        self.controls_side_panel.board_roll_input.SetValue(self.settings.board_roll)
        self._update_viewport_rotation()
        self.check_preset_match(manual_change=True)

    def on_board_roll_input(self, event):
        self.reset_status_bar()
        self.settings.board_roll = float(self.controls_side_panel.board_roll_input.GetValue())
        self.controls_side_panel.board_roll_slider.SetValue(self.settings.board_roll)
        self._update_viewport_rotation()
        self.check_preset_match(manual_change=True)

    def on_spin_tilt_change(self, event):
        self.reset_status_bar()
        self.settings.spin_tilt = float(self.controls_side_panel.spin_tilt_slider.GetValue())
        self.controls_side_panel.spin_tilt_input.SetValue(self.settings.spin_tilt)
        self._update_viewport_rotation()
        self.check_preset_match(manual_change=True)

    def on_spin_tilt_input(self, event):
        self.reset_status_bar()
        self.settings.spin_tilt = float(self.controls_side_panel.spin_tilt_input.GetValue())
        self.controls_side_panel.spin_tilt_slider.SetValue(self.settings.spin_tilt)
        self._update_viewport_rotation()
        self.check_preset_match(manual_change=True)

    def on_spin_heading_change(self, event):
        self.reset_status_bar()
        self.settings.spin_heading = float(self.controls_side_panel.spin_heading_slider.GetValue())
        self.controls_side_panel.spin_heading_input.SetValue(self.settings.spin_heading)
        self._update_viewport_rotation()
        self.check_preset_match(manual_change=True)

    def on_spin_heading_input(self, event):
        self.reset_status_bar()
        self.settings.spin_heading = float(self.controls_side_panel.spin_heading_input.GetValue())
        self.controls_side_panel.spin_heading_slider.SetValue(self.settings.spin_heading)
        self._update_viewport_rotation()
        self.check_preset_match(manual_change=True)
    
    def _update_viewport_rotation(self):
        if hasattr(self.preview, 'viewport'):
            self.preview.viewport.set_universal_joint_parameters(self.settings.board_tilt, self.settings.board_roll, self.settings.spin_tilt, self.settings.spin_heading)
        self.preview.update_preview_overlay()

    def on_period_change(self, event):
        self.reset_status_bar()
        self.settings.period = round(float(self.controls_side_panel.period_slider.GetValue()), 1)
        self.controls_side_panel.period_input.SetValue(self.settings.period)
        self.controls_side_panel.frame_count.SetLabel(f"{int(self.settings.period * 30)} f")
        if hasattr(self.preview, 'viewport'):
            self.preview.viewport.set_period(self.settings.period)
        self.preview.update_preview_overlay()
        self.check_preset_match(manual_change=True)

    def on_period_input_change(self, event):
        self.reset_status_bar()
        v = round(float(self.controls_side_panel.period_input.GetValue()), 1)
        self.settings.period = v
        self.controls_side_panel.period_slider.SetValue(v)
        self.controls_side_panel.frame_count.SetLabel(f"{int(v * 30)} f")
        if hasattr(self.preview, 'viewport'):
            self.preview.viewport.set_period(v)
        self.preview.update_preview_overlay()
        self.check_preset_match(manual_change=True)
        
    def on_direction_change(self, event):
        self.reset_status_bar()
        self.settings.direction = 'cw' if self.controls_side_panel.dir_toggle.GetSelection() == 1 else 'ccw'
        if hasattr(self.preview, 'viewport'):
            self.preview.viewport.set_direction(self.settings.direction)
        self.preview.update_preview_overlay()
        self.check_preset_match(manual_change=True)

    def on_render_mode_change(self, mode_id):
        """Handle clicks on the WIREFRAME | SHADED | BOTH toggle"""
        self.settings.render_mode = mode_id
        if hasattr(self.preview, 'viewport'):
            self.preview.viewport.set_render_mode(mode_id)
        self.update_render_mode_ui(mode_id)
        self.save_settings()

    def update_render_mode_ui(self, active_mode):
        """Updates the colors of the mode toggle labels"""
        if not hasattr(self, 'render_mode_btns'): return
        for mode_id, btn in self.preview.render_mode_btns.items():
            if mode_id == active_mode:
                btn.SetForegroundColour(theme.ACCENT_CYAN)
            else:
                btn.SetForegroundColour(theme.GREY_100)
            btn.Refresh()
        
    def on_lighting_change(self, event):
        self.reset_status_bar()
        preset_id = self.controls_side_panel.light_options[self.controls_side_panel.light_toggle.GetSelection()]['id']
        self.settings.lighting = preset_id
        if hasattr(self.preview, 'viewport'):
            self.preview.viewport.set_lighting(preset_id)
        self.preview.update_preview_overlay()
        self.check_preset_match(manual_change=True)        

    def on_format_change(self, event):
        self.reset_status_bar()
        self.settings.format = self.controls_side_panel.format_ids[self.controls_side_panel.format_choice.GetSelection()]
        self.preview.update_preview_overlay()
        self.save_settings()

    def on_resolution_change(self, event):
        self.reset_status_bar()
        res = self.controls_side_panel.res_ids[self.controls_side_panel.res_choice.GetSelection()]
        self.settings.resolution = res
        
        # Update viewport aspect ratio for WYSIWYG
        try:
            w, h = map(int, res.split('x'))
            if hasattr(self.preview, 'viewport'):
                self.preview.viewport.set_aspect_ratio(w, h)
        except: pass
            
        self.preview.update_preview_overlay()
        self.save_settings()

    def on_bg_color_change(self, color_hex):
        self.reset_status_bar()
        self.settings.bg_color = color_hex
        if hasattr(self.preview, 'viewport'):
            self.preview.viewport.set_background_color(color_hex)
        self.preview.update_preview_overlay()
        self.save_settings()

    def on_advanced_options(self, event):
        self.reset_status_bar()
        from ui.dialogs import AdvancedOptionsDialog
        dlg = AdvancedOptionsDialog(self, self.settings, self.board_path)
        if dlg.ShowModal() == wx.ID_OK:
            self.save_settings()
            
        dlg.Destroy()
        self.preview.update_preview_overlay()
        pf = self.GetTopLevelParent()
        if pf: 
            pf.Raise()

    def on_cancel(self, event):
        if self.render_controller.is_rendering():
            self.render_controller.cancel()

        self.save_settings()
        f = self.GetTopLevelParent()
        if f:
            f.Close()
            
    def on_close(self, event):
        if self.render_controller.is_rendering():
            self.render_controller.cancel()

        self.save_settings()
        f = self.GetTopLevelParent()
        if f:
            f.Close()

    def on_render(self, event):
        # Check if already rendering via controller
        if self.render_controller.is_rendering():
            self.render_controller.cancel()
            self.status_msg = "STOPPING RENDER..."
            self.status_fg = theme.ACCENT_ORANGE
            self.status_bar_panel.Refresh()
            return

        # Prepare UI for rendering
        self.render_btn.SetLabel("STOP")
        self.render_btn.SetIcon("mdi-stop")
        self.render_btn.SetDanger(True)

        # Disable all controls during render
        self.enable_left_panel_controls(False)

        # Hide CANCEL and ADVANCED buttons, expand STOP button
        if hasattr(self, 'can_btn'):
            self.can_btn.Hide()
        if hasattr(self, 'adv_btn'):
            self.adv_btn.Hide()
        if hasattr(self, 'export_row_sizer'):
            self.export_row_sizer.Layout()

        # Ensure whole UI layout updates to reflect hidden buttons
        self.controls_side_panel.Layout()
        self.Layout()

        self.status_msg = "PREPARING RENDER..."
        self.status_fg = theme.ACCENT_CYAN
        self.status_prog = 0.0
        self.status_bar_panel.Refresh()

        # Start render state
        self.stop_playback()
        # Cleanup previous frame dir if it exists
        if self.last_frame_dir and os.path.exists(self.last_frame_dir):
            try:
                import shutil
                shutil.rmtree(self.last_frame_dir)
            except:
                pass
        self.last_frame_dir = None

        # IMMEDIATELY ACTIVATE RENDER PREVIEW (hides wireframe)
        self.render_preview_active = True
        self.render_preview_bitmap = None  # Clear old frame
        self.preview_manually_closed = False
        self.current_render_frame = 0
        self.total_render_frames = 0
        self.final_output_type = None

        if hasattr(self, 'render_preview_panel'):
            # Force size/pos sync before showing
            if hasattr(self.preview, 'viewport'):
                v_size = self.preview.viewport.GetSize()
                self.preview.render_preview_panel.SetSize(v_size)
                self.preview.render_preview_panel.SetPosition((0, 0))
            self.preview.render_preview_panel.Show()
            self.preview.render_preview_panel.Refresh()

        self.preview.update_preview_overlay()

        # Delegate render orchestration to controller
        self.render_controller.start_render(
            board_path=self.board_path,
            settings=self.settings,
            progress_cb=self.on_render_progress,
            complete_cb=self.on_render_finished
        )

    def on_render_progress(self, current, total, message, frame_path=None):
        wx.CallAfter(self._update_progress_ui, current, total, message, frame_path)

    def _update_progress_ui(self, current, total, message, frame_path=None):
        if not self: return
        self.status_msg = message
        self.status_prog = current / total if total > 0 else 0.0
        self.status_bar_panel.Refresh()
        
        # Update overlay frame info
        self.current_render_frame = current
        self.total_render_frames = total
        self.render_preview_active = True
        self.preview.update_preview_overlay()
        
        if frame_path and hasattr(self, 'render_preview_panel'):
            try:
                if not os.path.exists(frame_path): 
                    return
                img = wx.Image(frame_path, wx.BITMAP_TYPE_ANY)
                if img.IsOk():
                    self.render_preview_bitmap = wx.Bitmap(img)
                    if not self.preview_manually_closed:
                        # Position overlay to cover viewport exactly
                        if hasattr(self.preview, 'viewport'):
                            v_size = self.preview.viewport.GetSize()
                            self.preview.render_preview_panel.SetSize(v_size)
                            self.preview.render_preview_panel.SetPosition((0, 0))
                        if not self.preview.render_preview_panel.IsShown():
                            self.preview.render_preview_panel.Show()
                        self.preview.render_preview_panel.Refresh()
            except Exception as e:
                logger.error(f"Failed to load frame bitmap: {e}", exc_info=True)

    def on_render_finished(self, result, error=None):
        if not self: return
        # RenderController handles engine cleanup; just update UI
        self.render_btn.SetLabel("RENDER")
        self.render_btn.SetIcon("mdi-video-vintage")
        self.render_btn.SetDanger(False)
        
        # Re-enable all controls
        self.enable_left_panel_controls(True)
        
        # Restore CANCEL and ADVANCED buttons
        if hasattr(self, 'can_btn'):
            self.can_btn.Show()
        if hasattr(self, 'adv_btn'):
            self.adv_btn.Show()
        if hasattr(self, 'export_row_sizer'):
            self.export_row_sizer.Layout()
            
        # Force whole UI layout update
        self.controls_side_panel.Layout()
        self.Layout()
        
        # Give UI a moment to process button visibility changes
        wx.SafeYield()
        if not self: return
        self.controls_side_panel.Refresh()
        
        if error:
            # Only hide if no frames were actually rendered
            if not self.render_preview_bitmap:
                self.render_preview_active = False
                if hasattr(self, 'render_preview_panel'): 
                    self.preview.render_preview_panel.Hide()
            
            self.final_output_type = None
            self.status_msg = f"ERROR: {error.upper()}"
            self.status_fg = theme.ACCENT_ORANGE
            self.status_bar_color = theme.ACCENT_ORANGE
            wx.MessageBox(error, "Render Error", wx.OK | wx.ICON_ERROR)
        elif result:
            # Handle new dict return format or legacy string format
            if isinstance(result, dict):
                output_path = result.get('output')
                preview_path = result.get('preview')
                frame_dir = result.get('frame_dir')
                frame_count = result.get('frame_count')
            else:
                output_path = result
                preview_path = result
                frame_dir = None
                frame_count = 0

            self.status_msg = "RENDER COMPLETE"
            self.status_fg = theme.ACCENT_GREEN
            self.status_bar_color = theme.ACCENT_GREEN
            self.status_prog = 1.0
            
            # Start looping playback of the rendered result
            self.render_preview_active = True
            self.current_render_frame = None
            self.final_output_type = self.settings.format
            
            if hasattr(self, 'render_preview_panel'):
                if hasattr(self.preview, 'viewport'):
                    v_size = self.preview.viewport.GetSize()
                    self.preview.render_preview_panel.SetSize(v_size)
                    self.preview.render_preview_panel.SetPosition((0, 0))
                self.preview.render_preview_panel.Show()
                self.preview.render_preview_panel.Refresh()

            if frame_dir and frame_count:
                self.start_playback(frame_dir, frame_count)
            
            try:
                folder = os.path.dirname(output_path)
                if os.path.isdir(folder):
                    if wx.Platform == '__WXMSW__': 
                        os.startfile(folder)
                    elif wx.Platform == '__WXMAC__': 
                        subprocess.call(['open', folder])
                    else: 
                        subprocess.call(['xdg-open', folder])
            except Exception: 
                pass
        else:
            # Stopped manually - keep preview active if we have frames
            if self.render_preview_bitmap:
                self.render_preview_active = True
                if hasattr(self, 'render_preview_panel'):
                    self.preview.render_preview_panel.Show()
            else:
                self.render_preview_active = False
                if hasattr(self, 'render_preview_panel'):
                    self.preview.render_preview_panel.Hide()
                
            self.final_output_type = None
            self.status_msg = "RENDER STOPPED"
            self.status_fg = theme.ACCENT_ORANGE
            self.status_prog = 0.0
            
        self.preview.update_preview_overlay()
        self.status_bar_panel.Refresh()

    def on_drag_start(self, event): 
        w = event.GetEventObject(); self.drag_start_pos = w.ClientToScreen(event.GetPosition())
        f = self.GetTopLevelParent(); self.frame_start_pos = f.GetPosition(); w.CaptureMouse()
    def on_drag_motion(self, event):
        if self.drag_start_pos is None: return
        w = event.GetEventObject(); cur = w.ClientToScreen(event.GetPosition())
        delta = wx.Point(cur.x - self.drag_start_pos.x, cur.y - self.drag_start_pos.y)
        f = self.GetTopLevelParent(); f.SetPosition(wx.Point(self.frame_start_pos.x + delta.x, self.frame_start_pos.y + delta.y))
    def on_drag_end(self, event):
        w = event.GetEventObject()
        if w.HasCapture(): 
            w.ReleaseMouse()
        self.drag_start_pos = self.frame_start_pos = None
    def enable_drag(self, widget): 
        widget.Bind(wx.EVT_LEFT_DOWN, self.on_drag_start)
        widget.Bind(wx.EVT_MOTION, self.on_drag_motion)
        widget.Bind(wx.EVT_LEFT_UP, self.on_drag_end)
    def cleanup(self):
        if hasattr(self, 'viewport') and self.preview.viewport: self.preview.viewport.cleanup()
