#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""Unit tests for SpinRender.version.

Covers direct ``.git`` parsing (loose ref, packed-refs, detached HEAD, the
``gitdir:`` file form, and missing/corrupt cases) plus semver comparison used
by the update check.
"""
import pytest

from SpinRender import version as ver
from SpinRender import __version__


# ─────────────────────────────────────────────────────────────
# .git fixtures
# ─────────────────────────────────────────────────────────────

def _make_git_dir(root, head, refs=None, packed=None):
    """Create a minimal .git directory under ``root`` and return its path."""
    git_dir = root / ".git"
    git_dir.mkdir()
    (git_dir / "HEAD").write_text(head, encoding="utf-8")
    for ref_path, sha in (refs or {}).items():
        target = git_dir / ref_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(sha + "\n", encoding="utf-8")
    if packed is not None:
        (git_dir / "packed-refs").write_text(packed, encoding="utf-8")
    return git_dir


# ─────────────────────────────────────────────────────────────
# _head_commit
# ─────────────────────────────────────────────────────────────

def test_head_commit_loose_ref(tmp_path):
    sha = "abc1234def5678901234567890123456789012ab"
    git_dir = _make_git_dir(
        tmp_path,
        head="ref: refs/heads/main\n",
        refs={"refs/heads/main": sha},
    )
    assert ver._head_commit(git_dir) == sha


def test_head_commit_packed_ref(tmp_path):
    sha = "1111111222222233333334444444555555566666"
    packed = (
        "# pack-refs with: peeled fully-peeled sorted\n"
        f"{sha} refs/heads/main\n"
        "aaaa000011112222333344445555666677778888 refs/tags/v0.6.1\n"
        "^bbbb0000111122223333444455556666777788899\n"
    )
    git_dir = _make_git_dir(tmp_path, head="ref: refs/heads/main\n", packed=packed)
    assert ver._head_commit(git_dir) == sha


def test_head_commit_loose_ref_takes_priority_over_packed(tmp_path):
    loose = "cccccccc11112222333344445555666677778888"
    packed = "99999999111122223333444455556666777700000 refs/heads/main\n"
    git_dir = _make_git_dir(
        tmp_path,
        head="ref: refs/heads/main\n",
        refs={"refs/heads/main": loose},
        packed=packed,
    )
    assert ver._head_commit(git_dir) == loose


def test_head_commit_detached(tmp_path):
    sha = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
    git_dir = _make_git_dir(tmp_path, head=sha + "\n")
    assert ver._head_commit(git_dir) == sha


def test_head_commit_missing_head(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    assert ver._head_commit(git_dir) is None


def test_head_commit_ref_points_nowhere(tmp_path):
    git_dir = _make_git_dir(tmp_path, head="ref: refs/heads/ghost\n")
    assert ver._head_commit(git_dir) is None


# ─────────────────────────────────────────────────────────────
# _resolve_git_dir
# ─────────────────────────────────────────────────────────────

def test_resolve_git_dir_directory(tmp_path):
    git_dir = _make_git_dir(tmp_path, head="ref: refs/heads/main\n")
    assert ver._resolve_git_dir(tmp_path) == git_dir


def test_resolve_git_dir_missing(tmp_path):
    assert ver._resolve_git_dir(tmp_path) is None


def test_resolve_git_dir_gitdir_file_form(tmp_path):
    real_git = tmp_path / "actual_git"
    real_git.mkdir()
    (tmp_path / ".git").write_text(f"gitdir: {real_git}\n", encoding="utf-8")
    assert ver._resolve_git_dir(tmp_path) == real_git.resolve()


def test_resolve_git_dir_gitdir_file_bad_pointer(tmp_path):
    (tmp_path / ".git").write_text("gitdir: /does/not/exist\n", encoding="utf-8")
    assert ver._resolve_git_dir(tmp_path) is None


# ─────────────────────────────────────────────────────────────
# get_version (via monkeypatched git resolution)
# ─────────────────────────────────────────────────────────────

def test_get_version_no_git_returns_base(monkeypatch):
    ver.get_version.cache_clear()
    monkeypatch.setattr(ver, "_resolve_git_dir", lambda root: None)
    assert ver.get_version() == __version__
    ver.get_version.cache_clear()


def test_get_version_with_git_appends_short_sha(monkeypatch):
    ver.get_version.cache_clear()
    sha = "abcdef1234567890abcdef1234567890abcdef12"
    monkeypatch.setattr(ver, "_resolve_git_dir", lambda root: root)
    monkeypatch.setattr(ver, "_head_commit", lambda git_dir: sha)
    assert ver.get_version() == f"{__version__}+abcdef1"
    ver.get_version.cache_clear()


def test_get_version_never_raises(monkeypatch):
    ver.get_version.cache_clear()
    def boom(root):
        raise RuntimeError("disk gone")
    monkeypatch.setattr(ver, "_resolve_git_dir", boom)
    assert ver.get_version() == __version__
    ver.get_version.cache_clear()


def test_base_version_is_clean():
    assert ver.base_version() == __version__
    assert "+" not in ver.base_version()


# ─────────────────────────────────────────────────────────────
# semver comparison
# ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("candidate,current,expected", [
    ("0.7.0", "0.6.1", True),
    ("v0.7.0", "0.6.1-beta", True),
    ("0.10.0", "0.9.0", True),          # string compare would get this wrong
    ("0.6.1", "0.6.1", False),
    ("0.6.0", "0.6.1", False),
    ("0.6.1", "0.6.1-beta", False),     # suffix ignored -> equal release
    ("0.6.1+abc1234", "0.6.1", False),  # build metadata ignored
    ("", "0.6.1", False),               # no tag -> not newer
])
def test_is_newer(candidate, current, expected):
    assert ver.is_newer(candidate, current) is expected


def test_version_key_handles_garbage():
    assert ver._version_key("not.a.version") == (0, 0, 0)
    assert ver._version_key("") == (0,)


# ─────────────────────────────────────────────────────────────
# build stamp + install-kind detection
# ─────────────────────────────────────────────────────────────

def test_get_version_prefers_build_stamp(tmp_path, monkeypatch):
    """A _version stamp wins over a live .git checkout."""
    ver.get_version.cache_clear()
    (tmp_path / ver._STAMP_FILENAME).write_text("0.6.1-beta+deadbee\n", encoding="utf-8")
    monkeypatch.setattr(ver, "_package_dir", lambda: tmp_path)
    # Even if git resolution would succeed, the stamp takes priority.
    monkeypatch.setattr(ver, "_resolve_git_dir", lambda root: root)
    monkeypatch.setattr(ver, "_head_commit", lambda g: "ffffffffffff")
    assert ver.get_version() == "0.6.1-beta+deadbee"
    ver.get_version.cache_clear()


def test_get_version_no_stamp_falls_back_to_git(tmp_path, monkeypatch):
    ver.get_version.cache_clear()
    monkeypatch.setattr(ver, "_package_dir", lambda: tmp_path)  # no _version file
    monkeypatch.setattr(ver, "_resolve_git_dir", lambda root: root)
    monkeypatch.setattr(ver, "_head_commit", lambda g: "abcdef1234")
    assert ver.get_version() == f"{__version__}+abcdef1"
    ver.get_version.cache_clear()


def test_get_version_no_stamp_no_git_returns_base(tmp_path, monkeypatch):
    ver.get_version.cache_clear()
    monkeypatch.setattr(ver, "_package_dir", lambda: tmp_path)
    monkeypatch.setattr(ver, "_resolve_git_dir", lambda root: None)
    assert ver.get_version() == __version__
    ver.get_version.cache_clear()


def test_is_pcm_install_true(monkeypatch, tmp_path):
    pcm_dir = tmp_path / ver._PCM_DIR_NAME
    pcm_dir.mkdir()
    monkeypatch.setattr(ver, "_package_dir", lambda: pcm_dir)
    assert ver.is_pcm_install() is True


def test_is_pcm_install_false_for_manual(monkeypatch, tmp_path):
    manual_dir = tmp_path / "SpinRender"
    manual_dir.mkdir()
    monkeypatch.setattr(ver, "_package_dir", lambda: manual_dir)
    assert ver.is_pcm_install() is False


def test_is_pcm_install_never_raises(monkeypatch):
    def boom():
        raise RuntimeError("nope")
    monkeypatch.setattr(ver, "_package_dir", boom)
    assert ver.is_pcm_install() is False


@pytest.mark.parametrize("version,expected", [
    ("0.6.1-beta+abc1234", True),
    ("0.6.1-beta", False),
    ("0.6.1", False),
])
def test_is_dev_build(version, expected):
    assert ver.is_dev_build(version) is expected
