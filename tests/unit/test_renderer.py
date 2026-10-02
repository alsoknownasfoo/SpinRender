import struct
import subprocess
from unittest.mock import Mock

from SpinRender.core.renderer import (
    RenderEngine,
    _prepare_kicad_config_home,
    _crash_diagnostics,
    _kicad_cli_arch_report,
    _pad_frame_to_size,
    _png_size,
    _render_size_from_cmd,
    _run_minimal_probe,
)


def _write_png_header(path, width, height):
    """Write just enough of a PNG (signature + IHDR) for size probing."""
    ihdr = struct.pack('>II5B', width, height, 8, 6, 0, 0, 0)
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + struct.pack('>I', 13) + b'IHDR' + ihdr + b'\0' * 4)


def test_generate_frames_uses_utf8_for_cli_output(monkeypatch, tmp_path):
    settings = {
        'period': '0.04',
        'resolution': '640x480',
        'format': 'png_sequence',
    }
    engine = RenderEngine('/tmp/example.kicad_pcb', settings)

    mock_process = Mock()
    mock_process.communicate.return_value = ('Rendered frame \u2013 ok\n', None)
    mock_process.returncode = 0

    popen_calls = []

    def fake_popen(*args, **kwargs):
        popen_calls.append({'args': args, 'kwargs': kwargs})
        return mock_process

    monkeypatch.setattr('SpinRender.core.renderer.find_command', lambda _: '/usr/bin/kicad-cli')
    monkeypatch.setattr('SpinRender.core.renderer.subprocess.Popen', fake_popen)

    frame_count = engine.generate_frames(str(tmp_path))

    assert frame_count == 1
    assert len(popen_calls) == 1
    assert popen_calls[0]['kwargs']['text'] is True
    assert popen_calls[0]['kwargs']['encoding'] == 'utf-8'
    assert popen_calls[0]['kwargs']['errors'] == 'replace'


def test_malformed_quality_override_does_not_block_crash_retry(monkeypatch, tmp_path):
    """A leftover/malformed override like "--quality-high" (issue #1) must not
    be mistaken for an intentional --quality override: it isn't a real
    kicad-cli flag, so it should neither suppress the crash-retry-at-basic
    safety net nor go unnoticed."""
    settings = {
        'period': '0.04',
        'resolution': '640x480',
        'format': 'png_sequence',
        'cli_overrides': '--quality-high',
    }
    engine = RenderEngine('/tmp/example.kicad_pcb', settings)

    class FakeProcess:
        def __init__(self, returncode, stdout=''):
            self.returncode = returncode
            self._stdout = stdout

        def communicate(self, timeout=None):
            return self._stdout, None

    calls = []
    real_popen = subprocess.Popen

    def fake_popen(cmd, **kwargs):
        # The crash path also logs diagnostics that call platform.platform()
        # (which on some systems shells out, e.g. `uname -p`) and runs the
        # minimal-probe render (a bare, --perspective-less command) — only
        # intercept and count the actual frame-render call, and let anything
        # else (uname, the probe) run for real.
        if not cmd or cmd[0] != '/usr/bin/kicad-cli' or '--perspective' not in cmd:
            return real_popen(cmd, **kwargs)
        calls.append(cmd)
        quality = cmd[cmd.index('--quality') + 1]
        if quality == 'user':
            return FakeProcess(-11)  # simulated SIGSEGV at raytraced quality
        return FakeProcess(0)  # basic quality succeeds

    monkeypatch.setattr('SpinRender.core.renderer.find_command', lambda _: '/usr/bin/kicad-cli')
    monkeypatch.setattr('SpinRender.core.renderer.subprocess.Popen', fake_popen)

    frame_count = engine.generate_frames(str(tmp_path))

    assert frame_count == 1
    assert engine.degraded_quality is True
    assert len(calls) == 2  # crashed at "user", retried and succeeded at "basic"


def test_kicad_cli_arch_report_detects_native_execution(tmp_path, monkeypatch):
    path = tmp_path / "fake_kicad_cli"
    path.write_bytes(
        b'\xca\xfe\xba\xbe' + struct.pack('>I', 1) + struct.pack('>iIIII', 0x0100000c, 0, 0, 0, 0)
    )
    monkeypatch.setattr('SpinRender.core.renderer.platform.machine', lambda: 'arm64')

    report = _kicad_cli_arch_report(str(path))

    assert 'native arm64 execution expected' in report


def test_kicad_cli_arch_report_flags_translation(tmp_path, monkeypatch):
    path = tmp_path / "fake_kicad_cli"
    path.write_bytes(
        b'\xca\xfe\xba\xbe' + struct.pack('>I', 1) + struct.pack('>iIIII', 0x01000007, 0, 0, 0, 0)
    )
    monkeypatch.setattr('SpinRender.core.renderer.platform.machine', lambda: 'arm64')

    report = _kicad_cli_arch_report(str(path))

    assert 'NOT one of them' in report
    assert 'translated' in report


def test_kicad_cli_arch_report_empty_for_non_macho(tmp_path):
    path = tmp_path / "not_a_binary.txt"
    path.write_text("hello")

    assert _kicad_cli_arch_report(str(path)) == ""


def test_crash_diagnostics_flags_silent_fast_crash(tmp_path):
    path = tmp_path / "kicad-cli"
    path.write_bytes(b'not mach-o')

    block = _crash_diagnostics(str(path), 0.3, '')

    assert 'crashed before emitting any output' in block


def test_crash_diagnostics_no_flag_for_slow_crash_with_output(tmp_path):
    path = tmp_path / "kicad-cli"
    path.write_bytes(b'not mach-o')

    block = _crash_diagnostics(str(path), 30.0, 'Loading...\n')

    assert 'crashed before emitting any output' not in block


def test_minimal_probe_success_points_at_render_settings(monkeypatch, tmp_path):
    class FakeProcess:
        returncode = 0

        def communicate(self, timeout=None):
            return '', None

    monkeypatch.setattr('SpinRender.core.renderer.subprocess.Popen', lambda *a, **k: FakeProcess())

    result = _run_minimal_probe('/usr/bin/kicad-cli', str(tmp_path / 'board.kicad_pcb'), {})

    assert 'SUCCEEDED' in result
    assert 'not kicad-cli/environment itself' in result


def test_minimal_probe_failure_points_at_environment(monkeypatch, tmp_path):
    class FakeProcess:
        returncode = -11

        def communicate(self, timeout=None):
            return '', None

    monkeypatch.setattr('SpinRender.core.renderer.subprocess.Popen', lambda *a, **k: FakeProcess())

    result = _run_minimal_probe('/usr/bin/kicad-cli', str(tmp_path / 'board.kicad_pcb'), {})

    assert 'ALSO FAILED' in result
    assert 'outside SpinRender' in result


def test_minimal_probe_reports_inconclusive_on_launch_failure(tmp_path):
    result = _run_minimal_probe('/no/such/kicad-cli', str(tmp_path / 'board.kicad_pcb'), {})

    assert 'could not be run' in result

def test_png_size_reads_ihdr(tmp_path):
    frame = tmp_path / 'frame0000.png'
    _write_png_header(frame, 1904, 1064)
    assert _png_size(str(frame)) == (1904, 1064)


def test_png_size_returns_none_for_missing_or_invalid(tmp_path):
    assert _png_size(str(tmp_path / 'missing.png')) is None
    bad = tmp_path / 'bad.png'
    bad.write_bytes(b'not a png at all, just text')
    assert _png_size(str(bad)) is None


def test_pad_frame_skips_when_already_requested_size(monkeypatch, tmp_path):
    frame = tmp_path / 'frame0000.png'
    _write_png_header(frame, 1920, 1080)
    calls = []
    monkeypatch.setattr('SpinRender.core.renderer._start_text_process', lambda *a, **k: calls.append(a))
    _pad_frame_to_size(str(frame), 1920, 1080, '/usr/bin/ffmpeg')
    assert calls == []


def test_pad_frame_centers_kicad_crop_on_transparent_canvas(monkeypatch, tmp_path):
    # kicad-cli renders a centered crop: 1920x1080 -> 1904x1064 at offset (8, 8)
    frame = tmp_path / 'frame0000.png'
    _write_png_header(frame, 1904, 1064)
    calls = []

    def fake_process(cmd, **kwargs):
        calls.append(cmd)
        open(cmd[-1], 'wb').close()  # ffmpeg writes the padded temp file
        proc = Mock()
        proc.communicate.return_value = ('', None)
        proc.returncode = 0
        return proc

    monkeypatch.setattr('SpinRender.core.renderer._start_text_process', fake_process)
    _pad_frame_to_size(str(frame), 1920, 1080, '/usr/bin/ffmpeg')

    assert len(calls) == 1
    vf = calls[0][calls[0].index('-vf') + 1]
    assert vf.startswith('pad=1920:1080:8:8:')
    assert 'black@0' in vf
    assert frame.exists()
    assert not any(p.name != 'frame0000.png' for p in tmp_path.iterdir())


def test_pad_frame_keeps_original_when_ffmpeg_fails(monkeypatch, tmp_path):
    frame = tmp_path / 'frame0000.png'
    _write_png_header(frame, 1904, 1064)
    original = frame.read_bytes()

    proc = Mock()
    proc.communicate.return_value = ('boom', None)
    proc.returncode = 1
    monkeypatch.setattr('SpinRender.core.renderer._start_text_process', lambda *a, **k: proc)

    _pad_frame_to_size(str(frame), 1920, 1080, '/usr/bin/ffmpeg')
    assert frame.read_bytes() == original
    assert [p.name for p in tmp_path.iterdir()] == ['frame0000.png']


def test_pad_frame_noop_without_ffmpeg(tmp_path):
    frame = tmp_path / 'frame0000.png'
    _write_png_header(frame, 1904, 1064)
    original = frame.read_bytes()
    _pad_frame_to_size(str(frame), 1920, 1080, None)
    assert frame.read_bytes() == original


def test_pad_frame_kills_timed_out_ffmpeg_and_keeps_original(monkeypatch, tmp_path):
    frame = tmp_path / 'frame0000.png'
    _write_png_header(frame, 1904, 1064)
    original = frame.read_bytes()

    proc = Mock()
    proc.communicate.side_effect = [subprocess.TimeoutExpired('ffmpeg', 60), ('', None)]
    monkeypatch.setattr('SpinRender.core.renderer._start_text_process', lambda *a, **k: proc)

    _pad_frame_to_size(str(frame), 1920, 1080, '/usr/bin/ffmpeg')

    proc.kill.assert_called_once()
    assert proc.communicate.call_count == 2  # drained after kill
    assert frame.read_bytes() == original


def test_pad_frame_cleanup_failure_is_not_fatal(monkeypatch, tmp_path):
    frame = tmp_path / 'frame0000.png'
    _write_png_header(frame, 1904, 1064)

    def fake_process(cmd, **kwargs):
        open(cmd[-1], 'wb').close()
        proc = Mock()
        proc.communicate.return_value = ('boom', None)
        proc.returncode = 1
        return proc

    def locked_remove(path):
        raise PermissionError('file in use')

    monkeypatch.setattr('SpinRender.core.renderer._start_text_process', fake_process)
    monkeypatch.setattr('SpinRender.core.renderer.os.remove', locked_remove)
    _pad_frame_to_size(str(frame), 1920, 1080, '/usr/bin/ffmpeg')  # must not raise


def test_render_size_from_cmd_uses_settings_when_not_overridden():
    cmd = ['kicad-cli', 'pcb', 'render', '-w', '1920', '-h', '1080', '-o', 'x.png']
    assert _render_size_from_cmd(cmd, 1920, 1080) == (1920, 1080)


def test_render_size_from_cmd_honours_overrides():
    cmd = ['kicad-cli', 'pcb', 'render', '--quality', 'user', '-w', '1280', '-h', '720']
    assert _render_size_from_cmd(cmd, 1920, 1080) == (1280, 720)


def test_render_size_from_cmd_long_flags_and_first_wins():
    # kicad-cli takes the first occurrence when a flag is repeated
    cmd = ['kicad-cli', '--width', '800', '--height', '600', '-w', '1920', '-h', '1080']
    assert _render_size_from_cmd(cmd, 1920, 1080) == (800, 600)


def test_render_size_from_cmd_ignores_unparseable_values():
    cmd = ['kicad-cli', '-w', 'wide', '-h']
    assert _render_size_from_cmd(cmd, 1920, 1080) == (1920, 1080)


def test_generate_frames_pads_to_overridden_size(monkeypatch, tmp_path):
    settings = {
        'period': '0.04',
        'resolution': '1920x1080',
        'format': 'png_sequence',
        'cli_overrides': '-w 1280 -h 720',
    }
    engine = RenderEngine('/tmp/example.kicad_pcb', settings)

    proc = Mock()
    proc.communicate.return_value = ('', None)
    proc.returncode = 0
    monkeypatch.setattr('SpinRender.core.renderer.find_command', lambda _: '/usr/bin/tool')
    monkeypatch.setattr('SpinRender.core.renderer.subprocess.Popen', lambda *a, **k: proc)
    pads = []
    monkeypatch.setattr('SpinRender.core.renderer._pad_frame_to_size',
                        lambda path, w, h, ffmpeg: pads.append((w, h)))

    engine.generate_frames(str(tmp_path))
    assert pads == [(1280, 720)]


def _capture_assembly_cmds(monkeypatch):
    cmds = []

    def fake_process(cmd, **kwargs):
        cmds.append(cmd)
        proc = Mock()
        proc.communicate.return_value = ('', None)
        proc.returncode = 0
        return proc

    monkeypatch.setattr('SpinRender.core.renderer.find_command', lambda _: '/usr/bin/ffmpeg')
    monkeypatch.setattr('SpinRender.core.renderer._start_text_process', fake_process)
    return cmds


def _filter_graph(cmd):
    return cmd[cmd.index('-filter_complex') + 1]


def test_assemble_mp4_canvas_matches_rendered_frames(monkeypatch, tmp_path):
    _write_png_header(tmp_path / 'frame0000.png', 1280, 720)
    engine = RenderEngine('/tmp/example.kicad_pcb', {'resolution': '1920x1080'})
    cmds = _capture_assembly_cmds(monkeypatch)

    engine.assemble_mp4(str(tmp_path), str(tmp_path / 'out.mp4'), 1)

    assert 's=1280x720' in _filter_graph(cmds[0])


def test_assemble_gif_canvas_matches_rendered_frames(monkeypatch, tmp_path):
    _write_png_header(tmp_path / 'frame0000.png', 1280, 720)
    engine = RenderEngine('/tmp/example.kicad_pcb', {'resolution': '1920x1080'})
    cmds = _capture_assembly_cmds(monkeypatch)

    engine.assemble_gif(str(tmp_path), str(tmp_path / 'out.gif'), 1)

    assert len(cmds) == 2  # palette + assembly
    assert all('s=1280x720' in _filter_graph(c) for c in cmds)


def test_assembly_canvas_falls_back_to_resolution_setting(monkeypatch, tmp_path):
    engine = RenderEngine('/tmp/example.kicad_pcb', {'resolution': '1920x1080'})
    cmds = _capture_assembly_cmds(monkeypatch)

    engine.assemble_mp4(str(tmp_path), str(tmp_path / 'out.mp4'), 1)

    assert 's=1920x1080' in _filter_graph(cmds[0])


def _fake_plugin_dir(tmp_path, versions=('9.0', '10.0')):
    plugin_dir = tmp_path / 'plugin'
    for v in versions:
        d = plugin_dir / 'resources' / 'kicad_config' / v
        d.mkdir(parents=True)
        (d / '3d_viewer.json').write_text('{}')
    return plugin_dir


GLOBAL_LIB_TABLES = {
    'sym-lib-table': 'sym_lib_table',
    'fp-lib-table': 'fp_lib_table',
    'design-block-lib-table': 'design_block_lib_table',
}


def test_config_home_seeds_empty_global_lib_tables(monkeypatch, tmp_path):
    # KiCad <= 10.0.6 segfaults when a config home has no global library tables
    # and PCM-installed libraries exist (issue #15).
    monkeypatch.setattr('SpinRender.core.renderer.tempfile.gettempdir', lambda: str(tmp_path / 'tmp'))
    home = _prepare_kicad_config_home(str(_fake_plugin_dir(tmp_path)))

    for version in ('9.0', '10.0'):
        for filename, root in GLOBAL_LIB_TABLES.items():
            table = tmp_path / 'tmp' / 'SpinRender_kicad_config' / version / filename
            assert table.read_text().lstrip().startswith(f'({root}'), (version, filename)
    assert home == str(tmp_path / 'tmp' / 'SpinRender_kicad_config')


def test_config_home_keeps_existing_lib_tables(monkeypatch, tmp_path):
    # kicad-cli may add PCM rows to the tables; don't clobber them on each render
    monkeypatch.setattr('SpinRender.core.renderer.tempfile.gettempdir', lambda: str(tmp_path / 'tmp'))
    existing = tmp_path / 'tmp' / 'SpinRender_kicad_config' / '10.0' / 'fp-lib-table'
    existing.parent.mkdir(parents=True)
    existing.write_text('(fp_lib_table\n  (lib (name "PCM_Example"))\n)\n')

    _prepare_kicad_config_home(str(_fake_plugin_dir(tmp_path, versions=('10.0',))))

    assert 'PCM_Example' in existing.read_text()


def test_config_home_lib_table_failure_is_not_fatal(monkeypatch, tmp_path):
    monkeypatch.setattr('SpinRender.core.renderer.tempfile.gettempdir', lambda: str(tmp_path / 'tmp'))
    real_open = open

    def failing_open(path, *args, **kwargs):
        if str(path).endswith('-lib-table'):
            raise PermissionError('read-only temp dir')
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr('builtins.open', failing_open)
    home = _prepare_kicad_config_home(str(_fake_plugin_dir(tmp_path, versions=('10.0',))))
    assert (tmp_path / 'tmp' / 'SpinRender_kicad_config' / '10.0' / '3d_viewer.json').exists()
    assert home
