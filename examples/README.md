# SpinRender Example Presets

This directory contains example preset configurations that demonstrate different rendering styles and use cases.

## Using Example Presets

### Method 1: Import via UI

1. Open SpinRender in KiCad
2. In the Rotation Settings section, click **SELECT CUSTOM..**
3. Browse to this `examples/presets/` directory
4. Select the preset JSON file you want to use

### Method 2: Copy to User Directory

Copy preset files to your global presets directory:

**macOS/Linux:**
```bash
mkdir -p ~/.spinrender/presets
cp examples/presets/*.json ~/.spinrender/presets/
```

**Windows:**
```cmd
mkdir %USERPROFILE%\.spinrender\presets
copy examples\presets\*.json %USERPROFILE%\.spinrender\presets\
```

Then access them via the **SELECT CUSTOM..** button in SpinRender.

### Method 3: Project-Local Presets

For project-specific presets, copy to your board's directory:

```bash
mkdir -p .spinrender
cp examples/presets/hero_orbit_fast.json .spinrender/
```

## Available Presets

### Hero Orbit Fast
**File:** `hero_orbit_fast.json`

A quick 5-second version of the classic hero orbit shot. Perfect for social media or quick showcases.

- **Tilt:** 45° (balanced perspective)
- **Period:** 5 seconds (fast rotation)
- **Direction:** Counter-clockwise
- **Lighting:** Studio (professional 3-point)

**Best for:** Quick demos, social media posts, portfolio highlights

---

### Dramatic Reveal
**File:** `dramatic_reveal.json`

A medium-speed clockwise rotation with dramatic high-contrast lighting, perfect for making components stand out.

- **Tilt:** 30° (lower angle for depth)
- **Period:** 8 seconds (smooth reveal)
- **Direction:** Clockwise
- **Lighting:** Dramatic (strong shadows, high contrast)

**Best for:** Product reveals, component highlights, marketing videos

---

### Soft Top View
**File:** `soft_top_view.json`

A slow overhead rotation with soft diffused lighting, ideal for layout documentation.

- **Tilt:** 0° (flat top-down)
- **Period:** 12 seconds (slow, detailed)
- **Direction:** Counter-clockwise
- **Lighting:** Soft (minimal shadows, even illumination)

**Best for:** PCB layout documentation, assembly guides, technical reviews

---

### Isometric Showcase
**File:** `isometric_showcase.json`

A high-angle isometric view that shows both the board surface and edge details clearly.

- **Tilt:** 60° (steep isometric angle)
- **Period:** 10 seconds (standard speed)
- **Direction:** Counter-clockwise
- **Lighting:** Studio (balanced professional lighting)

**Best for:** Design showcases, depth visualization, technical presentations

## Creating Your Own Presets

Preset files are simple JSON documents with the following structure:

```json
{
  "name": "My Custom Preset",
  "settings": {
    "tilt": 45.0,
    "period": 10.0,
    "direction": "ccw",
    "rotate_z": -45.0,
    "lighting": "studio"
  }
}
```

### Parameter Reference

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| `tilt` | float | 0-90 | View inclination in degrees (0° = flat, 90° = edge-on) |
| `period` | float | 1-60 | Seconds for one complete 360° rotation |
| `direction` | string | "cw" or "ccw" | Rotation direction (clockwise or counter-clockwise) |
| `rotate_z` | float | -180 to 180 | Initial Z-axis rotation offset |
| `lighting` | string | "studio", "dramatic", "soft", "none" | Lighting preset |

### Lighting Presets

- **studio**: Balanced three-point lighting for professional look
- **dramatic**: High-contrast directional lighting with strong shadows
- **soft**: Diffused low-shadow ambient lighting
- **none**: No additional lighting (useful for custom setups via CLI overrides)

## Tips

1. **Start with an example**: Copy an existing preset and modify it rather than starting from scratch
2. **Test incrementally**: Adjust one parameter at a time to understand its effect
3. **Use descriptive names**: Make preset names clear and memorable
4. **Document your presets**: Add comments in a separate README if you create a collection
5. **Share presets**: Preset files are portable - share them with your team or the community

## Troubleshooting

**Preset doesn't appear in UI:**
- Verify the JSON syntax is valid (use a JSON validator)
- Ensure the file has a `.json` extension
- Check that the preset is in the correct directory

**Render looks different than expected:**
- Some lighting effects are subtle at certain angles
- Try adjusting tilt or lighting preset
- Use the wireframe preview to verify rotation before rendering

**Need more control:**
- Use the Advanced Options dialog to pass custom kicad-cli parameters
- See `docs/KICAD_CLI_RENDER_NOTES.md` for available render options
