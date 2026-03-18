"""
SpinRender KiCad Plugin Package
"""
import sys

# Disable bytecode generation globally for this plugin session
# This prevents KiCad from loading stale __pycache__ files during development
sys.dont_write_bytecode = True
