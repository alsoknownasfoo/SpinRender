<!-- Generated: 2026-03-13 | Files scanned: 3 | Token estimate: ~700 -->
# Frontend (UI) Codemap

## Entry Point
`SpinRender/ui/main_panel.py` → `SpinRenderPanel(wx.Panel)` — 1,542 lines

## Panel Layout
```
SpinRenderPanel
├── Header
│   └── SVGLogoPanel + title label
├── Left Panel (Controls)
│   ├── Preset Section
│   │   └── PresetCard grid (load/save presets)
│   ├── Parameters Section
│   │   ├── board_tilt  → CustomSlider + CustomInput (-90..90)
│   │   ├── board_roll  → CustomSlider + CustomInput (-180..180)
│   │   ├── spin_tilt   → CustomSlider + CustomInput (-90..90)
│   │   └── period      → CustomSlider (animation duration)
│   │   └── direction   → CustomToggleButton (ccw|cw)
│   ├── Lighting        → CustomDropdown (studio|outdoor|warm|cool)
│   ├── Output Settings
│   │   ├── format      → CustomDropdown (mp4|gif|png_sequence)
│   │   ├── resolution  → CustomDropdown (720|1080|1440)
│   │   └── frame_rate  → CustomDropdown (24|30|60)
│   └── Export
│       └── Render / Cancel buttons
└── Right Panel (Preview)
    ├── GLPreviewRenderer (live OpenGL 3D canvas)
    └── Overlay (status, playback controls)
```

## Key UI Files

| File | Lines | Purpose |
|------|-------|---------|
| `ui/main_panel.py` | 1,542 | Main panel, event handlers, 20+ builder methods |
| `ui/custom_controls.py` | 1,465 | Reusable control classes |
| `ui/dialogs.py` | 473 | File/settings dialogs |

## Custom Controls (`custom_controls.py`)

| Class | Purpose |
|-------|---------|
| `CustomSlider` | Range slider with live numeric display |
| `CustomToggleButton` | 2-option toggle (ccw/cw, etc.) |
| `CustomDropdown` + `DropdownPopup` | Styled dropdown selector |
| `CustomButton` | Styled button (primary/ghost/danger) |
| `PresetCard` | Clickable preset card |
| `NumericDisplay` | Read-only number label |
| `NumericInput` | Validated number input field |

## State Management
- Settings stored as Python `dict` in `SpinRenderPanel`
- Live preview triggered on any param change via `update_preview()`
- Presets saved/loaded via `PresetManager` (JSON files)
- Background color stored as hex string (e.g., `"#000000"`)
