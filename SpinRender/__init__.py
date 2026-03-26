"""
SpinRender - KiCad Plugin for PCB Animation Rendering
Version: 0.95-beta
Author: Foo Hoang
License: MIT
"""

# DO NOT import heavy plugin modules at package import time.
# This breaks unit tests for individual modules (like core.theme) by
# pulling in unnecessary dependencies (wx, OpenGL). Instead, plugins
# should import their own dependencies explicitly. 

# KiCad plugin metadata
__version__ = "0.95-beta"
__author__ = "Foo Hoang"

import sys
from .spinrender_plugin import SpinRenderPlugin