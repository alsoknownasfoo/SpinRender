"""
SpinRender - KiCad Plugin for PCB Animation Rendering
Version: 0.9.0-alpha
Author: Foo Hoang
License: MIT
"""

import sys
from .spinrender_plugin import SpinRenderPlugin

# REMOVE THIS LINE IN PRODUCTION - This is for development to prevent .pyc files from being generated in the plugin directory
sys.dont_write_bytecode = True 

# KiCad plugin metadata
__version__ = "0.9.0-alpha"
__author__ = "Foo Hoang"
