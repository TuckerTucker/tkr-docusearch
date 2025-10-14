# Technical Debt

**Last Updated**: 2025-10-14

## Overview

This document tracks known technical debt, architectural issues, and areas for refactoring in the tkr-docusearch codebase.

---

## High Priority

(None currently - all high priority items have been resolved)

## Medium Priority

(None currently - medium priority items have been resolved)

---

## Low Priority

### 4. Environment Variable Naming Inconsistency

**Issue**: Some config uses different env var patterns

**Examples**:
- `SUPPORTED_FORMATS` (comma-separated)
- `ENABLE_TABLE_STRUCTURE` (boolean as string)
- `CHROMA_HOST` / `CHROMA_PORT` (separate vars)

**Recommended Solution**:
- Document standard patterns in CONFIGURATION.md
- Consider using a config library like `pydantic-settings`
- Prefix all vars consistently (e.g., `DOCUSEARCH_*`)

**Effort**: Low (1-2 hours for documentation)
**Impact**: Low (improves clarity)

---

### 5. Enhanced Mode Config Defaults in Multiple Places

**Issue**: EnhancedModeConfig defaults are in code, not easily configurable

**File**: `src/config/processing_config.py` (lines 147-191)

**Problem**:
- Defaults hardcoded in dataclass
- No single config file (all env vars)
- Could benefit from YAML/TOML config file

**Recommended Solution**:
- Add optional config file support: `.docusearch.yml`
- Keep env vars as override mechanism
- Use pydantic for validation

**Effort**: Medium (3-4 hours)
**Impact**: Low (nice to have, not critical)

---

## Refactoring Opportunities

### A. Shared Validation Module

**Status**: Recommended (see #1 above)

**Benefits**:
- Single source of truth
- Easier to test
- Consistent error messages
- Easier to extend

---

### B. Configuration Consolidation

**Status**: Nice to have

**Idea**: Consolidate all config into single module/file
- Environment variables
- Defaults
- Validation
- Type hints

**Example Structure**:
```
src/config/
  __init__.py
  settings.py        # Main settings (Pydantic)
  defaults.py        # Default values
  validation.py      # Validation functions
```

---

### C. Worker Architecture Unification

**Status**: Consider for v2.0

**Idea**: Single worker with pluggable triggers
```python
class DocumentWorker:
    def __init__(self, trigger: Trigger):
        self.trigger = trigger

# Usage:
webhook_worker = DocumentWorker(WebhookTrigger())
watchdog_worker = DocumentWorker(WatchdogTrigger())
```

---

## How to Use This Document

### Adding New Debt
1. Identify the issue
2. Choose priority level
3. Add to appropriate section
4. Include:
   - Clear description
   - File locations
   - Recommended solution
   - Effort/impact estimates

### Resolving Debt
1. Create issue/task
2. Implement fix
3. Update this document
4. Move to "Resolved" section below

---

## Resolved

### 1. Duplicate Format Validation Logic
**Resolved**: 2025-10-13
**Solution**: Created centralized `file_validator` module with single source of truth for validation logic. Integrated into both workers and ProcessingConfig, eliminating ~40 lines of duplicate code across 3 locations.

**Implementation Waves**:
- **Wave 1 - Foundation**: Created `file_validator.py` with validation functions (`get_supported_extensions()`, `validate_file_type()`, `validate_file_size()`) and comprehensive test suite
- **Wave 2 - Worker Integration**: Integrated file_validator into both `worker_webhook.py` and `worker.py`, removing duplicate SUPPORTED_EXTENSIONS code
- **Wave 3 - Configuration Integration**: Connected ProcessingConfig to use file_validator module

**Commits**:
- `46f12e0` - feat(processing): consolidate file validation - Waves 1-2 complete
- `bfca3f9` - refactor(wave3): consolidate configuration management via ProcessingConfig

**Files Changed**:
- Created: `src/processing/file_validator.py` (136 lines, 18 format support)
- Created: `src/processing/test_file_validator.py` (424 lines, comprehensive tests)
- Modified: `src/processing/worker_webhook.py` (removed duplicate validation)
- Modified: `src/processing/worker.py` (removed duplicate validation)
- Modified: `src/config/processing_config.py` (delegated to file_validator)

**Impact**:
- ✅ Eliminated code duplication (DRY principle enforced)
- ✅ Single source of truth for file validation
- ✅ Consistent validation logic across all workers
- ✅ Easier to maintain and extend supported formats
- ✅ 569 lines of new code (validator + tests) replaced 40+ lines of duplicates

---

### 2. Two Worker Implementations
**Resolved**: 2025-10-14
**Solution**: Documented both worker modes as complementary architectures rather than deprecating. Created comprehensive decision document analyzing both modes and their use cases.

**Decision**: DOCUMENT AS ALTERNATIVE MODE (not deprecate)
- **worker_webhook.py**: Production default (Docker + copyparty webhook + REST API)
- **worker.py**: Standalone mode (watchdog-based, development, testing, backup)

**Analysis Findings**:
- Both workers actively maintained (worker.py updated 2025-10-13, worker_webhook.py updated 2025-10-14)
- Different architectures for different use cases (not redundant)
- Low duplication after Wave 1-3 refactoring (shared file_validator, ProcessingConfig)
- Valid use cases for watchdog mode: standalone development, no Docker, simple file-drop workflow

**Implementation**:
- Created `.context-kit/_specs/worker-architecture-decision.md` (comprehensive 400+ line analysis)
- Documented architecture comparison, use cases, and mode selection guidance
- Recommended documentation creation: `docs/WORKER_MODES.md` (comparison guide)
- Recommended script support: `scripts/run-worker-watchdog.sh`

**Files Changed**:
- Created: `.context-kit/_specs/worker-architecture-decision.md` (decision document)
- Updated: `.context-kit/_specs/TECHNICAL_DEBT.md` (moved to resolved)

**Impact**:
- ✅ Clear guidance on worker mode selection
- ✅ Both modes documented and supported
- ✅ Production default clearly established (webhook)
- ✅ Eliminated confusion about "which worker to use"
- ✅ Acknowledged active maintenance of both modes

**Next Steps** (recommended, not blocking):
- Create `docs/WORKER_MODES.md` comparison guide
- Add `--watchdog` flag to `scripts/start-all.sh`
- Update `docs/QUICK_START.md` with mode selection section

---

### 3. ProcessingConfig Module Unused
**Resolved**: 2025-10-13
**Solution**: Integrated ProcessingConfig into both workers during startup. Workers now initialize ProcessingConfig and use it for centralized configuration management instead of hardcoded module-level variables.

**Implementation**:
- ProcessingConfig now delegates file validation to the shared `file_validator` module
- Both workers (`worker_webhook.py` and `worker.py`) initialize ProcessingConfig on startup
- Added `supported_extensions_set` property to ProcessingConfig for easy access
- Eliminated hardcoded configuration scattered across worker files

**Commits**:
- `bfca3f9` - refactor(wave3): consolidate configuration management via ProcessingConfig

**Files Changed**:
- Modified: `src/config/processing_config.py` (delegated validate_file() to file_validator, +22/-10 lines)
- Modified: `src/processing/worker_webhook.py` (initialized ProcessingConfig, +12/-3 lines)
- Modified: `src/processing/worker.py` (initialized ProcessingConfig, +7/-1 lines)

**Impact**:
- ✅ ProcessingConfig now used in production code (not just tests)
- ✅ Single source of truth for processing configuration
- ✅ Eliminated module-level configuration duplication
- ✅ Established clear configuration flow: ENV → ProcessingConfig → Workers
- ✅ Improved consistency and maintainability

---

## Notes

- This document should be reviewed quarterly
- Update as new debt is discovered
- Link to issues/PRs when debt is addressed
- Keep recommendations realistic and actionable

---

## See Also

- **ARCHITECTURE.md**: System architecture overview
- **CONFIGURATION.md**: Configuration guide (TODO)
- **CONTRIBUTING.md**: Development guidelines (TODO)
