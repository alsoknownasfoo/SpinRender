# Product Requirements Document (PRD)

## Product Name

**SpinRender**

## Document Metadata

- **Version:** 0.4 (Draft)
- **Date:** 2026-03-13
- **Status:** Draft / Alignment / Implementation Sync
- **Owner:** Founding Product + Engineering

---

## 1) Problem Statement

KiCad users can design excellent boards, but turning those designs into visually compelling animations for demos, crowdfunding, documentation, social media, and stakeholder updates is still difficult.

Today’s workflow often requires:

- Exporting models manually from KiCad
- Learning external 3D tools with steep learning curves
- Rebuilding scenes repeatedly for each new board revision
- Complex rendering setups for animation quality and performance

This creates friction and prevents many hardware creators from sharing their work in a polished, engaging format.

---

## 2) Vision

Make beautiful PCB animation rendering **accessible inside the KiCad workflow**, so any hardware creator can go from board design to shareable motion visuals in minutes.

---

## 3) Goals and Non-Goals

### Goals

1. Enable users to produce attractive animated board renders quickly from KiCad projects.
2. Provide sensible cinematic defaults (camera, lighting, materials, motion presets).
3. Support repeatable outputs across board revisions.
4. Reduce need for external DCC tools for common showcase use cases.

### Non-Goals (MVP)

1. Replacing full-featured 3D suites (e.g., Blender workflows).
2. Full physically accurate simulation pipeline.
3. Real-time game-engine-level scene editing.
4. Complex VFX compositing features.

---

## 4) Target Users

### Primary

- **Indie hardware makers** showcasing prototypes
- **Open-source hardware maintainers** preparing release media
- **Startup engineering teams** creating demo visuals for investors/customers

### Secondary

- Educators producing teaching visuals
- Technical marketers creating launch content

---

## 5) User Jobs To Be Done

1. “When my board is ready, I want to generate a polished animation quickly so I can share progress publicly.”
2. “When I revise a board, I want to re-render with the same style without rebuilding everything.”
3. “When I need launch assets, I want predictable output formats for social and web.”

---

## 6) User Experience Overview

### Entry Points

- KiCad toolbar button / menu action: **Render with SpinRender**
- Project-local preset and last-used settings persisted under `.spinrender/`

### Core Flow (MVP)

1. User opens board in KiCad.
2. User launches SpinRender panel.
3. User sees a two-panel layout: controls on the left, auto-playing preview loop on the right.
4. User selects a loop preset (currently Hero, Spin, or Flip).
5. User adjusts rotation settings and lighting preset.
6. Preview updates live as controls change.
7. User clicks **RENDER** to export the final animation.

### Current State Snapshot

The current implementation is broadly aligned with the MVP direction, but some behaviors are more concrete than the original PRD and some planned simplifications have not yet been applied.

- The plugin is implemented as a KiCad action plugin with a dedicated floating window.
- The UI currently exposes a universal-joint-style rotation model with four controls: `Board Tilt`, `Board Roll`, `Spin Tilt`, and `Spin Heading`.
- The preview supports `wireframe`, `shaded`, and `both` modes, plus looping playback of rendered frames after export.
- The exporter currently supports `MP4`, `GIF`, and `PNG Sequence` outputs.
- Project-local presets and last-used settings are persisted today; an external styling/configuration format is still future work.

### UX Principles

- Fast defaults over deep setup
- Progressive disclosure (simple first, advanced later)
- Deterministic, reproducible outputs

---

## 7) Functional Requirements

### FR-1: KiCad Integration

- Plugin installs using standard KiCad plugin mechanism.
- Plugin can read current board context and associated 3D resources.
- Plugin launches a dedicated UI panel/dialog.

### FR-2: Scene Presets

- Include at least 3 built-in loop presets for MVP:
   - Hero
   - Spin
   - Flip
- Presets include tilt baseline, loop direction, light rig, and timing defaults.

### FR-2A: Tilted Loop Control Model (Core UX)

- Main UI exposes a constrained rotation model instead of raw timeline/keyframe editing.
- All rotation-related controls are grouped under a single **Rotation Settings** category:
   - **Board Tilt**
   - **Board Roll**
   - **Spin Tilt**
   - **Spin Heading**
   - **Rotation Period** (`seconds per revolution`)
   - **Direction** — presented as a CW/CCW segmented toggle (not a simple button)
- Loop generation must ensure deterministic, repeatable `360°` progression per export.
- Easing remains linear internally in MVP; no dedicated easing control is currently exposed in the UI.
- Frame rate is fixed at 30 fps and is not user-configurable in MVP.

### FR-2B: Lighting Presets

- Include at least 3 built-in lighting presets for MVP:
   - Studio (neutral, balanced three-point lighting)
   - Dramatic (high-contrast, directional key light)
   - Soft (diffused, low-shadow ambient lighting)
- Lighting presets are selectable via a dedicated Lighting section in the UI.
- Each preset defines key light position, fill light intensity, and ambient level.
- Current implementation note: the preview also exposes a `Workspace` lighting option to approximate KiCad viewer lighting; this should be treated as implementation-specific until productized.

### FR-3: Material/Look Controls (MVP-Lite)

Core Aesthetic: A "High-Density Industrial" Dark Mode UI inspired by Blender and technical CAD software.

- Geometric Precision:
   - Edges: Prefer 4px border-radius with radii expansion/contraction on elements within 4px distance.
    - Layout: A rigid grid-based system where components share 1px borders. Use "crosshair" or "L-bracket" corner accents to define panel boundaries.
   - Depth: Prefer 1px inset or outset borders in varying shades of grey to create structural depth and "pressed" vs. "raised" states.

- Color Palette & Typography:
    - Background: Deep charcoal or "matte black" (#121212 to #1A1A1A).
    - Signal Colors (iOS-inspired but high-contrast):
    - Cyan/Teal: For primary active sliders and focal points.
    - Yellow/Amber: For numerical data and status values.
    - Green: For positive toggles (e.g., "CCW" or "Active").
    - Orange: For secondary branding or warning accents.
   - Typography: Monospaced fonts for all numerical data (e.g., JetBrains Mono) to ensure character alignment. Distinct display and label fonts are acceptable if they preserve the high-density industrial aesthetic.

- Component Styling:
    - Sliders: Minimalist tracks with a thick, rectangular block as the handle ("thumb"). The handle should use a solid signal color.
    - Input Boxes: Sharp rectangular boxes with a high-contrast border. Text should be right-aligned for numerical precision.
    - Icons: Simple, line-art vector icons with uniform stroke weights. No fills, only strokes in the designated signal color.

- Metadata & Overlays:
    - Include technical metadata in the corners (e.g., "v1.0", "300 f", "deg") in a smaller, muted grey font to reinforce the "pro-tool" utility vibe.

### FR-4: Export Pipeline

- Export animation to at least one widely used format (MP4 preferred for MVP).
- Additional formats may be supported if they do not materially complicate the MVP experience.
- Optional image sequence export (PNG) if feasible in MVP.
- Configurable output resolution (300px minimum).
- Frame rate is fixed at 30 fps (not user-configurable in MVP).
- Primary export action is labeled **RENDER** (not "Export").
- An **Advanced Options** button opens a modal/dialog for secondary settings (output path, parameter override).

Current implementation note:
- The current product already supports `MP4`, `GIF`, and `PNG Sequence` exports.

### FR-5: Revision-Friendly Reuse

- Save/load render settings per project.
- Re-render after board updates without full manual reconfiguration.
- Current implementation note: settings are persisted as JSON files under `.spinrender/`, including preset files and `last_used.json`.

### FR-6: Preview & Validation

- Preview is an always-playing animation view displayed in the right panel of the UI.
- Preview auto-plays continuously — there is no separate "Preview" button. The loop updates live as the user adjusts rotation, lighting, and preset controls.
- Preview currently uses an OpenGL board preview for live interaction, with a rendered-frame playback overlay shown after export.
- Validate missing assets and show actionable error messages.

### FR-7: Error Handling

- Fail gracefully with clear diagnostics for:
  - Missing models
  - Unsupported board/model data
  - Export path/write failures

---

## 8) Non-Functional Requirements

1. **Performance:**
   - Initial preview generation under 5 seconds for typical medium boards (target).
   - Render progress feedback for exports.

2. **Reliability:**
   - Recoverable failure states with no corruption of KiCad project files.

3. **Compatibility:**
   - Target KiCad 8+ on macOS, Windows, Linux (MVP may ship in phased OS support).

4. **Security & Privacy:**
   - No telemetry in MVP unless explicitly opt-in.
   - No external upload by default.

5. **Maintainability:**
   - Modular rendering backend abstraction to support future renderer options.

---

## 9) Success Metrics (MVP)

### Adoption

- Number of plugin installs
- Weekly active rendering users

### Activation

- % of installed users who complete first render within 24 hours

### Output Quality / Utility

- % of exports completed successfully
- User-rated satisfaction for “visual quality” and “ease of use”

### Efficiency

- Median time from plugin open to first exported clip

---

## 10) MVP Scope

### In Scope

- KiCad plugin shell + UI panel (two-panel layout: controls left, preview right)
- 3 built-in loop presets
- 3 lighting presets (Studio, Dramatic, Soft)
- Basic look themes
- MP4 export at fixed 30 fps (480p minimum)
- Per-project render setting persistence
- Clear error handling for common failure modes
- Grouped rotation settings UI with deterministic loop controls
- Auto-playing preview (no separate preview action)
- Advanced options modal for secondary export settings
- Live preview behavior tuned for fast interaction

### Current State (2026-03-13)

- Implemented: KiCad action plugin shell and floating panel UI
- Implemented: built-in `Hero`, `Spin`, and `Flip` loop presets
- Implemented: `Studio`, `Dramatic`, and `Soft` lighting presets, plus an implementation-specific `Workspace` preview mode
- Implemented: `MP4`, `GIF`, and `PNG Sequence` export formats at fixed `30 fps`
- Implemented: project-local and global persistence for presets and last-used settings
- Implemented: always-on OpenGL preview with post-render looping playback overlay
- Implemented: advanced options dialog for output path, CLI overrides, and logging level
- Partially aligned: the current rotation model is more explicit than the originally planned simplified tilt-only model
- Not yet implemented: external config-driven styling/theme system described in UI planning docs

### Out of Scope

- Custom light definitions
- Easing animation options
- Arbitrary keyframe authoring and timeline editing

---

## 11) Risks and Mitigations

1. **Renderer complexity / performance variability**
   - Mitigation: Start with constrained presets and bounded quality settings.

2. **Cross-platform packaging friction**
   - Mitigation: MVP with one reference platform first, then phased platform expansion.

3. **Asset inconsistencies from KiCad projects**
   - Mitigation: Strong preflight checks + user-visible remediation steps.

4. **Scope creep into full DCC tool**
   - Mitigation: Enforce strict MVP boundaries and non-goals.

---

## 12) Release Plan (Proposed)

### Phase 0: Definition (Current)

- Finalize PRD
- Define architecture and technical spike plan

### Phase 1: MVP Build

- Plugin integration + UI scaffold
- Presets + preview + export
- Internal alpha testing
- Align implementation details and docs on preset naming, rotation model, and export scope

### Phase 2: Beta

- Expand compatibility
- Performance tuning
- User feedback loop and UX iteration

### Phase 3: Public Launch

- Stable docs and install flow
- Example templates and sample outputs

---

## 13) Open Questions

1. ~~Should direction default remain `CCW` globally or be preset-dependent?~~ **Resolved:** Direction is a CW/CCW segmented toggle, default per preset.
2. Should rotation period support both `seconds` and explicit `frame count` entry in UI?
3. Should virtualized preview include optional quality tiers for very large boards?
4. Should "beautiful defaults" include branded preset packs?
5. What licensing model (open-source only vs dual model)?

---

## 14) Appendix: Candidate Future Features

- Turntable + exploded view choreography
- Depth of field and motion blur tuning
- Bezier easing profile support for non-linear loop timing
- Scene annotations / callouts for component highlights
- Batch render presets for marketing channels
- Template gallery and community-shared styles
