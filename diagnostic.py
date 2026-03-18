#!/usr/bin/env python3
"""
SpinRender Plugin Diagnostic Script
Tests the plugin import chain and dependency detection without requiring KiCad.
Run with: python3 diagnostic.py
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "SpinRender"))

print("=" * 60)
print("SPINRENDER DIAGNOSTIC")
print("=" * 60)

# Test 1: Check file structure
print("\n[1] Checking file structure...")
required_files = [
    "SpinRender/__init__.py",
    "SpinRender/spinrender_plugin.py",
    "SpinRender/utils/logger.py",
    "SpinRender/utils/check_dependencies.py",
    "SpinRender/ui/dependencies.py",
    "SpinRender/core/theme.py",
    "SpinRender/resources/themes/dark.yaml",
]
all_present = True
for f in required_files:
    path = project_root / f
    exists = path.exists()
    status = "✓" if exists else "✗"
    print(f"  {status} {f}")
    if not exists:
        all_present = False
if not all_present:
    print("\nERROR: Some required files are missing!")
    sys.exit(1)

# Test 2: Check package imports (no wx/pcbnew)
print("\n[2] Testing pure Python imports (no wx/pcbnew)...")
try:
    from SpinRender.utils.logger import SpinLogger
    print("  ✓ SpinRender.utils.logger")
except Exception as e:
    print(f"  ✗ logger: {e}")

try:
    from SpinRender.core.theme import Theme
    print("  ✓ SpinRender.core.theme")
except Exception as e:
    print(f"  ✗ core.theme: {e}")

try:
    from SpinRender.utils.check_dependencies import DependencyChecker
    print("  ✓ SpinRender.utils.check_dependencies")
except Exception as e:
    print(f"  ✗ check_dependencies: {e}")

# Test 3: Test dependency checker instantiation
print("\n[3] Testing DependencyChecker instantiation...")
try:
    checker = DependencyChecker()
    print("  ✓ DependencyChecker created successfully")
    print(f"    Platform: {checker.system}")
except Exception as e:
    print(f"  ✗ Failed to create DependencyChecker: {e}")

# Test 4: Test dependency check (no wx, so limited)
print("\n[4] Running dependency check (this may take a few seconds)...")
try:
    status = checker.check_all()
    print("  ✓ check_all() completed")
    missing = checker.missing_deps
    if missing:
        print(f"    ⚠ Missing dependencies: {', '.join(missing)}")
    else:
        print("    ✓ All dependencies satisfied!")
except Exception as e:
    print(f"  ✗ check_all() failed: {e}")

# Test 5: Check theme loading
print("\n[5] Testing theme system...")
try:
    theme = Theme.load("dark")
    print("  ✓ Theme loaded from YAML")
    # Test color resolution
    color = theme.color("colors.accent.primary")
    print(f"    ✓ Resolved colors.accent.primary: RGB({color.Red()}, {color.Green()}, {color.Blue()})")
except Exception as e:
    print(f"  ✗ Theme loading failed: {e}")

# Test 6: Check foundation imports
print("\n[6] Testing foundation imports...")
try:
    from SpinRender.foundation.fonts import JETBRAINS_MONO, OSWALD, MDI_FONT_FAMILY
    print(f"  ✓ Fonts: {JETBRAINS_MONO}, {OSWALD}, {MDI_FONT_FAMILY}")
except Exception as e:
    print(f"  ✗ Foundation fonts: {e}")

# Test 7: Check logger setup
print("\n[7] Testing logger setup...")
try:
    logs_dir = project_root / "SpinRender" / "logs"
    SpinLogger.setup(level='verbose')
    print(f"  ✓ Logger initialized, logs dir: {logs_dir}")
    if logs_dir.exists():
        log_files = list(logs_dir.glob("spinrender_*.log"))
        print(f"    ✓ Found {len(log_files)} log file(s)")
        if log_files:
            latest = max(log_files, key=lambda p: p.stat().st_mtime)
            print(f"      Latest: {latest.name}")
    else:
        print("    ⚠ Logs directory not created yet (will create on first log)")
except Exception as e:
    print(f"  ✗ Logger setup failed: {e}")

# Summary
print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
print("\nIf all tests passed ✓, the plugin should be ready to install.")
print("Next steps:")
print("  1. Run: ./install.sh")
print("  2. Start KiCad (if not running)")
print("  3. Open a PCB file")
print("  4. Run: Tools → External Plugins → SpinRender")
print("\nCheck logs at: SpinRender/logs/spinrender_YYYY-MM-DD.log")
print("=" * 60)
