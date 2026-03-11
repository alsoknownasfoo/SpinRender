"""
Dependency checker for SpinRender
Checks for kicad-cli and ffmpeg, offers automatic installation
"""
import subprocess
import platform
import os
import sys
import wx
import shutil
import importlib
import site
import threading
from ui.custom_controls import CustomButton, get_mdi_font

class DependencyChecker:
    """
    Checks and manages dependencies for SpinRender
    """

    REQUIRED_DEPS = {
        'kicad-cli': {
            'command': 'kicad-cli',
            'test_args': ['--version'],
            'install_macos': 'brew install kicad',
            'install_linux': 'sudo apt-get install kicad',
            'install_windows': 'Download from https://www.kicad.org/download/',
            'type': 'command'
        },
        'ffmpeg': {
            'command': 'ffmpeg',
            'test_args': ['-version'],
            'install_macos': 'brew install ffmpeg',
            'install_linux': 'sudo apt-get install ffmpeg',
            'install_windows': 'Download from https://ffmpeg.org/download.html',
            'type': 'command'
        },
        'PyOpenGL': {
            'package_name': 'PyOpenGL PyOpenGL-accelerate',
            'type': 'python'
        },
        'numpy': {
            'package_name': 'numpy',
            'type': 'python'
        },
        'trimesh': {
            'package_name': 'trimesh',
            'type': 'python'
        }
    }

    def __init__(self):
        self.system = platform.system().lower()
        self.missing_deps = []
        self.found_paths = {}  # Store paths where deps were found
        
        # Ensure user site-packages are in sys.path
        user_site = site.getusersitepackages()
        if user_site not in sys.path:
            sys.path.append(user_site)

    def _get_python_executable(self):
        """
        Find the actual Python executable
        """
        exe = sys.executable
        
        if 'darwin' in self.system and ('kicad' in exe.lower() or 'pcbnew' in exe.lower()):
            dir_path = os.path.dirname(exe)
            py_exe = os.path.join(dir_path, "python3")
            if os.path.exists(py_exe):
                return py_exe
            
            bundle_contents = os.path.dirname(dir_path) # Contents
            framework_py = os.path.join(bundle_contents, "Frameworks", "Python.framework", "Versions", "Current", "bin", "python3")
            if os.path.exists(framework_py):
                return framework_py

        if 'windows' in self.system and 'python.exe' not in exe.lower():
            dir_path = os.path.dirname(exe)
            py_exe = os.path.join(dir_path, "python.exe")
            if os.path.exists(py_exe):
                return py_exe

        return exe

    def check_dependency(self, dep_name):
        """
        Check if a dependency is available
        """
        dep_info = self.REQUIRED_DEPS.get(dep_name)
        if not dep_info:
            return False

        command_path = shutil.which(dep_info['command'])
        if not command_path and dep_name == 'kicad-cli':
            common_paths = [
                '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli',
                '/usr/local/bin/kicad-cli',
                '/opt/homebrew/bin/kicad-cli'
            ]
            for path in common_paths:
                if os.path.exists(path):
                    command_path = path
                    break

        if not command_path and dep_name == 'ffmpeg':
            common_paths = [
                '/usr/local/bin/ffmpeg',
                '/opt/homebrew/bin/ffmpeg',
                '/usr/bin/ffmpeg'
            ]
            for path in common_paths:
                if os.path.exists(path):
                    command_path = path
                    break

        if command_path:
            try:
                subprocess.run(
                    [command_path] + dep_info['test_args'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5,
                    check=False
                )
                self.found_paths[dep_name] = command_path
                return True
            except Exception:
                if os.path.exists(command_path) and os.access(command_path, os.X_OK):
                    self.found_paths[dep_name] = command_path
                    return True
                return False

        return False

    def check_python_package(self, package_name):
        """
        Check if a Python package is available
        """
        try:
            importlib.invalidate_caches()
            pkg = package_name.split()[0]
            if pkg == 'PyOpenGL':
                pkg = 'OpenGL'
            __import__(pkg)
            return True
        except ImportError:
            return False

    def check_all(self):
        """
        Check all required dependencies
        """
        results = {}
        self.missing_deps = []

        for dep_name, dep_info in self.REQUIRED_DEPS.items():
            if dep_info['type'] == 'command':
                found = self.check_dependency(dep_name)
            elif dep_info['type'] == 'python':
                found = self.check_python_package(dep_info['package_name'])
            else:
                found = False

            results[dep_name] = found
            if not found:
                self.missing_deps.append(dep_name)

        return results

    def check_and_prompt(self):
        """
        Check dependencies and prompt user if any are missing
        """
        # On macOS, check for required fonts and offer installation
        if self.system == 'darwin':
            if not self._ensure_macos_fonts():
                return False  # User chose to EXIT

        dep_status = self.check_all()

        if not self.missing_deps:
            return True

        dialog = DependencyCheckDialog(None, dep_status, self)
        result = dialog.ShowModal()
        dialog.Destroy()

        return result == wx.ID_OK or not self.missing_deps

    def _ensure_macos_fonts(self):
        """
        On macOS, check for JetBrains Mono, MDI, and Oswald. 
        If missing, offer to open the font files for the user to install.
        """
        from ui.custom_controls import _JETBRAINS_MONO, _MDI_FONT_FAMILY, _OSWALD
        
        # Helper to check if a font face is already available in the runtime.
        def is_font_available(face_name):
            try:
                enumerator = wx.FontEnumerator()
                enumerator.EnumerateFacenames()
                return face_name in enumerator.GetFacenames()
            except Exception:
                return False

        def get_missing_fonts():
            missing = []
            if not is_font_available(_JETBRAINS_MONO):
                missing.append("JetBrains Mono")
            if not is_font_available(_MDI_FONT_FAMILY):
                missing.append("Material Design Icons")
            if not is_font_available(_OSWALD):
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
            
            # 1. Open ONLY missing font files
            if os.path.exists(fonts_dir):
                if "JetBrains Mono" in missing:
                    subprocess.run(["open", os.path.join(fonts_dir, "JetBrainsMono-VariableFont_wght.ttf")])
                if "Material Design Icons" in missing:
                    subprocess.run(["open", os.path.join(fonts_dir, "MaterialDesignIconsDesktop.ttf")])
                if "Oswald" in missing:
                    subprocess.run(["open", os.path.join(fonts_dir, "Oswald-VariableFont_wght.ttf")])

            # 2. Wait in background for fonts to be installed
            wait_dlg = wx.ProgressDialog(
                "Installing Fonts",
                "Waiting for font installation in Font Book...\nPlugin will continue automatically when finished.\n\nClick 'Cancel' to exit setup.",
                parent=None,
                style=wx.PD_APP_MODAL | wx.PD_CAN_ABORT | wx.PD_ELAPSED_TIME
            )
            
            ready = False
            while not ready:
                # Check if fonts are now available
                if not get_missing_fonts():
                    ready = True
                    break
                
                # Update dialog and check for cancel
                keep_going, _ = wait_dlg.Update(50, "Waiting for font installation in Font Book...")
                if not keep_going:
                    wait_dlg.Destroy()
                    return False
                
                # Yield to UI and wait a bit
                wx.SafeYield()
                import time
                time.sleep(1.0)
            
            wait_dlg.Destroy()
            return True
        else:
            return False

    def install_dependency(self, dep_name, callback=None):
        """
        Attempt to install a missing dependency with real-time feedback
        """
        dep_info = self.REQUIRED_DEPS.get(dep_name)
        if not dep_info:
            return False, f"Unknown dependency: {dep_name}"

        if dep_info['type'] == 'python':
            package_name = dep_info.get('package_name', '')
            python_exe = self._get_python_executable()
            install_cmd = [python_exe, "-m", "pip", "install", "--user"] + package_name.split()
            use_shell = False
        else:
            install_key = f'install_{self.system}' if 'darwin' not in self.system else 'install_macos'
            install_cmd_str = dep_info.get(install_key, '')

            if not install_cmd_str or install_cmd_str.startswith('Download from'):
                return False, install_cmd_str or "No install command"

            if 'darwin' in self.system or 'linux' in self.system:
                brew_paths = ['/opt/homebrew/bin/brew', '/usr/local/bin/brew']
                apt_paths = ['/usr/bin/apt-get']

                cmd_to_run = None
                if 'brew' in install_cmd_str:
                    for brew_path in brew_paths:
                        if os.path.exists(brew_path):
                            cmd_to_run = install_cmd_str.replace('brew', brew_path)
                            break
                elif 'apt-get' in install_cmd_str:
                    for apt_path in apt_paths:
                        if os.path.exists(apt_path):
                            cmd_to_run = install_cmd_str.replace('sudo apt-get', f'sudo {apt_path}')
                            break

                if not cmd_to_run:
                    return False, f"Package manager not found: {install_cmd_str}"

                install_cmd = cmd_to_run
                use_shell = True
            else:
                return False, install_cmd_str

        try:
            process = subprocess.Popen(
                install_cmd,
                shell=use_shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            if process.stdout:
                for line in process.stdout:
                    clean_line = line.strip()
                    if clean_line and callback:
                        callback(clean_line)

            process.wait()

            if process.returncode == 0:
                if dep_info['type'] == 'python':
                    importlib.invalidate_caches()
                return True, "Success"
            else:
                return False, "Failed"

        except Exception as e:
            return False, str(e)


class DependencyCheckDialog(wx.Dialog):
    """
    Dialog for dependency checking and installation
    Follows High-Density aesthetic from Res/SpinRender.pen
    """

    def __init__(self, parent, dep_status, checker):
        super().__init__(
            parent,
            title="SpinRender - Setup Required",
            size=(500, 650),
            style=wx.FRAME_NO_TASKBAR | wx.BORDER_NONE | wx.STAY_ON_TOP
        )

        self.dep_status = dep_status
        self.checker = checker

        # Design system colors
        self.bg_color = wx.Colour(17, 17, 17) # $bg-surface
        self.bg_input = wx.Colour(13, 13, 13) # $bg-input
        self.text_primary = wx.Colour(224, 224, 224) # $text-primary
        self.text_secondary = wx.Colour(119, 119, 119) # $text-secondary
        self.accent_yellow = wx.Colour(255, 214, 0) # $accent-yellow
        self.accent_green = wx.Colour(76, 175, 80) # $accent-green
        self.accent_orange = wx.Colour(255, 107, 53) # $accent-orange
        self.accent_cyan = wx.Colour(0, 188, 212) # $accent-cyan
        self.border_default = wx.Colour(51, 51, 51) # $border-default

        self.SetBackgroundColour(self.bg_color)
        
        # UI state
        self.current_dep_index = 0
        self.num_deps = 0
        
        # simulated progress timer
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)

        self.build_ui()
        self.Centre()

        # Dragging support - Bind specifically to header components
        self.header.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.header.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.header.Bind(wx.EVT_MOTION, self.on_mouse_motion)
        
        self.header_title.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.header_title.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.header_title.Bind(wx.EVT_MOTION, self.on_mouse_motion)
        
        self.drag_pos = None

    def build_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Header (Drag handle)
        self.header = wx.Panel(self, size=(-1, 48))
        self.header.SetBackgroundColour(self.bg_color)
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.header_title = wx.StaticText(self.header, label="SETUP REQUIRED")
        self.header_title.SetForegroundColour(self.accent_yellow)
        self.header_title.SetFont(wx.Font(13, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_SEMIBOLD, faceName="JetBrains Mono"))
        
        header_sizer.Add(self.header_title, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 16)
        self.header.SetSizer(header_sizer)
        main_sizer.Add(self.header, 0, wx.EXPAND)

        # Border separator
        line = wx.Panel(self, size=(-1, 1))
        line.SetBackgroundColour(self.border_default)
        main_sizer.Add(line, 0, wx.EXPAND)

        # Content Panel
        content = wx.Panel(self)
        self.content_sizer = wx.BoxSizer(wx.VERTICAL)
        
        msg = wx.StaticText(content, label="SpinRender requires the following dependencies to function:")
        msg.SetForegroundColour(self.text_secondary)
        msg.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="Inter"))
        self.content_sizer.Add(msg, 0, wx.ALL, 16)

        # List existing dependencies
        for dep_name, is_found in self.dep_status.items():
            dep_panel = wx.Panel(content)
            dep_panel.SetBackgroundColour(self.bg_input)
            dep_sizer = wx.BoxSizer(wx.VERTICAL)
            row_sizer = wx.BoxSizer(wx.HORIZONTAL)

            dep_label = wx.StaticText(dep_panel, label=dep_name)
            dep_label.SetForegroundColour(self.text_primary)
            dep_label.SetFont(wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="JetBrains Mono"))

            # Use bundled MDI symbols (required)
            status_symbol = "mdi-check-circle" if is_found else "mdi-close-circle"
            status_color = self.accent_green if is_found else self.accent_orange
            
            # The CustomButton.ICONS already handles the hex translation
            from ui.custom_controls import CustomButton
            icon_char = CustomButton.ICONS.get(status_symbol, "")
            
            status_label = wx.StaticText(dep_panel, label=icon_char)
            status_label.SetForegroundColour(status_color)
            status_label.SetFont(get_mdi_font(14))

            row_sizer.Add(dep_label, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 16)
            row_sizer.Add(status_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 16)
            # Increase vertical height/whitespace
            dep_sizer.Add(row_sizer, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 12)

            dep_panel.SetSizer(dep_sizer)
            # Increase horizontal padding (inset more)
            self.content_sizer.Add(dep_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 24)

        # Integrated Progress Area
        self.progress_panel = wx.Panel(content)
        self.progress_panel.Hide()
        progress_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.progress_gauge = wx.Gauge(self.progress_panel, range=100, size=(-1, 4))
        self.progress_gauge.SetBackgroundColour(self.bg_input)
        self.progress_gauge.SetForegroundColour(self.accent_cyan)
        progress_sizer.Add(self.progress_gauge, 0, wx.EXPAND | wx.BOTTOM, 8)
        
        self.progress_status = wx.StaticText(self.progress_panel, label="Initializing...")
        self.progress_status.SetForegroundColour(self.text_primary)
        self.progress_status.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, faceName="Inter"))
        progress_sizer.Add(self.progress_status, 0, wx.EXPAND | wx.BOTTOM, 8)
        
        self.progress_log = wx.TextCtrl(
            self.progress_panel, 
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.NO_BORDER | wx.TE_RICH
        )
        self.progress_log.SetBackgroundColour(self.bg_input)
        self.progress_log.SetForegroundColour(self.text_secondary)
        self.progress_log.SetFont(wx.Font(8, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="JetBrains Mono"))
        progress_sizer.Add(self.progress_log, 1, wx.EXPAND)
        
        self.progress_panel.SetSizer(progress_sizer)
        self.content_sizer.Add(self.progress_panel, 1, wx.EXPAND | wx.ALL, 16)

        content.SetSizer(self.content_sizer)
        main_sizer.Add(content, 1, wx.EXPAND)

        # Footer with custom buttons
        footer = wx.Panel(self)
        footer_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Secondary Button (Close)
        self.close_btn = CustomButton(footer, label="EXIT", primary=False, danger=True, size=(90, 36))
        self.close_btn.Bind(wx.EVT_BUTTON, self.on_close)
        
        # Action Button (Install)
        self.install_btn = CustomButton(footer, label="INSTALL", primary=True, size=(150, 36))
        self.install_btn.Bind(wx.EVT_BUTTON, self.on_install)

        footer_sizer.AddStretchSpacer()
        footer_sizer.Add(self.close_btn, 0, wx.RIGHT, 12)
        footer_sizer.Add(self.install_btn, 0, wx.RIGHT, 16)

        footer.SetSizer(footer_sizer)
        main_sizer.Add(footer, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 16)

        self.SetSizer(main_sizer)

    # Window Dragging Logic
    def on_left_down(self, event):
        win = event.GetEventObject()
        win.CaptureMouse()
        x, y = win.ClientToScreen(event.GetPosition())
        origin_x, origin_y = self.GetPosition()
        self.drag_pos = wx.Point(x - origin_x, y - origin_y)

    def on_left_up(self, event):
        win = event.GetEventObject()
        if win.HasCapture():
            win.ReleaseMouse()

    def on_mouse_motion(self, event):
        if event.Dragging() and event.LeftIsDown() and self.drag_pos:
            win = event.GetEventObject()
            x, y = win.ClientToScreen(event.GetPosition())
            new_pos = wx.Point(x - self.drag_pos.x, y - self.drag_pos.y)
            self.Move(new_pos)

    def on_timer(self, event):
        val = self.progress_gauge.GetValue()
        limit = (self.current_dep_index * 100) + 95
        if val < limit:
            self.progress_gauge.SetValue(val + 1)

    def on_close(self, event):
        """Close dialog"""
        self.EndModal(wx.ID_CANCEL)

    def on_install(self, event):
        if not self.checker.missing_deps:
            self.EndModal(wx.ID_OK)
            return

        # UI State: Disable buttons
        self.install_btn.Enable(False)
        self.close_btn.Enable(False)
        
        self.progress_panel.Show()
        self.progress_log.Clear()
        self.Layout()

        self.num_deps = len(self.checker.missing_deps)
        self.progress_gauge.SetRange(self.num_deps * 100)
        self.progress_gauge.SetValue(0)
        
        self.timer.Start(100)

        thread = threading.Thread(target=self._run_install_thread)
        thread.daemon = True
        thread.start()

    def _run_install_thread(self):
        num_deps = len(self.checker.missing_deps)
        for i, dep_name in enumerate(self.checker.missing_deps):
            self.current_dep_index = i
            is_last = (i == num_deps - 1)
            wx.CallAfter(self.progress_status.SetLabel, f"Installing {dep_name}...")
            
            def log_callback(message):
                wx.CallAfter(self._append_log, message)
                if is_last and "Successfully installed" in message:
                    wx.CallAfter(self.progress_gauge.SetValue, num_deps * 100)
                    wx.CallAfter(self.progress_status.SetLabel, "Installation complete.")

            self.checker.install_dependency(dep_name, callback=log_callback)
            wx.CallAfter(self.progress_gauge.SetValue, (i + 1) * 100)

        wx.CallAfter(self._on_install_finished)

    def _append_log(self, message):
        self.progress_log.AppendText(message + "\n")
        self.progress_log.ShowPosition(self.progress_log.GetLastPosition())

    def _on_install_finished(self):
        self.timer.Stop()
        self.progress_gauge.SetValue(self.num_deps * 100)
        
        self.dep_status = self.checker.check_all()
        if not self.checker.missing_deps:
            self.EndModal(wx.ID_OK)
        else:
            self.install_btn.Enable(True)
            self.close_btn.Enable(True)
            self.progress_status.SetLabel("Some installations failed.")
            self.Layout()
