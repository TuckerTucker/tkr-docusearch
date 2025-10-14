# Technical Debt Resolution - Orchestration Plan

**Goal**: Eliminate duplicate validation code, consolidate configuration, and establish clear architecture patterns

**Strategy**: 4-wave parallel execution with interface-first development and progressive validation

**Max Agents**: 6 concurrent agents
**Estimated Duration**: 4 synchronization gates
**Success Metric**: Zero duplicate code, single source of truth for validation and configuration

---

## Wave 1: Foundation & Specification (Parallel Foundation)

**Objective**: Create shared validation module and comprehensive specifications before any refactoring

**Duration**: 1 sync gate
**Agents**: 3 parallel

### Agent 1: validation-core-agent
**Territory**: `src/processing/file_validator.py`, `src/processing/test_file_validator.py`
**Deliverables**:
- Create file_validator.py with validation functions
- Implement comprehensive test suite (100% coverage)
- Document API contract in integration-contracts/
- Export: `get_supported_extensions()`, `validate_file()`, `validate_file_type()`, `validate_file_size()`

**Contract Exports**:
```python
# Public API
def get_supported_extensions() -> Set[str]
def validate_file_type(file_path: str) -> Tuple[bool, str]
def validate_file_size(size_bytes: int, max_mb: int = 100) -> Tuple[bool, str]
def validate_file(file_path: str, size_bytes: int, max_mb: int = 100) -> Tuple[bool, str]

# Constants
DEFAULT_FORMATS: str
```

**Validation Gate**:
- All tests pass with 100% coverage
- API contract documented
- No dependencies on existing workers

---

### Agent 2: worker-analysis-agent
**Territory**: Analysis output only (read-only on workers)
**Deliverables**:
- Analyze worker.py and worker_webhook.py usage patterns
- Document all validation call sites
- Identify configuration variables used
- Map integration points to file_validator API
- Output: `integration-contracts/worker-integration-spec.md`

**Contract Exports**:
```yaml
worker_validation_patterns:
  - location: "worker_webhook.py:207"
    current_code: "if path.suffix.lower() not in SUPPORTED_EXTENSIONS"
    replacement: "validate_file_type(str(path))"
    error_format: '{"status": "skipped", "error": "..."}'

  - location: "worker.py:XXX"
    # ... similar mappings
```

**Validation Gate**:
- All validation call sites documented
- Replacement patterns specified
- Error response formats preserved

---

### Agent 3: config-analysis-agent
**Territory**: Analysis output only (read-only on config)
**Deliverables**:
- Analyze ProcessingConfig.validate_file() implementation
- Document config initialization patterns in workers
- Map configuration variables to ProcessingConfig attributes
- Identify integration opportunities
- Output: `integration-contracts/config-integration-spec.md`

**Contract Exports**:
```yaml
config_integration_points:
  worker_webhook:
    current_vars:
      - SUPPORTED_FORMATS (line 73)
      - MAX_FILE_SIZE_MB (implicit, default 100)
    replacement_pattern: |
      config = ProcessingConfig()
      SUPPORTED_EXTENSIONS = {f".{fmt}" for fmt in config.supported_formats}

  worker:
    # ... similar mapping
```

**Validation Gate**:
- All config usage documented
- Migration path specified
- Backward compatibility verified

---

**Wave 1 Synchronization Gate**:
- ✅ file_validator module complete with tests
- ✅ Worker integration patterns documented
- ✅ Config integration patterns documented
- ✅ All contracts published to integration-contracts/
- ✅ No merge conflicts (new files only)

---

## Wave 2: Worker Integration (Parallel Refactoring)

**Objective**: Integrate file_validator into both workers simultaneously

**Duration**: 1 sync gate
**Agents**: 2 parallel

### Agent 4: webhook-worker-refactor-agent
**Territory**: `src/processing/worker_webhook.py` (lines 72-74, 207-210)
**Dependencies**: Wave 1 complete
**Deliverables**:
- Import file_validator
- Replace SUPPORTED_EXTENSIONS with get_supported_extensions()
- Update validation call sites using integration spec
- Preserve error response format exactly
- Add integration test

**Integration Contract**: Uses `worker-integration-spec.md`

**Before**:
```python
# Line 73
_formats_str = os.getenv("SUPPORTED_FORMATS", "...")
SUPPORTED_EXTENSIONS = {f".{fmt.strip().lower()}" for fmt in _formats_str.split(",")}

# Line 207
if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
    return {"status": "skipped", "error": f"Unsupported file type: {path.suffix}"}
```

**After**:
```python
# Line 73
from .file_validator import get_supported_extensions, validate_file_type

# Remove _formats_str and SUPPORTED_EXTENSIONS

# Line 207
valid, error = validate_file_type(str(path))
if not valid:
    return {"status": "skipped", "error": error}
```

**Validation Gate**:
- Worker starts successfully
- File validation works identically
- Error messages match original format
- No behavior changes

---

### Agent 5: legacy-worker-refactor-agent
**Territory**: `src/processing/worker.py` (lines 47-49, validation call sites)
**Dependencies**: Wave 1 complete
**Deliverables**:
- Same changes as webhook-worker-refactor-agent
- Apply to worker.py instead
- Preserve existing behavior
- Add integration test

**Integration Contract**: Uses `worker-integration-spec.md`

**Validation Gate**:
- Worker starts successfully
- File validation works identically
- No behavior changes

---

**Wave 2 Synchronization Gate**:
- ✅ Both workers refactored
- ✅ All tests pass
- ✅ Validation behavior unchanged
- ✅ No duplicate validation code in workers
- ✅ file_validator is single source of truth

---

## Wave 3: Configuration Integration (Parallel Consolidation)

**Objective**: Integrate ProcessingConfig into workers and update it to use file_validator

**Duration**: 1 sync gate
**Agents**: 3 parallel

### Agent 6: config-refactor-agent
**Territory**: `src/config/processing_config.py` (lines 67-93)
**Dependencies**: Wave 1 complete
**Deliverables**:
- Import file_validator
- Replace validate_file() implementation to delegate to file_validator
- Maintain same API signature for backward compatibility
- Update __post_init__ to use file_validator constants
- Add tests

**Before**:
```python
def validate_file(self, filename: str, size_bytes: int) -> Tuple[bool, str]:
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    if ext not in self.supported_formats:
        return False, f"Unsupported format: {ext}..."
    # ... size validation
```

**After**:
```python
def validate_file(self, filename: str, size_bytes: int) -> Tuple[bool, str]:
    from .file_validator import validate_file as validator
    return validator(filename, size_bytes, self.max_file_size_mb)
```

**Validation Gate**:
- ProcessingConfig tests pass
- API contract unchanged
- Delegates to file_validator

---

### Agent 7: webhook-worker-config-agent
**Territory**: `src/processing/worker_webhook.py` (startup section lines 639-700)
**Dependencies**: Wave 2 complete, config-refactor-agent complete
**Deliverables**:
- Import ProcessingConfig
- Initialize in startup_event()
- Replace module-level config variables with config instance
- Use config.validate_file() for validation
- Use config.supported_formats for logging

**Integration Contract**: Uses `config-integration-spec.md`

**Before**:
```python
# Module level
_formats_str = os.getenv("SUPPORTED_FORMATS", "...")
MAX_FILE_SIZE_MB = 100  # implicit

# In startup
logger.info(f"  Supported Extensions: {SUPPORTED_EXTENSIONS}")
```

**After**:
```python
# Remove module-level config

# In startup
from src.config.processing_config import ProcessingConfig
config = ProcessingConfig()
logger.info(f"  Supported Extensions: {config.supported_formats}")

# Store config as global
app.state.config = config
```

**Validation Gate**:
- Worker starts with ProcessingConfig
- Configuration loaded correctly
- Validation uses config instance

---

### Agent 8: legacy-worker-config-agent
**Territory**: `src/processing/worker.py` (startup section)
**Dependencies**: Wave 2 complete, config-refactor-agent complete
**Deliverables**:
- Same integration as webhook-worker-config-agent
- Apply to worker.py
- Use ProcessingConfig in startup

**Integration Contract**: Uses `config-integration-spec.md`

**Validation Gate**:
- Worker starts with ProcessingConfig
- Configuration loaded correctly

---

**Wave 3 Synchronization Gate**:
- ✅ ProcessingConfig uses file_validator
- ✅ Both workers use ProcessingConfig
- ✅ No module-level config duplication
- ✅ Single source of truth: ProcessingConfig → file_validator
- ✅ All tests pass

---

## Wave 4: Documentation & Cleanup (Parallel Finalization)

**Objective**: Document architecture, update technical debt tracker, decide worker fate

**Duration**: 1 sync gate
**Agents**: 3 parallel

### Agent 9: documentation-agent
**Territory**: New files in `docs/` or `.context-kit/_specs/`
**Dependencies**: Wave 3 complete
**Deliverables**:
- Create CONFIGURATION.md documenting all env vars
- Document file_validator API and usage
- Document ProcessingConfig integration
- Update README with configuration examples
- Add migration guide if needed

**Template**:
```markdown
# Configuration Guide

## Environment Variables
- SUPPORTED_FORMATS: Comma-separated file extensions
- MAX_FILE_SIZE_MB: Maximum file size (default: 100)
...

## File Validation
All validation goes through `file_validator` module...

## ProcessingConfig
Workers use ProcessingConfig for all settings...
```

**Validation Gate**:
- Comprehensive configuration documentation
- Clear usage examples
- Migration path documented

---

### Agent 10: worker-decision-agent
**Territory**: Analysis and recommendation only
**Dependencies**: Wave 3 complete
**Deliverables**:
- Investigate worker.py actual usage (scripts, docker, docs)
- Check git history for recent worker.py changes
- Recommend: deprecate OR document dual modes
- If deprecate: create deprecation notice and migration guide
- If keep: document when to use each worker type
- Output: `worker-architecture-decision.md`

**Decision Framework**:
```yaml
if worker.py unused in last 6 months AND no watchdog references:
  recommendation: deprecate
  actions:
    - Move to src/processing/legacy/
    - Add deprecation notice
    - Update docs to reference webhook only
else:
  recommendation: document_modes
  actions:
    - Create worker comparison table
    - Document webhook vs watchdog use cases
    - Add startup examples for both
```

**Validation Gate**:
- Clear recommendation with justification
- Action plan specified
- Migration path if deprecating

---

### Agent 11: debt-resolution-agent
**Territory**: `.context-kit/_specs/TECHNICAL_DEBT.md`
**Dependencies**: All waves complete
**Deliverables**:
- Update TECHNICAL_DEBT.md
- Move resolved items (1, 3) to "Resolved" section
- Add resolution notes with PR/commit references
- Update remaining items if priority changed
- Add date of resolution

**Before**:
```markdown
## High Priority
### 1. Duplicate Format Validation Logic
**Status**: Open
...

## Medium Priority
### 3. ProcessingConfig Unused in Production
**Status**: Open
```

**After**:
```markdown
## Resolved
### 1. Duplicate Format Validation Logic
**Resolved**: 2025-10-13
**Solution**: Created file_validator module used by all components
**Files Changed**: [list]
**Commits**: [hashes]

### 3. ProcessingConfig Unused in Production
**Resolved**: 2025-10-13
**Solution**: Integrated into both workers during startup
```

**Validation Gate**:
- Technical debt document updated
- Resolved items documented
- Commit references added

---

**Wave 4 Synchronization Gate**:
- ✅ Configuration fully documented
- ✅ Worker architecture decision made and documented
- ✅ Technical debt tracker updated
- ✅ All documentation in place
- ✅ Project ready for next features

---

## Integration Testing Strategy

### After Wave 1
```bash
# Validate file_validator independently
pytest src/processing/test_file_validator.py -v --cov=src/processing/file_validator
```

### After Wave 2
```bash
# Validate workers with new validation
./scripts/start-all.sh --docker-only  # Start services only
python -m pytest src/processing/test_worker_validation.py

# Manual test: Upload various file types
curl -X POST http://localhost:8002/process -d '{"file_path": "/uploads/test.png", "filename": "test.png"}'
curl -X POST http://localhost:8002/process -d '{"file_path": "/uploads/test.xyz", "filename": "test.xyz"}'  # Should fail
```

### After Wave 3
```bash
# Validate full integration
./scripts/stop-all.sh
./scripts/start-all.sh

# Check logs for config initialization
tail -f logs/worker-native.log | grep -i "config\|supported"

# Full system test
# Upload files, verify processing works identically
```

### After Wave 4
```bash
# Final validation
pytest src/ -v --cov=src/
./scripts/status.sh
# Review all documentation
```

---

## Conflict Prevention Matrix

| Wave | Agent | Files Modified | Potential Conflicts | Prevention Strategy |
|------|-------|---------------|-------------------|-------------------|
| 1 | validation-core | NEW files only | None | New file creation |
| 1 | worker-analysis | READ only | None | Analysis only |
| 1 | config-analysis | READ only | None | Analysis only |
| 2 | webhook-refactor | worker_webhook.py | Low (different agent than Wave 3) | Territorial ownership |
| 2 | legacy-refactor | worker.py | None | Different file |
| 3 | config-refactor | processing_config.py | None | Different file from workers |
| 3 | webhook-config | worker_webhook.py | None | Different lines than Wave 2 |
| 3 | legacy-config | worker.py | None | Different lines than Wave 2 |
| 4 | documentation | NEW files only | None | New file creation |
| 4 | worker-decision | READ/ANALYSIS | None | Analysis only |
| 4 | debt-resolution | TECHNICAL_DEBT.md | None | Single agent owns this file |

**Conflict Risk**: ZERO
**Reason**: Territorial ownership + progressive refactoring of different sections

---

## Rollback Procedures

### Wave 1 Rollback
```bash
# Remove new files
rm src/processing/file_validator.py
rm src/processing/test_file_validator.py
# No impact on existing system
```

### Wave 2 Rollback
```bash
# Revert workers
git revert <wave-2-commits>
# System returns to Wave 1 state (file_validator present but unused)
```

### Wave 3 Rollback
```bash
# Revert config and worker changes
git revert <wave-3-commits>
# System returns to Wave 2 state (workers use file_validator directly)
```

### Wave 4 Rollback
```bash
# Only documentation changes, no code impact
# Can keep or revert as needed
```

---

## Success Metrics

### Code Quality
- ✅ Zero duplicate validation code
- ✅ Single source of truth (file_validator)
- ✅ ProcessingConfig actively used
- ✅ Test coverage >95% for validation code

### Architecture
- ✅ Clear separation of concerns
- ✅ Consistent configuration patterns
- ✅ Worker architecture clarified

### Documentation
- ✅ Configuration fully documented
- ✅ API contracts clear
- ✅ Migration guides present
- ✅ Technical debt resolved

### Operational
- ✅ No behavior changes (pure refactoring)
- ✅ All tests pass
- ✅ System runs identically
- ✅ Zero downtime

---

## Agent Handoff Protocol

### Status Broadcasting
Each agent must update status file after completion:

```yaml
# .context-kit/orchestration/tech-debt-resolution/status/{agent-name}.yml
agent: validation-core-agent
wave: 1
status: complete  # queued | in_progress | complete | failed
deliverables:
  - src/processing/file_validator.py
  - src/processing/test_file_validator.py
  - integration-contracts/file-validator-api.md
tests_passing: true
integration_validated: true
timestamp: 2025-10-13T23:00:00Z
notes: "All tests pass with 100% coverage"
```

### Contract Publishing
Contracts must be published before dependent waves:

```bash
.context-kit/orchestration/tech-debt-resolution/integration-contracts/
├── file-validator-api.md          (Wave 1, Agent 1)
├── worker-integration-spec.md     (Wave 1, Agent 2)
├── config-integration-spec.md     (Wave 1, Agent 3)
└── worker-architecture-decision.md (Wave 4, Agent 10)
```

### Dependency Verification
Before starting, each agent must verify:
1. Prerequisites complete (check status files)
2. Required contracts exist
3. Tests for dependencies passing

---

## Timeline Estimate

| Wave | Agents | Duration | Total Time |
|------|--------|----------|------------|
| Wave 1 | 3 parallel | 1.5 hours each | 1.5 hours |
| Wave 2 | 2 parallel | 1 hour each | 1 hour |
| Wave 3 | 3 parallel | 1.5 hours each | 1.5 hours |
| Wave 4 | 3 parallel | 1 hour each | 1 hour |
| **Total** | | | **~5 hours** |

With sequential execution: ~11 hours
**Parallelism Gain**: 54% faster

---

## Next Steps

1. Review and approve orchestration plan
2. Create integration contract templates
3. Generate agent-specific task files
4. Execute Wave 1 with 3 parallel agents
5. Gate validation and proceed to Wave 2

**Ready to begin orchestration?** All specifications are in place for zero-conflict parallel execution.
