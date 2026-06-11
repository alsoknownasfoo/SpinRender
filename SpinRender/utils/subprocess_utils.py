"""Shared subprocess helpers.

Windows spawns a momentary console window for any child process unless
explicitly suppressed, even when stdout/stderr are piped. ``NO_WINDOW_FLAGS``
is a no-op on other platforms.
"""
import subprocess
import sys

NO_WINDOW_FLAGS = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
