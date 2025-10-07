# Coordination Protocol: Docling Enhanced Mode

**Plan ID**: docling-enhanced-mode
**Version**: 1.0
**Status**: Active

## Purpose

Define communication protocols, status reporting, and coordination mechanisms for parallel agent execution to ensure successful integration without conflicts.

---

## Communication Channels

### Status Broadcasting

**Channel**: Orchestration status file
**Location**: `.context-kit/orchestration/docling-enhanced-mode/status/agent-status.json`

**Format**:
```json
{
  "agent_id": "config-agent",
  "wave": 1,
  "status": "in_progress",  // pending, in_progress, complete, failed
  "progress": 0.75,          // 0.0 - 1.0
  "current_task": "Creating configuration dataclasses",
  "deliverables_complete": [
    "src/config/processing_config.py"
  ],
  "tests_status": {
    "unit_tests": "passing",
    "integration_tests": "pending"
  },
  "last_updated": "2025-10-07T14:30:00Z",
  "notes": "Configuration loading works, validation in progress"
}
```

### Update Protocol

Each agent must:
1. **Initialize**: Create status file when starting work
2. **Update frequently**: Every major task completion (~15-30 min)
3. **Report deliverables**: List completed files
4. **Report test status**: Pass/fail for each test category
5. **Finalize**: Mark complete when all tasks done

---

## Wave Coordination

### Wave Start Protocol

**Before starting Wave N**:

1. **Orchestrator verifies prerequisites**:
   - Previous wave (N-1) complete
   - All agents from Wave N-1 reported success
   - Wave gate tests passed
   - Integration contracts available

2. **Orchestrator broadcasts wave start**:
   ```json
   {
     "wave": N,
     "status": "starting",
     "agents": ["agent-1", "agent-2"],
     "start_time": "2025-10-07T14:00:00Z",
     "prerequisites": ["contract-1", "contract-2"]
   }
   ```

3. **Agents acknowledge**:
   - Read assigned integration contracts
   - Verify prerequisites available
   - Create status file
   - Begin work

### Wave Completion Protocol

**When agent completes Wave N work**:

1. **Agent updates status**:
   ```json
   {
     "agent_id": "config-agent",
     "wave": 1,
     "status": "complete",
     "progress": 1.0,
     "deliverables_complete": [
       "src/config/processing_config.py",
       ".env.template (updated)"
     ],
     "tests_status": {
       "unit_tests": "passing (5/5)",
       "integration_tests": "passing (2/2)"
     },
     "completion_time": "2025-10-07T15:30:00Z"
   }
   ```

2. **Agent runs self-validation**:
   ```bash
   # Run agent-specific tests
   pytest src/config/ -v
   ```

3. **Agent reports completion**:
   - Update status to "complete"
   - List all deliverables
   - Confirm all tests passing
   - Note any issues or concerns

4. **Orchestrator validates**:
   - Verify deliverables exist
   - Review test results
   - Check integration contract compliance

### Wave Gate Protocol

**When all Wave N agents complete**:

1. **Orchestrator runs gate tests**:
   ```bash
   # Run wave-specific validation
   pytest tests/wave_N_gate/ -v
   ```

2. **Gate decision**:
   - **PASS**: Approve transition to Wave N+1
   - **FAIL**: Block Wave N+1, identify issues

3. **Notification**:
   - Update wave status file
   - Notify all agents of gate status
   - If failed: Identify blocking issues

---

## Integration Contract Compliance

### Contract Verification

Each agent must verify:

1. **Input contracts**: Prerequisites available
2. **Output contracts**: Deliverables match specification
3. **Interface contracts**: APIs match defined signatures
4. **Data contracts**: Data structures match schemas

### Compliance Checklist

Before marking wave complete:

- ☐ All input contracts read and understood
- ☐ All output contracts fulfilled
- ☐ Interface signatures match specification
- ☐ Data structures match schemas
- ☐ Error handling implemented per contract
- ☐ Documentation strings complete
- ☐ Tests validate contract compliance

---

## Conflict Prevention

### File Access Protocol

**Before modifying shared file**:

1. **Check ownership**: Verify you're authorized to modify
2. **Read current state**: Get latest version
3. **Identify modification region**: Know exact lines/methods
4. **Make targeted changes**: Minimize diff size
5. **Preserve existing functionality**: Don't break other code
6. **Run tests**: Verify no regressions

### Shared File Coordination

**For `docling_parser.py`** (modified by structure-agent and chunking-agent):

**structure-agent modifications**:
- Method: `_parse_with_docling()`
- Lines: Approximately 299-362 (pipeline options)
- Action: Update pipeline_options configuration

**chunking-agent modifications**:
- Method: `_chunk_document()` (new method)
- Lines: After existing methods (~420+)
- Action: Add new method

**Coordination**:
- structure-agent goes first (Wave 2)
- chunking-agent adds method after structure-agent complete
- Both agents coordinate on imports at top of file

### Merge Strategy

1. **Prefer new files**: Avoid modifying shared files when possible
2. **Minimize overlaps**: Different methods/sections
3. **Sequential modifications**: Wave separation reduces conflicts
4. **Clear boundaries**: Each agent owns specific methods

---

## Error Handling & Recovery

### Agent Failure Protocol

**If agent encounters blocking issue**:

1. **Update status immediately**:
   ```json
   {
     "status": "failed",
     "error": "Structure extraction fails on document X",
     "last_successful_task": "Heading extraction working",
     "blocked_by": "Unable to parse Docling table structure",
     "needs_help": true
   }
   ```

2. **Document issue**:
   - Exact error message
   - Steps to reproduce
   - Attempted solutions
   - Contract compliance concerns

3. **Notify orchestrator**:
   - Block wave progression
   - Request guidance
   - Provide debugging info

4. **Resolution**:
   - Orchestrator investigates
   - Contract clarification if needed
   - Agent fixes issue
   - Revalidate and continue

### Rollback Protocol

**If integration fails**:

1. **Identify problematic wave**:
   - Review test failures
   - Identify breaking changes
   - Determine responsible agent

2. **Rollback strategy**:
   - Revert changes from failed wave
   - Restore previous wave state
   - Re-run validation

3. **Fix and retry**:
   - Address root cause
   - Update implementation
   - Re-run wave with fixes

---

## Testing Coordination

### Test Execution Schedule

**Unit Tests**: Run after each deliverable
**Integration Tests**: Run after wave completion
**Gate Tests**: Run before wave transition
**System Tests**: Run after all waves complete

### Test Reporting Format

```json
{
  "test_suite": "unit_tests",
  "agent": "config-agent",
  "wave": 1,
  "total_tests": 5,
  "passed": 5,
  "failed": 0,
  "skipped": 0,
  "duration_seconds": 2.3,
  "timestamp": "2025-10-07T15:00:00Z",
  "failures": []
}
```

### Test Failure Handling

**If test fails**:

1. **Document failure**:
   - Test name
   - Failure message
   - Expected vs actual
   - Reproduction steps

2. **Investigate**:
   - Review implementation
   - Check contract compliance
   - Verify test correctness

3. **Fix**:
   - Correct implementation OR
   - Correct test if specification misunderstood

4. **Revalidate**:
   - Re-run failed test
   - Run related tests
   - Verify fix doesn't break others

---

## Status Tracking

### Wave Status Dashboard

**Location**: `.context-kit/orchestration/docling-enhanced-mode/status/wave-dashboard.json`

```json
{
  "current_wave": 2,
  "wave_status": {
    "wave_0": {
      "status": "complete",
      "completion_time": "2025-10-07T13:00:00Z"
    },
    "wave_1": {
      "status": "complete",
      "agents": {
        "config-agent": "complete",
        "metadata-agent": "complete"
      },
      "gate_tests": "passing",
      "completion_time": "2025-10-07T15:30:00Z"
    },
    "wave_2": {
      "status": "in_progress",
      "agents": {
        "structure-agent": "in_progress (75%)",
        "chunking-agent": "in_progress (60%)"
      },
      "start_time": "2025-10-07T16:00:00Z",
      "estimated_completion": "2025-10-07T18:00:00Z"
    }
  }
}
```

### Progress Visualization

```
Wave Progress
=============

Wave 0: Foundation ✓ Complete
Wave 1: Configuration & Schemas ✓ Complete
  ├─ config-agent ✓ Complete
  └─ metadata-agent ✓ Complete

Wave 2: Core Features [In Progress]
  ├─ structure-agent ▓▓▓▓▓▓▓░░░ 75%
  └─ chunking-agent  ▓▓▓▓▓▓░░░░ 60%

Wave 3: Integration [Pending]
Wave 4: Validation [Pending]
```

---

## Documentation Standards

### Code Documentation

**Docstrings Required For**:
- All public functions
- All classes
- All public methods
- Complex algorithms

**Format**:
```python
def extract_document_structure(
    doc: DoclingDocument,
    config: EnhancedModeConfig
) -> DocumentStructure:
    """
    Extract document structure from DoclingDocument.

    Extracts hierarchical headings, tables, pictures, and other structural
    elements according to the configuration. All elements are validated
    for size and consistency.

    Args:
        doc: Parsed DoclingDocument from Docling converter
        config: Enhanced mode configuration with feature flags

    Returns:
        DocumentStructure containing all extracted elements

    Raises:
        StructureExtractionError: If extraction fails or size limit exceeded
        ValidationError: If structure data is invalid

    Example:
        >>> config = EnhancedModeConfig()
        >>> structure = extract_document_structure(doc, config)
        >>> print(f"Found {len(structure.headings)} headings")
    """
```

### Integration Contract Updates

**If contract needs clarification**:

1. **Document ambiguity**: Note unclear specification
2. **Propose clarification**: Suggest specific wording
3. **Get approval**: Orchestrator reviews and approves
4. **Update contract**: Modify contract document
5. **Notify consumers**: All affected agents notified

---

## Meeting Points

### Synchronization Points

**Wave Gates**: All agents must synchronize
**Contract Reviews**: As needed for clarifications
**Integration Debugging**: If cross-agent issues arise

### Decision Making

**Agent-level decisions**: Agent makes independently
**Wave-level decisions**: Orchestrator decides
**Plan-level decisions**: Requires explicit approval

---

## Success Metrics

### Agent Performance

- **Delivery time**: On schedule with wave
- **Test pass rate**: 100% of assigned tests passing
- **Contract compliance**: Full compliance with all contracts
- **Code quality**: Passes linting, type checking
- **Documentation**: Complete docstrings and comments

### Wave Performance

- **Completion time**: Within estimated duration
- **Test pass rate**: All gate tests passing
- **Integration success**: No conflicts or breaks
- **Quality**: Meets all acceptance criteria

---

## Communication Examples

### Status Update (Progress)

```json
{
  "agent_id": "structure-agent",
  "wave": 2,
  "status": "in_progress",
  "progress": 0.6,
  "current_task": "Implementing picture extraction",
  "completed_tasks": [
    "DocumentStructure dataclass created",
    "Heading extraction implemented and tested",
    "Table extraction implemented and tested"
  ],
  "next_tasks": [
    "Complete picture extraction",
    "Add size validation",
    "Integration with docling_parser"
  ],
  "blockers": [],
  "estimated_completion": "2025-10-07T17:30:00Z"
}
```

### Status Update (Complete)

```json
{
  "agent_id": "structure-agent",
  "wave": 2,
  "status": "complete",
  "progress": 1.0,
  "deliverables": [
    "src/processing/structure_extractor.py (387 lines)",
    "src/processing/docling_parser.py (modified +67 lines)"
  ],
  "tests": {
    "unit": "7/7 passing",
    "integration": "3/3 passing"
  },
  "contract_compliance": {
    "STRUCT-001": "fulfilled",
    "CONFIG-001": "consumed"
  },
  "completion_time": "2025-10-07T17:45:00Z",
  "notes": "All features working, structure size averaging 15KB"
}
```

### Issue Report

```json
{
  "agent_id": "chunking-agent",
  "wave": 2,
  "issue_type": "blocker",
  "severity": "high",
  "description": "HybridChunker failing on documents without headings",
  "error_message": "AttributeError: 'NoneType' object has no attribute 'headings'",
  "reproduction_steps": [
    "Load simple_document.pdf (no headings)",
    "Call chunker.chunk_document()",
    "Error occurs in _extract_chunk_context()"
  ],
  "attempted_solutions": [
    "Added null check for meta.headings - partial success",
    "Need contract clarification on handling docs without structure"
  ],
  "needs": "Contract clarification: Should chunks without headings have empty context?",
  "blocking": "Cannot complete wave 2 until resolved"
}
```

---

**Coordination Protocol Version**: 1.0
**Last Updated**: 2025-10-07
