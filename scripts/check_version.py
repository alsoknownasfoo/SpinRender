#!/usr/bin/env python3
"""Assert the packaged metadata version matches the canonical __version__.

``SpinRender/__init__.py`` is the single source of truth for the version. The
PCM ``metadata.json`` files carry their own copy that KiCad reads, so they can
drift. Run this in CI / before tagging a release to catch a mismatch early.

The metadata uses release versions (e.g. ``0.6.1``) while ``__version__`` may
carry a pre-release suffix (e.g. ``0.6.1-beta``); only the release core is
compared.

Exit code 0 on match, 1 on mismatch or missing data.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INIT_FILE = REPO_ROOT / "SpinRender" / "__init__.py"
METADATA_FILES = [
    REPO_ROOT / "metadata.json",
    REPO_ROOT / "build" / "pcm" / "metadata.json",
    REPO_ROOT / "build" / "submission" / "packages" / "com.alsoknownasfoo.spinrender" / "metadata.json",
]


def _release_core(version: str) -> str:
    """Strip a leading ``v`` and any pre-release/build suffix."""
    core = version.strip().lstrip("vV")
    return re.split(r"[-+]", core, maxsplit=1)[0]


def _canonical_version() -> str:
    text = INIT_FILE.read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
    if not match:
        raise SystemExit(f"Could not find __version__ in {INIT_FILE}")
    return match.group(1)


def main() -> int:
    canonical = _canonical_version()
    expected = _release_core(canonical)
    print(f"Canonical __version__ = {canonical}  (release core {expected})")

    ok = True
    for meta_path in METADATA_FILES:
        if not meta_path.exists():
            print(f"SKIP  {meta_path} (not found)")
            continue
        try:
            versions = json.loads(meta_path.read_text(encoding="utf-8")).get("versions", [])
            found = {_release_core(v.get("version", "")) for v in versions}
        except (json.JSONDecodeError, OSError) as exc:
            print(f"FAIL  {meta_path}: {exc}")
            ok = False
            continue
        if expected in found:
            print(f"OK    {meta_path} ({', '.join(sorted(found))})")
        else:
            print(f"FAIL  {meta_path}: expected {expected}, found {sorted(found) or 'none'}")
            ok = False

    if not ok:
        print("\nVersion mismatch — bump metadata.json to match __version__.")
        return 1
    print("\nAll metadata versions match.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
