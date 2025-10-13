# Coordination Protocol - Library Frontend

**Goal**: Synchronize 11 agents across 3 waves with zero conflicts
**Approach**: Clear gates, status broadcasting, failure recovery
**Communication**: Specification-driven integration

---

## Coordination Principles

### **1. Territorial Ownership**
- Each agent owns specific files
- Zero file overlaps
- No shared file modifications
- Integration via contracts, not coupling

### **2. Wave-Based Execution**
- Synchronous waves with explicit gates
- All agents complete wave before next wave starts
- Progressive validation at each gate
- Failure stops progression

### **3. Contract-Driven Integration**
- Specifications defined before implementation
- Agents code to contracts, not to each other
- Runtime integration via DOM events
- No direct dependencies between agents

### **4. Status Broadcasting**
- Each agent reports progress
- Coordination lead monitors status
- Blockers escalated immediately
- Validation gates enforce quality

---

## Wave Execution Protocol

### **Wave Start**

1. **Coordination Lead Announces Wave**
   - Broadcast wave number and agent assignments
   - Confirm all agents ready
   - Release agents to begin work

2. **Agents Acknowledge**
   - Each agent confirms receipt
   - Each agent confirms understanding of responsibilities
   - Each agent confirms contract review

3. **Work Begins**
   - All agents work in parallel (Wave 1)
   - Sequential agents wait for dependencies (Wave 2, 3)
   - Status updates every 30 minutes or at checkpoints

### **During Wave**

**Status Update Format**:
```
Agent: {agent_id}
Wave: {wave_number}
Status: {in_progress|blocked|completed}
Progress: {percentage}
Blockers: {none|description}
ETA: {time_estimate}
```

**Example**:
```
Agent: library-agent
Wave: 1
Status: in_progress
Progress: 60%
Blockers: none
ETA: 30 minutes
```

### **Wave Completion**

1. **Agent Reports Completion**
   ```
   Agent: library-agent
   Wave: 1
   Status: completed
   Deliverables:
     - library-manager.js ✓
     - websocket-client.js ✓
     - api-client.js ✓
   Self-Validation: passed
   ```

2. **Coordination Lead Validates**
   - Run automated validation checks
   - Verify deliverables exist
   - Check contract compliance
   - Review code quality

3. **Gate Decision**
   - ✅ **PASS**: All agents complete, validation passes → Proceed to next wave
   - ❌ **FAIL**: Any agent incomplete or validation fails → Block progression
   - 🔄 **RETRY**: Minor issues, quick fix → Re-validate

### **Wave Gate**

**Gate Criteria** (all must be true):
- [ ] All assigned agents report completion
- [ ] All deliverables present
- [ ] Automated validation passes
- [ ] Integration smoke tests pass
- [ ] No critical blockers

**Gate Options**:
1. **PROCEED** - All checks pass, start next wave
2. **HOLD** - Minor issues, fix and re-validate within 1 hour
3. **ROLLBACK** - Major issues, revert and restart wave

---

## Communication Channels

### **1. Status Updates**

**Frequency**: Every 30 minutes or at key milestones

**Format**:
```markdown
## Status Update - {timestamp}

**Agent**: {agent_id}
**Wave**: {wave_number}
**Status**: {in_progress|blocked|completed}

### Progress
- {Task 1}: ✓ Complete
- {Task 2}: 🔄 In Progress (75%)
- {Task 3}: ⏳ Pending

### Blockers
- {None|Description of blocker}

### Next Steps
- {What's coming next}

### Questions/Concerns
- {Any questions or concerns}
```

---

### **2. Blocker Escalation**

**When to Escalate**:
- Blocked for >15 minutes
- Unclear contract specification
- Integration issue discovered
- External dependency failure

**Escalation Format**:
```markdown
## BLOCKER - {timestamp}

**Agent**: {agent_id}
**Wave**: {wave_number}
**Severity**: {low|medium|high|critical}

### Issue
{Clear description of the blocker}

### Impact
{What is blocked, which other agents affected}

### Attempted Solutions
- {What has been tried}

### Assistance Needed
{What is needed to unblock}
```

**Response Time**:
- Critical: <5 minutes
- High: <15 minutes
- Medium: <30 minutes
- Low: <1 hour

---

### **3. Contract Clarification**

**When Needed**:
- Ambiguous specification
- Missing detail
- Integration point unclear

**Request Format**:
```markdown
## Contract Clarification - {timestamp}

**Agent**: {agent_id}
**Contract**: {contract_name}
**Section**: {section reference}

### Question
{Specific question about the contract}

### Context
{Why this matters, what you're trying to implement}

### Proposed Interpretation
{Your best guess at the answer}
```

---

## Validation Protocol

### **Self-Validation** (Agent Responsibility)

Each agent must validate their own work before reporting completion:

1. **Syntactic Validation**
   - Code parses without errors
   - No console errors
   - Exports available

2. **Contract Compliance**
   - Function signatures match
   - Event payloads match
   - Return types correct

3. **Basic Functionality**
   - Component renders
   - Events emit
   - API calls work

**Self-Validation Checklist**:
```markdown
- [ ] Code syntax valid (no parse errors)
- [ ] All exports present
- [ ] Contracts followed
- [ ] Browser console clean (no errors)
- [ ] Basic smoke test passed
- [ ] Deliverables complete
```

---

### **Gate Validation** (Coordination Lead)

At each wave gate, coordination lead validates:

1. **Completeness Check**
   ```bash
   # All expected files exist
   # All agents reported completion
   # All deliverables present
   ```

2. **Automated Validation**
   ```bash
   # Run validation script
   ./src/frontend/validate.sh
   ```

3. **Integration Smoke Test**
   ```bash
   # Load page, check console
   # Verify imports work
   # Check DOM structure
   ```

4. **Contract Compliance Spot Check**
   ```javascript
   // Test key integration points
   // Verify event formats
   // Check API signatures
   ```

---

## Failure Recovery Protocol

### **Agent Failure**

**Scenario**: Agent unable to complete assigned work

**Actions**:
1. **Identify Issue**
   - Agent reports blocker
   - Coordination lead investigates
   - Determine if resolvable

2. **Mitigation Options**:
   - **Quick Fix**: Agent fixes issue, re-validates, continues
   - **Assistance**: Another agent helps, issue resolved
   - **Reassignment**: Work reassigned to different agent
   - **Wave Restart**: If major issue, restart entire wave

3. **Communication**:
   - Inform all agents of delay
   - Update timeline
   - Adjust dependencies

---

### **Integration Failure**

**Scenario**: Components don't integrate correctly

**Actions**:
1. **Identify Integration Point**
   - Which agents affected?
   - Which contract violated?
   - What is the mismatch?

2. **Root Cause**:
   - Contract ambiguous?
   - Implementation incorrect?
   - Misunderstanding?

3. **Resolution**:
   - **Contract Issue**: Update contract, re-implement both sides
   - **Implementation Issue**: One agent fixes, other re-validates
   - **Misunderstanding**: Clarify, re-implement, re-test

4. **Prevention**:
   - Update contract with clarification
   - Add validation check
   - Document lesson learned

---

### **Validation Failure**

**Scenario**: Wave validation fails

**Actions**:
1. **Identify Failure**
   - Which validation check failed?
   - Which agent's work affected?
   - Severity of failure?

2. **Fix Strategy**:
   - **Minor**: Quick fix, re-validate, proceed
   - **Major**: Rollback, restart wave
   - **Blocker**: Investigate, resolve, restart

3. **Re-Validation**:
   - Run full validation suite
   - Manual verification
   - Integration testing

---

## Agent Handoff Protocol

### **When Needed**
- Wave 1 → Wave 2 transition
- Wave 2 → Wave 3 transition
- Agent dependencies

### **Handoff Checklist**

**From Agent (Producer)**:
```markdown
## Handoff - {from_agent} → {to_agent}

### Deliverables
- {File 1}: Complete, location: {path}
- {File 2}: Complete, location: {path}

### Contract Compliance
- {Contract 1}: ✓ Compliant
- {Contract 2}: ✓ Compliant

### Known Issues
- {None|List of issues}

### Integration Notes
- {How to use the deliverable}
- {Special considerations}

### Test Coverage
- {What is tested}
- {What needs testing}
```

**To Agent (Consumer)**:
```markdown
## Handoff Received - {to_agent}

### Validation
- [ ] Deliverables received
- [ ] Contracts reviewed
- [ ] Integration points understood
- [ ] Ready to proceed

### Questions
- {Any clarifications needed}
```

---

## Status Tracking

### **Wave Progress Dashboard**

```markdown
# Library Frontend - Wave Progress

## Wave 0: Foundation
- [x] infrastructure-agent: Complete ✓

## Wave 1: Parallel Development
- [x] html-agent: Complete ✓
- [x] library-agent: Complete ✓
- [x] card-agent: Complete ✓
- [x] filter-agent: Complete ✓
- [x] upload-agent: Complete ✓
- [x] style-agent: Complete ✓

## Wave 2: Integration & Testing
- [ ] integration-agent: In Progress (60%)
- [ ] e2e-agent: Pending
- [ ] docs-agent: Pending

## Wave 3: Polish & Production
- [ ] perf-agent: Pending
- [ ] cleanup-agent: Pending
```

---

## Meeting Cadence

### **Wave Kickoff** (15 minutes)
- Review wave goals
- Confirm agent assignments
- Answer questions
- Release to work

### **Daily Standup** (15 minutes)
- Each agent: Yesterday, Today, Blockers
- Address blockers
- Adjust timeline if needed

### **Wave Retrospective** (30 minutes)
- What went well?
- What didn't go well?
- Lessons learned
- Improvements for next wave

---

## Documentation Protocol

### **Agent Deliverables**

Each agent must provide:

1. **Code/Files**
   - All assigned files
   - Properly formatted
   - Commented as needed

2. **Self-Validation Report**
   - Checklist completed
   - Tests run
   - Results documented

3. **Integration Notes**
   - How to use the component
   - Known limitations
   - Future enhancements

---

## Success Metrics

### **Efficiency**
- **Target**: Wave 1 complete in 1 day (6 agents in parallel)
- **Measure**: Time from wave start to gate pass

### **Quality**
- **Target**: Zero integration bugs
- **Measure**: Number of issues at each gate

### **Collaboration**
- **Target**: <5 blocker escalations per wave
- **Measure**: Number of escalations, resolution time

### **Completeness**
- **Target**: 100% deliverables on first attempt
- **Measure**: Percentage of work needing rework

---

## Emergency Protocol

### **Critical Blocker**

**Definition**: Issue preventing all forward progress

**Actions**:
1. **IMMEDIATE**: All agents stop work
2. **IMMEDIATE**: Coordination lead notified
3. **15 MIN**: Emergency meeting to assess
4. **30 MIN**: Resolution plan developed
5. **DECISION**: Proceed, rollback, or pivot

---

### **External Dependency Failure**

**Example**: ChromaDB down, Worker crash

**Actions**:
1. **ASSESS**: Which agents affected?
2. **COMMUNICATE**: Notify affected agents
3. **WORKAROUND**: Can work proceed with mocks?
4. **RESOLVE**: Fix external dependency
5. **RESUME**: Re-validate and continue

---

## Coordination Lead Responsibilities

1. **Monitor Progress**
   - Track agent status
   - Identify blockers early
   - Ensure timeline adherence

2. **Validate Quality**
   - Run validation checks
   - Verify contract compliance
   - Approve wave gates

3. **Resolve Conflicts**
   - Address blockers quickly
   - Clarify contracts
   - Mediate integration issues

4. **Communicate Status**
   - Update stakeholders
   - Report progress
   - Escalate major issues

---

## Final Checklist

Before declaring production ready:

```markdown
## Production Readiness Checklist

### Functionality
- [ ] All features implemented
- [ ] Real-time updates working
- [ ] Upload flow functional
- [ ] Filtering/sorting working
- [ ] Pagination working

### Quality
- [ ] All tests passing (>80% coverage)
- [ ] No console errors
- [ ] Performance targets met
- [ ] Accessibility validated (WCAG AA)
- [ ] Security reviewed

### Documentation
- [ ] README complete
- [ ] API docs updated
- [ ] Integration contracts documented
- [ ] User guide provided

### Deployment
- [ ] POC removed
- [ ] All services running
- [ ] Frontend accessible
- [ ] End-to-end verified

### Sign-off
- [ ] Coordination lead approval
- [ ] Technical review complete
- [ ] User acceptance testing passed
```

---

**Status**: Ready for implementation
**Next Step**: Wave 0 - Foundation setup
