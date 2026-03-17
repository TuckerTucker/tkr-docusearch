---
name: <agent-name>
description: <One-line description of what this agent does and when to use it. Include keywords for discoverability.>
model: sonnet
skills:
  - <skill-name>
called-by:
  - <command-name> or "direct invocation"
---

# <Agent Name>

> **Layer 2 — Scale.** This is an agent. It wraps a Layer 1 skill with isolation, structured reporting, and parallel execution support. It does NOT contain business logic — that belongs in the skill. It does NOT discover work or fan out — that belongs to Layer 3 (commands). Its only job: receive a scoped task, invoke the skill, enforce the output contract, report results.

## Stack Position

| Layer | Component | Relationship |
|-------|-----------|-------------|
| L3 Command | `<command-name>` | spawns this agent via Task tool, parses the Report below |
| **L2 Agent** | **`<agent-name>` (this file)** | **wraps the skill, enforces output format** |
| L1 Skill | `<skill-name>` | provides the raw capability this agent invokes |

When creating this agent, remember:
- **You are thin.** Under 50 lines of meaningful config. If you're writing business logic, it belongs in the skill.
- **Your Report format is a contract.** The command (L3) parses it to aggregate results. The `STATUS:` line, the table structure, and the failure detail format must be stable.
- **You handle setup and teardown.** Create output directories, open sessions, close sessions. The skill shouldn't care about these concerns.
- **On failure, report — don't retry.** Capture diagnostics (console errors, stack traces), format the failure report, and return. The command decides what to do next.

## Purpose

You are a <role> agent. <One sentence describing the scoped task this agent performs using the named skill.>

## Variables

- **VAR_NAME:** `default-value` — description of what this controls
- **OUTPUT_DIR:** `./output/<agent-name>` — base directory for artifacts

## Workflow

1. **Parse** the incoming task into discrete work items
2. **Setup** — create output directories via `mkdir -p`, derive session identifiers
3. **Execute** — invoke the skill for each work item:
   a. Perform the action via `/<skill-name>`
   b. Capture artifacts (screenshots, files, findings)
   c. Evaluate result: PASS or FAIL
   d. On FAIL: capture diagnostic context, stop, mark remaining items SKIPPED
4. **Teardown** — close sessions, release resources
5. **Return** the structured report per the Report section below

## Report

> This is the contract between this agent (L2) and the command (L3) that spawns it. The command parses the STATUS line, the table rows, and the failure detail. Do not change this format without updating the corresponding command.

### On success

```
STATUS: SUCCESS

**Task:** <task description>
**Items:** N/N passed
**Artifacts:** <output directory path>

| # | Item | Status | Detail |
|---|------|--------|--------|
| 1 | Item description | PASS | relevant detail |
| 2 | Item description | PASS | relevant detail |
```

### On failure

```
STATUS: FAILURE

**Task:** <task description>
**Items:** X/N passed
**Failed at:** Item Y
**Artifacts:** <output directory path>

| # | Item | Status | Detail |
|---|------|--------|--------|
| 1 | Item description | PASS | relevant detail |
| 2 | Item description | FAIL | what went wrong |
| 3 | Item description | SKIPPED | — |

### Failure Detail
**Item Y:** description
**Expected:** what should have happened
**Actual:** what actually happened
**Diagnostic:** captured errors or context
```
