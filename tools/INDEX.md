# Tools

Developer tooling for SpinRender. Run Python scripts with KiCad's bundled
interpreter (`C:\Program Files\KiCad\10.0\bin\python.exe` on Windows) so the
wxPython build matches what the plugin runs against.

## Theme validation

| File | Purpose |
| :--- | :--- |
| `validate_theme.py` | CLI entry point: scans Python sources for theme-token references, compares them against a theme YAML, and can auto-fix discrepancies. |
| `theme_validator/` | Package backing `validate_theme.py` — `scanner.py` (extract token references from code), `yaml_parser.py` (parse theme YAML), `comparator.py` (diff code vs theme), `fixer.py` (apply fixes), `__main__.py` (module entry: `python -m theme_validator`). |

## Visual debugging (`visual_debug/`)

Scripts for verifying UI changes outside KiCad — no relaunch loop needed.

| File | Purpose |
| :--- | :--- |
| `visual_debug/smoke_controls.py` | Constructs and paints every custom control (sliders, toggles, inputs, …). Catches constructor/attribute-order bugs and paint-handler exceptions in one pass. |
| `visual_debug/smoke_dialogs.py` | Constructs every styled dialog (About, RecallPreset, AdvancedOptions, Message). Catches constructor errors and sizer assertions. |
| `visual_debug/measure_about.py` | Prints the About dialog's layout tree (pos/size/best-size/bg per panel) for diagnosing clipping and sizer-squeeze issues. |
| `visual_debug/render_about.py` | Renders the About dialog per-monitor-DPI-aware (matching KiCad) and screenshots it to `about_render.png` for pixel-level verification. |

## Crash-dump analysis

One-off forensics from debugging native KiCad crashes (wx paint-handler DC
leaks). Kept for the next time a minidump needs reading without symbols.

| File | Purpose |
| :--- | :--- |
| `analyze_dump.py` | Walks a KiCad crash minidump's faulting-thread stack and resolves raw values to module+offset to identify the crashing module without symbols. |
| `analyze_dump2.py` | Deep-dive variant: reads the exception stream's own CONTEXT record and maps stack hits to the nearest exported symbol via each DLL's export table. |
| `disasm_caller.py` | Disassembles a wxmsw DLL around a faulting offset (pefile + capstone) to find the failing indirect call. |
| `near_exports.py` | Lists exports of the wxmsw core DLL nearest a faulting return address to name the crash site. |
| `apply_paint_guard.py` | One-shot codemod that inserted `@guarded_paint` above every paint handler creating a paint DC (already applied; kept for reference). |
