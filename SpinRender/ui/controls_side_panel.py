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
from SpinRender.core.locale import Locale
_theme = Theme.current()
_locale = Locale.current()
from .helpers import create_section_label, create_numeric_input


class ControlsSidePanel(wx.Panel):
    """
    Left sidebar panel containing all rendering controls.
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
        self.scrolled_panel = scrolled.ScrolledPanel(parent, size=(400, -1))
        self.scrolled_panel.SetBackgroundColour(_theme.color("components.main.frame.bg"))
        self.scrolled_panel.SetupScrolling(scroll_x=False, scroll_y=True, rate_y=20)
        sizer = wx.BoxSizer(wx.VERTICAL)

        padding = 16

        self.header_panel = self.create_header(self.scrolled_panel)
        sizer.Add(self.header_panel, 0, wx.EXPAND)

        self.div1 = wx.Panel(self.scrolled_panel, size=(-1, 1))
        self.div1.SetBackgroundColour(_theme.color("borders.default.color"))
        sizer.Add(self.div1, 0, wx.EXPAND)

        presets = self.create_preset_section(self.scrolled_panel)
        sizer.Add(presets, 0, wx.EXPAND | wx.ALL, padding)

        self.div2 = wx.Panel(self.scrolled_panel, size=(-1, 1))
        self.div2.SetBackgroundColour(_theme.color("borders.default.color"))
        sizer.Add(self.div2, 0, wx.EXPAND)

        params = self.create_parameters_section(self.scrolled_panel)
        sizer.Add(params, 0, wx.EXPAND | wx.ALL, padding)

        self.div3 = wx.Panel(self.scrolled_panel, size=(-1, 1))
        self.div3.SetBackgroundColour(_theme.color("borders.default.color"))
        sizer.Add(self.div3, 0, wx.EXPAND)

        output_settings = self.create_output_settings_section(self.scrolled_panel)
        sizer.Add(output_settings, 1, wx.EXPAND | wx.ALL, padding)

        self.div4 = wx.Panel(self.scrolled_panel, size=(-1, 1))
        self.div4.SetBackgroundColour(_theme.color("borders.default.color"))
        sizer.Add(self.div4, 0, wx.EXPAND)

        export = self.create_export_section(self.scrolled_panel)
        sizer.Add(export, 0, wx.EXPAND | wx.ALL, padding)

        self.scrolled_panel.SetSizer(sizer)
        required_h = sizer.CalcMin().y + 40
        self.scrolled_panel.SetMinSize((400, required_h))
        sizer.Fit(self.scrolled_panel)
        return self.scrolled_panel

    def create_header(self, parent):
        """Create the logo and title header."""
        header = wx.Panel(parent, size=(-1, 90))
        header.SetBackgroundColour(_theme.color("components.main.leftpanel.bg"))
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        logo = SVGLogoPanel(header, size=(58, 58))
        sizer.Add(logo, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 16)

        title_sizer = wx.BoxSizer(wx.VERTICAL)
        self.header_title = wx.StaticText(header, label=_locale.get("component.main.header.title", "SPINRENDER"))
        # Header title color and font will be applied in reapply_theme
        title_sizer.Add(self.header_title, 0)

        self.header_subtitle = wx.StaticText(header, label=_locale.get("component.main.header.subtitle", "0.9 alpha"))
        title_sizer.Add(self.header_subtitle, 0)
        sizer.Add(title_sizer, 0, wx.ALIGN_CENTER_VERTICAL)

        sizer.AddStretchSpacer()
        
        # Close button - use id syntax for auto-derivation
        self.header_close_btn = CustomButton(header, id="close", label="", ghost=True, size=(36, 36))
        
        self.header_close_btn.Bind(wx.EVT_BUTTON, self.main_panel.on_close)
        sizer.Add(self.header_close_btn, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 16)

        header.SetSizerAndFit(sizer)
        self.main_panel.enable_drag(header)
        return header

    def reapply_theme(self):
        """Re-apply theme to static container elements and labels after hot-reload."""
        self.SetBackgroundColour(_theme.color("components.main.frame.bg"))
        
        if hasattr(self, 'scrolled_panel'):
            self.scrolled_panel.SetBackgroundColour(_theme.color("components.main.frame.bg"))
            
        if hasattr(self, 'header_panel'):
            self.header_panel.SetBackgroundColour(_theme.color("components.main.header.bg"))
            
        # 1. Update Global Text Styles
        if hasattr(self, 'header_title'):
            style = TextStyles.title
            self.header_title.SetForegroundColour(style.color)
            self.header_title.SetFont(style.create_font())
            self.header_title.SetLabel(style.format_text(self.header_title.GetLabel()))
            
        if hasattr(self, 'header_subtitle'):
            style = TextStyles.version
            self.header_subtitle.SetForegroundColour(style.color)
            self.header_subtitle.SetFont(style.create_font())
            
        # 2. Update Subheaders
        subheader_style = TextStyles.subheader
        for attr in ['rot_heading', 'period_heading', 'dir_heading', 'light_heading', 
                     'format_heading', 'res_heading', 'bg_heading']:
            if hasattr(self, attr):
                lbl = getattr(self, attr)
                lbl.SetForegroundColour(subheader_style.color)
                lbl.SetFont(subheader_style.create_font())
                
        # 3. Update Metadata/Hints
        meta_style = TextStyles.metadata
        for attr in ['rot_desc', 'period_desc', 'light_hint', 'frame_count']:
            if hasattr(self, attr):
                lbl = getattr(self, attr)
                lbl.SetForegroundColour(meta_style.color)
                lbl.SetFont(meta_style.create_font())

        # 4. Update Dividers
        for attr in ['div1', 'div2', 'div3', 'div4']:
            if hasattr(self, attr):
                getattr(self, attr).SetBackgroundColour(_theme.color("components.main.divider.bg"))

        # Refresh all components recursively to trigger their internal on_paint lookups
        def refresh_recursive(window):
            window.Refresh()
            for child in window.GetChildren():
                refresh_recursive(child)
        
        refresh_recursive(self)
        self.Update()

    def create_preset_section(self, parent):
        """Create the preset selection buttons."""
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(_theme.TRANSPARENT)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(create_section_label(panel, _locale.get("sections.presets", "LOOP PRESET"), id="presets"), 0, wx.EXPAND | wx.BOTTOM, 8)

        preset_row = wx.Panel(panel)
        preset_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        preset_ids = ["hero", "spin", "flip", "custom"]
        self.preset_buttons = {}
        for i, pid in enumerate(preset_ids):
            # PresetCard handles label/icon lookup internally via ID-driven mapping
            btn = PresetCard(preset_row, id=f"card{i+1}", size=(90, 64))
            btn.Bind(wx.EVT_BUTTON, lambda e, p=pid: self.main_panel.on_preset_change(p))
            if self.settings.preset == pid:
                btn.SetSelected(True)
            self.preset_buttons[pid] = btn
            flags = wx.EXPAND
            if i < len(preset_ids) - 1:
                flags |= wx.RIGHT
            preset_sizer.Add(btn, 1, flags, 8)

        preset_row.SetSizerAndFit(preset_sizer)
        sizer.Add(preset_row, 0, wx.EXPAND)
        panel.SetSizerAndFit(sizer)
        return panel

    def create_parameters_section(self, parent):
        """Create the collapsible parameters section."""
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(_theme.TRANSPARENT)
        sizer = wx.BoxSizer(wx.VERTICAL)

        header = wx.Panel(panel)
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        header_sizer.Add(create_section_label(header, _locale.get("sections.parameters", "PARAMETERS"), id="parameters"), 1, wx.ALIGN_CENTER_VERTICAL)
        
        # Save Preset Button - simplified id syntax
        save_btn = CustomButton(header, id="save_preset", size=(120, 28))
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
        self.rot_heading = wx.StaticText(panel, label=_locale.get("parameters.rotation_heading", "ROTATION SETTINGS"))
        sizer.Add(self.rot_heading, 0, wx.BOTTOM, 6)

        # V2: Fetch icon_ref from locale for each axis. Colors are now ID-driven.
        row1 = self.create_axis_control(
            panel, "BOARD TILT", self.settings.board_tilt, 
            _locale.get("parameters.board_tilt.icon_ref", "axis-x"),
            -90, 90, locale_key="parameters.board_tilt.label", id="primary"
        )
        sizer.Add(row1, 0, wx.EXPAND | wx.BOTTOM, 4)
        
        row2 = self.create_axis_control(
            panel, "BOARD ROLL", self.settings.board_roll, 
            _locale.get("parameters.board_roll.icon_ref", "axis-y"),
            -180, 180, locale_key="parameters.board_roll.label", id="secondary"
        )
        sizer.Add(row2, 0, wx.EXPAND | wx.BOTTOM, 4)
        
        row3 = self.create_axis_control(
            panel, "SPIN TILT", self.settings.spin_tilt, 
            _locale.get("parameters.spin_tilt.icon_ref", "axis-y-rot"),
            -90, 90, locale_key="parameters.spin_tilt.label", id="tertiary"
        )
        sizer.Add(row3, 0, wx.EXPAND | wx.BOTTOM, 4)
        
        row4 = self.create_axis_control(
            panel, "SPIN HEADING", self.settings.spin_heading, 
            _locale.get("parameters.spin_heading.icon_ref", "axis-z-rot"),
            -180, 180, locale_key="parameters.spin_heading.label", id="quaternary"
        )
        sizer.Add(row4, 0, wx.EXPAND | wx.BOTTOM, 4)

        self.rot_desc = wx.StaticText(panel, label=_locale.get("parameters.rotation_desc", "BOARD: ORIENT ON SPINDLE | SPIN: ORIENT THE SPINDLE ITSELF"))
        sizer.Add(self.rot_desc, 0)
        panel.SetSizerAndFit(sizer)
        return panel

    def create_axis_control(self, parent, label_text, def_val, icon_name, min_val, max_val, locale_key=None, id="default"):
        """Create a labeled slider + numeric input row."""
        row = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        label_part = wx.Panel(row, size=(130, -1))
        lp_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # icon_name is now a glyph name (e.g., 'axis-x-arrow'), call theme.glyph()
        icon_char = _theme.glyph(icon_name)
        
        # Get axis color from theme if it exists, otherwise default to primary
        axis_token = f"components.slider.{id}.nub.color"
        axis_col = _theme.color(axis_token) if _theme.has_token(axis_token) else _theme.color("colors.primary")

        if icon_char:
            icon_lbl = wx.StaticText(label_part, label=icon_char)
            icon_lbl.SetForegroundColour(axis_col)
            icon_lbl.SetFont(_theme.font("icon"))
            lp_sizer.Add(icon_lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        resolved_label = _locale.get(locale_key, label_text) if locale_key else label_text
        lbl = wx.StaticText(label_part, label=f"{resolved_label}:")
        lbl.SetForegroundColour(axis_col)
        lbl.SetFont(_theme.font("label"))
        lp_sizer.Add(lbl, 0, wx.ALIGN_CENTER_VERTICAL)
        label_part.SetSizer(lp_sizer)
        sizer.Add(label_part, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)

        slider = CustomSlider(row, value=def_val, min_val=min_val, max_val=max_val, size=(-1, 18), id=id)
        sizer.Add(slider, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)

        inp = create_numeric_input(row, f"{def_val:.2f}", "°", editable=True, min_val=min_val, max_val=max_val, id="slider")
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
        self.period_heading = wx.StaticText(panel, label=_locale.get("parameters.period.label", "ROTATION PERIOD"))
        sizer.Add(self.period_heading, 0, wx.BOTTOM, 6)


        crow = wx.Panel(panel)
        csizer = wx.BoxSizer(wx.HORIZONTAL)
        p_val = self.settings.period
        self.period_slider = CustomSlider(crow, value=p_val, min_val=0.1, max_val=30, size=(-1, 18), id="primary")
        csizer.Add(self.period_slider, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        unit = _locale.get("parameters.period.unit", "sec")
        self.period_input = create_numeric_input(crow, f"{p_val:.1f}", unit, editable=True, min_val=0.1, max_val=30, id="slider")
        csizer.Add(self.period_input, 0, wx.ALIGN_CENTER_VERTICAL)
        crow.SetSizerAndFit(csizer)
        sizer.Add(crow, 0, wx.EXPAND | wx.BOTTOM, 6)

        mrow = wx.Panel(panel)
        msizer = wx.BoxSizer(wx.HORIZONTAL)
        self.period_desc = wx.StaticText(mrow, label=_locale.get("parameters.period.desc", "SPEED OF 360° SPIN"))
        msizer.Add(self.period_desc, 1)
        self.frame_count = wx.StaticText(mrow, label=f"{int(p_val * 30)} f")
        msizer.Add(self.frame_count, 0)
        mrow.SetSizerAndFit(msizer)
        sizer.Add(mrow, 0, wx.EXPAND)
        panel.SetSizerAndFit(sizer)
        return panel

    def create_direction_control(self, parent):
        """Create the direction toggle (CW/CCW)."""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.dir_heading = wx.StaticText(panel, label=_locale.get("parameters.direction.label", "DIRECTION"))
        sizer.Add(self.dir_heading, 0, wx.BOTTOM, 6)

        
        # V2: Fetch labels and icon refs from locale
        dir_options = [
            {'label': _locale.get("parameters.direction.options.ccw.label", "CCW"), 
             'icon': _locale.get("parameters.direction.options.ccw.icon_ref", "glyphs.ccw")},
            {'label': _locale.get("parameters.direction.options.cw.label", "CW"), 
             'icon': _locale.get("parameters.direction.options.cw.icon_ref", "glyphs.cw")}
        ]
        
        self.dir_toggle = CustomToggleButton(panel, options=dir_options, size=(210, 32), id="direction")
        initial_idx = 1 if self.settings.direction == 'cw' else 0
        self.dir_toggle.SetSelection(initial_idx)
        sizer.Add(self.dir_toggle, 0)
        panel.SetSizerAndFit(sizer)
        return panel

    def create_lighting_control(self, parent):
        """Create the lighting preset toggle."""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.light_heading = wx.StaticText(panel, label=_locale.get("parameters.lighting.label", "LIGHTING"))
        sizer.Add(self.light_heading, 0, wx.BOTTOM, 6)

        
        # V2: Fetch labels and icon refs from locale
        self.light_options = [
            {'id': 'studio', 
             'label': _locale.get("parameters.lighting.options.studio.label", "STUDIO"), 
             'icon': _locale.get("parameters.lighting.options.studio.icon_ref", "glyphs.sun")},
            {'id': 'dramatic', 
             'label': _locale.get("parameters.lighting.options.dramatic.label", "DRAMATIC"), 
             'icon': _locale.get("parameters.lighting.options.dramatic.icon_ref", "glyphs.bolt")},
            {'id': 'soft', 
             'label': _locale.get("parameters.lighting.options.soft.label", "SOFT"), 
             'icon': _locale.get("parameters.lighting.options.soft.icon_ref", "glyphs.cloud")},
            {'id': 'workspace', 
             'label': _locale.get("parameters.lighting.options.workspace.label", "WORKSPACE"), 
             'icon': _locale.get("parameters.lighting.options.workspace.icon_ref", "glyphs.edit")}
        ]
        
        self.light_toggle = CustomToggleButton(panel, options=self.light_options, size=(320, 32), id="lighting")
        current_light = self.settings.lighting
        initial_idx = next((i for i, opt in enumerate(self.light_options) if opt['id'] == current_light), 0)
        self.light_toggle.SetSelection(initial_idx)
        sizer.Add(self.light_toggle, 0, wx.EXPAND)

        self.light_hint = wx.StaticText(panel, label=_locale.get("parameters.lighting_hint", "SELECT WORKSPACE TO USE KICAD 3D VIEWER SETTINGS"))
        sizer.Add(self.light_hint, 0, wx.TOP, 4)

        panel.SetSizerAndFit(sizer)
        return panel

    def create_output_settings_section(self, parent):
        """Create format, resolution, and background color controls."""
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(_theme.TRANSPARENT)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(create_section_label(panel, _locale.get("sections.output", "OUTPUT SETTINGS"), id="output"), 0, wx.EXPAND | wx.BOTTOM, 10)

        # Row 1: Format and Resolution
        cols_panel = wx.Panel(panel)
        cols_sizer = wx.BoxSizer(wx.HORIZONTAL)
        f_col = wx.Panel(cols_panel)
        f_sizer = wx.BoxSizer(wx.VERTICAL)
        self.format_heading = wx.StaticText(f_col, label=_locale.get("parameters.format.label", "FORMAT"))
        f_sizer.Add(self.format_heading, 0, wx.BOTTOM, 6)

        self.format_choices = ["MP4 (H.264)", "GIF", "PNG Sequence"]
        self.format_ids = ["mp4", "gif", "png_sequence"]
        self.format_choice = CustomDropdown(f_col, choices=self.format_choices, size=(-1, 32), id="format")
        curr_fmt = self.settings.format
        fmt_idx = self.format_ids.index(curr_fmt) if curr_fmt in self.format_ids else 0
        self.format_choice.SetSelection(fmt_idx)
        f_sizer.Add(self.format_choice, 0, wx.EXPAND)
        f_col.SetSizerAndFit(f_sizer)
        cols_sizer.Add(f_col, 1, wx.EXPAND | wx.RIGHT, 12)

        r_col = wx.Panel(cols_panel)
        r_sizer = wx.BoxSizer(wx.VERTICAL)
        self.res_heading = wx.StaticText(r_col, label=_locale.get("parameters.resolution.label", "RESOLUTION"))
        r_sizer.Add(self.res_heading, 0, wx.BOTTOM, 6)

        self.res_choices = ["1920×1080 (1080P)", "1280×720 (720P)", "800×800 (Square)"]
        self.res_ids = ["1920x1080", "1280x720", "800x800"]
        self.res_choice = CustomDropdown(r_col, choices=self.res_choices, size=(-1, 32), id="resolution")
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
        self.bg_heading = wx.StaticText(bg_col, label=_locale.get("parameters.bg_color.label", "BACKGROUND COLOR"))
        bg_vsizer.Add(self.bg_heading, 0, wx.BOTTOM, 6)

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
        
        # V2: Fetch labels and icon references from locale for export row
        self.adv_btn = CustomButton(arow, id="options", size=(36, 36))
        self.adv_btn.Bind(wx.EVT_BUTTON, self.main_panel.on_advanced_options)
        asizer.Add(self.adv_btn, 0, wx.RIGHT, 8)

        self.can_btn = CustomButton(arow, id="close", size=(110, 36))
        self.can_btn.Bind(wx.EVT_BUTTON, self.main_panel.on_cancel)
        asizer.Add(self.can_btn, 0, wx.RIGHT, 8)

        self.render_btn = CustomButton(arow, id="render")

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
                gc.SetBrush(wx.Brush(_theme.color("colors.primary")))
                gc.DrawRectangle(0, 0, width, height)
