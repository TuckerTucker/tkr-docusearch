---
model: opus
description: <One-line description — what this command orchestrates and the result it produces>
argument-hint: [optional-arg-1] [optional-arg-2]
agents:
  - <agent-name>
---

# Purpose

> **Layer 3 — Orchestration.** This is a command. It discovers work, fans out Layer 2 agents in parallel, collects their structured reports, and aggregates results. It does NOT execute domain logic — that belongs in Layer 1 (skills). It does NOT wrap skills directly — that's Layer 2's job. It orchestrates.

## Stack Position

| Layer | Component | Relationship |
|-------|-----------|-------------|
| **L3 Command** | **`<command-name>` (this file)** | **discovers work, spawns agents, aggregates reports** |
| L2 Agent | `<agent-name>` | executes scoped tasks, returns structured reports (see agent's Report section) |
| L1 Skill | `<skill-name>` | provides raw capability (invoked by the agent, not by this command) |

When creating this command, remember:
- **You orchestrate, you don't execute.** If you're calling a skill directly, you're skipping L2. Extract that into an agent.
- **You parse agent Reports.** Your aggregation depends on the agent's STATUS line, table format, and failure detail. If the agent's report format changes, this command breaks.
- **Fan out in a single message.** Launch ALL agent teammates in one Tool call for true parallelism. Sequential spawning defeats the purpose of L3.
- **Be resilient.** One agent failing does not abort the run. Collect what you can, report what failed.
- **Clean up always.** TeamDelete runs even if the run fails partway through.

<One paragraph describing what this command orchestrates and what the user gets at the end.>

## Variables

- **VAR_1:** $1 (default: `"value"` — description)
- **FILTER:** detected from $ARGUMENTS — keyword detection rules
- **AGENT_TIMEOUT:** 300000
- **OUTPUT_DIR:** `./output/<command-name>` — base directory for run artifacts
- **RUN_DIR:** `{OUTPUT_DIR}/{YYYYMMDD_HHMMSS}_{short-uuid}` — generated once at start of run

## Codebase Structure

```
<directory>/
└── <source>/
    ├── file-a.yaml
    └── *.yaml
output/
└── <command-name>/
    └── 20260220_143022_a1b2c3/
        ├── <dimension-or-task>/
        └── <dimension-or-task>/
```

## Instructions

### Phase 1: Discover

1. Use Glob to find work items matching the source pattern
2. If FILTER is provided, narrow to matching items
3. Parse each source file; on parse error, log warning and skip (do not abort)
4. Build flat list of work items with metadata (source file, name, parameters)
5. If no items found, report that and stop
6. Generate RUN_DIR with timestamp and 6-char UUID

### Phase 2: Spawn

7. Use TeamCreate to create team named `<command-name>`
8. Use TaskCreate to create one task per work item
9. For each work item, spawn an agent teammate via Task tool:
   - `subagent_type: <agent-name>`
   - `team_name: "<command-name>"`
   - Include work item details, output path, and variables in the prompt
10. Launch ALL teammates in a single message for parallel execution

### Phase 3: Collect

11. Wait for teammate messages (auto-delivered as each completes)
12. Parse each agent's Report:
    - Extract `STATUS:` line → SUCCESS or FAILURE
    - Extract table rows → item-level results
    - Extract Failure Detail → root cause for failed items
13. Mark tasks as completed via TaskUpdate
14. If a teammate times out or crashes, mark that item as FAILURE with available output

### Phase 4: Report

15. Send shutdown requests to all teammates
16. Call TeamDelete to clean up
17. Aggregate results into summary report:

```markdown
# <Command Name> Summary

**Run:** {date and time}
**Items:** {total} total | {passed} passed | {failed} failed
**Status:** ✅ ALL PASSED | ❌ PARTIAL FAILURE | ❌ ALL FAILED

## Results

| # | Item | Source | Status | <Key Metric> |
|---|------|--------|--------|--------------|
| 1 | {name} | {source} | ✅ PASS | {value} |
| 2 | {name} | {source} | ❌ FAIL | {value} |

## Failures
(Only present if there are failures)

### Item: {failed item name}
**Source:** {source file}
**Agent Report:** {full failure report from agent}

## Artifacts
All output saved to: `{RUN_DIR}/`
```

## Resilience Rules

- One agent failing does NOT abort the run — continue collecting from others
- Parse errors in source files produce warnings, not failures
- Timeouts mark the item as FAILURE with whatever partial output is available
- Always clean up the team even if the run fails partway through
