"""Disposable working copy of the board's .kicad_pcb.

SpinRender renders from (and may edit) a copy of the board rather than the
original file, so board edits never touch the user's source. The copy is made
as a sibling in the *same directory* as the original on purpose: KiCad resolves
``${KIPRJMOD}`` and relative 3D-model / footprint references against the board
file's directory, so a same-directory copy renders identically to the original.
A system-temp copy would silently break boards that reference project-local 3D
models.

The working copy is hidden so it doesn't clutter the user's project folder:
a leading-dot filename on every platform (which hides it on Linux/macOS), plus
the hidden file attribute on Windows (where the leading dot alone isn't enough).
"""
import logging
import os
import shutil
import sys
from pathlib import Path

logger = logging.getLogger("SpinRender")

# Marker embedded in the working-copy filename so leftovers are recognizable.
_WORK_SUFFIX = ".spinrender-tmp"

_IS_WINDOWS = sys.platform.startswith("win")
_FILE_ATTRIBUTE_HIDDEN = 0x02


class BoardWorkspace:
    """Maintains a disposable, hidden working copy of a board's .kicad_pcb file."""

    def __init__(self, source_path: str):
        self.source_path = source_path
        src = Path(source_path)
        # Sibling in the same directory, distinct stem so we never clobber the
        # original. Same directory keeps KIPRJMOD / relative model paths valid.
        # Leading dot hides it on Linux/macOS (and is harmless on Windows, where
        # _hide() sets the hidden attribute).
        name = f".{src.stem}{_WORK_SUFFIX}{src.suffix}"
        self.board_path = str(src.with_name(name))
        shutil.copy2(source_path, self.board_path)
        self._hide()
        logger.debug(f"BoardWorkspace: working copy at {self.board_path}")

    def reset(self) -> None:
        """Overwrite the working copy with a fresh copy of the original."""
        shutil.copy2(self.source_path, self.board_path)
        self._hide()
        logger.debug("BoardWorkspace: working copy reset to original")

    def cleanup(self) -> None:
        """Remove the working copy. Safe to call multiple times."""
        try:
            if self.board_path and os.path.exists(self.board_path):
                os.remove(self.board_path)
                logger.debug(f"BoardWorkspace: removed {self.board_path}")
        except OSError as e:
            logger.warning(f"BoardWorkspace: failed to remove {self.board_path}: {e}")

    def _hide(self) -> None:
        """Set the Windows hidden attribute (no-op elsewhere; dotfile suffices)."""
        if not _IS_WINDOWS:
            return
        try:
            import ctypes
            if not ctypes.windll.kernel32.SetFileAttributesW(self.board_path, _FILE_ATTRIBUTE_HIDDEN):
                raise ctypes.WinError(ctypes.get_last_error())
        except Exception as e:
            # Non-fatal: the copy still works, it just isn't hidden.
            logger.warning(f"BoardWorkspace: could not set hidden attribute: {e}")
