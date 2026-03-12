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
from pathlib import Path

# Use absolute imports from the plugin root for KiCad compatibility
from ui.custom_controls import (
    CustomSlider, CustomToggleButton, CustomButton,
    PresetCard, SectionLabel, NumericDisplay, NumericInput,
    get_custom_font, get_mdi_font, _OSWALD
)

# Import preview renderers
from core.preview import GLPreviewRenderer


class SVGLogoPanel(wx.Panel):
    """
    Panel that renders the SpinRender SVG logo
    """
    def __init__(self, parent, size=(58, 58)):
        super().__init__(parent, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)

        # Load SVG
        plugin_dir = Path(__file__).parent.parent
        svg_path = plugin_dir / "resources" / "logo.svg"

        if not svg_path.exists():
            svg_path = plugin_dir.parent / "res" / "logo.svg"

        self.svg_image = None
        if svg_path.exists():
            try:
                self.svg_image = wx.svg.SVGimage.CreateFromFile(str(svg_path))
            except Exception as e:
                print(f"[SpinRender] Failed to load SVG: {e}")

        self.Bind(wx.EVT_PAINT, self.on_paint)

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc:
            return

        width, height = self.GetSize()
        gc.SetBrush(wx.TRANSPARENT_BRUSH)
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRectangle(0, 0, width, height)

        if self.svg_image:
            try:
                # Render SVG at scale 1.0
                self.svg_image.RenderToGC(gc, 1.0)
            except Exception:
                gc.SetBrush(wx.Brush(wx.Colour(0, 188, 212)))
                gc.DrawRectangle(0, 0, width, height)


class SpinRenderPanel(wx.Panel):
    """
    Main SpinRender UI panel with two-panel layout
    """

    BG_PAGE = wx.Colour(18, 18, 18)
    BG_PANEL = wx.Colour(26, 26, 26)
    BG_INPUT = wx.Colour(13, 13, 13)
    BG_SURFACE = wx.Colour(34, 34, 34)
    TEXT_PRIMARY = wx.Colour(224, 224, 224)
    TEXT_SECONDARY = wx.Colour(119, 119, 119)
    TEXT_MUTED = wx.Colour(85, 85, 85)
    ACCENT_CYAN = wx.Colour(0, 188, 212)
    ACCENT_YELLOW = wx.Colour(255, 214, 0)
    ACCENT_GREEN = wx.Colour(76, 175, 80)
    ACCENT_ORANGE = wx.Colour(255, 107, 53)
    BORDER_DEFAULT = wx.Colour(51, 51, 51)

    def __init__(self, parent, board_path):
        super().__init__(parent)
        self.board_path = board_path
        self.board_dir = os.path.dirname(board_path)
        
        # Default settings
        self.settings = {
            'preset': 'hero',
            'board_tilt': 0.0,
            'board_roll': -45.0,
            'spin_tilt': 90.0,
            'spin_heading': 90.0,
            'period': 10.0, 
            'easing': 'linear', 
            'direction': 'ccw', 
            'lighting': 'studio',
            'format': 'mp4', 
            'resolution': '1920x1080', 
            'output_auto': True,
            'output_path': '', 
            'cli_overrides': ''
        }
        
        # Attempt to load last used settings
        from core.presets import PresetManager
        manager = PresetManager(self.board_path)
        last_settings = manager.get_last_used_settings()
        if last_settings:
            self.settings.update(last_settings)
            
        self.SetBackgroundColour(self.BG_PAGE)
        self.drag_start_pos = None
        self.frame_start_pos = None
        self.is_rendering = False
        self.render_engine = None
        self.avg_frame_time = None
        self.frame_times = []
        
        # Status state for custom paint
        self.status_msg = "READY"
        self.status_fg = self.ACCENT_GREEN
        self.status_prog = 0.0
        self.status_bar_color = self.ACCENT_CYAN
        
        # Initialize render state tracking
        self.render_preview_active = False
        self.current_render_frame = None
        self.total_render_frames = None
        self.final_output_type = None # 'mp4' or 'gif'
        self.render_preview_bitmap = None
        self.preview_manually_closed = False
        
        # Playback state for looped preview
        self.playback_timer = wx.Timer(self)
        self.playback_frames = []
        self.playback_index = 0
        self.last_frame_dir = None
        self.Bind(wx.EVT_TIMER, self.on_playback_timer, self.playback_timer)
        
        self.build_ui()

    def build_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        top_panel = wx.Panel(self)
        top_panel.SetBackgroundColour(self.BG_PAGE)
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Left: Controls panel
        self.controls_panel = self.create_controls_panel(top_panel)
        top_sizer.Add(self.controls_panel, 0, wx.EXPAND)

        # Center Divider
        divider = wx.Panel(top_panel, size=(1, -1))
        divider.SetBackgroundColour(self.BORDER_DEFAULT)
        top_sizer.Add(divider, 0, wx.EXPAND)

        # Right: Preview panel
        self.preview_panel = self.create_preview_panel(top_panel)
        top_sizer.Add(self.preview_panel, 0, wx.EXPAND | wx.FIXED_MINSIZE)

        top_panel.SetSizer(top_sizer)
        top_sizer.Fit(top_panel)
        main_sizer.Add(top_panel, 1, wx.EXPAND)
        
        status_divider = wx.Panel(self, size=(-1, 1))
        status_divider.SetBackgroundColour(self.BORDER_DEFAULT)
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
            
        self.check_preset_match(manual_change=False)

    def create_controls_panel(self, parent):
        panel = scrolled.ScrolledPanel(parent, size=(450, -1))
        panel.SetBackgroundColour(self.BG_PAGE)
        panel.SetupScrolling(scroll_x=False, scroll_y=True, rate_y=20)
        sizer = wx.BoxSizer(wx.VERTICAL)

        padding = 16
        
        header = self.create_header(panel)
        sizer.Add(header, 0, wx.EXPAND)
        
        div1 = wx.Panel(panel, size=(-1, 1))
        div1.SetBackgroundColour(self.BORDER_DEFAULT)
        sizer.Add(div1, 0, wx.EXPAND)
        
        presets = self.create_preset_section(panel)
        sizer.Add(presets, 0, wx.EXPAND | wx.ALL, padding)
        
        div2 = wx.Panel(panel, size=(-1, 1))
        div2.SetBackgroundColour(self.BORDER_DEFAULT)
        sizer.Add(div2, 0, wx.EXPAND)
        
        params = self.create_parameters_section(panel)
        sizer.Add(params, 0, wx.EXPAND | wx.ALL, padding)
        
        div3 = wx.Panel(panel, size=(-1, 1))
        div3.SetBackgroundColour(self.BORDER_DEFAULT)
        sizer.Add(div3, 0, wx.EXPAND)
        
        output_settings = self.create_output_settings_section(panel)
        sizer.Add(output_settings, 1, wx.EXPAND | wx.ALL, padding)
        
        div4 = wx.Panel(panel, size=(-1, 1))
        div4.SetBackgroundColour(self.BORDER_DEFAULT)
        sizer.Add(div4, 0, wx.EXPAND)
        
        export = self.create_export_section(panel)
        sizer.Add(export, 0, wx.EXPAND | wx.ALL, padding)

        panel.SetSizer(sizer)
        required_h = sizer.CalcMin().y + 40
        panel.SetMinSize((450, required_h))
        sizer.Fit(panel)
        return panel

    def create_header(self, parent):
        header = wx.Panel(parent, size=(-1, 90))
        header.SetBackgroundColour(self.BG_PANEL)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        logo = SVGLogoPanel(header, size=(58, 58))
        sizer.Add(logo, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 16)

        title_sizer = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(header, label="SPINRENDER")
        title.SetForegroundColour(self.TEXT_PRIMARY)
        title.SetFont(get_custom_font(18, family_name=_OSWALD, weight=wx.FONTWEIGHT_BOLD))
        title_sizer.Add(title, 0)

        subtitle = wx.StaticText(header, label="0.9 alpha")
        subtitle.SetForegroundColour(self.ACCENT_CYAN)
        subtitle.SetFont(wx.Font(8, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="JetBrains Mono"))
        title_sizer.Add(subtitle, 0)
        sizer.Add(title_sizer, 0, wx.ALIGN_CENTER_VERTICAL)

        sizer.AddStretchSpacer()
        self.header_close_btn = CustomButton(header, label="", icon='mdi-close', primary=False, ghost=True, icon_color=wx.Colour(85, 85, 85), size=(36, 36))
        self.header_close_btn.Bind(wx.EVT_BUTTON, self.on_close)
        sizer.Add(self.header_close_btn, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 16)

        header.SetSizerAndFit(sizer)
        self.enable_drag(header)
        return header

    def create_preset_section(self, parent):
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(self.BG_PAGE)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.create_section_label(panel, "LOOP PRESET"), 0, wx.EXPAND | wx.BOTTOM, 8)

        preset_row = wx.Panel(panel)
        preset_sizer = wx.BoxSizer(wx.HORIZONTAL)
        presets_data = [
            ("hero", "HERO", "mdi-rotate-cw"), 
            ("spin", "SPIN", "mdi-rotate-360"), 
            ("flip", "FLIP", "mdi-rotate-orbit"), 
            ("custom", "SELECT CUSTOM..", "mdi-star-settings-outline")
        ]
        self.preset_buttons = {}
        for i, (pid, lbl, ico) in enumerate(presets_data):
            btn = PresetCard(preset_row, label=lbl, icon_name=ico, size=(90, 64))
            btn.Bind(wx.EVT_BUTTON, lambda e, p=pid: self.on_preset_change(p))
            if self.settings['preset'] == pid: 
                btn.SetSelected(True)
            self.preset_buttons[pid] = btn
            flags = wx.EXPAND
            if i < len(presets_data) - 1: 
                flags |= wx.RIGHT
            preset_sizer.Add(btn, 1, flags, 8)
        
        preset_row.SetSizerAndFit(preset_sizer)
        sizer.Add(preset_row, 0, wx.EXPAND)
        panel.SetSizerAndFit(sizer)
        return panel

    def create_parameters_section(self, parent):
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(self.BG_PAGE)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        header = wx.Panel(panel)
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        header_sizer.Add(self.create_section_label(header, "PARAMETERS"), 1, wx.ALIGN_CENTER_VERTICAL)
        save_btn = CustomButton(header, label="+ SAVE PRESET", primary=False, size=(120, 28))
        save_btn.Bind(wx.EVT_BUTTON, self.on_save_preset)
        header_sizer.Add(save_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        header.SetSizerAndFit(header_sizer)
        
        sizer.Add(header, 0, wx.EXPAND | wx.BOTTOM, 10)
        sizer.Add(self.create_rotation_controls(panel), 0, wx.EXPAND | wx.BOTTOM, 10)
        sizer.Add(self.create_period_control(panel), 0, wx.EXPAND | wx.BOTTOM, 10)
        sizer.Add(self.create_direction_control(panel), 0, wx.EXPAND | wx.BOTTOM, 10)
        sizer.Add(self.create_lighting_control(panel), 0, wx.EXPAND)

        panel.SetSizerAndFit(sizer)
        return panel

    def create_rotation_controls(self, parent):
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(panel, label="ROTATION SETTINGS")
        label.SetForegroundColour(self.TEXT_PRIMARY)
        label.SetFont(wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_SEMIBOLD, faceName="JetBrains Mono"))
        sizer.Add(label, 0, wx.BOTTOM, 6)

        cols = [wx.Colour(255, 107, 107), wx.Colour(255, 180, 107), wx.Colour(77, 150, 255), wx.Colour(170, 107, 255)]
        icons = ["mdi-axis-x-arrow", "mdi-axis-y-arrow", "mdi-axis-y-rotate-counterclockwise", "mdi-axis-z-rotate-counterclockwise"]
        
        row1 = self.create_axis_control(panel, "BOARD TILT", self.settings['board_tilt'], cols[0], icons[0], -90, 90, self.on_board_tilt_change, self.on_board_tilt_input)
        sizer.Add(row1, 0, wx.EXPAND | wx.BOTTOM, 4)
        row2 = self.create_axis_control(panel, "BOARD ROLL", self.settings['board_roll'], cols[1], icons[1], -180, 180, self.on_board_roll_change, self.on_board_roll_input)
        sizer.Add(row2, 0, wx.EXPAND | wx.BOTTOM, 4)
        row3 = self.create_axis_control(panel, "SPIN TILT", self.settings['spin_tilt'], cols[2], icons[2], -90, 90, self.on_spin_tilt_change, self.on_spin_tilt_input)
        sizer.Add(row3, 0, wx.EXPAND | wx.BOTTOM, 4)
        row4 = self.create_axis_control(panel, "SPIN HEADING", self.settings['spin_heading'], cols[3], icons[3], -180, 180, self.on_spin_heading_change, self.on_spin_heading_input)
        sizer.Add(row4, 0, wx.EXPAND | wx.BOTTOM, 4)

        desc = wx.StaticText(panel, label="BOARD: ORIENT ON SPINDLE | SPIN: ORIENT THE SPINDLE ITSELF")
        desc.SetForegroundColour(self.TEXT_MUTED)
        desc.SetFont(wx.Font(8, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="JetBrains Mono"))
        sizer.Add(desc, 0)
        panel.SetSizerAndFit(sizer)
        return panel

    def create_axis_control(self, parent, label_text, def_val, col, icon_name, min_val, max_val, s_hand, i_hand):
        row = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        label_part = wx.Panel(row, size=(130, -1))
        lp_sizer = wx.BoxSizer(wx.HORIZONTAL)
        mdi_icons = {
            'mdi-axis-x-arrow': '\U000F0D4C', 
            'mdi-axis-y-arrow': '\U000F0D51', 
            'mdi-axis-y-rotate-counterclockwise': '\U000F0D54', 
            'mdi-axis-z-rotate-counterclockwise': '\U000F0D58'
        }
        icon_char = mdi_icons.get(icon_name, '')
        if icon_char:
            icon_lbl = wx.StaticText(label_part, label=icon_char)
            icon_lbl.SetForegroundColour(col)
            icon_lbl.SetFont(get_mdi_font(14))
            lp_sizer.Add(icon_lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        lbl = wx.StaticText(label_part, label=f"{label_text}:")
        lbl.SetForegroundColour(col)
        lbl.SetFont(wx.Font(9, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, faceName="JetBrains Mono"))
        lp_sizer.Add(lbl, 0, wx.ALIGN_CENTER_VERTICAL)
        label_part.SetSizer(lp_sizer)
        sizer.Add(label_part, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        
        slider = CustomSlider(row, value=def_val, min_val=min_val, max_val=max_val, size=(-1, 18), color=col)
        slider.Bind(wx.EVT_SLIDER, s_hand)
        sizer.Add(slider, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        
        inp = self.create_numeric_input(row, f"{def_val:.2f}", "°", editable=True, min_val=min_val, max_val=max_val)
        inp.Bind(wx.EVT_TEXT_ENTER, i_hand)
        sizer.Add(inp, 0, wx.ALIGN_CENTER_VERTICAL)
        
        attr_name = label_text.lower().replace(" ", "_")
        setattr(self, f"{attr_name}_slider", slider)
        setattr(self, f"{attr_name}_input", inp)
        row.SetSizerAndFit(sizer)
        return row

    def create_period_control(self, parent):
        panel = wx.Panel(panel if 'panel' in locals() else parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        lbl = wx.StaticText(panel, label="ROTATION PERIOD")
        lbl.SetForegroundColour(self.TEXT_PRIMARY)
        lbl.SetFont(wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_SEMIBOLD, faceName="JetBrains Mono"))
        sizer.Add(lbl, 0, wx.BOTTOM, 6)
        
        crow = wx.Panel(panel)
        csizer = wx.BoxSizer(wx.HORIZONTAL)
        p_val = self.settings.get('period', 10.0)
        self.period_slider = CustomSlider(crow, value=p_val, min_val=0.1, max_val=30, size=(-1, 18))
        self.period_slider.Bind(wx.EVT_SLIDER, self.on_period_change)
        csizer.Add(self.period_slider, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.period_input = self.create_numeric_input(crow, f"{p_val:.1f}", "sec", editable=True, min_val=0.1, max_val=30)
        self.period_input.Bind(wx.EVT_TEXT_ENTER, self.on_period_input_change)
        csizer.Add(self.period_input, 0, wx.ALIGN_CENTER_VERTICAL)
        crow.SetSizerAndFit(csizer)
        sizer.Add(crow, 0, wx.EXPAND | wx.BOTTOM, 6)
        
        mrow = wx.Panel(panel)
        msizer = wx.BoxSizer(wx.HORIZONTAL)
        desc = wx.StaticText(mrow, label="SPEED OF 360° SPIN")
        desc.SetForegroundColour(self.TEXT_MUTED)
        desc.SetFont(wx.Font(8, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="JetBrains Mono"))
        msizer.Add(desc, 1)
        self.frame_count = wx.StaticText(mrow, label=f"{int(p_val * 30)} f")
        self.frame_count.SetForegroundColour(self.TEXT_SECONDARY)
        self.frame_count.SetFont(wx.Font(8, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="JetBrains Mono"))
        msizer.Add(self.frame_count, 0)
        mrow.SetSizerAndFit(msizer)
        sizer.Add(mrow, 0, wx.EXPAND)
        panel.SetSizerAndFit(sizer)
        return panel

    def create_direction_control(self, parent):
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        lbl = wx.StaticText(panel, label="DIRECTION")
        lbl.SetForegroundColour(self.TEXT_PRIMARY)
        lbl.SetFont(wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_SEMIBOLD, faceName="JetBrains Mono"))
        sizer.Add(lbl, 0, wx.BOTTOM, 6)
        dir_options = [{'label': 'CCW', 'icon': 'mdi-restore'}, {'label': 'CW', 'icon': 'mdi-reload'}]
        self.dir_toggle = CustomToggleButton(panel, options=dir_options, size=(210, 32))
        initial_idx = 1 if self.settings.get('direction') == 'cw' else 0
        self.dir_toggle.SetSelection(initial_idx)
        self.dir_toggle.Bind(wx.EVT_TOGGLEBUTTON, self.on_direction_change)
        sizer.Add(self.dir_toggle, 0)
        panel.SetSizerAndFit(sizer)
        return panel

    def create_lighting_control(self, parent):
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        lbl = wx.StaticText(panel, label="LIGHTING")
        lbl.SetForegroundColour(self.TEXT_PRIMARY)
        lbl.SetFont(wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_SEMIBOLD, faceName="JetBrains Mono"))
        sizer.Add(lbl, 0, wx.BOTTOM, 6)
        self.light_options = [
            {'id': 'studio', 'label': 'STUDIO', 'icon': 'mdi-weather-sunny'}, 
            {'id': 'dramatic', 'label': 'DRAMATIC', 'icon': 'mdi-lightning-bolt'}, 
            {'id': 'soft', 'label': 'SOFT', 'icon': 'mdi-image-filter-drama-outline'}, 
            {'id': 'none', 'label': 'NONE', 'icon': 'mdi-circle-off-outline'}
        ]
        self.light_toggle = CustomToggleButton(panel, options=self.light_options, size=(320, 32), active_color=self.ACCENT_YELLOW)
        current_light = self.settings.get('lighting', 'studio')
        initial_idx = next((i for i, opt in enumerate(self.light_options) if opt['id'] == current_light), 0)
        self.light_toggle.SetSelection(initial_idx)
        self.light_toggle.Bind(wx.EVT_TOGGLEBUTTON, self.on_lighting_change)
        sizer.Add(self.light_toggle, 0, wx.EXPAND)
        panel.SetSizerAndFit(sizer)
        return panel

    def create_output_settings_section(self, parent):
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(self.BG_PAGE)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.create_section_label(panel, "OUTPUT SETTINGS"), 0, wx.EXPAND | wx.BOTTOM, 10)
        cols_panel = wx.Panel(panel)
        cols_sizer = wx.BoxSizer(wx.HORIZONTAL)
        from ui.custom_controls import CustomDropdown
        f_col = wx.Panel(cols_panel)
        f_sizer = wx.BoxSizer(wx.VERTICAL)
        f_lbl = wx.StaticText(f_col, label="FORMAT")
        f_lbl.SetForegroundColour(self.TEXT_PRIMARY)
        f_lbl.SetFont(wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_SEMIBOLD, faceName="JetBrains Mono"))
        f_sizer.Add(f_lbl, 0, wx.BOTTOM, 6)
        self.format_choices = ["MP4 (H.264)", "GIF", "PNG Sequence"]
        self.format_ids = ["mp4", "gif", "png_sequence"]
        self.format_choice = CustomDropdown(f_col, choices=self.format_choices, size=(-1, 32))
        curr_fmt = self.settings.get('format', 'mp4')
        fmt_idx = self.format_ids.index(curr_fmt) if curr_fmt in self.format_ids else 0
        self.format_choice.SetSelection(fmt_idx)
        self.format_choice.Bind(wx.EVT_CHOICE, self.on_format_change)
        f_sizer.Add(self.format_choice, 0, wx.EXPAND)
        f_col.SetSizerAndFit(f_sizer)
        cols_sizer.Add(f_col, 1, wx.EXPAND | wx.RIGHT, 12)
        r_col = wx.Panel(cols_panel)
        r_sizer = wx.BoxSizer(wx.VERTICAL)
        r_lbl = wx.StaticText(r_col, label="RESOLUTION")
        r_lbl.SetForegroundColour(self.TEXT_PRIMARY)
        r_lbl.SetFont(wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_SEMIBOLD, faceName="JetBrains Mono"))
        r_sizer.Add(r_lbl, 0, wx.BOTTOM, 6)
        self.res_choices = ["1920×1080 (1080P)", "1280×720 (720P)", "800×600 (Square)"]
        self.res_ids = ["1920x1080", "1280x720", "800x600"]
        self.res_choice = CustomDropdown(r_col, choices=self.res_choices, size=(-1, 32))
        curr_res = self.settings.get('resolution', '1920x1080')
        res_idx = self.res_ids.index(curr_res) if curr_res in self.res_ids else 0
        self.res_choice.SetSelection(res_idx)
        self.res_choice.Bind(wx.EVT_CHOICE, self.on_resolution_change)
        r_sizer.Add(self.res_choice, 0, wx.EXPAND)
        r_col.SetSizerAndFit(r_sizer)
        cols_sizer.Add(r_col, 1, wx.EXPAND)
        cols_panel.SetSizerAndFit(cols_sizer)
        sizer.Add(cols_panel, 0, wx.EXPAND)
        panel.SetSizerAndFit(sizer)
        return panel

    def create_export_section(self, parent):
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddStretchSpacer()
        arow = wx.Panel(panel)
        asizer = wx.BoxSizer(wx.HORIZONTAL)
        self.adv_btn = CustomButton(arow, label="", icon='mdi-cog', primary=False, size=(36, 36))
        self.adv_btn.Bind(wx.EVT_BUTTON, self.on_advanced_options)
        asizer.Add(self.adv_btn, 0, wx.RIGHT, 8)
        self.can_btn = CustomButton(arow, label="CANCEL", icon='mdi-close', primary=False, danger=True, size=(110, 36))
        self.can_btn.Bind(wx.EVT_BUTTON, self.on_cancel)
        asizer.Add(self.can_btn, 0, wx.RIGHT, 8)
        self.render_btn = CustomButton(arow, label="RENDER", icon='mdi-video-vintage', primary=True, size=(150, 36))
        self.render_btn.Bind(wx.EVT_BUTTON, self.on_render)
        asizer.Add(self.render_btn, 1, wx.EXPAND)
        arow.SetSizerAndFit(asizer)
        self.export_row_sizer = asizer
        sizer.Add(arow, 0, wx.EXPAND)
        panel.SetSizerAndFit(sizer)
        return panel

    def create_preview_panel(self, parent):
        panel = wx.Panel(parent, size=(700, -1))
        panel.SetBackgroundColour(wx.Colour(10, 10, 10))
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # --- TOP OVERLAY ---
        top_meta = wx.Panel(panel)
        top_meta_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Top-Left: Parameters OR Preset Name
        self.ov_top_left = wx.StaticText(top_meta, label="")
        self.ov_top_left.SetForegroundColour(wx.Colour(255, 255, 255, 68))
        self.ov_top_left.SetFont(wx.Font(9, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="JetBrains Mono"))
        top_meta_sizer.Add(self.ov_top_left, 1, wx.ALIGN_CENTER_VERTICAL)
        
        # Top-Right: CLOSE PREVIEW button
        self.ov_top_right = wx.StaticText(top_meta, label="CLOSE PREVIEW")
        self.ov_top_right.SetForegroundColour(self.ACCENT_CYAN)
        self.ov_top_right.SetFont(wx.Font(9, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, faceName="JetBrains Mono"))
        self.ov_top_right.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        self.ov_top_right.Hide()
        self.ov_top_right.Bind(wx.EVT_LEFT_DOWN, self.on_close_render_preview)
        top_meta_sizer.Add(self.ov_top_right, 0, wx.ALIGN_CENTER_VERTICAL)
        
        top_meta.SetSizerAndFit(top_meta_sizer)
        sizer.Add(top_meta, 0, wx.EXPAND | wx.ALL, 12)

        # --- VIEWPORT CONTAINER ---
        viewport_container = wx.Panel(panel)
        viewport_container.SetBackgroundColour(wx.Colour(0, 0, 0))
        viewport_sizer = wx.BoxSizer(wx.VERTICAL)

        self.viewport = GLPreviewRenderer(viewport_container, self.board_path)
        viewport_sizer.Add(self.viewport, 1, wx.EXPAND)
        viewport_container.SetSizer(viewport_sizer)

        # Render preview overlay panel
        self.render_preview_panel = wx.Panel(viewport_container, style=wx.BORDER_NONE)
        self.render_preview_panel.SetBackgroundColour(wx.Colour(0, 0, 0))
        self.render_preview_panel.Hide()
        self.render_preview_panel.Bind(wx.EVT_PAINT, self._on_render_preview_paint)

        sizer.Add(viewport_container, 1, wx.EXPAND)
        
        # --- BOTTOM OVERLAY ---
        bottom_meta = wx.Panel(panel)
        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Bottom-Left: Lighting + BG
        self.ov_bottom_left = wx.StaticText(bottom_meta, label="")
        self.ov_bottom_left.SetForegroundColour(wx.Colour(255, 255, 255, 68))
        self.ov_bottom_left.SetFont(wx.Font(9, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="JetBrains Mono"))
        bottom_sizer.Add(self.ov_bottom_left, 1, wx.ALIGN_CENTER_VERTICAL)
        
        # Bottom-Center: Res + Ratio + FPS
        self.ov_bottom_center = wx.StaticText(bottom_meta, label="")
        self.ov_bottom_center.SetForegroundColour(wx.Colour(255, 255, 255, 68))
        self.ov_bottom_center.SetFont(wx.Font(9, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="JetBrains Mono"))
        bottom_sizer.Add(self.ov_bottom_center, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        self.ov_bottom_center.SetWindowStyle(wx.ST_NO_AUTORESIZE | wx.ALIGN_CENTRE_HORIZONTAL)
        
        # Bottom-Right: State Info
        self.ov_bottom_right = wx.StaticText(bottom_meta, label="")
        self.ov_bottom_right.SetForegroundColour(self.ACCENT_GREEN)
        self.ov_bottom_right.SetFont(wx.Font(9, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="JetBrains Mono"))
        bottom_sizer.Add(self.ov_bottom_right, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        self.ov_bottom_right.SetWindowStyle(wx.ST_NO_AUTORESIZE | wx.ALIGN_RIGHT)
        
        bottom_meta.SetSizerAndFit(bottom_sizer)
        sizer.Add(bottom_meta, 0, wx.EXPAND | wx.ALL, 12)
        
        panel.SetSizer(sizer)
        panel.SetMinSize((700, -1))
        panel.SetMaxSize((700, -1))
        
        # Drag enabling - exclude the close preview button so it can handle its own clicks
        for w in [panel, self.viewport, top_meta, self.ov_top_left, bottom_meta, self.ov_bottom_left, self.ov_bottom_center, self.ov_bottom_right]: 
            self.enable_drag(w)
            
        self.viewport.set_universal_joint_parameters(self.settings['board_tilt'], self.settings['board_roll'], self.settings['spin_tilt'], self.settings['spin_heading'])
        self.viewport.set_period(self.settings['period'])
        self.viewport.set_direction(self.settings['direction'])
        self.viewport.start_preview()
        
        # Initial update
        self.update_preview_overlay()
        
        return panel

    def update_preview_overlay(self):
        """Clean layout update for the preview information overlay"""
        if not hasattr(self, 'ov_top_left'): return

        # --- Top-Left: Parameters OR Preset Name ---
        preset_id = self.settings.get('preset', 'custom')
        if preset_id != 'custom':
            label = preset_id.replace('_', ' ').upper()
            if hasattr(self, 'preset_buttons') and preset_id in self.preset_buttons:
                btn_label = self.preset_buttons[preset_id].label
                if btn_label and btn_label != "SELECT CUSTOM..":
                    label = btn_label
            self.ov_top_left.SetLabel(label)
        else:
            # Show raw parameters
            params = [
                f"BT:{self.settings.get('board_tilt', 0):.0f}°",
                f"BR:{self.settings.get('board_roll', 0):.0f}°",
                f"ST:{self.settings.get('spin_tilt', 0):.0f}°",
                f"SH:{self.settings.get('spin_heading', 0):.0f}°",
                f"· {self.settings.get('period', 10):.1f}s"
            ]
            self.ov_top_left.SetLabel("  ".join(params))

        # --- Top-Right: CLOSE PREVIEW button ---
        if self.render_preview_active and not self.preview_manually_closed and not self.is_rendering:
            self.ov_top_right.Show()
        else:
            self.ov_top_right.Hide()

        # --- Bottom-Left: Lighting + BG color ---
        lighting = self.settings.get('lighting', 'studio').upper()
        self.ov_bottom_left.SetLabel(f"{lighting} · BG:BLACK")

        # --- Bottom-Center: Resolution + Ratio + FPS ---
        res = self.settings.get('resolution', '1920x1080')
        fps = "30fps"
        try:
            parts = res.split('x')
            if len(parts) == 2:
                w, h = map(int, parts)
                if abs(w/h - 16/9) < 0.01: ratio = "16:9"
                elif abs(w/h - 4/3) < 0.01: ratio = "4:3"
                elif w == h: ratio = "1:1"
                else: ratio = f"{w}:{h}"
            else: ratio = "16:9"
        except: ratio = "16:9"
        self.ov_bottom_center.SetLabel(f"{res.replace('x', ' × ')}  ·  {ratio}  ·  {fps}")

        # --- Bottom-Right: State Info ---
        if self.render_preview_active and not self.preview_manually_closed:
            if self.current_render_frame is not None:
                self.ov_bottom_right.SetLabel(f"FRAME {self.current_render_frame} / {self.total_render_frames}")
            elif self.final_output_type:
                self.ov_bottom_right.SetLabel(f"{self.final_output_type.upper()} OUTPUT")
            else:
                self.ov_bottom_right.SetLabel("RENDER PREVIEW")
        else:
            self.ov_bottom_right.SetLabel("WIREFRAME")

        self.Layout()

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
        
        process_widget(self.controls_panel)
        
        # Header close button should NEVER be disabled
        if hasattr(self, 'header_close_btn'):
            self.header_close_btn.Enable(True)
        
        # Force a refresh of all controls to update their visual state
        self.controls_panel.Refresh()

    def on_close_render_preview(self, event):
        """Hides the render overlay and resets to wireframe state"""
        self.stop_playback()
        self.render_preview_active = False
        self.preview_manually_closed = True
        self.final_output_type = None
        if hasattr(self, 'render_preview_panel'):
            self.render_preview_panel.Hide()
        self.update_preview_overlay()

    def start_playback(self, frame_dir, frame_count):
        """Starts looping playback of rendered frames"""
        self.stop_playback() # Ensure clean state
        
        if not frame_dir or not os.path.exists(frame_dir) or frame_count <= 0:
            return
            
        self.playback_frames = [os.path.join(frame_dir, f"frame{i:04d}.png") for i in range(frame_count)]
        self.playback_index = 0
        self.last_frame_dir = frame_dir
        
        # Start at 30fps
        self.playback_timer.Start(33)

    def stop_playback(self):
        """Stops the looping playback"""
        if self.playback_timer.IsRunning():
            self.playback_timer.Stop()
        self.playback_frames = []
        self.playback_index = 0

    def on_playback_timer(self, event):
        """Cycle through frames for looping preview"""
        if not self.playback_frames:
            self.stop_playback()
            return
            
        frame_path = self.playback_frames[self.playback_index]
        if os.path.exists(frame_path):
            try:
                img = wx.Image(frame_path, wx.BITMAP_TYPE_PNG)
                if img.IsOk():
                    self.render_preview_bitmap = wx.Bitmap(img)
                    if hasattr(self, 'render_preview_panel'):
                        self.render_preview_panel.Refresh()
            except Exception:
                pass
                
        self.playback_index = (self.playback_index + 1) % len(self.playback_frames)

    def on_left_panel_interaction(self, event):
        """Handle clicks on active controls in left panel to close preview"""
        # Only close if the control we clicked is actually enabled
        obj = event.GetEventObject()
        if obj and obj.IsEnabled():
            self.reset_status_bar()
        event.Skip()

    def _on_render_preview_paint(self, _event):
        """Paint handler for render preview overlay using GraphicsContext for high-DPI sharpness"""
        dc = wx.AutoBufferedPaintDC(self.render_preview_panel)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        w, h = self.render_preview_panel.GetSize()
        gc.SetBrush(wx.Brush(wx.Colour(0, 0, 0)))
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
            gc.SetInterpolationQuality(wx.INTERPOLATION_BEST)
            gc.DrawBitmap(self.render_preview_bitmap, x_offset, y_offset, display_width, display_height)
            
            # Draw faint gray outline around the render
            gc.SetBrush(wx.TRANSPARENT_BRUSH)
            gc.SetPen(wx.Pen(wx.Colour(255, 255, 255, 30), 1))
            gc.DrawRectangle(x_offset, y_offset, display_width, display_height)
        else:
            # Draw empty outline matching resolution if no bitmap yet
            # Calculate Display Dimensions based on current settings resolution
            try:
                parts = self.settings.get('resolution', '1920x1080').split('x')
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
                gc.SetPen(wx.Pen(wx.Colour(255, 255, 255, 30), 1))
                gc.DrawRectangle(ox, oy, dw, dh)
            except: pass

    def create_status_bar(self, parent):
        panel = wx.Panel(parent, size=(-1, 25))
        panel.SetBackgroundColour(self.BG_PANEL)
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
        gc.SetBrush(wx.Brush(self.BG_PANEL))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRectangle(0, 0, w, h)
        font = wx.Font(8, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="JetBrains Mono")
        gc.SetFont(font, self.status_fg)
        tw, th = gc.GetTextExtent(self.status_msg)
        tx, ty = 10, (h - th) / 2
        gc.DrawText(self.status_msg, tx, ty)
        fill_w = int(w * self.status_prog)
        if fill_w > 0:
            gc.SetBrush(wx.Brush(self.status_bar_color))
            gc.DrawRectangle(0, 0, fill_w, h)
            gc.Clip(0, 0, fill_w, h)
            gc.SetFont(font, wx.Colour(13, 13, 13))
            gc.DrawText(self.status_msg, tx, ty)
            gc.ResetClip()

    def reset_status_bar(self):
        """Resets the status bar to ready state if not currently rendering."""
        if self.is_rendering: return
        
        # Any adjustment closes render preview
        if self.render_preview_active:
            self.render_preview_active = False
            self.final_output_type = None
            if hasattr(self, 'render_preview_panel'):
                self.render_preview_panel.Hide()
            self.update_preview_overlay()

        if self.status_msg == "READY" and self.status_prog == 0.0: return
        self.status_msg = "READY"
        self.status_fg = self.ACCENT_GREEN
        self.status_prog = 0.0
        self.status_bar_color = self.ACCENT_CYAN
        if hasattr(self, 'status_bar_panel'):
            self.status_bar_panel.Refresh()

    def create_section_label(self, parent, text):
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(panel, label=text)
        label.SetForegroundColour(self.ACCENT_CYAN)
        label.SetFont(get_custom_font(13, family_name=_OSWALD, weight=wx.FONTWEIGHT_SEMIBOLD))
        sizer.Add(label, 0, wx.ALIGN_CENTER_VERTICAL)
        line = wx.Panel(panel, size=(60, 1))
        line.SetBackgroundColour(self.BORDER_DEFAULT)
        sizer.Add(line, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 8)
        panel.SetSizerAndFit(sizer)
        return panel

    def create_numeric_input(self, parent, value, unit, editable=True, min_val=None, max_val=None):
        v = float(value) if isinstance(value, str) else value
        if editable: return NumericInput(parent, value=v, unit=unit, min_val=min_val, max_val=max_val, size=(100, 32))
        else: return NumericDisplay(parent, value=v, unit=unit, size=(100, 32))

    def on_preset_change(self, preset_id):
        if self.is_rendering: return
        
        # Choosing a preset closes render preview
        self.reset_status_bar()
        
        from core.renderer import RenderEngine
        presets = RenderEngine.PRESETS
        if preset_id == 'custom':
            if 'custom' in self.preset_buttons: 
                self.preset_buttons['custom'].SetSelected(False)
            from ui.dialogs import RecallPresetDialog, ID_RESET
            while True:
                dlg = RecallPresetDialog(self, self.board_path)
                result = dlg.ShowModal()
                if result == wx.ID_OK:
                    pd = dlg.GetSelectedSettings()
                    pn = dlg.GetSelectedName()
                    dlg.Destroy()
                    if pd:
                        if 'custom' in self.preset_buttons: 
                            self.preset_buttons['custom'].SetLabel(pn)
                        self.apply_preset_data(pd, f"CUSTOM: {pn.upper()}")
                        pf = self.GetTopLevelParent()
                        if pf: pf.Raise()
                    return
                elif result == ID_RESET:
                    if 'custom' in self.preset_buttons: 
                        self.preset_buttons['custom'].SetLabel("SELECT CUSTOM..")
                    self.check_preset_match(manual_change=True)
                    pf = self.GetTopLevelParent()
                    if pf: pf.Raise()
                    dlg.Destroy()
                    continue
                else:
                    dlg.Destroy()
                    self.check_preset_match()
                    pf = self.GetTopLevelParent()
                    if pf: pf.Raise()
                    return
        if preset_id in presets:
            self.apply_preset_data(presets[preset_id], preset_id.replace('_', ' ').upper())

    def apply_preset_data(self, preset, label):
        if not label.startswith("CUSTOM:"):
            if 'custom' in self.preset_buttons: self.preset_buttons['custom'].SetLabel("SELECT CUSTOM..")
        keys = ['board_tilt', 'board_roll', 'spin_tilt', 'spin_heading', 'period', 'direction', 'lighting']
        for k in keys:
            if k in preset: self.settings[k] = preset[k]
        if hasattr(self, 'board_tilt_slider'): 
            self.board_tilt_slider.SetValue(self.settings['board_tilt'])
            self.board_tilt_input.SetValue(self.settings['board_tilt'])
        if hasattr(self, 'board_roll_slider'): 
            self.board_roll_slider.SetValue(self.settings['board_roll'])
            self.board_roll_input.SetValue(self.settings['board_roll'])
        if hasattr(self, 'spin_tilt_slider'): 
            self.spin_tilt_slider.SetValue(self.settings['spin_tilt'])
            self.spin_tilt_input.SetValue(self.settings['spin_tilt'])
        if hasattr(self, 'spin_heading_slider'): 
            self.spin_heading_slider.SetValue(self.settings['spin_heading'])
            self.spin_heading_input.SetValue(self.settings['spin_heading'])
        if hasattr(self, 'period_slider'): 
            p = self.settings['period']
            self.period_slider.SetValue(p)
            self.period_input.SetValue(round(p, 1))
            self.frame_count.SetLabel(f"{int(p * 30)} f")
        if hasattr(self, 'dir_toggle'): 
            self.dir_toggle.SetSelection(1 if self.settings['direction'] == 'cw' else 0)
        if hasattr(self, 'light_toggle'): 
            idx = next((i for i, o in enumerate(self.light_options) if o['id'] == self.settings['lighting']), 0)
            self.light_toggle.SetSelection(idx)
        if hasattr(self, 'viewport'): 
            self.viewport.set_universal_joint_parameters(self.settings['board_tilt'], self.settings['board_roll'], self.settings['spin_tilt'], self.settings['spin_heading'])
            self.viewport.set_period(self.settings['period'])
            self.viewport.set_direction(self.settings['direction'])
        self.update_preview_overlay()
        self.check_preset_match(manual_change=False)

    def check_preset_match(self, manual_change=False):
        from core.renderer import RenderEngine
        from core.presets import PresetManager
        presets = RenderEngine.PRESETS
        manager = PresetManager(self.board_path)
        custom_presets = manager.list_presets()
        matched_any = False
        for pid, btn in self.preset_buttons.items():
            if pid == 'custom': continue
            p = presets.get(pid)
            if not p: btn.SetSelected(False); continue
            is_match = all(abs(self.settings.get(k, 0) - p.get(k, 0)) < 0.01 for k in ['board_tilt', 'board_roll', 'spin_tilt', 'spin_heading', 'period'])
            is_match = is_match and self.settings.get('direction') == p.get('direction')
            is_match = is_match and self.settings.get('lighting') == p.get('lighting')
            btn.SetSelected(is_match)
            if is_match: 
                matched_any = True; self.settings['preset'] = pid
                if 'custom' in self.preset_buttons: self.preset_buttons['custom'].SetLabel("SELECT CUSTOM..")
        cmn = None
        if not matched_any and not manual_change:
            for scope, name in custom_presets:
                pd = manager.load_preset(name, is_global=(scope=='global'))
                if not pd: continue
                match = all(abs(self.settings.get(k, 0) - pd.get(k, 0)) < 0.01 for k in ['board_tilt', 'board_roll', 'spin_tilt', 'spin_heading', 'period'])
                match = match and self.settings.get('direction') == pd.get('direction')
                match = match and self.settings.get('lighting') == pd.get('lighting')
                if match: cmn = name; matched_any = True; break
        if 'custom' in self.preset_buttons:
            if cmn: 
                self.preset_buttons['custom'].SetLabel(cmn); self.preset_buttons['custom'].SetSelected(True)
                self.settings['preset'] = 'custom'
            else:
                self.preset_buttons['custom'].SetSelected(False)
                if not matched_any: self.settings['preset'] = 'custom'
                if manual_change and not matched_any: self.preset_buttons['custom'].SetLabel("SELECT CUSTOM..")
        self.update_preview_overlay()

    def on_board_tilt_change(self, event): 
        self.reset_status_bar()
        self.settings['board_tilt'] = float(self.board_tilt_slider.GetValue())
        self.board_tilt_input.SetValue(self.settings['board_tilt'])
        self._update_viewport_rotation()
        self.check_preset_match(manual_change=True)

    def on_board_tilt_input(self, event): 
        self.reset_status_bar()
        self.settings['board_tilt'] = float(self.board_tilt_input.GetValue())
        self.board_tilt_slider.SetValue(self.settings['board_tilt'])
        self._update_viewport_rotation()
        self.check_preset_match(manual_change=True)

    def on_board_roll_change(self, event): 
        self.reset_status_bar()
        self.settings['board_roll'] = float(self.board_roll_slider.GetValue())
        self.board_roll_input.SetValue(self.settings['board_roll'])
        self._update_viewport_rotation()
        self.check_preset_match(manual_change=True)

    def on_board_roll_input(self, event): 
        self.reset_status_bar()
        self.settings['board_roll'] = float(self.board_roll_input.GetValue())
        self.board_roll_slider.SetValue(self.settings['board_roll'])
        self._update_viewport_rotation()
        self.check_preset_match(manual_change=True)

    def on_spin_tilt_change(self, event): 
        self.reset_status_bar()
        self.settings['spin_tilt'] = float(self.spin_tilt_slider.GetValue())
        self.spin_tilt_input.SetValue(self.settings['spin_tilt'])
        self._update_viewport_rotation()
        self.check_preset_match(manual_change=True)

    def on_spin_tilt_input(self, event): 
        self.reset_status_bar()
        self.settings['spin_tilt'] = float(self.spin_tilt_input.GetValue())
        self.spin_tilt_slider.SetValue(self.settings['spin_tilt'])
        self._update_viewport_rotation()
        self.check_preset_match(manual_change=True)

    def on_spin_heading_change(self, event): 
        self.reset_status_bar()
        self.settings['spin_heading'] = float(self.spin_heading_slider.GetValue())
        self.spin_heading_input.SetValue(self.settings['spin_heading'])
        self._update_viewport_rotation()
        self.check_preset_match(manual_change=True)

    def on_spin_heading_input(self, event): 
        self.reset_status_bar()
        self.settings['spin_heading'] = float(self.spin_heading_input.GetValue())
        self.spin_heading_slider.SetValue(self.settings['spin_heading'])
        self._update_viewport_rotation()
        self.check_preset_match(manual_change=True)
    
    def _update_viewport_rotation(self):
        if hasattr(self, 'viewport'): 
            self.viewport.set_universal_joint_parameters(self.settings['board_tilt'], self.settings['board_roll'], self.settings['spin_tilt'], self.settings['spin_heading'])
        self.update_preview_overlay()
        
    def on_period_change(self, event): 
        self.reset_status_bar()
        self.settings['period'] = round(float(self.period_slider.GetValue()), 1)
        self.period_input.SetValue(self.settings['period'])
        self.frame_count.SetLabel(f"{int(self.settings['period'] * 30)} f")
        if hasattr(self, 'viewport'): 
            self.viewport.set_period(self.settings['period'])
        self.update_preview_overlay()
        self.check_preset_match(manual_change=True)
        
    def on_period_input_change(self, event): 
        self.reset_status_bar()
        v = round(float(self.period_input.GetValue()), 1)
        self.settings['period'] = v
        self.period_slider.SetValue(v)
        self.frame_count.SetLabel(f"{int(v * 30)} f")
        if hasattr(self, 'viewport'): 
            self.viewport.set_period(v)
        self.update_preview_overlay()
        self.check_preset_match(manual_change=True)
        
    def on_direction_change(self, event): 
        self.reset_status_bar()
        self.settings['direction'] = 'cw' if self.dir_toggle.GetSelection() == 1 else 'ccw'
        if hasattr(self, 'viewport'): 
            self.viewport.set_direction(self.settings['direction'])
        self.update_preview_overlay()
        self.check_preset_match(manual_change=True)
        
    def on_lighting_change(self, event): 
        self.reset_status_bar()
        self.settings['lighting'] = self.light_options[self.light_toggle.GetSelection()]['id']
        self.update_preview_overlay()
        self.check_preset_match(manual_change=True)
        
    def on_format_change(self, event): 
        self.reset_status_bar()
        self.settings['format'] = self.format_ids[self.format_choice.GetSelection()]
        self.update_preview_overlay()
        
    def on_resolution_change(self, event): 
        self.reset_status_bar()
        self.settings['resolution'] = self.res_ids[self.res_choice.GetSelection()]
        self.update_preview_overlay()

    def on_save_preset(self, event):
        self.reset_status_bar()
        from ui.dialogs import SavePresetDialog
        from core.presets import PresetManager
        dlg = SavePresetDialog(self, self.board_path)
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            name = dlg.GetPresetName()
            if name:
                manager = PresetManager(self.board_path)
                if manager.save_preset(name, self.settings):
                    if 'custom' in self.preset_buttons: 
                        self.preset_buttons['custom'].SetLabel(name)
                    self.check_preset_match(manual_change=False)
        dlg.Destroy()
        self.update_preview_overlay()
        pf = self.GetTopLevelParent()
        if pf: 
            pf.Raise()

    def on_advanced_options(self, event):
        self.reset_status_bar()
        from ui.dialogs import AdvancedOptionsDialog
        dlg = AdvancedOptionsDialog(self, self.settings, self.board_path)
        dlg.ShowModal()
        dlg.Destroy()
        self.update_preview_overlay()
        pf = self.GetTopLevelParent()
        if pf: 
            pf.Raise()

    def on_cancel(self, event):
        from core.presets import PresetManager
        PresetManager(self.board_path).save_last_used_settings(self.settings)
        f = self.GetTopLevelParent()
        if f: 
            f.Close()
            
    def on_close(self, event):
        from core.presets import PresetManager
        PresetManager(self.board_path).save_last_used_settings(self.settings)
        f = self.GetTopLevelParent()
        if f: 
            f.Close()

    def on_render(self, event):
        if self.is_rendering:
            if self.render_engine: 
                self.render_engine.cancel()
            self.status_msg = "STOPPING RENDER..."
            self.status_fg = self.ACCENT_ORANGE
            self.status_bar_panel.Refresh()
            return

        from core.renderer import RenderEngine
        self.is_rendering = True
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
        self.controls_panel.Layout()
        self.Layout()

        self.status_msg = "PREPARING RENDER..."
        self.status_fg = self.ACCENT_CYAN
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
        self.render_preview_bitmap = None # Clear old frame
        self.preview_manually_closed = False
        self.current_render_frame = 0
        self.total_render_frames = 0
        self.final_output_type = None
        
        if hasattr(self, 'render_preview_panel'):
            # Force size/pos sync before showing
            if hasattr(self, 'viewport'):
                v_size = self.viewport.GetSize()
                self.render_preview_panel.SetSize(v_size)
                self.render_preview_panel.SetPosition((0, 0))
            self.render_preview_panel.Show()
            self.render_preview_panel.Refresh()
            
        self.update_preview_overlay()
        
        def run_render():
            try:
                self.render_engine = RenderEngine(self.board_path, self.settings, progress_callback=self.on_render_progress)
                out = self.render_engine.render()
                wx.CallAfter(self.on_render_finished, out)
            except Exception as e:
                wx.CallAfter(self.on_render_finished, None, str(e))

        threading.Thread(target=run_render, daemon=True).start()

    def on_render_progress(self, current, total, message, frame_path=None):
        wx.CallAfter(self._update_progress_ui, current, total, message, frame_path)

    def _update_progress_ui(self, current, total, message, frame_path=None):
        self.status_msg = message
        self.status_prog = current / total if total > 0 else 0.0
        self.status_bar_panel.Refresh()
        
        # Update overlay frame info
        self.current_render_frame = current
        self.total_render_frames = total
        self.render_preview_active = True
        self.update_preview_overlay()
        
        if frame_path and hasattr(self, 'render_preview_panel'):
            try:
                if not os.path.exists(frame_path): 
                    return
                img = wx.Image(frame_path, wx.BITMAP_TYPE_ANY)
                if img.IsOk():
                    self.render_preview_bitmap = wx.Bitmap(img)
                    if not self.preview_manually_closed:
                        # Position overlay to cover viewport exactly
                        if hasattr(self, 'viewport'):
                            v_size = self.viewport.GetSize()
                            self.render_preview_panel.SetSize(v_size)
                            self.render_preview_panel.SetPosition((0, 0))
                        if not self.render_preview_panel.IsShown():
                            self.render_preview_panel.Show()
                        self.render_preview_panel.Refresh()
            except Exception as e:
                print(f"[SpinRender] Failed to load frame bitmap: {e}")

    def on_render_finished(self, result, error=None):
        self.is_rendering = False
        self.render_engine = None
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
        self.controls_panel.Layout()
        self.Layout()
        
        # Give UI a moment to process button visibility changes
        wx.SafeYield()
        self.controls_panel.Refresh()
        
        if error:
            # Only hide if no frames were actually rendered
            if not self.render_preview_bitmap:
                self.render_preview_active = False
                if hasattr(self, 'render_preview_panel'): 
                    self.render_preview_panel.Hide()
            
            self.final_output_type = None
            self.status_msg = f"ERROR: {error.upper()}"
            self.status_fg = self.ACCENT_ORANGE
            self.status_bar_color = self.ACCENT_ORANGE
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
            self.status_fg = self.ACCENT_GREEN
            self.status_bar_color = self.ACCENT_GREEN
            self.status_prog = 1.0
            
            # Start looping playback of the rendered result
            self.render_preview_active = True
            self.current_render_frame = None
            self.final_output_type = self.settings.get('format', 'mp4')
            
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
            else:
                self.render_preview_active = False
                
            self.final_output_type = None
            self.status_msg = "RENDER STOPPED"
            self.status_fg = self.ACCENT_ORANGE
            self.status_prog = 0.0
            
        self.update_preview_overlay()
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
        if hasattr(self, 'viewport') and self.viewport: self.viewport.cleanup()
