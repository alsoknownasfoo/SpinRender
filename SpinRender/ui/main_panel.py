"""
SpinRender Main UI Panel
"""
import wx
import os
import subprocess
import logging

logger = logging.getLogger("SpinRender")

# Import theme module for centralized colors
from SpinRender.core.theme import Theme
from SpinRender.core.locale import Locale
_theme = Theme.current()
_locale = Locale.current()
from .preview_panel import PreviewPanel

# Import RenderSettings
from SpinRender.core.settings import RenderSettings
from .preset_controller import PresetController
from SpinRender.core.render_controller import RenderController
from .controls_side_panel import ControlsSidePanel
from .events import EVT_PARAMETER_INTERACTION
from .custom_controls import EVT_COLOURPICKER_CHANGED
from .status_bar import StatusBar
from .parameter_controller import ParameterController


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
            
        self.SetBackgroundColour(_theme.color("layout.main.frame.bg"))
        self.drag_start_pos = None
        self.frame_start_pos = None
        self.render_controller = RenderController()
        self.avg_frame_time = None
        self.frame_times = []

        self.build_ui()

    def build_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.top_container = wx.Panel(self)
        self.top_container.SetBackgroundColour(_theme.color("layout.main.frame.bg"))
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Left: Controls panel - instantiate ControlsSidePanel
        self.controls_side_panel = ControlsSidePanel(self.top_container, self.settings, self.board_path)
        self.controls_side_panel.Bind(EVT_PARAMETER_INTERACTION, self.on_parameter_interaction)
        # Fixed width of 450px for controls panel
        self.controls_side_panel.SetMinSize((450, -1))
        self.controls_side_panel.SetMaxSize((450, -1))
        top_sizer.Add(self.controls_side_panel, 0, wx.EXPAND)
        # Expose commonly accessed controls from side panel
        self.render_btn = self.controls_side_panel.render_btn
        self.adv_btn = self.controls_side_panel.adv_btn
        self.can_btn = self.controls_side_panel.can_btn
        self.header_close_btn = self.controls_side_panel.header_close_btn
        self.preset_buttons = self.controls_side_panel.preset_buttons

        # Center Divider
        self.center_divider = wx.Panel(self.top_container, size=(1, -1))
        self.center_divider.SetBackgroundColour(_theme.color("borders.default.color"))
        top_sizer.Add(self.center_divider, 0, wx.EXPAND)

        # Right: Preview panel
        self.preview_panel = self.create_preview_panel(self.top_container)
        # Ensure preview panel has minimum width of 700px BEFORE adding to sizer
        self.preview_panel.SetMinSize((700, -1))
        top_sizer.Add(self.preview_panel, 1, wx.EXPAND)

        self.top_container.SetSizer(top_sizer)
        top_sizer.Fit(self.top_container)
        main_sizer.Add(self.top_container, 1, wx.EXPAND)

        self.status_divider = wx.Panel(self, size=(-1, 1))
        self.status_divider.SetBackgroundColour(_theme.color("borders.default.color"))
        main_sizer.Add(self.status_divider, 0, wx.EXPAND)

        self.status_bar = StatusBar(self)
        main_sizer.Add(self.status_bar, 0, wx.EXPAND)

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

    def reapply_theme(self):
        """Orchestrate theme re-application across all sub-panels."""
        self.SetBackgroundColour(_theme.color("layout.main.frame.bg"))
        
        if hasattr(self, 'top_container'):
            self.top_container.SetBackgroundColour(_theme.color("layout.main.frame.bg"))
            
        if hasattr(self, 'center_divider'):
            self.center_divider.SetBackgroundColour(_theme.color("borders.default.color"))
            
        if hasattr(self, 'status_divider'):
            self.status_divider.SetBackgroundColour(_theme.color("borders.default.color"))
            
        # Call reapply_theme on sub-panels
        if hasattr(self, 'controls_side_panel'):
            self.controls_side_panel.reapply_theme()
            
        if hasattr(self, 'preview_panel'):
            self.preview_panel.reapply_theme()
            
        # StatusBar handles its own dynamic lookups in _on_paint
        if hasattr(self, 'status_bar'):
            self.status_bar.SetBackgroundColour(_theme.color("layout.main.status.default.bg"))
            self.status_bar.Refresh()
            self.status_bar.Update()
            
        self.Refresh()
        self.Update()

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

        # Extract additional controls for parameter controller
        param_controls = {
            'board_tilt_slider': csp.board_tilt_slider,
            'board_tilt_input': csp.board_tilt_input,
            'board_roll_slider': csp.board_roll_slider,
            'board_roll_input': csp.board_roll_input,
            'spin_tilt_slider': csp.spin_tilt_slider,
            'spin_tilt_input': csp.spin_tilt_input,
            'spin_heading_slider': csp.spin_heading_slider,
            'spin_heading_input': csp.spin_heading_input,
            'period_slider': csp.period_slider,
            'period_input': csp.period_input,
            'frame_count': csp.frame_count,
            'dir_toggle': csp.dir_toggle,
            'light_toggle': csp.light_toggle,
            'light_options': csp.light_options,
            'format_choice': csp.format_choice,
            'format_ids': csp.format_ids,
            'res_choice': csp.res_choice,
            'res_ids': csp.res_ids,
            'bg_picker': csp.bg_picker,
        }

        self.parameter_controller = ParameterController(
            settings=self.settings,
            controls=param_controls,
            preview=self.preview,
            preset_controller=self.preset_controller
        )

        # Wire parameter control events to ParameterController
        self._wire_parameter_events()

    def _wire_parameter_events(self):
        """Bind parameter control events to ParameterController methods."""
        pc = self.parameter_controller
        # Rotation controls
        self.controls_side_panel.board_tilt_slider.Bind(wx.EVT_SLIDER, pc.on_board_tilt_change)
        self.controls_side_panel.board_tilt_input.Bind(wx.EVT_TEXT_ENTER, pc.on_board_tilt_input)
        self.controls_side_panel.board_roll_slider.Bind(wx.EVT_SLIDER, pc.on_board_roll_change)
        self.controls_side_panel.board_roll_input.Bind(wx.EVT_TEXT_ENTER, pc.on_board_roll_input)
        self.controls_side_panel.spin_tilt_slider.Bind(wx.EVT_SLIDER, pc.on_spin_tilt_change)
        self.controls_side_panel.spin_tilt_input.Bind(wx.EVT_TEXT_ENTER, pc.on_spin_tilt_input)
        self.controls_side_panel.spin_heading_slider.Bind(wx.EVT_SLIDER, pc.on_spin_heading_change)
        self.controls_side_panel.spin_heading_input.Bind(wx.EVT_TEXT_ENTER, pc.on_spin_heading_input)
        # Period
        self.controls_side_panel.period_slider.Bind(wx.EVT_SLIDER, pc.on_period_change)
        self.controls_side_panel.period_input.Bind(wx.EVT_TEXT_ENTER, pc.on_period_input_change)
        # Direction
        self.controls_side_panel.dir_toggle.Bind(wx.EVT_TOGGLEBUTTON, pc.on_direction_change)
        # Lighting
        self.controls_side_panel.light_toggle.Bind(wx.EVT_TOGGLEBUTTON, pc.on_lighting_change)
        # Output format
        self.controls_side_panel.format_choice.Bind(wx.EVT_CHOICE, pc.on_format_change)
        # Resolution
        self.controls_side_panel.res_choice.Bind(wx.EVT_CHOICE, pc.on_resolution_change)
        # Background color
        if self.controls_side_panel.bg_picker:
            self.controls_side_panel.bg_picker.Bind(EVT_COLOURPICKER_CHANGED, lambda e: pc.on_bg_color_change(e.GetString()))

    def create_preview_panel(self, parent):
        """Create the preview panel using the extracted PreviewPanel component."""
        # Create the PreviewPanel component
        self.preview = PreviewPanel(parent, self.settings, self.board_path)

        # Set preview panel width to 700px
        self.preview.SetMinSize((700, -1))

        # Expose preset_buttons for overlay label overrides
        self.preview.preset_buttons = self.preset_buttons

        # Bind close button to handler
        self.preview.ov_top_right.Bind(wx.EVT_LEFT_DOWN, self.preview.on_close_render_preview)

        # Bind render mode buttons
        for mode_id, btn in self.preview.render_mode_btns.items():
            btn.Bind(wx.EVT_LEFT_DOWN, lambda e, m=mode_id: self.on_render_mode_change(m))

        # Enable drag on preview panel and its overlay widgets (excluding close button which handles its own clicks)
        self.enable_drag(self.preview)
        self.enable_drag(self.preview.ov_top_left)
        self.enable_drag(self.preview.ov_bottom_left)
        self.enable_drag(self.preview.ov_bottom_center)

        # Initial overlay update will be called by PreviewPanel constructor
        return self.preview


    def enable_parameter_controls(self, enable=True):
        """Enable or disable parameter controls during render. Export controls (render/options/cancel) are unaffected."""
        registry = self.controls_side_panel._registry
        for ctrl in registry.controls(section='presets') + \
                    registry.controls(section='parameters') + \
                    registry.controls(section='output'):
            ctrl.Enable(enable)

        if hasattr(self.controls_side_panel, 'reapply_theme'):
            self.controls_side_panel.reapply_theme()
        self.controls_side_panel.Refresh()


    def on_parameter_interaction(self, event):
        """Close render preview when an enabled parameter control is interacted with."""
        registry = self.controls_side_panel._registry
        if any(e['control'].GetId() == event.GetId() for e in registry):
            self.reset_status_bar()
        event.Skip()

    def reset_status_bar(self):
        """Resets the status bar to ready state if not currently rendering."""
        if self.render_controller.is_rendering():
            return

        # Any adjustment closes render preview
        if self.preview.render_preview_active:
            self.preview.render_preview_active = False
            self.preview.final_output_type = None
            if hasattr(self.preview, 'render_preview_panel'):
                self.preview.render_preview_panel.Hide()
            self.preview.update_preview_overlay()

        self.status_bar.reset()

    def save_settings(self):
        """Persist current settings to project-local config file."""
        from core.presets import PresetManager
        PresetManager(self.board_path).save_last_used_settings(self.settings)

    def on_preset_change(self, preset_id):
        """Delegates to PresetController."""
        if self.render_controller.is_rendering():
            return
        self.reset_status_bar()
        self.preset_controller.on_preset_change(preset_id)

    def on_save_preset(self, event=None):
        """Delegates to PresetController."""
        if self.render_controller.is_rendering():
            return
        self.reset_status_bar()
        self.preset_controller.on_save_preset(event)

    def on_render_mode_change(self, mode_id):
        """Handle clicks on the WIREFRAME | SHADED | BOTH toggle"""
        self.settings.render_mode = mode_id
        if hasattr(self.preview, 'viewport'):
            self.preview.viewport.set_render_mode(mode_id)
        self.update_render_mode_ui(mode_id)
        self.save_settings()

    def update_render_mode_ui(self, active_mode):
        """Updates the colors of the mode toggle labels - delegate to preview panel"""
        if hasattr(self.preview, 'update_render_mode_ui'):
            self.preview.update_render_mode_ui(active_mode)
        

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
            self.status_bar.set_status(_locale.get("component.status.stopping", "STOPPING RENDER..."), fg_color=_theme.color("colors.warning"))
            return

        # Prepare UI for rendering
        self.render_btn.SetStyle("exit", update_content=False)
        self.render_btn.SetLabel(_locale.get("component.button.stop.label", "STOP"))
        self.render_btn.SetIcon(_locale.get("component.button.stop.icon_ref", "stop"))

        # Disable all controls during render
        self.enable_parameter_controls(False)

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

        self.status_bar.set_status("PREPARING RENDER...", fg_color=_theme.color("colors.primary"), progress=0.0)

        # Start render state
        self.preview.stop_playback()
        # Cleanup previous frame dir if it exists
        if self.preview.last_frame_dir and os.path.exists(self.preview.last_frame_dir):
            try:
                import shutil
                shutil.rmtree(self.preview.last_frame_dir)
            except:
                pass
        self.preview.last_frame_dir = None

        # IMMEDIATELY ACTIVATE RENDER PREVIEW (hides wireframe)
        self.preview.render_preview_active = True
        self.preview.is_rendering = True
        self.preview.render_preview_bitmap = None  # Clear old frame
        self.preview.preview_manually_closed = False
        self.preview.current_render_frame = 0
        self.preview.total_render_frames = 0
        self.preview.final_output_type = None

        if hasattr(self.preview, 'render_preview_panel'):
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
        progress = current / total if total > 0 else 0.0
        self.status_bar.set_status(message, progress=progress)

        # Update overlay frame info
        self.preview.current_render_frame = current
        self.preview.total_render_frames = total
        self.preview.render_preview_active = True
        self.preview.update_preview_overlay()

        if frame_path and hasattr(self.preview, 'render_preview_panel'):
            try:
                if not os.path.exists(frame_path):
                    return
                img = wx.Image(frame_path, wx.BITMAP_TYPE_ANY)
                if img.IsOk():
                    self.preview.render_preview_bitmap = wx.Bitmap(img)
                    if not self.preview.preview_manually_closed:
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
        self.render_btn.SetStyle("render")
        
        # Re-enable all controls
        self.enable_parameter_controls(True)
        self.preview.is_rendering = False
        
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
            if not self.preview.render_preview_bitmap:
                self.preview.render_preview_active = False
                if hasattr(self.preview, 'render_preview_panel'):
                    self.preview.render_preview_panel.Hide()

            self.preview.final_output_type = None
            self.status_bar.set_error(f"ERROR: {error.upper()}")
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

            self.status_bar.set_complete()
            self.status_bar.set_status("RENDER COMPLETE", progress=1.0)

            # Start looping playback of the rendered result
            self.preview.render_preview_active = True
            self.preview.current_render_frame = None
            self.preview.final_output_type = self.settings.format

            if hasattr(self.preview, 'render_preview_panel'):
                if hasattr(self.preview, 'viewport'):
                    v_size = self.preview.viewport.GetSize()
                    self.preview.render_preview_panel.SetSize(v_size)
                    self.preview.render_preview_panel.SetPosition((0, 0))
                self.preview.render_preview_panel.Show()
                self.preview.render_preview_panel.Refresh()

            if frame_dir and frame_count:
                self.preview.start_playback(frame_dir, frame_count)

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
            if self.preview.render_preview_bitmap:
                self.preview.render_preview_active = True
                if hasattr(self.preview, 'render_preview_panel'):
                    self.preview.render_preview_panel.Show()
            else:
                self.preview.render_preview_active = False
                if hasattr(self.preview, 'render_preview_panel'):
                    self.preview.render_preview_panel.Hide()

            self.preview.final_output_type = None
            self.status_bar.set_status("RENDER STOPPED", fg_color=_theme.color("colors.warning"), progress=0.0)

        self.preview.update_preview_overlay()
        self.status_bar.Refresh()

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
        if hasattr(self.preview, 'viewport') and self.preview.viewport:
            self.preview.viewport.cleanup()
