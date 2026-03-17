---
name: <skill-name>
description: <One-line description. Include when-to-use triggers and keywords for discoverability.>
allowed-tools: [Read, Glob, Grep, Bash]
source: tkr-kit
version: 1.0.0
---

# <Skill Name>

> **Layer 1 — Capability.** This is a skill. It encapsulates domain logic and tool invocation for a single concern. It does NOT orchestrate agents or fan out work — that belongs to Layer 3 (commands). It produces structured output that Layer 2 (agents) can parse and enforce.

## Composition

How this skill fits into the three-layer stack:

| Layer | Component | Status |
|-------|-----------|--------|
| L3 Command | `<command-name>` or _none yet_ | orchestrates multiple agents running this skill |
| L2 Agent | `<agent-name>` or _none yet_ | wraps this skill with isolation + structured reporting |
| **L1 Skill** | **`<skill-name>` (this file)** | **provides the raw capability** |

When creating this skill, consider:
- **Will this be called by an agent?** If so, the Output Contract must be machine-parseable — agents extract status, metrics, and findings from it
- **Will multiple instances run in parallel?** If so, ensure the skill is stateless or uses scoped identifiers (session names, output subdirectories) to avoid conflicts
- **Is the output contract stable?** Agents and commands depend on it. Changing the format requires updating the agent's Report parser

## Purpose

<One paragraph describing what this skill does and why it exists.>

## When to Use

- User asks for <trigger phrase>
- User mentions <keyword>
- Agent invokes this skill as part of a scoped task

## Data Access

<How this skill reads and writes data. Reference the appropriate layer:>

### REST API (preferred for CRUD)
```bash
API="http://127.0.0.1:${TKR_OBS_PORT:-42005}/api/<domain>"
# List relevant endpoints
```

### Direct imports (for scripts)
```typescript
import { ... } from "core/<domain>/<module>.js";
```

## Instructions

<Numbered steps for executing this skill. Be precise and imperative.>

1. **Validate inputs** — confirm required parameters are present
2. **Read context** — gather the necessary files or data
3. **Execute** — perform the core analysis/action
4. **Format output** — structure results per the Output Contract below

## Output Contract

> This contract is the interface between layers. Agents (L2) parse this output to build their reports. Commands (L3) aggregate agent reports built from this format. Do not change this format without updating the corresponding agent.

### Success
```
STATUS: SUCCESS

**<Primary Label>:** <value>
**<Metric>:** <value>

| # | <Column> | <Column> | <Column> |
|---|----------|----------|----------|
| 1 | data     | data     | data     |
```

### Failure
```
STATUS: FAILURE

**Error:** <what went wrong>
**Context:** <diagnostic information>
```

## Examples

### Example 1: <scenario>
```
/<skill-name> <arguments>
```
Expected: <what the skill produces>

### Example 2: <scenario>
```
/<skill-name> <arguments>
```
Expected: <what the skill produces>
