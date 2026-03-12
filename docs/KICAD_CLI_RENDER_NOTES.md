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
- `--perspective`
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

## Rotation Coordinate System (Universal Joint Model)

**Verified through test renders (2026-03-11)**

SpinRender uses a "Universal Joint" model to provide full 360° freedom for any rotation style (spin, roll, tumble) without axis redundancy or gimbal lock.

### Adjustment Parameters

1.  **BOARD TILT**: Sets the angle at which the board is "mounted" to the rotation axis.
    *   *0°*: Board is flat on the axis (spins like a record).
    *   *90°*: Board is standing straight up on the axis (spins like a coin).
2.  **SPIN TILT**: Tilts the entire rotation axis itself from Vertical to Horizontal.
    *   *0°*: Turntable spin (Vertical axis).
    *   *90°*: Somersault/Roll (Horizontal axis).
3.  **SPIN HEADING**: Rotates the *direction* of the axis tilt around the table.
    *   Lets you choose if a "roll" comes towards the camera, goes sideways, or moves diagonally.

### Common Scenarios

| Scenario | BOARD TILT | SPIN TILT | SPIN HEADING | Result |
| :--- | :--- | :--- | :--- | :--- |
| **Hero Orbit** | **45°** | **0°** | *Irrelevant* | Spun on a vertical axis, board leaning back at 45°. |
| **Standard Spin** | **90°** | **0°** | *Irrelevant* | Spun on a vertical axis, board standing straight up (spinning L-to-R). |
| **Somersault/Roll** | **0°** | **90°** | **0°** | Horizontal axis (L-to-R), board flat on it, rolling towards camera. |

### Technical Implementation (Preview)

The 3D preview applies transformations in this order:

1.  **Spin Animation**: Rotation around the dynamic axis defined by **Spin Tilt** and **Spin Heading**.
2.  **Board Tilt**: Static leaning of the board relative to that axis.

**Implementation Logic:**
```python
# Orientation axis is calculated from Spin Tilt (t) and Spin Heading (h)
y = cos(t)
x = sin(t) * cos(h)
z = sin(t) * sin(h)
axis = [x, y, z]

# Apply Angle-Axis Rotation for the spin
glRotatef(rotation_angle, axis[0], axis[1], axis[2])

# Apply static Board Tilt relative to the axis
glRotatef(board_tilt, 1, 0, 0)
```

## Why this doc exists

This is intentionally in-repo so future work does not rely on ephemeral chat context.
