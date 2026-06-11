"""
Compatibility shim for wx.svg.

Some KiCad 10 Windows builds ship a wxPython whose wx/svg package is missing
the compiled `_nanosvg` extension (only the .pyx/.pxd sources are present),
making `import wx.svg` raise ModuleNotFoundError. wx.svg.SVGimage is built on
SVGimageBase from that extension, so the whole module is unusable without it.

_nanosvg only depends on the Python C API and the VC runtime (no direct
wxWidgets DLL linkage), so the matching upstream wxPython wheel's build of the
extension can be loaded in its place. This module bundles that build for the
affected interpreter (KiCad 10 / CPython 3.11 / win_amd64) and registers it in
sys.modules before importing wx.svg, so the package's own
`from ._nanosvg import *` resolves to it.
"""
import importlib.util
import logging
import os
import sys

logger = logging.getLogger("SpinRender")

_VENDOR_DIR = os.path.join(os.path.dirname(__file__), "..", "vendor", "wx_svg")


def ensure_wx_svg():
    """Import and return wx.svg, patching in the bundled _nanosvg extension
    if the host wxPython build is missing it."""
    try:
        import wx.svg
        return wx.svg
    except ModuleNotFoundError as e:
        if e.name != "wx.svg._nanosvg":
            raise

    tag = f"cp{sys.version_info.major}{sys.version_info.minor}-win_amd64"
    pyd_path = os.path.normpath(os.path.join(_VENDOR_DIR, f"_nanosvg.{tag}.pyd"))
    if os.name != "nt" or not os.path.exists(pyd_path):
        raise

    spec = importlib.util.spec_from_file_location("wx.svg._nanosvg", pyd_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["wx.svg._nanosvg"] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        del sys.modules["wx.svg._nanosvg"]
        raise

    import wx.svg
    logger.info("Loaded bundled wx.svg._nanosvg (%s) - host wxPython build was missing it", tag)
    return wx.svg
