"""
SpinRender KiCad Action Plugin Entry Point
"""
import pcbnew
import wx
import os
import sys
import site
import logging
from pathlib import Path


# Add user site-packages to path
# This is critical for KiCad bundled Python to find packages installed via 'pip install --user'
user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.append(user_site)

# Add plugin parent directory to path for package-style imports
# This ensures that 'from SpinRender.xxx' works correctly
plugin_dir = os.path.dirname(os.path.abspath(__file__))
plugin_real_dir = os.path.dirname(os.path.realpath(__file__))
plugin_parent = os.path.dirname(plugin_dir)

for p in [plugin_parent, plugin_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Initialize logging system
try:
    from SpinRender.utils.logger import SpinLogger
    SpinLogger.setup(level='debug')
except ImportError:
    from utils.logger import SpinLogger
    SpinLogger.setup(level='debug')

logger = logging.getLogger("SpinRender")
logger.info(f"Loading SpinRender plugin from {plugin_dir}")
logger.debug(f"Python executable: {sys.executable}")
logger.debug(f"Python version: {sys.version}")
logger.debug(f"Platform: {sys.platform}")

# Import dependency checker
logger.debug("Importing dependency checker...")
try:
    from SpinRender.ui.dependencies import DependencyChecker
except ImportError:
    from ui.dependencies import DependencyChecker
logger.debug("Dependency checker imported successfully")


def _get_board_file_path(board) -> str:
    """Resolve the current KiCad board filename across API wrapper variants."""
    getter = getattr(board, "GetFileName", None)
    if callable(getter):
        return getter()

    for caster_name in ("Cast_to_BOARD", "BOARD"):
        caster = getattr(pcbnew, caster_name, None)
        if not callable(caster):
            continue

        try:
            typed_board = caster(board)
        except Exception:
            continue

        getter = getattr(typed_board, "GetFileName", None)
        if callable(getter):
            return getter()

    raise AttributeError(f"{type(board).__name__!s} object has no attribute 'GetFileName'")

# NOTE: Do NOT import ui.main_panel here - it pulls in core.preview which requires
# trimesh/OpenGL. We import it inside Run() AFTER checking dependencies.


class SpinRenderPlugin(pcbnew.ActionPlugin):
    """
    KiCad Action Plugin for SpinRender
    """

    def defaults(self):
        """
        Plugin metadata for KiCad
        """
        self.name = "SpinRender"
        self.category = "Render"
        self.description = "Generate animated PCB renders with camera loops and lighting presets"
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(plugin_dir, "resources", "icon.png")
        self.dark_icon_file_name = os.path.join(plugin_dir, "resources", "icon.png")
        
        logger.debug(f"SpinRender defaults() called: name={self.name}")

    def Run(self):
        """
        Called when plugin is executed from KiCad
        """
        logger.info("SpinRender Run() called")
        try:
            # 1. CHECK DEPENDENCIES (INCLUDING wxPython) FIRST
            logger.debug("Starting dependency check...")
            checker = DependencyChecker()
            if not checker.check_and_prompt():
                # User chose to exit or installation failed/cancelled
                logger.info("Dependency check/prompt returned False - exiting")
                return

            # Now that dependencies (specifically wxPython) are guaranteed:
            import wx

            # 2. Check if window already exists - bring to front instead of creating new one
            if SpinRenderFrame.active_instance is not None:
                logger.debug("Found existing SpinRenderFrame instance - bringing to front")
                frame = SpinRenderFrame.active_instance
                if frame and not frame.IsBeingDeleted():
                    frame.Raise()
                    frame.SetFocus()
                    logger.debug("Existing frame raised and focused")
                    return
                else:
                    # Frame was closed, clear the reference
                    logger.debug("Frame was marked as deleted, clearing active_instance")
                    SpinRenderFrame.active_instance = None

            # Get current board
            logger.debug("Getting current board from KiCad...")
            board = pcbnew.GetBoard()
            if not board:
                logger.warning("No board is currently open - aborting")
                wx.MessageBox(
                    "No board is currently open. Please open a PCB file first.",
                    "SpinRender - No Board",
                    wx.OK | wx.ICON_ERROR
                )
                return
            board_path = _get_board_file_path(board)
            logger.debug(f"Board loaded: {board_path if board_path else 'Unsaved'}")

            # Check dependencies BEFORE importing any heavy modules
            logger.debug("Starting dependency check...")
            checker = DependencyChecker()
            dep_status = checker.check_all()
            logger.debug(f"Dependency check results: {dep_status}")
            if not checker.missing_deps:
                logger.info("All dependencies satisfied")
            else:
                logger.warning(f"Missing dependencies: {checker.missing_deps}")

            if not checker.check_and_prompt():
                # User chose to exit or installation failed
                logger.info("Dependency check/prompt returned False - exiting")
                return

            # Import SpinRenderPanel only after dependencies are verified
            logger.debug("Dependencies OK, importing SpinRenderPanel...")
            try:
                from SpinRender.ui.main_panel import SpinRenderPanel
            except ImportError:
                from ui.main_panel import SpinRenderPanel
            logger.debug("SpinRenderPanel imported successfully")

            # Get board file path
            board_path = _get_board_file_path(board)
            logger.debug(f"Board path: {board_path}")
            # The board must have been saved at least once: SpinRender needs a
            # real project directory so KiCad can resolve ${KIPRJMOD} and
            # relative 3D-model paths for the working copy. Unsaved *edits* are
            # fine — we serialize the live in-memory board at launch/render
            # (see BoardWorkspace.capture_live_board), so the user does not need
            # to save the latest changes first.
            if not board_path or not os.path.exists(board_path):
                logger.warning("Board has never been saved - aborting launch")
                dlg = wx.MessageDialog(
                    None,
                    "Document needs to be saved before launching SpinRender",
                    "SpinRender",
                    wx.OK | wx.ICON_WARNING
                )
                dlg.SetOKLabel("Close")
                dlg.ShowModal()
                dlg.Destroy()
                return

            # Launch SpinRender panel
            logger.debug("Looking for KiCad parent window...")
            parent = wx.FindWindowByName("PcbFrame")
            if not parent:
                logger.debug("PcbFrame not found, using top window")
                parent = wx.GetApp().GetTopWindow()
            logger.debug(f"Parent window: {parent}")

            # Pre-flight: warm KiCad's 3D model tessellation cache before opening
            # the window. A cold cache makes the preview and first render block
            # for minutes; this shows a progress dialog (only when actually
            # needed) and lets the user cancel. Cancelling aborts the launch.
            logger.debug("Ensuring 3D model cache is warm...")
            try:
                from SpinRender.core.cache_warmer import ensure_model_cache_warm
            except ImportError:
                from core.cache_warmer import ensure_model_cache_warm
            if not ensure_model_cache_warm(parent, board_path):
                logger.info("Cache warm-up cancelled by user - aborting launch")
                return

            logger.debug("Creating SpinRenderFrame...")
            frame = SpinRenderFrame(parent, board_path)
            logger.debug("Showing frame...")
            frame.Show()
            logger.info("SpinRender frame shown successfully")

        except Exception as e:
            logger.error(f"Failed to launch SpinRender: {e}", exc_info=True)
            wx.MessageBox(
                f"Failed to launch SpinRender:\n{str(e)}",
                "SpinRender - Error",
                wx.OK | wx.ICON_ERROR
            )


class SpinRenderFrame(wx.Frame):
    """
    Main SpinRender window frame
    """
    active_instance = None

    def __init__(self, parent, board_path):
        logger.debug(f"SpinRenderFrame.__init__ starting (board_path={board_path})")
        super().__init__(
            parent,
            title="SpinRender",
            style=wx.FRAME_NO_TASKBAR | wx.NO_BORDER
        )
        logger.debug("Frame created, setting up panel...")

        self.board_path = board_path

        # Create main panel - import here after dependencies are verified
        logger.debug("Importing SpinRenderPanel...")
        try:
            from SpinRender.ui.main_panel import SpinRenderPanel
        except ImportError:
            from ui.main_panel import SpinRenderPanel
        logger.debug("Creating SpinRenderPanel...")
        self.panel = SpinRenderPanel(self, board_path)
        logger.debug("Panel created")

        # Create sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        logger.debug("Sizer set")

        # FIT LOGIC: We call Fit() and Centre() after a short delay
        # to ensure the panel has finished its internal Layout()
        logger.debug("Scheduling _finalize_init via CallAfter...")
        wx.CallAfter(self._finalize_init)

        # Set as active instance
        SpinRenderFrame.active_instance = self
        logger.debug("Set as active_instance")

        # Theme Hot-Reload Watcher
        self._init_theme_watcher()

        # Bind close event
        self.Bind(wx.EVT_CLOSE, self.on_close)

        # Refresh the preview when the window regains focus so it reflects edits
        # made in the PCB editor while SpinRender stayed open (hash-gated, so an
        # unchanged board is a no-op).
        self.Bind(wx.EVT_ACTIVATE, self.on_activate)
        logger.debug("Close event bound, __init__ complete")

    def on_activate(self, event):
        """Re-sync the preview to the live board when the window is activated."""
        try:
            if event.GetActive() and self.panel and hasattr(self.panel, 'refresh_preview_if_changed'):
                self.panel.refresh_preview_if_changed()
        except Exception as e:
            logger.error(f"on_activate refresh failed: {e}", exc_info=True)
        event.Skip()

    def _init_theme_watcher(self):
        """Initialize a timer to watch for theme file changes (Hot Reload)."""
        try:
            from SpinRender.core.theme import Theme as _Theme
        except ImportError:
            from core.theme import Theme as _Theme
        active_name = _Theme._loaded_name or "dark"
        self.theme_path = Path(plugin_real_dir) / "resources" / "themes" / f"{active_name}.yaml"
        self.last_theme_mtime = self.theme_path.stat().st_mtime if self.theme_path.exists() else 0

        self.theme_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_theme_watch_timer, self.theme_timer)
        self.theme_timer.Start(1000) # Check every second
        logger.debug(f"Theme watcher initialized for {self.theme_path.name}")

    def on_theme_watch_timer(self, event):
        """Check if theme file has been modified and reload if needed."""
        try:
            try:
                from SpinRender.core.theme import Theme
            except ImportError:
                from core.theme import Theme

            # Update watch path if the active theme has changed (e.g. user switched)
            active_name = Theme._loaded_name or "dark"
            expected_path = Path(plugin_real_dir) / "resources" / "themes" / f"{active_name}.yaml"
            if expected_path != self.theme_path:
                self.theme_path = expected_path
                self.last_theme_mtime = self.theme_path.stat().st_mtime if self.theme_path.exists() else 0

            if not self.theme_path.exists():
                return

            mtime = self.theme_path.stat().st_mtime
            if mtime > self.last_theme_mtime:
                self.last_theme_mtime = mtime
                logger.info(f"Theme file {self.theme_path.name} changed. Hot-reloading...")
                Theme.reload()

                if hasattr(self.panel, 'reapply_theme'):
                    self.panel.reapply_theme()
                else:
                    self.panel.Refresh()
                    self._refresh_recursive(self.panel)

                logger.info("Theme hot-reload complete.")
        except Exception as e:
            logger.error(f"Theme watcher error: {e}")

    def _refresh_recursive(self, window):
        """Recursively refresh all child windows."""
        window.Refresh()
        for child in window.GetChildren():
            self._refresh_recursive(child)

    def _finalize_init(self):
        """Finalize window size and position"""
        logger.debug("_finalize_init called")
        if self:
            logger.debug("Fitting window...")
            self.Fit()
            # Enforce minimum width: controls (400) + divider (1) + preview (700) + padding
            min_width = 1120  # 400 + 1 + 700 + ~19px for borders/sizer padding
            current_size = self.GetSize()
            if current_size.GetWidth() < min_width:
                logger.debug(f"Enforcing minimum width: {min_width}px (current: {current_size.GetWidth()})")
                self.SetSize((min_width, current_size.GetHeight()))
            logger.debug("Centering window...")
            self.Centre()
            # Keep the window within the display's work area and fully on-screen.
            self._fit_to_display()
            logger.debug("_finalize_init complete")

    def _fit_to_display(self):
        """Ensure the window fits within, and is fully visible on, its display.

        If the window is larger than the available work area (screen minus
        taskbar/dock/menubar), shrink it to fit. Then move it so no part is
        off-screen. Falls back to the primary display if the window currently
        renders entirely off every display.
        """
        if not self:
            return
        try:
            idx = wx.Display.GetFromWindow(self)
            if idx == wx.NOT_FOUND:
                idx = 0
            area = wx.Display(idx).GetClientArea()

            size = self.GetSize()
            w, h = size.GetWidth(), size.GetHeight()
            fit_w, fit_h = min(w, area.GetWidth()), min(h, area.GetHeight())

            # 1. Resize down to the available space if the window is too big.
            if fit_w != w or fit_h != h:
                # SetSizeHints() pinned a min size; relax it only as needed so
                # the frame can actually shrink to fit the display.
                mw, mh = self.GetMinWidth(), self.GetMinHeight()
                self.SetMinSize((
                    min(mw, fit_w) if mw > 0 else fit_w,
                    min(mh, fit_h) if mh > 0 else fit_h,
                ))
                self.SetSize((fit_w, fit_h))
                w, h = fit_w, fit_h

            # 2. Move so the whole window sits inside the work area.
            pos = self.GetPosition()
            x = max(area.GetX(), min(pos.x, area.GetX() + area.GetWidth() - w))
            y = max(area.GetY(), min(pos.y, area.GetY() + area.GetHeight() - h))
            if x != pos.x or y != pos.y:
                self.SetPosition((x, y))
        except Exception as e:
            logger.error(f"_fit_to_display failed: {e}", exc_info=True)

    def on_close(self, event):
        """
        Handle window close
        """
        logger.debug("SpinRenderFrame.on_close() called")
        # Clean up resources
        if hasattr(self.panel, 'cleanup'):
            logger.debug("Calling panel cleanup()...")
            self.panel.cleanup()
        else:
            logger.debug("Panel has no cleanup() method")

        # Clear active instance
        SpinRenderFrame.active_instance = None
        logger.debug("Cleared active_instance reference")

        self.Destroy()
        logger.debug("Frame destroyed")


# Register plugin with KiCad
try:
    logger.debug("Attempting to register SpinRender plugin")
    SpinRenderPlugin().register()
    logger.info("SpinRender plugin registered")
except Exception as e:
    logger.error(f"SpinRender registration failed: {e}", exc_info=True)
