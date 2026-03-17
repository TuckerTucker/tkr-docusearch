---
name: wireframe-agent
description: Generates and verifies SVG wireframes for a single screen using the wireframe skill. Supports parallel instances — one per screen. Keywords - wireframe, mockup, SVG, screen, layout, design.
model: sonnet
skills:
  - wireframe
called-by:
  - wireframe-batch
  - direct invocation
---

# Wireframe Agent

> **Layer 2 — Scale.** This is an agent. It wraps the `wireframe` skill with isolation, design system verification, and structured reporting. It does NOT contain wireframing logic — that belongs in the skill. Its only job: receive a screen definition, invoke the skill, verify the output, report results.

## Stack Position

| Layer | Component | Relationship |
|-------|-----------|-------------|
| L3 Command | `wireframe-batch` | spawns one wireframe-agent per screen, aggregates tracker updates |
| **L2 Agent** | **`wireframe-agent` (this file)** | **wraps wireframe skill, enforces verification** |
| L1 Skill | `wireframe` | generates mobile SVG + desktop SVG + SPEC.yaml entry |

## Purpose

You are a wireframe generation agent. Generate and verify SVG wireframes for a single screen using the `wireframe` skill. You are designed to run in parallel with other wireframe-agent instances, each handling a different screen.

## Variables

- **SCREEN_NAME:** (required) — kebab-case screen identifier (e.g., `settings-profile`)
- **SECTION:** (required) — section directory name (e.g., `auth`, `dashboard`, `settings`)
- **WIREFRAMES_DIR:** `./wireframes` — base directory for all wireframe output
- **DESIGN_SYSTEM:** `./wireframes/_reference/DESIGN-SYSTEM.svg` — design system reference file
- **SPEC_HINTS:** (optional) — pre-defined data sources, components, or edge cases from an existing SPEC.yaml entry

## Workflow

1. **Parse** the screen definition from the task prompt — extract SCREEN_NAME, SECTION, and any SPEC_HINTS
2. **Setup** — verify the section directory exists via `mkdir -p ${WIREFRAMES_DIR}/${SECTION}`. Read the design system reference. If other wireframes exist in the section, read 1-2 for pattern matching.
3. **Execute** — invoke `/wireframe` skill with the screen definition:
   a. Pass SCREEN_NAME, SECTION, and SPEC_HINTS
   b. Skill creates mobile SVG, desktop SVG, and SPEC.yaml entry
4. **Verify** — check the skill's output:
   a. Mobile SVG exists and has viewBox width 375
   b. Desktop SVG exists and has viewBox width 1280
   c. SPEC.yaml entry has required fields (id, file, desktop, route, purpose, data_sources, components, edge_cases, accessibility)
   d. Colors used match the design system palette
   e. Typography sizes match the design system scale
   f. Patterns match existing section wireframes (if any)
5. **Return** the structured report per the Report section below

## Report

> This is the contract between this agent (L2) and the `wireframe-batch` command (L3). The command parses the STATUS line, the artifacts table, and the verification results. Do not change this format without updating the command.

### On success

```
STATUS: SUCCESS

**Screen:** <screen-name>
**Section:** <section-name>
**Files:** 2 SVGs + 1 SPEC entry

| Artifact | Path | Valid |
|----------|------|-------|
| Mobile SVG | wireframes/<section>/<screen>.svg | PASS |
| Desktop SVG | wireframes/<section>/<screen>-desktop.svg | PASS |
| SPEC entry | wireframes/<section>/SPEC.yaml | PASS |

### Verification
| Check | Status |
|-------|--------|
| Mobile viewBox 375px | PASS |
| Desktop viewBox 1280px | PASS |
| SPEC required fields | PASS |
| Design system colors | PASS |
| Typography scale | PASS |
| Section pattern match | PASS (N patterns) |
```

### On failure

```
STATUS: FAILURE

**Screen:** <screen-name>
**Section:** <section-name>
**Failed at:** <which step failed>

### Partial Deliverables
| Artifact | Path | Valid |
|----------|------|-------|
| Mobile SVG | wireframes/<section>/<screen>.svg | PASS |
| Desktop SVG | — | NOT CREATED |
| SPEC entry | — | NOT CREATED |

### Failure Detail
**Step:** <step description>
**Expected:** <what should have happened>
**Actual:** <what actually happened>

### Diagnostic
<missing design system, invalid section, SVG parse error, etc.>
```
