"""Tests for disposable board working copies."""

import sys
from pathlib import Path
from types import SimpleNamespace

from SpinRender.core import board_workspace
from SpinRender.core.board_workspace import BoardWorkspace


def test_board_workspace_copies_matching_project_file(tmp_path):
    """A temp board copy should keep a matching project stem for KiCad lookups."""
    board_path = tmp_path / "demo.kicad_pcb"
    project_path = tmp_path / "demo.kicad_pro"

    board_path.write_text("(kicad_pcb)", encoding="utf-8")
    project_path.write_text("{\"board\": \"demo\"}", encoding="utf-8")

    workspace = BoardWorkspace(str(board_path))

    work_board = Path(workspace.board_path)
    work_project = work_board.with_suffix(".kicad_pro")

    assert work_board.exists()
    assert work_project.exists()
    assert work_project.read_text(encoding="utf-8") == project_path.read_text(encoding="utf-8")

    workspace.cleanup()

    assert not work_board.exists()
    assert not work_project.exists()


def test_remove_vias_from_board_file_saves_board_without_vias(monkeypatch):
    """Via stripping should remove only vias from the loaded KiCad board."""

    class FakeVia:
        pass

    class FakeTrack:
        pass

    class FakeBoard:
        def __init__(self):
            self.items = [FakeTrack(), FakeVia(), FakeTrack(), FakeVia()]

        def GetTracks(self):
            return list(self.items)

        def Remove(self, item):
            self.items.remove(item)

    fake_board = FakeBoard()
    save_calls = []
    fake_pcbnew = SimpleNamespace(
        PCB_VIA=FakeVia,
        LoadBoard=lambda path: fake_board,
        SaveBoard=lambda path, board: save_calls.append((path, board)),
    )

    monkeypatch.setitem(sys.modules, 'pcbnew', fake_pcbnew)

    board_workspace.remove_vias_from_board_file('/tmp/demo.kicad_pcb')

    assert [type(item) for item in fake_board.items] == [FakeTrack, FakeTrack]
    assert save_calls == [('/tmp/demo.kicad_pcb', fake_board)]


def test_remove_components_from_board_file_saves_board_without_footprints(monkeypatch):
    """Component stripping should remove 3D models while keeping footprints."""

    class FakeFootprint:
        def __init__(self, reference, models):
            self.reference = reference
            self.models = list(models)

        def GetReference(self):
            return self.reference

        def Models(self):
            return self.models

    class FakeBoard:
        def __init__(self):
            self.footprints = [
                FakeFootprint('U1', ['body.step']),
                FakeFootprint('R3', ['resistor.step', 'resistor.wrl']),
            ]

        def GetFootprints(self):
            return list(self.footprints)

        def Remove(self, item):
            self.footprints.remove(item)

    fake_board = FakeBoard()
    save_calls = []
    fake_pcbnew = SimpleNamespace(
        LoadBoard=lambda path: fake_board,
        SaveBoard=lambda path, board: save_calls.append((path, board)),
    )

    monkeypatch.setitem(sys.modules, 'pcbnew', fake_pcbnew)

    board_workspace.remove_components_from_board_file('/tmp/demo.kicad_pcb')

    assert [footprint.GetReference() for footprint in fake_board.footprints] == ['U1', 'R3']
    assert [footprint.Models() for footprint in fake_board.footprints] == [[], []]
    assert save_calls == [('/tmp/demo.kicad_pcb', fake_board)]


def test_remove_testpoints_from_board_file_saves_board_without_t_refs(monkeypatch):
    """Test-point stripping should remove only T# refs, leaving TP# pads intact."""

    class FakeFootprint:
        def __init__(self, reference):
            self.reference = reference

        def GetReference(self):
            return self.reference

    class FakeBoard:
        def __init__(self):
            self.footprints = [FakeFootprint('U1'), FakeFootprint('T1'), FakeFootprint('TP1'), FakeFootprint('J2')]

        def GetFootprints(self):
            return list(self.footprints)

        def Remove(self, item):
            self.footprints.remove(item)

    fake_board = FakeBoard()
    save_calls = []
    fake_pcbnew = SimpleNamespace(
        LoadBoard=lambda path: fake_board,
        SaveBoard=lambda path, board: save_calls.append((path, board)),
    )

    monkeypatch.setitem(sys.modules, 'pcbnew', fake_pcbnew)

    board_workspace.remove_testpoints_from_board_file('/tmp/demo.kicad_pcb')

    assert [footprint.GetReference() for footprint in fake_board.footprints] == ['U1', 'TP1', 'J2']
    assert save_calls == [('/tmp/demo.kicad_pcb', fake_board)]


def test_remove_user_drawings_from_board_file_strips_only_user_drawings(monkeypatch):
    """Render prep should strip User.Drawings from the board and from footprints."""

    class FakeDrawing:
        def __init__(self, layer_name):
            self.layer_name = layer_name

        def GetLayerName(self):
            return self.layer_name

    class FakeFootprint:
        def __init__(self, graphics):
            self.graphics = list(graphics)

        def GraphicalItems(self):
            return list(self.graphics)

        def Remove(self, item):
            self.graphics.remove(item)

    class FakeBoard:
        def __init__(self):
            self.drawings = [FakeDrawing('User.Drawings'), FakeDrawing('Edge.Cuts')]
            self.footprint = FakeFootprint([FakeDrawing('User.Drawings'), FakeDrawing('F.SilkS')])

        def GetDrawings(self):
            return list(self.drawings)

        def GetFootprints(self):
            return [self.footprint]

        def Delete(self, item):
            self.drawings.remove(item)

    fake_board = FakeBoard()
    save_calls = []
    fake_pcbnew = SimpleNamespace(
        LoadBoard=lambda path: fake_board,
        SaveBoard=lambda path, board: save_calls.append((path, board)),
    )

    monkeypatch.setitem(sys.modules, 'pcbnew', fake_pcbnew)

    board_workspace.remove_user_drawings_from_board_file('/tmp/demo.kicad_pcb')

    assert [drawing.GetLayerName() for drawing in fake_board.drawings] == ['Edge.Cuts']
    assert [g.GetLayerName() for g in fake_board.footprint.graphics] == ['F.SilkS']
    assert save_calls == [('/tmp/demo.kicad_pcb', fake_board)]


def test_board_workspace_prepare_for_render_resets_copy_before_hiding_vias(tmp_path, monkeypatch):
    """Each render should start from a fresh copy before optional via stripping."""
    board_path = tmp_path / 'demo.kicad_pcb'
    board_path.write_text('(kicad_pcb)', encoding='utf-8')

    workspace = BoardWorkspace(str(board_path))
    calls = []

    monkeypatch.setattr(workspace, 'reset', lambda: calls.append('reset'))
    monkeypatch.setattr(board_workspace, 'remove_user_drawings_from_board_file', lambda path: calls.append(('remove_user_drawings', path)))
    monkeypatch.setattr(board_workspace, 'remove_vias_from_board_file', lambda path: calls.append(('hide_vias', path)))

    prepared_path = workspace.prepare_for_render(hide_vias=True)

    assert prepared_path == workspace.board_path
    assert calls == ['reset', ('remove_user_drawings', workspace.board_path), ('hide_vias', workspace.board_path)]

    workspace.cleanup()


def test_apply_render_filters_removes_vias_and_t_footprints(monkeypatch):
    """Render filters should remove vias, strip models, and remove only T# footprints."""

    class FakeVia:
        pass

    class FakeTrack:
        pass

    class FakeFootprint:
        def __init__(self, ref, models):
            self.ref = ref
            self.models = list(models)

        def GetReference(self):
            return self.ref

        def Models(self):
            return self.models

    class FakeBoard:
        def __init__(self):
            self.items = [
                FakeTrack(),
                FakeVia(),
                FakeFootprint('U1', ['u1.step']),
                FakeFootprint('T3', ['t.step']),
            ]

        def GetTracks(self):
            return [item for item in self.items if isinstance(item, (FakeTrack, FakeVia))]

        def GetFootprints(self):
            return [item for item in self.items if isinstance(item, FakeFootprint)]

        def Remove(self, item):
            self.items.remove(item)

    fake_board = FakeBoard()
    save_calls = []
    fake_pcbnew = SimpleNamespace(
        PCB_VIA=FakeVia,
        LoadBoard=lambda path: fake_board,
        SaveBoard=lambda path, board: save_calls.append((path, board)),
    )

    monkeypatch.setitem(sys.modules, 'pcbnew', fake_pcbnew)

    board_workspace.apply_render_filters_to_board_file(
        '/tmp/demo.kicad_pcb',
        hide_vias=True,
        hide_components=True,
        hide_test_points=True,
    )

    assert [type(item).__name__ for item in fake_board.items] == ['FakeTrack', 'FakeFootprint']
    assert fake_board.items[1].GetReference() == 'U1'
    assert fake_board.items[1].Models() == []
    assert save_calls == [('/tmp/demo.kicad_pcb', fake_board)]


def test_apply_render_filters_supports_tracks_and_footprints_api_variants(monkeypatch):
    """Render filters should work with KiCad boards exposing Tracks/Footprints methods."""

    class FakeVia:
        pass

    class FakeTrack:
        pass

    class FakeFootprint:
        def __init__(self, ref, models):
            self.ref = ref
            self.models = list(models)

        def GetReference(self):
            return self.ref

        def Models(self):
            return self.models

    class FakeBoard:
        def __init__(self):
            self.items = [
                FakeTrack(),
                FakeVia(),
                FakeFootprint('U1', ['u1.step']),
                FakeFootprint('T1', ['t.step']),
            ]

        def Tracks(self):
            return [item for item in self.items if isinstance(item, (FakeTrack, FakeVia))]

        def Footprints(self):
            return [item for item in self.items if isinstance(item, FakeFootprint)]

        def Remove(self, item):
            self.items.remove(item)

    fake_board = FakeBoard()
    save_calls = []
    fake_pcbnew = SimpleNamespace(
        PCB_VIA=FakeVia,
        LoadBoard=lambda path: fake_board,
        SaveBoard=lambda path, board: save_calls.append((path, board)),
    )

    monkeypatch.setitem(sys.modules, 'pcbnew', fake_pcbnew)

    board_workspace.apply_render_filters_to_board_file(
        '/tmp/demo.kicad_pcb',
        hide_vias=True,
        hide_components=True,
        hide_test_points=True,
    )

    assert [type(item).__name__ for item in fake_board.items] == ['FakeTrack', 'FakeFootprint']
    assert fake_board.items[1].GetReference() == 'U1'
    assert fake_board.items[1].Models() == []
    assert save_calls == [('/tmp/demo.kicad_pcb', fake_board)]


def test_apply_render_filters_casts_raw_loaded_board_when_needed(monkeypatch):
    """Render filters should cast raw loaded boards before reading tracks and footprints."""

    class FakeVia:
        pass

    class FakeTrack:
        pass

    class FakeFootprint:
        def __init__(self, ref, models):
            self.ref = ref
            self.models = list(models)

        def GetReference(self):
            return self.ref

        def Models(self):
            return self.models

    class RawBoard:
        def Remove(self, item):
            raise AssertionError('raw board should be cast before mutation')

    class TypedBoard:
        def __init__(self):
            self.items = [
                FakeTrack(),
                FakeVia(),
                FakeFootprint('U1', ['u1.step']),
                FakeFootprint('T1', ['t.step']),
            ]

        def GetTracks(self):
            return [item for item in self.items if isinstance(item, (FakeTrack, FakeVia))]

        def GetFootprints(self):
            return [item for item in self.items if isinstance(item, FakeFootprint)]

        def Remove(self, item):
            self.items.remove(item)

    raw_board = RawBoard()
    typed_board = TypedBoard()
    save_calls = []
    fake_pcbnew = SimpleNamespace(
        PCB_VIA=FakeVia,
        LoadBoard=lambda path: raw_board,
        Cast_to_BOARD=lambda board: typed_board,
        SaveBoard=lambda path, board: save_calls.append((path, board)),
    )

    monkeypatch.setitem(sys.modules, 'pcbnew', fake_pcbnew)

    board_workspace.apply_render_filters_to_board_file(
        '/tmp/demo.kicad_pcb',
        hide_vias=True,
        hide_components=True,
        hide_test_points=True,
    )

    assert [type(item).__name__ for item in typed_board.items] == ['FakeTrack', 'FakeFootprint']
    assert typed_board.items[1].GetReference() == 'U1'
    assert typed_board.items[1].Models() == []
    assert save_calls == [('/tmp/demo.kicad_pcb', typed_board)]


def test_board_workspace_prepare_for_render_applies_all_selected_filters(tmp_path, monkeypatch):
    """Each selected render option should transform the fresh working copy in order."""
    board_path = tmp_path / 'demo.kicad_pcb'
    board_path.write_text('(kicad_pcb)', encoding='utf-8')

    workspace = BoardWorkspace(str(board_path))
    calls = []

    monkeypatch.setattr(workspace, 'reset', lambda: calls.append('reset'))
    monkeypatch.setattr(board_workspace, 'remove_user_drawings_from_board_file', lambda path: calls.append(('remove_user_drawings', path)))
    monkeypatch.setattr(board_workspace, 'remove_vias_from_board_file', lambda path: calls.append(('vias', path)))
    monkeypatch.setattr(board_workspace, 'remove_components_from_board_file', lambda path: calls.append(('components', path)))
    monkeypatch.setattr(board_workspace, 'remove_testpoints_from_board_file', lambda path: calls.append(('testpoints', path)))

    prepared_path = workspace.prepare_for_render(hide_vias=True, hide_components=True, hide_testpoints=True)

    assert prepared_path == workspace.board_path
    assert calls == [
        'reset',
        ('remove_user_drawings', workspace.board_path),
        ('vias', workspace.board_path),
        ('components', workspace.board_path),
        ('testpoints', workspace.board_path),
    ]

    workspace.cleanup()


class _FakeBoard:
    """Minimal stand-in for a pcbnew BOARD with mutable filename/modified state."""

    def __init__(self, filename, modified=True):
        self._filename = filename
        self._modified = modified

    def GetFileName(self):
        return self._filename

    def SetFileName(self, name):
        self._filename = name

    def IsModified(self):
        return self._modified

    def SetModified(self):
        self._modified = True


def _install_fake_pcbnew(monkeypatch, board, save_log):
    """Register a fake ``pcbnew`` module so ``import pcbnew`` resolves to it."""

    def save_board(dest, b):
        # Mimic KiCad's documented side effect of repointing the board's
        # filename, and write content so the snapshot is non-empty.
        b.SetFileName(dest)
        save_log.append((dest, b))
        with open(dest, 'w', encoding='utf-8') as f:
            f.write('(kicad_pcb (live))')

    fake = SimpleNamespace(GetBoard=lambda: board, SaveBoard=save_board)
    monkeypatch.setitem(sys.modules, 'pcbnew', fake)
    return fake


def test_capture_live_board_serializes_in_memory_board(tmp_path, monkeypatch):
    """The snapshot should come from the live board, not the stale on-disk file."""
    board_path = tmp_path / 'demo.kicad_pcb'
    board_path.write_text('(kicad_pcb (saved))', encoding='utf-8')

    board = _FakeBoard(str(board_path), modified=True)
    save_log = []
    _install_fake_pcbnew(monkeypatch, board, save_log)

    workspace = BoardWorkspace(str(board_path))

    # The working copy carries the live content, not the saved file.
    assert Path(workspace.board_path).read_text(encoding='utf-8') == '(kicad_pcb (live))'
    assert save_log  # SaveBoard was used
    # The live board's filename + modified flag are restored (editor untouched).
    assert board.GetFileName() == str(board_path)
    assert board.IsModified() is True

    workspace.cleanup()


def test_capture_live_board_deletes_sibling_project_saveboard_invents(tmp_path, monkeypatch):
    """SaveBoard invents a full .kicad_pro/.kicad_prl next to a project-less
    snapshot path (confirmed against real pcbnew); left in place, that's a
    second real, loadable KiCad project a running session can pick up as
    "current" (issue #3). It must not survive capture_live_board()."""
    board_path = tmp_path / 'demo.kicad_pcb'
    board_path.write_text('(kicad_pcb (saved))', encoding='utf-8')

    board = _FakeBoard(str(board_path), modified=True)
    save_log = []

    def save_board(dest, b):
        b.SetFileName(dest)
        save_log.append((dest, b))
        with open(dest, 'w', encoding='utf-8') as f:
            f.write('(kicad_pcb (live))')
        # Mimic pcbnew.SaveBoard's real, unrequested side effect.
        for suffix in ('.kicad_pro', '.kicad_prl'):
            Path(dest).with_suffix(suffix).write_text('{}', encoding='utf-8')

    fake = SimpleNamespace(GetBoard=lambda: board, SaveBoard=save_board)
    monkeypatch.setitem(sys.modules, 'pcbnew', fake)

    workspace = BoardWorkspace(str(board_path))

    snapshot_pro = Path(workspace.snapshot_path).with_suffix('.kicad_pro')
    snapshot_prl = Path(workspace.snapshot_path).with_suffix('.kicad_prl')
    assert not snapshot_pro.exists()
    assert not snapshot_prl.exists()
    assert save_log  # SaveBoard was used

    workspace.cleanup()


def test_cleanup_removes_kicad_lock_files_next_to_tracked_paths(tmp_path):
    """cleanup() must also remove '~<name>.lck' KiCad drops when it opens one
    of our tracked project files (confirmed real, orphaned examples found on
    disk: '~.default.spinrender-tmp.kicad_pro.lck'). Deleting the project out
    from under an existing lock without going through KiCad's own close path
    is exactly how these get orphaned — cleanup() must take the lock with it."""
    board_path = tmp_path / 'demo.kicad_pcb'
    project_path = tmp_path / 'demo.kicad_pro'
    board_path.write_text('(kicad_pcb)', encoding='utf-8')
    project_path.write_text('{"board": "demo"}', encoding='utf-8')

    workspace = BoardWorkspace(str(board_path))

    work_project = Path(workspace.board_path).with_suffix('.kicad_pro')
    lock_file = work_project.with_name(f"~{work_project.name}.lck")
    lock_file.write_text('{"hostname":"host","username":"user"}', encoding='utf-8')

    workspace.cleanup()

    assert not lock_file.exists()


def test_capture_live_board_falls_back_when_board_mismatch(tmp_path, monkeypatch):
    """A live board for a different project must not be trusted; copy disk file."""
    board_path = tmp_path / 'demo.kicad_pcb'
    board_path.write_text('(kicad_pcb (saved))', encoding='utf-8')

    other = _FakeBoard(str(tmp_path / 'other.kicad_pcb'))
    save_log = []
    _install_fake_pcbnew(monkeypatch, other, save_log)

    workspace = BoardWorkspace(str(board_path))

    assert Path(workspace.board_path).read_text(encoding='utf-8') == '(kicad_pcb (saved))'
    assert not save_log  # SaveBoard never called on a mismatched board

    workspace.cleanup()