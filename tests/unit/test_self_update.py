"""Unit tests for SpinRender.core.self_update.

Covers the pure logic — locating the package inside an extracted archive and
swapping it into place — plus error handling for the network helpers (via a
stubbed urlopen). No real network or KiCad dependency.
"""
import io
import json
import zipfile
from contextlib import contextmanager
from pathlib import Path

import pytest

from SpinRender.core import self_update as su


# ─────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────

def _make_package(root: Path) -> Path:
    """Create a minimal SpinRender package under ``root`` and return it."""
    pkg = root / "SpinRender"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("x = 1\n", encoding="utf-8")
    (pkg / "version.py").write_text("__version__ = '0'\n", encoding="utf-8")
    (pkg / "core").mkdir()
    (pkg / "core" / "theme.py").write_text("# theme\n", encoding="utf-8")
    return pkg


# ─────────────────────────────────────────────────────────────
# _is_package / find_package_root
# ─────────────────────────────────────────────────────────────

def test_is_package_true(tmp_path):
    pkg = _make_package(tmp_path)
    assert su._is_package(pkg) is True


def test_is_package_false_missing_version(tmp_path):
    d = tmp_path / "SpinRender"
    d.mkdir()
    (d / "__init__.py").write_text("", encoding="utf-8")
    assert su._is_package(d) is False


def test_find_package_root_fast_path(tmp_path):
    # Simulate a GitHub zipball: <top>/SpinRender/...
    top = tmp_path / "alsoknownasfoo-SpinRender-6f70af5"
    top.mkdir()
    pkg = _make_package(top)
    assert su.find_package_root(tmp_path) == pkg


def test_find_package_root_recursive_fallback(tmp_path):
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    pkg = _make_package(nested)
    assert su.find_package_root(tmp_path) == pkg


def test_find_package_root_not_found(tmp_path):
    (tmp_path / "unrelated").mkdir()
    with pytest.raises(su.UpdateError):
        su.find_package_root(tmp_path)


# ─────────────────────────────────────────────────────────────
# apply_package
# ─────────────────────────────────────────────────────────────

def test_apply_package_replaces_contents(tmp_path):
    # old install dir with a stale file that should disappear after update
    install_dir = tmp_path / "install" / "SpinRender"
    install_dir.mkdir(parents=True)
    (install_dir / "__init__.py").write_text("OLD\n", encoding="utf-8")
    (install_dir / "stale.py").write_text("remove me\n", encoding="utf-8")

    new_pkg = _make_package(tmp_path / "new")

    su.apply_package(new_pkg, install_dir)

    assert (install_dir / "__init__.py").read_text() == "x = 1\n"
    assert (install_dir / "version.py").is_file()
    assert not (install_dir / "stale.py").exists()  # stale file gone
    # no temp/backup left behind
    assert not (install_dir.parent / "SpinRender.update_tmp").exists()
    assert not (install_dir.parent / "SpinRender.update_old").exists()


def test_apply_package_into_empty_target(tmp_path):
    install_dir = tmp_path / "install" / "SpinRender"  # does not exist yet
    new_pkg = _make_package(tmp_path / "new")
    su.apply_package(new_pkg, install_dir)
    assert (install_dir / "__init__.py").read_text() == "x = 1\n"


def test_apply_package_rolls_back_on_stage_failure(tmp_path):
    install_dir = tmp_path / "install" / "SpinRender"
    install_dir.mkdir(parents=True)
    (install_dir / "__init__.py").write_text("KEEP\n", encoding="utf-8")

    missing = tmp_path / "does_not_exist"  # copytree source missing -> failure
    with pytest.raises(su.UpdateError):
        su.apply_package(missing, install_dir)

    # original install left intact
    assert (install_dir / "__init__.py").read_text() == "KEEP\n"
    assert not (install_dir.parent / "SpinRender.update_tmp").exists()


def test_apply_package_cleans_prior_leftovers(tmp_path):
    install_dir = tmp_path / "install" / "SpinRender"
    install_dir.mkdir(parents=True)
    (install_dir / "__init__.py").write_text("OLD\n", encoding="utf-8")
    # leftovers from a previous interrupted run
    (install_dir.parent / "SpinRender.update_tmp").mkdir()
    (install_dir.parent / "SpinRender.update_old").mkdir()

    new_pkg = _make_package(tmp_path / "new")
    su.apply_package(new_pkg, install_dir)
    assert (install_dir / "__init__.py").read_text() == "x = 1\n"


# ─────────────────────────────────────────────────────────────
# extract_zip
# ─────────────────────────────────────────────────────────────

def test_extract_zip_roundtrip(tmp_path):
    zpath = tmp_path / "a.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.writestr("top/SpinRender/__init__.py", "x = 1\n")
        zf.writestr("top/SpinRender/version.py", "v = 0\n")
    out = tmp_path / "out"
    su.extract_zip(zpath, out)
    assert (out / "top" / "SpinRender" / "__init__.py").is_file()


def test_extract_zip_bad_archive(tmp_path):
    bad = tmp_path / "bad.zip"
    bad.write_text("not a zip", encoding="utf-8")
    with pytest.raises(su.UpdateError):
        su.extract_zip(bad, tmp_path / "out")


# ─────────────────────────────────────────────────────────────
# resolve_latest (stubbed urlopen)
# ─────────────────────────────────────────────────────────────

@contextmanager
def _fake_response(payload: bytes):
    yield io.BytesIO(payload)


def test_resolve_latest_success(monkeypatch):
    payload = json.dumps({
        "tag_name": "v0.7.0-beta",
        "zipball_url": "https://api.github.com/.../zipball/v0.7.0-beta",
    }).encode()
    monkeypatch.setattr(su.urllib.request, "urlopen",
                        lambda req, timeout=0: _fake_response(payload))
    tag, zipball = su.resolve_latest("owner", "repo")
    assert tag == "v0.7.0-beta"
    assert zipball.endswith("/zipball/v0.7.0-beta")


def test_resolve_latest_missing_fields(monkeypatch):
    payload = json.dumps({"tag_name": "v0.7.0"}).encode()  # no zipball_url
    monkeypatch.setattr(su.urllib.request, "urlopen",
                        lambda req, timeout=0: _fake_response(payload))
    with pytest.raises(su.UpdateError):
        su.resolve_latest("owner", "repo")


def test_resolve_latest_network_error(monkeypatch):
    def boom(req, timeout=0):
        raise OSError("no network")
    monkeypatch.setattr(su.urllib.request, "urlopen", boom)
    with pytest.raises(su.UpdateError):
        su.resolve_latest("owner", "repo")
