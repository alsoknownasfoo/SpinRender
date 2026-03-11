# Product Requirements Document (PRD)

## Product Name

**SpinRender**

## Document Metadata

- **Version:** 0.3 (Draft)
- **Date:** 2026-03-06
- **Status:** Draft / Alignment
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
- Optional project-side config file for reusable presets

### Core Flow (MVP)

1. User opens board in KiCad.
2. User launches SpinRender panel.
3. User sees a two-panel layout: controls on the left, auto-playing preview loop on the right.
4. User selects a loop preset (e.g., hero orbit, top sweep, angle reveal).
5. User adjusts rotation settings (view tilt, rotation period, easing, direction) and lighting preset.
6. Preview updates live as controls change.
7. User clicks **RENDER** to export the final animation.

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
   - Hero Orbit
   - Top Sweep
   - Angle Reveal
- Presets include tilt baseline, loop direction, light rig, and timing defaults.

### FR-2A: Tilted Loop Control Model (Core UX)

- Main UI exposes a simplified loop model instead of raw XYZ keyframing controls.
- All rotation-related controls are grouped under a single **Rotation Settings** category:
   - **View Tilt (θ)** `0°..90°`
   - **Rotation Period** (`seconds per revolution`)
   - **Easing Profile** — displayed as a graphical curve visualization (linear in MVP)
   - **Direction** — presented as a CW/CCW segmented toggle (not a simple button)
- Loop generation must ensure deterministic, repeatable `360°` progression per export.
- Easing remains linear in MVP; non-linear easing is deferred.
- Frame rate is fixed at 30 fps and is not user-configurable in MVP.

### FR-2B: Lighting Presets

- Include at least 3 built-in lighting presets for MVP:
   - Studio (neutral, balanced three-point lighting)
   - Dramatic (high-contrast, directional key light)
   - Soft (diffused, low-shadow ambient lighting)
- Lighting presets are selectable via a dedicated Lighting section in the UI.
- Each preset defines key light position, fill light intensity, and ambient level.

### FR-3: Material/Look Controls (MVP-Lite)

Core Aesthetic: A "High-Density Industrial" Dark Mode UI inspired by Blender and technical CAD software.

- Geometric Precision:
    - Edges: Strict 0px border-radius (sharp corners only). No rounded corners on buttons, sliders, or panels.
    - Layout: A rigid grid-based system where components share 1px borders. Use "crosshair" or "L-bracket" corner accents to define panel boundaries.
    - Depth: No drop shadows. Use 1px inset or outset borders in varying shades of grey to create structural depth and "pressed" vs. "raised" states.

- Color Palette & Typography:
    - Background: Deep charcoal or "matte black" (#121212 to #1A1A1A).
    - Signal Colors (iOS-inspired but high-contrast):
    - Cyan/Teal: For primary active sliders and focal points.
    - Yellow/Amber: For numerical data and status values.
    - Green: For positive toggles (e.g., "CCW" or "Active").
    - Orange: For secondary branding or warning accents.
    - Typography: Monospaced fonts for all numerical data (e.g., JetBrains Mono) to ensure character alignment. Sans-serif for labels (e.g., Inter or IBM Plex Sans).

- Component Styling:
    - Sliders: Minimalist tracks with a thick, rectangular block as the handle ("thumb"). The handle should use a solid signal color.
    - Input Boxes: Sharp rectangular boxes with a high-contrast border. Text should be right-aligned for numerical precision.
    - Icons: Simple, line-art vector icons with uniform stroke weights. No fills, only strokes in the designated signal color.

- Metadata & Overlays:
    - Include technical metadata in the corners (e.g., "v1.0", "300 f", "deg") in a smaller, muted grey font to reinforce the "pro-tool" utility vibe.

### FR-4: Export Pipeline

- Export animation to at least one widely used format (MP4 preferred for MVP).
- Optional image sequence export (PNG) if feasible in MVP.
- Configurable output resolution (1080p minimum).
- Frame rate is fixed at 30 fps (not user-configurable in MVP).
- Primary export action is labeled **RENDER** (not "Export").
- An **Advanced Options** button opens a modal/dialog for secondary settings (output path, parameter override).

### FR-5: Revision-Friendly Reuse

- Save/load render settings per project.
- Re-render after board updates without full manual reconfiguration.

### FR-6: Preview & Validation

- Preview is an always-playing, low-resolution unshaded animation loop displayed in the right panel of the UI.
- Preview auto-plays continuously — there is no separate "Preview" button. The loop updates live as the user adjusts rotation, lighting, and preset controls.
- Preview is virtualized from a small set of rendered source images and manipulated in UI for responsiveness.
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
- 3 loop presets
- 3 lighting presets (Studio, Dramatic, Soft)
- Basic look themes
- MP4 export at fixed 30 fps (1080p)
- Per-project render setting persistence
- Clear error handling for common failure modes
- Grouped rotation settings UI (tilt, period, easing curve, CW/CCW toggle)
- Auto-playing low-res preview loop (no separate preview action)
- Advanced options modal for secondary export settings
- Virtualized preview behavior for fast interaction

### Out of Scope

- 

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
