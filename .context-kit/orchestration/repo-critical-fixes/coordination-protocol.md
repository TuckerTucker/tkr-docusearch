# Coordination Protocol

This document defines how agents communicate, share status, and coordinate work during parallel execution.

## Communication Principles

1. **Asynchronous by Default:** Agents work independently, communicating through shared files
2. **Status Broadcasting:** All agents publish regular status updates
3. **Contract-Driven:** Communication through interfaces, not direct dependencies
4. **Explicit Handoffs:** Clear notifications when dependencies are ready
5. **Failure Transparency:** Problems are immediately visible to all agents

---

## Status Reporting

### Agent Status Files

Each agent maintains a JSON status file in `.context-kit/orchestration/repo-critical-fixes/status/{agent-name}.json`

**Status File Schema:**
```json
{
  "agent": "security-fixer-agent",
  "wave": 1,
  "status": "in_progress",
  "started_at": "2025-10-16T20:00:00Z",
  "last_updated": "2025-10-16T21:30:00Z",
  "completed_tasks": [
    {
      "task": "Fix CORS configuration",
      "files": ["src/api/server.py", "src/processing/worker_webhook.py"],
      "completed_at": "2025-10-16T20:45:00Z",
      "validation": "passed"
    },
    {
      "task": "Replace eval() with ast.literal_eval()",
      "files": ["src/storage/chroma_client.py"],
      "completed_at": "2025-10-16T21:15:00Z",
      "validation": "passed"
    }
  ],
  "in_progress_tasks": [
    {
      "task": "Add path validation to slide renderer",
      "files": ["docker/slide_renderer_api.py"],
      "started_at": "2025-10-16T21:20:00Z",
      "estimated_completion": "2025-10-16T22:30:00Z"
    }
  ],
  "remaining_tasks": [
    "Secure hardcoded password",
    "Fix bare except clause"
  ],
  "blockers": [],
  "validation_status": {
    "unit_tests_passing": true,
    "integration_tests_passing": true,
    "security_scan_clean": false,
    "contract_compliance": true
  },
  "metrics": {
    "tests_run": 45,
    "tests_passed": 45,
    "tests_failed": 0,
    "coverage_percentage": 62.3,
    "security_findings": 2
  },
  "next_steps": [
    "Complete path validation implementation",
    "Run full security scan",
    "Validate all contracts"
  ]
}
```

**Status Values:**
- `not_started` - Agent has not begun work
- `in_progress` - Agent is actively working
- `blocked` - Agent cannot proceed due to blocker
- `paused` - Agent work temporarily halted
- `completed` - Agent has finished all assigned tasks
- `failed` - Agent encountered unrecoverable error

---

### Status Update Frequency

**During Active Work:**
- Update status JSON after each task completion
- Update status JSON when encountering blocker
- Update status JSON at least every 2 hours

**During Idle Periods:**
- Update status JSON when starting/stopping work
- No updates required when not actively working

---

## Handoff Protocol

### Handoff File

All handoffs are documented in `.context-kit/orchestration/repo-critical-fixes/handoffs.md`

**Handoff Entry Format:**
```markdown
## Handoff #{number}: {provider-agent} → {consumer-agent}

**Date:** 2025-10-16T22:00:00Z
**Wave:** {wave-number}
**Status:** ✅ Complete | ⚠️ Partial | ❌ Blocked

### Deliverables
- {Deliverable 1}: {status and location}
- {Deliverable 2}: {status and location}
- {Deliverable 3}: {status and location}

### Integration Contract Validated
- ✅ Contract requirement 1: {validation result}
- ✅ Contract requirement 2: {validation result}
- ✅ Contract requirement 3: {validation result}

### Test Results
\`\`\`
pytest output showing validation
\`\`\`

### Known Issues
- {Issue 1}: {description and workaround}

### Next Agent Action
{Consumer agent} may proceed with {specific tasks}, using {specific interfaces}.

### Validation Commands
\`\`\`bash
# Commands the consumer agent should run to validate integration
pytest tests/integration/ -v
python scripts/validate_contract.py
\`\`\`
```

**Example Handoff:**
```markdown
## Handoff #1: test-infrastructure-agent → complexity-refactor-agent

**Date:** 2025-10-19T15:30:00Z
**Wave:** 1 → 2
**Status:** ✅ Complete

### Deliverables
- ✅ pytest.ini configured with pythonpath = src
- ✅ All 72 tests passing (0 failures, 0 errors)
- ✅ Test coverage baseline: 61.5% overall
- ✅ New test files: test_validate_search.py, test_markdown_utils.py

### Integration Contract Validated
- ✅ All tests discoverable: pytest --collect-only shows 72 tests
- ✅ No import errors: All modules load successfully
- ✅ Processing tests pass: 28/28 in tests/processing/
- ✅ Storage tests pass: 35/35 in tests/storage/

### Test Results
\`\`\`
========================= test session starts ==========================
platform darwin -- Python 3.13.0
collected 72 items

tests/processing/test_docling_parser.py ................ [100%]
tests/processing/test_processor.py ................ [100%]
tests/storage/test_chroma_client.py ................ [100%]

========================= 72 passed in 5.23s ===========================
\`\`\`

### Known Issues
None - all systems green

### Next Agent Action
complexity-refactor-agent may proceed with refactoring DoclingParser and DocumentProcessor. The full test suite is available for validation after each refactoring step.

### Validation Commands
\`\`\`bash
# Verify test infrastructure working
pytest --collect-only | grep "72 tests collected"
pytest tests/processing/ -v --tb=short
pytest tests/storage/ -v --tb=short
\`\`\`
```

---

## Daily Status Updates

### Daily Standup File

All agents post daily updates to `.context-kit/orchestration/repo-critical-fixes/daily-status.md`

**Daily Update Format:**
```markdown
## {Agent Name} - {Date}

### Yesterday
- {Task 1 completed}
- {Task 2 completed}
- {Blocker encountered and resolution}

### Today
- {Task 1 planned}
- {Task 2 planned}
- {Expected completion: X%}

### Blockers
- {Blocker 1}: {description and help needed}
- {Blocker 2}: {description and ETA for resolution}

### Dependencies Waiting On
- {Agent name}: {Specific deliverable needed}
- {Agent name}: {Specific deliverable needed}

### Help Needed
- {Specific question or resource needed}
```

**Example Daily Update:**
```markdown
## complexity-refactor-agent - 2025-10-20

### Yesterday
- Completed DoclingParser refactoring (CC: 57 → 8)
- Extracted 4 strategy pattern classes
- All 28 processing tests passing

### Today
- Begin DocumentProcessor._store_embeddings refactoring
- Extract embedding handler classes
- Add integration tests for new handlers
- Expected completion: 70%

### Blockers
None - on track

### Dependencies Waiting On
None - test infrastructure complete from Wave 1

### Help Needed
None - proceeding independently
```

---

## Blocker Management

### Blocker Escalation Process

When an agent encounters a blocker:

1. **Document in Status JSON:**
   ```json
   "blockers": [
     {
       "description": "Cannot run integration tests - ChromaDB unavailable",
       "severity": "high",
       "started_at": "2025-10-16T14:00:00Z",
       "dependencies": ["infrastructure"],
       "workaround": "Using mocks for now",
       "resolution_attempts": [
         "Tried starting docker-compose",
         "Checked port 8001 availability"
       ]
     }
   ]
   ```

2. **Post to Blockers File** (`.context-kit/orchestration/repo-critical-fixes/blockers.md`):
   ```markdown
   ## Blocker #{number}: {Agent} - {Title}

   **Agent:** {agent-name}
   **Severity:** Critical | High | Medium | Low
   **Started:** {timestamp}
   **Status:** Open | In Progress | Resolved

   ### Description
   {Detailed description of the blocker}

   ### Impact
   - Cannot complete: {specific tasks}
   - Blocks: {dependent agents}
   - Timeline impact: {estimated delay}

   ### Resolution Attempts
   1. {Attempt 1}: {result}
   2. {Attempt 2}: {result}

   ### Help Needed
   {Specific expertise or resources needed}

   ### Workaround
   {Temporary solution if available}
   ```

3. **Notify Dependent Agents** via daily status update

4. **Escalate to Orchestrator** if blocker not resolved within 4 hours

### Blocker Resolution

When a blocker is resolved:

1. Update status JSON: Remove from `blockers` array
2. Update blocker file: Set status to "Resolved"
3. Document resolution in handoffs.md
4. Resume normal work

---

## Wave Synchronization

### Wave Gate Process

At the end of each wave:

1. **All Agents Complete Tasks**
   - Update status JSON to "completed"
   - Run all validation tests
   - Document final status

2. **Orchestrator Validates Gate**
   - Check all agents show "completed" status
   - Run wave gate validation tests
   - Review all handoffs

3. **Gate Decision:**
   - ✅ **PASS:** All agents may proceed to next wave
   - ⚠️ **CONDITIONAL PASS:** Some issues, but can proceed with caution
   - ❌ **FAIL:** Must fix issues before next wave

4. **Gate Report Published**
   - Create `.context-kit/orchestration/repo-critical-fixes/gates/wave-{n}-gate-report.md`
   - Document pass/fail status
   - List remaining issues if any
   - Authorize next wave start

**Gate Report Format:**
```markdown
# Wave {N} Gate Report

**Date:** {timestamp}
**Status:** ✅ PASS | ⚠️ CONDITIONAL PASS | ❌ FAIL
**Orchestrator:** {name}

## Gate Validation Results

### Required Criteria
- ✅ Criterion 1: {validation result}
- ✅ Criterion 2: {validation result}
- ⚠️ Criterion 3: {validation result - minor issue}
- ✅ Criterion 4: {validation result}

### Agent Completion Status
- ✅ security-fixer-agent: All tasks complete
- ✅ test-infrastructure-agent: All tasks complete
- ✅ automation-agent: All tasks complete
- ✅ accessibility-agent: All tasks complete

### Test Results
\`\`\`
Overall test pass rate: 100% (72/72)
Coverage: 65.2% (+3.7% from baseline)
Security findings: 0 critical, 0 high
\`\`\`

### Known Issues
1. ⚠️ Minor: 3 tests skip due to optional dependencies (acceptable)
2. ✅ Resolved: Initial ChromaDB connection issue fixed

### Decision Rationale
All critical criteria met. Minor issues documented but do not block progress. Wave 2 may proceed.

### Next Wave Authorization
**Wave 2 START AUTHORIZED**
**Start Date:** 2025-10-20T09:00:00Z
**Agents:** complexity-refactor-agent, test-infrastructure-agent, automation-agent

### Action Items for Next Wave
1. Monitor test coverage improvements
2. Validate refactoring maintains test pass rate
3. Review complexity reduction metrics
```

---

## Cross-Agent Communication

### Direct Communication (When Needed)

For urgent issues requiring coordination:

1. **Post to Coordination File:**
   `.context-kit/orchestration/repo-critical-fixes/coordination.md`

2. **Tag Relevant Agents:**
   ```markdown
   ## @security-fixer-agent @automation-agent - Security Scan Configuration

   **From:** automation-agent
   **Date:** 2025-10-16

   Question: Should the security scan fail CI if medium-severity issues found?

   **Context:** Setting up pre-commit hooks and want to align with security standards.

   **Request:** Please advise on threshold settings.
   ```

3. **Respond in Same File:**
   ```markdown
   ### Response from security-fixer-agent

   Recommend: Fail on high/critical only. Medium should warn but not block.

   Rationale: Medium findings often require context-specific analysis.
   ```

---

## Progress Tracking

### Overall Progress Dashboard

Orchestrator maintains `.context-kit/orchestration/repo-critical-fixes/progress.json`:

```json
{
  "orchestration_start": "2025-10-16T20:00:00Z",
  "last_updated": "2025-10-20T15:00:00Z",
  "current_wave": 2,
  "total_waves": 4,
  "overall_progress_percentage": 45,
  "waves": [
    {
      "wave": 1,
      "status": "completed",
      "started": "2025-10-16T20:00:00Z",
      "completed": "2025-10-19T15:00:00Z",
      "duration_hours": 67,
      "agents_completed": 4,
      "agents_total": 4,
      "tasks_completed": 15,
      "tasks_total": 15,
      "gate_status": "passed"
    },
    {
      "wave": 2,
      "status": "in_progress",
      "started": "2025-10-20T09:00:00Z",
      "estimated_completion": "2025-10-24T17:00:00Z",
      "agents_completed": 1,
      "agents_total": 3,
      "tasks_completed": 3,
      "tasks_total": 8,
      "progress_percentage": 38
    }
  ],
  "agents": [
    {
      "name": "security-fixer-agent",
      "status": "completed",
      "tasks_completed": 5,
      "tasks_total": 5
    },
    {
      "name": "complexity-refactor-agent",
      "status": "in_progress",
      "tasks_completed": 1,
      "tasks_total": 2
    }
  ],
  "metrics": {
    "repository_health_score": 82,
    "test_coverage_percentage": 65.2,
    "security_findings": 0,
    "performance_vs_baseline": "+5%"
  }
}
```

### Visualization Commands

```bash
# View overall progress
cat .context-kit/orchestration/repo-critical-fixes/progress.json | jq '.overall_progress_percentage'

# View current wave status
cat .context-kit/orchestration/repo-critical-fixes/progress.json | jq '.waves[] | select(.status == "in_progress")'

# List agent statuses
ls .context-kit/orchestration/repo-critical-fixes/status/*.json | xargs -I {} jq -r '"\(.agent): \(.status)"' {}

# Check for blockers
find .context-kit/orchestration/repo-critical-fixes/status/ -name "*.json" -exec jq -r 'select(.blockers | length > 0) | .agent' {} \;
```

---

## File Structure

```
.context-kit/orchestration/repo-critical-fixes/
├── orchestration-plan.md           # Main execution plan
├── agent-assignments.md            # Territorial ownership
├── validation-strategy.md          # Testing approach
├── coordination-protocol.md        # This file
├── integration-contracts/          # Contract specifications
│   ├── README.md
│   ├── security-api-contract.md
│   ├── test-infrastructure-contract.md
│   ├── docling-parser-refactor-contract.md
│   └── ...
├── status/                         # Agent status files
│   ├── security-fixer-agent.json
│   ├── test-infrastructure-agent.json
│   ├── automation-agent.json
│   └── ...
├── gates/                          # Wave gate reports
│   ├── wave-1-gate-report.md
│   ├── wave-2-gate-report.md
│   └── ...
├── handoffs.md                     # Integration handoffs
├── daily-status.md                 # Daily standup updates
├── blockers.md                     # Active blockers
├── coordination.md                 # Cross-agent communication
└── progress.json                   # Overall progress tracking
```

---

## Best Practices

### DO:
- ✅ Update status JSON after each task
- ✅ Document handoffs explicitly
- ✅ Post daily status updates
- ✅ Escalate blockers quickly
- ✅ Validate contracts before declaring complete
- ✅ Run all validation tests before handoff

### DON'T:
- ❌ Assume other agents know your status
- ❌ Skip handoff documentation
- ❌ Leave blockers undocumented
- ❌ Proceed without validating dependencies
- ❌ Modify files outside your territory without coordination
- ❌ Declare completion without running tests

---

This coordination protocol ensures smooth parallel execution with clear communication channels and minimal coordination overhead.
