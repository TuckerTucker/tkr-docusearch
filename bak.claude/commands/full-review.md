---
model: opus
description: Comprehensive codebase review — fans out review-agents across all dimensions in parallel, aggregates scored findings into a single dashboard
argument-hint: [mode] [scope]
agents:
  - review-agent
---

# Purpose

> **Layer 3 — Orchestration.** This is a command. It selects review dimensions based on mode, fans out one `review-agent` per dimension in parallel, collects scored findings, and aggregates into a dashboard with overall health score. It does NOT perform analysis — that's the `repo-review` skill (L1) via the agent (L2).

## Stack Position

| Layer | Component | Relationship |
|-------|-----------|-------------|
| **L3 Command** | **`full-review` (this file)** | **selects dimensions, spawns agents, aggregates scores** |
| L2 Agent | `review-agent` | executes one dimension, returns scored findings |
| L1 Skill | `repo-review` | analyzes codebase for a single dimension |

## Variables

- **MODE:** $1 (default: `full`) — determines which dimensions to run
- **SCOPE:** $2 (default: `.`) — directory or glob to scope all reviews
- **AGENT_TIMEOUT:** 300000
- **OUTPUT_DIR:** `./output/review`
- **RUN_DIR:** `{OUTPUT_DIR}/{YYYYMMDD_HHMMSS}_{6-char-uuid}`

### Review Modes

| Mode | Dimensions |
|------|-----------|
| `full` | all 9 dimensions |
| `security` | security, dependencies |
| `quality` | quality, architecture |
| `performance` | performance, testing |
| `compliance` | accessibility, documentation, git-practices |

### Dimension List

All 9 dimensions: `security`, `quality`, `performance`, `accessibility`, `testing`, `documentation`, `architecture`, `dependencies`, `git-practices`

## Instructions

### Phase 1: Discover

1. Parse MODE from $ARGUMENTS — default to `full` if not provided
2. Parse SCOPE from $ARGUMENTS — default to `.` if not provided
3. Resolve MODE to dimension list using the Review Modes table
4. Generate RUN_DIR with timestamp and 6-char UUID
5. Create output directory via `mkdir -p ${RUN_DIR}`

### Phase 2: Spawn

6. Use TeamCreate to create team named `full-review`
7. Use TaskCreate to create one task per dimension
8. For each dimension, spawn a `review-agent` teammate via Task tool:
   - `subagent_type: review-agent`
   - `team_name: "full-review"`
   - Include in the prompt:
     - DIMENSION name
     - SCOPE path
     - OUTPUT_DIR for artifacts
9. Launch ALL teammates in a single message for parallel execution

### Phase 3: Collect

10. Wait for teammate messages (auto-delivered as each completes)
11. Parse each agent's Report:
    - Extract `STATUS:` line → SUCCESS or FAILURE
    - Extract `**Score:**` → numeric score out of 100
    - Extract `**Findings:**` → total count and severity breakdown
    - Extract findings table → individual issues
    - Extract `### Top Recommendations` → priority fixes
12. Mark tasks as completed via TaskUpdate
13. If a teammate times out or crashes, mark that dimension as FAILURE with score 0

### Phase 4: Report

14. Send shutdown requests to all teammates
15. Call TeamDelete to clean up
16. Calculate overall health score: weighted average of dimension scores
    - Security and architecture weighted 1.5x (critical dimensions)
    - All others weighted 1.0x
17. Aggregate results into summary report:

```markdown
# Codebase Review Summary

**Run:** {RUN_ID}
**Mode:** {mode}
**Scope:** {scope}
**Dimensions:** {total} total | {passed} healthy | {warning} warning | {critical} critical
**Overall Health:** {score}/100 {grade}

## Scorecard

| # | Dimension | Score | Findings | Status |
|---|-----------|-------|----------|--------|
| 1 | security | 85/100 | 3 (0c, 1h, 2m) | ⚠️ WARNING |
| 2 | quality | 92/100 | 2 (0c, 0h, 2m) | ✅ HEALTHY |
| 3 | testing | 45/100 | 8 (1c, 3h, 4m) | ❌ CRITICAL |
| ... | ... | ... | ... | ... |

## Grade Scale
- ✅ HEALTHY: 80-100
- ⚠️ WARNING: 50-79
- ❌ CRITICAL: 0-49

## Critical Findings
(All critical and high severity findings across dimensions)

| # | Dimension | Finding | Severity | File | Line |
|---|-----------|---------|----------|------|------|
| 1 | security | Hardcoded API key | critical | src/config.ts | 12 |
| 2 | testing | No tests for auth module | high | core/auth/ | — |

## Top Recommendations
(Merged and deduplicated from all dimensions, ordered by impact)

1. {highest impact recommendation}
2. {second highest}
3. {third highest}
4. {fourth highest}
5. {fifth highest}

## Dimension Details
(Full findings for each dimension that scored below 80)

### {dimension name} — {score}/100
{full agent report}

## Artifacts
All output saved to: `{RUN_DIR}/`
```

## Resilience Rules

- One dimension failing does NOT abort the run — continue collecting from others
- Failed dimensions get score 0 and appear as ❌ CRITICAL in the scorecard
- Timeouts mark the dimension as FAILURE with whatever partial output is available
- Always clean up the team even if the run fails partway through
- Overall health score excludes failed dimensions from the weighted average (to avoid unfairly penalizing partial runs) but notes them as unscored
