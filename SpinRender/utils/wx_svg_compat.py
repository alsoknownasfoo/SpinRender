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

Separately, at least one tested Ubuntu/aarch64 distro-packaged wxPython pairs
an older `wx/svg/__init__.py` with a newer compiled `_nanosvg` extension.
The older wrapper references several SVG enum constants (the shape-visible
flag, paint types, line join/cap styles) as bare module-level names, e.g.
`SVG_FLAGS_VISIBLE`, but the newer extension only exports them namespaced
under enum classes, e.g. `SVGflags.SVG_FLAGS_VISIBLE`. Every call into
`SVGimage.RenderToGC()` (used to draw every SVG icon in the app, including
the header logo) then raises `NameError` on whichever constant it reaches
first and falls back to a solid placeholder shape. We copy every member of
each known namespace back onto the module as a bare name so the existing
bytecode's global lookups succeed.
"""
import importlib.util
import logging
import os
import sys

logger = logging.getLogger("SpinRender")

_VENDOR_DIR = os.path.join(os.path.dirname(__file__), "..", "vendor", "wx_svg")

# Enum classes RenderToGC()/_makeBrush()/_makePen() reference as bare names
# in the mismatched older wx/svg/__init__.py (see module docstring).
_SVG_CONST_NAMESPACES = ("SVGflags", "SVGpaintType", "SVGlineJoin", "SVGlineCap", "SVGfillRule")


def _patch_missing_svg_flags(wx_svg):
    """Copy enum members from _SVG_CONST_NAMESPACES onto wx.svg as bare names."""
    patched = []
    for ns_name in _SVG_CONST_NAMESPACES:
        namespace = getattr(wx_svg, ns_name, None)
        if namespace is None:
            continue
        for member_name in dir(namespace):
            if not member_name.isupper() or hasattr(wx_svg, member_name):
                continue
            setattr(wx_svg, member_name, getattr(namespace, member_name))
            patched.append(member_name)
    if patched:
        logger.info("wx_svg_compat: patched missing wx.svg constants: %s", ", ".join(patched))


def ensure_wx_svg():
    """Import and return wx.svg, patching in the bundled _nanosvg extension
    if the host wxPython build is missing it."""
    try:
        import wx.svg
        _patch_missing_svg_flags(wx.svg)
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
    _patch_missing_svg_flags(wx.svg)
    return wx.svg
