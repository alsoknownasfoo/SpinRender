# Changelog

All notable changes to SpinRender are documented here. Format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## Install

- **PCM:** Plugin and Content Manager → search "SpinRender".
- **Manual:** download the release's `sr-pcm-XYZ.zip` and install via PCM's
  "Install from File…", or use `install.sh` / `install.bat` from a clone.

## [0.8.1] - 2026-07-28

### 💥 Crash recovery & diagnostics
- Fixed a crash affecting some Linux/KiCad 9 installs where the dependency check itself could take KiCad down with a `free(): invalid pointer` glibc abort — dependency checks now run out-of-process, so a native crash in a package probe can no longer propagate to KiCad.
- If `kicad-cli` crashes mid-render, SpinRender now automatically retries the frame at basic quality instead of failing outright, and sticks with basic quality for the rest of that render once it's proven necessary.
- Crash diagnostics (binary identity, a macOS Rosetta/architecture check, a "died before any output" flag, peak memory) are now logged on every crash, whether or not the automatic retry recovers it.
- Render error dialogs now have a **Copy Details** button, so the full error text (including the new diagnostics) can be pasted straight into a bug report instead of retyped or screenshotted.

### 🔍 Dependency detection
- `kicad-cli` is now found by looking next to KiCad's own bundled Python interpreter, which works regardless of KiCad's version or install location — no more missing it just because KiCad wasn't installed to the default path.
- The dependency-check dialog's checkmarks no longer get stuck showing stale (pre-install) status after clicking Install; added a note explaining that `kicad-cli`/`ffmpeg` are bundled binaries that can't be pip-installed and need manual setup instead.

### 🗂 Project-file safety
- Fixed a bug where rendering could silently create a second, fully valid KiCad project file next to your board — a running KiCad session could pick this up as the "current" project and start offering to create files under it.
- Cleaned up orphaned KiCad project lock files (`~*.kicad_pro.lck`) left behind by the above.

**Full changelog:** https://github.com/alsoknownasfoo/SpinRender/compare/v0.8.0...v0.8.1

## [0.8.0] - 2026-06-10

### 🪟 Full Windows support
- SpinRender now runs natively on Windows, with the UI brought to full visual parity with macOS:
  - Dialogs, the main panel, and custom controls (toggles, sliders, sponsor bar) now match geometry, spacing (DIP-correct), backgrounds, and the SVG logo.
  - Theme font sizes are correctly converted from design pixels to points on Windows.
  - Layout now scales properly with display DPI, and paint buffers are cleared correctly on HiDPI displays.
  - Spawned subprocesses (kicad-cli, ffmpeg) no longer flash momentary console windows.
  - `kicad-cli` and `ffmpeg` are now found via Windows install-path fallbacks even when not on `PATH`.

### 🛠 Installer overhaul
- `install.sh` / `install.bat` UX has been overhauled, including better KiCad/OneDrive path detection and automatic `ffmpeg` installation.

### 🐧 Linux
- SpinRender now warns users on launch that Linux support is **untested** — please try it and report issues on GitHub.

### 🎨 Theming & dialog fixes
- Dialog panels are now themed and coloured solid (no more transparent panels on macOS), including footer panels so buttons clear to the correct colour, with frame margins restored.
- Native scrollbars are themed and dialog theme switching is now complete; the preview overlay correctly refreshes its theme and forces scrollbar mode.
- Fixed the `SectionToggle` +/- glyph never drawing (`wx.Pen` rejected a float width).
- Fixed assorted macOS visual regressions introduced by the Windows parity work.

### 🖥 Stability & crash fixes
- Paint-handler exceptions no longer crash KiCad — leaked device contexts are now guarded against.
- The theme watcher timer is stopped on close, preventing a KiCad crash on plugin shutdown.
- Fixed a `wx.Rect` `TypeError` and a bundled MDI font filename issue.
- Bundled a `wx.svg._nanosvg` shim for KiCad 10 wxPython builds that are missing it.

### 🎬 Render & preview fixes
- Preview playback no longer flashes gray between frames.
- The GL viewport is switched off while the render preview overlay is up.
- `SaveBoard`'s side-written project files are now hidden/unhidden as a set, and hidden/read-only attributes are cleared before overwriting working copies — fixing render failures on Windows.

### ✏️ Misc
- The **Check for Updates** button is hidden in the About dialog (update flow is being revisited).

**Full changelog:** https://github.com/alsoknownasfoo/SpinRender/compare/v0.7.0-beta...v0.8.0

## [0.7.0-beta] - 2026-06-09

### 🔄 In-plugin updates
- **Check for Updates** in the About dialog now resolves real GitHub releases and acts on your install type:
  - **PCM installs** → prompted to update through KiCad's Plugin & Content Manager.
  - **Manual / dev installs** → one-click **self-update**: downloads the latest release, verifies it, and swaps the plugin in place (restart KiCad to load it).
- Version string now carries provenance: a clean `0.7.0-beta` for releases, `0.7.0-beta+<sha>` for a build installed from a git clone.

### 📦 PCM packaging fix
- The PCM archive is now **flat** — files install to `…/com_alsoknownasfoo_spinrender/` directly instead of a nested `…/SpinRender/` subfolder, so KiCad loads the plugin correctly. Absolute `SpinRender.*` imports are preserved via a package-name alias regardless of the installed directory name.

### 🛠 Installers
- `install.sh` / `install.bat` now **warn if a PCM-managed copy is already installed** (and offer to abort) to avoid double-registration.
- When installed from a git clone, the installers **stamp the exact commit** so the version display and updater can tell a dev build from a release.

### 🌐 Localization
- Update-flow strings translated across all supported locales.

**Full changelog:** https://github.com/alsoknownasfoo/SpinRender/compare/v0.6.1-beta...v0.7.0-beta

## [0.6.1-beta] - 2026-06-05

A small follow-up to 0.6.0-beta with input fixes and a new high-resolution preset.

### ✨ New
- **Phone/Tablet resolution preset** — added a 2160×3840 portrait output preset for mobile/social formats.

### 🐛 Fixes
- **Numeric inputs now behave as proper spinners** — increment/decrement and keyboard entry work as expected.
- **Spin preset orientation** — corrected board/spindle/shadow orientation (−90°) so the Spin preset frames the board correctly.

### 📦 Packaging / PCM
- Published to the KiCad **Plugin & Content Manager** as `0.6.1`.
- Cleaned up listing metadata: removed the non-standard `category`, added discovery `tags` and a `maintainer`.
