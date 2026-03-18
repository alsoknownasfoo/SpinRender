"""
UI-specific dependency management.
Provides DependencyChecker with UI integration (check_and_prompt, font installation).
"""
import wx
import os
import subprocess
import threading
import time
import logging

from SpinRender.utils.check_dependencies import DependencyChecker as PureDependencyChecker
from SpinRender.foundation.fonts import JETBRAINS_MONO, MDI_FONT_FAMILY, OSWALD

logger = logging.getLogger("SpinRender")


class DependencyChecker(PureDependencyChecker):
    """DependencyChecker with UI methods for prompting and font installation."""

    def check_and_prompt(self):
        """
        Check dependencies and show UI prompts if any are missing.
        Returns True if all deps are satisfied or user proceeds with installation.
        """
        logger.debug("DependencyChecker.check_and_prompt() starting")
        # macOS font check
        if self.system == 'darwin':
            logger.debug("Running macOS font check...")
            if not self._ensure_macos_fonts():
                logger.warning("macOS font check failed - user cancelled")
                return False
            logger.debug("macOS font check passed")
        else:
            logger.debug(f"Skipping font check on platform: {self.system}")

        logger.debug("Running check_all()...")
        dep_status = self.check_all()
        logger.debug(f"Dependency status: {dep_status}")

        if not self.missing_deps:
            logger.info("No missing dependencies - all checks passed")
            return True

        logger.warning(f"Missing dependencies detected: {self.missing_deps}")

        # Import bootstrap dialog to avoid early theme loading
        logger.debug("Importing bootstrap DependencyCheckDialog...")
        from .dependency_dialog import DependencyCheckDialog
        logger.debug("Creating dialog...")
        dialog = DependencyCheckDialog(None, dep_status, self)
        logger.debug("Showing modal dialog...")
        result = dialog.ShowModal()
        logger.debug(f"Dialog returned: {result}, missing_deps: {self.missing_deps}")
        dialog.Destroy()

        passed = result == wx.ID_OK or not self.missing_deps
        logger.debug(f"check_and_prompt returning: {passed}")
        return passed

    def _ensure_macos_fonts(self):
        """On macOS, check for required fonts and offer to install if missing."""
        logger.debug("_ensure_macos_fonts() starting")
        # Helper to check if a font face is available
        def is_font_available(face_name):
            try:
                enumerator = wx.FontEnumerator()
                enumerator.EnumerateFacenames()
                available = face_name in enumerator.GetFacenames()
                logger.debug(f"Font '{face_name}' available: {available}")
                return available
            except Exception as e:
                logger.debug(f"Font check error for '{face_name}': {e}")
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
            logger.debug("All required fonts are present")
            return True

        logger.info(f"Missing fonts: {missing}")
        # Prompt user to install
        msg = (
            f"SpinRender requires the following fonts for its interface:\n"
            f"• {', '.join(missing)}\n\n"
            "These fonts must be installed to continue. Would you like to install them now?\n"
            "(macOS Font Book will open; please click 'Install Font' for each file)"
        )

        logger.debug("Showing font installation prompt...")
        dlg = wx.MessageDialog(None, msg, "Fonts Required", wx.YES_NO | wx.ICON_INFORMATION)
        dlg.SetYesNoLabels("Install", "Exit")
        resp = dlg.ShowModal()
        dlg.Destroy()
        logger.debug(f"Font prompt response: {resp} (wx.ID_YES={wx.ID_YES})")

        if resp == wx.ID_YES:
            logger.info("User chose to install fonts")
            # Locate fonts directory
            plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            fonts_dir = os.path.join(plugin_dir, "resources", "fonts")
            logger.debug(f"Fonts directory: {fonts_dir}")

            # Open only missing font files
            if os.path.exists(fonts_dir):
                if "JetBrains Mono" in missing:
                    font_path = os.path.join(fonts_dir, "JetBrainsMono-VariableFont_wght.ttf")
                    logger.debug(f"Opening JetBrains Mono: {font_path}")
                    subprocess.run(["open", font_path])
                if "Material Design Icons" in missing:
                    font_path = os.path.join(fonts_dir, "materialdesignicons-webfont.ttf")
                    logger.debug(f"Opening MDI: {font_path}")
                    subprocess.run(["open", font_path])
                if "Oswald" in missing:
                    font_path = os.path.join(fonts_dir, "Oswald-VariableFont_wght.ttf")
                    logger.debug(f"Opening Oswald: {font_path}")
                    subprocess.run(["open", font_path])
            else:
                logger.warning(f"Fonts directory not found: {fonts_dir}")

            # Wait in background for fonts to be installed
            wait_dlg = wx.ProgressDialog(
                "Installing Fonts",
                "Waiting for font installation in Font Book...\nPlugin will continue automatically when finished.\n\nClick 'Cancel' to exit setup.",
                parent=None,
                style=wx.PD_APP_MODAL | wx.PD_CAN_ABORT | wx.PD_ELAPSED_TIME
            )

            ready = False
            wait_iterations = 0
            while not ready:
                wait_iterations += 1
                current_missing = get_missing_fonts()
                logger.debug(f"Font check iteration {wait_iterations}: still missing: {current_missing}")
                if not current_missing:
                    ready = True
                    break

                keep_going, _ = wait_dlg.Update(50, "Waiting for font installation in Font Book...")
                if not keep_going:
                    logger.warning("User cancelled font installation wait")
                    wait_dlg.Destroy()
                    return False

                wx.SafeYield()
                time.sleep(1.0)

            wait_dlg.Destroy()
            logger.info("Font installation completed/verified")
            return True
        else:
            logger.info("User declined font installation")
            return False
