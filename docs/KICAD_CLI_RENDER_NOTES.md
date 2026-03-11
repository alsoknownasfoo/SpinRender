# KiCad CLI Render Notes

This document captures practical behavior of `kicad-cli pcb render` observed during SpinRender integration.

## Verified Behavior (KiCad on macOS, 2026-03-06)

Command tested:
- `kicad-cli pcb render --help`

Key options in use:
- `--output`
- `--width`, `--height`
- `--side`
- `--background`
- `--quality`
- `--floor`, `--perspective`
- `--zoom`
- `--pivot`
- `--rotate`
- `--light-side`, `--light-side-elevation`

## Important Parser Quirk

On this KiCad build, negative vector values for `--pivot` (and related vector args) can be parsed as unknown arguments.

Example that fails:
- `--pivot=-10.0,2.0,0.0`

Observed error:
- `Unknown argument: -10.0,2.0,0.0`

Example that parses (then fails later only because test input file is missing):
- `--pivot=10.0,2.0,0.0`

## SpinRender Mitigation

SpinRender uses a tilted-loop model and emits render-safe vectors by default:
- `--pivot=0.0000,0.0000,0.0000`
- `--rotate=<tilt>,<loop_angle>,0.0000` with non-negative tilt range

Legacy or manual CLI override tokens that are standalone vector literals are sanitized before command execution.

## Why this doc exists

This is intentionally in-repo so future work does not rely on ephemeral chat context.
