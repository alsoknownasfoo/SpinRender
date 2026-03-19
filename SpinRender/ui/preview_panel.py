#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
PreviewPanel component extracted from SpinRenderPanel.

Encapsulates all preview-related UI: viewport, playback, render overlay.
"""
import wx
import os
from pathlib import Path
from typing import List, Optional

from .text_styles import TextStyle, TextStyles
from SpinRender.core.theme import Theme
from SpinRender.core.locale import Locale
_theme = Theme.current()
_locale = Locale.current()
from SpinRender.core.preview import GLPreviewRenderer


class PreviewPanel(wx.Panel):
    """
    Panel containing the preview viewport and its overlays.

    Responsibilities:
    - Create and manage the OpenGL viewport (GLPreviewRenderer)
    - Display information overlays (top/bottom metadata)
    - Show render preview overlay with playback
    - Handle playback animation loop
    - Expose controls for rotation, lighting, background, etc.
    """

    def __init__(self, parent, settings, board_path: str):
        """
        Initialize PreviewPanel.

        Args:
            parent: Parent wx.Window
            settings: RenderSettings object (or MagicMock/dict with required fields)
            board_path: Path to the KiCad PCB file for viewport loading
        """
        super().__init__(parent)
        self.settings = settings
        self.board_path = board_path

        # State flags
        self.render_preview_active = False
        self.preview_manually_closed = False
        self.is_rendering = False  # set by controller
        self.current_render_frame: Optional[int] = None
        self.total_render_frames: Optional[int] = None
        self.final_output_type: Optional[str] = None  # 'mp4' or 'gif'
        self.render_preview_bitmap: Optional[wx.Bitmap] = None
        self.last_frame_dir: Optional[str] = None

        # Playback state
        self.playback_timer = wx.Timer(self)
        self.playback_frames: List[str] = []
        self.playback_index = 0
        self.Bind(wx.EVT_TIMER, self.on_playback_timer, self.playback_timer)

        # Build UI
        self._create_viewport(board_path)
        self._create_overlay_widgets()
        self._setup_main_layout()
        self._initialize_from_settings()

        # Initial overlay update
        self.update_preview_overlay()

    def _create_overlay_widgets(self):
        """Create all overlay text widgets."""
        # Top overlay container
        top_meta = wx.Panel(self)
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Top-Left: Preset name OR parameters
        self.ov_top_left = wx.StaticText(top_meta, label="")
        self.ov_top_left.SetForegroundColour(_theme.color("colors.white-68"))
        self.ov_top_left.SetFont(TextStyles.label_sm.create_font())
        top_sizer.Add(self.ov_top_left, 1, wx.ALIGN_CENTER_VERTICAL)

        # Top-Right: Render mode buttons container
        self.render_mode_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.render_mode_btns = {}
        self.render_mode_divs = []

        modes = [(_locale.get("viewport.mode.wireframe", "WIREFRAME"), "wireframe"),
                 (_locale.get("viewport.mode.shaded", "SHADED"), "shaded"),
                 (_locale.get("viewport.mode.both", "BOTH"), "both")]

        for i, (label, mode_id) in enumerate(modes):
            btn = wx.StaticText(top_meta, label=label)
            btn.SetFont(TextStyle(family=_theme.font_family("mono"), size=9, weight=700).create_font())
            btn.SetCursor(wx.Cursor(wx.CURSOR_HAND))
            self.render_mode_btns[mode_id] = btn
            self.render_mode_sizer.Add(btn, 0, wx.ALIGN_CENTER_VERTICAL)

            if i < len(modes) - 1:
                div = wx.StaticText(top_meta, label="  |  ")
                div.SetFont(TextStyle(family=_theme.font_family("mono"), size=9, weight=700).create_font())
                div.SetForegroundColour(_theme.color("colors.border.default"))
                self.render_mode_divs.append(div)
                self.render_mode_sizer.Add(div, 0, wx.ALIGN_CENTER_VERTICAL)

        top_sizer.Add(self.render_mode_sizer, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)

        # Close Preview button (hidden by default)
        self.ov_top_right = wx.StaticText(top_meta, label=_locale.get("component.button.close.label", "CLOSE PREVIEW"))
        self.ov_top_right.SetForegroundColour(_theme.color("colors.accent.primary"))
        self.ov_top_right.SetFont(TextStyle(family=_theme.font_family("mono"), size=9, weight=700).create_font())
        self.ov_top_right.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        self.ov_top_right.Hide()
        top_sizer.Add(self.ov_top_right, 0, wx.ALIGN_CENTER_VERTICAL)

        top_meta.SetSizer(top_sizer)

        # Bottom overlay container
        bottom_meta = wx.Panel(self)
        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.ov_bottom_left = wx.StaticText(bottom_meta, label="")
        self.ov_bottom_left.SetForegroundColour(_theme.color("colors.white-68"))
        self.ov_bottom_left.SetFont(TextStyles.label_sm.create_font())
        bottom_sizer.Add(self.ov_bottom_left, 1, wx.ALIGN_CENTER_VERTICAL)

        self.ov_bottom_center = wx.StaticText(bottom_meta, label="")
        self.ov_bottom_center.SetForegroundColour(_theme.color("colors.white-68"))
        self.ov_bottom_center.SetFont(TextStyles.label_sm.create_font())
        bottom_sizer.Add(self.ov_bottom_center, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        self.ov_bottom_center.SetWindowStyle(wx.ST_NO_AUTORESIZE | wx.ALIGN_CENTRE_HORIZONTAL)

        self.ov_bottom_right = wx.StaticText(bottom_meta, label="")
        self.ov_bottom_right.SetForegroundColour(_theme.color("colors.accent.success"))
        self.ov_bottom_right.SetFont(TextStyles.label_sm.create_font())
        bottom_sizer.Add(self.ov_bottom_right, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        self.ov_bottom_right.SetWindowStyle(wx.ST_NO_AUTORESIZE | wx.ALIGN_RIGHT)

        bottom_meta.SetSizer(bottom_sizer)

        # Store references for later use
        self._top_meta = top_meta
        self._bottom_meta = bottom_meta

    def reapply_theme(self):
        """Re-apply theme to static overlay elements."""
        self.SetBackgroundColour(_theme.color("colors.bg.page"))

        # Overlay labels
        label_font = TextStyles.label_sm.create_font()
        for lbl in [self.ov_top_left, self.ov_bottom_left, self.ov_bottom_center]:
            lbl.SetForegroundColour(_theme.color("colors.white-68"))
            lbl.SetFont(label_font)

        self.ov_bottom_right.SetForegroundColour(_theme.color("colors.accent.success"))
        self.ov_bottom_right.SetFont(label_font)

        self.ov_top_right.SetForegroundColour(_theme.color("colors.accent.primary"))
        self.ov_top_right.SetFont(TextStyle(family=_theme.font_family("mono"), size=9, weight=700).create_font())

        # Render mode buttons
        mode_font = TextStyle(family=_theme.font_family("mono"), size=9, weight=700).create_font()
        for mode_id, btn in self.render_mode_btns.items():
            btn.SetFont(mode_font)
            # Active mode will be updated via update_render_mode_ui below

        for div in self.render_mode_divs:
            div.SetFont(mode_font)
            div.SetForegroundColour(_theme.color("colors.border.default"))

        self.update_render_mode_ui(self.settings.render_mode)
        self.update_preview_overlay()
        self.Refresh()

    def _setup_main_layout(self):
        """Set up the main sizer for PreviewPanel to manage all children."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Add top info overlay with 12px margins
        main_sizer.Add(self._top_meta, 0, wx.EXPAND | wx.ALL, 12)

        # Add viewport container with proportion=1 to fill remaining space
        main_sizer.Add(self._viewport_container, 1, wx.EXPAND)

        # Add bottom info overlay with 12px margins
        main_sizer.Add(self._bottom_meta, 0, wx.EXPAND | wx.ALL, 12)

        self.SetSizer(main_sizer)

    def _create_viewport(self, board_path: str):
        """Create the OpenGL viewport."""
        viewport_container = wx.Panel(self)
        viewport_sizer = wx.BoxSizer(wx.VERTICAL)

        self.viewport = GLPreviewRenderer(viewport_container, board_path)
        viewport_sizer.Add(self.viewport, 1, wx.EXPAND)
        viewport_container.SetSizer(viewport_sizer)

        # Render preview overlay panel (for frames after export)
        self.render_preview_panel = wx.Panel(viewport_container, style=wx.BORDER_NONE)
        self.render_preview_panel.Hide()
        self.render_preview_panel.Bind(wx.EVT_PAINT, self._on_render_preview_paint)

        # Add overlay panels as children of main panel
        # In original, they are children of viewport_container for proper layering
        # We'll keep that structure
        self._viewport_container = viewport_container

        # Keep render_preview_panel sized to match viewport_container
        viewport_container.Bind(wx.EVT_SIZE, self._on_viewport_container_size)

    def _initialize_from_settings(self):
        """Configure viewport from initial settings."""
        self.viewport.set_universal_joint_parameters(
            self.settings.board_tilt,
            self.settings.board_roll,
            self.settings.spin_tilt,
            self.settings.spin_heading
        )
        self.viewport.set_period(self.settings.period)
        self.viewport.set_direction(self.settings.direction)
        self.viewport.set_render_mode(getattr(self.settings, 'render_mode', 'both'))
        self.viewport.set_background_color(getattr(self.settings, 'bg_color', '#000000'))

        # Set aspect ratio from resolution
        try:
            w, h = map(int, self.settings.resolution.split('x'))
            self.viewport.set_aspect_ratio(w, h)
        except Exception:
            pass

        self.viewport.start_preview()

    # ------------------------------------------------------------------------
    # Public API for parent/orchestrator to call
    # ------------------------------------------------------------------------

    def update_preview_overlay(self):
        """Update overlay text based on current settings and state."""
        if not hasattr(self, 'ov_top_left'):
            return

        # Top-Left: Preset name or parameters
        preset_id = self.settings.preset
        if preset_id != 'custom':
            label = preset_id.replace('_', ' ').upper()
            # Check if preset_buttons exist and have a label override
            if hasattr(self, 'preset_buttons') and preset_id in self.preset_buttons:
                btn_label = self.preset_buttons[preset_id].label
                if btn_label and btn_label != "SELECT CUSTOM..":
                    label = btn_label
            self.ov_top_left.SetLabel(label)
        else:
            # Show raw parameters
            params = [
                f"BT:{self.settings.board_tilt:.0f}°",
                f"BR:{self.settings.board_roll:.0f}°",
                f"ST:{self.settings.spin_tilt:.0f}°",
                f"SH:{self.settings.spin_heading:.0f}°",
                f"· {self.settings.period:.1f}s"
            ]
            self.ov_top_left.SetLabel("  ".join(params))

        # Top-Right: Close button visibility
        if self.render_preview_active and not self.preview_manually_closed and not self.is_rendering:
            self.ov_top_right.Show()
            if hasattr(self, 'render_mode_sizer'):
                self.render_mode_sizer.ShowItems(False)
        else:
            self.ov_top_right.Hide()
            if hasattr(self, 'render_mode_sizer'):
                self.render_mode_sizer.ShowItems(True)

        # Bottom-Left: Lighting + BG
        lighting = getattr(self.settings, 'lighting', 'studio').upper()
        bg_hex = getattr(self.settings, 'bg_color', '#000000').upper()
        self.ov_bottom_left.SetLabel(f"{lighting} · BG:{bg_hex}")

        # Bottom-Center: Resolution, aspect ratio, FPS
        res = self.settings.resolution
        fps = "30fps"
        try:
            w, h = map(int, res.split('x'))
            aspect = w / h
            if abs(aspect - 16/9) < 0.01:
                ratio = "16:9"
            elif abs(aspect - 4/3) < 0.01:
                ratio = "4:3"
            elif abs(aspect - 1.0) < 0.01:
                ratio = "1:1"
            else:
                ratio = f"{w}:{h}"
        except Exception:
            ratio = "16:9"
        self.ov_bottom_center.SetLabel(f"{res.replace('x', ' × ')}  ·  {ratio}  ·  {fps}")

        # Bottom-Right: State info
        if self.render_preview_active and not self.preview_manually_closed:
            if self.current_render_frame is not None and self.total_render_frames:
                self.ov_bottom_right.SetLabel(f"FRAME {self.current_render_frame} / {self.total_render_frames}")
            elif self.final_output_type:
                self.ov_bottom_right.SetLabel(f"{self.final_output_type.upper()} OUTPUT")
            else:
                self.ov_bottom_right.SetLabel("RENDER PREVIEW")
        else:
            self.ov_bottom_right.SetLabel("WIREFRAME")

        self.Layout()

    def show_overlay(self, text: str = ""):
        """Show the render preview overlay."""
        if text:
            self.ov_top_left.SetLabel(text)
        self.render_preview_panel.Show()

    def hide_overlay(self):
        """Hide the render preview overlay."""
        self.render_preview_panel.Hide()

    # ------------------------------------------------------------------------
    # Playback methods
    # ------------------------------------------------------------------------

    def start_playback(self, frame_dir: str, frame_count: int):
        """
        Start looping playback of rendered frames.

        Args:
            frame_dir: Directory containing frame_0000.png, frame_0001.png, etc.
            frame_count: Number of frames to play
        """
        self.stop_playback()

        if not frame_dir or not os.path.exists(frame_dir) or frame_count <= 0:
            return

        self.playback_frames = [os.path.join(frame_dir, f"frame{i:04d}.png") for i in range(frame_count)]
        self.playback_index = 0
        self.last_frame_dir = frame_dir
        self.playback_timer.Start(33)  # ~30 fps

    def stop_playback(self):
        """Stop the looping playback."""
        if self.playback_timer.IsRunning():
            self.playback_timer.Stop()
        self.playback_frames = []
        self.playback_index = 0

    def on_playback_timer(self, event):
        """Timer event - advance to next frame."""
        if not self.playback_frames:
            self.stop_playback()
            return

        frame_path = self.playback_frames[self.playback_index]
        if os.path.exists(frame_path):
            try:
                img = wx.Image(frame_path, wx.BITMAP_TYPE_PNG)
                if img.IsOk():
                    self.render_preview_bitmap = wx.Bitmap(img)
                    self.render_preview_panel.Refresh()
            except Exception:
                pass

        self.playback_index = (self.playback_index + 1) % len(self.playback_frames)

    # ------------------------------------------------------------------------
    # Render overlay paint
    # ------------------------------------------------------------------------

    def _on_render_preview_paint(self, event):
        """Paint handler for render preview overlay."""
        dc = wx.AutoBufferedPaintDC(self.render_preview_panel)
        gc = wx.GraphicsContext.Create(dc)
        if not gc:
            return

        w, h = self.render_preview_panel.GetSize()
        bg_hex = getattr(self.settings, 'bg_color', '#000000')
        if bg_hex == 'opaque':
            bg_hex = '#000000'
        bg_color = wx.Colour(bg_hex)

        # Fill background
        gc.SetBrush(wx.Brush(bg_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRectangle(0, 0, w, h)

        if self.render_preview_bitmap and self.render_preview_bitmap.IsOk():
            bmp_w = self.render_preview_bitmap.GetWidth()
            bmp_h = self.render_preview_bitmap.GetHeight()
            if w <= 0 or h <= 0 or bmp_w <= 0 or bmp_h <= 0:
                return

            panel_aspect = w / h
            bmp_aspect = bmp_w / bmp_h

            if bmp_aspect > panel_aspect:
                display_w = w
                display_h = w / bmp_aspect
                x_offset = 0
                y_offset = (h - display_h) / 2
            else:
                display_h = h
                display_w = h * bmp_aspect
                x_offset = (w - display_w) / 2
                y_offset = 0

            gc.SetInterpolationQuality(wx.INTERPOLATION_BEST)
            gc.DrawBitmap(self.render_preview_bitmap, x_offset, y_offset, display_w, display_h)

    # ------------------------------------------------------------------------
    # Viewport container size sync
    # ------------------------------------------------------------------------

    def _on_viewport_container_size(self, event):
        """Keep render preview panel same size as viewport container."""
        if hasattr(self, 'render_preview_panel') and self.render_preview_panel.IsShown():
            container_size = self._viewport_container.GetSize()
            self.render_preview_panel.SetSize(container_size)
            self.render_preview_panel.SetPosition((0, 0))
        event.Skip()

    # ------------------------------------------------------------------------
    # Close preview handler (to be bound by parent)
    # ------------------------------------------------------------------------

    def on_close_render_preview(self, event):
        """
        Handle close preview button click.
        Note: Actual event binding is done by parent; this method can be called directly.
        """
        self.stop_playback()
        self.render_preview_active = False
        self.preview_manually_closed = True
        self.final_output_type = None
        self.render_preview_panel.Hide()
        self.update_preview_overlay()

    # ------------------------------------------------------------------------
    # Viewport control methods (called by parent/orchestrator)
    # ------------------------------------------------------------------------

    def set_rotation(self, board_tilt: float, board_roll: float, spin_tilt: float, spin_heading: float):
        """Update viewport rotation parameters."""
        self.viewport.set_universal_joint_parameters(board_tilt, board_roll, spin_tilt, spin_heading)
        self.update_preview_overlay()

    def set_period(self, period: float):
        """Update viewport spin period."""
        self.viewport.set_period(period)
        self.update_preview_overlay()

    def set_direction(self, direction: str):
        """Update viewport spin direction."""
        self.viewport.set_direction(direction)
        self.update_preview_overlay()

    def set_render_mode(self, mode: str):
        """Update viewport render mode (wireframe/shaded/both)."""
        self.viewport.set_render_mode(mode)
        self.update_preview_overlay()

    def set_background_color(self, color_hex: str):
        """Update viewport background color."""
        self.viewport.set_background_color(color_hex)
        self.update_preview_overlay()

    def set_aspect_ratio(self, width: int, height: int):
        """Update viewport aspect ratio."""
        self.viewport.set_aspect_ratio(width, height)
        self.update_preview_overlay()

    def update_render_mode_ui(self, active_mode: str):
        """
        Update colors of render mode toggle buttons.
        Called by parent when mode changes.
        """
        for mode_id, btn in self.render_mode_btns.items():
            if mode_id == active_mode:
                btn.SetForegroundColour(_theme.color("colors.accent.primary"))
            else:
                btn.SetForegroundColour(_theme.color("colors.gray-medium"))
            btn.Refresh()
