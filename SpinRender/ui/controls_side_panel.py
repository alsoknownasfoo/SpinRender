"""
ControlsSidePanel - Extracted left sidebar UI construction from SpinRenderPanel.

This panel contains all the controls for rendering parameters, presets, and output settings.
"""
import wx
from SpinRender.utils.wx_svg_compat import ensure_wx_svg
ensure_wx_svg()
import wx.svg
import wx.lib.scrolledpanel as scrolled
from pathlib import Path

from .custom_controls import (
    CustomSlider, CustomToggleButton, CustomButton, CustomCheckbox,
    PresetCard, CustomDropdown, CustomColorPicker, SectionToggle
)
from .text_styles import TextStyle
from .registry import ControlRegistry
from SpinRender.core.theme import Theme
from SpinRender.core.locale import Locale
from SpinRender.version import get_version
_theme = Theme.current()
_locale = Locale.current()
from .helpers import create_section_label, create_numeric_input, create_text, reapply_text_styles, load_svg, set_text_widget_state, effective_background


# Built-in output resolutions: (display label, "WxH" id). Custom resolutions
# added by the user are appended after these and persisted in settings.
BUILTIN_RESOLUTIONS = [
    ("3840×2160 (4K)", "3840x2160"),
    ("2160×3840 (4K Phone/Tablet)", "2160x3840"),
    ("2160×2160 (4K Square)", "2160x2160"),
    ("1920×1080 (1080P)", "1920x1080"),
    ("1280×720 (720P)", "1280x720"),
    ("800×800 (Square)", "800x800"),
]


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

        # Registry of all UI controls, populated automatically via self-registration.
        # Query with _registry.filter(section='parameters') etc.
        self._registry = ControlRegistry()

        # Build the UI - now returns a container with scrolled content + footer
        controls_panel = self.create_controls_panel(self)

        # Set up sizer for this panel
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(controls_panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        sizer.Fit(self)

    def _reg(self, ctrl, section=None):
        """Register a parameter control and return it unchanged."""
        self._registry.append({
            'control': ctrl,
            'type':    type(ctrl).__name__,
            'id':      getattr(ctrl, '_id', None),
            'section': section,
        })
        return ctrl

    def create_controls_panel(self, parent):
        """Create the main controls container with scrollable content and persistent footer."""
        # Main container that holds everything
        main_container = wx.Panel(parent)
        main_container.SetBackgroundColour(_theme.color("layout.main.frame.bg"))
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Get uniform padding from theme (theme values are 96dpi design pixels;
        # scale to the display's actual DPI like the rest of the layout)
        padding = self.FromDIP(_theme._parse_padding(_theme._resolve("layout.main.leftpanel.padding") or 16)['left'])
        self.padding = padding  # Store for use in sub-layouts

        # Header (always visible at top)
        self.header_panel = self.create_header(main_container)
        main_sizer.Add(self.header_panel, 0, wx.EXPAND)

        # Divider after header
        self._header_divider = wx.Panel(main_container, size=(-1, 1))
        self._header_divider.SetBackgroundColour(_theme.color("dividers.default.color"))
        main_sizer.Add(self._header_divider, 0, wx.EXPAND)

        # Scrollable content area (presets, parameters, output)
        self.scrolled_panel = scrolled.ScrolledPanel(main_container, size=self.FromDIP(wx.Size(400, -1)))
        self.scrolled_panel.SetBackgroundColour(_theme.color("layout.main.frame.bg"))
        self.scrolled_panel.SetupScrolling(scroll_x=False, scroll_y=True, rate_y=20)
        content_sizer = wx.BoxSizer(wx.VERTICAL)

        # Presets section
        presets = self.create_preset_section(self.scrolled_panel)
        content_sizer.Add(presets, 0, wx.EXPAND | wx.ALL, padding)

        self.div2 = wx.Panel(self.scrolled_panel, size=(-1, 1))
        self.div2.SetBackgroundColour(_theme.color("dividers.default.color"))
        content_sizer.Add(self.div2, 0, wx.EXPAND)

        # Parameters section
        params = self.create_parameters_section(self.scrolled_panel)
        content_sizer.Add(params, 0, wx.EXPAND | wx.ALL, padding)

        self.div3 = wx.Panel(self.scrolled_panel, size=(-1, 1))
        self.div3.SetBackgroundColour(_theme.color("dividers.default.color"))
        content_sizer.Add(self.div3, 0, wx.EXPAND)

        # Output settings section. Proportion 0 (not 1) so it sits naturally
        # after Parameters instead of stretching to fill — otherwise it gets
        # anchored to the bottom when the window is taller than the content.
        output_settings = self.create_output_settings_section(self.scrolled_panel)
        content_sizer.Add(output_settings, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, padding)

        self.scrolled_panel.SetSizer(content_sizer)
        self.scrolled_panel.Layout()

        # Calculate minimum height needed to display all content without scrolling.
        # Measured while Parameters is expanded so the window is sized to the
        # expanded view; collapsing later just leaves empty space rather than
        # shrinking the window.
        min_height = content_sizer.CalcMin().y
        # Add extra padding for comfortable viewing
        required_h = min_height + self.FromDIP(40)
        self.scrolled_panel.SetMinSize((self.FromDIP(400), required_h))

        # Now apply the persisted collapsed states without disturbing the scroll
        # area's min height established above. Each collapsed section's own panel
        # min size must be recomputed (its children are hidden but SetSizerAndFit
        # already locked in the expanded height); otherwise sections below it stay
        # anchored beneath a full-height, empty panel.
        if self.settings.params_collapsed:
            self._apply_params_collapsed(True)
            self._params_sizer.Layout()
            self._params_panel.SetMinSize(self._params_sizer.CalcMin())
        if self.settings.output_collapsed:
            self._apply_output_collapsed(True)
            self._output_sizer.Layout()
            self._output_panel.SetMinSize(self._output_sizer.CalcMin())
        if self.settings.params_collapsed or self.settings.output_collapsed:
            content_sizer.Layout()

        main_sizer.Add(self.scrolled_panel, 1, wx.EXPAND)

        # Divider before footer (distinctive separator)
        self._footer_divider = wx.Panel(main_container, size=(-1, 1))
        self._footer_divider.SetBackgroundColour(_theme.color("dividers.default.color"))
        main_sizer.Add(self._footer_divider, 0, wx.EXPAND)

        # Persistent footer with action buttons
        self.footer_panel = self.create_footer_panel(main_container)
        main_sizer.Add(self.footer_panel, 0, wx.EXPAND)

        main_container.SetSizer(main_sizer)
        main_sizer.Fit(main_container)
        return main_container

    def create_header(self, parent):
        """Create the logo and title header."""
        header = wx.Panel(parent, size=(-1, 90))
        header.SetBackgroundColour(_theme.color("layout.main.leftpanel.bg"))
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        logo = SVGLogoPanel(header, size=(58, 58))
        sizer.Add(logo, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 16)

        title_sizer = wx.BoxSizer(wx.VERTICAL)
        self.header_title = create_text(header, _locale.get("component.main.header.title", "SPINRENDER"), "title")
        title_sizer.Add(self.header_title, 0)

        self.header_subtitle = create_text(header, get_version(), "version")
        title_sizer.Add(self.header_subtitle, 0)
        sizer.Add(title_sizer, 0, wx.ALIGN_CENTER_VERTICAL)

        sizer.AddStretchSpacer()
        
        # Close button - use id syntax for auto-derivation
        self.header_close_btn = CustomButton(header, id="close", label="", size=(36, 36))
        
        self.header_close_btn.Bind(wx.EVT_BUTTON, self.main_panel.on_close)
        sizer.Add(self.header_close_btn, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 16)

        header.SetSizerAndFit(sizer)
        self.main_panel.enable_drag(header)
        return header

    def reapply_theme(self):
        """Re-apply theme to static container elements and labels after hot-reload."""
        self.SetBackgroundColour(_theme.color("layout.main.frame.bg"))

        if hasattr(self, 'scrolled_panel'):
            self.scrolled_panel.SetBackgroundColour(_theme.color("layout.main.frame.bg"))

        if hasattr(self, 'header_panel'):
            self.header_panel.SetBackgroundColour(_theme.color("layout.main.header.bg"))

        if hasattr(self, 'footer_panel'):
            footer_bg = _theme.color("layout.main.leftpanel.bg") or _theme.color("colors.secondary")
            self.footer_panel.SetBackgroundColour(footer_bg)

        if hasattr(self, 'preset_row'):
            self.preset_row.SetBackgroundColour(_theme.TRANSPARENT)

        # 1. Re-apply all registered text styles globally
        reapply_text_styles()

        # 2. Update preset row container (PresetCard.on_paint clears to parent bg)
        if hasattr(self, '_preset_row'):
            self._preset_row.SetBackgroundColour(_theme.color("layout.main.frame.bg"))

        # 3. Update Dividers
        for attr in ['_header_divider', '_footer_divider', 'div2', 'div3']:
            if hasattr(self, attr):
                getattr(self, attr).SetBackgroundColour(_theme.color("dividers.default.color"))

        # Propagate reapply_theme() to child controls that support geometry updates,
        # then refresh all components to trigger their internal on_paint lookups.
        def reapply_recursive(window):
            if window is not self and hasattr(window, 'reapply_theme') and callable(window.reapply_theme):
                window.reapply_theme()
            window.Refresh()
            for child in window.GetChildren():
                reapply_recursive(child)

        reapply_recursive(self)
        self.Update()

    def create_preset_section(self, parent):
        """Create the preset selection buttons."""
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(_theme.TRANSPARENT)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(create_section_label(panel, _locale.get("sections.presets", "LOOP PRESETS"), id="presets"), 0, wx.EXPAND | wx.BOTTOM, 8)

        preset_row = wx.Panel(panel)
        self.preset_row = preset_row
        self._preset_row = preset_row
        preset_row.SetBackgroundColour(_theme.TRANSPARENT)
        preset_sizer = wx.BoxSizer(wx.HORIZONTAL)

        preset_ids = ["hero", "spin", "flip", "custom"]
        self.preset_buttons = {}
        for i, pid in enumerate(preset_ids):
            # PresetCard handles label/icon lookup internally via ID-driven mapping
            btn = PresetCard(preset_row, id=f"card{i+1}", size=(90, 64), section='presets')
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
        header.SetBackgroundColour(_theme.TRANSPARENT)
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        section_label = create_section_label(header, _locale.get("sections.parameters", "PARAMETERS"), id="parameters")

        # Title, then the expand/collapse toggle to its RIGHT (12x12, 5px gap).
        self._params_title = section_label
        header_sizer.Add(section_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.params_toggle = SectionToggle(
            header, size=12, y_nudge=1,
            collapsed=self.settings.params_collapsed,
            on_toggle=self.on_params_toggle,
        )
        header_sizer.Add(self.params_toggle, 0, wx.ALIGN_CENTER_VERTICAL)
        header_sizer.AddStretchSpacer()

        # Save Preset Button - use themed component definition
        self.save_btn = CustomButton(header, id="save_preset", size=(100, 24), section='parameters')
        self.save_btn.Bind(wx.EVT_BUTTON, self.main_panel.on_save_preset)
        header_sizer.Add(self.save_btn, 0, wx.ALIGN_CENTER_VERTICAL)

        header.SetSizerAndFit(header_sizer)

        # Whole header acts as a toggle hit area, except the save-preset button
        # (and the toggle itself, which carries its own handler).
        self._bind_header_toggle(
            header, self._on_params_header_click,
            exclude={self.save_btn, self.params_toggle},
        )
        # Hovering anywhere on the line (minus the save button) highlights both
        # the title and the toggle together.
        self._bind_header_hover(
            header,
            lambda state: self._set_header_hover(self.params_toggle, self._params_title, state),
            exclude={self.save_btn},
        )

        self._params_panel = panel
        self._params_sizer = sizer
        sizer.Add(header, 0, wx.EXPAND | wx.BOTTOM, 10)
        self._params_header_item = sizer.GetItem(header)

        # Collapsible body — hidden when collapsed so only the title shows.
        self._params_content = [
            self.create_rotation_controls(panel),
            self.create_period_control(panel),
            self.create_direction_control(panel),
            self.create_lighting_control(panel),
        ]
        sizer.Add(self._params_content[0], 0, wx.EXPAND | wx.BOTTOM, 10)
        sizer.Add(self._params_content[1], 0, wx.EXPAND | wx.BOTTOM, 10)
        sizer.Add(self._params_content[2], 0, wx.EXPAND | wx.BOTTOM, 10)
        sizer.Add(self._params_content[3], 0, wx.EXPAND)

        # Build in the expanded state so the panel measures at full height.
        # The persisted collapsed state is applied later (after the scroll
        # area's min height is computed) so the window sizes to the expanded
        # view rather than the collapsed one.
        panel.SetSizerAndFit(sizer)
        return panel

    def _bind_header_toggle(self, widget, handler, exclude):
        """Recursively make a section header (and its children) a click target.

        Subtrees in `exclude` keep their own handlers and are skipped.
        """
        if widget in exclude:
            return
        widget.Bind(wx.EVT_LEFT_DOWN, handler)
        if hasattr(widget, 'SetCursor'):
            widget.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        for child in widget.GetChildren():
            self._bind_header_toggle(child, handler, exclude)

    def _bind_header_hover(self, root, on_change, exclude):
        """Make the whole header (minus `exclude` subtrees) a shared hover zone.

        Entering any target turns the section's hover on; leaving turns it off
        only when the pointer has left every target (so moving between the title
        and toggle doesn't flicker, and hovering the save button doesn't count).

        Excluded subtrees still get enter/leave bindings: their screen rects sit
        inside the header root's rect, so without them the hover state would
        stay on while the pointer is over (or exits through) an excluded widget.
        """
        targets, excluded = [], []

        def collect(widget, into):
            into.append(widget)
            for child in widget.GetChildren():
                collect(child, into)

        def collect_targets(widget):
            if widget in exclude:
                collect(widget, excluded)
                return
            targets.append(widget)
            for child in widget.GetChildren():
                collect_targets(child)

        collect_targets(root)

        def pointer_in_targets():
            mouse_pos = wx.GetMousePosition()
            for widget in excluded:
                rect = widget.GetScreenRect()
                if rect and rect.Contains(mouse_pos):
                    return False
            for widget in targets:
                rect = widget.GetScreenRect()
                if rect and rect.Contains(mouse_pos):
                    return True
            return False

        def update(event):
            on_change(pointer_in_targets())
            event.Skip()

        for widget in targets + excluded:
            widget.Bind(wx.EVT_ENTER_WINDOW, update)
            widget.Bind(wx.EVT_LEAVE_WINDOW, update)

    def _set_header_hover(self, toggle, title_label, hovered):
        """Apply the shared hover color to a section's toggle icon and title."""
        # toggle.hovered tracks the section's current state; skip redundant work
        # as the pointer moves between child widgets within the header.
        if toggle.hovered == bool(hovered):
            return
        toggle.set_hovered(hovered)
        set_text_widget_state(
            title_label._txt,
            color_token="colors.primary" if hovered else None,
        )

    def _relayout_section(self, panel, sizer):
        """Reflow a collapsed/expanded section and the surrounding scroll area."""
        sizer.Layout()
        panel.SetMinSize(sizer.CalcMin())
        if hasattr(self, 'scrolled_panel'):
            self.scrolled_panel.Layout()
            self.scrolled_panel.SetupScrolling(
                scroll_x=False, scroll_y=True, rate_y=20, scrollToTop=False
            )
        self.Layout()
        if hasattr(self.main_panel, 'save_settings'):
            self.main_panel.save_settings()

    def _apply_params_collapsed(self, collapsed):
        """Show/hide the parameters body and keep top/bottom padding symmetric."""
        show = not collapsed
        if hasattr(self, 'save_btn'):
            self.save_btn.Show(show)
        for child in getattr(self, '_params_content', []):
            child.Show(show)
        # When collapsed, drop the header's bottom margin so the gap to the
        # divider below matches the padding above the title.
        if getattr(self, '_params_header_item', None) is not None:
            self._params_header_item.SetBorder(0 if collapsed else 10)

    def on_params_toggle(self, collapsed):
        """Persist and apply a parameters expand/collapse change."""
        self.settings.params_collapsed = collapsed
        self._apply_params_collapsed(collapsed)
        self._relayout_section(self._params_panel, self._params_sizer)

    def _on_params_header_click(self, event):
        """Toggle parameters when the header (outside the save button) is clicked."""
        new_state = not self.settings.params_collapsed
        self.params_toggle.set_collapsed(new_state)
        self.on_params_toggle(new_state)

    def _apply_output_collapsed(self, collapsed):
        """Show/hide the output-settings body, keeping header padding tidy."""
        show = not collapsed
        for child in getattr(self, '_output_content', []):
            child.Show(show)
        if getattr(self, '_output_header_item', None) is not None:
            self._output_header_item.SetBorder(0 if collapsed else 10)

    def on_output_toggle(self, collapsed):
        """Persist and apply an output-settings expand/collapse change."""
        self.settings.output_collapsed = collapsed
        self._apply_output_collapsed(collapsed)
        self._relayout_section(self._output_panel, self._output_sizer)

    def _on_output_header_click(self, event):
        """Toggle output settings when its header is clicked."""
        new_state = not self.settings.output_collapsed
        self.output_toggle.set_collapsed(new_state)
        self.on_output_toggle(new_state)

    def create_rotation_controls(self, parent):
        """Create all rotation axis controls."""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(10)
        self.rot_heading = create_text(panel, _locale.get("parameters.rotation_heading", "ROTATION SETTINGS"), "subheader")
        sizer.Add(self.rot_heading, 0, wx.BOTTOM, 6)

        # Helper text immediately below subheader
        self.rot_desc = create_text(panel, _locale.get("parameters.rotation_desc", "BOARD: ORIENT ON SPINDLE | SPIN: ORIENT THE SPINDLE ITSELF"), "description")
        sizer.Add(self.rot_desc, 0, wx.BOTTOM, 10)

        # Fetch icon_ref from locale for each axis. Colors are ID-driven.
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

        # Back-apply the final maximum label width to all axis label panels so
        # every slider in the group ends up with the same (minimum) width.
        final_label_width = getattr(self, '_max_axis_label_width', 0)
        for lp in getattr(self, '_axis_label_parts', []):
            lp.SetMinSize((final_label_width, -1))
        # Reset tracking state so a future rebuild starts fresh
        self._axis_label_parts = []
        self._max_axis_label_width = 0

        panel.SetSizerAndFit(sizer)
        return panel

    def create_axis_control(self, parent, label_text, def_val, icon_name, min_val, max_val, locale_key=None, id="default"):
        """Create a labeled slider + numeric input row."""
        row = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddSpacer(10)

        # Build label content first to measure its width
        label_part = wx.Panel(row)
        lp_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # icon_name is now a glyph name (e.g., 'axis-x-arrow'), call theme.glyph()
        icon_char = _theme.glyph(icon_name)

        # Get axis color token from theme if it exists, otherwise fall back to primary
        axis_token = f"components.slider.{id}.nub.color"
        resolved_token = axis_token if _theme.has_token(axis_token) else "colors.primary"

        if icon_char:
            icon_lbl = create_text(label_part, icon_char, "icon", color_token=resolved_token)
            self._registry.add(icon_lbl, section='parameters')
            lp_sizer.Add(icon_lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)

        resolved_label = _locale.get(locale_key, label_text) if locale_key else label_text
        lbl = create_text(label_part, f"{resolved_label}:", "label", color_token=resolved_token)
        self._registry.add(lbl, section='parameters')
        lp_sizer.Add(lbl, 0, wx.ALIGN_CENTER_VERTICAL)

        label_part.SetSizer(lp_sizer)
        # Track label width so we can harmonise all axis labels after creation
        label_width = label_part.GetBestSize().x
        if not hasattr(self, '_max_axis_label_width'):
            self._max_axis_label_width = label_width
        else:
            self._max_axis_label_width = max(self._max_axis_label_width, label_width)
        # Register this label panel so create_rotation_controls can back-apply the max
        if not hasattr(self, '_axis_label_parts'):
            self._axis_label_parts = []
        self._axis_label_parts.append(label_part)

        sizer.Add(label_part, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)

        slider = CustomSlider(row, value=def_val, min_val=min_val, max_val=max_val, size=(-1, 18), id=id, section='parameters')
        sizer.Add(slider, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)

        # Numeric input with themed size (use component definition)
        inp = create_numeric_input(row, f"{def_val:.2f}", "°", editable=True, min_val=min_val, max_val=max_val, id="axis", section='parameters')
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
        self.period_heading = create_text(panel, _locale.get("parameters.period.label", "ROTATION PERIOD"), "subheader")
        sizer.Add(self.period_heading, 0, wx.BOTTOM, 6)

        p_val = self.settings.period
        self.period_meta_row = wx.Panel(panel)
        meta_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.period_desc = create_text(self.period_meta_row, _locale.get("parameters.period.desc", "SPEED OF 360° SPIN"), "description")
        meta_sizer.Add(self.period_desc, 0, wx.ALIGN_CENTER_VERTICAL)
        meta_sizer.AddStretchSpacer()
        self.frame_count = create_text(self.period_meta_row, f"{int(p_val * 30)} f", "description")
        meta_sizer.Add(self.frame_count, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 8)
        self.period_meta_row.SetSizerAndFit(meta_sizer)
        sizer.Add(self.period_meta_row, 0, wx.EXPAND | wx.BOTTOM, 10)

        crow = wx.Panel(panel)
        csizer = wx.BoxSizer(wx.HORIZONTAL)
        csizer.AddSpacer(10)
        self.period_slider = CustomSlider(crow, value=p_val, min_val=0.1, max_val=30, size=(-1, 18), id="default", section='parameters')
        csizer.Add(self.period_slider, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        unit = _locale.get("parameters.period.unit", "sec")
        self.period_input = create_numeric_input(crow, f"{p_val:.1f}", unit, editable=True, min_val=0.1, max_val=30, id="speed", section='parameters')
        csizer.Add(self.period_input, 0, wx.ALIGN_CENTER_VERTICAL)
        crow.SetSizerAndFit(csizer)
        sizer.Add(crow, 0, wx.EXPAND)
        panel.SetSizerAndFit(sizer)
        return panel

    def create_direction_control(self, parent):
        """Create the direction toggle (CW/CCW)."""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.dir_heading = create_text(panel, _locale.get("parameters.direction.label", "DIRECTION"), "subheader")
        sizer.Add(self.dir_heading, 0, wx.BOTTOM, 6)

        # Helper text immediately below subheader
        self.dir_desc = create_text(panel, _locale.get("parameters.direction.desc", "Rotation direction"), "description")
        sizer.Add(self.dir_desc, 0, wx.BOTTOM, 10)

        # Fetch labels and icon refs from locale
        dir_options = [
            {'label': _locale.get("parameters.direction.options.ccw.label", "CCW"),
             'icon': _locale.get("parameters.direction.options.ccw.icon_ref", "glyphs.ccw")},
            {'label': _locale.get("parameters.direction.options.cw.label", "CW"),
             'icon': _locale.get("parameters.direction.options.cw.icon_ref", "glyphs.cw")}
        ]

        csizer = wx.BoxSizer(wx.HORIZONTAL)
        csizer.AddSpacer(10)

        self.dir_toggle = CustomToggleButton(panel, options=dir_options, size=(210, 32), id="direction", section='parameters')
        initial_idx = 1 if self.settings.direction == 'cw' else 0
        self.dir_toggle.SetSelection(initial_idx)
        csizer.Add(self.dir_toggle, 0, wx.EXPAND)

        sizer.Add(csizer, 0, wx.EXPAND)
        panel.SetSizerAndFit(sizer)
        return panel

    def create_lighting_control(self, parent):
        """Create the lighting preset toggle."""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(10)
        self.light_heading = create_text(panel, _locale.get("parameters.lighting.label", "LIGHTING"), "subheader")
        sizer.Add(self.light_heading, 0, wx.BOTTOM, 6)

        # Helper text immediately below subheader
        self.light_hint = create_text(panel, _locale.get("parameters.lighting_hint", "SELECT WORKSPACE TO USE KICAD 3D VIEWER SETTINGS"), "description")
        sizer.Add(self.light_hint, 0, wx.BOTTOM, 10)

        # Fetch labels and icon refs from locale
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

        csizer = wx.BoxSizer(wx.HORIZONTAL)
        csizer.AddSpacer(10)
        self.light_toggle = CustomToggleButton(panel, options=self.light_options, size=(320, 32), id="lighting", section='parameters')
        current_light = self.settings.lighting
        initial_idx = next((i for i, opt in enumerate(self.light_options) if opt['id'] == current_light), 0)
        self.light_toggle.SetSelection(initial_idx)
        csizer.Add(self.light_toggle, 1, wx.EXPAND)
        sizer.Add(csizer, 0, wx.EXPAND)

        panel.SetSizerAndFit(sizer)
        return panel

    def create_output_settings_section(self, parent):
        """Create the collapsible format, resolution, and background color controls."""
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(_theme.TRANSPARENT)
        sizer = wx.BoxSizer(wx.VERTICAL)

        header = wx.Panel(panel)
        header.SetBackgroundColour(_theme.TRANSPARENT)
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        section_label = create_section_label(header, _locale.get("sections.output", "OUTPUT SETTINGS"), id="output")

        # Title, then the expand/collapse toggle to its RIGHT (12x12, 5px gap).
        self._output_title = section_label
        header_sizer.Add(section_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.output_toggle = SectionToggle(
            header, size=12, y_nudge=1,
            collapsed=self.settings.output_collapsed,
            on_toggle=self.on_output_toggle,
        )
        header_sizer.Add(self.output_toggle, 0, wx.ALIGN_CENTER_VERTICAL)
        header_sizer.AddStretchSpacer()

        header.SetSizerAndFit(header_sizer)

        # Whole header acts as a toggle hit area (the toggle keeps its own handler).
        self._bind_header_toggle(
            header, self._on_output_header_click, exclude={self.output_toggle}
        )
        # Hovering the line highlights both the title and the toggle together.
        self._bind_header_hover(
            header,
            lambda state: self._set_header_hover(self.output_toggle, self._output_title, state),
            exclude=set(),
        )

        self._output_panel = panel
        self._output_sizer = sizer
        sizer.Add(header, 0, wx.EXPAND | wx.BOTTOM, 10)
        self._output_header_item = sizer.GetItem(header)

        # Row 1: Format and Resolution
        cols_panel = wx.Panel(panel)
        cols_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # Heading rows are kept a fixed height so the FORMAT and RESOLUTION
        # dropdowns stay vertically aligned even though RESOLUTION carries a gear.
        head_h = 22

        f_col = wx.Panel(cols_panel)
        f_sizer = wx.BoxSizer(wx.VERTICAL)
        f_sizer.AddSpacer(10)
        # Heading is a direct child of the column so its left edge lines up with
        # the dropdown below; a zero-width spacer pins the row height so FORMAT
        # and RESOLUTION (which carries a gear) stay vertically in step.
        f_head_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.format_heading = create_text(f_col, _locale.get("parameters.format.label", "FORMAT"), "subheader")
        f_head_sizer.Add(self.format_heading, 0, wx.ALIGN_CENTER_VERTICAL)
        f_head_sizer.Add((0, self.FromDIP(head_h)))
        f_sizer.Add(f_head_sizer, 0, wx.EXPAND | wx.BOTTOM, 6)

        self.format_choices = ["MP4 (H.264)", "GIF", "PNG Sequence"]
        self.format_ids = ["mp4", "gif", "png_sequence"]
        self.format_choice = CustomDropdown(f_col, choices=self.format_choices, size=(-1, 32), id="format", section='output')
        curr_fmt = self.settings.format
        fmt_idx = self.format_ids.index(curr_fmt) if curr_fmt in self.format_ids else 0
        self.format_choice.SetSelection(fmt_idx)
        f_sizer.Add(self.format_choice, 0, wx.EXPAND)
        f_col.SetSizerAndFit(f_sizer)
        cols_sizer.Add(f_col, 1, wx.EXPAND | wx.RIGHT, 12)

        board_options_col = wx.Panel(panel)
        board_options_sizer = wx.BoxSizer(wx.VERTICAL)
        board_options_sizer.AddSpacer(10)
        self.board_options_heading = create_text(
            board_options_col,
            _locale.get("output.board_options.label", "RENDER OPTIONS"),
            "subheader",
        )
        board_options_sizer.Add(self.board_options_heading, 0, wx.BOTTOM, 6)

        self.render_options_grid = wx.FlexGridSizer(0, 3, 8, 12)
        self.render_options_grid.AddGrowableCol(0, 1)
        self.render_options_grid.AddGrowableCol(1, 1)
        self.render_options_grid.AddGrowableCol(2, 1)

        self.hide_vias_row, self.hide_vias_checkbox, self.hide_vias_label = self._create_render_option_row(
            board_options_col,
            option_id="hide_vias",
            label=_locale.get("output.hide_vias.label", "VIAS"),
            value=self.settings.hide_vias,
        )
        self.render_options_grid.Add(self.hide_vias_row, 0, wx.EXPAND)

        self.hide_components_row, self.hide_components_checkbox, self.hide_components_label = self._create_render_option_row(
            board_options_col,
            option_id="hide_components",
            label=_locale.get("output.hide_components.label", "COMPONENTS"),
            value=self.settings.hide_components,
        )
        self.render_options_grid.Add(self.hide_components_row, 0, wx.EXPAND)

        self.hide_test_points_row, self.hide_test_points_checkbox, self.hide_test_points_label = self._create_render_option_row(
            board_options_col,
            option_id="hide_test_points",
            label=_locale.get("output.hide_test_points.label", "TEST POINTS (T# REFS)"),
            value=self.settings.hide_test_points,
        )
        self.render_options_grid.Add(self.hide_test_points_row, 0, wx.EXPAND)

        board_options_sizer.Add(self.render_options_grid, 0, wx.EXPAND)

        board_options_col.SetSizer(board_options_sizer)
        sizer.Add(board_options_col, 0, wx.EXPAND | wx.BOTTOM, 12)

        r_col = wx.Panel(cols_panel)
        r_sizer = wx.BoxSizer(wx.VERTICAL)
        r_sizer.AddSpacer(10)

        # Heading row: title on the left (a direct child of the column, so it
        # left-aligns with the dropdown), a gear on the right that opens the
        # "Custom Resolutions" management dialog. The gear is head_h tall, so it
        # pins this row to the same height as the FORMAT heading row.
        res_head_sizer = wx.BoxSizer(wx.HORIZONTAL)
        res_head_sizer.AddSpacer(4)
        self.res_heading = create_text(r_col, _locale.get("parameters.resolution.label", "RESOLUTION"), "subheader")
        res_head_sizer.Add(self.res_heading, 0, wx.ALIGN_CENTER_VERTICAL)
        res_head_sizer.AddStretchSpacer()
        self.res_gear_btn = CustomButton(r_col, id="options", label="", size=(head_h, head_h), section='output')
        res_head_sizer.Add(self.res_gear_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        r_sizer.Add(res_head_sizer, 0, wx.EXPAND | wx.BOTTOM, 6)

        self.res_choices, self.res_ids = self._build_resolution_items()
        self.res_choice = CustomDropdown(r_col, choices=self.res_choices,
                                         size=(-1, 32), id="resolution", section='output')
        self.res_choice.SetSelection(self._resolution_index(self.settings.resolution))
        r_sizer.Add(self.res_choice, 0, wx.EXPAND)
        r_col.SetSizerAndFit(r_sizer)
        cols_sizer.Add(r_col, 1, wx.EXPAND)
        cols_panel.SetSizerAndFit(cols_sizer)
        sizer.Add(cols_panel, 0, wx.EXPAND | wx.BOTTOM, 12)
        self._output_content = [board_options_col, cols_panel]

        # Row 3: Background Color
        bg_col = wx.Panel(panel)
        bg_vsizer = wx.BoxSizer(wx.VERTICAL)
        bg_vsizer.AddSpacer(10)
        self.bg_heading = create_text(bg_col, _locale.get("parameters.bg_color.label", "BACKGROUND COLOR"), "subheader")
        bg_vsizer.Add(self.bg_heading, 0, wx.BOTTOM, 6)

        self.bg_picker = CustomColorPicker(bg_col, current_color=self.settings.bg_color, section='output')
        bg_vsizer.Add(self.bg_picker, 0, wx.EXPAND)

        bg_col.SetSizer(bg_vsizer)
        sizer.Add(bg_col, 0, wx.EXPAND)
        self._output_content.append(bg_col)

        # Built expanded; the persisted collapsed state is applied later (after
        # the scroll area's min height is measured), matching Parameters.
        panel.SetSizerAndFit(sizer)
        return panel

    def _create_render_option_row(self, parent, option_id, label, value):
        """Build a single render-option checkbox row for the options grid."""
        row = wx.Panel(parent)
        row.SetBackgroundColour(_theme.TRANSPARENT)
        row_sizer = wx.BoxSizer(wx.HORIZONTAL)

        checkbox = CustomCheckbox(
            row,
            size=(14, 14),
            id=option_id,
            section='output',
        )
        checkbox.SetValue(value)
        row_sizer.Add(checkbox, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)

        text = create_text(row, label, "description")
        row_sizer.Add(text, 0, wx.ALIGN_CENTER_VERTICAL)

        row.SetSizerAndFit(row_sizer)
        text.Bind(wx.EVT_LEFT_DOWN, lambda event, target=checkbox: target.on_click(event))
        return row, checkbox, text

    # ─── Resolution dropdown helpers ──────────────────────────────────────
    @staticmethod
    def _format_custom_res_label(res_id):
        """Render a 'WxH' id as a 'Custom (W×H)' dropdown label."""
        try:
            w, h = res_id.split('x')
            return _locale.get("output.resolution.custom_label", "Custom ({w}×{h})").format(w=w, h=h)
        except (ValueError, AttributeError):
            return str(res_id)

    def _build_resolution_items(self):
        """Build (choices, ids) for the resolution dropdown: built-in
        resolutions followed by the user's saved custom resolutions."""
        choices, ids = [], []
        for label, res_id in BUILTIN_RESOLUTIONS:
            choices.append(label)
            ids.append(res_id)
        for res_id in (getattr(self.settings, 'custom_resolutions', None) or []):
            choices.append(self._format_custom_res_label(res_id))
            ids.append(res_id)
        return choices, ids

    def _resolution_index(self, res_id, ids=None):
        """Index of res_id in the id list, defaulting to 1080P (or 0)."""
        ids = ids if ids is not None else self.res_ids
        if res_id in ids:
            return ids.index(res_id)
        if '1920x1080' in ids:
            return ids.index('1920x1080')
        return 0

    def rebuild_resolution_items(self, selected_id=None):
        """Rebuild the resolution dropdown after a custom resolution add/delete."""
        self.res_choices, self.res_ids = self._build_resolution_items()
        target = selected_id if selected_id is not None else getattr(self.settings, 'resolution', None)
        self.res_choice.SetItems(self.res_choices, self._resolution_index(target))

    def create_footer_panel(self, parent):
        """Create the persistent footer panel with action buttons."""
        # Create footer container with distinct styling
        footer = wx.Panel(parent)
        footer.SetBackgroundColour(_theme.color("layout.main.leftpanel.bg") or _theme.color("colors.secondary"))

        # Vertical sizer for footer content
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Compute padding from theme (use same padding as main left panel)
        padding = _theme._parse_padding(_theme._resolve("layout.main.leftpanel.padding") or 16)
        vertical_pad = padding.get('top', 12)
        horizontal_pad = padding.get('left', 16)

        # Top divider already added by parent, but we add spacing
        main_sizer.Add((0, vertical_pad))

        # Button row
        btn_row = wx.Panel(footer)
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Options button (small icon button)
        self.adv_btn = CustomButton(btn_row, id="options", size=(36, 36), section='footer')
        self.adv_btn.Bind(wx.EVT_BUTTON, self.main_panel.on_advanced_options)
        btn_sizer.Add(self.adv_btn, 0, wx.RIGHT, 4)

        # About button (help-circle icon)
        self.about_btn = CustomButton(btn_row, id="about", size=(36, 36), section='footer')
        self.about_btn.Bind(wx.EVT_BUTTON, self.on_about)
        btn_sizer.Add(self.about_btn, 0, wx.RIGHT, 8)

        # Cancel/Exit button
        self.can_btn = CustomButton(btn_row, id="exit", size=(110, 36), section='footer')
        self.can_btn.Bind(wx.EVT_BUTTON, self.main_panel.on_cancel)
        btn_sizer.Add(self.can_btn, 0, wx.RIGHT, 8)

        # Render button (takes remaining space)
        self.render_btn = CustomButton(btn_row, id="render", section='footer')
        self.render_btn.Bind(wx.EVT_BUTTON, self.main_panel.on_render)
        btn_sizer.Add(self.render_btn, 1, wx.EXPAND)

        # Apply consistent horizontal padding
        btn_row.SetSizer(btn_sizer)
        main_sizer.Add(btn_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, horizontal_pad)

        main_sizer.Add((0, vertical_pad))
        footer.SetSizer(main_sizer)
        footer.Layout()

        return footer


    def on_about(self, event):
        from .dialogs import AboutSpinRenderDialog
        dlg = AboutSpinRenderDialog(self.main_panel)
        dlg.ShowModal()
        dlg.Destroy()
        self.main_panel.restore_plugin_focus()


class SVGLogoPanel(wx.Panel):
    """Panel that renders the SpinRender SVG logo."""
    def __init__(self, parent, size=(58, 58)):
        # `size` is 96dpi design pixels; scale the panel and render the SVG
        # to fill it (a fixed 1.0 render scale stays small on HiDPI displays).
        super().__init__(parent, size=parent.FromDIP(wx.Size(*size)))
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.svg_image = load_svg(Path(__file__).parent.parent / "resources" / "icons" / "logo.svg")
        self.Bind(wx.EVT_PAINT, self.on_paint)

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        # Clear the buffer first: AutoBufferedPaintDC starts with undefined
        # contents, and the SVG's transparent pixels would show stale memory.
        dc.SetBackground(wx.Brush(effective_background(self)))
        dc.Clear()
        gc = wx.GraphicsContext.Create(dc)
        if not gc:
            return
        width, height = self.GetSize()
        if self.svg_image:
            try:
                self.svg_image.RenderToGC(gc, size=(float(width), float(height)))
            except Exception:
                gc.SetBrush(wx.Brush(_theme.color("colors.primary")))
                gc.DrawRectangle(0, 0, width, height)
