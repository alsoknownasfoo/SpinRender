# SpinRender - KiCad PCB Animation Rendering Plugin

**Version:** 0.9.0-alpha

SpinRender is a KiCad plugin that makes it easy to generate beautiful animated PCB renders directly from your KiCad projects. Create professional showcase videos, GIFs, and image sequences with just a few clicks.

## Features

- 🎬 **Three Export Formats**: MP4 (H.264), GIF, or PNG sequences
- 🎨 **Built-in Presets**: Hero Orbit, Top Sweep, and Angle Reveal camera loops
- 💡 **Lighting Presets**: Studio, Dramatic, Soft, and None lighting configurations
- ⚡ **Real-time 3D Preview**: OpenGL-accelerated preview with actual PCB geometry and lighting
- 🎯 **Tilted Loop Model**: Intuitive controls for view tilt, rotation period, and direction
- 💾 **Custom Presets**: Save and recall your favorite render settings
- 🔧 **Advanced Options**: Full control over output paths and kicad-cli parameters

## Requirements

### Core Dependencies

- **KiCad 8+** (with kicad-cli)
- **ffmpeg** (for video/GIF export)
- **Python 3.8+** (typically bundled with KiCad)
- **wxPython** (typically bundled with KiCad)

SpinRender will automatically check for dependencies on first launch and offer to install missing components.

### Optional: 3D Preview Enhancement

For full OpenGL-accelerated 3D preview with real-time PCB rendering:

```bash
pip install -r requirements_preview.txt
```

This installs:
- **PyOpenGL** - Hardware-accelerated 3D rendering
- **trimesh** - GLB file mesh loading
- **numpy** - Numerical operations

Without these packages, SpinRender will use a lightweight wireframe preview instead.

## Installation

### Method 1: Automatic Installation (Recommended)

Run the installation script from the repository directory:

**macOS/Linux:**
```bash
./install.sh
```

**Windows:**
```cmd
install.bat
```

The script will:
- Copy the plugin to `~/Documents/KiCad/9.0/3rdparty/plugins/SpinRender`
- Check for existing installations and prompt before overwriting
- Verify the installation completed successfully

### Method 2: Manual Installation

1. Download or clone this repository
2. Copy the `SpinRender` directory to your KiCad plugins directory:
   - **All platforms**: `~/Documents/KiCad/9.0/3rdparty/plugins/`
   - (Windows: `%USERPROFILE%\Documents\KiCad\9.0\3rdparty\plugins\`)

3. Restart KiCad

### Method 3: Plugin Manager (Coming Soon)

SpinRender will be available through the KiCad Plugin and Content Manager in a future release.

## Usage

### Quick Start

1. Open your PCB in KiCad PCB Editor
2. Click the SpinRender toolbar button or go to **Tools → External Plugins → SpinRender**
3. Choose a loop preset (Hero Orbit, Top Sweep, or Angle Reveal)
4. Adjust rotation settings (tilt, period, direction) as desired
5. Select a lighting preset
6. Choose output format (MP4, GIF, or PNG Sequence) and resolution
7. Click **RENDER**

Your animation will be saved to a timestamped directory in `Renders/` next to your board file.

### Loop Presets

- **Hero Orbit**: 45° tilted rotating view, perfect for showcasing the entire board
- **Top Sweep**: Flat overhead rotation, ideal for layout overviews
- **Angle Reveal**: 30° angle rotation, great for demonstrating board depth

### Rotation Settings

- **View Tilt (θ)**: Inclination from flat (0°) to edge-on (90°)
- **Rotation Period**: How many seconds for one complete 360° revolution
- **Easing Profile**: Currently linear (additional easing curves coming soon)
- **Direction**: CW (clockwise) or CCW (counter-clockwise) rotation

### Lighting Presets

- **Studio**: Balanced three-point lighting for professional look
- **Dramatic**: High-contrast directional lighting with strong shadows
- **Soft**: Diffused low-shadow ambient lighting
- **None**: No additional lighting (useful for custom setups)

### Output Formats

- **MP4 (H.264)**: High-quality video at 30fps, compatible with all platforms
- **GIF**: Animated GIF with optimized palette
- **PNG Sequence**: Individual frames for post-processing or custom assembly

### Advanced Options

Click the **ADVANCED** button to access:

- **Output Path**: Override automatic timestamped directory creation
- **Parameter Overrides**: Pass custom flags directly to kicad-cli render

### Saving Custom Presets

1. Configure your desired rotation, lighting, and other settings
2. Click **+ SAVE PRESET** in the Rotation Settings section
3. Enter a name for your preset
4. Your preset is saved and can be loaded via the "SELECT CUSTOM.." button

## How It Works

SpinRender uses the tilted-loop model to generate smooth camera animations:

1. **Frame Generation**: For each frame, SpinRender calls `kicad-cli pcb render` with calculated rotation parameters
2. **Assembly**: Frames are assembled into the final output using ffmpeg
3. **Preview**: The wireframe preview gives real-time feedback as you adjust parameters

All rendering respects the quirks documented in `docs/KICAD_CLI_RENDER_NOTES.md` for maximum compatibility.

## Troubleshooting

### "kicad-cli not found"

Ensure KiCad 8+ is installed and `kicad-cli` is in your PATH. On macOS, you may need to add:
```bash
export PATH="/Applications/KiCad/KiCad.app/Contents/MacOS:$PATH"
```

### "ffmpeg not found"

Install ffmpeg:
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt-get install ffmpeg`
- **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

### Render fails with "Unknown argument" error

This is likely due to negative vector values in rotation parameters. SpinRender sanitizes these automatically, but if using custom CLI overrides, ensure all vector components are positive or properly formatted.

### Preview shows wireframe instead of PCB model

If you see a simple wireframe box instead of your actual PCB:

1. Install the optional 3D preview dependencies: `pip install -r requirements_preview.txt`
2. Restart KiCad
3. The preview will now show your actual PCB geometry with lighting and shading

The preview automatically exports your PCB to GLB format in the background. You'll see "GLB MODEL READY" when the export completes.

## Roadmap

- [x] **3D Preview**: Real-time OpenGL preview with actual PCB geometry *(v0.9.0)*
- [ ] **Non-linear Easing**: Bezier curves for ease-in, ease-out, ease-in-out
- [ ] **Exploded View**: Animate board layer separation
- [ ] **Component Highlights**: Spotlight specific components during animation
- [ ] **Batch Rendering**: Process multiple boards with the same settings
- [ ] **Preset Packs**: Downloadable preset collections for different use cases

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details

## Credits

Built with:
- [KiCad](https://www.kicad.org/) - PCB design software
- [ffmpeg](https://ffmpeg.org/) - Video processing
- [wxPython](https://www.wxpython.org/) - GUI framework
- [Pencil](https://pencil.dev/) - UI design tool

## Support

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/yourusername/SpinRender/issues)
- 💬 [Discussions](https://github.com/yourusername/SpinRender/discussions)
