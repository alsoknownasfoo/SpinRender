"""Install bundled fonts into the user's fontconfig directory on Linux.

wx.Font.AddPrivateFont() - used to register bundled fonts in-process on
other platforms - segfaults deep in libpangoft2 the instant a privately
loaded font's text metrics are computed, on at least one tested Linux
build (Ubuntu/aarch64). This isn't specific to one font: it reproduced
with both the MDI icon font and Oswald. Installing into
~/.local/share/fonts instead makes these ordinary, fontconfig-registered
fonts - the same category macOS's Font Book / Windows' font installer
produce - which uses the normal system font resolution path every desktop
app relies on, sidestepping AddPrivateFont entirely.

A font copied here won't necessarily be visible to the *current* process
(fontconfig's font list is typically built once at startup), so this is
best-effort for next launch - callers should still tolerate the font
being unavailable in the current session and let wx fall back silently,
same as any other missing font name.
"""
import logging
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger("SpinRender")

_INSTALLED = False

FONT_FILES = [
    "JetBrainsMono-VariableFont_wght.ttf",
    "materialdesignicons-webfont.ttf",
    "Oswald-VariableFont_wght.ttf",
]


def install_linux_fonts(plugin_dir=None):
    """Copy bundled fonts to ~/.local/share/fonts/SpinRender and refresh fontconfig.

    Idempotent per-process; safe to call from multiple modules.
    """
    global _INSTALLED
    if _INSTALLED:
        return

    if plugin_dir is None:
        plugin_dir = Path(__file__).resolve().parent.parent
    fonts_dir = Path(plugin_dir) / "resources" / "fonts"

    dest_dir = Path.home() / ".local" / "share" / "fonts" / "SpinRender"
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.warning(f"install_linux_fonts: could not create {dest_dir}: {e}")
        return

    _INSTALLED = True

    copied_any = False
    for filename in FONT_FILES:
        src = fonts_dir / filename
        if not src.exists():
            logger.warning(f"install_linux_fonts: font file not found: {src}")
            continue
        dest = dest_dir / filename
        try:
            if not dest.exists() or dest.stat().st_size != src.stat().st_size:
                shutil.copy2(src, dest)
                copied_any = True
        except Exception as e:
            logger.warning(f"install_linux_fonts: failed to copy {filename}: {e}")

    if not copied_any:
        return

    fc_cache = shutil.which("fc-cache")
    if not fc_cache:
        return
    try:
        result = subprocess.run(
            [fc_cache, "-f", str(dest_dir)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            text=True,
        )
        if result.returncode == 0:
            logger.info("install_linux_fonts: installed bundled fonts to ~/.local/share/fonts/SpinRender")
        else:
            combined = ((result.stdout or "") + (result.stderr or "")).strip()
            logger.warning(f"install_linux_fonts: fc-cache failed (exit {result.returncode}): {combined}")
    except Exception as e:
        logger.warning(f"install_linux_fonts: fc-cache failed: {e}")
