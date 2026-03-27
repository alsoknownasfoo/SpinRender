# ![SPINRENDER](res/images/sr_logo.png)

#### **Easy hero animations for your nerdy KiCad PCBs**

![Plugin Overview Screenshot](res/images/ui_overview-dark.gif)

SpinRender is a KiCad 9+ plugin for generating high-fidelity, social-media-ready looping 3D renders of your circuit boards. 

Use presets, or precisely control how your board rotates.

Give your board dramatic lighting to add wow to your presentation or have it well lit and use it as a pseudo-3D reference model on your phone.

<table align="center" style="width:100%; table-layout:fixed; border-collapse:collapse;">
   <tr>
      <td style="width:33%; text-align:center; vertical-align:top; padding:0;">
         <img src="res/images/sr_sample1.gif" alt="Sample Output 1" style="max-width:100%; min-width:180px; display:inline-block; margin:0; border:0; padding:0;" />
      </td>
      <td style="width:33%; text-align:center; vertical-align:top; padding:0;">
         <img src="res/images/sr_sample2.gif" alt="Sample Output 2" style="max-width:100%; min-width:180px; display:inline-block; margin:0; border:0; padding:0;" />
      </td>
      <td style="width:33%; text-align:center; vertical-align:top; padding:0;">
         <img src="res/images/sr_sample3.gif" alt="Sample Output 3" style="max-width:100%; min-width:180px; display:inline-block; margin:0; border:0; padding:0;" />
      </td>
   </tr>
</table>

## <span style="color:#00FFFF">Features</span>
|||
|---|---|
| **Easy Button**     | Two-click, no-fuss, no-skills-required renders.|
| **Spin Precision**  | Control the speed and direction of your spin to the 0.01°.|
| **Flexible Staging**| Personalize the background and control how your board is lit.|
| **Format Options**  | Export to an MP4 movie file, animated GIF, or lossless PNG sequence.|

## <span style="color:#00FFFF">Installation</spam>

#### Requirements

>**KiCad 9.0 or 10.0**
>
><details>
>  <summary><strong>Fonts & Libraries</strong></summary>
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
></details>

#### Setup

><details>
>   <summary><strong>Using PCM</strong> (Recommended)</summary>
>
>1. Start KiCad and click on <strong>Plugin and Content Manager</strong> in the project window.
>2. Under <strong>Plugins</strong>, filter for <strong>SpinRender</strong>.
>3. Click <strong>Install</strong>.
>4. Click <strong>Apply Pending Changes</strong>.
></details>
>
><details>
>
>   <summary><strong>Release Download</strong></summary>
>
>1. Download the latest release from <strong>Releases</strong>.
>2. In PCB Editor, go to <code>Tools &gt; External Plugins &gt; Reveal Plugin Folder ..</code>
>3. Unzip and drag the <strong>SpinRender</strong> folder into the revealed folder.
></details>
>
><details>
>   <summary><strong>Clone Repository</strong></summary>
>
>1. Run <code>git clone https://github.com/alsoknownasfoo/SpinRender</code>
>2. Run the install script:
>    - <strong>Windows:</strong> <code>install.bat</code>
>    - <strong>macOS/Linux:</strong> <code>install.sh</code>
></details>

#### Run
>1. Restart KiCad and open PCB Editor
>
> ![SpinRender Icon](/SpinRender/resources/icons/logo.svg)
>
>2. Find the **SpinRender** icon in top toolbar or under `Tools > External Plugins`.

## <span style="color:#00FFFF">Usage</span>
**_Coming.._**

## <span style="color:#00FFFF">Troubleshooting</span>
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
<sup>Open an issue on GitHub with your OS, KiCad version, and any error messages.</sup>

## <span style="color:#00FFFF">Community & Contributing</span>

Built with support from:[^1]
[^1]:So there might be some wonky code
<p align="left">
   <a href="https://claude.ai/" title="Claude">
      <img src="SpinRender/resources/icons/claude.svg" alt="Claude" height="28" style="vertical-align:middle; margin:0 8px;">
   </a>
   <a href="https://gemini.google.com/" title="Gemini">
      <img src="SpinRender/resources/icons/gemini.svg" alt="Gemini" height="28" style="vertical-align:middle; margin:0 8px;">
   </a>
   <a href="https://chatgpt.com/" title="ChatGPT">
      <img src="SpinRender/resources/icons/chatgpt.svg" alt="ChatGPT" height="28" style="vertical-align:middle; margin:0 8px;">
   </a>
   <a href="https://github.com/features/copilot" title="Copilot">
      <img src="SpinRender/resources/icons/copilot.svg" alt="Copilot" height="28" style="vertical-align:middle; margin:0 8px;">
   </a>
   <a href="https://stepfun.ai/" title="StepFun">
      <img src="SpinRender/resources/icons/stepfun.svg" alt="StepFun" height="28" style="vertical-align:middle; margin:0 8px;">
   </a>
</p>

All feedback and suggestions welcomed.

*   **Bug Reports:** Open a GitHub issue.
*   **Feature Requests:** Submit via GitHub discussions.

## <span style="color:#00FFFF">License</span>

SpinRender is released under the **GPLv3 License**. See `LICENSE` for details.

## <span style="color:#00FFFF">Thank You!</span>
_This plugin was designed for engineers who care about how their work is seen._

Thanks for taking the time to check it out. I hope it proves to be useful for whatever your needs are.

<p align="left">
<a href="https://ko-fi.com/alsoknownasfoo">
   <img src="https://img.shields.io/badge/Support_me_on-KO--FI-C8A27A?style=for-the-badge&logo=ko-fi&logoColor=white" height="30">
</a>
&nbsp;
<a href="https://github.com/sponsors/alsoknownasfoo">
   <img src="https://img.shields.io/badge/Sponsor_me_on-GITHUB-EA4AAA?style=for-the-badge&logo=github-sponsors&logoColor=white" height="30">
</a>
</p>