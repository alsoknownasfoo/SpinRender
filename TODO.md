
## WORKFLOW INSTRUCTIONS

**Context:** See `docs/README.md`. Maintain existing code patterns.

**Task Workflow:**

_Simple fix (1-2 files, clear scope):_
1. /plan — read code, propose approach, confirm with user
2. Create worktree → implement → commit
3. Move to REVIEW → user verifies → merge → DONE

_Medium/Large (3+ files, new patterns, or architectural changes):_
1. /plan with @architect if structural — context + plan, confirm with user
2. Create worktree, write plan to file for agent handoff
3. Implement; run @python-reviewer before moving to REVIEW
4. Move to REVIEW → user verifies → merge → DONE
5. Run @doc-updater only if architecture changed

_Agent gates (only invoke when they add value):_
- @architect: new subsystems or cross-cutting refactors only
- @python-reviewer: 3+ file changes or security-sensitive code
- @doc-updater: only when docs/README.md would be outdated
- Never merge without user verification

**Design Alternatives:**
If a refactor would significantly improve code quality, present it as an option for user consideration.

### TODO

# Format: [TAG] Simple Title: Task...
# Branch name format: (feat/fix)/name-of-task

[UI/UX] Advanced Output Formatting: output path, parameter overrides, system logging should all use subheader. the body text should all be upper. this shoud be defined in theme.yaml. The Parameter Overrides box still has a light gray bg on the input field. it should not show or be painted transparent. This interesting isnt an issue for non-multiline renders of the inputfield.

[UI/UX] Window Borders: Add a 1px black border around the main window and dialog boxes and add a 4px radius on them. ensure that these definitions are in the yaml

[UI/UX] Project Folder Badge: Ensure that the project folder badge can apply all customization in the yaml. we want to use a bigger and bolder font.

[CODE] Preview/Dependency Dialog Font Refactor: `preview_panel.py` and `dependency_dialog.py` use hardcoded `wx.Font()` calls with no theme integration. Migrate to `create_text()` with proper YAML-backed style paths. Dependency dialog also uses hardcoded font constants (FONT_MONO, FONT_BODY, FONT_ICON).

[UI/UX] Advanced/About Section: In the advanced settings, add:
- An "About" section with app origin, authorship, and tools/LLMs used.
- Helper text for getting help, reporting issues, or donating (link to GitHub).
- Placeholder "Check for Updates" button.

[CODE] Theme Comment Cleanup: Remove all "v2"/"V2" references in code comments. Use "theme", "current", or omit if obvious.

[CODE] Regenerate Light Theme: Regenerate a new light.yaml theme file based on the current dark.yaml, ensuring all relevant values are adapted for a light color scheme and consistent with the latest dark theme structure.

[CODE] CSS Padding Audit: `Theme._parse_padding()` added to support CSS-style shorthand (1/2/4 values). Audit all `padding` token reads across dialogs and components to switch from raw int reads to `_parse_padding()` calls.

[CODE] BaseStyledDialog Footer Refactor: Dialog footers (padding, gap, proportion=1 buttons) are defined ad-hoc per dialog. Extract a `create_footer(btn1, btn2, padding, gap)` helper into `BaseStyledDialog` so all dialogs share the same code for consistency. Then use the @refactor-cleaner agent to do cleanup

[UI/UX] Audit String Localization: Audit all user-facing strings in the codebase to ensure no strings are hardcoded and all are pulled from locale files. Output a list of any hardcoded strings and locations that need to be updated for proper localization.

[CODE] Audit YAML Value Usage: Audit all YAML values to verify they are actually applied in code. Output a list of:
    - YAML values that need supporting code
    - YAML values that need to be added
    - Any inconsistencies with usage patterns
Then, review the patterns and identify areas where code can be modularized for efficiency and consistency.

[CODE] Documentation Cleanup: Use @doc-updater agent to review and clean up the `docs/` directory:
- Remove outdated planning docs and temporary files.
- Cross-check documentation accuracy with current repo code.
- Add missing details to ensure docs are efficient and informative for both humans and LLMs.

[CODE] Code cleanup via @refactor-cleaner agent

[CODE] Get code ready for publishing to the public.  Make sure we are following best practices for kicad plugins. Advance code version 0.99

---

### REVIEW

# Move tasks here when a branch is ready for review.
# Format: [TAG] [YYYY-MM-DD] [branch-name] Simple Title: Task...

[UI/UX+CODE] [2026-03-22] [feat/programmatic-uppercase] Programmatic Uppercasing + Global create_text Refactor:
- Added formatting: "uppercase" to text.subheader, text.metadata, text.status in dark.yaml
- Normalized all sub-body locale strings to sentence case
- Fixed bypass sites in dialogs.py, status_bar.py, main_panel.py
- Upgraded helpers.create_text() to canonical styled-text factory: resolves TextStyle by name, applies format_text(), sets font+color, registers in global weak-ref registry for hot-reload
- Added reapply_text_styles() for global theme hot-reload of all wx.StaticText
- Deleted _add_text() and _hotload_map from controls_side_panel; replaced with create_text()
- Redesigned SectionLabel from paint-based to wx.StaticText via create_text()
- All dialogs.py bare wx.StaticText+SetFont replaced with create_text()
- Added layout.dialogs.default.description and .section_label YAML paths
- Updated docs: CODEMAPS/frontend.md, theme-design-principles.md

---

### DONE

# (Move tasks here after merge/verification with commit # with notes)
# Format: [TAG] [YYYY-MM-DD] [branch-name] Simple Title: Task...

[CODE] [2026-03-22] [fix/png-sequence-path] PNG Sequence Path: update_path_display shows name_#####.png. on_browse uses DirDialog + FilenameEntryDialog (styled, smart SAVE→OVERWRITE on keystroke via glob). OverwriteConfirmDialog removed. assemble_png_sequence uses base_#####.png (5 digits). get_output_path uses stored base prefix. Theme._parse_padding() added (CSS shorthand). layout.dialogs.filename token added to dark.yaml. Merge: 35ea857.

[CODE] [2026-03-21] [fix/textyle-color] TextStyle Color Refactor: color_override (raw wx.Colour) replaced with color_token (theme string). TextStyle gains color_token field. reapply_theme now re-resolves from live theme on hot-reload.

[UI/UX] [2026-03-21] [fix/custombutton-cleanup] CustomButton Parameter Cleanup: Dropped primary/ghost/danger/color-override params. on_paint simplified to pure style_id token lookup. SetPrimary/SetDanger removed. Two ghost=True caller sites cleaned up.

[CODE] [2026-03-21] [fix/logger-alignment] Logger Alignment: Renamed 'simple'→'info' and 'verbose'→'debug' across 6 files. Backward compat via _legacy alias map in setup(). Merge: 2255abd.

[CODE] [2026-03-21] [fix/mesh-loading] Optimize Mesh Loading: Replaced scene.to_mesh() with manual vertex/face concatenation using scene.graph.nodes_geometry. Bypasses texture-atlas packing entirely. process=False avoids thread-unsafe trimesh internals in background loader. Merge: 297e72a.

[CODE] [2026-03-21] [fix/logger-flooding] Eliminate Logger Flooding: Added _active_level guard to SpinLogger.setup() — skips re-init if level unchanged. Applied logging level immediately on Advanced Options OK. Removed dead preset_controller.save_settings() (latent flooding bug). Cached list_presets() in check_preset_match to eliminate per-slider-tick disk I/O. Merge: 31f4c80.

[CODE] [2026-03-21] [fix/debounce-settings-saves] Debounce Settings Saves: All parameter handlers call schedule_save() — 500ms debounced write to disk. save_settings() skips write if MD5 hash of settings is unchanged. flush_save() used on close/cancel for guaranteed persistence. Previously settings were only saved on close/cancel/render-mode-change. Merge: b3ef6b4.

[UI/UX] [2026-03-21] [fix/preview-auto-close] Preview Auto-Close: Restored preview dismissal on parameter interaction via EVT_PARAMETER_INTERACTION (custom wx.CommandEvent). Fires from all 7 control click handlers when enabled. Single bind on controls_side_panel in main_panel. Registry lookup via event.GetId() matches against registered controls. Renamed on_left_panel_interaction → on_parameter_interaction. Added SpinRender/ui/events.py. Merge: 2445c85.

[CODE] [2026-03-11] Square view aspect ratio:
    - Fixed view to be actually square (800x800 resolution).
    - Synced viewport aspect ratio.
    - Calibrated camera distance for correct framing (CLI: 0.8, GL: 0.85).

[UI/UX] [2026-03-11] Render preview for mp4/gif:
    - Ensured preview panel visibility after ffmpeg render.
    - Enabled looping playback of rendered frames.

[UI/UX] [2026-03-11] Cancel button crash & rename:
    - Added safety checks for background threads (`if not self: return`).
    - Renamed button to "CLOSE" and updated icon to `mdi-exit-to-app`.
    - Explicitly cancel render engine on window close.

[CODE] [2026-03-12] Persistent loop presets/settings:
    - Implemented global session persistence (~/.spinrender/last_used.json).
    - Added cross-project fallback for new projects.
    - Included bg_color in preset serialization.

[UI/UX] [2026-03-12] Background color options:
    - Added CustomColorPicker matching Pencil design.
    - Supported Black, Slate, Cream, White, and Custom colors.
    - Applied color via FFmpeg overlay for consistent results.
    - Synced GL preview color on startup/change.

[CODE] [2026-03-12] Direction setting parity:
    - Fixed CCW/CW rotation by normalizing Euler angles to [0, 360).
    - Removed negative signs confusing kicad-cli parser.

[CODE] [2026-03-12] Logging system:
    - Implemented date-based logging with 30-day auto-cleanup.
    - Standardized logging levels: OFF, SIMPLE, VERBOSE.
    - Converted print() to structured logger calls.
    - Captured/labeled all CLI output in verbose logs.

[CODE] [2026-03-12] High quality rendering & floor removal:
    - Created "SpinRender Gold" config directory in resources.
    - Forced raytracing, post-processing, and disabled floor via KICAD_CONFIG_HOME.
    - Removed floor parameters from all presets.

[CODE] [2026-03-12] Main-thread mesh processing:
    - Moved all trimesh/numpy operations (loading, vertex processing, normal calculation) to main UI thread.
    - Prevented GIL-related crashes from native libraries in background threads.