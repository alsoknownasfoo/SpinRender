"""
Dependency checker for SpinRender.
Pure logic module - checks for kicad-cli and ffmpeg, offers automatic installation.
"""
import subprocess
import platform
import os
import sys
import shutil
import importlib
import site
import logging

from .subprocess_utils import NO_WINDOW_FLAGS, find_kicad_sibling_binary

logger = logging.getLogger("SpinRender")


class DependencyChecker:
    """
    Checks and manages dependencies for SpinRender.
    Pure methods: __init__, _get_python_executable, check_dependency, check_python_package,
                  check_all, install_dependency. These have no UI dependencies.
    """

    REQUIRED_DEPS = {
        'wxPython': {
            'package_name': 'wxPython',
            'type': 'python'
        },
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
            'install_windows': 'Re-run install.bat to install ffmpeg via winget',
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
        },
        'PyYAML': {
            'package_name': 'PyYAML',
            'type': 'python'
        },
        'pyobjc-core': {
            'package_name': 'pyobjc-core',
            'type': 'python',
            'platforms': ['darwin']
        },
        'pyobjc-framework-Cocoa': {
            'package_name': 'pyobjc-framework-Cocoa',
            'type': 'python',
            'platforms': ['darwin']
        }
    }

    def __init__(self):
        self.system = platform.system().lower()
        self.missing_deps = []
        self.found_paths = {}  # Store paths where deps were found

        logger.debug(f"DependencyChecker.__init__ on platform: {self.system}")
        # Ensure user site-packages are in sys.path
        user_site = site.getusersitepackages()
        if user_site not in sys.path:
            sys.path.append(user_site)
            logger.debug(f"Added user site-packages: {user_site}")
        else:
            logger.debug(f"User site-packages already present: {user_site}")

    def _get_python_executable(self):
        """Find the actual Python executable"""
        exe = sys.executable

        if 'darwin' in self.system and ('kicad' in exe.lower() or 'pcbnew' in exe.lower()):
            dir_path = os.path.dirname(exe)
            py_exe = os.path.join(dir_path, "python3")
            if os.path.exists(py_exe):
                return py_exe

            bundle_contents = os.path.dirname(dir_path)
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
        """Check if a dependency is available"""
        dep_info = self.REQUIRED_DEPS.get(dep_name)
        if not dep_info:
            return False

        command_path = shutil.which(dep_info['command'])
        if not command_path and dep_name == 'kicad-cli':
            exe_name = 'kicad-cli.exe' if self.system == 'windows' else 'kicad-cli'
            command_path = find_kicad_sibling_binary(exe_name)
        if not command_path and dep_name == 'kicad-cli':
            common_paths = [
                '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli',
                '/usr/local/bin/kicad-cli',
                '/opt/homebrew/bin/kicad-cli'
            ]
            if self.system == 'windows':
                prog_files = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
                for ver in ('10.0', '9.0', '8.0'):
                    common_paths.append(os.path.join(prog_files, 'KiCad', ver, 'bin', 'kicad-cli.exe'))
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
            if self.system == 'windows':
                prog_files = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
                common_paths += [
                    os.path.join(prog_files, 'Gyan', 'FFmpeg', 'bin', 'ffmpeg.exe'),
                    os.path.join(prog_files, 'ffmpeg', 'bin', 'ffmpeg.exe'),
                    'C:\\ffmpeg\\bin\\ffmpeg.exe',
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
                    check=False,
                    creationflags=NO_WINDOW_FLAGS,
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
        """Check if a Python package is available.

        Runs the actual import in a subprocess rather than in-process.
        Some packages (trimesh, via its native/C-extension dependency
        chain) can abort the whole process with a glibc-level crash (e.g.
        "free(): invalid pointer") on certain Linux installs, when native
        libraries they load conflict with ones KiCad already has loaded
        (issue #4). That's a SIGABRT, not a Python exception, so no
        try/except here could ever have caught it - importing in-process
        risks taking KiCad down with it. A crashed child is just reported
        as "not found" instead.
        """
        logger.debug(f"Checking Python package: {package_name}")
        pkg = package_name.split()[0]
        if pkg == 'PyOpenGL':
            pkg = 'OpenGL'
        elif pkg == 'PyYAML':
            pkg = 'yaml'
        elif pkg == 'wxPython':
            pkg = 'wx'
        elif pkg.startswith('pyobjc'):
            pkg = 'objc'

        python_exe = self._get_python_executable()
        try:
            result = subprocess.run(
                [python_exe, "-c", f"import {pkg}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=15,
                creationflags=NO_WINDOW_FLAGS,
            )
        except Exception as e:
            logger.debug(f"  Could not probe package {pkg}: {e}")
            return False

        if result.returncode == 0:
            logger.debug(f"  Package {pkg} is available")
            return True

        stderr = result.stderr.decode(errors='replace').strip()
        logger.debug(f"  Package {pkg} not available (exit {result.returncode}): {stderr}")
        return False

    def check_all(self):
        """Check all required dependencies"""
        logger.debug("check_all() starting")
        results = {}
        self.missing_deps = []

        for dep_name, dep_info in self.REQUIRED_DEPS.items():
            # Skip if not for this platform
            platforms = dep_info.get('platforms')
            if platforms and self.system not in platforms:
                logger.debug(f"Skipping dependency {dep_name} - not required for platform {self.system}")
                continue

            logger.debug(f"Checking dependency: {dep_name}")
            if dep_info['type'] == 'command':
                found = self.check_dependency(dep_name)
            elif dep_info['type'] == 'python':
                found = self.check_python_package(dep_info['package_name'])
            else:
                found = False
            logger.debug(f"  {dep_name}: {'OK' if found else 'MISSING'}")
            results[dep_name] = found
            if not found:
                self.missing_deps.append(dep_name)

        logger.info(f"Dependency check complete: {len(self.missing_deps)} missing: {self.missing_deps}")
        return results

    def _pip_available(self, python_exe):
        """Check whether `python_exe -m pip` actually works.

        Debian/Ubuntu ship a system Python3 with the `pip` module removed
        (it's a separate `python3-pip` apt package), so this can't be
        assumed just because Python itself is present.
        """
        try:
            result = subprocess.run(
                [python_exe, "-m", "pip", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=15,
                creationflags=NO_WINDOW_FLAGS,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _ensure_pip(self, python_exe, callback=None):
        """Bootstrap `pip` on Linux via apt if the interpreter lacks it.

        Uses pkexec rather than sudo: this runs from a GUI process with no
        controlling terminal, so sudo's password prompt has nowhere to go
        ("sudo: A terminal is required to authenticate"). pkexec shows a
        graphical polkit prompt instead and needs no TTY.
        """
        if self._pip_available(python_exe):
            return True

        if 'linux' not in self.system:
            return False

        pkexec_path = shutil.which('pkexec')
        if not pkexec_path:
            logger.error("pip is missing and pkexec is unavailable to install python3-pip")
            return False

        if callback:
            callback("pip not found - requesting privileges to install python3-pip...")
        logger.info("Bootstrapping pip via 'pkexec apt-get install -y python3-pip'")
        apt_path = shutil.which('apt-get') or '/usr/bin/apt-get'
        if not os.path.exists(apt_path):
            logger.error(f"pip is missing and apt-get was not found at {apt_path}")
            return False
        try:
            result = subprocess.run(
                [pkexec_path, apt_path, 'install', '-y', 'python3-pip'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=180,
                creationflags=NO_WINDOW_FLAGS,
            )
        except Exception as e:
            logger.error(f"Failed to bootstrap pip: {e}")
            return False

        if result.returncode != 0:
            logger.error(f"python3-pip install failed (exit {result.returncode}): "
                         f"{result.stdout.decode(errors='replace').strip()}")
            return False

        return self._pip_available(python_exe)

    def install_dependency(self, dep_name, callback=None):
        """Attempt to install a missing dependency with real-time feedback"""
        logger.info(f"Attempting to install dependency: {dep_name}")
        dep_info = self.REQUIRED_DEPS.get(dep_name)
        if not dep_info:
            logger.error(f"Unknown dependency requested: {dep_name}")
            return False, f"Unknown dependency: {dep_name}"

        if dep_info['type'] == 'python':
            package_name = dep_info.get('package_name', '')
            python_exe = self._get_python_executable()
            logger.debug(f"Using Python executable: {python_exe}")

            if not self._ensure_pip(python_exe, callback):
                msg = ("pip is not available for this Python interpreter and could not be "
                       "installed automatically. Run 'sudo apt install python3-pip' and try again.")
                logger.error(msg)
                return False, msg

            install_cmd = [python_exe, "-m", "pip", "install", "--user"]
            if 'linux' in self.system:
                # Debian/Ubuntu's system Python is PEP 668 "externally managed",
                # which makes pip refuse any install outside a venv. --user
                # already keeps this out of apt-managed site-packages, so the
                # override is safe here - it's what PEP 668 itself suggests
                # for this exact case (installing into a specific host app's
                # runtime rather than the system-wide environment).
                install_cmd.append("--break-system-packages")
            install_cmd += package_name.split()
            use_shell = False
        else:
            install_key = f'install_{self.system}' if 'darwin' not in self.system else 'install_macos'
            install_cmd_str = dep_info.get(install_key, '')
            logger.debug(f"Install command string: {install_cmd_str}")

            if not install_cmd_str or install_cmd_str.startswith('Download from'):
                logger.warning(f"No automatic install available for {dep_name}")
                return False, install_cmd_str or "No install command"

            if 'darwin' in self.system or 'linux' in self.system:
                brew_paths = ['/opt/homebrew/bin/brew', '/usr/local/bin/brew']

                cmd_to_run = None
                if 'brew' in install_cmd_str:
                    for brew_path in brew_paths:
                        if os.path.exists(brew_path):
                            cmd_to_run = install_cmd_str.replace('brew', brew_path)
                            break
                elif 'apt-get' in install_cmd_str:
                    pkexec_path = shutil.which('pkexec')
                    if pkexec_path:
                        # pkexec needs an absolute path to the target binary and
                        # doesn't go through a login shell PATH lookup like sudo does.
                        apt_path = shutil.which('apt-get') or '/usr/bin/apt-get'
                        rest = install_cmd_str.split('apt-get', 1)[1].strip()
                        cmd_to_run = f'{pkexec_path} {apt_path} -y {rest}'

                if not cmd_to_run:
                    logger.error(f"Package manager not found for: {install_cmd_str}")
                    return False, f"Package manager not found: {install_cmd_str}"

                install_cmd = cmd_to_run
                use_shell = True
            else:
                logger.warning(f"No automatic installer for {dep_name} on {self.system}")
                return False, install_cmd_str

        logger.debug(f"Executing: {install_cmd}")
        try:
            process = subprocess.Popen(
                install_cmd,
                shell=use_shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=NO_WINDOW_FLAGS,
            )

            if process.stdout:
                for line in process.stdout:
                    clean_line = line.strip()
                    if clean_line:
                        logger.debug(f"[install] {clean_line}")
                        if callback:
                            callback(clean_line)

            process.wait()

            if process.returncode == 0:
                logger.info(f"Successfully installed {dep_name}")
                if dep_info['type'] == 'python':
                    importlib.invalidate_caches()
                return True, "Success"
            else:
                logger.error(f"Installation failed for {dep_name} with exit code {process.returncode}")
                return False, f"Install failed with exit code {process.returncode}"

        except Exception as e:
            logger.error(f"Installation exception for {dep_name}: {e}", exc_info=True)
            return False, str(e)
