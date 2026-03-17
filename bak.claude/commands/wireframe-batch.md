---
model: opus
description: Batch wireframe generation — discovers screens from SPEC inventory or tracker, fans out wireframe-agents in parallel, aggregates results and updates tracker
argument-hint: [section-filter] [screen-filter]
agents:
  - wireframe-agent
---

# Purpose

> **Layer 3 — Orchestration.** This is a command. It discovers screens that need wireframes, fans out Layer 2 wireframe-agents in parallel, collects their structured reports, and aggregates results into a tracker update. It does NOT generate wireframes — that's Layer 1's job via the agent.

## Stack Position

| Layer | Component | Relationship |
|-------|-----------|-------------|
| **L3 Command** | **`wireframe-batch` (this file)** | **discovers screens, spawns agents, aggregates tracker** |
| L2 Agent | `wireframe-agent` | generates + verifies one screen's wireframes |
| L1 Skill | `wireframe` | SVG generation logic, design system, SPEC.yaml |

## Variables

- **SECTION_FILTER:** $1 (default: all sections — filter to a specific section by name)
- **SCREEN_FILTER:** detected from $ARGUMENTS — filter to specific screen names
- **WIREFRAMES_DIR:** `./wireframes`
- **TRACKER:** `./wireframes/_reference/TRACKER.md`
- **AGENT_TIMEOUT:** 300000
- **RUN_ID:** `{YYYYMMDD_HHMMSS}_{6-char-uuid}` — generated once at start of run

## Codebase Structure

```
wireframes/
├── _reference/
│   ├── DESIGN-SYSTEM.svg
│   ├── TRACKER.md
│   └── PROCESS.md
├── auth/
│   ├── login.svg
│   ├── login-desktop.svg
│   └── SPEC.yaml
├── dashboard/
│   ├── overview.svg
│   ├── overview-desktop.svg
│   └── SPEC.yaml
└── ...
```

## Instructions

### Phase 1: Discover

1. Read the TRACKER at `${TRACKER}` to identify screens with incomplete wireframes (⬜ status)
2. If TRACKER doesn't exist, scan for SPEC.yaml files via `Glob wireframes/*/SPEC.yaml` and extract screen entries that are missing SVG files
3. If SECTION_FILTER is provided, narrow to screens in that section only
4. If SCREEN_FILTER is provided, narrow to screens matching that name substring
5. For each discovered screen, check whether mobile SVG, desktop SVG, and SPEC entry already exist — only include screens with missing artifacts
6. Build flat list of work items: `{ screen_name, section, spec_hints (from SPEC.yaml if entry exists) }`
7. If no screens need wireframes, report that and stop
8. Read the design system reference to confirm it exists — if missing, report failure and stop

### Phase 2: Spawn

9. Use TeamCreate to create team named `wireframe-batch`
10. Use TaskCreate to create one task per screen
11. For each screen, spawn a `wireframe-agent` teammate via Task tool:
    - `subagent_type: wireframe-agent`
    - `team_name: "wireframe-batch"`
    - Include in the prompt:
      - SCREEN_NAME and SECTION
      - SPEC_HINTS if a SPEC.yaml entry already defines data sources or components
      - Path to design system reference
      - Names of existing section wireframes (for pattern matching)
12. Launch ALL teammates in a single message for parallel execution

### Phase 3: Collect

13. Wait for teammate messages (auto-delivered as each completes)
14. Parse each agent's Report:
    - Extract `STATUS:` line → SUCCESS or FAILURE
    - Extract artifacts table → file paths and validation status
    - Extract verification table → per-check pass/fail
15. Mark tasks as completed via TaskUpdate
16. If a teammate times out or crashes, mark that screen as FAILURE with available output

### Phase 4: Report

17. Send shutdown requests to all teammates
18. Call TeamDelete to clean up
19. Update the TRACKER:
    - Mark completed screens as ✅ for mobile, desktop, SPEC columns
    - Recalculate section and total completion percentages
    - Add changelog entry: `{date} — Batch run {RUN_ID}: {N} screens generated`
20. Aggregate results into summary report:

```markdown
# Wireframe Batch Summary

**Run:** {RUN_ID}
**Screens:** {total} total | {passed} generated | {failed} failed
**Sections:** {sections touched}
**Status:** ✅ ALL GENERATED | ❌ PARTIAL | ❌ ALL FAILED

## Results

| # | Screen | Section | Status | Mobile | Desktop | SPEC | Verification |
|---|--------|---------|--------|--------|---------|------|-------------|
| 1 | login | auth | ✅ PASS | ✅ | ✅ | ✅ | 6/6 checks |
| 2 | overview | dashboard | ❌ FAIL | ✅ | ❌ | ❌ | 2/6 checks |

## Failures
(Only present if there are failures)

### Screen: {failed screen name}
**Section:** {section}
**Agent Report:** {full failure report from agent}

## Tracker
Updated: `{TRACKER}`
Completion: {before}% → {after}%

## Files Created
{list all new SVG and SPEC files}
```

## Resilience Rules

- One agent failing does NOT abort the run — continue collecting from others
- Missing SPEC.yaml entries are fine — the agent creates them
- Missing design system reference is a hard stop — all screens depend on it
- Timeouts mark the screen as FAILURE with whatever partial output is available
- Always clean up the team even if the run fails partway through
- Always update the tracker, even for partial runs — mark failures as ⬜ with a note
