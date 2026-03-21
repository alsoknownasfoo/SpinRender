# KiCad CLI Render Notes

This document captures practical behavior of `kicad-cli pcb render` and related preview/export commands as they are currently used by SpinRender.

## Verified Behavior (Current Implementation Snapshot, 2026-03-13)

Command tested:
- `kicad-cli pcb render --help`

SpinRender currently uses these commands:
- `kicad-cli pcb render`
- `kicad-cli pcb export glb`

Key `pcb render` options currently emitted by SpinRender:
- `--rotate`
- `--perspective`
- `--zoom`
- `--background transparent`
- `--quality user`
- `-w`, `-h`
- `--light-top`
- `--light-bottom`
- `--light-side`
- `--light-camera`
- `--light-side-elevation`
- `-o`

Key `pcb export glb` options currently emitted for preview loading:
- `--fuse-shapes`
- `--grid-origin`
- `--no-dnp`
- `--subst-models`
- `--include-pads`
- `--include-silkscreen`
- `--output`

Important implementation clarification:
- Final MP4 and GIF outputs are composited with the selected background color in `ffmpeg`; the KiCad render step itself stays transparent.
- SpinRender sets `KICAD_CONFIG_HOME` to the in-repo `resources/kicad_config` directory so render behavior can be influenced by shipped KiCad config files.

Important clarification:
- Manual CLI overrides are currently appended with simple whitespace splitting.
- They are **not** sanitized or normalized before execution.
- Any future override validation should happen before tokens are appended to the command.

## Rotation Coordinate System (Universal Joint Model)

**Verified through test renders (2026-03-11)**

SpinRender uses a universal-joint-style control model to provide full 360° freedom for spin, roll, and tumble style motions while still emitting KiCad-safe Euler angles per frame.

### Adjustment Parameters

1. **BOARD TILT**: Static X-axis tilt applied to the board before the animated spin.
2. **BOARD ROLL**: Static Z-axis roll used to bias the board's resting orientation.
3. **SPIN TILT**: Polar tilt of the animated spin axis.
4. **SPIN HEADING**: Azimuth of the animated spin axis around the board.
5. **DIRECTION**: `ccw` keeps the animated angle positive, `cw` negates it.
6. **PERIOD**: Controls frame count through a fixed `30 fps` render cadence.

### Built-In Presets in the Current Renderer

| Preset | BOARD TILT | BOARD ROLL | SPIN TILT | SPIN HEADING | DIRECTION | LIGHTING |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **hero** | `0°` | `-45°` | `90°` | `90°` | `ccw` | `dramatic` |
| **spin** | `0°` | `-45°` | `90°` | `135°` | `ccw` | `studio` |
| **flip** | `0°` | `-180°` | `90°` | `45°` | `cw` | `dramatic` |

### Render-Side Rotation Mapping

For each frame, SpinRender computes an animation angle from:
- `frame_count = period * 30`
- `step_degrees = 360 / frame_count`
- `anim_angle = raw_angle` for `ccw`
- `anim_angle = -raw_angle` for `cw`

The exporter then converts the control model into KiCad's `--rotate X,Y,Z` using two paths:

1. **Fast path** when `spin_tilt == 0`:
   - `X = board_tilt`
   - `Y = 0`
   - `Z = anim_angle + board_roll`

2. **General path** when the spin axis is tilted:
   - Construct an axis from spherical coordinates with **Z as the polar axis**.
   - Build `R_spin` with Rodrigues rotation.
   - Compose the matrix as `R_X(board_tilt) · R_spin · R_Z(board_roll)`.
   - Decompose that matrix back into intrinsic XYZ Euler angles for KiCad.

Before emission, all three output angles are normalized into `[0, 360)` to avoid leading negative values that may confuse the CLI parser.

### Technical Implementation (Preview)

The OpenGL preview is intentionally aligned with the renderer's rotation model.

Preview axis construction:

```python
x = sin(t) * cos(h)
y = sin(t) * sin(h)
z = cos(t)
axis = normalize([x, y, z])
```

Preview transform order:

1. **BOARD TILT** as X rotation
2. **Animated spin** around the dynamic axis
3. **BOARD ROLL** as Z rotation

```python
glRotatef(board_tilt, 1, 0, 0)
glRotatef(direction_sign * rotation_angle, axis[0], axis[1], axis[2])
glRotatef(board_roll, 0, 0, 1)
```

This matches the intended order noted in the preview code:
- `R_X(board_tilt) · R_spin · R_Z(board_roll)`

## Preview/Export Parity Notes

The preview pipeline includes a few implementation details that are important for parity with export:

- Exported GLB meshes are rotated by `+90°` around X after loading so the preview uses the same face-up orientation assumption as the renderer math.
- If the loaded mesh appears to be in meters, the preview auto-scales it to millimeters.
- The preview supports `wireframe`, `shaded`, and `both` modes, but final export is still driven by `kicad-cli pcb render` rather than the OpenGL preview.
- The preview has a special `workspace` lighting mode that approximates the KiCad viewer more closely, even though the renderer still uses the CLI lighting preset table.

## CLI Override Caveat

`cli_overrides` are currently appended directly onto the render command using basic string splitting. That means:
- quoting behavior is limited,
- malformed tokens pass through unchanged.

## Why this doc exists

This is intentionally in-repo so future work does not rely on ephemeral chat context.
