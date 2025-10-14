# Validation Strategy

**Purpose**: Ensure quality and correctness at each wave through progressive validation

**Philosophy**: Test early, test often, validate integration continuously

---

## Validation Pyramid

```
                    ┌─────────────────┐
                    │ System Tests    │  (Wave 4)
                    │ End-to-End      │
                    └─────────────────┘
                  ┌───────────────────────┐
                  │ Integration Tests     │  (Wave 2, 3)
                  │ Component Interaction │
                  └───────────────────────┘
              ┌─────────────────────────────────┐
              │ Unit Tests                      │  (Wave 1)
              │ Individual Functions            │
              └─────────────────────────────────┘
```

---

## Wave 1: Foundation Validation

### Objective
Validate file_validator module independently before any integration

### Test Categories

#### 1. Unit Tests (file_validator.py)
**File**: `src/processing/test_file_validator.py`

**Coverage Requirements**: >95%

**Test Cases**:
```python
class TestGetSupportedExtensions:
    def test_default_formats(self):
        """Verify default format list is correct"""

    def test_env_override(self, monkeypatch):
        """Verify SUPPORTED_FORMATS env var works"""

    def test_case_insensitive(self):
        """Verify extensions are lowercased"""

    def test_dot_prefix(self):
        """Verify extensions include dot prefix"""


class TestValidateFileType:
    def test_supported_extension(self):
        """Verify supported extensions return (True, '')"""

    def test_unsupported_extension(self):
        """Verify unsupported returns (False, error_message)"""

    def test_no_extension(self):
        """Verify files without extension are rejected"""

    def test_multiple_dots(self):
        """Verify file.tar.gz handling"""

    def test_case_insensitive_validation(self):
        """Verify .PDF == .pdf"""


class TestValidateFileSize:
    def test_within_limit(self):
        """Verify files under limit pass"""

    def test_exactly_at_limit(self):
        """Verify edge case of exact limit"""

    def test_over_limit(self):
        """Verify oversized files fail"""

    def test_custom_limit(self):
        """Verify max_mb parameter works"""

    def test_error_message_format(self):
        """Verify error message shows actual vs limit"""


class TestValidateFile:
    def test_valid_file(self):
        """Verify combined validation success"""

    def test_invalid_type(self):
        """Verify type error caught"""

    def test_invalid_size(self):
        """Verify size error caught"""

    def test_both_invalid(self):
        """Verify type checked first"""
```

**Execution**:
```bash
pytest src/processing/test_file_validator.py -v --cov=src/processing/file_validator --cov-report=term-missing
```

**Success Criteria**:
- All tests pass
- Coverage >95%
- No external dependencies required

---

#### 2. Contract Validation
**File**: `integration-contracts/file-validator-api.md`

**Validation**:
- API signature matches documented contract
- Return types match specification
- Error formats match specification
- Constants exported as documented

**Checklist**:
```yaml
API Contract Verification:
  - [ ] get_supported_extensions() returns Set[str]
  - [ ] validate_file_type() returns Tuple[bool, str]
  - [ ] validate_file_size() returns Tuple[bool, str]
  - [ ] validate_file() returns Tuple[bool, str]
  - [ ] DEFAULT_FORMATS constant exists
  - [ ] All functions have docstrings
  - [ ] All functions have type hints
```

---

#### 3. Integration Spec Validation
**Files**: `integration-contracts/worker-integration-spec.md`, `config-integration-spec.md`

**Validation**:
- All validation call sites documented
- Replacement patterns specified
- Error formats preserved
- No validation logic missed

**Manual Review**:
```bash
# Verify all SUPPORTED_EXTENSIONS references found
grep -n "SUPPORTED_EXTENSIONS" src/processing/worker*.py

# Verify all path.suffix validations found
grep -n "path.suffix" src/processing/worker*.py

# Cross-check with spec
diff <(grep -n "location:" integration-contracts/worker-integration-spec.md) <(grep -n "SUPPORTED" src/processing/worker*.py)
```

---

### Wave 1 Gate Criteria

**PASS Requirements**:
- ✅ All file_validator unit tests pass
- ✅ Coverage >95%
- ✅ API contract documented and validated
- ✅ Worker integration spec complete
- ✅ Config integration spec complete
- ✅ No TODOs or FIXMEs in code
- ✅ All status files show "complete"

**FAIL Triggers**:
- ❌ Any test failures
- ❌ Coverage <95%
- ❌ Missing contract documentation
- ❌ Incomplete integration specs

**If FAIL**: Block Wave 2, fix issues, re-validate

---

## Wave 2: Worker Integration Validation

### Objective
Verify file_validator integrates correctly into both workers without behavior changes

### Test Categories

#### 1. Integration Tests (worker validation)
**Files**: `src/processing/test_worker_validation.py` (new)

**Test Cases**:
```python
class TestWorkerWebhookValidation:
    def test_supported_file_accepted(self):
        """Verify PDF upload accepted"""

    def test_unsupported_file_rejected(self):
        """Verify .xyz upload rejected"""

    def test_error_format_preserved(self):
        """Verify error response format unchanged"""

    def test_supported_extensions_loaded(self):
        """Verify extensions from file_validator"""


class TestLegacyWorkerValidation:
    # Same tests for worker.py
```

**Execution**:
```bash
# Start services
./scripts/start-all.sh --docker-only

# Run integration tests
pytest src/processing/test_worker_validation.py -v

# Manual verification
curl -X POST http://localhost:8002/process \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/uploads/test.pdf", "filename": "test.pdf"}'

curl -X POST http://localhost:8002/process \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/uploads/test.xyz", "filename": "test.xyz"}'
# Should return: {"status": "skipped", "error": "Unsupported file type: .xyz"}
```

---

#### 2. Regression Tests
**Objective**: Verify no behavior changes

**Test Matrix**:
| File Type | Before Wave 2 | After Wave 2 | Status |
|-----------|--------------|--------------|--------|
| .pdf | Accepted | Accepted | ✅ |
| .png | Accepted | Accepted | ✅ |
| .mp3 | Accepted | Accepted | ✅ |
| .xyz | Rejected | Rejected | ✅ |
| .PDF (caps) | Accepted | Accepted | ✅ |

**Execution**:
```bash
# Record baseline before Wave 2
./scripts/start-all.sh
python tests/record_validation_baseline.py > baseline_wave1.json

# Apply Wave 2 changes
# ...

# Compare behavior
python tests/compare_validation_behavior.py baseline_wave1.json > wave2_diff.json

# Verify no differences
test $(jq '.differences | length' wave2_diff.json) -eq 0
```

---

#### 3. Worker Startup Tests
**Objective**: Verify workers start successfully

**Checklist**:
```bash
# Start webhook worker
./scripts/start-all.sh

# Check health
curl http://localhost:8002/health
# Expected: {"status": "healthy", ...}

# Check logs for errors
tail -100 logs/worker-native.log | grep -i error
# Expected: no errors

# Verify file_validator import
grep -n "from .file_validator import" src/processing/worker_webhook.py
# Expected: import exists

# Start legacy worker (if still used)
python -m src.processing.worker
# Expected: starts without import errors
```

---

### Wave 2 Gate Criteria

**PASS Requirements**:
- ✅ All integration tests pass
- ✅ Regression tests show zero behavior changes
- ✅ Both workers start successfully
- ✅ Health endpoints respond
- ✅ File validation works identically
- ✅ Error formats preserved
- ✅ No import errors

**FAIL Triggers**:
- ❌ Any test failures
- ❌ Behavior changes detected
- ❌ Worker startup failures
- ❌ Import errors

**If FAIL**: Roll back Wave 2 changes, fix, re-validate

---

## Wave 3: Configuration Integration Validation

### Objective
Verify ProcessingConfig integration and worker configuration consolidation

### Test Categories

#### 1. ProcessingConfig Tests
**File**: `src/config/test_processing_config.py` (exists, update)

**New Test Cases**:
```python
class TestProcessingConfigValidation:
    def test_validate_file_delegates_to_validator(self):
        """Verify ProcessingConfig.validate_file uses file_validator"""

    def test_supported_formats_from_env(self):
        """Verify formats loaded from environment"""

    def test_backward_compatibility(self):
        """Verify existing API unchanged"""

    def test_file_validator_integration(self):
        """Verify calls to file_validator work"""
```

**Execution**:
```bash
pytest src/config/test_processing_config.py -v
```

---

#### 2. Worker Configuration Tests
**File**: `src/processing/test_worker_config.py` (new)

**Test Cases**:
```python
class TestWorkerWebhookConfiguration:
    def test_uses_processing_config(self):
        """Verify worker initializes ProcessingConfig"""

    def test_no_module_level_duplication(self):
        """Verify no SUPPORTED_FORMATS at module level"""

    def test_config_accessible(self):
        """Verify config stored in app.state"""

    def test_supported_formats_from_config(self):
        """Verify formats come from config instance"""


class TestLegacyWorkerConfiguration:
    # Same tests for worker.py
```

**Execution**:
```bash
pytest src/processing/test_worker_config.py -v
```

---

#### 3. End-to-End Configuration Tests
**Objective**: Verify entire configuration chain works

**Test Flow**:
```python
# 1. Set environment variable
os.environ['SUPPORTED_FORMATS'] = 'pdf,png,test'

# 2. Start worker
worker = start_worker()

# 3. Verify config loaded
assert worker.config.supported_formats == ['pdf', 'png', 'test']

# 4. Test file validation
assert worker.validate_file('test.pdf')[0] == True
assert worker.validate_file('test.test')[0] == True
assert worker.validate_file('test.xyz')[0] == False
```

---

#### 4. Integration Chain Tests
**Objective**: Verify file_validator → ProcessingConfig → Worker chain

**Validation**:
```
Environment Variable (SUPPORTED_FORMATS)
    ↓
file_validator.get_supported_extensions()
    ↓
ProcessingConfig.supported_formats
    ↓
Worker startup uses config
    ↓
Worker validation works
```

**Test**:
```bash
# Set env var
export SUPPORTED_FORMATS="pdf,test"

# Start system
./scripts/start-all.sh

# Verify chain
python -c "
from src.processing.file_validator import get_supported_extensions
from src.config.processing_config import ProcessingConfig

# Step 1: file_validator
exts = get_supported_extensions()
assert '.test' in exts

# Step 2: ProcessingConfig
config = ProcessingConfig()
assert 'test' in config.supported_formats

# Step 3: Worker uses config (check logs)
"

# Check worker logs
tail -50 logs/worker-native.log | grep -i "supported"
# Expected: mentions 'test' format
```

---

### Wave 3 Gate Criteria

**PASS Requirements**:
- ✅ ProcessingConfig tests pass
- ✅ Worker config tests pass
- ✅ End-to-end config tests pass
- ✅ Integration chain validated
- ✅ No module-level config duplication
- ✅ Workers use ProcessingConfig
- ✅ All existing tests still pass

**FAIL Triggers**:
- ❌ Any test failures
- ❌ Configuration chain broken
- ❌ Module-level duplication still exists
- ❌ Workers not using ProcessingConfig

**If FAIL**: Roll back Wave 3 changes, fix, re-validate

---

## Wave 4: Documentation & Final Validation

### Objective
Verify documentation completeness and update tracking

### Validation Categories

#### 1. Documentation Completeness
**Checklist**:
```markdown
CONFIGURATION.md:
  - [ ] All environment variables documented
  - [ ] Defaults specified
  - [ ] Valid value ranges provided
  - [ ] Examples included
  - [ ] ProcessingConfig API documented
  - [ ] file_validator API documented
  - [ ] Migration guide present

file-validator-usage.md:
  - [ ] Usage examples clear
  - [ ] Integration patterns shown
  - [ ] Error handling documented

worker-architecture-decision.md:
  - [ ] Decision documented with justification
  - [ ] Action plan specified
  - [ ] If deprecated: migration guide present
  - [ ] If kept: comparison table present

TECHNICAL_DEBT.md:
  - [ ] Items #1 and #3 moved to "Resolved"
  - [ ] Resolution dates added
  - [ ] Commit references included
  - [ ] Solution approach documented
```

---

#### 2. Documentation Accuracy Tests
**Validation**:
```bash
# Extract code examples from docs
python tests/extract_doc_examples.py CONFIGURATION.md > examples.py

# Verify examples work
python examples.py
# Expected: all examples execute without error

# Verify API signatures match docs
python tests/verify_api_docs.py \
  --module src.processing.file_validator \
  --docs integration-contracts/file-validator-api.md
# Expected: all signatures match
```

---

#### 3. Final System Tests
**Objective**: Complete end-to-end validation

**Test Scenarios**:
```yaml
Scenario 1: Fresh Start
  - Stop all services
  - Clear environment
  - Set SUPPORTED_FORMATS=pdf,png
  - Start services
  - Verify PDF accepted, PNG accepted, XYZ rejected

Scenario 2: Environment Override
  - Set SUPPORTED_FORMATS=pdf
  - Restart services
  - Verify only PDF accepted

Scenario 3: Config Chain
  - Verify env var → file_validator → ProcessingConfig → Worker
  - Trace through logs

Scenario 4: Legacy vs Webhook
  - Start both workers (if both kept)
  - Verify identical behavior
  - Verify both use ProcessingConfig
```

**Execution**:
```bash
pytest tests/test_system_final.py -v --log-cli-level=INFO
```

---

### Wave 4 Gate Criteria

**PASS Requirements**:
- ✅ All documentation complete
- ✅ Documentation examples work
- ✅ API docs match implementation
- ✅ Final system tests pass
- ✅ TECHNICAL_DEBT.md updated
- ✅ All previous wave tests still pass

**FAIL Triggers**:
- ❌ Incomplete documentation
- ❌ Doc examples don't work
- ❌ System tests fail
- ❌ Technical debt not updated

**If FAIL**: Complete documentation, fix issues, re-validate

---

## Continuous Validation

### On Every Commit
```bash
# Quick validation
pytest src/ -x  # Stop on first failure
./scripts/start-all.sh --docker-only
curl http://localhost:8002/health
./scripts/stop-all.sh
```

### On Every Wave Completion
```bash
# Full validation suite
pytest src/ -v --cov=src/ --cov-report=html
./scripts/start-all.sh
./scripts/status.sh
python tests/full_system_test.py
./scripts/stop-all.sh
```

### On Final Completion
```bash
# Comprehensive validation
pytest src/ -v --cov=src/ --cov-report=html --cov-fail-under=90
./scripts/start-all.sh

# Upload test files
python tests/upload_test_suite.py

# Monitor processing
python tests/monitor_processing.py --timeout=300

# Verify results
python tests/verify_processing_results.py

# Check logs for errors
grep -i error logs/*.log
# Expected: no unexpected errors

./scripts/stop-all.sh
```

---

## Quality Metrics

### Code Coverage
- **Target**: >90% overall
- **Minimum**: >85% per module
- **Critical Path**: 100% for file_validator

### Test Success Rate
- **Target**: 100% pass rate
- **Allowed Flakiness**: 0% (no flaky tests)

### Performance
- **Validation Speed**: <10ms per file
- **Worker Startup**: <30s with config loading

### Behavior Preservation
- **Regression Count**: 0
- **API Changes**: 0 (pure refactoring)
- **Error Format Changes**: 0

---

## Rollback Testing

### Rollback Validation
After each wave, verify rollback works:

```bash
# Record current state
git rev-parse HEAD > current_commit.txt
pytest src/ -v > current_tests.log
./scripts/status.sh > current_status.txt

# Simulate rollback
git revert HEAD
pytest src/ -v > rollback_tests.log

# Verify rollback successful
diff current_tests.log rollback_tests.log || echo "Tests differ (expected)"
./scripts/start-all.sh
./scripts/status.sh
# Verify system works in rolled-back state

# Return to current
git revert HEAD
```

---

## Validation Automation

### CI/CD Integration
```yaml
# .github/workflows/tech-debt-validation.yml
name: Technical Debt Resolution Validation

on:
  push:
    branches: [ tech-debt-resolution/* ]

jobs:
  wave-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.13'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest src/ -v --cov=src/ --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v2

      - name: Validate contracts
        run: python tests/validate_integration_contracts.py

      - name: System test
        run: |
          docker-compose up -d
          sleep 10
          python tests/system_validation.py
          docker-compose down
```

---

## Success Criteria Summary

### Wave 1
- ✅ file_validator complete with >95% coverage
- ✅ All contracts published
- ✅ Zero external dependencies

### Wave 2
- ✅ Both workers refactored
- ✅ Zero behavior changes
- ✅ All tests pass

### Wave 3
- ✅ ProcessingConfig integrated everywhere
- ✅ No config duplication
- ✅ Configuration chain working

### Wave 4
- ✅ Documentation complete and accurate
- ✅ Technical debt updated
- ✅ All tests pass

### Overall
- ✅ Zero duplicate validation code
- ✅ Single source of truth established
- ✅ All tests passing
- ✅ System behavior unchanged
- ✅ Documentation complete
- ✅ Technical debt resolved
