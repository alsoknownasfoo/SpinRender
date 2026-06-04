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
        self._paired_paths = [Path(self.board_path)]
        self._copy_source_files()
        logger.debug(f"BoardWorkspace: working copy at {self.board_path}")

    def reset(self) -> None:
        """Overwrite the working copy with a fresh copy of the original."""
        self._copy_source_files()
        logger.debug("BoardWorkspace: working copy reset to original")

    def cleanup(self) -> None:
        """Remove the working copy. Safe to call multiple times."""
        for path in self._paired_paths:
            try:
                if path.exists():
                    os.remove(path)
                    logger.debug(f"BoardWorkspace: removed {path}")
            except OSError as e:
                logger.warning(f"BoardWorkspace: failed to remove {path}: {e}")

    def _copy_source_files(self) -> None:
        """Refresh the board copy and any same-stem project files KiCad expects."""
        board_copy = Path(self.board_path)
        shutil.copy2(self.source_path, board_copy)
        self._hide(str(board_copy))

        src = Path(self.source_path)
        for suffix in ('.kicad_pro', '.kicad_prl'):
            source_file = src.with_suffix(suffix)
            target_file = board_copy.with_suffix(suffix)
            if source_file.exists():
                shutil.copy2(source_file, target_file)
                self._hide(str(target_file))
                if target_file not in self._paired_paths:
                    self._paired_paths.append(target_file)
            elif target_file in self._paired_paths:
                self._paired_paths.remove(target_file)
                if target_file.exists():
                    os.remove(target_file)

    def _hide(self, path: str = None) -> None:
        """Set the Windows hidden attribute (no-op elsewhere; dotfile suffices)."""
        if not _IS_WINDOWS:
            return
        target_path = path or self.board_path
        try:
            import ctypes
            if not ctypes.windll.kernel32.SetFileAttributesW(target_path, _FILE_ATTRIBUTE_HIDDEN):
                raise ctypes.WinError(ctypes.get_last_error())
        except Exception as e:
            # Non-fatal: the copy still works, it just isn't hidden.
            logger.warning(f"BoardWorkspace: could not set hidden attribute: {e}")
