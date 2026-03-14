# SpinRender UI Refactor — TDD Plan

**Status:** Pre-implementation planning
**Coverage Target:** 80% minimum (lines + branches + functions)
**Current Coverage:** 0% (no tests exist)
**Test Framework:** pytest + pytest-cov (no wx required for unit tests via mocking)

---

## Overview

The UI refactor introduces a centralized theme system to replace hardcoded colors scattered
across `custom_controls.py`, `main_panel.py`, and `dialogs.py`. This plan defines the test
structure, mocking strategy, and coverage targets for that work.

---

## Test Infrastructure

### Directory Structure

```
SpinRender/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures and wx mock setup
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_theme.py        # Theme token resolution
│   │   ├── test_custom_controls.py  # Control logic (no rendering)
│   │   ├── test_presets.py      # Preset manager
│   │   ├── test_renderer.py     # Render engine (subprocess mocked)
│   │   └── test_logger.py       # Logger
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_theme_application.py   # Theme applied to controls
│   │   ├── test_panel_construction.py  # Panel builds without wx display
│   │   └── test_preset_roundtrip.py    # Save/load cycle
│   └── fixtures/
│       ├── sample_preset.json
│       └── theme_overrides.json
```

### Dependencies

```
pytest>=7.0
pytest-cov>=4.0
pytest-mock>=3.10    # mocker fixture
```

### pytest.ini (project root)

```ini
[pytest]
testpaths = SpinRender/tests
addopts = --cov=SpinRender --cov-report=term-missing --cov-fail-under=80
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

---

## Mock Strategy

### wx Module Mock (conftest.py)

wx is not available in CI/headless environments. All unit tests must mock it at import time:

```python
# conftest.py
import sys
from unittest.mock import MagicMock, patch

# Build a minimal wx stub before any SpinRender import
wx_mock = MagicMock()
wx_mock.Panel = object          # base class for inheritance
wx_mock.Colour = lambda r,g,b: (r, g, b)
wx_mock.Brush = MagicMock()
wx_mock.Pen = MagicMock()
wx_mock.Font = MagicMock()
wx_mock.DC = MagicMock()
wx_mock.EVT_PAINT = MagicMock()
wx_mock.EVT_LEFT_DOWN = MagicMock()
wx_mock.EVT_LEFT_UP = MagicMock()
wx_mock.EVT_MOTION = MagicMock()

sys.modules['wx'] = wx_mock
sys.modules['pcbnew'] = MagicMock()

@pytest.fixture
def mock_wx():
    return wx_mock
```

### Subprocess Mock (renderer tests)

```python
@pytest.fixture
def mock_subprocess(mocker):
    return mocker.patch('subprocess.run', return_value=MagicMock(returncode=0, stdout=''))
```

### Filesystem Mock (preset tests)

```python
@pytest.fixture
def tmp_preset_dir(tmp_path):
    preset_dir = tmp_path / '.spinrender' / 'presets'
    preset_dir.mkdir(parents=True)
    return preset_dir
```

---

## Unit Tests

### 1. Theme System (`test_theme.py`)

The new `SpinRender/ui/theme.py` module is the core deliverable. Tests define its contract.

#### Token Resolution

```python
class TestThemeTokens:
    def test_all_required_tokens_present(self):
        """Theme must expose every color token used in the UI."""
        from SpinRender.ui.theme import Theme
        required = [
            'BG_PAGE', 'BG_PANEL', 'BG_INPUT', 'BG_SURFACE', 'BG_MODAL',
            'TEXT_PRIMARY', 'TEXT_SECONDARY', 'TEXT_MUTED',
            'ACCENT_CYAN', 'ACCENT_YELLOW', 'ACCENT_GREEN', 'ACCENT_ORANGE',
            'BORDER_DEFAULT',
        ]
        theme = Theme()
        for token in required:
            assert hasattr(theme, token), f"Missing token: {token}"

    def test_default_dark_theme_values(self):
        from SpinRender.ui.theme import Theme, DARK_THEME
        theme = Theme(DARK_THEME)
        assert theme.BG_PAGE == (18, 18, 18)
        assert theme.ACCENT_CYAN == (0, 188, 212)
        assert theme.ACCENT_ORANGE == (255, 107, 53)

    def test_token_returns_rgb_tuple(self):
        from SpinRender.ui.theme import Theme, DARK_THEME
        theme = Theme(DARK_THEME)
        color = theme.BG_PANEL
        assert isinstance(color, tuple)
        assert len(color) == 3
        assert all(0 <= c <= 255 for c in color)

    def test_theme_is_immutable(self):
        """Theme tokens must not be mutated after construction."""
        from SpinRender.ui.theme import Theme, DARK_THEME
        theme = Theme(DARK_THEME)
        with pytest.raises((AttributeError, TypeError)):
            theme.BG_PAGE = (0, 0, 0)
```

#### Theme Overrides

```python
class TestThemeOverrides:
    def test_custom_override_replaces_token(self):
        from SpinRender.ui.theme import Theme, DARK_THEME
        overrides = {'ACCENT_CYAN': (255, 0, 128)}
        theme = Theme(DARK_THEME, overrides=overrides)
        assert theme.ACCENT_CYAN == (255, 0, 128)

    def test_override_does_not_affect_other_tokens(self):
        from SpinRender.ui.theme import Theme, DARK_THEME
        overrides = {'ACCENT_CYAN': (255, 0, 128)}
        theme = Theme(DARK_THEME, overrides=overrides)
        assert theme.BG_PAGE == (18, 18, 18)

    def test_invalid_override_key_raises(self):
        from SpinRender.ui.theme import Theme, DARK_THEME
        with pytest.raises(KeyError):
            Theme(DARK_THEME, overrides={'NONEXISTENT_TOKEN': (0, 0, 0)})

    def test_invalid_rgb_value_raises(self):
        from SpinRender.ui.theme import Theme, DARK_THEME
        with pytest.raises(ValueError):
            Theme(DARK_THEME, overrides={'ACCENT_CYAN': (256, 0, 0)})

    def test_override_from_dict_roundtrip(self):
        from SpinRender.ui.theme import Theme, DARK_THEME
        data = {'ACCENT_CYAN': [0, 100, 200]}  # JSON uses lists
        theme = Theme(DARK_THEME, overrides=data)
        assert theme.ACCENT_CYAN == (0, 100, 200)
```

#### Color Resolution Helpers

```python
class TestColorHelpers:
    def test_to_wx_colour_returns_correct_type(self, mock_wx):
        from SpinRender.ui.theme import Theme, DARK_THEME
        theme = Theme(DARK_THEME)
        result = theme.to_wx_colour('ACCENT_CYAN')
        mock_wx.Colour.assert_called_once_with(0, 188, 212)

    def test_with_alpha_blends_on_background(self):
        from SpinRender.ui.theme import blend_alpha
        # blend_alpha(color, alpha, bg) → RGB
        result = blend_alpha((0, 188, 212), 0.5, (18, 18, 18))
        assert result == (9, 103, 115)  # floor((0+18)*0.5, (188+18)*0.5, ...)

    def test_disabled_alpha_returns_muted_color(self):
        from SpinRender.ui.theme import Theme, DARK_THEME
        theme = Theme(DARK_THEME)
        color = theme.ACCENT_CYAN
        muted = theme.disabled(color)
        # Disabled = 40% opacity blended onto BG_PANEL
        assert muted != color
        for c in muted:
            assert 0 <= c <= 255
```

---

### 2. Custom Controls (`test_custom_controls.py`)

Tests focus on **logic** (values, state transitions) not painting (mocked).

#### CustomSlider

```python
class TestCustomSlider:
    @pytest.fixture
    def slider(self, mock_wx):
        from SpinRender.ui.custom_controls import CustomSlider
        parent = MagicMock()
        return CustomSlider(parent, min_val=0, max_val=100, value=50)

    def test_get_value_returns_initial_value(self, slider):
        assert slider.GetValue() == 50

    def test_set_value_clamps_to_min(self, slider):
        slider.SetValue(-10)
        assert slider.GetValue() == 0

    def test_set_value_clamps_to_max(self, slider):
        slider.SetValue(200)
        assert slider.GetValue() == 100

    def test_set_value_midpoint(self, slider):
        slider.SetValue(75)
        assert slider.GetValue() == 75

    def test_value_fraction_at_min(self, slider):
        slider.SetValue(0)
        assert slider._value_fraction() == pytest.approx(0.0)

    def test_value_fraction_at_max(self, slider):
        slider.SetValue(100)
        assert slider._value_fraction() == pytest.approx(1.0)

    def test_value_fraction_midpoint(self, slider):
        slider.SetValue(50)
        assert slider._value_fraction() == pytest.approx(0.5)

    def test_drag_updates_value_from_position(self, slider):
        """Simulate mouse drag: position maps to value."""
        slider._track_rect = MagicMock()
        slider._track_rect.x = 0
        slider._track_rect.width = 200
        slider._on_drag(position_x=100)  # midpoint → value 50
        assert slider.GetValue() == 50

    def test_disabled_state_prevents_drag(self, slider):
        slider.Enable(False)
        original = slider.GetValue()
        slider._on_drag(position_x=0)
        assert slider.GetValue() == original
```

#### CustomToggleButton

```python
class TestCustomToggleButton:
    @pytest.fixture
    def toggle(self, mock_wx):
        from SpinRender.ui.custom_controls import CustomToggleButton
        parent = MagicMock()
        return CustomToggleButton(parent, options=['CCW', 'CW'], selected=0)

    def test_initial_selection(self, toggle):
        assert toggle.GetValue() == 0

    def test_set_value_changes_selection(self, toggle):
        toggle.SetValue(1)
        assert toggle.GetValue() == 1

    def test_set_value_invalid_index_raises(self, toggle):
        with pytest.raises((ValueError, IndexError)):
            toggle.SetValue(5)

    def test_toggle_cycles_on_click(self, toggle):
        toggle._on_click(option_index=1)
        assert toggle.GetValue() == 1
        toggle._on_click(option_index=0)
        assert toggle.GetValue() == 0
```

#### CustomDropdown

```python
class TestCustomDropdown:
    @pytest.fixture
    def dropdown(self, mock_wx):
        from SpinRender.ui.custom_controls import CustomDropdown
        parent = MagicMock()
        return CustomDropdown(parent, choices=['Studio', 'Key', 'Fill'], selected=0)

    def test_get_value_returns_initial(self, dropdown):
        assert dropdown.GetValue() == 'Studio'

    def test_set_selection_by_index(self, dropdown):
        dropdown.SetSelection(2)
        assert dropdown.GetValue() == 'Fill'

    def test_set_selection_out_of_range_raises(self, dropdown):
        with pytest.raises((ValueError, IndexError)):
            dropdown.SetSelection(99)

    def test_get_selection_returns_index(self, dropdown):
        dropdown.SetSelection(1)
        assert dropdown.GetSelection() == 1
```

#### CustomButton

```python
class TestCustomButton:
    @pytest.fixture
    def button(self, mock_wx):
        from SpinRender.ui.custom_controls import CustomButton
        parent = MagicMock()
        return CustomButton(parent, label='Render', style='primary')

    def test_label_accessible(self, button):
        assert button.GetLabel() == 'Render'

    def test_disabled_state(self, button):
        button.Enable(False)
        assert not button.IsEnabled()

    def test_enabled_state_default(self, button):
        assert button.IsEnabled()

    def test_style_primary(self, button):
        assert button._style == 'primary'

    def test_style_danger_changes_colors(self, mock_wx):
        from SpinRender.ui.custom_controls import CustomButton
        parent = MagicMock()
        btn = CustomButton(parent, label='Delete', style='danger')
        assert btn._style == 'danger'
```

---

### 3. Theme Application to Controls (`test_theme_application.py`)

Integration tests: theme tokens flow into controls at construction time.

```python
class TestThemeApplicationToControls:
    def test_slider_uses_theme_accent_color(self, mock_wx):
        from SpinRender.ui.theme import Theme, DARK_THEME
        from SpinRender.ui.custom_controls import CustomSlider
        theme = Theme(DARK_THEME)
        parent = MagicMock()
        slider = CustomSlider(parent, min_val=0, max_val=100, value=50, theme=theme)
        assert slider._fill_color == theme.ACCENT_CYAN

    def test_slider_uses_theme_track_color(self, mock_wx):
        from SpinRender.ui.theme import Theme, DARK_THEME
        from SpinRender.ui.custom_controls import CustomSlider
        theme = Theme(DARK_THEME)
        parent = MagicMock()
        slider = CustomSlider(parent, min_val=0, max_val=100, value=50, theme=theme)
        assert slider._track_color == theme.BG_SURFACE

    def test_button_primary_uses_accent_cyan(self, mock_wx):
        from SpinRender.ui.theme import Theme, DARK_THEME
        from SpinRender.ui.custom_controls import CustomButton
        theme = Theme(DARK_THEME)
        parent = MagicMock()
        btn = CustomButton(parent, label='Go', style='primary', theme=theme)
        assert btn._bg_color == theme.ACCENT_CYAN

    def test_button_danger_uses_accent_orange(self, mock_wx):
        from SpinRender.ui.theme import Theme, DARK_THEME
        from SpinRender.ui.custom_controls import CustomButton
        theme = Theme(DARK_THEME)
        parent = MagicMock()
        btn = CustomButton(parent, label='Delete', style='danger', theme=theme)
        assert btn._bg_color == theme.ACCENT_ORANGE

    def test_custom_override_propagates_to_slider(self, mock_wx):
        from SpinRender.ui.theme import Theme, DARK_THEME
        from SpinRender.ui.custom_controls import CustomSlider
        custom_cyan = (100, 200, 100)
        theme = Theme(DARK_THEME, overrides={'ACCENT_CYAN': custom_cyan})
        parent = MagicMock()
        slider = CustomSlider(parent, min_val=0, max_val=100, value=0, theme=theme)
        assert slider._fill_color == custom_cyan

    def test_all_controls_accept_theme_parameter(self, mock_wx):
        from SpinRender.ui.theme import Theme, DARK_THEME
        import SpinRender.ui.custom_controls as cc
        theme = Theme(DARK_THEME)
        parent = MagicMock()
        # None of these should raise TypeError for unexpected keyword
        cc.CustomSlider(parent, min_val=0, max_val=100, value=0, theme=theme)
        cc.CustomToggleButton(parent, options=['A', 'B'], selected=0, theme=theme)
        cc.CustomDropdown(parent, choices=['X'], selected=0, theme=theme)
        cc.CustomButton(parent, label='L', style='primary', theme=theme)
```

---

### 4. Panel Construction (`test_panel_construction.py`)

Verify panel can be constructed and settings round-trip without a display.

```python
class TestPanelConstruction:
    def test_panel_builds_without_exception(self, mock_wx):
        from SpinRender.ui.main_panel import SpinRenderPanel
        parent = MagicMock()
        panel = SpinRenderPanel(parent, board_path='/fake/board.kicad_pcb')
        assert panel is not None

    def test_panel_exposes_settings_dict(self, mock_wx):
        from SpinRender.ui.main_panel import SpinRenderPanel
        parent = MagicMock()
        panel = SpinRenderPanel(parent, board_path='/fake/board.kicad_pcb')
        settings = panel.get_settings()
        assert isinstance(settings, dict)

    def test_default_settings_have_required_keys(self, mock_wx):
        from SpinRender.ui.main_panel import SpinRenderPanel
        parent = MagicMock()
        panel = SpinRenderPanel(parent, board_path='/fake/board.kicad_pcb')
        settings = panel.get_settings()
        required_keys = [
            'preset', 'board_tilt', 'board_roll', 'spin_tilt', 'spin_heading',
            'period', 'direction', 'lighting', 'format', 'resolution',
            'bg_color', 'render_mode',
        ]
        for key in required_keys:
            assert key in settings, f"Missing settings key: {key}"

    def test_panel_uses_theme(self, mock_wx):
        from SpinRender.ui.main_panel import SpinRenderPanel
        from SpinRender.ui.theme import Theme
        parent = MagicMock()
        panel = SpinRenderPanel(parent, board_path='/fake/board.kicad_pcb')
        assert isinstance(panel.theme, Theme)

    def test_controls_disabled_during_render(self, mock_wx):
        from SpinRender.ui.main_panel import SpinRenderPanel
        parent = MagicMock()
        panel = SpinRenderPanel(parent, board_path='/fake/board.kicad_pcb')
        panel.enable_left_panel_controls(False)
        # Controls container should be disabled
        # (panel.left_panel.IsEnabled() == False)
        assert not panel._controls_enabled
```

---

### 5. Preset Manager (`test_presets.py`)

```python
class TestPresetManager:
    @pytest.fixture
    def preset_mgr(self, tmp_preset_dir):
        from SpinRender.core.presets import PresetManager
        return PresetManager(global_dir=tmp_preset_dir)

    def test_save_and_load_preset(self, preset_mgr):
        settings = {'board_tilt': 30, 'format': 'gif', 'preset': 'hero'}
        preset_mgr.save_preset('my_preset', settings)
        loaded = preset_mgr.load_preset('my_preset')
        assert loaded == settings

    def test_list_presets_returns_saved(self, preset_mgr):
        preset_mgr.save_preset('alpha', {})
        preset_mgr.save_preset('beta', {})
        names = preset_mgr.list_presets()
        assert 'alpha' in names
        assert 'beta' in names

    def test_overwrite_preset(self, preset_mgr):
        preset_mgr.save_preset('p', {'val': 1})
        preset_mgr.save_preset('p', {'val': 2})
        assert preset_mgr.load_preset('p')['val'] == 2

    def test_load_nonexistent_raises(self, preset_mgr):
        with pytest.raises(KeyError):
            preset_mgr.load_preset('does_not_exist')

    def test_delete_preset(self, preset_mgr):
        preset_mgr.save_preset('removeme', {})
        preset_mgr.delete_preset('removeme')
        assert 'removeme' not in preset_mgr.list_presets()

    def test_last_used_settings_roundtrip(self, preset_mgr):
        settings = {'board_tilt': 45}
        preset_mgr.save_last_used_settings(settings)
        loaded = preset_mgr.get_last_used_settings()
        assert loaded['board_tilt'] == 45

    def test_preset_json_is_valid_on_disk(self, preset_mgr, tmp_preset_dir):
        import json
        settings = {'format': 'mp4', 'resolution': '1080p'}
        preset_mgr.save_preset('disk_test', settings)
        preset_file = tmp_preset_dir / 'disk_test.json'
        assert preset_file.exists()
        data = json.loads(preset_file.read_text())
        assert data['settings'] == settings
```

---

### 6. Renderer (`test_renderer.py`)

```python
class TestRenderEngine:
    @pytest.fixture
    def engine(self, tmp_path):
        from SpinRender.core.renderer import RenderEngine
        return RenderEngine(output_dir=str(tmp_path))

    def test_rotation_args_hero_preset(self, engine):
        args = engine._build_rotation_args(board_tilt=30, board_roll=0,
                                            spin_tilt=15, spin_heading=0)
        assert '--rotate' in args

    def test_rotation_args_return_list(self, engine):
        args = engine._build_rotation_args(board_tilt=0, board_roll=0,
                                            spin_tilt=0, spin_heading=0)
        assert isinstance(args, list)

    def test_cancel_sets_flag(self, engine):
        engine.cancel()
        assert engine._cancelled

    def test_render_calls_subprocess(self, engine, mock_subprocess):
        settings = {
            'board_tilt': 0, 'board_roll': 0, 'spin_tilt': 0,
            'spin_heading': 0, 'period': 3.0, 'format': 'gif',
            'resolution': '720p', 'lighting': 'studio',
        }
        engine.render('/fake/board.kicad_pcb', settings, progress_cb=lambda p, m: None)
        assert mock_subprocess.called

    def test_render_calls_progress_callback(self, engine, mock_subprocess):
        calls = []
        settings = {
            'board_tilt': 0, 'board_roll': 0, 'spin_tilt': 0,
            'spin_heading': 0, 'period': 3.0, 'format': 'gif',
            'resolution': '720p', 'lighting': 'studio',
        }
        engine.render('/fake/board.kicad_pcb', settings, progress_cb=lambda p, m: calls.append(p))
        assert len(calls) > 0

    def test_subprocess_failure_raises(self, engine, mocker):
        mocker.patch('subprocess.run', return_value=MagicMock(returncode=1, stderr='error'))
        settings = {
            'board_tilt': 0, 'board_roll': 0, 'spin_tilt': 0,
            'spin_heading': 0, 'period': 3.0, 'format': 'gif',
            'resolution': '720p', 'lighting': 'studio',
        }
        with pytest.raises(RuntimeError):
            engine.render('/fake/board.kicad_pcb', settings, progress_cb=lambda p, m: None)
```

---

### 7. Logger (`test_logger.py`)

```python
class TestSpinLogger:
    def test_off_level_logs_nothing(self, tmp_path):
        from SpinRender.utils.logger import SpinLogger
        log = SpinLogger(level='off', log_dir=str(tmp_path))
        log.info('should not appear')
        log.debug('should not appear')
        assert list(tmp_path.glob('*.log')) == []

    def test_simple_level_logs_info(self, tmp_path):
        from SpinRender.utils.logger import SpinLogger
        log = SpinLogger(level='simple', log_dir=str(tmp_path))
        log.info('hello')
        files = list(tmp_path.glob('*.log'))
        assert len(files) == 1
        assert 'hello' in files[0].read_text()

    def test_simple_level_suppresses_debug(self, tmp_path):
        from SpinRender.utils.logger import SpinLogger
        log = SpinLogger(level='simple', log_dir=str(tmp_path))
        log.debug('hidden')
        content = list(tmp_path.glob('*.log'))[0].read_text() if list(tmp_path.glob('*.log')) else ''
        assert 'hidden' not in content

    def test_verbose_level_logs_debug(self, tmp_path):
        from SpinRender.utils.logger import SpinLogger
        log = SpinLogger(level='verbose', log_dir=str(tmp_path))
        log.debug('visible')
        files = list(tmp_path.glob('*.log'))
        assert 'visible' in files[0].read_text()

    def test_log_file_named_with_date(self, tmp_path):
        import datetime
        from SpinRender.utils.logger import SpinLogger
        log = SpinLogger(level='simple', log_dir=str(tmp_path))
        log.info('x')
        today = datetime.date.today().strftime('%Y-%m-%d')
        files = list(tmp_path.glob('*.log'))
        assert any(today in f.name for f in files)
```

---

## Preset Roundtrip Integration (`test_preset_roundtrip.py`)

```python
class TestPresetRoundtrip:
    def test_full_settings_roundtrip(self, tmp_preset_dir):
        from SpinRender.core.presets import PresetManager
        mgr = PresetManager(global_dir=tmp_preset_dir)
        full_settings = {
            'preset': 'hero', 'board_tilt': 30, 'board_roll': -10,
            'spin_tilt': 15, 'spin_heading': 45, 'period': 4.0,
            'direction': 'CCW', 'lighting': 'studio', 'format': 'mp4',
            'resolution': '1080p', 'bg_color': (18, 18, 18),
            'render_mode': 'full', 'cli_overrides': '--aa 4',
        }
        mgr.save_preset('full_test', full_settings)
        loaded = mgr.load_preset('full_test')
        assert loaded == full_settings
```

---

## Coverage Targets by Module

| Module | Target | Notes |
|--------|--------|-------|
| `ui/theme.py` (new) | **95%** | Core deliverable — fully tested |
| `ui/custom_controls.py` | **80%** | Logic only; painting excluded via mock |
| `ui/main_panel.py` | **70%** | Construction + settings; rendering excluded |
| `ui/dialogs.py` | **70%** | Construction + input validation |
| `core/presets.py` | **90%** | Pure data logic, easy to test |
| `core/renderer.py` | **75%** | Subprocess mocked; arg building tested |
| `utils/logger.py` | **85%** | Straightforward I/O |
| **Overall** | **≥80%** | Enforced by `--cov-fail-under=80` |

---

## Test Execution Order

### Phase 1 — Before Any Refactoring (Establish Baseline)

```bash
cd /path/to/SpinRender_claude
pip install pytest pytest-cov pytest-mock
pytest SpinRender/tests/unit/test_presets.py -v   # Should pass now (pure logic)
pytest SpinRender/tests/unit/test_logger.py -v    # Should pass now (pure I/O)
```

Expected: ~15 tests pass, ~0% UI coverage (theme doesn't exist yet).

### Phase 2 — Write Theme Tests First (RED)

```bash
pytest SpinRender/tests/unit/test_theme.py -v
# EXPECTED: All FAIL (ImportError — ui/theme.py doesn't exist)
```

### Phase 3 — Implement theme.py (GREEN)

Implement `SpinRender/ui/theme.py` to pass Phase 2 tests.

```bash
pytest SpinRender/tests/unit/test_theme.py -v
# EXPECTED: All pass
```

### Phase 4 — Write Control Tests (RED)

```bash
pytest SpinRender/tests/unit/test_custom_controls.py -v
# Some fail if controls don't accept theme= kwarg yet
```

### Phase 5 — Refactor Controls to Accept Theme (GREEN)

Update controls to accept optional `theme=` parameter.

```bash
pytest SpinRender/tests/unit/test_custom_controls.py -v
pytest SpinRender/tests/integration/test_theme_application.py -v
# EXPECTED: All pass
```

### Phase 6 — Full Suite + Coverage

```bash
pytest --cov=SpinRender --cov-report=html
# EXPECTED: ≥80% coverage, all tests green
```

---

## What Is Explicitly NOT Tested

| Excluded | Reason |
|----------|--------|
| `wx.DC` painting calls | Requires display; mock would test nothing real |
| OpenGL preview rendering | Requires GPU + OpenGL context |
| KiCad CLI integration | Requires KiCad installation; tested in manual QA |
| Font loading from disk | Platform-specific; tested in manual QA |
| wxPython event loop | Requires wx.App; not unit-testable |

---

## CI Integration

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install pytest pytest-cov pytest-mock
      - run: pytest --cov=SpinRender --cov-fail-under=80
```

---

## Implementation Notes for Refactor

1. **Start with `theme.py`** — tests define the contract; implementation follows
2. **Controls get `theme=None`** — default `None` falls back to `DARK_THEME` for backwards compatibility
3. **No behavioral changes** — only color sourcing changes; GetValue/SetValue semantics unchanged
4. **One color source of truth** — every hex literal in `custom_controls.py`, `main_panel.py`, `dialogs.py` becomes a `theme.TOKEN` reference
5. **Painting functions stay mocked** — tests verify _what_ color is stored, not _how_ it's drawn
