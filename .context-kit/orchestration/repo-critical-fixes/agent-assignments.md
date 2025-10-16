# Agent Assignments & Territorial Ownership

This document defines clear territorial boundaries for each agent to prevent merge conflicts and ensure clean parallel execution.

## Territorial Ownership Model

Each agent has exclusive write access to specific files and directories. No two agents may modify the same file within the same wave.

---

## Agent 1: security-fixer-agent

### Primary Territory
- `src/api/server.py` (CORS fixes)
- `src/processing/worker_webhook.py` (CORS fixes)
- `src/storage/chroma_client.py` (eval() replacement)
- `docker/slide_renderer_api.py` (path validation)
- `docker/.env` (password security)
- `src/embeddings/model_loader.py` (bare except fix)

### New Files Created
- `docker/.env.example` (template)

### Read-Only Access
- Test files for validation

### Wave Assignments
- **Wave 1:** Security vulnerability fixes (all tasks)

### Success Metrics
- Zero critical/high security findings in bandit scan
- All security tests passing
- CVSS scores reduced to acceptable levels

---

## Agent 2: test-infrastructure-agent

### Primary Territory
- `pytest.ini` (configuration)
- `conftest.py` (test setup)
- `tests/` (all test files, can create new ones)

### New Files Created
- `tests/search/test_validate_search.py`
- `tests/storage/test_markdown_utils.py`
- `tests/processing/test_strategies.py` (Wave 2)
- `tests/processing/test_handlers.py` (Wave 2)
- `tests/docs/test_examples.py` (Wave 3)
- `tests/performance/` (Wave 4)

### Read-Only Access
- Source files being tested

### Wave Assignments
- **Wave 1:** Fix test infrastructure, import errors, failing tests
- **Wave 2:** Increase coverage for storage module
- **Wave 3:** API documentation, code example validation, license review
- **Wave 4:** Final validation, comprehensive testing, benchmarking

### Success Metrics
- All tests passing (100% test suite health)
- Coverage ≥80% overall
- Zero import errors

---

## Agent 3: automation-agent

### Primary Territory
- `requirements.txt` or `pyproject.toml` (dependency updates)
- `.pre-commit-config.yaml` (pre-commit hooks)
- `.github/dependabot.yml` (dependency automation)
- `pyproject.toml` (tool configurations)
- `CHANGELOG.md` (new file)
- `LICENSE` (new file)
- `docs/CONTRIBUTING.md` (documentation)

### New Files Created
- `.pre-commit-config.yaml`
- `.github/dependabot.yml`
- `CHANGELOG.md`
- `LICENSE`
- Security scan reports in `.context-kit/orchestration/repo-critical-fixes/reports/`

### Read-Only Access
- All source files (for formatting/linting)

### Wave Assignments
- **Wave 1:** Dependency patches, pre-commit setup, Dependabot
- **Wave 2:** Automated formatting (autoflake, black, isort), CHANGELOG, LICENSE
- **Wave 4:** Final security scan, repository health report

### Success Metrics
- Zero CVEs in dependencies
- Pre-commit hooks functional
- All code formatted consistently
- CHANGELOG and LICENSE present

---

## Agent 4: accessibility-agent

### Primary Territory
- `src/frontend/` (all frontend files)
- `data/copyparty/www/` (web UI files)
- CSS files for styling
- JavaScript files for interactivity

### New Files Created
- None (modifies existing frontend files)

### Read-Only Access
- None specific

### Wave Assignments
- **Wave 1:** Color contrast fixes, keyboard upload alternative
- **Wave 3:** aria-live regions, focus management, skip navigation

### Success Metrics
- WCAG 2.1 AA compliance ≥75%
- Zero color contrast violations
- Full keyboard navigation support
- Screen reader compatibility

---

## Agent 5: complexity-refactor-agent

### Primary Territory
- `src/processing/docling_parser.py` (refactoring)
- `src/processing/processor.py` (refactoring)
- `src/embeddings/colpali_wrapper.py` (Wave 4 optimizations)
- `src/embeddings/scoring.py` (Wave 4 optimizations)
- `src/storage/chroma_client.py` (Wave 4 optimizations - batch decompression only)

### New Files Created
- `src/processing/parsers/pdf_parse_strategy.py`
- `src/processing/parsers/docx_parse_strategy.py`
- `src/processing/parsers/pptx_parse_strategy.py`
- `src/processing/parsers/asr_options_builder.py`
- `src/processing/parsers/__init__.py`
- `src/processing/handlers/visual_embedding_handler.py`
- `src/processing/handlers/text_embedding_handler.py`
- `src/processing/handlers/__init__.py`

### Read-Only Access
- Test files for validation

### Wave Assignments
- **Wave 2:** Refactor high-complexity functions (DoclingParser, DocumentProcessor)
- **Wave 4:** Performance optimizations (batching, GPU cache, decorators)

### Success Metrics
- All refactored functions have CC <10
- All existing tests passing
- Performance targets met (Wave 4)

---

## Agent 6: architecture-cleanup-agent

### Primary Territory
- `src/utils/file_operations.py` (new)
- `src/utils/paths.py` (expansion)
- `src/utils/validation.py` (new)
- Files being refactored for DRY:
  - `src/processing/vtt_generator.py`
  - `src/storage/markdown_utils.py`
  - `src/processing/audio_metadata.py`
  - `src/processing/image_utils.py`
- `src/storage/chroma_client.py` (Wave 4 logging optimization - different section than complexity-refactor-agent)

### New Files Created
- `src/utils/file_operations.py`
- `src/utils/validation.py`

### Read-Only Access
- Files consuming shared utilities

### Wave Assignments
- **Wave 3:** Consolidate file I/O, centralize paths, centralize validation
- **Wave 4:** Logging optimization (guard debug serialization)

### Success Metrics
- DRY violations reduced from 8 → ≤2
- All utilities centralized in `src/utils/`
- Zero duplicated code patterns

---

## File Conflict Prevention Matrix

| File Path | Wave 1 | Wave 2 | Wave 3 | Wave 4 |
|-----------|--------|--------|--------|--------|
| `src/api/server.py` | security-fixer | - | - | - |
| `src/processing/worker_webhook.py` | security-fixer | - | - | - |
| `src/storage/chroma_client.py` | security-fixer (eval) | - | - | complexity-refactor (batch), architecture-cleanup (logging) |
| `src/processing/docling_parser.py` | - | complexity-refactor | - | - |
| `src/processing/processor.py` | - | complexity-refactor | - | - |
| `src/embeddings/colpali_wrapper.py` | - | - | - | complexity-refactor |
| `src/embeddings/scoring.py` | - | - | - | complexity-refactor |
| `src/frontend/*` | accessibility | - | accessibility | - |
| `src/utils/file_operations.py` | - | - | architecture-cleanup | - |
| `pytest.ini` | test-infrastructure | - | - | - |
| `requirements.txt` | automation | - | - | - |

**Note:** In Wave 4, `src/storage/chroma_client.py` has two agents working on different sections:
- **complexity-refactor-agent:** Lines 654-665 (batch decompression)
- **architecture-cleanup-agent:** Lines 351-361 (logging optimization)

These are non-overlapping changes and can be coordinated through Git or done sequentially within the wave.

---

## Coordination Rules

1. **No Overlapping File Access:** Within a wave, only one agent may write to a given file
2. **New Files Preferred:** When possible, create new files rather than modifying shared files
3. **Integration Through Interfaces:** Agents coordinate through well-defined contracts, not direct code dependencies
4. **Sequential Sub-Waves:** If conflicts arise, split work into sub-waves (e.g., Wave 4a, 4b)
5. **Read-Only Access:** Agents may read any file for validation but must not modify files outside their territory

---

## Handoff Protocol

When an agent completes work that another agent depends on:

1. **Complete All Tasks** in assigned territory
2. **Run Validation Tests** to confirm quality
3. **Update Status JSON** in `.context-kit/orchestration/repo-critical-fixes/status/`
4. **Post Handoff Notification** in `.context-kit/orchestration/repo-critical-fixes/handoffs.md`
5. **Dependent Agent Validates** integration contract before starting work

Example handoff entry:
```markdown
## Handoff: test-infrastructure-agent → complexity-refactor-agent
**Date:** 2025-10-19
**Wave:** 1 → 2
**Status:** ✅ Complete

### Deliverables
- All tests passing (pytest -v: 72/72 passed)
- Test coverage baseline: 61.5%
- Import errors fixed (pytest --collect-only: 72 tests collected)

### Integration Contract Validated
- ✅ All processing tests pass
- ✅ All storage tests pass
- ✅ End-to-end test passes

### Next Agent Action
complexity-refactor-agent may proceed with refactoring, using test suite for validation.
```

---

## Conflict Resolution

If two agents need to modify the same file:

1. **Option 1: Sequential Execution** - First agent completes, second agent starts
2. **Option 2: Interface Extraction** - Create new interface file both agents can implement
3. **Option 3: Coordinate Changes** - Agents communicate and merge changes manually
4. **Option 4: Escalate to Orchestrator** - If conflict cannot be resolved, escalate for manual coordination

Conflicts should be rare due to territorial ownership, but this protocol ensures quick resolution if they occur.

---

## Territory Expansion Rules

If an agent needs to modify a file outside their territory:

1. **Check Ownership** in this document
2. **Request Permission** from owning agent
3. **Document Exception** in handoffs.md
4. **Coordinate Changes** to avoid conflicts
5. **Update This Document** if territory changes permanently

---

This territorial ownership model ensures clean parallel execution with minimal merge conflicts and clear accountability for each component of the codebase.
