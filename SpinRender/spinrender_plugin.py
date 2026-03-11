"""
SpinRender KiCad Action Plugin Entry Point
"""
import pcbnew
import wx
import os
import sys
import site
# REMOVE THIS LINE IN PRODUCTION - This is for development to prevent .pyc files from being generated in the plugin directory
sys.dont_write_bytecode = True 

# Add user site-packages to path
# This is critical for KiCad bundled Python to find packages installed via 'pip install --user'
user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.append(user_site)

# Add plugin directory to path for imports
plugin_dir = os.path.dirname(os.path.abspath(__file__))
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)

from utils.dependencies import DependencyChecker
from ui.main_panel import SpinRenderPanel


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

    def Run(self):
        """
        Called when plugin is executed from KiCad
        """
        try:
            # Check if window already exists - bring to front instead of creating new one
            if SpinRenderFrame.active_instance is not None:
                frame = SpinRenderFrame.active_instance
                if frame and not frame.IsBeingDeleted():
                    frame.Raise()
                    frame.SetFocus()
                    return
                else:
                    # Frame was closed, clear the reference
                    SpinRenderFrame.active_instance = None

            # Get current board
            board = pcbnew.GetBoard()
            if not board:
                wx.MessageBox(
                    "No board is currently open. Please open a PCB file first.",
                    "SpinRender - No Board",
                    wx.OK | wx.ICON_ERROR
                )
                return

            # Check dependencies on first run
            checker = DependencyChecker()
            if not checker.check_and_prompt():
                # User chose to exit or installation failed
                return

            # Get board file path
            board_path = board.GetFileName()
            if not board_path or not os.path.exists(board_path):
                wx.MessageBox(
                    "Board file not saved. Please save your board file first.",
                    "SpinRender - Unsaved Board",
                    wx.OK | wx.ICON_ERROR
                )
                return

            # Launch SpinRender panel
            parent = wx.FindWindowByName("PcbFrame")
            if not parent:
                parent = wx.GetApp().GetTopWindow()

            frame = SpinRenderFrame(parent, board_path)
            frame.Show()

        except Exception as e:
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
        super().__init__(
            parent,
            title="SpinRender",
            style=wx.FRAME_NO_TASKBAR | wx.NO_BORDER
        )

        self.board_path = board_path

        # Create main panel
        self.panel = SpinRenderPanel(self, board_path)

        # Create sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(sizer)

        # FIT LOGIC: We call Fit() and Centre() after a short delay
        # to ensure the panel has finished its internal Layout()
        wx.CallAfter(self._finalize_init)

        # Set as active instance
        SpinRenderFrame.active_instance = self

        # Bind close event
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def _finalize_init(self):
        """Finalize window size and position"""
        if self:
            self.Fit()
            self.Centre()

    def on_close(self, event):
        """
        Handle window close
        """
        # Clean up resources
        if hasattr(self.panel, 'cleanup'):
            self.panel.cleanup()

        # Clear active instance
        SpinRenderFrame.active_instance = None

        self.Destroy()


# Register plugin with KiCad
SpinRenderPlugin().register()
