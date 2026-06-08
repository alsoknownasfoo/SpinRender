"""Runtime version resolution for SpinRender.

The single source of truth is ``__version__`` in this package's ``__init__.py``.
Packaged installs (PCM or release zip) ship without a ``.git`` directory, so
``get_version()`` returns that clean release string. When the plugin is run from
a git checkout, the short commit hash is appended (e.g. ``0.6.1-beta+abc1234``)
so contributors can tell an unreleased working copy apart from a tagged release.

Git information is read directly from the ``.git`` directory — we never shell out
to a ``git`` binary, because KiCad's bundled Python often runs without ``git`` on
PATH (notably on Windows). Every failure path falls back to the static version;
this module never raises.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from . import __version__


def _read_text(path: Path) -> str | None:
    """Return the stripped text of ``path``, or ``None`` if it can't be read."""
    try:
        return path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        return None


def _resolve_git_dir(repo_root: Path) -> Path | None:
    """Locate the ``.git`` directory for ``repo_root``.

    Handles the worktree/submodule form where ``.git`` is a file containing a
    ``gitdir: <path>`` pointer rather than a directory.
    """
    dot_git = repo_root / ".git"
    if dot_git.is_dir():
        return dot_git
    if dot_git.is_file():
        content = _read_text(dot_git)
        if content and content.startswith("gitdir:"):
            target = content.split(":", 1)[1].strip()
            resolved = (repo_root / target).resolve()
            if resolved.is_dir():
                return resolved
    return None


def _head_commit(git_dir: Path) -> str | None:
    """Resolve the commit SHA that ``HEAD`` points at, reading ``.git`` directly."""
    head = _read_text(git_dir / "HEAD")
    if not head:
        return None

    # Detached HEAD: the file holds the SHA directly.
    if not head.startswith("ref:"):
        return head

    ref = head.split(":", 1)[1].strip()

    # Loose ref: refs/heads/<branch> exists as a file holding the SHA.
    sha = _read_text(git_dir / ref)
    if sha:
        return sha

    # Packed ref: scan packed-refs for the matching ref line.
    packed = _read_text(git_dir / "packed-refs")
    if packed:
        for line in packed.splitlines():
            line = line.strip()
            if not line or line.startswith(("#", "^")):
                continue
            parts = line.split(" ", 1)
            if len(parts) == 2 and parts[1].strip() == ref:
                return parts[0].strip()

    return None


@lru_cache(maxsize=1)
def get_version() -> str:
    """Return the version string to display.

    Release/PCM installs return the static base version. Git checkouts append
    the short commit hash (e.g. ``0.6.1-beta+abc1234``). Any failure falls back
    to the static version — this never raises.
    """
    base = __version__
    try:
        # SpinRender/version.py -> SpinRender/ (package) -> repo root
        repo_root = Path(__file__).resolve().parent.parent
        git_dir = _resolve_git_dir(repo_root)
        if git_dir is None:
            return base
        sha = _head_commit(git_dir)
        if not sha:
            return base
        return f"{base}+{sha[:7]}"
    except Exception:
        # Version display must never break plugin startup.
        return base


def base_version() -> str:
    """Return the release version with no git build suffix.

    Used for update comparisons against published release tags.
    """
    return __version__


def _version_key(value: str) -> tuple[int, ...]:
    """Parse a version string into a comparable tuple of release numbers.

    Leading ``v`` and any pre-release/build suffix (``-beta``, ``+abc1234``) are
    ignored, so ``v0.10.0`` sorts above ``0.9.0`` (which naive string compare
    gets wrong). Non-numeric or missing segments are treated as ``0``.
    """
    core = value.strip().lstrip("vV")
    # Drop pre-release (-...) and build metadata (+...) — compare release only.
    for sep in ("-", "+"):
        core = core.split(sep, 1)[0]
    parts = []
    for segment in core.split("."):
        try:
            parts.append(int(segment))
        except ValueError:
            parts.append(0)
    return tuple(parts) or (0,)


def is_newer(candidate: str, current: str) -> bool:
    """Return ``True`` when ``candidate`` is a strictly newer release than ``current``."""
    if not candidate:
        return False
    return _version_key(candidate) > _version_key(current)
