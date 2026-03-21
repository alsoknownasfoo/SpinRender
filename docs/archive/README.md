# Archive

This directory contains historical planning and analysis documents that have been superseded by the current implementation.

## What's Archived

### Planning Documents (pre-2026-03-21)

- **ARCHIVED_ARCHITECTURE_IMPLEMENTATION.md** (2,356 lines)
  - Comprehensive plan for 8 non-theme architectural improvements
  - References missing MIGRATION_STRATEGY.md
  - Status: Partially implemented, planning stage obsolete

- **ARCHIVED_PROJECT_PLAN.md** (584 lines)
  - UI Refactor Project Plan with tasks, priorities, dependencies
  - Status: Most tasks completed; consolidated into GUIDE_DEVELOPMENT_WORKFLOW.md

- **ARCHIVED_TDD_PLAN.md** (762 lines)
  - Testing strategy, mock approach, test infrastructure
  - Status: Consolidated into GUIDE_DEVELOPMENT_WORKFLOW.md

- **ARCHIVED_PRD.md** (353 lines)
  - Product Requirements Document (v0.4 Draft, 2026-03-13)
  - Status: May be outdated; kept for historical context

### Analysis Documents

- **ARCHIVED_UI_ANALYSIS.md** (323 lines)
- **ARCHIVED_COMPONENT_PATTERNS.md** (332 lines)
- **ARCHIVED_COMPONENT_CONVENTIONS.md** (243 lines)
- **ARCHIVED_UI_REFACTOR.md** (75 lines)
- **ARCHIVED_UI_REFACTOR_TASKLIST.md** (56 lines)
- **ARCHIVED_LAYOUT_AND_LISTVIEW_PLAN.md** (47 lines)

Status: All superseded by auto-generated CODEMAPS/ reference.

### Operational Notes

- **ARCHIVED_KICAD_CLI_RENDER_NOTES.md** (137 lines)
  - Status: Operational reference kept; content integrated into GUIDE_DEVELOPMENT_WORKFLOW.md

### Theme Development Artifacts

- **theme_v2_drafts/**
  - Draft YAML files from theme v2 development:
    - `dark.yaml`
    - `light.yaml`
    - `locale_en.yaml`
  - Status: Theme v2 complete; live themes in SpinRender/resources/themes/ and SpinRender/resources/locale/

### Visual Assets

- **VISUAL_REFERENCE.jpg**

## Current Documentation Structure

```
docs/
├── README.md                          # Navigation hub
├── GUIDE_DEVELOPMENT_WORKFLOW.md      # Active developer guide
├── CODEMAPS/                          # Auto-generated architecture reference
│   ├── architecture.md
│   ├── modules.md
│   ├── frontend.md
│   ├── data.md
│   └── dependencies.md
└── reference/                         # Canonical specifications
    ├── theme-schema.md
    ├── theme-schema-v2.md
    ├── locale-schema.md
    ├── locale-schema-v2.md
    ├── theme-design-principles.md
    └── theme-validation.md
```

## Why Archive?

- Reduce clutter: 25+ active files → 8-10 active files
- Eliminate duplication: Multiple overlapping planning docs consolidated
- Fix broken references: Missing MIGRATION_STRATEGY.md references removed
- Separate current from historical: Active docs live in root; historical preserved here

## Need Information from an Archived Doc?

The archive is preserved intact. Check here for:
- Historical context for architectural decisions
- Original PRD or project plans
- Test infrastructure evolution

But for **current development**, always start with:
1. README.md (navigation)
2. CODEMAPS/ (architecture)
3. GUIDE_DEVELOPMENT_WORKFLOW.md (how-to)
4. reference/ (specs)

**Last Updated**: 2026-03-21
