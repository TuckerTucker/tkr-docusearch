# Repository Critical Fixes - Orchestration Plan

**Goal:** Increase repository health from 76/100 to 88+/100 through parallel agent execution
**Timeline:** 4 waves over 2-3 weeks
**Max Agents:** 6 concurrent agents
**Strategy:** Territorial ownership + Interface-first development

## Agent Roster

1. **security-fixer-agent** - Security vulnerability remediation
2. **complexity-refactor-agent** - Code complexity reduction and refactoring
3. **test-infrastructure-agent** - Test coverage and infrastructure improvements
4. **accessibility-agent** - WCAG 2.1 AA compliance improvements
5. **architecture-cleanup-agent** - DRY violations and architectural improvements
6. **automation-agent** - CI/CD, tooling, and automation setup

---

## Wave 1: Critical Security & Infrastructure (Days 1-3)

**Prerequisites:** None - foundational work
**Goal:** Eliminate critical security vulnerabilities, unblock testing
**Parallelism:** 4 agents working simultaneously

### Agent: security-fixer-agent
**Territory:** `src/api/`, `src/processing/worker_webhook.py`, `src/storage/chroma_client.py`, `docker/`

**Tasks:**
1. Fix CORS configuration (wildcard origins)
   - `src/api/server.py:105`
   - `src/processing/worker_webhook.py:101`
   - Replace `allow_origins=["*"]` with environment-based whitelist
2. Replace unsafe eval() with ast.literal_eval()
   - `src/storage/chroma_client.py:660,734`
3. Add path validation to slide renderer API
   - `docker/slide_renderer_api.py:96-147`
   - Implement sanitization, directory restrictions, authentication
4. Secure hardcoded password
   - Generate secure `COPYPARTY_PASSWORD` in `docker/.env`
   - Create `docker/.env.example` template
   - Update `.gitignore`
5. Fix bare except clause
   - `src/embeddings/model_loader.py:366`
   - Replace with `except Exception as e:`

**Deliverables:**
- Modified files with security patches applied
- `docker/.env.example` template file
- Security validation report (manual testing + bandit scan)

**Integration Points:**
- None (self-contained security fixes)

**Validation:**
```bash
# Run security scan
bandit -r src/ -ll
# Verify CORS config loads from environment
pytest tests/test_api_security.py -v
# Test storage operations still work
pytest tests/storage/ -v
```

---

### Agent: test-infrastructure-agent
**Territory:** `pytest.ini`, `conftest.py`, `tests/`, new test files

**Tasks:**
1. Fix test import errors (PYTHONPATH configuration)
   - Add `pythonpath = src` to `pytest.ini`
   - Configure test discovery in `conftest.py`
   - Verify 19 blocked test files now discoverable
2. Fix 10 failing tests
   - Debug compression, deletion, collection management tests
3. Create missing test files for zero-coverage modules
   - `tests/search/test_validate_search.py` (0% → 80%)
   - `tests/storage/test_markdown_utils.py` (0% → 80%)

**Deliverables:**
- Updated `pytest.ini` and `conftest.py`
- All existing tests passing
- New test files for uncovered modules
- Test execution report showing all tests pass

**Integration Points:**
- **Consumes:** Security fixes from security-fixer-agent (tests must pass with new validation)
- **Provides:** Working test infrastructure for Wave 2 refactoring

**Validation:**
```bash
# All tests should be discoverable
pytest --collect-only | grep "tests collected"
# All tests should pass
pytest -v --tb=short
# Coverage baseline established
pytest --cov=src --cov-report=term-missing
```

---

### Agent: automation-agent
**Territory:** `.github/`, `pyproject.toml`, pre-commit configuration, CI/CD

**Tasks:**
1. Patch critical CVEs in dependencies
   - Update `requirements.txt` or `pyproject.toml`
   - `torch>=2.8.0`, `urllib3>=2.5.0`
   - Run `pip-audit` to verify resolution
2. Set up automated code formatting
   - Configure `black` (line-length 100)
   - Configure `autoflake` (unused imports)
   - Configure `isort` (import sorting)
3. Set up pre-commit hooks
   - Install commitlint for conventional commits
   - Add formatting hooks (black, autoflake, isort)
   - Add linting hooks (flake8, mypy)
4. Create Dependabot configuration
   - `.github/dependabot.yml`
   - Weekly Python package updates

**Deliverables:**
- Updated `requirements.txt` with patched versions
- `.pre-commit-config.yaml` configuration
- `.github/dependabot.yml` configuration
- `pyproject.toml` with tool configurations
- Documentation in `docs/CONTRIBUTING.md`

**Integration Points:**
- **Provides:** Automated tooling for all agents to use

**Validation:**
```bash
# CVEs resolved
pip-audit --require-hashes --desc
# Pre-commit hooks work
pre-commit run --all-files
# Formatting is idempotent
black --check src/
isort --check src/
```

---

### Agent: accessibility-agent
**Territory:** `src/frontend/`, `data/copyparty/www/`, accessibility improvements

**Tasks:**
1. Fix color contrast violations (WCAG 2.1 AA)
   - `src/frontend/styles.css`
   - `data/copyparty/www/styles.css`
   - Change `#6b7280` → `#4b5563` (4.5:1 contrast)
   - Change `#9ca3af` → darker variant
2. Add keyboard alternative for file upload
   - Enhance `src/frontend/upload-modal.js` or equivalent
   - Add accessible `<input type="file">` alongside drag-and-drop
   - Ensure keyboard navigation with Enter/Space

**Deliverables:**
- Updated CSS files with WCAG-compliant colors
- Enhanced upload UI with keyboard support
- Accessibility testing report (axe-core or Pa11y)

**Integration Points:**
- None (self-contained frontend improvements)

**Validation:**
```bash
# Run axe-core accessibility audit
npx @axe-core/cli http://localhost:8000
# Manual keyboard navigation test
# Color contrast verification with tool
```

---

**Wave 1 Synchronization Gate:**
- ✅ All critical security vulnerabilities patched
- ✅ All tests passing (100% test suite health)
- ✅ CVEs resolved in dependencies
- ✅ Pre-commit hooks functional
- ✅ Basic accessibility improvements deployed

---

## Wave 2: Complexity Reduction & Code Quality (Days 4-8)

**Prerequisites:** Wave 1 complete (working tests required for safe refactoring)
**Goal:** Reduce complexity hotspots, improve code quality
**Parallelism:** 3 agents working simultaneously

### Agent: complexity-refactor-agent
**Territory:** `src/processing/docling_parser.py`, `src/processing/processor.py`, new strategy pattern files

**Tasks:**
1. Refactor `DoclingParser._parse_with_docling` (CC: 57 → <10)
   - Extract Strategy pattern classes in `src/processing/parsers/`:
     - `pdf_parse_strategy.py`
     - `docx_parse_strategy.py`
     - `pptx_parse_strategy.py`
     - `asr_options_builder.py`
   - Update `docling_parser.py` to use strategies
   - Maintain backward compatibility through same public interface
2. Refactor `DocumentProcessor._store_embeddings` (CC: 29 → <10)
   - Extract embedding handlers in `src/processing/handlers/`:
     - `visual_embedding_handler.py`
     - `text_embedding_handler.py`
   - Implement Command pattern
   - Update `processor.py` to use handlers

**Deliverables:**
- New strategy/handler files in `src/processing/parsers/` and `src/processing/handlers/`
- Refactored `docling_parser.py` and `processor.py`
- All existing tests passing
- Complexity report showing CC <10 for refactored functions

**Integration Points:**
- **Consumes:** Working test suite from test-infrastructure-agent
- **Contract:** Public API of `DoclingParser` and `DocumentProcessor` unchanged

**Validation:**
```bash
# Run processing tests
pytest tests/processing/ -v
# Verify complexity reduction
radon cc src/processing/docling_parser.py src/processing/processor.py -s -n C
# Integration test
pytest src/test_end_to_end.py -v
```

---

### Agent: test-infrastructure-agent (continued)
**Territory:** `tests/`, test coverage improvements

**Tasks:**
1. Improve storage module test coverage (52.8% → 80%)
   - Focus on `tests/storage/test_compression.py` (47.6%)
   - Add tests for collection management
   - Add edge case coverage
2. Add integration tests for refactored code
   - Tests for new strategy pattern classes
   - Tests for new handler classes

**Deliverables:**
- Enhanced test files with higher coverage
- Coverage report showing ≥80% for storage module
- Integration tests for Wave 2 refactorings

**Integration Points:**
- **Depends on:** Refactored code from complexity-refactor-agent

**Validation:**
```bash
# Check coverage improvement
pytest --cov=src/storage --cov-report=term-missing --cov-fail-under=80
pytest --cov=src/processing --cov-report=term-missing
```

---

### Agent: automation-agent (continued)
**Territory:** Automated code improvements, documentation

**Tasks:**
1. Run automated code quality fixes
   - `autoflake --remove-all-unused-imports --in-place --recursive src/`
   - `black src/ --line-length 100`
   - `isort src/ --profile black`
2. Create CHANGELOG.md
   - Document Wave 1-5 progression (from .context-kit)
   - Follow Keep a Changelog format
   - Include all major features, fixes, breaking changes
3. Add LICENSE file
   - MIT license as mentioned in README
   - Include copyright year and author

**Deliverables:**
- Formatted codebase (104 unused imports removed, 60 line length violations fixed)
- `CHANGELOG.md` file
- `LICENSE` file
- Git commit with formatting changes

**Integration Points:**
- **Timing:** Run after complexity-refactor-agent completes to avoid merge conflicts

**Validation:**
```bash
# Verify no formatting changes needed
black --check src/
isort --check src/
# All tests still pass after formatting
pytest -v
```

---

**Wave 2 Synchronization Gate:**
- ✅ All high-complexity functions refactored (CC <10)
- ✅ Storage module coverage ≥80%
- ✅ All PEP 8 violations fixed (0 flake8 errors)
- ✅ CHANGELOG.md and LICENSE created
- ✅ All tests passing

---

## Wave 3: Architecture & Accessibility (Days 9-14)

**Prerequisites:** Wave 2 complete (clean codebase for architectural improvements)
**Goal:** Address DRY violations, complete accessibility improvements
**Parallelism:** 3 agents working simultaneously

### Agent: architecture-cleanup-agent
**Territory:** `src/utils/`, consolidation of duplicated code

**Tasks:**
1. Consolidate file I/O patterns (DRY violation fix)
   - Create `src/utils/file_operations.py`
   - Implement `save_document_artifact()` shared function
   - Refactor callers:
     - `src/processing/vtt_generator.py`
     - `src/storage/markdown_utils.py`
     - `src/processing/audio_metadata.py`
     - `src/processing/image_utils.py`
2. Centralize path constants
   - Expand `src/utils/paths.py` with all path constants
   - Remove scattered path definitions
3. Centralize validation patterns
   - Create `src/utils/validation.py`
   - Consolidate `DOC_ID_PATTERN` and validators
   - Update all consumers to use shared validators

**Deliverables:**
- New utility modules: `file_operations.py`, expanded `paths.py`, `validation.py`
- Refactored calling code using shared utilities
- All tests passing
- DRY violations reduced from 8 → ≤2

**Integration Points:**
- **Contract:** Utility functions provide same behavior as scattered implementations
- **Consumers:** Processing and storage modules

**Validation:**
```bash
# All tests pass with centralized utilities
pytest tests/ -v
# Verify no duplicated code patterns remain
grep -r "def save.*artifact" src/ | wc -l  # Should be 1
# Architecture validation
radon mi src/utils/ -s -n B
```

---

### Agent: accessibility-agent (continued)
**Territory:** `src/frontend/`, `data/copyparty/www/`, accessibility completion

**Tasks:**
1. Implement aria-live regions for dynamic content
   - Document grid loading announcements
   - Search results announcements
   - Upload progress announcements
   - Error message announcements
2. Add focus management to modals
   - Implement focus trap in modals
   - Return focus on close
   - ESC key handler for dismissal
3. Add skip navigation links
   - Skip to main content link
   - Skip to search link

**Deliverables:**
- Enhanced HTML templates with aria-live regions
- Modal focus management in JavaScript
- Skip navigation links added
- Accessibility audit report showing ≥75% WCAG 2.1 AA compliance

**Integration Points:**
- None (self-contained frontend improvements)

**Validation:**
```bash
# Run accessibility audit
npx @axe-core/cli http://localhost:8000 --exit
# Manual screen reader testing (VoiceOver/NVDA)
# Keyboard navigation testing
# WCAG compliance checker
```

---

### Agent: test-infrastructure-agent (continued)
**Territory:** Documentation, API documentation

**Tasks:**
1. Document REST API error responses
   - Add FastAPI docstrings for error responses
   - Include examples for 400, 401, 404, 500
   - Update OpenAPI/Swagger documentation
2. Add code example validation
   - Implement pytest-examples or doctest
   - Extract code blocks from markdown files
   - Create validation tests in `tests/docs/`
3. Review PyMuPDF and mutagen license compliance
   - Evaluate AGPL 3.0 and GPLv2+ license compatibility
   - Document decision in `docs/LICENSES.md`
   - If needed, plan migration to alternatives (pypdf, tinytag)

**Deliverables:**
- Enhanced API documentation with error examples
- Code example validation tests
- License compliance review document
- Updated documentation in `docs/`

**Integration Points:**
- **Depends on:** Centralized utilities from architecture-cleanup-agent

**Validation:**
```bash
# API documentation complete
curl http://localhost:8002/docs | grep -o "400\|401\|404\|500" | wc -l
# Code examples valid
pytest tests/docs/test_examples.py -v
```

---

**Wave 3 Synchronization Gate:**
- ✅ DRY violations reduced to ≤2
- ✅ All utilities centralized in `src/utils/`
- ✅ WCAG 2.1 AA compliance ≥75%
- ✅ API documentation complete
- ✅ Code examples validated
- ✅ License review complete

---

## Wave 4: Performance Optimization & Final Validation (Days 15-18)

**Prerequisites:** Wave 3 complete (clean architecture for performance optimization)
**Goal:** Implement performance optimizations, final validation
**Parallelism:** 4 agents working simultaneously

### Agent: complexity-refactor-agent (performance optimization)
**Territory:** `src/embeddings/`, `src/storage/`, performance-critical code

**Tasks:**
1. Implement batch decompression optimization
   - `src/storage/chroma_client.py:654-665`
   - Batch decompress embeddings vs sequential
   - Target: 40-60% reduction in Stage 2 latency
2. Optimize MaxSim scoring with batching
   - `src/embeddings/scoring.py:73-97`
   - Implement batched GPU MaxSim scoring
   - Target: 50-70% faster Stage 2 re-ranking
3. Add @torch.no_grad() decorators
   - `src/embeddings/colpali_wrapper.py:85,158,235`
   - Add to all inference methods
   - Target: 15-20% memory reduction
4. Add GPU cache clearing after batches
   - `src/embeddings/colpali_wrapper.py:127-136`
   - Add `torch.mps.empty_cache()` or equivalent
   - Prevents OOM errors, enables larger batches

**Deliverables:**
- Optimized embedding and storage modules
- Performance benchmark report
- All tests passing with optimizations

**Integration Points:**
- **Contract:** Public APIs unchanged, performance improved
- **Validation:** Benchmark comparison before/after

**Validation:**
```bash
# Run performance benchmarks
pytest tests/performance/ -v --benchmark
# Verify memory usage reduced
# Verify search latency improved
python scripts/benchmark_search.py
```

---

### Agent: architecture-cleanup-agent (performance optimization)
**Territory:** `src/storage/chroma_client.py`, logging optimization

**Tasks:**
1. Guard debug JSON serialization with log level check
   - `src/storage/chroma_client.py:351-361`
   - Wrap with `if logger.isEnabledFor(logging.DEBUG):`
   - Target: 20-30% faster embedding insertion in production

**Deliverables:**
- Optimized logging in storage module
- Performance improvement verification

**Integration Points:**
- **Timing:** Can run in parallel with complexity-refactor-agent optimizations

**Validation:**
```bash
# Run insertion benchmarks
pytest tests/storage/test_performance.py -v
# Verify no unnecessary serialization in INFO log level
LOG_LEVEL=INFO python scripts/benchmark_insertion.py
```

---

### Agent: test-infrastructure-agent (final validation)
**Territory:** Comprehensive testing and validation

**Tasks:**
1. Run full test suite with coverage report
   - Target: ≥80% overall coverage
   - Generate HTML coverage report
2. Conduct integration testing
   - End-to-end workflow tests
   - Multi-component integration tests
3. Performance benchmarking
   - Search latency measurements
   - Embedding speed measurements
   - Memory usage profiling

**Deliverables:**
- Full coverage report (≥80%)
- Integration test results (all passing)
- Performance benchmark report
- Test summary document

**Integration Points:**
- **Depends on:** All performance optimizations complete

**Validation:**
```bash
# Full test suite with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing --cov-fail-under=80
# End-to-end tests
pytest src/test_end_to_end.py -v
# Performance benchmarks
python scripts/run_all_benchmarks.py
```

---

### Agent: automation-agent (final security scan)
**Territory:** Security re-validation, final reports

**Tasks:**
1. Run comprehensive security scan
   - `bandit -r src/ -ll`
   - `pip-audit`
   - Manual review of critical areas
2. Generate final repository health report
   - Re-run `/repo-review` command
   - Compare before/after metrics
   - Target: 88-92/100 score

**Deliverables:**
- Security scan report (zero critical/high findings)
- Final repository health report
- Improvement summary document

**Integration Points:**
- **Depends on:** All fixes and optimizations complete

**Validation:**
```bash
# Security scan clean
bandit -r src/ -ll -f json | jq '.results | length'  # Should be 0
pip-audit --desc | grep "No known vulnerabilities found"
# Repository health improved
# Compare .context-kit/analysis/reports/before vs after
```

---

**Wave 4 Synchronization Gate (Final):**
- ✅ All performance optimizations implemented
- ✅ Search latency maintained or improved
- ✅ Memory usage optimized
- ✅ Test coverage ≥80%
- ✅ Zero critical/high security findings
- ✅ Repository health score ≥88/100
- ✅ All tests passing
- ✅ Performance targets met/exceeded

---

## Success Criteria Summary

| Metric | Before | Target | Status |
|--------|--------|--------|--------|
| Repository Health | 76/100 | ≥88/100 | Pending |
| Security (Critical/High) | 1C + 3H | 0 | Pending |
| CVEs | 4 | 0 | Pending |
| Test Coverage | 61.5% | ≥80% | Pending |
| WCAG 2.1 AA Compliance | 45% | ≥75% | Pending |
| Max Cyclomatic Complexity | 57 | ≤15 | Pending |
| DRY Violations | 8 | ≤2 | Pending |
| Unused Imports | 104 | 0 | Pending |
| Documentation Coverage | 78/100 | ≥85/100 | Pending |
| Commit Quality | 80/100 | Maintained | N/A |

---

## Risk Management

### Identified Risks

1. **Test failures after refactoring** (Wave 2)
   - Mitigation: Progressive testing, maintain backward compatibility
   - Rollback: Revert to pre-refactor state if >5 tests fail

2. **Performance regression from optimizations** (Wave 4)
   - Mitigation: Benchmark before/after, validate against targets
   - Rollback: Disable optimizations if latency increases >10%

3. **Merge conflicts between agents**
   - Mitigation: Territorial ownership, clear file boundaries
   - Resolution: Sequential execution within waves if conflicts detected

4. **Dependency update breaking changes** (Wave 1)
   - Mitigation: Test suite validation, incremental updates
   - Rollback: Pin to previous versions if incompatibilities found

### Circuit Breakers

- **Wave 1 Gate:** If security tests fail, halt Wave 2 until resolved
- **Wave 2 Gate:** If coverage drops <60%, halt Wave 3 until recovered
- **Wave 3 Gate:** If architectural violations increase, halt Wave 4
- **Wave 4 Gate:** If performance degrades >10%, rollback optimizations

---

## Agent Status Tracking

Each agent must update `.context-kit/orchestration/repo-critical-fixes/status/{agent-name}.json`:

```json
{
  "agent": "security-fixer-agent",
  "wave": 1,
  "status": "in_progress | completed | failed",
  "completed_tasks": [
    "Fix CORS configuration",
    "Replace eval() with ast.literal_eval()"
  ],
  "remaining_tasks": [
    "Add path validation to slide renderer"
  ],
  "blockers": [],
  "validation_status": {
    "tests_passing": true,
    "security_scan_clean": false,
    "integration_validated": false
  },
  "last_updated": "2025-10-16T20:30:00Z"
}
```

---

## Communication Protocol

### Daily Standups (Async)
Each agent posts to `.context-kit/orchestration/repo-critical-fixes/daily-status.md`:
- What was completed yesterday
- What is planned for today
- Any blockers or dependencies

### Integration Handoffs
When an agent completes work that another depends on:
1. Update status JSON with completion
2. Run validation tests
3. Post handoff notification in `.context-kit/orchestration/repo-critical-fixes/handoffs.md`
4. Dependent agent validates integration contract before proceeding

### Failure Escalation
If an agent encounters a blocking issue:
1. Update status JSON with "blocked" status
2. Document blocker in detail
3. Tag dependent agents
4. Escalate to orchestrator if blocker cannot be resolved within 4 hours

---

## Estimated Timeline

- **Wave 1:** 3 days (security + infrastructure)
- **Wave 2:** 5 days (complexity reduction + quality)
- **Wave 3:** 6 days (architecture + accessibility)
- **Wave 4:** 4 days (performance + validation)

**Total:** 18 days with 4-6 agents working in parallel

**Sequential equivalent:** ~45 days (2.5x efficiency gain)

---

## Next Steps

1. **Create integration contracts** (see `integration-contracts/` directory)
2. **Assign agent territories** (see `agent-assignments.md`)
3. **Define validation strategy** (see `validation-strategy.md`)
4. **Establish coordination protocol** (see `coordination-protocol.md`)
5. **Launch Wave 1 agents** in parallel

See individual specification files for detailed contracts and coordination details.
