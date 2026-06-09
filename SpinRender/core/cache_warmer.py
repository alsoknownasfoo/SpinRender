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


def _estimate_progress(elapsed):
    """Eased progress estimate in [0, _PROGRESS_MAX). Approaches but never
    reaches the max until the process actually completes."""
    frac = 1.0 - 0.5 ** (elapsed / _PROGRESS_HALFLIFE)
    return int((_PROGRESS_MAX - 10) * frac)


class _WarmupDialog(wx.Dialog):
    """Cold-cache warm-up progress dialog.

    Short message up top, the full explanation tucked behind a collapsible
    "More Info" expander, an estimated-progress gauge, an elapsed-time label,
    and Cancel. A wx.Timer drives the gauge/elapsed; ShowModal runs the event
    loop so Cancel and the expander stay responsive while the warm render runs
    in a background thread. finish_ok() (via wx.CallAfter) ends the modal when
    warming completes.
    """

    def __init__(self, parent, start_time):
        super().__init__(parent, title="SpinRender",
                         style=wx.DEFAULT_DIALOG_STYLE & ~wx.RESIZE_BORDER)
        self._start = start_time
        self.cancelled = False

        root = wx.BoxSizer(wx.VERTICAL)
        pad = wx.LEFT | wx.RIGHT | wx.TOP

        head = wx.StaticText(self, label=_SHORT_MSG)
        head_font = head.GetFont()
        head_font.MakeBold()
        head.SetFont(head_font)
        root.Add(head, 0, pad, 16)

        # "More Info" disclosure using the same control as the side-panel
        # section headers: a clickable label + SectionToggle (+/- box) that
        # shows/hides the detail text below.
        root.Add(self._build_more_info(), 0, pad, 12)

        self._gauge = wx.Gauge(self, range=_PROGRESS_MAX, size=(380, -1))
        root.Add(self._gauge, 0, wx.EXPAND | pad, 16)

        self._elapsed = wx.StaticText(self, label="Elapsed: 0m 00s")
        root.Add(self._elapsed, 0, pad, 8)

        btns = wx.BoxSizer(wx.HORIZONTAL)
        btns.AddStretchSpacer()
        btns.Add(wx.Button(self, wx.ID_CANCEL, "Cancel"), 0)
        root.Add(btns, 0, wx.EXPAND | wx.ALL, 16)

        self.SetSizer(root)
        self.Fit()
        self.Centre()

        self.Bind(wx.EVT_BUTTON, self._on_cancel, id=wx.ID_CANCEL)
        self.Bind(wx.EVT_CLOSE, self._on_cancel)

        self._timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_tick, self._timer)
        self._timer.Start(_TICK_MS)

    def _build_more_info(self):
        """Build the 'More Info' disclosure with the same +/- SectionToggle the
        side-panel sections use; clicking the label or the box toggles the body."""
        try:
            from SpinRender.ui.custom_controls import SectionToggle
        except ImportError:
            from ui.custom_controls import SectionToggle

        box = wx.BoxSizer(wx.VERTICAL)

        header = wx.BoxSizer(wx.HORIZONTAL)
        # Normal body font — deliberately NOT the side-panel section-header
        # style (we only borrow the +/- SectionToggle control, not its header
        # typography).
        self._more_label = wx.StaticText(self, label="More Info")
        self._more_label.SetFont(wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT))
        self._more_toggle = SectionToggle(
            self, size=12, y_nudge=1, collapsed=True,
            on_toggle=self._on_more_info_toggle,
        )
        header.Add(self._more_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        header.Add(self._more_toggle, 0, wx.ALIGN_CENTER_VERTICAL)
        box.Add(header, 0)

        self._detail = wx.StaticText(self, label=_DETAIL)
        self._detail.Hide()
        box.Add(self._detail, 0, wx.TOP, 8)

        # Clicking the label toggles too (mirrors the section-header hit area).
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
        self.Layout()
        self.Fit()

    def _on_tick(self, _evt):
        elapsed = time.time() - self._start
        self._gauge.SetValue(_estimate_progress(elapsed))
        mins, secs = divmod(int(elapsed), 60)
        self._elapsed.SetLabel(f"Elapsed: {mins}m {secs:02d}s")

    def _on_cancel(self, _evt):
        self.cancelled = True
        self._stop_timer()
        self.EndModal(wx.ID_CANCEL)

    def _stop_timer(self):
        if self._timer.IsRunning():
            self._timer.Stop()

    def finish_ok(self):
        """End the modal successfully once warming completes (main thread)."""
        if self.cancelled:
            return
        self._stop_timer()
        self._gauge.SetValue(_PROGRESS_MAX)
        if self.IsModal():
            self.EndModal(wx.ID_OK)


def _show_required_warning(parent):
    """Explain that warming is required, then return False to abort the launch."""
    import wx
    dlg = wx.MessageDialog(
        parent,
        "SpinRender can't start without preparing the 3D model cache.\n\n"
        "This is the same 3D model data KiCad's own 3D Viewer builds, and it\n"
        "only needs to be done once — until your 3D models change. Please\n"
        "relaunch SpinRender when you're ready to let it finish.",
        "SpinRender",
        wx.OK | wx.ICON_WARNING,
    )
    dlg.SetOKLabel("Close")
    dlg.ShowModal()
    dlg.Destroy()
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
                errors='replace', env=env,
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
    dlg = _WarmupDialog(parent, start)

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
