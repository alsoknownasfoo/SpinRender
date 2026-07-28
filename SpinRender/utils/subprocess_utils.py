"""Shared subprocess helpers.

Windows spawns a momentary console window for any child process unless
explicitly suppressed, even when stdout/stderr are piped. ``NO_WINDOW_FLAGS``
is a no-op on other platforms.
"""
import os
import subprocess
import sys

NO_WINDOW_FLAGS = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0


def find_kicad_sibling_binary(name):
    """Look for `name` next to the Python interpreter running this process.

    When running inside KiCad's own embedded Python (macOS/Windows bundle
    Python alongside their other binaries), sys.executable resolves to a
    path that lives in the same install directory as kicad-cli - e.g.
    ".../KiCad.app/Contents/MacOS/" or ".../KiCad/<ver>/bin/". Deriving the
    directory this way finds kicad-cli regardless of KiCad's version or
    install location, unlike a hardcoded list of known install paths.
    On Linux, KiCad typically scripts with the system Python instead, so
    this lookup just won't find anything there - PATH/common-paths search
    is still needed as a fallback everywhere.
    """
    candidate = os.path.join(os.path.dirname(sys.executable), name)
    return candidate if os.path.exists(candidate) else None
