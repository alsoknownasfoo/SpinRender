"""
SpinRender - KiCad Plugin for PCB Animation Rendering
Version: 0.7.0-beta
Author: Foo Hoang
License: GPLv3
"""

# DO NOT import heavy plugin modules at package import time.
# This breaks unit tests for individual modules (like core.theme) by
# pulling in unnecessary dependencies (wx, OpenGL). Instead, plugins
# should import their own dependencies explicitly. 

# KiCad plugin metadata
__version__ = "0.7.0-beta"
__author__ = "Foo Hoang"

import sys

# Package-name alias for PCM installs.
# KiCad's Plugin & Content Manager extracts this package into a directory named
# after the plugin identifier (e.g. "com_alsoknownasfoo_spinrender"), so KiCad
# imports it under that name rather than "SpinRender". The codebase uses absolute
# "from SpinRender.xxx" imports, so we register this package under the "SpinRender"
# name as well. setdefault keeps the manual install (already named "SpinRender")
# and the test suite working unchanged, while making PCM installs resolve to the
# exact same single module instance (no duplicate-namespace pitfalls).
sys.modules.setdefault("SpinRender", sys.modules[__name__])

from SpinRender.spinrender_plugin import SpinRenderPlugin