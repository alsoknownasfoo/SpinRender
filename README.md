# ![SPINRENDER][logo_img]

#### **Easy hero animations for your nerdy KiCad PCBs**

![Plugin Overview Screenshot][overview_img]

SpinRender is a KiCad 9+ plugin for generating high-fidelity, social-media-ready looping 3D renders of your circuit boards. 

Use presets, or precisely control how your board rotates.

Give your board dramatic lighting to add wow to your presentation or have it well lit and use it as a pseudo-3D reference model on your phone.

<img src="res/images/sr_sample1.gif" width="276" alt="Sample Output 1"><img src="res/images/sr_sample2.gif" width="276" alt="Sample Output 2"><img src="res/images/sr_sample3.gif" width="276" alt="Sample Output 3">

&nbsp;
## Features

| Feature | Description |
| :--- | :--- |
| **Easy Button** | Two-click, no-fuss, no-skills-required renders. |
| **Spin Precision** | Control the speed and direction of your spin to the 0.01°. |
| **Flexible Staging** | Personalize the background and control how your board is lit. |
| **Format Options** | Export to an MP4 movie file, animated GIF, or lossless PNG sequence. |

&nbsp;
## Installation

### Requirements

> **KiCad 9.0 or 10.0**
>
> <details>
>   <summary><strong>Fonts & Libraries</strong></summary>
>
>   SpinRender will attempt to download and install the following Python packages and fonts on first launch:
>
>   **Python Packages:**
>   - `PyOpenGL`
>   - `PyYAML`
>   - `trimesh`
>   - `numpy`
>
>   **Fonts:**
>   - `JetBrains Mono`
>   - `Material Design Icons`
>   - `Oswald`
>
>   If you experience font rendering issues, ensure your system allows Python to access the internet, or manually install the recommended fonts listed above. For manual installation instructions, see the documentation.
> </details>

### Setup

<details>
   <summary><strong>Using PCM</strong> (Recommended)</summary>
```
1. Start KiCad and click on **Plugin and Content Manager** in the project window.
2. Under **Plugins**, filter for **SpinRender**.
3. Click **Install**.
4. Click **Apply Pending Changes**.
```
</details>

<details>
   <summary><strong>Release Download</strong></summary>

1. Download the latest release from **Releases**.
2. In PCB Editor, go to `Tools > External Plugins > Reveal Plugin Folder ..`
3. Unzip and drag the **SpinRender** folder into the revealed folder.
</details>

<details>
   <summary><strong>Clone Repository</strong></summary>

1. Run `git clone https://github.com/alsoknownasfoo/SpinRender`
2. Run the install script:
    - **Windows:** `install.bat`
    - **macOS/Linux:** `install.sh`
</details>

### Run

1. Restart KiCad and open PCB Editor

   ![SpinRender Icon][icon_img]

2. Find the **SpinRender** icon in top toolbar or under `Tools > External Plugins`.

&nbsp;
## Usage

Coming..

## Troubleshooting

<details>
   <summary><strong>Missing Toolbar Icon</strong></summary> 

   - Ensure you installed to the correct plugin folder for your KiCad version and platform.
   - Restart KiCad after installation.
   - Check the plugin manager for errors or missing dependencies.
</details>

<details>
   <summary><strong>Missing dependencies:</strong></summary> 

  * Open a terminal and run the manual install command above.
  * Verify your Python version matches the one bundled with KiCad.
</details>

<details>
   <summary><strong>Permission errors:</strong></summary> 

  - On macOS/Linux, you may need to run `chmod +x install.sh` before executing the install script.
  - On Windows, run the installer as administrator if you encounter access issues.
</details>

#### Still stuck?
Open an issue on GitHub with your OS, KiCad version, and any error messages.

&nbsp;
## Contributing

Built with support from: [^1]
[^1]: So there might be some wonky code.

[![Claude][claude_icon]][claude_link] &nbsp;&nbsp; [![Gemini][gemini_icon]][gemini_link] &nbsp;&nbsp; [![ChatGPT][chatgpt_icon]][chatgpt_link] &nbsp;&nbsp; [![Copilot][copilot_icon]][copilot_link] &nbsp;&nbsp; [![StepFun][stepfun_icon]][stepfun_link]

**Bug Reports:** Open a GitHub issue.  
**Feature Requests:** Submit via GitHub discussions.

_All feedback and suggestions welcomed!_

&nbsp;
## License

SpinRender is released under the **GPLv3 License**. See `LICENSE` for details.

&nbsp;
## Thank You!

Thanks for taking the time to check this project.  
I created it because I wanted a way to show people how beautiful PCB design can be.   

Hopefully, it helps you do the same.  

[![Support me on Ko-Fi][kofi_badge]][kofi_link] &nbsp; [![Sponsor me on GitHub][github_badge]][github_link]

[logo_img]: res/images/sr_logo.png
[overview_img]: res/images/ui_overview-dark.gif
[sample_gif1]: res/images/sr_sample1.gif
[sample_gif2]: res/images/sr_sample2.gif
[sample_gif3]: res/images/sr_sample3.gif
[icon_img]: /SpinRender/resources/icons/logo.svg

[claude_icon]: SpinRender/resources/icons/claude.svg
[gemini_icon]: SpinRender/resources/icons/gemini.svg
[chatgpt_icon]: SpinRender/resources/icons/chatgpt.svg
[copilot_icon]: SpinRender/resources/icons/copilot.svg
[stepfun_icon]: SpinRender/resources/icons/stepfun.svg

[claude_link]: https://claude.ai/
[gemini_link]: https://gemini.google.com/
[chatgpt_link]: https://chatgpt.com/
[copilot_link]: https://github.com/features/copilot
[stepfun_link]: https://stepfun.ai/

[kofi_badge]: https://img.shields.io/badge/Support_me_on-KO--FI-C8A27A?style=for-the-badge&logo=ko-fi&logoColor=white
[kofi_link]: https://ko-fi.com/alsoknownasfoo
[github_badge]: https://img.shields.io/badge/Sponsor_me_on-GITHUB-EA4AAA?style=for-the-badge&logo=github-sponsors&logoColor=white
[github_link]: https://github.com/sponsors/alsoknownasfoo
