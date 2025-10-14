# Agent Assignments & Territorial Boundaries

**Purpose**: Define clear ownership to prevent merge conflicts and enable parallel execution

---

## Agent Roster

| Agent ID | Name | Wave | Territory | Role |
|----------|------|------|-----------|------|
| 1 | validation-core-agent | 1 | `src/processing/file_validator.py`, `test_file_validator.py` | Foundation builder |
| 2 | worker-analysis-agent | 1 | READ-ONLY analysis | Integration mapper |
| 3 | config-analysis-agent | 1 | READ-ONLY analysis | Integration mapper |
| 4 | webhook-worker-refactor-agent | 2 | `src/processing/worker_webhook.py` (lines 72-74, 207-210) | Worker integrator |
| 5 | legacy-worker-refactor-agent | 2 | `src/processing/worker.py` (lines 47-49, validation sites) | Worker integrator |
| 6 | config-refactor-agent | 3 | `src/config/processing_config.py` (lines 67-93) | Config integrator |
| 7 | webhook-worker-config-agent | 3 | `src/processing/worker_webhook.py` (lines 639-700) | Config integrator |
| 8 | legacy-worker-config-agent | 3 | `src/processing/worker.py` (startup section) | Config integrator |
| 9 | documentation-agent | 4 | NEW files in `docs/` or `.context-kit/_specs/` | Documentation writer |
| 10 | worker-decision-agent | 4 | READ-ONLY analysis + decision doc | Architect |
| 11 | debt-resolution-agent | 4 | `.context-kit/_specs/TECHNICAL_DEBT.md` | Tracker maintainer |

---

## Territorial Map

### File Ownership by Wave

#### Wave 1 (Foundation)
```
src/processing/
├── file_validator.py ← Agent 1 (CREATE)
├── test_file_validator.py ← Agent 1 (CREATE)
├── worker.py ← Agent 2 (READ ONLY)
├── worker_webhook.py ← Agent 2 (READ ONLY)

src/config/
└── processing_config.py ← Agent 3 (READ ONLY)

.context-kit/orchestration/tech-debt-resolution/integration-contracts/
├── file-validator-api.md ← Agent 1 (CREATE)
├── worker-integration-spec.md ← Agent 2 (CREATE)
└── config-integration-spec.md ← Agent 3 (CREATE)
```

**Conflict Risk**: ZERO (all new files or read-only)

---

#### Wave 2 (Worker Integration)
```
src/processing/
├── file_validator.py ← LOCKED (created in Wave 1)
├── worker_webhook.py ← Agent 4 (MODIFY lines 72-74, 207-210)
└── worker.py ← Agent 5 (MODIFY lines 47-49, validation sites)
```

**Conflict Risk**: ZERO (different files)

---

#### Wave 3 (Config Integration)
```
src/config/
└── processing_config.py ← Agent 6 (MODIFY lines 67-93)

src/processing/
├── worker_webhook.py ← Agent 7 (MODIFY lines 639-700, different from Wave 2)
└── worker.py ← Agent 8 (MODIFY startup section, different from Wave 2)
```

**Conflict Risk**: ZERO (different files + different line ranges)

**Line Range Protection**:
- Wave 2 modified validation logic (lines 72-74, 207-210)
- Wave 3 modifies startup/config (lines 639-700)
- No overlap

---

#### Wave 4 (Documentation & Cleanup)
```
docs/ (or .context-kit/_specs/)
├── CONFIGURATION.md ← Agent 9 (CREATE)
├── file-validator-usage.md ← Agent 9 (CREATE)
└── worker-architecture-decision.md ← Agent 10 (CREATE)

.context-kit/_specs/
└── TECHNICAL_DEBT.md ← Agent 11 (MODIFY resolved section)

src/processing/ ← Agent 10 (READ ONLY)
```

**Conflict Risk**: ZERO (all new files except TECHNICAL_DEBT.md owned by single agent)

---

## Agent Responsibilities

### Agent 1: validation-core-agent

**Expertise**: Python testing, validation logic, API design

**Mission**: Create bulletproof file validation module

**Deliverables**:
1. `src/processing/file_validator.py`
   - Implement all validation functions
   - Clear docstrings
   - Type hints
   - Proper error messages

2. `src/processing/test_file_validator.py`
   - 100% code coverage
   - Edge case testing
   - Environment variable testing
   - Integration examples

3. `integration-contracts/file-validator-api.md`
   - API documentation
   - Function signatures
   - Return value specifications
   - Usage examples

**Success Criteria**:
- All tests pass
- Coverage >95%
- No external dependencies
- API contract published

**Dependencies**: None (foundation)

---

### Agent 2: worker-analysis-agent

**Expertise**: Code analysis, pattern recognition, integration planning

**Mission**: Map all validation usage in workers to create integration blueprint

**Deliverables**:
1. `integration-contracts/worker-integration-spec.md`
   - List all validation call sites with line numbers
   - Current code patterns
   - Proposed replacement code
   - Error format preservation requirements
   - Integration test requirements

**Analysis Required**:
```python
# Find all patterns like:
- SUPPORTED_EXTENSIONS usage
- path.suffix validation
- Error response formats
- Configuration variable usage
```

**Success Criteria**:
- All validation sites documented
- Replacement patterns specified
- No validation logic missed

**Dependencies**: None (analysis)

---

### Agent 3: config-analysis-agent

**Expertise**: Configuration management, dependency analysis

**Mission**: Map ProcessingConfig integration opportunities

**Deliverables**:
1. `integration-contracts/config-integration-spec.md`
   - Current config variable usage in workers
   - ProcessingConfig attribute mapping
   - Initialization patterns
   - Migration approach
   - Backward compatibility notes

**Analysis Required**:
```python
# Document:
- Where configs are initialized
- What attributes are used
- How to integrate ProcessingConfig
- Startup sequence changes needed
```

**Success Criteria**:
- All config usage documented
- Integration path clear
- No breaking changes

**Dependencies**: None (analysis)

---

### Agent 4: webhook-worker-refactor-agent

**Expertise**: FastAPI, webhook patterns, refactoring

**Mission**: Integrate file_validator into production webhook worker

**Territory**: `src/processing/worker_webhook.py`
**Lines Modified**: 72-74, 207-210

**Tasks**:
1. Import file_validator functions
2. Remove duplicate SUPPORTED_EXTENSIONS logic
3. Update validation call sites
4. Preserve error response format
5. Add integration test
6. Verify startup works

**Code Changes**:
```python
# Lines 72-74: Remove, replace with import
from .file_validator import get_supported_extensions, validate_file_type

# Line 207-210: Replace validation
valid, error = validate_file_type(str(path))
if not valid:
    return {"status": "skipped", "error": error}
```

**Success Criteria**:
- Worker starts successfully
- Validation behavior identical
- Error format unchanged
- Tests pass

**Dependencies**: Wave 1 complete (file_validator exists)

---

### Agent 5: legacy-worker-refactor-agent

**Expertise**: Watchdog patterns, file system events

**Mission**: Integrate file_validator into legacy worker

**Territory**: `src/processing/worker.py`
**Lines Modified**: 47-49, validation call sites

**Tasks**: Same as Agent 4, but for worker.py

**Success Criteria**: Same as Agent 4

**Dependencies**: Wave 1 complete (file_validator exists)

---

### Agent 6: config-refactor-agent

**Expertise**: Configuration architecture, API design

**Mission**: Make ProcessingConfig use file_validator

**Territory**: `src/config/processing_config.py`
**Lines Modified**: 67-93

**Tasks**:
1. Import file_validator
2. Refactor validate_file() to delegate
3. Maintain API signature
4. Update tests
5. Document changes

**Code Changes**:
```python
def validate_file(self, filename: str, size_bytes: int) -> Tuple[bool, str]:
    from ..processing.file_validator import validate_file as validator
    return validator(filename, size_bytes, self.max_file_size_mb)
```

**Success Criteria**:
- ProcessingConfig tests pass
- API unchanged
- Delegates to file_validator

**Dependencies**: Wave 1 complete (file_validator exists)

---

### Agent 7: webhook-worker-config-agent

**Expertise**: FastAPI, dependency injection, configuration

**Mission**: Make webhook worker use ProcessingConfig

**Territory**: `src/processing/worker_webhook.py`
**Lines Modified**: 639-700 (startup_event function)

**Tasks**:
1. Import ProcessingConfig
2. Initialize in startup
3. Remove module-level config vars
4. Use config instance
5. Store in app.state for access

**Code Changes**:
```python
@app.on_event("startup")
async def startup_event():
    from src.config.processing_config import ProcessingConfig

    config = ProcessingConfig()
    app.state.config = config

    logger.info(f"Supported formats: {config.supported_formats}")
```

**Success Criteria**:
- Worker uses ProcessingConfig
- Configuration loaded correctly
- No module-level duplication

**Dependencies**:
- Wave 2 complete (file_validator integrated)
- Agent 6 complete (ProcessingConfig uses file_validator)

---

### Agent 8: legacy-worker-config-agent

**Expertise**: Configuration patterns

**Mission**: Make legacy worker use ProcessingConfig

**Territory**: `src/processing/worker.py` (startup section)

**Tasks**: Same as Agent 7, but for worker.py

**Success Criteria**: Same as Agent 7

**Dependencies**: Same as Agent 7

---

### Agent 9: documentation-agent

**Expertise**: Technical writing, API documentation

**Mission**: Create comprehensive configuration and usage documentation

**Territory**: NEW files in `docs/` or `.context-kit/_specs/`

**Deliverables**:
1. `CONFIGURATION.md` - Complete config guide
2. `file-validator-usage.md` - Usage examples
3. Updates to README if needed
4. Migration guide if necessary

**Content Required**:
```markdown
# CONFIGURATION.md
- All environment variables
- Defaults and valid values
- Examples
- ProcessingConfig API
- file_validator API
- Migration from old patterns
```

**Success Criteria**:
- All config options documented
- Clear examples
- Migration path clear

**Dependencies**: Wave 3 complete (all code changes done)

---

### Agent 10: worker-decision-agent

**Expertise**: Architecture, git analysis, decision-making

**Mission**: Determine fate of legacy worker.py

**Territory**: READ-ONLY analysis, creates decision document

**Tasks**:
1. Check git history (recent changes to worker.py)
2. Search for worker.py usage in scripts
3. Check Docker configs
4. Analyze if watchdog mode is needed
5. Make recommendation: deprecate OR document
6. Create action plan

**Deliverables**:
1. `worker-architecture-decision.md`
   - Analysis findings
   - Recommendation with justification
   - Action plan
   - Migration guide if deprecating

**Decision Tree**:
```
if worker.py unused for 6+ months:
    recommend: deprecate
    action: move to legacy/, add notice
else:
    recommend: document_modes
    action: create comparison doc
```

**Success Criteria**:
- Clear recommendation
- Justification provided
- Action plan specified

**Dependencies**: Wave 3 complete (both workers working)

---

### Agent 11: debt-resolution-agent

**Expertise**: Project management, documentation

**Mission**: Update technical debt tracker with resolutions

**Territory**: `.context-kit/_specs/TECHNICAL_DEBT.md`

**Tasks**:
1. Move items #1 and #3 to "Resolved" section
2. Add resolution dates
3. Link to commits/PRs
4. Document solution approach
5. Update remaining items if priorities changed

**Format**:
```markdown
## Resolved

### 1. Duplicate Format Validation Logic
**Resolved**: 2025-10-13
**Solution**: Created file_validator module...
**Commits**: [hash1, hash2]
**Files**: [list]
```

**Success Criteria**:
- Resolved items documented
- Commit references added
- Clear resolution notes

**Dependencies**: All waves complete

---

## Communication Protocol

### Status Updates
Each agent must create status file after completion:

**Location**: `.context-kit/orchestration/tech-debt-resolution/status/{agent-name}.yml`

**Format**:
```yaml
agent: validation-core-agent
wave: 1
status: complete  # queued | in_progress | complete | failed
started: 2025-10-13T22:00:00Z
completed: 2025-10-13T23:30:00Z
deliverables:
  - path: src/processing/file_validator.py
    status: complete
    tests_passing: true
  - path: src/processing/test_file_validator.py
    status: complete
    coverage: 98%
  - path: integration-contracts/file-validator-api.md
    status: complete
integration_validated: true
notes: "All tests pass, API contract published"
blockers: []
```

### Pre-flight Checks
Before starting, agents must verify:
```bash
# Check wave dependencies
cat .context-kit/orchestration/tech-debt-resolution/status/*.yml | grep "wave: [previous_wave]" | grep "status: complete"

# Verify required contracts exist
test -f integration-contracts/file-validator-api.md

# Run prerequisite tests
pytest <dependency-path>
```

### Failure Protocol
If agent fails:
1. Update status file with failure reason
2. Document blocker
3. Notify about blocked dependencies
4. Provide rollback instructions

---

## Handoff Specifications

### Wave 1 → Wave 2
**Deliverables Required**:
- ✅ `src/processing/file_validator.py` with tests passing
- ✅ `integration-contracts/file-validator-api.md` published
- ✅ `integration-contracts/worker-integration-spec.md` published

**Verification**:
```bash
pytest src/processing/test_file_validator.py -v
test -f integration-contracts/file-validator-api.md
test -f integration-contracts/worker-integration-spec.md
```

### Wave 2 → Wave 3
**Deliverables Required**:
- ✅ Both workers refactored
- ✅ Both workers start successfully
- ✅ Validation tests pass

**Verification**:
```bash
python -c "from src.processing.file_validator import get_supported_extensions; print(get_supported_extensions())"
./scripts/start-all.sh --docker-only
curl http://localhost:8002/health
```

### Wave 3 → Wave 4
**Deliverables Required**:
- ✅ ProcessingConfig refactored
- ✅ Workers use ProcessingConfig
- ✅ All tests pass

**Verification**:
```bash
pytest src/ -v
./scripts/start-all.sh
./scripts/status.sh
```

---

## Territory Boundaries Summary

| File | Wave 1 | Wave 2 | Wave 3 | Wave 4 |
|------|--------|--------|--------|--------|
| `file_validator.py` | Agent 1 CREATE | LOCKED | LOCKED | LOCKED |
| `test_file_validator.py` | Agent 1 CREATE | LOCKED | LOCKED | LOCKED |
| `worker_webhook.py` | Agent 2 READ | Agent 4 MODIFY | Agent 7 MODIFY | LOCKED |
| `worker.py` | Agent 2 READ | Agent 5 MODIFY | Agent 8 MODIFY | LOCKED |
| `processing_config.py` | Agent 3 READ | LOCKED | Agent 6 MODIFY | LOCKED |
| `TECHNICAL_DEBT.md` | - | - | - | Agent 11 MODIFY |
| Integration contracts | Agents 1,2,3 CREATE | LOCKED | LOCKED | LOCKED |
| Documentation | - | - | - | Agent 9 CREATE |

**Key**: CREATE (new file), MODIFY (edit existing), READ (analysis only), LOCKED (no changes)

---

## Conflict Resolution

Despite careful territorial boundaries, if conflicts occur:

1. **Detection**: Git merge conflict during integration
2. **Resolution Owner**: Agent with later wave number yields
3. **Rollback**: Later agent rolls back, waits for earlier agent completion
4. **Retry**: After earlier agent completes, later agent retries

**Example**:
- If Agent 7 (Wave 3) conflicts with Agent 4 (Wave 2)
- Agent 7 rolls back
- Agent 4 completes
- Agent 7 rebases and retries

**Prevention**: This should never happen with proper territorial boundaries!

---

## Resource Requirements

| Wave | Concurrent Agents | Memory | CPU |
|------|------------------|---------|-----|
| 1 | 3 | Low (analysis) | Low |
| 2 | 2 | Medium (worker tests) | Medium |
| 3 | 3 | Medium (integration) | Medium |
| 4 | 3 | Low (documentation) | Low |

**Total Parallelism**: Up to 3 concurrent agents per wave
**Sequential Equivalent**: 11 agents
**Time Savings**: ~54% reduction
