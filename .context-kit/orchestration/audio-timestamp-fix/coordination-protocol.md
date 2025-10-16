# Coordination Protocol - Audio Timestamp Fix

## Communication Channels

### Status File
**Location**: `.context-kit/orchestration/audio-timestamp-fix/status.md`

**Format**:
```markdown
## Wave [N] Status - [Timestamp]

### [Agent Name]
- Status: [✅ Complete | 🔄 In Progress | ⏸️ Waiting | ❌ Blocked]
- Current Task: [specific task from orchestration plan]
- Progress: [X/Y deliverables complete]
- Blockers: [None | specific blocker description]
- ETA: [time estimate if in progress]
- Last Updated: [timestamp]
```

**Update Frequency**: Every 30 minutes or on status change

---

### Issues File
**Location**: `.context-kit/orchestration/audio-timestamp-fix/issues.md`

**Format**:
```markdown
## Issue #[N]: [Short Description]
- **Reported By**: [Agent Name]
- **Date**: [Timestamp]
- **Severity**: [Critical | High | Medium | Low]
- **Affected Components**: [list of files/contracts]
- **Description**: [detailed problem description]
- **Proposed Solution**: [if any]
- **Status**: [Open | In Progress | Resolved]
- **Resolution**: [how it was resolved, if applicable]
```

---

### Contract Review Process
**Location**: `.context-kit/orchestration/audio-timestamp-fix/contract-reviews.md`

**Format**:
```markdown
## [Contract ID]: [Contract Name] - Review

### Author
[Agent Name]

### Reviewers
- [ ] Backend Implementation Agent
- [ ] Frontend Implementation Agent
- [ ] Integration Testing Agent

### Review Comments
#### [Reviewer Name]
- **Status**: [Approved | Changes Requested]
- **Comments**: [specific feedback]
- **Date**: [timestamp]

### Resolution
- **Final Status**: [Approved | Revised]
- **Changes Made**: [if any]
- **Approval Date**: [timestamp]
```

---

## Wave Transition Protocol

### Gate 1: Specification Complete (After Wave 1)

**Checklist Owner**: Backend Specification Agent

**Steps**:
1. Backend Spec Agent marks all contracts complete
2. Backend Spec Agent posts Gate 1 checklist:
   ```markdown
   ## Gate 1 Checklist
   - [ ] IC-001: TextChunk Timestamp Contract (complete + reviewed)
   - [ ] IC-002: VTT Pipeline Contract (complete + reviewed)
   - [ ] IC-003: Metadata Flags Contract (complete + reviewed)
   - [ ] IC-004: API Response Contract (complete + reviewed)
   - [ ] IC-005: VTT Track Element Contract (complete + reviewed)
   - [ ] IC-006: Caption Display Contract (complete + reviewed)
   - [ ] IC-007: Accordion Timestamp Contract (complete + reviewed)
   - [ ] IC-008: Deprecation Contract (complete + reviewed)
   - [ ] All contracts reviewed by dependent agents
   - [ ] No critical issues open
   - [ ] Backend Impl Agent ready to proceed
   - [ ] Frontend Impl Agent ready to proceed
   ```
3. Each agent reviews assigned contracts and approves
4. Once all checkboxes ticked, Gate 1 passes
5. Backend Spec Agent announces: "Gate 1 PASSED - Wave 2 may begin"
6. Backend and Frontend Implementation Agents update status to "In Progress"

**Failure Condition**: If any contract rejected, must be revised and re-reviewed

---

### Gate 2: Implementation Complete (After Wave 2)

**Checklist Owner**: Backend Implementation Agent

**Steps**:
1. Backend Impl Agent completes work and runs unit tests
2. Frontend Impl Agent completes work and creates test page
3. Backend Impl Agent posts Gate 2 checklist:
   ```markdown
   ## Gate 2 Checklist
   - [ ] Backend: All unit tests pass (pytest)
   - [ ] Backend: `extract_timestamps_from_text()` implemented
   - [ ] Backend: TextChunk fields populated correctly
   - [ ] Backend: Metadata flags accurate
   - [ ] Backend: VTT generation triggers
   - [ ] Backend: No regression in existing tests
   - [ ] Frontend: Native track element working
   - [ ] Frontend: Markdown parsing removed
   - [ ] Frontend: Test page demonstrates VTT
   - [ ] Frontend: Backward compatibility implemented
   - [ ] Code review completed
   - [ ] No critical issues open
   - [ ] Integration Agent ready to test
   ```
4. Each implementation agent validates their section
5. Cross-review: Frontend agent reviews backend code, vice versa
6. Once all checkboxes ticked, Gate 2 passes
7. Backend Impl Agent announces: "Gate 2 PASSED - Wave 3 may begin"
8. Integration Testing Agent updates status to "In Progress"

**Failure Condition**: If any tests fail or code review rejects, must be fixed

---

### Gate 3: Integration Validated (After Wave 3)

**Checklist Owner**: Integration Testing Agent

**Steps**:
1. Integration Agent runs end-to-end test
2. Integration Agent runs reprocessing script
3. Integration Agent performs manual browser testing
4. Integration Agent posts Gate 3 checklist:
   ```markdown
   ## Gate 3 Checklist
   - [ ] Integration test passes 100%
   - [ ] Existing audio file reprocessed successfully
   - [ ] VTT file exists at data/vtt/{doc_id}.vtt
   - [ ] VTT file valid (passes validation)
   - [ ] API response includes populated timestamps
   - [ ] VTT endpoint returns valid content
   - [ ] Browser: Captions display correctly
   - [ ] Browser: Accordion shows cleaned text
   - [ ] Browser: Click-to-seek works
   - [ ] Performance: Caption sync <50ms
   - [ ] Regression: Non-audio docs unaffected
   - [ ] Backward compat: Null timestamps handled
   - [ ] Documentation updated
   - [ ] Migration checklist complete
   ```
5. All agents review validation results
6. Once all checkboxes ticked, Gate 3 passes
7. Integration Agent announces: "Gate 3 PASSED - Ready for production"

**Failure Condition**: If integration test fails, rollback to Wave 2 for fixes

---

## Contract Change Management

### Minor Change (No Breaking Changes)
**Examples**: Clarify wording, add example, improve comments

**Process**:
1. Author updates contract with `[UPDATED - v1.1]` tag
2. Post notice in status.md: "IC-00X updated (minor)"
3. Dependent agents acknowledge within 1 hour
4. No re-approval needed

---

### Major Change (Breaking Changes)
**Examples**: Change function signature, modify data structure, alter behavior

**Process**:
1. Author proposes change with `[PROPOSAL - v2.0]` tag in contract file
2. Post detailed explanation in issues.md:
   ```markdown
   ## Issue #[N]: Contract Change Proposal - IC-00X
   - **Proposed By**: [Agent Name]
   - **Reason**: [why change is needed]
   - **Impact**: [which agents/files affected]
   - **Alternative Considered**: [if any]
   - **Approval Needed From**: [list of dependent agents]
   ```
3. All dependent agents review and comment
4. If approved by all:
   - Update contract with `[APPROVED - v2.0]` tag
   - Notify all dependent agents
   - Dependent agents update implementations
   - May delay gate transition
5. If rejected:
   - Discuss alternatives
   - Find compromise solution
   - Repeat process

**Escalation**: If consensus can't be reached, escalate to orchestration lead

---

## Code Review Protocol

### Backend Code Review
**Reviewer**: Frontend Implementation Agent (consumer perspective)

**Checklist**:
- [ ] Function signatures match IC-001, IC-002
- [ ] Error handling follows contract
- [ ] Logging adequate for debugging
- [ ] Type hints and docstrings present
- [ ] Test coverage comprehensive
- [ ] No obvious bugs or edge case issues
- [ ] Performance acceptable

**Process**:
1. Backend Impl Agent posts: "Backend code ready for review"
2. Frontend Impl Agent reviews within 2 hours
3. Frontend Impl Agent posts review in contract-reviews.md
4. If changes requested, Backend Impl Agent fixes and re-submits
5. If approved, Backend Impl Agent proceeds to Gate 2

---

### Frontend Code Review
**Reviewer**: Backend Implementation Agent (producer perspective)

**Checklist**:
- [ ] Uses API response correctly per IC-004
- [ ] Native track element implemented per IC-005
- [ ] Error handling for missing VTT
- [ ] Backward compatibility for null timestamps
- [ ] Code cleaner (markdown parsing removed)
- [ ] No obvious UI bugs
- [ ] Test page demonstrates functionality

**Process**:
1. Frontend Impl Agent posts: "Frontend code ready for review"
2. Backend Impl Agent reviews within 2 hours
3. Backend Impl Agent posts review in contract-reviews.md
4. If changes requested, Frontend Impl Agent fixes and re-submits
5. If approved, Frontend Impl Agent proceeds to Gate 2

---

## Conflict Resolution

### File Conflict (Should Never Happen)
With territorial ownership, file conflicts should never occur. If they do:

1. **Stop immediately** - both agents pause work
2. **Document conflict** in issues.md with CRITICAL severity
3. **Review territory assignments** - identify where boundaries were unclear
4. **Clarify ownership** - update agent-assignments.md
5. **Resolve conflict** - owner keeps their changes, other agent adapts
6. **Update protocol** - improve territoriality to prevent recurrence

---

### Dependency Conflict
**Example**: Frontend agent needs backend feature not yet implemented

**Process**:
1. Frontend agent posts in issues.md: "Dependency Issue"
2. Backend agent prioritizes the needed feature
3. Frontend agent continues with other tasks or creates mock/stub
4. Once backend feature ready, frontend agent integrates
5. Mark issue resolved

---

### Performance Conflict
**Example**: Backend implementation too slow for frontend requirements

**Process**:
1. Frontend agent measures and documents performance issue
2. Post in issues.md with performance benchmarks
3. Backend agent investigates optimization options
4. If optimization possible: implement and re-test
5. If not possible: negotiate revised performance contract
6. Update IC-002 or other contracts if thresholds change

---

## Status Indicators

### Agent Status
- ✅ **Complete**: All deliverables done, validated, ready for next wave
- 🔄 **In Progress**: Actively working on deliverables
- ⏸️ **Waiting**: Ready but waiting for gate/dependencies
- ❌ **Blocked**: Cannot proceed due to issue or dependency
- 🔍 **Review**: Work complete, awaiting code review
- 🚀 **Ready**: Reviewed and approved, ready for gate transition

### Contract Status
- 📝 **Draft**: Initial version being written
- 👀 **Under Review**: Awaiting approval from dependent agents
- ✅ **Approved**: Reviewed and approved, implementation may proceed
- 🔄 **Revision**: Changes requested, being updated
- 📋 **Proposal**: Major change proposed, awaiting discussion
- 🔒 **Locked**: Approved and locked, no further changes without escalation

### Issue Status
- 🆕 **Open**: New issue reported, not yet addressed
- 🔄 **In Progress**: Being actively worked on
- ⏸️ **Blocked**: Waiting on external factor
- ✅ **Resolved**: Fixed and verified
- ❌ **Won't Fix**: Decided not to address
- 📋 **Deferred**: Important but postponed to future work

---

## Emergency Procedures

### Critical Bug Found
1. Agent discovering bug posts CRITICAL issue immediately
2. All affected agents stop work on affected components
3. Team discusses root cause and solution
4. Assign owner to fix
5. Test fix thoroughly before resuming work
6. May require contract revision or wave rollback

### Gate Failure
1. Agent running gate checklist identifies failure
2. Post failed checklist with details of what failed
3. Identify root cause (code bug, test issue, contract mismatch)
4. Assign owner to fix
5. Re-run gate checklist once fixed
6. Do not proceed to next wave until gate passes

### Rollback Procedure
If Wave 3 integration testing fails catastrophically:

1. **Frontend rollback**: Revert audio-player.js and accordion.js changes
   - Restore markdown parsing code
   - System returns to working state

2. **Backend preserved**: Keep timestamp extraction improvements
   - Data structure improved even if frontend doesn't use yet
   - Can retry frontend integration later

3. **Analysis phase**: Document what went wrong
   - Update integration contracts based on findings
   - Plan fixes before retry

4. **Retry**: Re-execute Wave 2 (frontend only) or Wave 3 with fixes

---

## Success Signals

### Wave 1 Success
- 📋 All 8 integration contracts written and approved
- 👥 All dependent agents acknowledged readiness
- ✅ Gate 1 checklist complete

### Wave 2 Success
- ✅ All unit tests pass (15+ backend tests)
- 🎨 Frontend test page demonstrates VTT working
- 👀 Cross-agent code reviews approved
- ✅ Gate 2 checklist complete

### Wave 3 Success
- ✅ Integration test passes 100%
- 🎯 Performance requirements met (<50ms caption sync)
- 🔄 Existing files reprocessed successfully
- 🌐 Browser testing confirms correct display
- ✅ Gate 3 checklist complete

### Final Success
- 🚀 Production deployment complete
- 📊 Validation report shows all metrics green
- 📚 Documentation updated
- 🎉 Feature working as designed

---

**Communication is Key**: Regular status updates, proactive issue reporting, and thorough contract reviews ensure smooth parallel execution and successful integration.
