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

# Filename of the build stamp written by install.sh / install.bat when the
# plugin is deployed from a git clone. Installed copies ship without a ``.git``
# directory, so this static file is how a commit-based install is told apart
# from a clean release install after deployment.
_STAMP_FILENAME = "_version"

# Directory name KiCad's PCM uses for this package (the identifier with dots
# replaced by underscores). A manual install.sh deploy uses "SpinRender", so the
# parent directory name reliably distinguishes a PCM install from a manual one.
_PCM_DIR_NAME = "com_alsoknownasfoo_spinrender"


def _read_text(path: Path) -> str | None:
    """Return the stripped text of ``path``, or ``None`` if it can't be read."""
    try:
        return path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        return None


def _package_dir() -> Path:
    """Return the directory holding this package (where the build stamp lives)."""
    return Path(__file__).resolve().parent


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

    Resolution order (first hit wins):

    1. A static ``_version`` build stamp in the package directory, written by
       the installer when deployed from a git clone (e.g. ``0.6.1-beta+abc1234``).
       This is authoritative for installed copies, which have no ``.git``.
    2. A live ``.git`` directory (running straight from a checkout): append the
       short commit hash.
    3. The clean static base version (release / PCM install).

    Any failure falls back to the static version — this never raises.
    """
    base = __version__
    try:
        pkg_dir = _package_dir()

        # 1. Install-time build stamp (survives in installs that lack .git).
        stamp = _read_text(pkg_dir / _STAMP_FILENAME)
        if stamp:
            return stamp

        # 2. Running from a git checkout.
        git_dir = _resolve_git_dir(pkg_dir.parent)
        if git_dir is None:
            return base
        sha = _head_commit(git_dir)
        if not sha:
            return base
        return f"{base}+{sha[:7]}"
    except Exception:
        # Version display must never break plugin startup.
        return base


def installed_package_dir() -> Path:
    """Return the directory this package is installed in (for self-update)."""
    return _package_dir()


def is_pcm_install() -> bool:
    """Return ``True`` when this copy was installed by KiCad's PCM.

    PCM extracts the package into a directory named after the plugin identifier
    (``com_alsoknownasfoo_spinrender``); a manual ``install.sh`` deploy uses
    ``SpinRender``. The parent directory name is the reliable discriminator.
    Never raises.
    """
    try:
        return _package_dir().name == _PCM_DIR_NAME
    except Exception:
        return False


def is_dev_build(version: str | None = None) -> bool:
    """Return ``True`` when ``version`` carries a git commit suffix (``+sha``).

    Defaults to the resolved :func:`get_version`. A dev/commit build is one
    deployed from a clone; a clean release string has no ``+`` build metadata.
    """
    value = get_version() if version is None else version
    return "+" in value


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
