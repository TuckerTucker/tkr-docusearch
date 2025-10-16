# Audio Timestamp Architecture Fix - Orchestration

## Quick Reference

**Goal**: Replace fragile markdown parsing with proper VTT file generation by extracting timestamps from markdown into TextChunk fields.

**Status**: 📋 Ready to Begin Wave 1

**Agents**: 5 specialized agents across 3 waves

---

## Documentation Structure

| File | Purpose |
|------|---------|
| **orchestration-plan.md** | Complete execution plan with waves, tasks, and gates |
| **agent-assignments.md** | Agent responsibilities and territorial boundaries |
| **coordination-protocol.md** | Communication and status management |
| **validation-strategy.md** | Testing and quality assurance approach |
| **integration-contracts/** | Detailed interface specifications (IC-001 through IC-008) |
| **status.md** | Real-time agent status updates |
| **issues.md** | Issue tracking and resolution |
| **validation-results.md** | Final test results and approval |

---

## Quick Start

### For Orchestration Lead

1. **Review the plan**: Read `orchestration-plan.md`
2. **Assign agents**: Allocate agents to roles from `agent-assignments.md`
3. **Kick off Wave 1**: Post initial status update
4. **Monitor progress**: Track status in `status.md`
5. **Manage gates**: Validate gate criteria before wave transitions

### For Agent Participants

1. **Read your assignment**: Check `agent-assignments.md` for your territory and deliverables
2. **Review contracts**: Understand which integration contracts you depend on
3. **Update status regularly**: Post updates in `status.md` every 30 min
4. **Report issues**: Document any problems in `issues.md`
5. **Follow coordination protocol**: See `coordination-protocol.md` for details

---

## Wave Overview

### Wave 1: Specification (Parallel)
- **Agents**: Backend Spec, Frontend Spec
- **Duration**: 2-3 hours
- **Output**: 8 integration contracts (IC-001 through IC-008)
- **Gate**: All contracts approved by dependent agents

### Wave 2: Implementation (Parallel)
- **Agents**: Backend Impl, Frontend Impl
- **Duration**: 3-4 hours
- **Output**: Timestamp extraction + VTT integration code
- **Gate**: All tests pass, code reviews approved

### Wave 3: Validation (Sequential)
- **Agent**: Integration Testing
- **Duration**: 3-4 hours
- **Output**: Integration tests, reprocessing script, validation report
- **Gate**: 100% test pass, performance targets met

---

## Key Contracts

| Contract | Description | Owner | Consumers |
|----------|-------------|-------|-----------|
| **IC-001** | TextChunk timestamp structure | Backend Spec | Backend Impl |
| **IC-002** | VTT pipeline integration | Backend Spec | Backend Impl |
| **IC-003** | Metadata flags (has_timestamps, vtt_available) | Backend Spec | Backend Impl, API |
| **IC-004** | API response schema | Backend Spec | Frontend Impl |
| **IC-005** | VTT track element usage | Frontend Spec | Frontend Impl |
| **IC-006** | Caption display logic | Frontend Spec | Frontend Impl |
| **IC-007** | Accordion timestamp display | Frontend Spec | Frontend Impl |
| **IC-008** | Deprecation strategy | Frontend Spec | Frontend Impl |

---

## Current Status

**Wave**: Not started
**Active Agents**: None
**Blocked**: None
**Next Milestone**: Begin Wave 1 specification

---

## Success Criteria

### Technical
- ✅ Timestamps extracted from `[time: X-Y]` markers
- ✅ TextChunk objects populated with start_time/end_time
- ✅ VTT files generated automatically
- ✅ Frontend uses native HTML5 `<track>` element
- ✅ ~100 lines of regex parsing removed
- ✅ Caption sync latency <50ms

### Quality
- ✅ 15+ unit tests pass
- ✅ Integration tests 100% pass
- ✅ Code coverage ≥95%
- ✅ Zero regression in existing features
- ✅ Performance targets met

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Breaking existing functionality | Preserve working system until Wave 3 validation |
| Timestamp extraction failures | Comprehensive unit tests, graceful error handling |
| VTT generation not triggering | Verify metadata flags, add logging |
| Frontend-backend mismatch | Wave 1 contract alignment, cross-agent reviews |

---

## Contact Points

### Escalation Path
1. **Agent-to-agent**: Post in issues.md
2. **Gate blockers**: Notify all agents in status.md
3. **Critical failures**: Document in issues.md with CRITICAL tag

### Status Updates
- Post every 30 minutes in `status.md`
- Use status indicators: ✅ Complete, 🔄 In Progress, ⏸️ Waiting, ❌ Blocked

---

## Files Created During Execution

### Wave 1
- `integration-contracts/IC-001-textchunk-timestamp.md`
- `integration-contracts/IC-002-vtt-pipeline.md`
- `integration-contracts/IC-003-metadata-flags.md`
- `integration-contracts/IC-004-api-response.md`
- `integration-contracts/IC-005-vtt-track-element.md`
- `integration-contracts/IC-006-caption-display.md`
- `integration-contracts/IC-007-accordion-timestamp.md`
- `integration-contracts/IC-008-deprecation.md`

### Wave 2
- `src/processing/test_timestamp_extraction.py` (NEW)
- `src/processing/text_processor.py` (MODIFIED)
- `src/processing/processor.py` (MINIMAL CHANGES)
- `src/frontend/audio-player.js` (MODIFIED)
- `src/frontend/accordion.js` (MODIFIED)
- `src/frontend/test_vtt_integration.html` (NEW)

### Wave 3
- `src/test_audio_timestamp_integration.py` (NEW)
- `scripts/reprocess_audio_files.py` (NEW)
- `validation-results.md` (NEW)
- `migration-checklist.md` (NEW)

---

## Timeline Estimate

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Wave 1 (Specification) | 2-3 hours | 3 hours |
| Gate 1 Review | 30 min | 3.5 hours |
| Wave 2 (Implementation) | 3-4 hours | 7.5 hours |
| Gate 2 Review | 1 hour | 8.5 hours |
| Wave 3 (Validation) | 3-4 hours | 12.5 hours |
| Gate 3 Review | 30 min | 13 hours |
| **Total** | **~13 hours** | **2 work days** |

---

## Next Steps

1. ✅ Orchestration plan complete
2. ⏳ Assign agents to roles
3. ⏳ Create initial status.md
4. ⏳ Begin Wave 1: Backend Spec Agent starts IC-001
5. ⏳ Begin Wave 1: Frontend Spec Agent starts IC-005

---

**Orchestration Framework**: Wave-based execution with territorial ownership and progressive validation

**Last Updated**: 2025-10-16
