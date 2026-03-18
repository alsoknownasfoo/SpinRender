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
# This ensures that 'from SpinRender.xxx' works correctly and consistently
plugin_dir = os.path.dirname(os.path.abspath(__file__))
plugin_parent = os.path.dirname(plugin_dir)

if plugin_parent not in sys.path:
    sys.path.insert(0, plugin_parent)

# Remove the plugin_dir itself if it's in sys.path to avoid duplicate modules
# (e.g. importing 'core.theme' vs 'SpinRender.core.theme')
if plugin_dir in sys.path:
    sys.path.remove(plugin_dir)

# Initialize logging system
from SpinRender.utils.logger import SpinLogger
SpinLogger.setup(level='verbose')  # Enable DEBUG level logging for troubleshooting
logger = logging.getLogger("SpinRender")
logger.info(f"Loading SpinRender plugin from {plugin_dir}")
logger.debug(f"Python executable: {sys.executable}")
logger.debug(f"Python version: {sys.version}")
logger.debug(f"Platform: {sys.platform}")

# Import dependency checker early (doesn't require heavy dependencies)
logger.debug("Importing dependency checker...")
from SpinRender.ui.dependencies import DependencyChecker
logger.debug("Dependency checker imported successfully")

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
            # Check if window already exists - bring to front instead of creating new one
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
            board_path = board.GetFileName()
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
            from SpinRender.ui.main_panel import SpinRenderPanel
            logger.debug("SpinRenderPanel imported successfully")

            # Get board file path
            board_path = board.GetFileName()
            logger.debug(f"Board path: {board_path}")
            if not board_path or not os.path.exists(board_path):
                logger.warning("Board file not saved or doesn't exist - aborting")
                wx.MessageBox(
                    "Board file not saved. Please save your board file first.",
                    "SpinRender - Unsaved Board",
                    wx.OK | wx.ICON_ERROR
                )
                return

            # Launch SpinRender panel
            logger.debug("Looking for KiCad parent window...")
            parent = wx.FindWindowByName("PcbFrame")
            if not parent:
                logger.debug("PcbFrame not found, using top window")
                parent = wx.GetApp().GetTopWindow()
            logger.debug(f"Parent window: {parent}")

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
        from SpinRender.ui.main_panel import SpinRenderPanel
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
        logger.debug("Close event bound, __init__ complete")

    def _init_theme_watcher(self):
        """Initialize a timer to watch for theme file changes (Hot Reload)."""
        self.theme_path = Path(__file__).parent / "resources" / "themes" / "dark.yaml"
        self.last_theme_mtime = self.theme_path.stat().st_mtime if self.theme_path.exists() else 0
        
        self.theme_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_theme_watch_timer, self.theme_timer)
        self.theme_timer.Start(1000) # Check every second
        logger.debug(f"Theme watcher initialized for {self.theme_path.name}")

    def on_theme_watch_timer(self, event):
        """Check if theme file has been modified and reload if needed."""
        if not self.theme_path.exists():
            return
            
        mtime = self.theme_path.stat().st_mtime
        if mtime > self.last_theme_mtime:
            self.last_theme_mtime = mtime
            logger.info(f"Theme file {self.theme_path.name} changed. Hot-reloading...")
            try:
                from SpinRender.core.theme import Theme
                Theme.reload()
                
                # Use the new orchestrated re-application method
                if hasattr(self.panel, 'reapply_theme'):
                    self.panel.reapply_theme()
                else:
                    self.panel.Refresh()
                    self._refresh_recursive(self.panel)
                    
                logger.info("Theme hot-reload complete.")
            except Exception as e:
                logger.error(f"Theme hot-reload failed: {e}")

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
            logger.debug("_finalize_init complete")

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
