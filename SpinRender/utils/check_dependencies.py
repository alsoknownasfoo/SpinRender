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

logger = logging.getLogger("SpinRender")


class DependencyChecker:
    """
    Checks and manages dependencies for SpinRender.
    Pure methods: __init__, _get_python_executable, check_dependency, check_python_package,
                  check_all, install_dependency. These have no UI dependencies.
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
        },
        'PyYAML': {
            'package_name': 'PyYAML',
            'type': 'python'
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
        """Check if a Python package is available"""
        logger.debug(f"Checking Python package: {package_name}")
        try:
            importlib.invalidate_caches()
            pkg = package_name.split()[0]
            if pkg == 'PyOpenGL':
                pkg = 'OpenGL'
            __import__(pkg)
            logger.debug(f"  Package {pkg} is available")
            return True
        except ImportError as e:
            logger.debug(f"  Package not available: {e}")
            return False

    def check_all(self):
        """Check all required dependencies"""
        logger.debug("check_all() starting")
        results = {}
        self.missing_deps = []

        for dep_name, dep_info in self.REQUIRED_DEPS.items():
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
            install_cmd = [python_exe, "-m", "pip", "install", "--user"] + package_name.split()
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
                    logger.error(f"Package manager not found for: {install_cmd_str}")
                    return False, f"Package manager not found: {install_cmd_str}"

                install_cmd = cmd_to_run
                use_shell = True
            else:
                logger.warning(f"Unsupported platform for auto-install: {self.system}")
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
                universal_newlines=True
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
