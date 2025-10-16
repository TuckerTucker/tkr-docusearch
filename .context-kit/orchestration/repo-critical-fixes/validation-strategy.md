# Validation Strategy

This document defines the comprehensive testing and quality assurance approach for the repository critical fixes orchestration.

## Validation Philosophy

**Progressive Validation:** Quality gates after each wave ensure problems are caught early and don't cascade into later work.

**Multi-Layer Validation:** Combine automated testing, manual review, and integration validation for comprehensive quality assurance.

**Contract-Driven Validation:** Test implementations against published contracts, not internal details.

---

## Validation Layers

### Layer 1: Unit Testing
**Scope:** Individual functions and classes
**When:** Continuously during development
**Tool:** pytest
**Owner:** All agents

**Requirements:**
- Every modified function has corresponding unit tests
- New code achieves ≥80% coverage
- Edge cases and error paths tested
- Fast execution (<5 seconds for full suite)

**Example:**
```bash
# Run unit tests for specific module
pytest tests/processing/test_docling_parser.py -v

# Check coverage
pytest tests/processing/ --cov=src/processing --cov-report=term-missing
```

---

### Layer 2: Integration Testing
**Scope:** Component interactions and data flow
**When:** After unit tests pass
**Tool:** pytest with integration fixtures
**Owner:** test-infrastructure-agent

**Requirements:**
- Test interactions between modified components
- Validate integration contracts
- Test realistic data flows
- Execution time <30 seconds

**Example:**
```bash
# Run integration tests
pytest tests/integration/ -v

# Test end-to-end workflow
pytest src/test_end_to_end.py -v
```

---

### Layer 3: Contract Validation
**Scope:** Interface compliance against published contracts
**When:** Before wave completion
**Tool:** Custom contract validation tests
**Owner:** Consuming agents

**Requirements:**
- Validate function signatures match contracts
- Test data format compliance
- Verify error handling matches spec
- Check performance requirements met

**Example:**
```bash
# Run contract validation tests
pytest tests/contracts/ -v --tb=short
```

---

### Layer 4: Security Validation
**Scope:** Vulnerability scanning and security testing
**When:** Wave 1 and Wave 4 (final)
**Tool:** bandit, pip-audit, manual review
**Owner:** automation-agent, security-fixer-agent

**Requirements:**
- Zero critical/high severity findings
- All CVEs patched
- Security tests pass
- Manual code review of sensitive areas

**Example:**
```bash
# Run security scans
bandit -r src/ -ll -f json > security-report.json
pip-audit --desc --format json > cve-report.json

# Verify clean
jq '.results | length' security-report.json  # Should be 0
```

---

### Layer 5: Performance Validation
**Scope:** Latency, throughput, memory usage
**When:** Wave 4
**Tool:** pytest-benchmark, custom profilers
**Owner:** complexity-refactor-agent, test-infrastructure-agent

**Requirements:**
- Search latency ≤300ms (target maintained)
- Memory usage within acceptable bounds
- No performance regressions >10%
- Optimizations show expected improvements

**Example:**
```bash
# Run performance benchmarks
pytest tests/performance/ --benchmark-only --benchmark-json=benchmark.json

# Compare before/after
python scripts/compare_benchmarks.py before.json after.json
```

---

### Layer 6: Accessibility Validation
**Scope:** WCAG 2.1 AA compliance
**When:** Wave 1 and Wave 3
**Tool:** axe-core, Pa11y, manual testing
**Owner:** accessibility-agent

**Requirements:**
- WCAG 2.1 AA compliance ≥75%
- Zero color contrast violations
- Keyboard navigation fully functional
- Screen reader compatibility verified

**Example:**
```bash
# Run automated accessibility audit
npx @axe-core/cli http://localhost:8000 --exit --tags wcag2a,wcag2aa

# Manual testing checklist
# - Tab through entire interface
# - Test with VoiceOver/NVDA
# - Verify color contrast with tool
# - Test at 200% zoom
```

---

### Layer 7: Code Quality Validation
**Scope:** Complexity, style, maintainability
**When:** Wave 2, continuous
**Tool:** radon, flake8, black, mypy
**Owner:** automation-agent

**Requirements:**
- Cyclomatic complexity ≤15 for all functions
- Zero flake8 errors
- Code formatted consistently
- Type hints validated

**Example:**
```bash
# Check complexity
radon cc src/ -s -n C --total-average

# Check style
flake8 src/ --config .flake8

# Check formatting
black --check src/
isort --check src/

# Check types
mypy src/ --config-file pyproject.toml
```

---

## Wave-Specific Validation Gates

### Wave 1 Gate: Critical Security & Infrastructure
**Prerequisites:** None
**Must Pass:**
1. ✅ All critical/high security vulnerabilities patched
   - bandit scan: 0 critical/high findings
   - Manual review: Security fixes validated
2. ✅ All tests passing
   - pytest: 100% test suite health
   - No import errors
   - No failing tests
3. ✅ CVEs resolved
   - pip-audit: Zero CVEs
   - All dependencies up to date with patches
4. ✅ Pre-commit hooks functional
   - pre-commit run --all-files passes
5. ✅ Basic accessibility improvements deployed
   - Color contrast meets WCAG AA
   - Keyboard upload alternative present

**Validation Commands:**
```bash
# Security validation
bandit -r src/ -ll | grep "Total issues (by severity)" | grep "High: 0" | grep "Critical: 0"
pip-audit | grep "No known vulnerabilities found"

# Test validation
pytest -v --tb=short
pytest --collect-only | grep "error" && exit 1 || exit 0

# Pre-commit validation
pre-commit run --all-files

# Accessibility validation
npx @axe-core/cli http://localhost:8000 --tags wcag2a --exit
```

**Blocking Criteria:**
- If >0 critical/high security findings: BLOCK Wave 2
- If >5% tests failing: BLOCK Wave 2
- If CVEs remain: BLOCK Wave 2

---

### Wave 2 Gate: Complexity Reduction & Code Quality
**Prerequisites:** Wave 1 gate passed
**Must Pass:**
1. ✅ All high-complexity functions refactored
   - radon: All functions CC <15
   - Target functions (docling_parser, processor) CC <10
2. ✅ Storage module coverage ≥80%
   - pytest --cov: storage coverage 80%+
3. ✅ All PEP 8 violations fixed
   - flake8: 0 errors
   - black: formatted
   - isort: sorted
4. ✅ CHANGELOG.md and LICENSE created
   - Files exist and are properly formatted
5. ✅ All tests passing
   - pytest: 100% test suite health after refactoring

**Validation Commands:**
```bash
# Complexity validation
radon cc src/processing/docling_parser.py src/processing/processor.py -s -n C

# Coverage validation
pytest --cov=src/storage --cov-report=term --cov-fail-under=80

# Code quality validation
flake8 src/
black --check src/
isort --check src/

# File existence
test -f CHANGELOG.md && test -f LICENSE && echo "Files present" || exit 1

# Test validation
pytest -v --tb=short
```

**Blocking Criteria:**
- If any function CC >15: BLOCK Wave 3
- If storage coverage <75%: BLOCK Wave 3
- If >10 flake8 errors: BLOCK Wave 3

---

### Wave 3 Gate: Architecture & Accessibility
**Prerequisites:** Wave 2 gate passed
**Must Pass:**
1. ✅ DRY violations reduced to ≤2
   - Manual code review
   - No duplicated file I/O patterns
2. ✅ All utilities centralized in `src/utils/`
   - file_operations.py, validation.py created
   - All consumers updated
3. ✅ WCAG 2.1 AA compliance ≥75%
   - axe-core: <10 violations
   - aria-live regions implemented
   - Focus management working
4. ✅ API documentation complete
   - All endpoints have error response docs
   - OpenAPI schema complete
5. ✅ Code examples validated
   - pytest tests/docs/ passing

**Validation Commands:**
```bash
# DRY validation (manual)
grep -r "def save.*artifact" src/ | wc -l  # Should be 1
grep -r "DOC_ID_PATTERN = " src/ | wc -l  # Should be 1

# Accessibility validation
npx @axe-core/cli http://localhost:8000 --tags wcag2aa --exit

# API documentation validation
curl http://localhost:8002/docs | grep -o "400\|401\|404\|500" | sort | uniq -c

# Code examples validation
pytest tests/docs/ -v
```

**Blocking Criteria:**
- If >2 DRY violations: BLOCK Wave 4
- If WCAG compliance <70%: BLOCK Wave 4
- If API docs incomplete: BLOCK Wave 4

---

### Wave 4 Gate (Final): Performance Optimization & Validation
**Prerequisites:** Wave 3 gate passed
**Must Pass:**
1. ✅ All performance optimizations implemented
   - Batch decompression active
   - GPU cache clearing implemented
   - MaxSim batching working
   - @torch.no_grad() decorators added
2. ✅ Search latency maintained or improved
   - Benchmark: avg latency ≤300ms
   - No regressions >10%
3. ✅ Memory usage optimized
   - Peak memory reduced
   - No OOM errors under load
4. ✅ Test coverage ≥80%
   - pytest --cov: Overall 80%+
5. ✅ Zero critical/high security findings
   - Final bandit scan clean
   - Final pip-audit clean
6. ✅ Repository health score ≥88/100
   - Re-run /repo-review
   - Validate improvement

**Validation Commands:**
```bash
# Performance validation
pytest tests/performance/ --benchmark-only --benchmark-json=final.json
python scripts/validate_performance.py final.json

# Coverage validation
pytest --cov=src --cov-report=term --cov-fail-under=80

# Security validation (final)
bandit -r src/ -ll -f json | jq '.results | length'  # Should be 0
pip-audit --desc | grep "No known vulnerabilities found"

# Repository health validation
# Re-run /repo-review and compare scores
```

**Blocking Criteria:**
- If performance regressed >10%: ROLLBACK optimizations
- If coverage <80%: BLOCK release
- If any critical/high security: BLOCK release
- If repo health <88/100: Review and address gaps

---

## Continuous Validation

### During Development
Every agent should run these checks before committing:

```bash
# Pre-commit checks (automated via pre-commit hooks)
black src/
isort src/
flake8 src/
mypy src/

# Local test run
pytest tests/ -v --tb=short

# If modifying security-sensitive code
bandit -r src/ -ll
```

### Daily Validation
Orchestrator runs comprehensive checks:

```bash
# Full test suite
pytest -v --cov=src --cov-report=html

# Security scan
bandit -r src/ -ll -f json > daily-security.json

# Complexity check
radon cc src/ -s -n C --total-average

# Coverage trending
python scripts/track_coverage.py
```

---

## Rollback Procedures

### If Tests Fail After Merge
1. Identify failing tests
2. Check if failures are in modified code
3. If >5% tests fail: Revert offending commit
4. Fix issues in isolation
5. Re-validate before merging

### If Performance Regresses
1. Run benchmark comparison
2. If >10% regression: Revert optimization
3. Profile to identify issue
4. Fix and re-benchmark
5. Merge only if performance restored

### If Security Issues Found
1. Immediately revert vulnerable code
2. Analyze vulnerability scope
3. Patch in isolation
4. Security review
5. Merge with additional tests

---

## Quality Metrics Dashboard

Track progress with these metrics:

| Metric | Baseline | Wave 1 | Wave 2 | Wave 3 | Wave 4 | Target |
|--------|----------|--------|--------|--------|--------|--------|
| Security (Critical/High) | 4 | 0 | - | - | 0 | 0 |
| CVEs | 4 | 0 | - | - | 0 | 0 |
| Test Coverage | 61.5% | 61.5% | 65% | 75% | 80% | ≥80% |
| Max Complexity | 57 | 57 | <10 | - | - | ≤15 |
| WCAG Compliance | 45% | 60% | - | 75% | - | ≥75% |
| Flake8 Errors | 247 | 247 | 0 | 0 | 0 | 0 |
| DRY Violations | 8 | - | - | ≤2 | - | ≤2 |
| Repo Health | 76/100 | 78/100 | 82/100 | 85/100 | 88/100 | ≥88/100 |

---

## Manual Review Checklist

### Security Review (Wave 1 & 4)
- [ ] All CORS configurations use explicit whitelists
- [ ] No eval() or exec() usage
- [ ] All user inputs validated
- [ ] Secrets not in version control
- [ ] Authentication on all endpoints
- [ ] SQL injection prevention verified
- [ ] Path traversal prevention verified

### Code Quality Review (Wave 2)
- [ ] No functions exceed CC 15
- [ ] No files exceed 500 lines
- [ ] Proper error handling
- [ ] Meaningful variable names
- [ ] Appropriate comments
- [ ] No TODO/FIXME in prod code

### Architecture Review (Wave 3)
- [ ] No code duplication
- [ ] Clear separation of concerns
- [ ] Dependency injection used
- [ ] Interfaces properly defined
- [ ] Configuration centralized
- [ ] Proper module boundaries

### Performance Review (Wave 4)
- [ ] No N+1 queries
- [ ] Efficient algorithms
- [ ] Proper caching
- [ ] Memory leaks addressed
- [ ] Database indexes optimal
- [ ] Bundle size acceptable

---

## Testing Best Practices

### Write Tests That Are:
- **Fast:** Execute in milliseconds
- **Isolated:** No dependencies on external services
- **Repeatable:** Same result every time
- **Self-validating:** Clear pass/fail
- **Timely:** Written with code

### Avoid:
- **Flaky tests:** That randomly fail
- **Slow tests:** That take >5 seconds
- **Coupled tests:** That depend on each other
- **Unclear assertions:** That don't explain failures

---

This validation strategy ensures quality at every step of the orchestration while maintaining fast feedback loops and clear gates for progress.
