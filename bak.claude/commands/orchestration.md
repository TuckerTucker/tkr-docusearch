---
name: orchestration
description: Plan and execute parallel agent workflows for complex feature implementations using wave-based coordination
allowed-tools: [Read, Write, Glob, Grep, Bash, Task, SendMessage]
source: tkr-kit
version: 2.0.0
---

# /orchestration Command

Plan and execute coordinated multi-agent workflows for complex implementations. Decomposes work into agent territories, organizes execution into dependency-ordered waves, and coordinates parallel agent execution with validation gates. All orchestration data is stored in Koji and surfaced via REST API + dashboard.

## Hierarchy

```
Product (high-level initiative)
  └── Capability (13-section spec)
       └── Orchestration Plan (wave-based execution) <-- YOU ARE HERE
            ├── Wave 1: Foundation (parallel agents)
            ├── Wave 2: Implementation (parallel agents)
            ├── Wave 3: Integration (parallel agents)
            └── Wave N: Wiring (auto-generated, parallel agents)
```

## When to Orchestrate vs. Implement Directly

**Use orchestration when:**
- Feature spans 5+ files across multiple subsystems
- Capability from product hierarchy needs implementation
- Clear parallelization opportunities exist (3+ independent workstreams)
- Complex dependencies require sequenced waves

**Implement directly when:**
- Simple, linear tasks (single file edits)
- Tightly coupled changes where parallelization adds overhead
- Exploratory work where requirements are unclear
- Bug fixes or small enhancements

**Rule of thumb:** If work requires < 3 independent steps, implement directly. If work requires 3+ parallel workstreams across waves, orchestrate.

## Usage

```
/orchestration [action] [args]
```

## Actions

### /orchestration plan [source]

Analyze requirements and create a wave-based execution plan with agent territories, contracts, and validation gates.

**Arguments:**
- `source` - One of:
  - `capability:<id>` or shorthand capability ID (e.g., `cap_abc123`) - Plan from 13-section capability spec (preferred)
  - `feature:<id>` - Plan from feature's slices in the planning database
  - `"<goal description>" [agent_count]` - Plan from a feature goal description with optional agent count

**Examples:**
```
/orchestration plan capability:cap_abc123
/orchestration plan cap_abc123
/orchestration plan feature:feat_def456
/orchestration plan "user authentication with OAuth" 4
```

### /orchestration execute <run-id> [wave|all]

Execute an orchestration plan by launching agents wave-by-wave.

**Arguments:**
- `run-id` - ID of the orchestration run (returned from plan creation)
- `wave` (optional) - Specific wave number to execute, or `all` to run all waves sequentially (default: next incomplete wave)

**Examples:**
```
/orchestration execute run_abc123 1
/orchestration execute run_abc123 all
/orchestration execute run_abc123
```

### /orchestration complete <run-id> [wave]

Validate wave or plan completion by verifying contracts and gate definitions.

**Arguments:**
- `run-id` - ID of the orchestration run
- `wave` (optional) - Specific wave to validate, or omit for full run validation

**Examples:**
```
/orchestration complete run_abc123 1
/orchestration complete run_abc123
```

### /orchestration debug <run-id> [wave]

Debug verification failures in a wave or plan.

**Arguments:**
- `run-id` - ID of the orchestration run
- `wave` (optional) - Specific wave to debug

**Examples:**
```
/orchestration debug run_abc123 2
/orchestration debug run_abc123
```

## Quick Reference

| Command | Purpose |
|---------|---------|
| `/orchestration plan <source>` | Create wave-based execution plan |
| `/orchestration execute <run-id> [wave]` | Launch agents for wave(s) |
| `/orchestration complete <run-id> [wave]` | Validate wave/plan completion |
| `/orchestration debug <run-id> [wave]` | Debug verification failures |

## API Reference

```bash
API="http://127.0.0.1:${TKR_OBS_PORT:-42005}/api"
```

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/orchestration/runs` | Create run from feature |
| POST | `/api/orchestration/runs/tasks` | Create run from task IDs |
| GET | `/api/orchestration/runs` | List all runs |
| GET | `/api/orchestration/runs/{id}/status` | Full status + waves + agents |
| PATCH | `/api/orchestration/runs/{id}` | Update run |
| POST | `/api/orchestration/runs/{id}/waves/{n}/start` | Start wave |
| POST | `/api/orchestration/runs/{id}/waves/{n}/complete` | Complete wave (verifies contracts) |
| POST | `/api/orchestration/agents/{id}/complete` | Mark agent done |
| GET | `/api/orchestration/runs/{id}/contracts` | List contracts |
| PATCH | `/api/orchestration/contracts/{id}` | Update contract status |
| GET | `/api/orchestration/runs/{id}/gate-definitions` | List gate definitions |
| GET | `/api/orchestration/runs/{id}/timeline` | Timeline view |
| POST | `/api/orchestration/runs/{id}/pause` | Pause run |
| POST | `/api/orchestration/runs/{id}/resume` | Resume run |
| POST | `/api/orchestration/runs/{id}/cancel` | Cancel run |
| GET | `/api/orchestration/briefings/{sessionId}` | Agent briefing context |

## Implementation

When this command is invoked, parse `$ARGUMENTS` to determine the action (first word) and remaining arguments.

---

### For `/orchestration plan`

#### Step 1: Resolve Input Source

Determine the source of requirements based on the argument format:

**From Capability (preferred):**
```bash
curl -s "$API/planning/capabilities/{id}"
```
Extract the 13-section spec from `spec_content`. If the capability has no spec, advise the user to run `/capability generate-spec <id>` first.

Check prerequisites:
```bash
curl -s "$API/planning/capabilities/{id}/dependencies"
```
Verify all dependencies have `status: implemented`. If not, report which dependencies are blocking.

**From Feature:**
```bash
curl -s "$API/planning/features/{id}"
curl -s "$API/planning/slices?feature_id={id}"
```

**From Goal Description:**
Parse the quoted description and optional agent count from the arguments. Use the description to analyze requirements directly.

#### Step 2: Analyze and Decompose

Read the supporting documentation to inform wave design:
- `.claude/skills/orchestrate/wave-planning.md` - Wave structure patterns
- `.claude/skills/orchestrate/coordination.md` - Agent coordination patterns

Analyze the requirements to identify:
1. **Agent territories** - Independent domains of work (backend, frontend, data, tests, etc.)
2. **Dependency layers** - Which work must complete before other work can begin
3. **Contracts** - Shared interfaces, schemas, API specs, file locations between agents
4. **Gates** - Automated, verifiable success criteria for each wave

#### Step 3: Create Orchestration Run

Create the run via API. The planner automatically generates:
- Wave groupings from topological sort of slice dependencies
- `file_location` contracts from slice `delivers` arrays
- L1-L5 gate definitions based on slice layers
- Agent constraints (path_constraints, pattern_requirements, completion_checklist) per layer
- Wiring wave for orphan detection, route coverage, barrel exports

```bash
curl -s -X POST "$API/orchestration/runs" \
  -H 'Content-Type: application/json' \
  -d '{
    "feature_id": "<feature-id>",
    "feature_name": "User Authentication",
    "capability_id": "<optional-capability-id>",
    "agents_per_wave": 3,
    "agent_prefix": "auth",
    "run_pre_build_gates": true
  }'
```

Returns:
```json
{
  "success": true,
  "data": {
    "run": { "id": "run_...", "status": "pending", ... },
    "plan": { "feature": "...", "waves": [...] },
    "gateResult": { "passed": true },
    "sliceCount": 8,
    "waveCount": 4,
    "agentCount": 10
  }
}
```

For task-based orchestration (ad-hoc task IDs instead of feature slices):
```bash
curl -s -X POST "$API/orchestration/runs/tasks" \
  -H 'Content-Type: application/json' \
  -d '{
    "task_ids": ["task_1", "task_2", "task_3"],
    "max_parallel": 3,
    "agent_prefix": "fix"
  }'
```

#### Step 4: Present Plan for Review

Fetch the created run's status and display:

```bash
curl -s "$API/orchestration/runs/{id}/status"
curl -s "$API/orchestration/runs/{id}/contracts"
curl -s "$API/orchestration/runs/{id}/gate-definitions"
```

Display the generated plan to the user with:
- Wave overview (wave number, name, agents, gate summary)
- Agent territory map (which agent owns which files)
- Contract summary (auto-generated from slice delivers)
- Gate definitions (auto-generated per layer)
- Wiring wave details (auto-appended)
- Ask user to confirm before proceeding to execution

The plan is also viewable in the dashboard at `/orchestration`.

---

### For `/orchestration execute`

#### Step 1: Load Run

Fetch the orchestration run status:
```bash
curl -s "$API/orchestration/runs/{id}/status"
```

Determine which wave to execute:
- If a specific wave number is provided, execute that wave
- If `all` is provided, execute all waves sequentially
- If no argument, find the next incomplete wave from the status response

#### Step 2: Validate Pre-Conditions

Before starting a wave, verify:
1. All prior waves are completed (check wave status in run status response)
2. No broken contracts from prior waves (check contracts endpoint)
3. If pre-conditions fail, report what is missing and do not proceed

#### Step 3: Start Wave

```bash
curl -s -X POST "$API/orchestration/runs/{id}/waves/{n}/start"
```

This creates agent execution records. Each agent automatically receives:
- **Territory** — file paths they own
- **Contracts** — what to produce (stored in `orchestration_contracts`)
- **Constraints** — path_constraints, pattern_requirements, completion_checklist (stored on `agent_executions`)
- **Briefing context** — auto-assembled by `assembleBriefing()` including slice details, prior wave outputs, handoffs, and prior insights

For each agent in the wave, use the **Agent** tool to spawn a sub-agent. The task prompt for each agent MUST include:
1. **Territory** - Exact file paths the agent owns
2. **Contracts consumed** - What to import/use from prior waves (fetch from contracts endpoint)
3. **Contracts produced** - What this agent must create (from contracts endpoint, filtered by agent)
4. **Constraints** - From agent execution record (path, patterns, checklist)
5. **Completion verification** - Diagnostics, browser checks if applicable

Launch agents in batches of 2-3 (max 4 concurrent).

#### Step 4: Monitor and Track

As agents complete, mark them done via API:
```bash
curl -s -X POST "$API/orchestration/agents/{id}/complete" \
  -H 'Content-Type: application/json' \
  -d '{ "success": true, "report": "..." }'
```

The dashboard auto-polls running/paused runs with a 3-second interval, showing real-time progress.

#### Step 5: Complete Wave

After all agents in a wave finish:
```bash
curl -s -X POST "$API/orchestration/runs/{id}/waves/{n}/complete"
```

The executor's `completeWave` automatically:
1. Verifies all contracts for the wave (blocks advancement if any are broken)
2. Evaluates gate definitions (runs commands, checks expected output)
3. Records gate evaluation results
4. Returns completion status with contract verification results

If the wave passes, proceed to the next wave (or report run completion).
If the wave fails, report failures and stop execution.

#### Step 6: Wave Progression

If executing `all` waves:
- After wave N completes successfully, automatically start wave N+1
- If any wave fails (broken contracts or failed gates), stop and report
- After final wave (wiring wave) completes, the run is done

---

### For `/orchestration complete`

#### Step 1: Load State

```bash
curl -s "$API/orchestration/runs/{id}/status"
curl -s "$API/orchestration/runs/{id}/contracts"
curl -s "$API/orchestration/runs/{id}/gate-definitions"
```

#### Step 2: Validate

**If a specific wave is provided:**
1. Verify all agents in the wave reported `status: completed`
2. Verify all contracts for the wave are `fulfilled`
3. Check gate evaluation results
4. Run additional verification:
   - `bun run typecheck` — no type errors
   - `bun test` — tests pass
   - For UI waves: browser error check
   - For API waves: network request check

**If no wave is provided (full run validation):**
1. Verify ALL waves completed
2. Verify ALL contracts fulfilled (none broken or pending)
3. Run final acceptance criteria:
   - All success criteria from the plan met
   - Integration tests pass
   - No blocking technical debt
4. Spec conformance check:
   - All spec deliverables have corresponding code
   - All spec edge cases have test coverage

#### Step 3: Update Source Status

**If source was a capability:**
```bash
curl -s -X PATCH "$API/planning/capabilities/{id}" \
  -H 'Content-Type: application/json' \
  -d '{ "status": "implemented" }'
```

**If source was a feature/slice:**
```bash
curl -s -X PATCH "$API/planning/specs/{id}" \
  -H 'Content-Type: application/json' \
  -d '{ "status": "x" }'
```

#### Step 4: Report

Generate a completion summary with:
- Overall status (passed/failed)
- Waves completed and their gate results
- Contract fulfillment summary
- Agents deployed and their outcomes
- Test metrics
- Files created/modified

---

### For `/orchestration debug`

#### Step 1: Identify Failure Context

```bash
curl -s "$API/orchestration/runs/{id}/status"
curl -s "$API/orchestration/runs/{id}/contracts"
curl -s "$API/orchestration/runs/{id}/gate-definitions"
```

If a specific wave is provided, focus on that wave's agents and gates. Otherwise, scan all waves for failures.

Use the dashboard's **Contracts** and **Gates** tabs for visual debugging.

#### Step 2: Diagnose Failures

For each failed gate or agent:

1. **Contract failures** — Check which contracts are `broken` or still `pending`:
   - Missing files → `file_location` contract not fulfilled
   - Wrong exports → `type` contract not met

2. **Gate failures** — Check which gate definitions failed:
   - L1 (existence): files missing
   - L3 (validation): typecheck or lint errors
   - L4 (integration): browser/network errors
   - L5 (e2e): integration tests failing

3. **Agent failures** — Check agent status and reports:
   - Did the agent report errors?
   - Path constraint violations (files in wrong locations)?
   - Missing pattern requirements?

#### Step 3: Run Diagnostic Checks

```bash
# Type checking
bun run typecheck 2>&1 | head -50

# Tests
bun test 2>&1 | tail -30

# Check contract fulfillment
curl -s "$API/orchestration/runs/{id}/contracts?wave_number={n}" | jq '.data[] | select(.status != "fulfilled")'
```

#### Step 4: Recommend Resolution

Based on diagnosis, recommend one of:
1. **Fix and re-complete** — Minor issue; fix, then re-run wave completion
2. **Re-run agent** — Agent produced incorrect output; re-run with corrected instructions
3. **Re-run wave** — Multiple agents failed; re-run the entire wave
4. **Replan** — Fundamental issue; adjust wave boundaries or contracts
5. **Update contract** — Mark contract as fulfilled/broken manually:
   ```bash
   curl -s -X PATCH "$API/orchestration/contracts/{id}" \
     -H 'Content-Type: application/json' \
     -d '{ "status": "fulfilled" }'
   ```

---

## Supporting Documentation

| Document | Location | Purpose |
|----------|----------|---------|
| Wave Planning Guide | `.claude/skills/orchestrate/wave-planning.md` | Wave structure patterns, sizing, dependency management |
| Coordination Guide | `.claude/skills/orchestrate/coordination.md` | Contract types, handoff patterns, anti-patterns |

## Execution Constraints

Based on production experience. Enforced via `PlanOptions.agentsPerWave` and executor batch control:

| Setting | Value | Rationale |
|---------|-------|-----------|
| `max_concurrent_agents` | 4 | >4 causes context fragmentation |
| `agent_batch_size` | 2-3 | Within a wave, launch in batches |
| `wave_strategy` | sequential | Complete Wave N before Wave N+1 |
| `max_waves` | 6 | Beyond 6, break into multiple orchestrations |
| `max_agents_per_wave` | 4 | Beyond 4, combine related work |

## Auto-Generated Artifacts

The planner automatically generates these from slice data — no manual creation needed:

| Artifact | Source | Storage |
|----------|--------|---------|
| Contracts | Slice `delivers` arrays | `orchestration_contracts` table |
| Gate definitions | Slice layers → L1-L5 rules | `wave_gate_definitions` table |
| Agent constraints | Territory + layer conventions | `agent_executions` columns |
| Wiring wave | Detected layers → wiring agents | Appended to plan waves |
| Briefing context | Slices, territory, prior waves, insights | Assembled at runtime |

## Wave Gate Standards

Gates are auto-generated by `generateGateDefinitions()` based on slice layers:

| Layer | Generated Gates |
|-------|----------------|
| All | L1 file existence, L3 typecheck + lint |
| UI | L4 browser error check |
| API | L4 network request check |
| Final wave | L5 integration tests |

The final wave (Wiring) always includes L5 gates for orphan detection, route coverage, and barrel exports.

## Output Formats

### Plan Output (from API)

```
Orchestration Plan: auth-system (run_abc123)
==============================================

Source: cap_abc123 (User Authentication)
Waves: 4 (3 + wiring)
Total Agents: 10
Contracts: 15

Wave 1: Foundation (2 agents)
  Agent: auth-w0-0  | territory: src/types/auth.ts, src/schemas/
  Agent: auth-w0-1  | territory: src/contracts/
  Contracts: 5 (file_location)
  Gates: L1 existence, L3 typecheck

Wave 2: Implementation (3 agents)
  Agent: auth-w1-0  | territory: src/services/
  Agent: auth-w1-1  | territory: src/components/
  Agent: auth-w1-2  | territory: src/middleware/
  Contracts: 6 (file_location, type)
  Gates: L1 existence, L3 typecheck+lint, L4 browser errors

Wave 3: Integration (2 agents)
  Agent: auth-w2-0  | territory: tests/e2e/
  Agent: auth-w2-1  | territory: docs/
  Contracts: 2 (behavior)
  Gates: L1, L3, L5 integration tests

Wave 4: Wiring [WIRING] (3 agents)
  Agent: wiring-ui    | routes, navigation, parent imports
  Agent: wiring-api   | server mounts, barrel exports
  Agent: wiring-core  | index.ts barrels, module re-exports
  Gates: L5 orphan detection, route coverage, barrel check

Dashboard: http://localhost:42001/orchestration

Confirm plan to proceed? [describe any adjustments needed]
```

### Execution Progress (from API)

```
Orchestration: auth-system (run_abc123)
========================================

Wave 1: Foundation [PASSED]
  auth-w0-0:  completed (3 files, contracts: 3/3 fulfilled)
  auth-w0-1:  completed (1 file, contracts: 2/2 fulfilled)
  Gates: PASSED (L1 ok, L3 ok)

Wave 2: Implementation [IN PROGRESS]
  auth-w1-0:  completed (4 files, 28 tests passed)
  auth-w1-1:  in_progress...
  auth-w1-2:  completed (2 files, 8 tests passed)
  Contracts: 4/6 fulfilled, 2 pending

Wave 3: Integration [PENDING]
Wave 4: Wiring [PENDING]
```

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| "Capability not found" | Invalid capability ID | Check with `GET $API/planning/capabilities` |
| "Capability has no spec" | Spec not generated | Run `/capability generate-spec <id>` first |
| "Dependencies not met" | Dependent capabilities not implemented | Implement dependencies first |
| "Run not found" | Invalid run ID | Check with `GET $API/orchestration/runs` |
| "Contracts broken" | Wave has broken contracts | Fix issues, update contracts via PATCH, re-complete wave |
| "Gate failed" | Blocker gate definition not met | Run `/orchestration debug` to diagnose |
| "Agent failed" | Agent task errored | Check agent report, re-run agent if needed |
| "Task not found" | Invalid task ID in task-based run | Verify task IDs exist |

## Related Commands

- `/planning` - Manage planning hierarchy (products, capabilities, features, slices, specs)

---

**Command Version:** 2.0.0
