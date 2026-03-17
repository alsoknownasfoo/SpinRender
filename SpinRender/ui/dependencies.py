"""
UI-specific dependency management.
Provides DependencyChecker with UI integration (check_and_prompt, font installation).
"""
import wx
import os
import subprocess
import threading
import time

from utils.dependencies import DependencyChecker as PureDependencyChecker
from .dialogs import DependencyCheckDialog
from foundation.fonts import JETBRAINS_MONO, MDI_FONT_FAMILY, OSWALD


class DependencyChecker(PureDependencyChecker):
    """DependencyChecker with UI methods for prompting and font installation."""

    def check_and_prompt(self):
        """
        Check dependencies and show UI prompts if any are missing.
        Returns True if all deps are satisfied or user proceeds with installation.
        """
        # macOS font check
        if self.system == 'darwin':
            if not self._ensure_macos_fonts():
                return False

        dep_status = self.check_all()
        if not self.missing_deps:
            return True

        dialog = DependencyCheckDialog(None, dep_status, self)
        result = dialog.ShowModal()
        dialog.Destroy()

        return result == wx.ID_OK or not self.missing_deps

    def _ensure_macos_fonts(self):
        """On macOS, check for required fonts and offer to install if missing."""
        # Helper to check if a font face is available
        def is_font_available(face_name):
            try:
                enumerator = wx.FontEnumerator()
                enumerator.EnumerateFacenames()
                return face_name in enumerator.GetFacenames()
            except Exception:
                return False

        def get_missing_fonts():
            missing = []
            if not is_font_available(JETBRAINS_MONO):
                missing.append("JetBrains Mono")
            if not is_font_available(MDI_FONT_FAMILY):
                missing.append("Material Design Icons")
            if not is_font_available(OSWALD):
                missing.append("Oswald")
            return missing

        missing = get_missing_fonts()
        if not missing:
            return True

        # Prompt user to install
        msg = (
            f"SpinRender requires the following fonts for its interface:\n"
            f"• {', '.join(missing)}\n\n"
            "These fonts must be installed to continue. Would you like to install them now?\n"
            "(macOS Font Book will open; please click 'Install Font' for each file)"
        )

        dlg = wx.MessageDialog(None, msg, "Fonts Required", wx.YES_NO | wx.ICON_INFORMATION)
        dlg.SetYesNoLabels("Install", "Exit")
        resp = dlg.ShowModal()
        dlg.Destroy()

        if resp == wx.ID_YES:
            # Locate fonts directory
            plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            fonts_dir = os.path.join(plugin_dir, "resources", "fonts")

            # Open only missing font files
            if os.path.exists(fonts_dir):
                if "JetBrains Mono" in missing:
                    subprocess.run(["open", os.path.join(fonts_dir, "JetBrainsMono-VariableFont_wght.ttf")])
                if "Material Design Icons" in missing:
                    subprocess.run(["open", os.path.join(fonts_dir, "MaterialDesignIconsDesktop.ttf")])
                if "Oswald" in missing:
                    subprocess.run(["open", os.path.join(fonts_dir, "Oswald-VariableFont_wght.ttf")])

            # Wait in background for fonts to be installed
            wait_dlg = wx.ProgressDialog(
                "Installing Fonts",
                "Waiting for font installation in Font Book...\nPlugin will continue automatically when finished.\n\nClick 'Cancel' to exit setup.",
                parent=None,
                style=wx.PD_APP_MODAL | wx.PD_CAN_ABORT | wx.PD_ELAPSED_TIME
            )

            ready = False
            while not ready:
                if not get_missing_fonts():
                    ready = True
                    break

                keep_going, _ = wait_dlg.Update(50, "Waiting for font installation in Font Book...")
                if not keep_going:
                    wait_dlg.Destroy()
                    return False

                wx.SafeYield()
                time.sleep(1.0)

            wait_dlg.Destroy()
            return True
        else:
            return False
