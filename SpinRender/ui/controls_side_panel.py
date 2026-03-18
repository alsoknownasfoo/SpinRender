"""
ControlsSidePanel - Extracted left sidebar UI construction from SpinRenderPanel.

This panel contains all the controls for rendering parameters, presets, and output settings.
"""
import wx
import wx.svg
import wx.lib.scrolledpanel as scrolled
from pathlib import Path

from .custom_controls import (
    CustomSlider, CustomToggleButton, CustomButton,
    PresetCard, CustomDropdown, CustomColorPicker
)
from .text_styles import TextStyle, TextStyles
from SpinRender.core.theme import Theme
_theme = Theme.current()
from .helpers import create_section_label, create_numeric_input


class ControlsSidePanel(wx.Panel):
    """
    Left sidebar panel containing all rendering controls.

    Constructs the UI for presets, rotation parameters, lighting, output settings,
    and export actions. All created controls are stored as instance attributes
    for the parent to access.

    Args:
        parent: The SpinRenderPanel instance (used for event handlers and helpers)
        settings: RenderSettings instance with current values
        board_path: Path to the board file (for preset management)
    """

    def __init__(self, parent, settings, board_path):
        super().__init__(parent)
        self.parent = parent  # wx parent (top_panel)
        self.main_panel = parent.GetParent()  # SpinRenderPanel for event handlers
        self.settings = settings
        self.board_path = board_path

        # Build the UI
        controls_panel = self.create_controls_panel(self)

        # Set up sizer for this panel
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(controls_panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        sizer.Fit(self)

    def create_controls_panel(self, parent):
        """Create the main scrolled controls container."""
        panel = scrolled.ScrolledPanel(parent, size=(400, -1))
        panel.SetBackgroundColour(_theme.color("colors.bg.page"))
        panel.SetupScrolling(scroll_x=False, scroll_y=True, rate_y=20)
        sizer = wx.BoxSizer(wx.VERTICAL)

        padding = 16

        header = self.create_header(panel)
        sizer.Add(header, 0, wx.EXPAND)

        div1 = wx.Panel(panel, size=(-1, 1))
        div1.SetBackgroundColour(_theme.color("colors.border.default"))
        sizer.Add(div1, 0, wx.EXPAND)

        presets = self.create_preset_section(panel)
        sizer.Add(presets, 0, wx.EXPAND | wx.ALL, padding)

        div2 = wx.Panel(panel, size=(-1, 1))
        div2.SetBackgroundColour(_theme.color("colors.border.default"))
        sizer.Add(div2, 0, wx.EXPAND)

        params = self.create_parameters_section(panel)
        sizer.Add(params, 0, wx.EXPAND | wx.ALL, padding)

        div3 = wx.Panel(panel, size=(-1, 1))
        div3.SetBackgroundColour(_theme.color("colors.border.default"))
        sizer.Add(div3, 0, wx.EXPAND)

        output_settings = self.create_output_settings_section(panel)
        sizer.Add(output_settings, 1, wx.EXPAND | wx.ALL, padding)

        div4 = wx.Panel(panel, size=(-1, 1))
        div4.SetBackgroundColour(_theme.color("colors.border.default"))
        sizer.Add(div4, 0, wx.EXPAND)

        export = self.create_export_section(panel)
        sizer.Add(export, 0, wx.EXPAND | wx.ALL, padding)

        panel.SetSizer(sizer)
        required_h = sizer.CalcMin().y + 40
        panel.SetMinSize((400, required_h))
        sizer.Fit(panel)
        return panel

    def create_header(self, parent):
        """Create the logo and title header."""
        header = wx.Panel(parent, size=(-1, 90))
        header.SetBackgroundColour(_theme.color("colors.bg.panel"))
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        logo = SVGLogoPanel(header, size=(58, 58))
        sizer.Add(logo, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 16)

        title_sizer = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(header, label="SPINRENDER")
        title.SetForegroundColour(_theme.color("colors.text.primary"))
        title.SetFont(TextStyles.panel_title.create_font())
        title_sizer.Add(title, 0)

        subtitle = wx.StaticText(header, label="0.9 alpha")
        subtitle.SetForegroundColour(_theme.color("colors.accent.primary"))
        subtitle.SetFont(TextStyles.label_xs.create_font())
        title_sizer.Add(subtitle, 0)
        sizer.Add(title_sizer, 0, wx.ALIGN_CENTER_VERTICAL)

        sizer.AddStretchSpacer()
        
        # Close button - use the new explicit button.close tokens
        icon_color, icon_color_hover, icon_color_pressed = _theme.color_states("components.button.close.text")
        bg_color, bg_color_hover, bg_color_pressed = _theme.color_states("components.button.close.bg")
        border_color, border_color_hover, border_color_pressed = _theme.color_states("components.button.close.border")
        radius = _theme.size("components.button.close.radius")

        self.header_close_btn = CustomButton(
            header, label="", icon='mdi-close', primary=False, ghost=True,
            icon_color=icon_color,
            icon_color_hover=icon_color_hover,
            icon_color_pressed=icon_color_pressed,
            bg_color=bg_color,
            bg_color_hover=bg_color_hover,
            bg_color_pressed=bg_color_pressed,
            size=(36, 36)
        )
        # CustomButton needs to support border_color overrides to fully implement the close button look
        self.header_close_btn.border_color_override = border_color
        self.header_close_btn.border_color_hover = border_color_hover
        self.header_close_btn.border_color_pressed = border_color_pressed
        # Could also add border_radius support if needed, but sticking to colors for now
        self.header_close_btn.Bind(wx.EVT_BUTTON, self.main_panel.on_close)
        sizer.Add(self.header_close_btn, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 16)

        header.SetSizerAndFit(sizer)
        self.main_panel.enable_drag(header)
        return header

    def create_preset_section(self, parent):
        """Create the preset selection buttons."""
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(_theme.color("colors.bg.page"))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(create_section_label(panel, "LOOP PRESET"), 0, wx.EXPAND | wx.BOTTOM, 8)

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
            btn.Bind(wx.EVT_BUTTON, lambda e, p=pid: self.main_panel.on_preset_change(p))
            if self.settings.preset == pid:
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
        """Create the collapsible parameters section."""
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(_theme.color("colors.bg.page"))
        sizer = wx.BoxSizer(wx.VERTICAL)

        header = wx.Panel(panel)
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        header_sizer.Add(create_section_label(header, "PARAMETERS"), 1, wx.ALIGN_CENTER_VERTICAL)
        save_btn = CustomButton(header, label="+ PRESET", primary=False, size=(120, 28))
        save_btn.Bind(wx.EVT_BUTTON, self.main_panel.on_save_preset)
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
        """Create all rotation axis controls."""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(panel, label="ROTATION SETTINGS")
        label.SetForegroundColour(_theme.color("colors.text.primary"))
        label.SetFont(TextStyle(family=_theme.font_family("mono"), size=10, weight=600).create_font())
        sizer.Add(label, 0, wx.BOTTOM, 6)

        cols = [_theme.get_palette_color("preset-red"), _theme.get_palette_color("preset-amber"), _theme.get_palette_color("preset-blue"), _theme.get_palette_color("preset-purple")]
        icons = ["mdi-axis-x-arrow", "mdi-axis-y-arrow", "mdi-axis-y-rotate-counterclockwise", "mdi-axis-z-rotate-counterclockwise"]

        row1 = self.create_axis_control(
            panel, "BOARD TILT", self.settings.board_tilt, cols[0], icons[0],
            -90, 90
        )
        sizer.Add(row1, 0, wx.EXPAND | wx.BOTTOM, 4)
        row2 = self.create_axis_control(
            panel, "BOARD ROLL", self.settings.board_roll, cols[1], icons[1],
            -180, 180
        )
        sizer.Add(row2, 0, wx.EXPAND | wx.BOTTOM, 4)
        row3 = self.create_axis_control(
            panel, "SPIN TILT", self.settings.spin_tilt, cols[2], icons[2],
            -90, 90
        )
        sizer.Add(row3, 0, wx.EXPAND | wx.BOTTOM, 4)
        row4 = self.create_axis_control(
            panel, "SPIN HEADING", self.settings.spin_heading, cols[3], icons[3],
            -180, 180
        )
        sizer.Add(row4, 0, wx.EXPAND | wx.BOTTOM, 4)

        desc = wx.StaticText(panel, label="BOARD: ORIENT ON SPINDLE | SPIN: ORIENT THE SPINDLE ITSELF")
        desc.SetForegroundColour(_theme.color("colors.text.muted"))
        desc.SetFont(TextStyles.label_xs.create_font())
        sizer.Add(desc, 0)
        panel.SetSizerAndFit(sizer)
        return panel

    def create_axis_control(self, parent, label_text, def_val, col, icon_name, min_val, max_val):
        """Create a labeled slider + numeric input row."""
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
            icon_lbl.SetFont(TextStyles.icon.create_font())
            lp_sizer.Add(icon_lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        lbl = wx.StaticText(label_part, label=f"{label_text}:")
        lbl.SetForegroundColour(col)
        lbl.SetFont(TextStyles.label_xs.create_font())
        lp_sizer.Add(lbl, 0, wx.ALIGN_CENTER_VERTICAL)
        label_part.SetSizer(lp_sizer)
        sizer.Add(label_part, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)

        slider = CustomSlider(row, value=def_val, min_val=min_val, max_val=max_val, size=(-1, 18), color=col)
        sizer.Add(slider, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)

        inp = create_numeric_input(row, f"{def_val:.2f}", "°", editable=True, min_val=min_val, max_val=max_val)
        sizer.Add(inp, 0, wx.ALIGN_CENTER_VERTICAL)

        attr_name = label_text.lower().replace(" ", "_")
        setattr(self, f"{attr_name}_slider", slider)
        setattr(self, f"{attr_name}_input", inp)
        row.SetSizerAndFit(sizer)
        return row

    def create_period_control(self, parent):
        """Create the rotation period control."""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        lbl = wx.StaticText(panel, label="ROTATION PERIOD")
        lbl.SetForegroundColour(_theme.color("colors.text.primary"))
        lbl.SetFont(TextStyle(family=_theme.font_family("mono"), size=10, weight=600).create_font())
        sizer.Add(lbl, 0, wx.BOTTOM, 6)

        crow = wx.Panel(panel)
        csizer = wx.BoxSizer(wx.HORIZONTAL)
        p_val = self.settings.period
        self.period_slider = CustomSlider(crow, value=p_val, min_val=0.1, max_val=30, size=(-1, 18))
        csizer.Add(self.period_slider, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.period_input = create_numeric_input(crow, f"{p_val:.1f}", "sec", editable=True, min_val=0.1, max_val=30)
        csizer.Add(self.period_input, 0, wx.ALIGN_CENTER_VERTICAL)
        crow.SetSizerAndFit(csizer)
        sizer.Add(crow, 0, wx.EXPAND | wx.BOTTOM, 6)

        mrow = wx.Panel(panel)
        msizer = wx.BoxSizer(wx.HORIZONTAL)
        desc = wx.StaticText(mrow, label="SPEED OF 360° SPIN")
        desc.SetForegroundColour(_theme.color("colors.text.muted"))
        desc.SetFont(TextStyles.label_xs.create_font())
        msizer.Add(desc, 1)
        self.frame_count = wx.StaticText(mrow, label=f"{int(p_val * 30)} f")
        self.frame_count.SetForegroundColour(_theme.color("colors.text.secondary"))
        self.frame_count.SetFont(TextStyles.label_xs.create_font())
        msizer.Add(self.frame_count, 0)
        mrow.SetSizerAndFit(msizer)
        sizer.Add(mrow, 0, wx.EXPAND)
        panel.SetSizerAndFit(sizer)
        return panel

    def create_direction_control(self, parent):
        """Create the direction toggle (CW/CCW)."""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        lbl = wx.StaticText(panel, label="DIRECTION")
        lbl.SetForegroundColour(_theme.color("colors.text.primary"))
        lbl.SetFont(TextStyle(family=_theme.font_family("mono"), size=10, weight=600).create_font())
        sizer.Add(lbl, 0, wx.BOTTOM, 6)
        dir_options = [{'label': 'CCW', 'icon': 'mdi-restore'}, {'label': 'CW', 'icon': 'mdi-reload'}]
        self.dir_toggle = CustomToggleButton(panel, options=dir_options, size=(210, 32))
        initial_idx = 1 if self.settings.direction == 'cw' else 0
        self.dir_toggle.SetSelection(initial_idx)
        sizer.Add(self.dir_toggle, 0)
        panel.SetSizerAndFit(sizer)
        return panel

    def create_lighting_control(self, parent):
        """Create the lighting preset toggle."""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        lbl = wx.StaticText(panel, label="LIGHTING")
        lbl.SetForegroundColour(_theme.color("colors.text.primary"))
        lbl.SetFont(TextStyle(family=_theme.font_family("mono"), size=10, weight=600).create_font())
        sizer.Add(lbl, 0, wx.BOTTOM, 6)
        self.light_options = [
            {'id': 'studio', 'label': 'STUDIO', 'icon': 'mdi-weather-sunny'},
            {'id': 'dramatic', 'label': 'DRAMATIC', 'icon': 'mdi-lightning-bolt'},
            {'id': 'soft', 'label': 'SOFT', 'icon': 'mdi-image-filter-drama-outline'},
            {'id': 'workspace', 'label': 'WORKSPACE', 'icon': 'mdi-application-edit'}
        ]
        self.light_toggle = CustomToggleButton(panel, options=self.light_options, size=(320, 32), active_color=_theme.color("colors.accent.secondary"))
        current_light = self.settings.lighting
        initial_idx = next((i for i, opt in enumerate(self.light_options) if opt['id'] == current_light), 0)
        self.light_toggle.SetSelection(initial_idx)
        sizer.Add(self.light_toggle, 0, wx.EXPAND)

        hint = wx.StaticText(panel, label="SELECT WORKSPACE TO USE KICAD 3D VIEWER SETTINGS")
        hint.SetForegroundColour(_theme.color("colors.text.muted"))
        hint.SetFont(TextStyle(family=_theme.font_family("mono"), size=7, weight=400).create_font())
        sizer.Add(hint, 0, wx.TOP, 4)

        panel.SetSizerAndFit(sizer)
        return panel

    def create_output_settings_section(self, parent):
        """Create format, resolution, and background color controls."""
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(_theme.color("colors.bg.page"))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(create_section_label(panel, "OUTPUT SETTINGS"), 0, wx.EXPAND | wx.BOTTOM, 10)

        # Row 1: Format and Resolution
        cols_panel = wx.Panel(panel)
        cols_sizer = wx.BoxSizer(wx.HORIZONTAL)
        f_col = wx.Panel(cols_panel)
        f_sizer = wx.BoxSizer(wx.VERTICAL)
        f_lbl = wx.StaticText(f_col, label="FORMAT")
        f_lbl.SetForegroundColour(_theme.color("colors.text.primary"))
        f_lbl.SetFont(TextStyle(family=_theme.font_family("mono"), size=10, weight=600).create_font())
        f_sizer.Add(f_lbl, 0, wx.BOTTOM, 6)
        self.format_choices = ["MP4 (H.264)", "GIF", "PNG Sequence"]
        self.format_ids = ["mp4", "gif", "png_sequence"]
        self.format_choice = CustomDropdown(f_col, choices=self.format_choices, size=(-1, 32))
        curr_fmt = self.settings.format
        fmt_idx = self.format_ids.index(curr_fmt) if curr_fmt in self.format_ids else 0
        self.format_choice.SetSelection(fmt_idx)
        f_sizer.Add(self.format_choice, 0, wx.EXPAND)
        f_col.SetSizerAndFit(f_sizer)
        cols_sizer.Add(f_col, 1, wx.EXPAND | wx.RIGHT, 12)

        r_col = wx.Panel(cols_panel)
        r_sizer = wx.BoxSizer(wx.VERTICAL)
        r_lbl = wx.StaticText(r_col, label="RESOLUTION")
        r_lbl.SetForegroundColour(_theme.color("colors.text.primary"))
        r_lbl.SetFont(TextStyle(family=_theme.font_family("mono"), size=10, weight=600).create_font())
        r_sizer.Add(r_lbl, 0, wx.BOTTOM, 6)
        self.res_choices = ["1920×1080 (1080P)", "1280×720 (720P)", "800×800 (Square)"]
        self.res_ids = ["1920x1080", "1280x720", "800x800"]
        self.res_choice = CustomDropdown(r_col, choices=self.res_choices, size=(-1, 32))
        curr_res = self.settings.resolution
        res_idx = self.res_ids.index(curr_res) if curr_res in self.res_ids else 0
        self.res_choice.SetSelection(res_idx)
        r_sizer.Add(self.res_choice, 0, wx.EXPAND)
        r_col.SetSizerAndFit(r_sizer)
        cols_sizer.Add(r_col, 1, wx.EXPAND)
        cols_panel.SetSizerAndFit(cols_sizer)
        sizer.Add(cols_panel, 0, wx.EXPAND | wx.BOTTOM, 12)

        # Row 2: Background Color
        bg_col = wx.Panel(panel)
        bg_vsizer = wx.BoxSizer(wx.VERTICAL)
        bg_lbl = wx.StaticText(bg_col, label="BACKGROUND COLOR")
        bg_lbl.SetForegroundColour(_theme.color("colors.text.primary"))
        bg_lbl.SetFont(TextStyle(family=_theme.font_family("mono"), size=10, weight=600).create_font())
        bg_vsizer.Add(bg_lbl, 0, wx.BOTTOM, 6)

        self.bg_picker = CustomColorPicker(bg_col, current_color=self.settings.bg_color)
        bg_vsizer.Add(self.bg_picker, 0, wx.EXPAND)

        bg_col.SetSizer(bg_vsizer)
        sizer.Add(bg_col, 0, wx.EXPAND)

        panel.SetSizerAndFit(sizer)
        return panel

    def create_export_section(self, parent):
        """Create the advanced, close, and render buttons."""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddStretchSpacer()
        arow = wx.Panel(panel)
        asizer = wx.BoxSizer(wx.HORIZONTAL)
        self.adv_btn = CustomButton(arow, label="", icon='mdi-cog', primary=False, size=(36, 36))
        self.adv_btn.Bind(wx.EVT_BUTTON, self.main_panel.on_advanced_options)
        asizer.Add(self.adv_btn, 0, wx.RIGHT, 8)
        self.can_btn = CustomButton(arow, label="CLOSE", icon='mdi-exit-to-app', primary=False, danger=True, size=(110, 36))
        self.can_btn.Bind(wx.EVT_BUTTON, self.main_panel.on_cancel)
        asizer.Add(self.can_btn, 0, wx.RIGHT, 8)
        self.render_btn = CustomButton(arow, label="RENDER", icon='mdi-video-vintage', primary=True, size=(150, 36))
        self.render_btn.Bind(wx.EVT_BUTTON, self.main_panel.on_render)
        asizer.Add(self.render_btn, 1, wx.EXPAND)
        arow.SetSizerAndFit(asizer)
        self.export_row_sizer = asizer
        sizer.Add(arow, 0, wx.EXPAND)
        panel.SetSizerAndFit(sizer)
        return panel


# Need to define SVGLogoPanel since it's used in create_header
class SVGLogoPanel(wx.Panel):
    """Panel that renders the SpinRender SVG logo."""
    def __init__(self, parent, size=(58, 58)):
        super().__init__(parent, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        plugin_dir = Path(__file__).parent.parent
        svg_path = plugin_dir / "resources" / "logo.svg"
        if not svg_path.exists():
            svg_path = plugin_dir.parent / "res" / "logo.svg"
        self.svg_image = None
        if svg_path.exists():
            try:
                self.svg_image = wx.svg.SVGimage.CreateFromFile(str(svg_path))
            except Exception as e:
                import logging
                logger = logging.getLogger("SpinRender")
                logger.error(f"Failed to load SVG: {e}", exc_info=True)
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
                self.svg_image.RenderToGC(gc, 1.0)
            except Exception:
                gc.SetBrush(wx.Brush(_theme.color("colors.accent.primary")))
                gc.DrawRectangle(0, 0, width, height)
