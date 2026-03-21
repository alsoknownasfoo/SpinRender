<!-- Generated: 2026-03-21 | Consolidated from TDD_PLAN.md, PROJECT_PLAN.md, KICAD_CLI_RENDER_NOTES.md -->

# Developer Workflow Guide

This guide covers essential SpinRender development practices: testing, environment setup, and KiCad CLI integration.

---

## Table of Contents
1. [Testing Strategy](#testing-strategy)
2. [Test Infrastructure](#test-infrastructure)
3. [Mock Strategy](#mock-strategy)
4. [Running Tests](#running-tests)
5. [KiCad CLI Integration](#kicad-cli-integration)
6. [Rotation Coordinate System](#rotation-coordinate-system)

---

## Testing Strategy

**Status**: This is the current testing approach for SpinRender UI development.

**Coverage Target**: 80% minimum (lines + branches + functions)

**Test Framework**: `pytest` + `pytest-cov`

** Philosophy**: Test-driven development (TDD) - write tests before implementation.

### Why TDD?
- Ensures testability from the start
- Catches regressions early
- Documents expected behavior
- Enables confident refactoring

---

## Test Infrastructure

### Directory Structure
```
SpinRender/
├── tests/
│   ├── unit/              # Unit tests (most tests go here)
│   │   ├── test_*.py
│   │   └── conftest.py   # Shared fixtures, mocks
│   ├── integration/      # Integration tests (optional)
│   └── fixtures/         # Test data, sample boards, etc.
```

### Dependencies
Install from `pyproject.toml`:
```bash
pip install pytest pytest-cov pytest-mock
```

### pytest.ini (Project Root)
```ini
[pytest]
testpaths = tests
addopts = --cov=SpinRender --cov-report=term-missing --cov-fail-under=80
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

---

## Mock Strategy

SpinRender uses `wxPython` for GUI. Unit tests must **not** create actual windows.

### Mocking wx Module
`tests/conftest.py` provides fixtures that mock wx:

```python
import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture(autouse=True)
def mock_wx():
    """Mock wx module for all tests."""
    with patch('wx.__init__') as mock_wx_init, \
         patch('wx.Frame'), \
         patch('wx.Panel'), \
         patch('wx.Slider'), \
         patch('wx.StaticText'), \
         patch('wx.Button'):
        yield mock_wx_init
```

**Key Points**:
- Patch at import time if needed
- Use `MagicMock` for complex interactions
- Verify method calls, not GUI states

### Mocking Subprocess (Renderer Tests)
The renderer calls `kicad-cli` subprocesses. Mock with `subprocess.run`:

```python
from unittest.mock import patch, MagicMock

def test_renderer_calls_kicad_cli():
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=b"", stderr=b"")
        renderer.render_frame(settings, board_path)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert 'kicad-cli' in args[0]
        assert 'pcb' in args[1]
```

---

## Running Tests

### All Tests with Coverage
```bash
pytest --cov=SpinRender --cov-report=html --cov-report=term
```

### Single Test File
```bash
pytest tests/unit/test_theme.py -v
```

### Single Test Function
```bash
pytest tests/unit/test_theme.py::test_color_resolution -v
```

### Coverage Report
Generated in `htmlcov/index.html` (open in browser).

**Goal**: Maintain ≥80% coverage. New code must have tests.

---

## KiCad CLI Integration

SpinRender invokes KiCad's command-line interface for rendering and 3D export.

### Commands Used
- **Render**: `kicad-cli pcb render`
- **3D Export**: `kicad-cli pcb export glb`

### Render Options (Current Usage)
```bash
kicad-cli pcb render \
  --rotate "$rotation" \
  --perspective "$perspective" \
  --zoom "$zoom" \
  --background transparent \
  --quality user \
  -w "$width" -h "$height" \
  --light-top "$top_rgb" \
  --light-bottom "$bottom_rgb" \
  --light-side "$side_rgb" \
  --light-camera "$camera_rgb" \
  --light-side-elevation "$side_elevation" \
  -o "$output_file"
```

### 3D Export Options (for preview loading)
```bash
kicad-cli pcb export glb \
  --fuse-shapes \
  --grid-origin \
  --no-dnp \
  --subst-models \
  --include-pads \
  --include-silkscreen \
  --output "$output_file"
```

### Important Notes
- SpinRender sets `KICAD_CONFIG_HOME` to `resources/kicad_config` to use shipped action configs
- Final video/GIF compositing happens in `ffmpeg`; KiCad renders to transparent background
- Manual CLI overrides (if exposed to user) are appended with simple whitespace splitting **without sanitization** - future validation recommended
- All lighting colors are RGB hex (e.g., `#ffffff`)

---

## Rotation Coordinate System

Camera rotation uses a "universal joint" model.

### Adjustment Parameters
- `spin_tilt` - angle around Y axis (horizontal orbit)
- `spin_yaw` - rotation around view axis (optional twist)
- `board_roll` - board rotation around board Z axis

### Built-In Presets
The renderer supports named camera paths:
- ` cinematic_spin`: Full 360° horizontal orbit, slight elevation
- `low_angle`: Low camera angle (15°), dramatic shadows
- `top_down`: Overhead view (90° elevation), straight down
- `orbit_loop`: Continuous orbit with smooth acceleration

### Render-Side Rotation Mapping
SpinRender computes rotation from orbit parameters:

```
Rotation = (
  spin_tilt * r_spin,    # Primary horizontal rotation
  board_roll * r_z,      # Board Z rotation
  spin_yaw * r_x,        # Camera twist
)
```

Where `r_spin`, `r_z`, `r_x` are per-preset multipliers.

---

## Development Workflow

1. **Write test first** (RED) - describe expected behavior
2. **Run test** - confirm it fails
3. **Implement minimal code** (GREEN) - make test pass
4. **Refactor** (IMPROVE) - clean up, maintain coverage
5. **Run all tests** - ensure no regressions
6. **Commit** - with clear message

---

## Environment Setup

### Local Development
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -e .

# Install test deps
pip install pytest pytest-cov pytest-mock

# Run tests
pytest --cov=SpinRender
```

### KiCad Plugin Installation
```bash
# Run installer (sets up user site-packages and KiCad config)
./install.sh      # Linux/macOS
install.bat       # Windows
```

---

## Getting Help

- **Architecture questions**: See `docs/CODEMAPS/`
- **Theme system**: See `docs/reference/theme-schema.md`
- **Locale strings**: See `docs/reference/locale-schema.md`
- **Historical context**: Check `docs/archive/` for old PRDs and plans

---

**Maintainers**: See `CONTRIBUTING.md` for contribution guidelines.
