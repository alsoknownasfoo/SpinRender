import struct
import subprocess
from unittest.mock import Mock

from SpinRender.core.renderer import (
    RenderEngine,
    _crash_diagnostics,
    _kicad_cli_arch_report,
    _run_minimal_probe,
)


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