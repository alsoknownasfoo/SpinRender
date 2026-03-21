"""
UI-specific dependency management.
Provides DependencyChecker with UI integration (check_and_prompt, font installation).
"""
import os
import subprocess
import threading
import time
import logging
import sys

# Try to import wx, but don't crash if it's missing yet
try:
    import wx
except ImportError:
    wx = None

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

        # 1. wxPython check (System level - required for any GUI)
        if not self.check_python_package("wxPython"):
            logger.warning("wxPython is missing. Prompting for system-level installation.")
            if not self._prompt_and_poll_for_wxpython():
                logger.error("User declined wxPython installation or polling failed.")
                return False

        # 2. System Assets check (Fonts - required for themed UI)
        # Use native dialogs for consistency with wxPython check
        if self.system == 'darwin':
            logger.debug("Running macOS font check...")
            if not self._ensure_macos_fonts_native():
                logger.warning("macOS font check failed - user cancelled")
                return False
            logger.debug("macOS font check passed")

        # 3. Comprehensive dependency check (Commands and Python libs)
        # Now that we have wx, we can safely proceed with wx-based UI
        import wx
        logger.debug("Running check_all()...")
        dep_status = self.check_all()
        logger.debug(f"Dependency status: {dep_status}")

        if not self.missing_deps:
            logger.info("No missing dependencies - all checks passed")
            return True

        logger.warning(f"Missing dependencies detected: {self.missing_deps}")

        # 4. Show Themed Dependency Dialog for remaining items
        logger.debug("Importing bootstrap DependencyDialog...")
        from .dependency_dialog import DependencyDialog
        logger.debug("Creating dialog...")
        dialog = DependencyDialog(None, dep_status, self)
        logger.debug("Showing modal dialog...")
        result = dialog.ShowModal()
        logger.debug(f"Dialog returned: {result}, missing_deps: {self.missing_deps}")
        dialog.Destroy()

        passed = result == wx.ID_OK or not self.missing_deps
        logger.debug(f"check_and_prompt returning: {passed}")
        return passed

    def _prompt_and_poll_for_wxpython(self):
        """Show native prompt, launch terminal for install, and poll for package availability."""
        msg = "SpinRender requires 'wxPython' to display its interface. Would you like to install it now in the KiCad Python environment?"
        title = "wxPython Required"
        
        python_exe = self._get_python_executable()
        install_cmd = f"{python_exe} -m pip install --user wxPython"
        user_chose_install = self._show_native_confirm(title, msg)

        if user_chose_install:
            if self.system == 'darwin':
                subprocess.Popen(['osascript', '-e', f'tell application "Terminal" to do script "{install_cmd}"'])
            elif self.system == 'windows':
                subprocess.Popen(['cmd', '/c', 'start', 'cmd', '/k', install_cmd])
            else:
                # Fallback for Linux
                print(f"\n!!! {title} !!!\n{msg}")
                subprocess.Popen(install_cmd.split())

            logger.info("Polling for wxPython installation (Timeout: 5m)...")
            start_time = time.time()
            while time.time() - start_time < 300:
                if self.check_python_package("wxPython"):
                    logger.info("wxPython detected!")
                    return True
                time.sleep(2)
            logger.error("Timed out waiting for wxPython installation.")
            
        return False

    def _ensure_macos_fonts_native(self):
        """Check for fonts and prompt using osascript for UX consistency."""
        # Note: We can't use wx.FontEnumerator here if wx isn't fully ready or we want zero wx dependency
        # but since this runs AFTER wxPython check, we could. However, for consistency, we'll keep it "native-ish".
        
        # Helper to check font files in standard locations
        def is_font_installed(face_name):
            # Simple check via fc-list if available or just assume we need them if we can't verify easily without wx
            try:
                import wx
                enumerator = wx.FontEnumerator()
                enumerator.EnumerateFacenames()
                return face_name in enumerator.GetFacenames()
            except:
                return False

        missing = []
        if not is_font_installed(JETBRAINS_MONO): missing.append("JetBrains Mono")
        if not is_font_installed(MDI_FONT_FAMILY): missing.append("Material Design Icons")
        if not is_font_installed(OSWALD): missing.append("Oswald")
        
        if not missing: return True

        msg = (f"SpinRender requires the following fonts for its interface:\\n• {', '.join(missing)}\\n\\n"
               "Would you like to install them now? (Font files will open; please click 'Install' for each)")
        
        if self._show_native_confirm("Fonts Required", msg):
            plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            fonts_dir = os.path.join(plugin_dir, "resources", "fonts")
            if os.path.exists(fonts_dir):
                font_files = {
                    "JetBrains Mono": "JetBrainsMono-VariableFont_wght.ttf",
                    "Material Design Icons": "materialdesignicons-webfont.ttf",
                    "Oswald": "Oswald-VariableFont_wght.ttf"
                }
                for name in missing:
                    file_path = os.path.join(fonts_dir, font_files.get(name, ""))
                    if os.path.exists(file_path):
                        subprocess.run(["open", file_path])
            
            # Poll for installation
            logger.info("Polling for font installation...")
            start_time = time.time()
            while time.time() - start_time < 300:
                still_missing = []
                if not is_font_installed(JETBRAINS_MONO): still_missing.append("JetBrains Mono")
                if not is_font_installed(MDI_FONT_FAMILY): still_missing.append("Material Design Icons")
                if not is_font_installed(OSWALD): still_missing.append("Oswald")
                
                if not still_missing:
                    logger.info("All fonts detected!")
                    return True
                time.sleep(2)
            
        return False

    def _show_native_confirm(self, title, msg):
        """Show a native OS confirmation dialog (osascript/powershell)."""
        if self.system == 'darwin':
            script = f'display dialog "{msg}" with title "{title}" buttons {{"Exit", "Install"}} default button "Install"'
            try:
                result = subprocess.check_output(['osascript', '-e', script]).decode('utf-8').strip()
                return "button returned:Install" in result
            except: return False
        elif self.system == 'windows':
            script = '[void][System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms"); '
            script += f'$res = [System.Windows.Forms.MessageBox]::Show("{msg}", "{title}", "YesNo", "Information"); if($res -eq "Yes") {{ echo "Install" }} else {{ echo "Exit" }}'
            try:
                result = subprocess.check_output(['powershell', '-Command', script]).decode('utf-8').strip()
                return "Install" in result
            except: return False
        return False
