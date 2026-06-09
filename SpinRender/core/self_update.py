"""In-place self-update for **non-PCM** installs.

Downloads the latest GitHub release source archive (zipball) and swaps the
installed plugin files into place. PCM installs are managed by KiCad's Plugin &
Content Manager and must NOT use this path — callers check
:func:`SpinRender.version.is_pcm_install` first and notify the user to update via
PCM instead.

Network and filesystem work are split into small functions so the pure logic
(locating the package inside an extracted archive, swapping it into place) is
testable without hitting the network.
"""
from __future__ import annotations

import json
import os
import shutil
import urllib.request
import zipfile
from pathlib import Path

_LATEST_API = "https://api.github.com/repos/{owner}/{repo}/releases/latest"
_HEADERS = {"User-Agent": "SpinRender", "Accept": "application/vnd.github+json"}


class UpdateError(Exception):
    """Raised when a self-update cannot be completed; message is user-facing."""


def resolve_latest(owner: str, repo: str, timeout: float = 8.0) -> tuple[str, str]:
    """Return ``(tag_name, zipball_url)`` for the latest release.

    Raises :class:`UpdateError` on any network or parse failure.
    """
    url = _LATEST_API.format(owner=owner, repo=repo)
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
    except Exception as exc:  # network, timeout, JSON — all surfaced uniformly
        raise UpdateError(f"Could not reach GitHub: {exc}") from exc

    tag = data.get("tag_name") or ""
    zipball = data.get("zipball_url") or ""
    if not tag or not zipball:
        raise UpdateError("Release metadata is missing a tag or download URL.")
    return tag, zipball


def download(url: str, dest: Path, timeout: float = 30.0) -> Path:
    """Stream ``url`` into ``dest``. Raises :class:`UpdateError` on failure."""
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp, open(dest, "wb") as fh:
            shutil.copyfileobj(resp, fh)
    except Exception as exc:
        raise UpdateError(f"Download failed: {exc}") from exc
    return dest


def extract_zip(zip_path: Path, dest_dir: Path) -> Path:
    """Extract ``zip_path`` into ``dest_dir``. Raises :class:`UpdateError`."""
    try:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(dest_dir)
    except Exception as exc:
        raise UpdateError(f"Could not read the downloaded archive: {exc}") from exc
    return dest_dir


def _is_package(path: Path) -> bool:
    """True when ``path`` looks like the SpinRender package directory."""
    return (path / "__init__.py").is_file() and (path / "version.py").is_file()


def find_package_root(extracted: Path) -> Path:
    """Locate the SpinRender package directory inside an extracted zipball.

    A GitHub zipball expands to a single top-level dir (e.g.
    ``alsoknownasfoo-SpinRender-<sha>/``) containing the repo, so the package is
    normally at ``<top>/SpinRender/``. Falls back to a recursive search.
    Raises :class:`UpdateError` if not found.
    """
    # Fast path: <top>/SpinRender for each top-level dir.
    for top in sorted(p for p in extracted.iterdir() if p.is_dir()):
        pkg = top / "SpinRender"
        if _is_package(pkg):
            return pkg

    # Fallback: recursive search; shallowest match wins.
    matches = [p for p in extracted.rglob("SpinRender") if _is_package(p)]
    if matches:
        return min(matches, key=lambda p: len(p.parts))

    raise UpdateError("Could not find the SpinRender package in the downloaded archive.")


def apply_package(new_pkg: Path, install_dir: Path) -> None:
    """Replace ``install_dir`` with ``new_pkg`` as atomically as possible.

    Stages a sibling copy, then swaps directories with renames (atomic on one
    filesystem), keeping a backup until the swap succeeds. Rolls back on
    failure. Raises :class:`UpdateError` on failure.
    """
    install_dir = install_dir.resolve()
    parent = install_dir.parent
    staged = parent / (install_dir.name + ".update_tmp")
    backup = parent / (install_dir.name + ".update_old")

    # Clear leftovers from any previous interrupted run.
    _force_rmtree(staged)
    _force_rmtree(backup)

    try:
        shutil.copytree(new_pkg, staged)
    except Exception as exc:
        _force_rmtree(staged)
        raise UpdateError(f"Could not stage the update: {exc}") from exc

    moved_aside = False
    try:
        if install_dir.exists():
            os.replace(install_dir, backup)
            moved_aside = True
        os.replace(staged, install_dir)
    except Exception as exc:
        # Best-effort rollback if the original was moved but the new one failed.
        if moved_aside and not install_dir.exists():
            try:
                os.replace(backup, install_dir)
            except Exception:
                pass
        _force_rmtree(staged)
        raise UpdateError(f"Could not apply the update: {exc}") from exc

    _force_rmtree(backup)


def _force_rmtree(path: Path) -> None:
    """Remove ``path`` recursively, clearing read-only bits; never raises."""
    if not path.exists():
        return

    def _on_error(func, p, _exc):
        try:
            os.chmod(p, 0o700)
            func(p)
        except Exception:
            pass

    shutil.rmtree(path, onerror=_on_error)
