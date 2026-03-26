# <img src="SpinRender/resources/icon.png" width="48" height="48" valign="middle"> SpinRender

**Bit-precise 3D spinning animations for your KiCad PCBs.**

SpinRender is a KiCad-CLI-based engine designed to generate high-fidelity, social-media-ready 3D loops of your circuit boards. By bypassing the standard GUI renderer, it achieves floating-point rotational precision and utilizes a 'Tilted Loop' logic to ensure seamless 360° revolutions without the gimbal lock or jitter common in manual screen recordings.

---

## 🎥 The Hero Loop
![The Hero Loop](res/hero_loop.gif)
*1080p 60fps render of a complex PCB performing a perfect Tilted Loop.*

---

## 💎 Key Features

| Feature | Description |
| :--- | :--- |
| **🎯 Floating-Point Precision** | Supports 0.0001° rotational increments for ultra-smooth motion. |
| **🔄 Tilted Loop Logic** | Specialized math to ensure perfect 360° loops with organic camera paths. |
| **💡 Studio Lighting** | High-contrast presets (Studio, Dramatic, Soft) for professional results. |
| **⚡ CLI-First Workflow** | Leverages `kicad-cli` for headless, reproducible rendering pipelines. |
| **🎨 Modern UI** | A teal-and-yellow high-contrast interface designed for efficiency. |

---

## 🛠️ Installation

### 1. Requirements
- **KiCad 8.0 or 9.0** (with `kicad-cli` in your PATH).
- **FFmpeg** (Required for MP4 and high-quality GIF assembly).
- **Python 3.10+** (The version bundled with your KiCad installation).

### 2. Plugin Setup
1. Download the latest release or clone this repository into your KiCad plugins folder:
   - **macOS:** `~/Library/Preferences/kicad/8.0/scripting/plugins`
   - **Windows:** `%APPDATA%\kicad\8.0\scripting\plugins`
   - **Linux:** `~/.local/share/kicad/8.0/scripting/plugins`
2. Open KiCad PCB Editor.
3. Click the **SpinRender** icon in the top toolbar or find it under `Tools > External Plugins`.

---

## 🚀 Usage

### Quick Start (GUI)
1. Open your `.kicad_pcb` file.
2. Launch **SpinRender**.
3. Select the **'Hero Reveal'** preset.
4. Hit **Render**. Your animation will be saved to the `/Renders` folder next to your PCB file.

### The 'Tilted Loop' Parameters
SpinRender uses a Universal-Joint model to define the camera path:

| Parameter | Function | Typical Value |
| :--- | :--- | :--- |
| **View Tilt** | The static elevation of the camera. | 15° - 30° |
| **Spin Tilt** | The angle of the rotation axis relative to the board normal. | 90° (Edge-on) |
| **Period** | Duration of one full 360° revolution. | 10.0s |
| **Easing** | Motion interpolation (Linear for loops, Bezier for reveals). | Linear |

### CLI Override Example
For power users, you can pass raw `kicad-cli` flags through the **CLI Overrides** field:
```bash
--raytracing --samples 128 --no-floor --post-processing
```

---

## 📸 Media Recommendations for Creators

To best showcase your hardware, we recommend producing the following assets:

1. **The "Hero Loop":** A 1080p 60fps GIF of a complex PCB (lots of vias and components) doing one full "Tilted Loop" revolution.
2. **The "UI Close-up":** A sharp screenshot of the SpinRender dialog box showing the teal/yellow high-contrast theme.
3. **The "Step-Comparison":** A split-screen GIF showing the difference between a 5-degree jump (jittery) and SpinRender's floating-point 0.5-degree jump (silky smooth).
4. **Lighting Showcase:** A side-by-side of 'Studio' (clear, technical) vs 'Dramatic' (heavy shadows, mood lighting).

---

## 🤝 Community & Contributing

Hardware geeks, welcome! Whether you're a KiCad wizard or a Python pro, we value your input.
- **Bug Reports:** Open an issue with your `.kicad_pcb` (if possible) and KiCad version.
- **Feature Requests:** We're currently exploring multi-board support and custom shader injection.

### License
SpinRender is released under the **MIT License**. See `LICENSE` for details.

---

*Designed for engineers who care about how their work is seen.*
