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
from typing import Any, Optional

logger = logging.getLogger("SpinRender")

# Marker embedded in the working-copy filename so leftovers are recognizable.
_WORK_SUFFIX = ".spinrender-tmp"
# Marker for the pristine snapshot of the live in-memory board.
_SNAPSHOT_SUFFIX = ".spinrender-src"

_IS_WINDOWS = sys.platform.startswith("win")
_FILE_ATTRIBUTE_HIDDEN = 0x02
_FILE_ATTRIBUTE_NORMAL = 0x80


def _hide_path(path: str) -> None:
    """Set the Windows hidden attribute (no-op elsewhere; dotfile suffices)."""
    if not _IS_WINDOWS:
        return
    try:
        import ctypes
        if not ctypes.windll.kernel32.SetFileAttributesW(path, _FILE_ATTRIBUTE_HIDDEN):
            raise ctypes.WinError(ctypes.get_last_error())
    except Exception as e:
        # Non-fatal: the file still works, it just isn't hidden.
        logger.warning(f"BoardWorkspace: could not set hidden attribute: {e}")


def _unhide_path(path: str) -> None:
    """Clear the Windows hidden/read-only attributes before overwriting.

    Cloud-sync providers (e.g. OneDrive) periodically re-stamp synced
    files as hidden+read-only; with the read-only bit set, opening the
    existing working copy for write raises PermissionError, and
    pcbnew.SaveBoard silently returns False. Reset to normal before each
    overwrite so the previous run's hidden copy doesn't block the next one.
    """
    if not _IS_WINDOWS or not os.path.exists(path):
        return
    try:
        import ctypes
        if not ctypes.windll.kernel32.SetFileAttributesW(path, _FILE_ATTRIBUTE_NORMAL):
            raise ctypes.WinError(ctypes.get_last_error())
    except Exception as e:
        logger.warning(f"BoardWorkspace: could not clear attributes on {path}: {e}")


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
        # Pristine snapshot of the *live* in-memory board. The working copy is
        # refreshed from this snapshot (not the on-disk file) so the preview and
        # render reflect exactly what the user currently sees in the editor,
        # including unsaved edits. See capture_live_board().
        snap_name = f".{src.stem}{_SNAPSHOT_SUFFIX}{src.suffix}"
        self.snapshot_path = str(src.with_name(snap_name))
        self._paired_paths = [Path(self.board_path), Path(self.snapshot_path)]
        self.capture_live_board()
        self._copy_source_files()
        logger.debug(f"BoardWorkspace: working copy at {self.board_path}")

    def capture_live_board(self) -> bool:
        """Serialize the live in-memory board to the pristine snapshot.

        Captures exactly what the user currently sees in the PCB editor —
        including unsaved edits — rather than the last-saved file on disk.

        MUST be called on KiCad's main/UI thread: pcbnew is not thread-safe.
        Returns True when the live board was captured, False when it fell back
        to copying the on-disk file. The snapshot is always populated on return
        (or an OSError is raised).
        """
        if self._serialize_live_board(self.snapshot_path):
            logger.debug("BoardWorkspace: captured live in-memory board")
            return True
        # Fallback: copy the last-saved file so the snapshot is always present.
        try:
            self._unhide(self.snapshot_path)
            shutil.copy2(self.source_path, self.snapshot_path)
            self._hide(self.snapshot_path)
            logger.debug("BoardWorkspace: snapshot fell back to on-disk file")
        except OSError as e:
            logger.error(f"BoardWorkspace: snapshot fallback copy failed: {e}")
            raise
        return False

    def _serialize_live_board(self, dest: str) -> bool:
        """Write the live board to ``dest`` via pcbnew, undoing any side effects
        on the live board (filename / modified flag) so the user's editor
        session is untouched. Returns False on any failure (caller falls back)."""
        try:
            import pcbnew
        except Exception:
            return False
        try:
            board = pcbnew.GetBoard()
        except Exception as e:
            logger.warning(f"BoardWorkspace: pcbnew.GetBoard() failed: {e}")
            return False
        if board is None:
            return False
        # Only trust the live board if it's the project we were opened for; a
        # filename mismatch means GetBoard() isn't our source board.
        try:
            live_name = board.GetFileName()
        except Exception:
            live_name = ""
        if not live_name or os.path.normpath(live_name) != os.path.normpath(self.source_path):
            logger.debug("BoardWorkspace: live board filename mismatch; using on-disk copy")
            return False
        # SaveBoard can mutate the board's filename (and clear its modified flag)
        # on some KiCad versions. Capture and restore both so the user's next
        # Ctrl+S still targets their real file and the dirty indicator is intact.
        was_modified = None
        try:
            if hasattr(board, "IsModified"):
                was_modified = board.IsModified()
        except Exception:
            was_modified = None
        try:
            self._unhide(dest)
            pcbnew.SaveBoard(dest, board)
        except Exception as e:
            logger.warning(f"BoardWorkspace: pcbnew.SaveBoard failed; using on-disk copy: {e}")
            return False
        finally:
            try:
                if board.GetFileName() != live_name:
                    board.SetFileName(live_name)
            except Exception:
                pass
            try:
                if was_modified and hasattr(board, "SetModified"):
                    board.SetModified()
            except Exception:
                pass
        if not os.path.exists(dest) or os.path.getsize(dest) == 0:
            logger.warning("BoardWorkspace: SaveBoard produced no output; using on-disk copy")
            return False
        self._hide(dest)
        return True

    def reset(self) -> None:
        """Overwrite the working copy with a fresh copy of the live-board snapshot."""
        self._copy_source_files()
        logger.debug("BoardWorkspace: working copy reset to live-board snapshot")

    def prepare_for_render(
        self,
        hide_vias: bool = False,
        hide_components: bool = False,
        hide_test_points: bool = False,
        hide_testpoints: Optional[bool] = None,
    ) -> str:
        """Refresh the working copy and apply any render-only board transforms."""
        if hide_testpoints is not None:
            hide_test_points = hide_testpoints
        # Re-capture the live board first so renders reflect any edits made
        # while the plugin stayed open. Called on the main thread via
        # SpinRenderPanel.on_render -> _prepare_render_board_path.
        self.capture_live_board()
        self.reset()
        remove_user_drawings_from_board_file(self.board_path)
        if hide_vias:
            remove_vias_from_board_file(self.board_path)
        if hide_components:
            remove_components_from_board_file(self.board_path)
        if hide_test_points:
            remove_testpoints_from_board_file(self.board_path)
        return self.board_path

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
        # Board geometry comes from the live-board snapshot (capture_live_board);
        # fall back to the on-disk source if the snapshot is somehow missing.
        board_src = self.snapshot_path if os.path.exists(self.snapshot_path) else self.source_path
        self._unhide(str(board_copy))
        shutil.copy2(board_src, board_copy)
        self._hide(str(board_copy))

        src = Path(self.source_path)
        for suffix in ('.kicad_pro', '.kicad_prl'):
            source_file = src.with_suffix(suffix)
            target_file = board_copy.with_suffix(suffix)
            if source_file.exists():
                self._unhide(str(target_file))
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
        _hide_path(path or self.board_path)

    def _unhide(self, path: str) -> None:
        """Clear the Windows hidden/read-only attributes before overwriting."""
        _unhide_path(path)


def _is_via(track: Any, pcbnew_module: Any) -> bool:
    """Best-effort KiCad track classification across API versions."""
    via_type = getattr(pcbnew_module, 'PCB_VIA', None)
    if via_type is not None:
        try:
            if isinstance(track, via_type):
                return True
        except TypeError:
            pass

    for attr_name in ('GetClass', 'GetClassName', 'GetTypeDesc'):
        getter = getattr(track, attr_name, None)
        if callable(getter):
            value = getter()
            if value and 'VIA' in str(value).upper():
                return True

    return False


def _is_test_point_footprint(footprint: Any) -> bool:
    """Return True when a footprint reference is a ``T#`` designator (e.g. T1).

    Matches a leading ``T`` immediately followed by a digit, so ``T1``/``T2`` are
    stripped while multi-letter prefixes such as ``TP1`` (test-point pads) are
    left intact.
    """
    ref_getter = getattr(footprint, 'GetReference', None)
    if not callable(ref_getter):
        return False

    reference = str(ref_getter() or '').strip().upper()
    return len(reference) >= 2 and reference[0] == 'T' and reference[1].isdigit()


def _clear_footprint_models(footprint: Any) -> bool:
    """Best-effort removal of a footprint's 3D models across KiCad API variants."""
    for getter_name in ('Models', 'GetModels'):
        getter = getattr(footprint, getter_name, None)
        if not callable(getter):
            continue

        models = getter()
        if models is None:
            continue

        for clearer_name in ('clear', 'Clear'):
            clearer = getattr(models, clearer_name, None)
            if callable(clearer):
                clearer()
                return True

        if isinstance(models, list):
            del models[:]
            return True

    return False


def _coerce_board(board: Any, pcbnew_module: Any) -> Any:
    """Best-effort conversion of raw KiCad SWIG board pointers to BOARD objects."""
    for getter_name in ('GetTracks', 'Tracks', 'GetFootprints', 'Footprints'):
        if callable(getattr(board, getter_name, None)):
            return board

    for caster_name in ('Cast_to_BOARD', 'BOARD'):
        caster = getattr(pcbnew_module, caster_name, None)
        if not callable(caster):
            continue

        try:
            typed_board = caster(board)
        except Exception:
            continue

        for getter_name in ('GetTracks', 'Tracks', 'GetFootprints', 'Footprints'):
            if callable(getattr(typed_board, getter_name, None)):
                return typed_board

    return board


def _get_board_items(board: Any, *getter_names: str) -> list[Any]:
    """Return board items across KiCad API variants such as Tracks/GetTracks."""
    for getter_name in getter_names:
        getter = getattr(board, getter_name, None)
        if callable(getter):
            items = getter()
            if items is not None:
                return list(items)

    getter_list = ', '.join(getter_names)
    raise AttributeError(f"Board object does not expose any of: {getter_list}")


def _remove_board_item(board: Any, item: Any) -> None:
    """Remove an item from its container (board or footprint) across API variants."""
    for remover_name in ('Delete', 'Remove', 'RemoveNative'):
        remover = getattr(board, remover_name, None)
        if callable(remover):
            remover(item)
            return

    raise AttributeError(f"Container does not support removing items of type {type(item).__name__}")


def _get_footprints(board: Any) -> list[Any]:
    """Return the board's footprints across API variants ([] when unavailable)."""
    for getter_name in ('GetFootprints', 'Footprints'):
        getter = getattr(board, getter_name, None)
        if callable(getter):
            items = getter()
            if items is not None:
                return list(items)
    return []


def _get_footprint_graphics(footprint: Any) -> list[Any]:
    """Return a footprint's graphic items across API variants ([] when unavailable)."""
    for getter_name in ('GraphicalItems', 'GetGraphicalItems'):
        getter = getattr(footprint, getter_name, None)
        if callable(getter):
            items = getter()
            if items is not None:
                return list(items)
    return []


def _is_user_drawings_item(item: Any, board: Any, pcbnew_module: Any) -> bool:
    """Return True when an item belongs to the User.Drawings layer."""
    layer_name_getter = getattr(item, 'GetLayerName', None)
    if callable(layer_name_getter):
        layer_name = layer_name_getter()
        if str(layer_name or '').strip() == 'User.Drawings':
            return True

    layer_getter = getattr(item, 'GetLayer', None)
    if callable(layer_getter):
        layer = layer_getter()

        board_layer_name = getattr(board, 'GetLayerName', None)
        if callable(board_layer_name):
            layer_name = board_layer_name(layer)
            if str(layer_name or '').strip() == 'User.Drawings':
                return True

        module_layer_name = getattr(pcbnew_module, 'LayerName', None)
        if callable(module_layer_name):
            layer_name = module_layer_name(layer)
            if str(layer_name or '').strip() == 'User.Drawings':
                return True

    return False


def apply_render_filters_to_board_file(
    board_path: str,
    *,
    hide_vias: bool = False,
    hide_components: bool = False,
    hide_test_points: bool = False,
) -> None:
    """Load a board through KiCad's Python API, apply render-only filters, and save it."""
    import pcbnew

    try:
        board = pcbnew.LoadBoard(board_path)
    except Exception as exc:
        logger.error(f"BoardWorkspace: pcbnew.LoadBoard failed for {board_path}: {exc}", exc_info=True)
        raise RuntimeError(f"Unable to load board for via stripping: {board_path}") from exc

    if board is None:
        raise RuntimeError(f"Unable to load board for via stripping: {board_path}")

    board = _coerce_board(board, pcbnew)

    removed_vias = 0
    if hide_vias:
        for track in _get_board_items(board, 'GetTracks', 'Tracks'):
            if _is_via(track, pcbnew):
                _remove_board_item(board, track)
                removed_vias += 1

    cleared_models = 0
    removed_footprints = 0
    if hide_components or hide_test_points:
        for footprint in _get_board_items(board, 'GetFootprints', 'Footprints'):
            if hide_components and _clear_footprint_models(footprint):
                cleared_models += 1
            if hide_test_points and _is_test_point_footprint(footprint):
                _remove_board_item(board, footprint)
                removed_footprints += 1

    _unhide_path(board_path)
    try:
        save_result = pcbnew.SaveBoard(board_path, board)
    except Exception as exc:
        logger.error(f"BoardWorkspace: pcbnew.SaveBoard failed for {board_path}: {exc}", exc_info=True)
        raise RuntimeError(f"Unable to save board after via stripping: {board_path}") from exc
    finally:
        _hide_path(board_path)

    if save_result is False:
        raise RuntimeError(f"Unable to save board after via stripping: {board_path}")

    logger.debug(
        "BoardWorkspace: applied render filters to %s (removed %s vias, cleared %s footprint model sets, removed %s footprints)",
        board_path,
        removed_vias,
        cleared_models,
        removed_footprints,
    )


def remove_vias_from_board_file(board_path: str) -> None:
    """Compatibility wrapper for via-only filtering."""
    apply_render_filters_to_board_file(board_path, hide_vias=True)


def remove_user_drawings_from_board_file(board_path: str) -> None:
    """Remove all User.Drawings items from the disposable render board.

    KiCad's 3D viewer renders the User.Drawings layer, so leftover documentation
    graphics show up on the rendered board. Both *board-level* drawings and the
    graphics owned by each *footprint* can live on User.Drawings, so we strip
    from both: ``board.GetDrawings()`` and every ``footprint.GraphicalItems()``.
    """
    import pcbnew

    try:
        board = pcbnew.LoadBoard(board_path)
    except Exception as exc:
        logger.error(f"BoardWorkspace: pcbnew.LoadBoard failed for {board_path}: {exc}", exc_info=True)
        raise RuntimeError(f"Unable to load board for drawing stripping: {board_path}") from exc

    if board is None:
        raise RuntimeError(f"Unable to load board for drawing stripping: {board_path}")

    board = _coerce_board(board, pcbnew)

    removed_drawings = 0
    for drawing in _get_board_items(board, 'GetDrawings', 'Drawings'):
        if _is_user_drawings_item(drawing, board, pcbnew):
            _remove_board_item(board, drawing)
            removed_drawings += 1

    removed_footprint_drawings = 0
    for footprint in _get_footprints(board):
        for item in _get_footprint_graphics(footprint):
            if _is_user_drawings_item(item, board, pcbnew):
                _remove_board_item(footprint, item)
                removed_footprint_drawings += 1

    _unhide_path(board_path)
    try:
        save_result = pcbnew.SaveBoard(board_path, board)
    except Exception as exc:
        logger.error(f"BoardWorkspace: pcbnew.SaveBoard failed for {board_path}: {exc}", exc_info=True)
        raise RuntimeError(f"Unable to save board after drawing stripping: {board_path}") from exc
    finally:
        _hide_path(board_path)

    if save_result is False:
        raise RuntimeError(f"Unable to save board after drawing stripping: {board_path}")

    logger.debug(
        "BoardWorkspace: removed %s board + %s footprint User.Drawings items from %s",
        removed_drawings,
        removed_footprint_drawings,
        board_path,
    )


def remove_components_from_board_file(board_path: str) -> None:
    """Compatibility wrapper for removing footprint 3D models only."""
    apply_render_filters_to_board_file(board_path, hide_components=True)


def remove_test_points_from_board_file(board_path: str) -> None:
    """Compatibility wrapper for TP*-reference filtering."""
    apply_render_filters_to_board_file(board_path, hide_test_points=True)


def remove_testpoints_from_board_file(board_path: str) -> None:
    """Backward-compatible alias for TP*-reference filtering."""
    remove_test_points_from_board_file(board_path)
