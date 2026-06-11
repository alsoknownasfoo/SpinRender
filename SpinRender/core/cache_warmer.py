"""
3D model tessellation cache warm-up.

KiCad renders 3D component models by tessellating their STEP/IGS solids with
OpenCASCADE and caching the result (``~/Library/Caches/kicad/<ver>/3d/*.3dc``,
or the platform equivalent). That cache is keyed on each model file + mtime and
is shared by KiCad's own 3D Viewer.

When the cache is *cold* (first use, or after the model files change) the first
render has to tessellate every model. For boards with many or heavy STEP models
this can take many minutes, and ``kicad-cli`` gives no progress signal while it
works. SpinRender's preview (OpenGL) and render both depend on this, so a cold
cache makes the plugin appear to hang.

This module runs a single tiny off-screen render *before* the main window opens.
It does no useful imaging — its only job is to make ``kicad-cli`` load and
tessellate the models, which populates the cache. When the cache is already warm
this finishes in a second or two and the user never sees a dialog; when it is
cold we show a progress dialog so the user understands the wait.
"""
import os
import time
import tempfile
import threading
import subprocess
import logging

import wx

from SpinRender.utils.subprocess_utils import NO_WINDOW_FLAGS
from SpinRender.utils.paint_guard import guarded_paint

logger = logging.getLogger("SpinRender")

# Short line shown immediately; the full explanation lives behind "More Info".
_SHORT_MSG = "Preparing 3D models for rendering…"
_DETAIL = (
    "KiCad tessellates each component's 3D model the first time it's used and\n"
    "caches the result — the same 3D model cache KiCad's own 3D Viewer builds.\n\n"
    "Boards with many or highly detailed models can take several minutes to\n"
    "prepare. It only happens again if your 3D model files change; after that,\n"
    "renders and the preview are fast."
)

# How long to wait for the warm-up to finish before showing a dialog. A warm
# cache returns in ~1-2s, so anything under this means "no dialog needed".
_PROBE_SECONDS = 2.0

# Estimated-progress half-life (seconds). kicad-cli emits no real progress, so
# we ease an estimate toward (but never reaching) 100% — at HALFLIFE we're at
# 50%, at 2x ~75%, etc. Completion snaps the bar to 100%. See module docstring
# for why a true percentage is impossible.
_PROGRESS_HALFLIFE = 45.0
_PROGRESS_MAX = 1000

# UI refresh cadence while the dialog is up (ms).
_TICK_MS = 120


def _build_warm_command(board_path):
    """Build a minimal ``kicad-cli pcb render`` that loads the board's models.

    Tiny resolution keeps the raytrace itself trivial, so essentially all the
    time is model tessellation — exactly what we want to cache. We reuse the
    renderer's command/env helpers so we warm precisely the cache the real
    render will hit.
    """
    try:
        from SpinRender.core.renderer import find_command, _prepare_kicad_config_home
    except ImportError:
        from core.renderer import find_command, _prepare_kicad_config_home

    kicad_cli = find_command('kicad-cli')
    if not kicad_cli:
        return None, None, None

    out_fd, out_path = tempfile.mkstemp(prefix='spinrender_warm_', suffix='.png')
    os.close(out_fd)

    cmd = [
        kicad_cli, 'pcb', 'render',
        '--rotate', '0,0,0',
        '-w', '96', '-h', '96',
        '--quality', 'user',
        '-o', out_path,
        board_path,
    ]

    plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = os.environ.copy()
    try:
        env['KICAD_CONFIG_HOME'] = _prepare_kicad_config_home(plugin_dir)
    except Exception as e:  # pragma: no cover - defensive; warming is best-effort
        logger.debug(f"cache_warmer: config home prep failed, using default: {e}")

    return cmd, env, out_path


def _format_elapsed(template, elapsed_seconds):
    """Render the elapsed-time label from a locale template with {mins}/{secs}."""
    mins, secs = divmod(int(elapsed_seconds), 60)
    try:
        return template.format(mins=mins, secs=secs)
    except (KeyError, IndexError, ValueError):
        return f"Elapsed: {mins}m {secs:02d}s"


def _estimate_progress(elapsed):
    """Eased progress estimate in [0, _PROGRESS_MAX). Approaches but never
    reaches the max until the process actually completes."""
    frac = 1.0 - 0.5 ** (elapsed / _PROGRESS_HALFLIFE)
    return int((_PROGRESS_MAX - 10) * frac)


class _ThemedProgressBar(wx.Panel):
    """Determinate progress bar drawn to match the parameter-section sliders
    (``components.slider.default``) — same track height, colors and corner
    radius — but without the draggable grabber/nub. This keeps the warm-up
    dialog visually consistent with the main window's bars."""

    _TOKEN = "components.slider.default"
    _RADIUS = 2

    def __init__(self, parent, theme, maximum, height=18):
        super().__init__(parent, size=(-1, height))
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self._theme = theme
        self._max = max(1, int(maximum))
        self._value = 0
        self.Bind(wx.EVT_PAINT, self._on_paint)

    def SetValue(self, value):
        self._value = max(0, min(self._max, int(value)))
        self.Refresh()
        self.Update()

    @guarded_paint
    def _on_paint(self, _evt):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc:
            return
        w, h = self.GetClientSize()
        if w <= 0 or h <= 0:
            return

        token = self._TOKEN if self._theme.has_token(self._TOKEN) else "components.slider.default"
        track_h = self._theme._resolve(f"{token}.track.frame.height") or 4
        track_y = (h - track_h) / 2
        track_color = self._theme.color(f"{token}.track.color")
        fill_color = self._theme.color(f"{token}.nub.color")

        gc.SetPen(wx.TRANSPARENT_PEN)
        # Paint the dialog background so the rounded track blends cleanly.
        gc.SetBrush(wx.Brush(self._theme.color("colors.gray-dark")))
        gc.DrawRectangle(0, 0, w, h)
        # Track (full width) then fill (value width) — same as CustomSlider,
        # just without the nub.
        gc.SetBrush(wx.Brush(track_color))
        gc.DrawRoundedRectangle(0, track_y, w, track_h, self._RADIUS)
        fill_w = w * (self._value / self._max)
        if fill_w > 0:
            gc.SetBrush(wx.Brush(fill_color))
            gc.DrawRoundedRectangle(0, track_y, fill_w, track_h, self._RADIUS)


def _build_warmup_dialog(parent, start_time):
    """Construct the cold-cache warm-up progress dialog.

    Built on the shared ``BaseStyledDialog`` so it carries the same themed
    chrome (dark frame, drop shadow, header bar, draggable, ESC-to-cancel) and
    themed text/buttons as every other SpinRender dialog. Short message up top,
    the full explanation behind a "More Info" disclosure (the same +/-
    SectionToggle the side-panel sections use), a themed progress bar, an
    elapsed-time label, and a Cancel button. A wx.Timer drives the bar/elapsed;
    ShowModal runs the event loop so Cancel and the expander stay responsive
    while the warm render runs in a background thread. ``finish_ok()`` (via
    wx.CallAfter) ends the modal when warming completes.

    The class is defined inside this factory so importing ``cache_warmer`` never
    hard-depends on the UI layer (the dialog is only built in a live wx app).
    """
    try:
        from SpinRender.ui.dialogs import BaseStyledDialog
        from SpinRender.ui.helpers import create_text, update_text
        from SpinRender.ui.custom_controls import CustomButton, SectionToggle
        from SpinRender.core.theme import Theme
        from SpinRender.core.locale import Locale
    except ImportError:
        from ui.dialogs import BaseStyledDialog
        from ui.helpers import create_text, update_text
        from ui.custom_controls import CustomButton, SectionToggle
        from core.theme import Theme
        from core.locale import Locale

    theme = Theme.current()
    loc = Locale.current()
    title = loc.get("dialog.warmup.title", "Starting SpinRender")
    short_msg = loc.get("dialog.warmup.message", _SHORT_MSG)
    detail = loc.get("dialog.warmup.detail", _DETAIL)
    more_info = loc.get("dialog.warmup.more_info", "More Info")
    elapsed_tmpl = loc.get("dialog.warmup.elapsed", "Elapsed: {mins}m {secs:02d}s")

    class _WarmupDialog(BaseStyledDialog):
        def __init__(self):
            super().__init__(parent, title, (420, 220))
            self._start = start_time
            self.cancelled = False
            self._build()
            self.autosize_dialog_height()
            self.center_over_parent()

            self._timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self._on_tick, self._timer)
            self.Bind(wx.EVT_CLOSE, self._on_cancel)
            self._timer.Start(_TICK_MS)

        def _build(self):
            pad = 20
            main = wx.BoxSizer(wx.VERTICAL)
            main.Add(self.create_header(title, show_close=False), 0, wx.EXPAND)

            self._header_line = wx.Panel(self.main_container, size=(-1, 1))
            self._header_line.SetBackgroundColour(theme.color("dividers.default.color"))
            main.Add(self._header_line, 0, wx.EXPAND)

            content = wx.Panel(self.main_container)
            content.SetBackgroundColour(theme.color("colors.gray-dark"))
            cs = wx.BoxSizer(wx.VERTICAL)

            head = create_text(content, short_msg, "dialog_description")
            head_font = head.GetFont()
            head_font.MakeBold()
            head.SetFont(head_font)
            cs.Add(head, 0, wx.LEFT | wx.RIGHT | wx.TOP, pad)

            cs.Add(self._build_more_info(content, create_text, SectionToggle),
                   0, wx.LEFT | wx.RIGHT | wx.TOP, pad)

            self._bar = _ThemedProgressBar(content, theme, _PROGRESS_MAX)
            cs.Add(self._bar, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, pad)

            self._elapsed = create_text(content, _format_elapsed(elapsed_tmpl, 0.0), "dialog_description")
            cs.Add(self._elapsed, 0, wx.LEFT | wx.RIGHT | wx.TOP, pad)
            cs.Add((0, pad))
            content.SetSizer(cs)
            main.Add(content, 1, wx.EXPAND)

            main.Add(self._build_footer(CustomButton), 0, wx.EXPAND)
            self.main_container.SetSizer(main)

        def _build_footer(self, CustomButton):
            footer = wx.Panel(self.main_container)
            outer = wx.BoxSizer(wx.VERTICAL)
            self._footer_divider = wx.Panel(footer, size=(-1, 1))
            self._footer_divider.SetBackgroundColour(theme.color("borders.default.color"))
            outer.Add(self._footer_divider, 0, wx.EXPAND)

            row = wx.BoxSizer(wx.HORIZONTAL)
            # label=None → CustomButton derives the localized "Cancel" label
            # from the component.button.cancel locale entry.
            cancel_btn = CustomButton(footer, id="cancel", size=(-1, 36))
            cancel_btn.Bind(wx.EVT_BUTTON, self._on_cancel)
            row.Add((16, 0))
            row.AddStretchSpacer()
            row.Add(cancel_btn, 0)
            row.Add((16, 0))

            outer.Add((0, 16))
            outer.Add(row, 0, wx.EXPAND)
            outer.Add((0, 16))
            footer.SetSizer(outer)
            return footer

        def _build_more_info(self, parent_panel, create_text, SectionToggle):
            """'More Info' disclosure: clickable label + the same +/-
            SectionToggle the side-panel sections use, showing/hiding the
            detail text. Normal themed body type — not the section-header font."""
            box = wx.BoxSizer(wx.VERTICAL)
            header = wx.BoxSizer(wx.HORIZONTAL)
            self._more_label = create_text(parent_panel, more_info, "dialog_description")
            self._more_toggle = SectionToggle(
                parent_panel, size=12, y_nudge=1, collapsed=True,
                on_toggle=self._on_more_info_toggle,
            )
            header.Add(self._more_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
            header.Add(self._more_toggle, 0, wx.ALIGN_CENTER_VERTICAL)
            box.Add(header, 0)

            self._detail = create_text(parent_panel, detail, "dialog_description")
            self._detail.Hide()
            box.Add(self._detail, 0, wx.TOP, 8)

            self._more_label.SetCursor(wx.Cursor(wx.CURSOR_HAND))
            self._more_label.Bind(wx.EVT_LEFT_DOWN, lambda _e: self._toggle_more_info())
            return box

        def _toggle_more_info(self):
            collapsed = not self._more_toggle.collapsed
            self._more_toggle.set_collapsed(collapsed)
            self._apply_more_info(collapsed)

        def _on_more_info_toggle(self, collapsed):
            self._apply_more_info(collapsed)

        def _apply_more_info(self, collapsed):
            self._detail.Show(not collapsed)
            self.main_container.Layout()
            self.autosize_dialog_height()

        def _on_tick(self, _evt):
            elapsed = time.time() - self._start
            self._bar.SetValue(_estimate_progress(elapsed))
            # update_text (not SetLabel) re-applies the style's uppercase
            # transform so the elapsed label stays consistent with the rest of
            # the dialog body across ticks.
            update_text(self._elapsed, _format_elapsed(elapsed_tmpl, elapsed))

        # ESC (routed via BaseStyledDialog.on_char_hook) and the header close
        # both funnel through on_cancel so the timer stops and cancelled is set.
        def on_char_hook(self, event):
            if event.GetKeyCode() == wx.WXK_ESCAPE:
                self._on_cancel(event)
            else:
                event.Skip()

        def on_cancel(self, event):
            self._on_cancel(event)

        def _on_cancel(self, _evt):
            self.cancelled = True
            self._stop_timer()
            self.EndModal(wx.ID_CANCEL)

        def _stop_timer(self):
            if getattr(self, "_timer", None) and self._timer.IsRunning():
                self._timer.Stop()

        def finish_ok(self):
            """End the modal successfully once warming completes (main thread)."""
            if self.cancelled:
                return
            self._stop_timer()
            self._bar.SetValue(_PROGRESS_MAX)
            if self.IsModal():
                self.EndModal(wx.ID_OK)

    return _WarmupDialog()


def _show_required_warning(parent):
    """Explain that warming is required, then return False to abort the launch."""
    try:
        from SpinRender.ui.dialogs import show_message
        from SpinRender.core.locale import Locale
    except ImportError:
        from ui.dialogs import show_message
        from core.locale import Locale
    loc = Locale.current()
    show_message(
        parent,
        loc.get("dialog.warmup.required_title", "Starting SpinRender"),
        loc.get(
            "dialog.warmup.required_message",
            "SpinRender can't start without preparing the 3D model cache.\n\n"
            "This is the same 3D model data KiCad's own 3D Viewer builds, and it "
            "only needs to be done once — until your 3D models change. Please "
            "relaunch SpinRender when you're ready to let it finish.",
        ),
    )
    return False


def ensure_model_cache_warm(parent, board_path):
    """Warm KiCad's 3D model cache before the main window opens.

    Returns True to proceed with launching the plugin, False to abort (the user
    cancelled the required warm-up). Warming is best-effort: if kicad-cli is
    missing or the warm render errors, we log and proceed rather than block.
    """
    cmd, env, out_path = _build_warm_command(board_path)
    if cmd is None:
        logger.warning("cache_warmer: kicad-cli not found; skipping warm-up")
        return True

    logger.debug(f"cache_warmer: warming via {' '.join(cmd)}")

    proc_holder = {}
    result = {'rc': None}
    done = threading.Event()

    def worker():
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL, text=True, encoding='utf-8',
                errors='replace', env=env, creationflags=NO_WINDOW_FLAGS,
            )
            proc_holder['proc'] = proc
            proc.communicate()
            result['rc'] = proc.returncode
        except Exception as e:
            logger.error(f"cache_warmer: warm render failed: {e}", exc_info=True)
            result['rc'] = -1
        finally:
            done.set()

    start = time.time()
    threading.Thread(target=worker, daemon=True).start()

    # Probe: a warm cache finishes fast — return without ever showing a dialog.
    if done.wait(_PROBE_SECONDS):
        _cleanup_temp(out_path)
        logger.debug(f"cache_warmer: cache warm (finished in {time.time()-start:.1f}s)")
        return True

    # Cold cache: show the progress dialog until warming finishes or is
    # cancelled. ShowModal runs the event loop; a waiter thread ends the modal
    # via finish_ok() when the warm render completes.
    dlg = _build_warmup_dialog(parent, start)

    def _waiter():
        done.wait()
        wx.CallAfter(dlg.finish_ok)

    threading.Thread(target=_waiter, daemon=True).start()
    ret = dlg.ShowModal()
    cancelled = (ret == wx.ID_CANCEL) or dlg.cancelled
    dlg.Destroy()

    if cancelled:
        logger.info("cache_warmer: user cancelled warm-up")
        _terminate(proc_holder)
        _cleanup_temp(out_path)
        return _show_required_warning(parent)

    _cleanup_temp(out_path)
    if result['rc'] not in (0, None):
        # Warming didn't succeed (e.g. board load error) but that's the real
        # render's problem to surface — don't block the user here.
        logger.warning(f"cache_warmer: warm render exited rc={result['rc']}; proceeding anyway")
    else:
        logger.info(f"cache_warmer: cache warmed in {time.time()-start:.1f}s")
    return True


def _terminate(proc_holder):
    """Stop the warm-up subprocess so a cancelled cold render doesn't keep
    tessellating in the background."""
    proc = proc_holder.get('proc')
    if proc is None:
        return
    try:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    except Exception as e:
        logger.debug(f"cache_warmer: terminate failed: {e}")


def _cleanup_temp(path):
    if path:
        try:
            os.remove(path)
        except OSError:
            pass
