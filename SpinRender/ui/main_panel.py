"""
SpinRender Main UI Panel
Implements the two-panel layout from Pencil design
"""
import wx
import wx.svg
import wx.lib.scrolledpanel as scrolled
import os
import json
import time
from pathlib import Path
from .custom_controls import (
    CustomSlider, CustomToggleButton, CustomButton,
    PresetCard, SectionLabel, NumericDisplay, NumericInput,
    get_custom_font, _OSWALD
)

# Import preview renderers
from core.preview import GLPreviewRenderer, PreviewRenderer


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
        if not gc: return

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
        self.settings = {
            'preset': 'hero', 
            'board_tilt': 35.0, 
            'board_roll': -90.0,
            'spin_tilt': 0.0, 
            'spin_heading': 0.0,
            'period': 10.0, 'easing': 'linear', 'direction': 'ccw', 'lighting': 'studio',
            'format': 'mp4', 'resolution': '1920x1080', 'output_auto': True,
            'output_path': '', 'cli_overrides': ''
        }
        self.SetBackgroundColour(self.BG_PAGE)
        self.drag_start_pos = None
        self.frame_start_pos = None
        self.build_ui()

    def build_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        top_panel = wx.Panel(self)
        top_panel.SetBackgroundColour(self.BG_PAGE)
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Left: Controls panel - Fixed width (determined by create_controls_panel)
        self.controls_panel = self.create_controls_panel(top_panel)
        top_sizer.Add(self.controls_panel, 0, wx.EXPAND)

        # Center Divider
        divider = wx.Panel(top_panel, size=(1, -1))
        divider.SetBackgroundColour(self.BORDER_DEFAULT)
        top_sizer.Add(divider, 0, wx.EXPAND)

        # Right: Preview panel - Explicitly forced to 700 width
        self.preview_panel = self.create_preview_panel(top_panel)
        top_sizer.Add(self.preview_panel, 0, wx.EXPAND | wx.FIXED_MINSIZE)

        top_panel.SetSizer(top_sizer)
        top_sizer.Fit(top_panel)
        main_sizer.Add(top_panel, 1, wx.EXPAND)
        status_divider = wx.Panel(self, size=(-1, 1))
        status_divider.SetBackgroundColour(self.BORDER_DEFAULT)
        main_sizer.Add(status_divider, 0, wx.EXPAND)

        self.status_bar = self.create_status_bar(self)
        main_sizer.Add(self.status_bar, 0, wx.EXPAND)

        self.SetSizer(main_sizer)
        
        # PROPAGATE SIZES
        main_sizer.Layout()
        min_size = main_sizer.CalcMin()
        self.SetMinSize(min_size)
        
        # Ensure top level frame knows about the min size
        parent_frame = self.GetTopLevelParent()
        if parent_frame:
            main_sizer.SetSizeHints(parent_frame)

    def create_controls_panel(self, parent):
        """
        Create the left controls panel with explicit height calculation
        """
        panel = scrolled.ScrolledPanel(parent, size=(450, -1))
        panel.SetBackgroundColour(self.BG_PAGE)
        panel.SetupScrolling(scroll_x=False, scroll_y=True, rate_y=20)
        sizer = wx.BoxSizer(wx.VERTICAL)

        padding = 16
        
        # Add all sections
        header = self.create_header(panel)
        sizer.Add(header, 0, wx.EXPAND)
        
        div1 = wx.Panel(panel, size=(-1, 1)); div1.SetBackgroundColour(self.BORDER_DEFAULT)
        sizer.Add(div1, 0, wx.EXPAND)
        
        presets = self.create_preset_section(panel)
        sizer.Add(presets, 0, wx.EXPAND | wx.ALL, padding)
        
        div2 = wx.Panel(panel, size=(-1, 1)); div2.SetBackgroundColour(self.BORDER_DEFAULT)
        sizer.Add(div2, 0, wx.EXPAND)
        
        params = self.create_parameters_section(panel)
        sizer.Add(params, 0, wx.EXPAND | wx.ALL, padding)
        
        div3 = wx.Panel(panel, size=(-1, 1)); div3.SetBackgroundColour(self.BORDER_DEFAULT)
        sizer.Add(div3, 0, wx.EXPAND)
        
        # New Output Settings section
        output_settings = self.create_output_settings_section(panel)
        sizer.Add(output_settings, 1, wx.EXPAND | wx.ALL, padding)
        
        div4 = wx.Panel(panel, size=(-1, 1)); div4.SetBackgroundColour(self.BORDER_DEFAULT)
        sizer.Add(div4, 0, wx.EXPAND)
        
        export = self.create_export_section(panel)
        sizer.Add(export, 0, wx.EXPAND | wx.ALL, padding)

        panel.SetSizer(sizer)
        
        # Calculate the required virtual size to fit everything
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
        close_btn = CustomButton(header, label="", icon='mdi-close', primary=False, ghost=True, danger=True, size=(36, 36))
        close_btn.Bind(wx.EVT_BUTTON, self.on_close)
        sizer.Add(close_btn, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 16)

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
        presets = [("hero", "HERO", "mdi-rotate-cw"), ("spin", "SPIN", "mdi-arrow-down"), ("roll", "ROLL", "mdi-arrow-up"), ("custom", "SELECT CUSTOM..", "mdi-star-settings-outline")]
        self.preset_buttons = {}
        for i, (pid, lbl, ico) in enumerate(presets):
            btn = PresetCard(preset_row, label=lbl, icon_name=ico, size=(90, 64))
            btn.Bind(wx.EVT_BUTTON, lambda e, p=pid: self.on_preset_change(p))
            if self.settings['preset'] == pid: btn.SetSelected(True)
            self.preset_buttons[pid] = btn
            # Add padding to all but the last item to ensure justification
            flags = wx.EXPAND
            if i < len(presets) - 1:
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

        cols = [
            wx.Colour(255, 107, 107),  # Board Tilt: Red-ish
            wx.Colour(255, 180, 107),  # Board Roll: Orange-ish
            wx.Colour(77, 150, 255),   # Spin Tilt: Blue
            wx.Colour(170, 107, 255)   # Spin Heading: Purple
        ]
        icons = ["mdi-axis-x-rotate-counterclockwise", "mdi-rotate-orbit", "mdi-axis-y-rotate-counterclockwise", "mdi-axis-z-rotate-counterclockwise"]
        
        # 1. BOARD TILT
        row1 = self.create_axis_control(panel, "BOARD TILT", 45.0, cols[0], icons[0], -90, 90, self.on_board_tilt_change, self.on_board_tilt_input)
        sizer.Add(row1, 0, wx.EXPAND | wx.BOTTOM, 4)
        
        # 2. BOARD ROLL
        row2 = self.create_axis_control(panel, "BOARD ROLL", 0.0, cols[1], icons[1], -180, 180, self.on_board_roll_change, self.on_board_roll_input)
        sizer.Add(row2, 0, wx.EXPAND | wx.BOTTOM, 4)
        
        # 3. SPIN TILT
        row3 = self.create_axis_control(panel, "SPIN TILT", 0.0, cols[2], icons[2], -90, 90, self.on_spin_tilt_change, self.on_spin_tilt_input)
        sizer.Add(row3, 0, wx.EXPAND | wx.BOTTOM, 4)
        
        # 4. SPIN HEADING
        row4 = self.create_axis_control(panel, "SPIN HEADING", 0.0, cols[3], icons[3], -180, 180, self.on_spin_heading_change, self.on_spin_heading_input)
        sizer.Add(row4, 0, wx.EXPAND | wx.BOTTOM, 4)

        desc = wx.StaticText(panel, label="// Board: Orient on spindle | Spin: Orient the spindle itself")
        desc.SetForegroundColour(self.TEXT_MUTED)
        desc.SetFont(wx.Font(8, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="JetBrains Mono"))
        sizer.Add(desc, 0)
        panel.SetSizerAndFit(sizer)
        return panel

    def create_axis_control(self, parent, label_text, def_val, col, icon_name, min_val, max_val, s_hand, i_hand):
        row = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Label part with fixed width ensures sliders start at same X
        label_part = wx.Panel(row, size=(130, -1))
        lp_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        mdi_icons = {
            'mdi-axis-x-rotate-counterclockwise': '\U000F0D1E',
            'mdi-rotate-orbit': '\U000F0D52',
            'mdi-axis-y-rotate-counterclockwise': '\U000F0D54',
            'mdi-axis-z-rotate-counterclockwise': '\U000F0D58'
        }
        
        from .custom_controls import get_mdi_font
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
        
        from .custom_controls import CustomSlider
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
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        lbl = wx.StaticText(panel, label="ROTATION PERIOD")
        lbl.SetForegroundColour(self.TEXT_PRIMARY)
        lbl.SetFont(wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_SEMIBOLD, faceName="JetBrains Mono"))
        sizer.Add(lbl, 0, wx.BOTTOM, 6)

        crow = wx.Panel(panel); csizer = wx.BoxSizer(wx.HORIZONTAL)
        # Proportion 1 makes it expand
        self.period_slider = CustomSlider(crow, value=10, min_val=1, max_val=30, size=(-1, 18))
        self.period_slider.Bind(wx.EVT_SLIDER, self.on_period_change)
        csizer.Add(self.period_slider, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.period_input = self.create_numeric_input(crow, "10.00", "sec", editable=True, min_val=1, max_val=30)
        self.period_input.Bind(wx.EVT_TEXT_ENTER, self.on_period_input_change)
        csizer.Add(self.period_input, 0, wx.ALIGN_CENTER_VERTICAL)
        crow.SetSizerAndFit(csizer); sizer.Add(crow, 0, wx.EXPAND | wx.BOTTOM, 6)

        mrow = wx.Panel(panel); msizer = wx.BoxSizer(wx.HORIZONTAL)
        desc = wx.StaticText(mrow, label="// speed of 360° spin")
        desc.SetForegroundColour(self.TEXT_MUTED); desc.SetFont(wx.Font(8, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="JetBrains Mono"))
        msizer.Add(desc, 1)
        self.frame_count = wx.StaticText(mrow, label="300 f")
        self.frame_count.SetForegroundColour(self.TEXT_SECONDARY); self.frame_count.SetFont(wx.Font(8, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="JetBrains Mono"))
        msizer.Add(self.frame_count, 0)
        mrow.SetSizerAndFit(msizer); sizer.Add(mrow, 0, wx.EXPAND)
        panel.SetSizerAndFit(sizer)
        return panel

    def create_direction_control(self, parent):
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        lbl = wx.StaticText(panel, label="DIRECTION")
        lbl.SetForegroundColour(self.TEXT_PRIMARY); lbl.SetFont(wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_SEMIBOLD, faceName="JetBrains Mono"))
        sizer.Add(lbl, 0, wx.BOTTOM, 6)
        
        # New options API
        dir_options = [
            {'label': 'CCW', 'icon': 'mdi-restore'},
            {'label': 'CW', 'icon': 'mdi-reload'}
        ]
        
        self.dir_toggle = CustomToggleButton(panel, options=dir_options, size=(210, 32))
        
        # CCW is 0, CW is 1
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
        lbl.SetForegroundColour(self.TEXT_PRIMARY); lbl.SetFont(wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_SEMIBOLD, faceName="JetBrains Mono"))
        sizer.Add(lbl, 0, wx.BOTTOM, 6)
        
        self.light_options = [
            {'id': 'studio', 'label': 'STUDIO', 'icon': 'mdi-weather-sunny'},
            {'id': 'dramatic', 'label': 'DRAMATIC', 'icon': 'mdi-lightning-bolt'},
            {'id': 'soft', 'label': 'SOFT', 'icon': 'mdi-image-filter-drama-outline'},
            {'id': 'none', 'label': 'NONE', 'icon': 'mdi-circle-off-outline'}
        ]
        
        # Pass ACCENT_YELLOW as active color
        self.light_toggle = CustomToggleButton(panel, options=self.light_options, size=(320, 32), active_color=self.ACCENT_YELLOW)
        
        # Set initial selection
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
        
        from .custom_controls import CustomDropdown

        # Column 1: Format
        f_col = wx.Panel(cols_panel); f_sizer = wx.BoxSizer(wx.VERTICAL)
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
        f_col.SetSizerAndFit(f_sizer); cols_sizer.Add(f_col, 1, wx.EXPAND | wx.RIGHT, 12)
        
        # Column 2: Resolution
        r_col = wx.Panel(cols_panel); r_sizer = wx.BoxSizer(wx.VERTICAL)
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
        r_col.SetSizerAndFit(r_sizer); cols_sizer.Add(r_col, 1, wx.EXPAND)
        
        cols_panel.SetSizerAndFit(cols_sizer)
        sizer.Add(cols_panel, 0, wx.EXPAND)
        
        panel.SetSizerAndFit(sizer)
        return panel

    def create_export_section(self, parent):
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Add stretch spacer to push buttons to the bottom
        sizer.AddStretchSpacer()
        
        arow = wx.Panel(panel); asizer = wx.BoxSizer(wx.HORIZONTAL)
        adv_btn = CustomButton(arow, label="", icon='mdi-cog', primary=False, size=(36, 36))
        adv_btn.Bind(wx.EVT_BUTTON, self.on_advanced_options); asizer.Add(adv_btn, 0, wx.RIGHT, 8)
        can_btn = CustomButton(arow, label="CANCEL", icon='mdi-close', primary=False, danger=True, size=(110, 36))
        can_btn.Bind(wx.EVT_BUTTON, self.on_cancel); asizer.Add(can_btn, 0, wx.RIGHT, 8)
        ren_btn = CustomButton(arow, label="RENDER", icon='mdi-play', primary=True, size=(150, 36))
        ren_btn.Bind(wx.EVT_BUTTON, self.on_render); asizer.Add(ren_btn, 1, wx.EXPAND)
        arow.SetSizerAndFit(asizer); sizer.Add(arow, 0, wx.EXPAND)
        panel.SetSizerAndFit(sizer)
        return panel

    def create_preview_panel(self, parent):
        panel = wx.Panel(parent, size=(700, -1))
        panel.SetBackgroundColour(wx.Colour(10, 10, 10))
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        top_meta = wx.Panel(panel)
        meta_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.meta_frame = wx.StaticText(top_meta, label="FRAME 001 / 300")
        self.meta_frame.SetForegroundColour(wx.Colour(255, 255, 255, 68))
        self.meta_frame.SetFont(wx.Font(9, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="JetBrains Mono"))
        meta_sizer.Add(self.meta_frame, 1)
        
        self.meta_angle = wx.StaticText(top_meta, label="X:0° Y:0° Z:0°  //  10.00s")
        self.meta_angle.SetForegroundColour(wx.Colour(255, 255, 255, 68))
        self.meta_angle.SetFont(wx.Font(9, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="JetBrains Mono"))
        meta_sizer.Add(self.meta_angle, 0)
        
        top_meta.SetSizerAndFit(meta_sizer)
        sizer.Add(top_meta, 0, wx.EXPAND | wx.ALL, 12)
        
        # GLPreviewRenderer is now mandatory
        self.viewport = GLPreviewRenderer(panel, self.board_path)
            
        sizer.Add(self.viewport, 1, wx.EXPAND)
        
        bottom_meta = wx.Panel(panel)
        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.meta_preset = wx.StaticText(bottom_meta, label="HERO ORBIT  //  STUDIO")
        self.meta_preset.SetForegroundColour(wx.Colour(255, 255, 255, 68))
        self.meta_preset.SetFont(wx.Font(9, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="JetBrains Mono"))
        bottom_sizer.Add(self.meta_preset, 1)
        
        status_text = wx.StaticText(bottom_meta, label="PLAYING")
        status_text.SetForegroundColour(self.ACCENT_GREEN)
        status_text.SetFont(wx.Font(9, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="JetBrains Mono"))
        bottom_sizer.Add(status_text, 0)
        
        bottom_meta.SetSizerAndFit(bottom_sizer)
        sizer.Add(bottom_meta, 0, wx.EXPAND | wx.ALL, 12)
        
        res_meta = wx.StaticText(panel, label="1920 × 1080  //  16:9  //  30fps")
        res_meta.SetForegroundColour(wx.Colour(255, 255, 255, 34))
        res_meta.SetFont(wx.Font(8, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="JetBrains Mono"))
        sizer.Add(res_meta, 0, wx.ALIGN_CENTER | wx.BOTTOM, 12)
        
        panel.SetSizer(sizer)
        panel.SetMinSize((700, -1))
        panel.SetMaxSize((700, -1))
        
        for w in [panel, self.viewport, top_meta, self.meta_frame, self.meta_angle, bottom_meta, self.meta_preset, status_text, res_meta]:
            self.enable_drag(w)
            
        self.viewport.set_universal_joint_parameters(
            self.settings['board_tilt'], 
            self.settings['board_roll'],
            self.settings['spin_tilt'], 
            self.settings['spin_heading']
        )
        self.viewport.set_period(self.settings['period'])
        self.viewport.set_direction(self.settings['direction'])
        self.viewport.start_preview()
        
        return panel

    def create_status_bar(self, parent):
        panel = wx.Panel(parent, size=(-1, 25))
        panel.SetBackgroundColour(self.BG_PANEL)
        panel.SetMinSize((-1, 25))
        panel.SetMaxSize((-1, 25))
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.status_text = wx.StaticText(panel, label="// ready")
        self.status_text.SetForegroundColour(self.ACCENT_GREEN)
        self.status_text.SetFont(wx.Font(8, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="JetBrains Mono"))
        
        sizer.Add(self.status_text, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        panel.SetSizer(sizer)
        return panel

    def create_section_label(self, parent, text):
        panel = wx.Panel(parent); sizer = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(panel, label=text); label.SetForegroundColour(self.ACCENT_CYAN); label.SetFont(get_custom_font(13, family_name=_OSWALD, weight=wx.FONTWEIGHT_SEMIBOLD))
        sizer.Add(label, 0, wx.ALIGN_CENTER_VERTICAL); line = wx.Panel(panel, size=(60, 1)); line.SetBackgroundColour(self.BORDER_DEFAULT); sizer.Add(line, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 8)
        panel.SetSizerAndFit(sizer)
        return panel

    def create_numeric_input(self, parent, value, unit, editable=True, min_val=None, max_val=None):
        v = float(value) if isinstance(value, str) else value
        return NumericInput(parent, value=v, unit=unit, min_val=min_val, max_val=max_val, size=(100, 32)) if editable else NumericDisplay(parent, value=v, unit=unit, size=(100, 32))

    def on_preset_change(self, preset_id):
        from core.renderer import RenderEngine
        presets = RenderEngine.PRESETS
        
        # Apply preset if it exists (skip 'custom')
        if preset_id in presets:
            preset = presets[preset_id]

            # Update settings
            self.settings['board_tilt'] = preset.get('board_tilt', 0.0)
            self.settings['board_roll'] = preset.get('board_roll', 0.0)
            self.settings['spin_tilt'] = preset.get('spin_tilt', 0.0)
            self.settings['spin_heading'] = preset.get('spin_heading', 0.0)
            self.settings['period'] = preset['period']
            self.settings['direction'] = preset['direction']
            self.settings['lighting'] = preset['lighting']

            # Update rotation sliders and inputs
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

            # Update period
            if hasattr(self, 'period_slider'):
                self.period_slider.SetValue(preset['period'])
                self.period_input.SetValue(preset['period'])
                self.frame_count.SetLabel(f"{int(preset['period'] * 30)} f")

            # Update direction toggle
            if hasattr(self, 'dir_toggle'):
                direction_idx = 1 if preset['direction'] == 'cw' else 0
                self.dir_toggle.SetSelection(direction_idx)

            # Update lighting toggle
            if hasattr(self, 'light_toggle'):
                light_idx = next((i for i, opt in enumerate(self.light_options) if opt['id'] == preset['lighting']), 0)
                self.light_toggle.SetSelection(light_idx)

            # Update viewport
            if hasattr(self, 'viewport'):
                self.viewport.set_universal_joint_parameters(
                    self.settings['board_tilt'],
                    self.settings['board_roll'],
                    self.settings['spin_tilt'],
                    self.settings['spin_heading']
                )
                self.viewport.set_period(preset['period'])
                self.viewport.set_direction(preset['direction'])

            # Update meta display
            self.update_meta_display()

            # Update status
            self.status_text.SetLabel(f"// preset: {preset_id.replace('_', ' ').upper()}")
            self.status_text.SetForegroundColour(self.ACCENT_CYAN)
            
            # Ensure highlights are updated
            self.check_preset_match(manual_change=False)

    def check_preset_match(self, manual_change=False):
        """
        Highlight presets only if current settings exactly match the preset definition.
        """
        from core.renderer import RenderEngine
        presets = RenderEngine.PRESETS
        
        matched_any = False
        for pid, btn in self.preset_buttons.items():
            if pid == 'custom':
                continue
                
            preset = presets.get(pid)
            if not preset:
                btn.SetSelected(False)
                continue
                
            # Compare relevant keys
            is_match = (
                abs(self.settings.get('board_tilt', 0) - preset.get('board_tilt', 0)) < 0.01 and
                abs(self.settings.get('board_roll', 0) - preset.get('board_roll', 0)) < 0.01 and
                abs(self.settings.get('spin_tilt', 0) - preset.get('spin_tilt', 0)) < 0.01 and
                abs(self.settings.get('spin_heading', 0) - preset.get('spin_heading', 0)) < 0.01 and
                self.settings.get('direction') == preset.get('direction') and
                abs(self.settings.get('period', 0) - preset.get('period', 0)) < 0.01 and
                self.settings.get('lighting') == preset.get('lighting')
            )
            
            btn.SetSelected(is_match)
            if is_match:
                matched_any = True
                self.settings['preset'] = pid
        
        # Update Custom button state
        if 'custom' in self.preset_buttons:
            show_custom = not matched_any and manual_change
            self.preset_buttons['custom'].SetSelected(show_custom)
            if not matched_any:
                self.settings['preset'] = 'custom'

    def on_board_tilt_change(self, event):
        val = float(self.board_tilt_slider.GetValue())
        self.settings['board_tilt'] = val
        if hasattr(self, 'board_tilt_input'): self.board_tilt_input.SetValue(val)
        self._update_viewport_rotation()
        self.check_preset_match(manual_change=True)

    def on_board_tilt_input(self, event):
        val = float(self.board_tilt_input.GetValue())
        self.settings['board_tilt'] = val
        if hasattr(self, 'board_tilt_slider'): self.board_tilt_slider.SetValue(val)
        self._update_viewport_rotation()
        self.check_preset_match(manual_change=True)

    def on_board_roll_change(self, event):
        val = float(self.board_roll_slider.GetValue())
        self.settings['board_roll'] = val
        if hasattr(self, 'board_roll_input'): self.board_roll_input.SetValue(val)
        self._update_viewport_rotation()
        self.check_preset_match(manual_change=True)

    def on_board_roll_input(self, event):
        val = float(self.board_roll_input.GetValue())
        self.settings['board_roll'] = val
        if hasattr(self, 'board_roll_slider'): self.board_roll_slider.SetValue(val)
        self._update_viewport_rotation()
        self.check_preset_match(manual_change=True)

    def on_spin_tilt_change(self, event):
        val = float(self.spin_tilt_slider.GetValue())
        self.settings['spin_tilt'] = val
        if hasattr(self, 'spin_tilt_input'): self.spin_tilt_input.SetValue(val)
        self._update_viewport_rotation()
        self.check_preset_match(manual_change=True)

    def on_spin_tilt_input(self, event):
        val = float(self.spin_tilt_input.GetValue())
        self.settings['spin_tilt'] = val
        if hasattr(self, 'spin_tilt_slider'): self.spin_tilt_slider.SetValue(val)
        self._update_viewport_rotation()
        self.check_preset_match(manual_change=True)

    def on_spin_heading_change(self, event):
        val = float(self.spin_heading_slider.GetValue())
        self.settings['spin_heading'] = val
        if hasattr(self, 'spin_heading_input'): self.spin_heading_input.SetValue(val)
        self._update_viewport_rotation()
        self.check_preset_match(manual_change=True)

    def on_spin_heading_input(self, event):
        val = float(self.spin_heading_input.GetValue())
        self.settings['spin_heading'] = val
        if hasattr(self, 'spin_heading_slider'): self.spin_heading_slider.SetValue(val)
        self._update_viewport_rotation()
        self.check_preset_match(manual_change=True)

    def _update_viewport_rotation(self):
        if hasattr(self, 'viewport'):
            self.viewport.set_universal_joint_parameters(
                self.settings['board_tilt'],
                self.settings['board_roll'],
                self.settings['spin_tilt'],
                self.settings['spin_heading']
            )
        self.update_meta_display()

    def on_period_change(self, event):
        self.settings['period'] = float(self.period_slider.GetValue())
        if hasattr(self, 'period_input'): self.period_input.SetValue(self.settings['period'])
        if hasattr(self, 'frame_count'): self.frame_count.SetLabel(f"{int(self.settings['period'] * 30)} f")
        if hasattr(self, 'viewport'): self.viewport.set_period(self.settings['period'])
        self.update_meta_display()
        self.check_preset_match(manual_change=True)

    def on_period_input_change(self, event):
        val = float(self.period_input.GetValue()); self.settings['period'] = val
        if hasattr(self, 'period_slider'): self.period_slider.SetValue(val)
        if hasattr(self, 'frame_count'): self.frame_count.SetLabel(f"{int(val * 30)} f")
        if hasattr(self, 'viewport'): self.viewport.set_period(val)
        self.update_meta_display()
        self.check_preset_match(manual_change=True)

    def on_direction_change(self, event):
        # Index 1 is CW, Index 0 is CCW
        self.settings['direction'] = 'cw' if self.dir_toggle.GetSelection() == 1 else 'ccw'
        self.status_text.SetLabel(f"// direction: {self.settings['direction'].upper()}")
        if hasattr(self, 'viewport'):
            self.viewport.set_direction(self.settings['direction'])
        self.check_preset_match(manual_change=True)

    def update_meta_display(self):
        if hasattr(self, 'meta_angle'): 
            self.meta_angle.SetLabel(f"BT:{self.settings.get('board_tilt', 0):.0f}° BR:{self.settings.get('board_roll', 0):.0f}° ST:{self.settings.get('spin_tilt', 0):.0f}° SH:{self.settings.get('spin_heading', 0):.0f}°  //  {self.settings.get('period', 10):.2f}s")

    def on_lighting_change(self, event):
        idx = self.light_toggle.GetSelection()
        self.settings['lighting'] = self.light_options[idx]['id']
        self.status_text.SetLabel(f"// lighting: {self.settings['lighting']}")
        self.update_meta_display()
        self.check_preset_match(manual_change=True)

    def on_format_change(self, event):
        idx = self.format_toggle.GetSelection()
        self.settings['format'] = self.format_options[idx]['id']
        self.status_text.SetLabel(f"// format: {self.settings['format'].upper()}")

    def on_resolution_change(self, event):
        idx = self.res_toggle.GetSelection()
        self.settings['resolution'] = self.res_options[idx]['id']
        self.status_text.SetLabel(f"// resolution: {self.settings['resolution']}")

    def on_save_preset(self, event):
        from ui.dialogs import SavePresetDialog; from core.presets import PresetManager
        dlg = SavePresetDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            name = dlg.GetPresetName()
            if name:
                manager = PresetManager(self.board_path)
                if manager.save_preset(name, self.settings): wx.MessageBox(f"Preset '{name}' saved successfully!", "Preset Saved", wx.OK | wx.ICON_INFORMATION)
                else: wx.MessageBox("Failed to save preset.", "Error", wx.OK | wx.ICON_ERROR)
        dlg.Destroy()

    def on_advanced_options(self, event):
        from ui.dialogs import AdvancedOptionsDialog; dlg = AdvancedOptionsDialog(self, self.settings)
        if dlg.ShowModal() == wx.ID_OK: pass
        dlg.Destroy()

    def on_cancel(self, event):
        f = self.GetTopLevelParent()
        if f: f.Close()
    def on_close(self, event):
        f = self.GetTopLevelParent()
        if f: f.Close()

    def on_render(self, event):
        from core.renderer import RenderEngine
        self.status_text.SetLabel("// preparing render..."); self.status_text.SetForegroundColour(self.ACCENT_CYAN)
        try:
            engine = RenderEngine(self.board_path, self.settings); engine.render()
            self.status_text.SetLabel("// render complete"); self.status_text.SetForegroundColour(self.ACCENT_GREEN)
        except Exception as e:
            self.status_text.SetLabel(f"// error: {str(e)}"); self.status_text.SetForegroundColour(self.ACCENT_ORANGE); wx.MessageBox(str(e), "Render Error", wx.OK | wx.ICON_ERROR)

    def on_drag_start(self, event):
        w = event.GetEventObject(); self.drag_start_pos = w.ClientToScreen(event.GetPosition()); f = self.GetTopLevelParent(); self.frame_start_pos = f.GetPosition(); w.CaptureMouse()
    def on_drag_motion(self, event):
        if self.drag_start_pos is None: return
        w = event.GetEventObject(); cur = w.ClientToScreen(event.GetPosition()); delta = wx.Point(cur.x - self.drag_start_pos.x, cur.y - self.drag_start_pos.y)
        f = self.GetTopLevelParent(); f.SetPosition(wx.Point(self.frame_start_pos.x + delta.x, self.frame_start_pos.y + delta.y))
    def on_drag_end(self, event):
        w = event.GetEventObject()
        if w.HasCapture(): w.ReleaseMouse()
        self.drag_start_pos = self.frame_start_pos = None

    def enable_drag(self, widget):
        widget.Bind(wx.EVT_LEFT_DOWN, self.on_drag_start); widget.Bind(wx.EVT_MOTION, self.on_drag_motion); widget.Bind(wx.EVT_LEFT_UP, self.on_drag_end)

    def cleanup(self):
        if hasattr(self, 'viewport') and self.viewport: self.viewport.cleanup()
