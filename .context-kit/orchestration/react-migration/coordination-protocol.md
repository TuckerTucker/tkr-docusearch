# Coordination Protocol

**Purpose:** Define how agents communicate, synchronize, and resolve conflicts during parallel execution

---

## Communication Channels

### 1. Status Broadcasting (Automated)

Each agent publishes status to `.context-kit/orchestration/react-migration/status/{agent-name}.json` every **15 minutes** or on significant state changes.

**Status Schema:**

```json
{
  "agent": "library-agent",
  "wave": 2,
  "status": "in_progress" | "completed" | "blocked" | "error",
  "started_at": "2025-10-18T10:00:00Z",
  "updated_at": "2025-10-18T10:30:00Z",
  "completed_tasks": 7,
  "total_tasks": 9,
  "current_task": "Integrating WebSocket real-time updates",
  "deliverables": [
    {
      "file": "components/document/DocumentCard.jsx",
      "status": "complete",
      "tests_passing": true,
      "contract_validated": true
    },
    {
      "file": "features/library/FilterBar.jsx",
      "status": "in_progress",
      "progress": 75
    }
  ],
  "blockers": [],
  "dependencies_met": true,
  "next_steps": [
    "Add upload functionality",
    "Write integration tests"
  ]
}
```

**Status Update Triggers:**
- Every 15 minutes (automated heartbeat)
- Task completion
- Deliverable completion
- Blocker encountered
- Wave completion

---

### 2. Integration Contract Changes (Manual Coordination)

If an agent needs to modify an integration contract, they must:

1. **Propose change** - Create `{contract-name}.change-proposal.md`
2. **Notify affected agents** - Update proposal with `@mentions`
3. **Wait for approval** - All consumers must approve (or object within 4 hours)
4. **Implement change** - Update contract + all affected code
5. **Validate** - Run cross-agent integration tests

**Change Proposal Template:**

```markdown
# Contract Change Proposal: {contract-name}

**Proposer:** {agent-name}
**Date:** {ISO-8601}
**Affected Agents:** {list}

## Current Behavior
{describe current contract}

## Proposed Change
{describe new contract}

## Reason
{why is this change needed}

## Impact Assessment
- **Breaking Change:** Yes/No
- **Affected Files:** {list}
- **Migration Path:** {how to update consuming code}

## Approvals
- [ ] infrastructure-agent (if applicable)
- [ ] layout-agent (if applicable)
- [ ] library-agent (if applicable)
- [ ] details-agent (if applicable)
- [ ] research-agent (if applicable)

## Timeline
- Proposal: {date}
- Approval Deadline: {date + 4 hours}
- Implementation: {date + 8 hours}
```

---

### 3. Blocker Resolution (Real-time)

If an agent encounters a blocker:

1. **Update status** - Set `status: "blocked"`, add blocker to `blockers[]`
2. **Identify dependency** - Determine which agent can unblock
3. **Request unblock** - Create `blockers/{blocker-id}.md` with details
4. **Escalate if needed** - If blocker unresolved after 1 hour, escalate to orchestration coordinator

**Blocker Schema:**

```json
{
  "id": "library-agent-001",
  "blocked_agent": "library-agent",
  "blocking_agent": "infrastructure-agent",
  "wave": 2,
  "issue": "useDocuments hook not returning deleteDocument function",
  "expected": "useDocuments should return { documents, isLoading, deleteDocument }",
  "actual": "useDocuments returns { documents, isLoading } only",
  "contract_reference": "hooks.contract.md#useDocuments",
  "severity": "high",
  "created_at": "2025-10-18T11:00:00Z",
  "resolved_at": null,
  "resolution": null
}
```

---

## Synchronization Points

### Wave Gates (Hard Synchronization)

At the end of each wave, all agents must:

1. **Mark wave complete** - Update status.json: `status: "completed"`, `wave: N`
2. **Run validation** - Execute all tests for their territory
3. **Publish artifacts** - Commit all files to version control
4. **Wait for gate** - Do NOT proceed to next wave until orchestration coordinator opens gate

**Gate Opening Criteria:**
- ✅ All agents marked wave complete
- ✅ All validation tests passing
- ✅ All deliverables present
- ✅ No unresolved blockers
- ✅ Manual QA checklist complete

**Gate Coordinator:** foundation-agent (Wave 0, Wave 1, Wave 4) or lead agent per wave

---

### Soft Checkpoints (Optional Synchronization)

Within a wave, agents can request optional sync points:

```json
{
  "checkpoint": "library-agent-filter-integration",
  "requested_by": "library-agent",
  "participants": ["infrastructure-agent", "library-agent"],
  "goal": "Verify FilterBar connects to useDocumentStore correctly",
  "scheduled_at": "2025-10-18T14:00:00Z",
  "status": "pending"
}
```

---

## Conflict Resolution

### File Conflicts (Should Not Happen)

**Prevention:** Territorial ownership - each agent owns exclusive directories
**If it happens:** Merge conflict indicates boundary violation - investigate and reassign files

**Resolution Process:**
1. Identify which agent violated boundary
2. Rollback violating changes
3. Update agent-assignments.md to clarify boundaries
4. Re-implement in correct agent's territory

---

### Contract Conflicts (Disagreement on Interface)

**Scenario:** Two agents have different expectations for same interface

**Resolution Process:**
1. **Immediate halt** - Both agents pause work on conflicting feature
2. **Review contract** - Re-read original integration contract
3. **Identify ambiguity** - What was unclear?
4. **Clarify contract** - Update contract with explicit specification
5. **Get consensus** - Both agents approve updated contract
6. **Resume work** - Implement per clarified contract

**Arbitration:** If agents cannot agree, escalate to orchestration coordinator (human decision maker)

---

### Dependency Conflicts (Agent A needs Agent B's deliverable)

**Scenario:** library-agent needs `useDocuments` hook but infrastructure-agent hasn't finished it

**Resolution Options:**

#### Option 1: Mock and Continue (Preferred)
```javascript
// library-agent creates temporary mock
const useDocuments = (filters) => ({
  documents: [],
  isLoading: false,
  deleteDocument: async () => {}
});
```

#### Option 2: Reorder Tasks
- Negotiate with blocking agent to prioritize needed deliverable
- Blocking agent completes that deliverable first
- Dependent agent unblocked

#### Option 3: Parallel Stub
- Blocking agent provides stub implementation immediately
- Dependent agent uses stub for integration
- Blocking agent fills in real implementation later

---

## Integration Testing Protocol

### When to Integrate

1. **After Wave 1** - Infrastructure + layout agents integrate
2. **After Wave 2** - All view agents integrate with infrastructure + layout
3. **During Wave 3** - Continuous integration (advanced features)
4. **Wave 4** - Final full integration

### Integration Testing Steps

1. **Consumer agent validates** - Agent depending on another's work tests the integration
   - Example: library-agent tests `useDocuments` hook from infrastructure-agent

2. **Contract compliance check** - Run contract validation tests
   ```bash
   npm run test -- tests/contracts/
   ```

3. **Integration test** - Run cross-component tests
   ```bash
   npm run test -- tests/integration/
   ```

4. **Report results** - Update status.json with test results

5. **Fix or escalate** - If tests fail:
   - Minor issue → Provider fixes
   - Contract violation → Blocker filed
   - Ambiguity → Contract clarification needed

---

## Version Control Strategy

### Branch Strategy

```
main                          (production-ready code)
├── feat/wave-0-foundation   (foundation-agent Wave 0)
├── feat/wave-1-infra        (infrastructure-agent Wave 1)
├── feat/wave-1-layout       (layout-agent Wave 1)
├── feat/wave-1-utils        (foundation-agent Wave 1)
├── feat/wave-2-library      (library-agent Wave 2)
├── feat/wave-2-details      (details-agent Wave 2)
├── feat/wave-2-research     (research-agent Wave 2)
└── feat/wave-4-integration  (all agents Wave 4)
```

### Commit Convention

```
<agent>(<scope>): <subject>

Examples:
library-agent(document-card): port DocumentCard component from vanilla JS
infrastructure-agent(hooks): create useDocuments hook with React Query
layout-agent(header): add navigation links to Header component
```

### Merge Strategy

**Wave 0:** foundation-agent merges directly to `main` (solo work)

**Wave 1-3:** Each agent works on feature branch, merges at wave end
1. Agent completes wave deliverables
2. Agent runs all tests (unit + integration)
3. Agent updates status.json: `status: "completed"`
4. Agent creates PR: `feat/wave-N-{agent}` → `main`
5. Orchestration coordinator reviews PR
6. If tests pass → Merge
7. All agents pull latest `main` before starting next wave

**Wave 4:** All agents merge to `feat/wave-4-integration` branch, then merge to `main` together

---

## Daily Standup (Async)

Each agent posts daily update to `.context-kit/orchestration/react-migration/standup/{date}-{agent}.md`:

```markdown
# Standup: 2025-10-18 - library-agent

## Yesterday
- Completed DocumentCard component (port from vanilla JS)
- Completed DocumentGrid component
- Started FilterBar component (75% done)

## Today
- Finish FilterBar component
- Start UploadModal component
- Write unit tests for DocumentCard

## Blockers
- None

## Help Needed
- None

## Questions
- Should pagination use infinite scroll or page numbers? (for design consistency)
```

---

## Emergency Procedures

### Agent Failure (Agent Cannot Continue)

**Scenario:** Agent encounters unrecoverable error or cannot complete wave

**Response:**
1. **Update status** - Set `status: "error"`, provide error details
2. **Notify coordinator** - File emergency report
3. **Reassign work** - Coordinator reassigns agent's tasks to another agent
4. **Rollback if needed** - If partial work is blocking others, rollback

### Critical Bug in Dependency

**Scenario:** library-agent discovers critical bug in `useDocuments` hook during Wave 2

**Response:**
1. **File blocker** - Create blocker with severity: "critical"
2. **Notify infrastructure-agent** - Tag in blocker issue
3. **Pause dependent work** - Stop work that depends on buggy code
4. **Hotfix** - Infrastructure-agent creates hotfix branch, fixes bug, merges immediately
5. **Verify fix** - Library-agent validates fix, resumes work

### Wave Gate Failure

**Scenario:** Wave 2 gate validation fails (tests failing)

**Response:**
1. **Identify failing agent** - Check which agent's tests are failing
2. **Fix in place** - Failing agent fixes issues immediately
3. **Re-run validation** - Run tests again
4. **If multiple failures** - Rollback entire wave, start over (rare)

---

## Success Metrics & Monitoring

### Agent Performance Metrics

```json
{
  "agent": "library-agent",
  "metrics": {
    "tasks_completed": 9,
    "tasks_total": 9,
    "completion_rate": 1.0,
    "test_pass_rate": 0.95,
    "blockers_encountered": 0,
    "blockers_created_for_others": 1,
    "contract_violations": 0,
    "time_to_complete_wave": "2.3 days"
  }
}
```

### Wave Completion Metrics

```json
{
  "wave": 2,
  "metrics": {
    "start_date": "2025-10-18",
    "end_date": "2025-10-20",
    "duration_days": 2,
    "agents_participating": 3,
    "tasks_completed": 30,
    "tests_written": 45,
    "test_pass_rate": 1.0,
    "integration_issues": 2,
    "contract_changes": 0,
    "blockers_filed": 1,
    "blockers_resolved": 1
  }
}
```

---

## Communication Best Practices

### Do's ✅
- **Update status frequently** - Every 15 minutes or on significant changes
- **Be specific in blockers** - Include expected vs actual behavior
- **Reference contracts** - Always cite contract section when discussing interfaces
- **Test before claiming complete** - Run tests before marking deliverable done
- **Ask questions early** - Don't wait until blocked to ask for clarification

### Don'ts ❌
- **Don't edit other agents' files** - Respect territorial boundaries
- **Don't assume contracts** - Always read integration contracts before implementing
- **Don't skip validation** - Always run tests before moving to next task
- **Don't merge without approval** - Wait for coordinator to approve wave completion
- **Don't hide blockers** - Report issues immediately

---

## Escalation Path

1. **Agent → Agent** - Direct communication for minor issues (4 hour SLA)
2. **Agent → Coordinator** - For blockers unresolved after 4 hours
3. **Coordinator → Human** - For conflicts requiring product/design decisions

**Coordinator Responsibilities:**
- Monitor all agent status.json files
- Identify blockers early
- Facilitate conflict resolution
- Approve wave gate openings
- Track overall progress

---

## Tools & Automation

### Status Monitor Script

```bash
#!/bin/bash
# scripts/monitor-agents.sh

echo "Agent Status Monitor"
echo "===================="

for agent in foundation infrastructure layout library details research; do
  status_file=".context-kit/orchestration/react-migration/status/${agent}-agent.json"
  if [ -f "$status_file" ]; then
    status=$(jq -r '.status' "$status_file")
    wave=$(jq -r '.wave' "$status_file")
    progress=$(jq -r '(.completed_tasks / .total_tasks * 100) | floor' "$status_file")
    echo "$agent-agent: Wave $wave - $status - $progress%"
  else
    echo "$agent-agent: No status file found"
  fi
done
```

### Integration Test Runner

```bash
#!/bin/bash
# scripts/run-integration-tests.sh

echo "Running Integration Tests"
echo "========================="

# Run all integration tests
npm run test -- tests/integration/ --run

# Run contract validation
npm run test -- tests/contracts/ --run

# Check for failures
if [ $? -eq 0 ]; then
  echo "✅ All integration tests passed"
  exit 0
else
  echo "❌ Integration tests failed"
  exit 1
fi
```

---

## Summary

**Key Principles:**
1. **Territorial Ownership** - Each agent owns specific files, no overlaps
2. **Interface-First** - All agents read contracts before implementing
3. **Continuous Validation** - Test early, test often
4. **Transparent Communication** - Status updates every 15 minutes
5. **Fail Fast** - Report blockers immediately

**Success Criteria:**
- ✅ All agents complete their waves on time
- ✅ Zero merge conflicts (proper boundaries)
- ✅ All integration tests passing
- ✅ All contracts honored
- ✅ Production-ready code at end of Wave 4
