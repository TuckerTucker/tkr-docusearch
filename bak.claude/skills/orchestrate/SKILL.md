---
name: orchestrate
description: Skill for planning and executing parallel agent workflows for complex feature implementations. Use when user needs to coordinate multiple agents, implement large features, or run parallel workstreams.
source: tkr-kit
version: 2.0.0
---

# Orchestration

Plan and execute coordinated multi-agent workflows for complex implementations. All orchestration data is stored in the Koji database and surfaced via REST API + dashboard.

## When to Use

Use orchestration when:
- **Large feature spans 5+ files** - Feature touches multiple subsystems or domains
- **Capability implementation** - A capability from the product-capability hierarchy needs implementation
- **Clear parallelization opportunities** - Independent workstreams that can run concurrently
- **Complex dependencies** - Work must be sequenced in waves (foundation → implementation → integration)
- **User explicitly requests** - User mentions "orchestration", "parallel agents", or "coordinate multiple tasks"

**Don't use orchestration when:**
- **Simple, linear tasks** - Single file edits or straightforward implementations
- **Tight coupling** - Changes are so interdependent that parallelization adds overhead
- **Exploratory work** - Requirements are unclear and need discovery first
- **Quick fixes** - Bug fixes or small enhancements better done directly

**Rule of thumb:** If you can complete the work in < 3 independent steps, implement directly. If you need ≥ 3 parallel workstreams across waves, orchestrate. For capability implementations, orchestration helps maintain the rich context from the 13-section spec.

## Relationship to Planning

Orchestration works downstream of the planning skill and product-capability workflows:

```
Product                         Capability                    Orchestration
   |                               |                               |
   v                               v                               v
High-level initiative     13-section AI spec          WHO builds in parallel
                          (detailed context)           (agents, waves, gates)

planning skill                  orchestration skill
     |                               |
     v                               v
  WHAT to build               WHO builds in parallel
  (specs, contracts)          (agents, waves, gates, contracts)
```

### Workflow Integration

**Product-Capability Path (large initiatives):**
1. **Product defines initiative** - Problem statement, success criteria
2. **Capability specifies context** - 13-section spec with all detail for AI agents
3. **Slices suggested from capability** - /capability suggest-slices generates slice boundaries
4. **Orchestration executes slices** - Slice spec → agent territories → waves

**Feature Path (standalone features):**
1. **Planning skill generates specs** - Feature inventory → slices → slice specs
2. **Orchestration consumes specs** - Slice spec → agent territories → waves
3. **Status flows back** - Orchestration completion → spec status update

### Data Access

All orchestration data is accessed via the observability REST API:

```bash
API="http://127.0.0.1:${TKR_OBS_PORT:-42005}/api"

# Runs
POST   $API/orchestration/runs                              # Create run from feature
POST   $API/orchestration/runs/tasks                        # Create run from task IDs
GET    $API/orchestration/runs                              # List runs
GET    $API/orchestration/runs/{id}/status                  # Full status + waves + agents

# Wave control
POST   $API/orchestration/runs/{id}/waves/{n}/start         # Start wave
POST   $API/orchestration/runs/{id}/waves/{n}/complete       # Complete wave (verifies contracts)

# Agent lifecycle
POST   $API/orchestration/agents/{id}/complete              # Mark agent done

# Contracts & gates
GET    $API/orchestration/runs/{id}/contracts                # List contracts
PATCH  $API/orchestration/contracts/{id}                     # Update contract status
GET    $API/orchestration/runs/{id}/gate-definitions         # List gate definitions

# Run control
POST   $API/orchestration/runs/{id}/pause
POST   $API/orchestration/runs/{id}/resume
POST   $API/orchestration/runs/{id}/cancel

# Context
GET    $API/orchestration/briefings/{sessionId}              # Agent briefing context
GET    $API/orchestration/runs/{id}/timeline                 # Timeline view
```

### Input Sources

When creating an orchestration run, read source data via REST API:

- **From Capability (preferred):** `GET $API/planning/capabilities/{id}` — Full 13-section spec
- **From Feature:** `GET $API/planning/features/{id}` then `GET $API/planning/slices?feature_id={id}` — Feature slices from Koji

### Prerequisites

Before orchestrating a capability:
1. Capability exists with `status: in_progress` or `implemented`
2. Capability spec_content contains valid 13-section spec
3. All dependent capabilities are implemented (check via `GET $API/planning/capabilities/{id}/dependencies`)

Before orchestrating slices:
1. Slice specs exist with `status: approved`
2. All dependent slices are implemented (`x` status)
3. Cross-cutting patterns referenced in spec exist

## Instructions

When orchestrating work:

### For Planning

1. Use **/orchestration plan** command to create a run:

   ```bash
   POST /api/orchestration/runs
   {
     "feature_id": "...",
     "feature_name": "...",
     "agents_per_wave": 3,
     "agent_prefix": "auth",
     "run_pre_build_gates": true
   }
   ```

   The planner (`core/planning/orchestration/planner.ts`) automatically:
   - Groups slices into waves via topological sort of dependency graph
   - Extracts `file_location` contracts from slice `delivers` arrays
   - Generates L1-L5 gate definitions based on slice layers
   - Derives agent constraints (path, patterns, checklist) per layer
   - Appends a wiring wave for orphan detection and route coverage

   **Wave Structure (auto-generated):**
   - Wave 1+: Topological layers from slice dependencies
   - Final Wave: Wiring (route coverage, barrel exports, orphan detection)

   See `wave-planning.md` for manual wave design patterns.

### For Execution

2. Use **/orchestration execute** command:

   ```bash
   # Start a wave
   POST /api/orchestration/runs/{id}/waves/{n}/start

   # Mark agent complete
   POST /api/orchestration/agents/{id}/complete
   { "success": true, "report": "..." }

   # Complete wave (auto-verifies contracts, evaluates gates)
   POST /api/orchestration/runs/{id}/waves/{n}/complete
   ```

   **Execution Flow:**
   - `startWave` creates agent execution records with briefing context
   - `assembleBriefing()` auto-gathers: slice details, territory, prior wave outputs, handoffs, constraints, and prior insights
   - Agents receive briefing via `formatBriefingForAgent()` as system-reminder XML
   - `completeWave` verifies contracts (blocks on broken), evaluates gate definitions
   - Dashboard auto-polls running/paused runs with 3s interval

### For Completion

3. Use **/orchestration complete** command:

   ```bash
   GET /api/orchestration/runs/{id}/status
   ```

   **Completion Checklist:**
   - All wave gates passed (check Gates tab in dashboard)
   - All contracts fulfilled (check Contracts tab in dashboard)
   - Integration tests pass
   - **Spec conformance verified**
   - No blocking technical debt
   - Code review ready

   **Spec Conformance Gate:**
   Before marking a slice `x` (implemented), verify:
   - All spec deliverables have corresponding code
   - All spec edge cases have test coverage
   - No undocumented code paths (or intentionally defer them)

   **Update source status:**
   ```bash
   PATCH $API/planning/capabilities/{id}  -d '{ "status": "implemented" }'
   PATCH $API/planning/specs/{id}         -d '{ "status": "x" }'
   ```

## Command Referenced

Use the unified `/orchestration` command:

```bash
# From capability (creates run + plan in DB)
/orchestration plan capability:<capability-id>
/orchestration plan cap_abc123

# From feature in Koji
/orchestration plan feature:<feature-id>

# From feature goal
/orchestration plan "user authentication with OAuth" 4

# Execute (API-backed, uses run ID)
/orchestration execute <run-id> [wave|all]

# Complete (API-backed)
/orchestration complete <run-id> [wave]

# Debug
/orchestration debug <run-id> [wave]
```

### Capability-Based Orchestration

When orchestrating from a capability:

1. **Read capability** - Get 13-section spec with full context
2. **Extract implementation steps** - Section 7 provides ordered steps
3. **Generate wave plan** - Map steps to waves by layer (data → domain → api → ui)
4. **Create agent territories** - Each deliverable becomes a task
5. **Track via capability status** - Update capability status as waves complete

## Supporting Documentation

- `wave-planning.md` - Wave structure patterns and dependency management
- `coordination.md` - Agent contracts, communication patterns, and coordination strategies

## Dashboard

The orchestration dashboard (`/orchestration` route) provides real-time visibility:

- **Run selector** — pick any run, auto-detects active runs
- **Wave timeline** — progress bars, agent cards, gate indicators, wiring badge
- **Contracts tab** — table grouped by wave with status badges (pending/fulfilled/broken)
- **Gates tab** — L1-L5 definitions with level indicators, commands, blocker flags
- **Agent detail** — territory, slices, report, duration, constraints panel
- **Run controls** — pause, resume, cancel

## Output

Guide user through orchestration:
- **When to use orchestration vs. direct implementation** - Apply decision criteria above
- **How to structure the plan** - Wave decomposition, agent territories, contracts
- **Monitoring execution progress** - Dashboard + API for wave/agent/contract/gate status
- **Handling failures and retries** - Debug via dashboard Gates/Contracts tabs, API endpoints
