# Worker Integration Specification

**Agent**: worker-analysis-agent
**Wave**: 1
**Date**: 2025-10-13
**Status**: Complete

## Executive Summary

This specification documents all file validation call sites in both workers and provides line-by-line replacement patterns for integration with the centralized `file_validator` module.

### Analysis Results
- **Total validation sites found**: 4 (plus 3 read-only usages)
- **Workers analyzed**: 2
  - `worker_webhook.py`: 2 sites + 1 logging usage
  - `worker.py`: 2 sites + 2 additional usages (file scanning + logging)
- **Validation patterns identified**: 2 types
  1. Configuration loading (SUPPORTED_EXTENSIONS initialization)
  2. Runtime validation (suffix checking)
- **Additional usages identified**: 3 read-only references
  - Logging: Lines 664 (webhook), 211 (worker)
  - File scanning: Line 187 (worker)

---

## Validation Call Sites

### Worker 1: `worker_webhook.py`

#### Site 1.1: Configuration Loading
**Location**: `src/processing/worker_webhook.py:73-74`

**Current Implementation**:
```python
# Load supported formats from environment
_formats_str = os.getenv("SUPPORTED_FORMATS", "pdf,docx,pptx,xlsx,html,xhtml,md,asciidoc,csv,mp3,wav,vtt,png,jpg,jpeg,tiff,bmp,webp")
SUPPORTED_EXTENSIONS = {f".{fmt.strip().lower()}" for fmt in _formats_str.split(",")}
```

**Replacement Pattern**:
```python
# Import at module level (line 44, after markdown_utils import)
from .file_validator import get_supported_extensions

# Replace lines 73-74 with:
# Load supported extensions from centralized validator
SUPPORTED_EXTENSIONS = get_supported_extensions()
```

**Context**:
- Located in module-level configuration section
- Sets global `SUPPORTED_EXTENSIONS` constant
- Used by downstream validation logic
- Also logged at startup (line 664)

**Dependencies**:
- Requires `file_validator` module to be implemented first
- No circular imports (validation is at module initialization)

---

#### Site 1.2: Runtime Validation
**Location**: `src/processing/worker_webhook.py:207-210`

**Current Implementation**:
```python
# Check extension
if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
    return {
        "status": "skipped",
        "error": f"Unsupported file type: {path.suffix}"
    }
```

**Context Block** (lines 200-211):
```python
try:
    # Verify file exists
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Check extension
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return {
            "status": "skipped",
            "error": f"Unsupported file type: {path.suffix}"
        }

    # Generate doc ID from file hash (SHA-256) if not provided
```

**Replacement Pattern**:
```python
# Import at module level (add after get_supported_extensions import)
from .file_validator import validate_file_type

# Replace lines 207-211 with:
# Validate file type
valid, error = validate_file_type(str(path))
if not valid:
    return {
        "status": "skipped",
        "error": error
    }
```

**Critical Requirements**:
1. **Return format MUST match exactly**: `{"status": "skipped", "error": "..."}`
2. **Error message format MUST preserve**: `f"Unsupported file type: {path.suffix}"`
3. **Case sensitivity**: Validation must be case-insensitive (current: `.lower()`)
4. **Path type**: Accept both `str` and `Path` objects

**Function**: `process_document_sync()`
- Called from: Thread pool executor (line 443)
- Return value: Used by webhook endpoint `/process`
- Error handling: Errors logged and broadcast via WebSocket

---

### Worker 2: `worker.py` (Legacy)

#### Site 2.1: Configuration Loading
**Location**: `src/processing/worker.py:48-49`

**Current Implementation**:
```python
# Load supported formats from environment
_formats_str = os.getenv("SUPPORTED_FORMATS", "pdf,docx,pptx,xlsx,html,xhtml,md,asciidoc,csv,mp3,wav,vtt,png,jpg,jpeg,tiff,bmp,webp")
SUPPORTED_EXTENSIONS = {f".{fmt.strip().lower()}" for fmt in _formats_str.split(",")}
```

**Replacement Pattern**:
```python
# Import at module level (after imports section, around line 23)
from .file_validator import get_supported_extensions

# Replace lines 48-49 with:
# Load supported extensions from centralized validator
SUPPORTED_EXTENSIONS = get_supported_extensions()
```

**Context**:
- Located in module-level configuration section
- Sets global `SUPPORTED_EXTENSIONS` constant
- Used for file scanning (line 187-188) and validation (line 82)
- Also logged at startup (line 211)

---

#### Site 2.2: Runtime Validation
**Location**: `src/processing/worker.py:82-84`

**Current Implementation**:
```python
# Check if supported file type
if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
    logger.debug(f"Ignoring unsupported file type: {file_path}")
    return
```

**Context Block** (lines 74-90):
```python
def on_created(self, event: FileCreatedEvent):
    """Handle file creation events."""
    if event.is_directory:
        return

    file_path = Path(event.src_path)

    # Check if supported file type
    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        logger.debug(f"Ignoring unsupported file type: {file_path}")
        return

    # Skip temp files
    if file_path.name.startswith('.') or file_path.name.startswith('~'):
        return

    logger.info(f"New upload detected: {file_path}")
```

**Replacement Pattern**:
```python
# Import at module level (add after get_supported_extensions import)
from .file_validator import validate_file_type

# Replace lines 82-84 with:
# Validate file type
valid, error = validate_file_type(str(file_path))
if not valid:
    logger.debug(f"Ignoring unsupported file type: {file_path}")
    return
```

**Critical Requirements**:
1. **Silent failure**: No exception raised, just return early
2. **Debug logging**: Must preserve debug-level log message
3. **Message format**: `f"Ignoring unsupported file type: {file_path}"`
4. **Path type**: Accept both `str` and `Path` objects

**Function**: `DocumentUploadHandler.on_created()`
- Called from: Watchdog file system observer
- Event type: `FileCreatedEvent`
- Error handling: Silent early return (no error propagation)

**Additional Context**:
- This worker is legacy/deprecated (webhook version is primary)
- Still used in some deployment scenarios
- Uses watchdog for file monitoring vs webhook

---

### Additional Read-Only Usages

These usages reference `SUPPORTED_EXTENSIONS` but do not require code changes (beyond importing the constant):

#### Usage 1: File Scanning (worker.py:187-188)
**Location**: `src/processing/worker.py:187-188`

**Current Implementation**:
```python
existing_files = []
for ext in SUPPORTED_EXTENSIONS:
    existing_files.extend(uploads_dir.glob(f"*{ext}"))
```

**Context**: `process_existing_files()` function scans uploads directory for existing files.

**Impact**: None - `SUPPORTED_EXTENSIONS` will work identically after replacement. No code changes needed.

---

#### Usage 2: Startup Logging (worker_webhook.py:664)
**Location**: `src/processing/worker_webhook.py:664`

**Current Implementation**:
```python
logger.info(f"  Supported Extensions: {SUPPORTED_EXTENSIONS}")
```

**Context**: `startup_event()` function logs configuration at worker startup.

**Impact**: None - Set will be printed identically. No code changes needed.

---

#### Usage 3: Startup Logging (worker.py:211)
**Location**: `src/processing/worker.py:211`

**Current Implementation**:
```python
logger.info(f"  Supported Extensions: {SUPPORTED_EXTENSIONS}")
```

**Context**: `main()` function logs configuration at worker startup.

**Impact**: None - Set will be printed identically. No code changes needed.

---

## Integration Contract Requirements

### `file_validator` Module Interface

Based on analysis of all call sites, the `file_validator` module must provide:

#### Function 1: `get_supported_extensions()`
```python
def get_supported_extensions() -> Set[str]:
    """
    Get set of supported file extensions from environment.

    Returns:
        Set of lowercase extensions with leading dot (e.g., {'.pdf', '.docx'})

    Example:
        >>> extensions = get_supported_extensions()
        >>> '.pdf' in extensions
        True
    """
```

**Requirements**:
- Read from `SUPPORTED_FORMATS` environment variable
- Default: `"pdf,docx,pptx,xlsx,html,xhtml,md,asciidoc,csv,mp3,wav,vtt,png,jpg,jpeg,tiff,bmp,webp"`
- Format: Comma-separated list (no dots)
- Output: Set with leading dots and lowercase (e.g., `{'.pdf', '.docx'}`)
- Processing: Strip whitespace, add dot prefix, convert to lowercase

#### Function 2: `validate_file_type()`
```python
def validate_file_type(file_path: Union[str, Path]) -> Tuple[bool, Optional[str]]:
    """
    Validate if file type is supported for processing.

    Args:
        file_path: Path to file (str or Path object)

    Returns:
        Tuple of (is_valid, error_message)
        - (True, None) if file type is supported
        - (False, "Unsupported file type: .xyz") if not supported

    Example:
        >>> valid, error = validate_file_type("/path/to/doc.pdf")
        >>> valid
        True
        >>> valid, error = validate_file_type("/path/to/file.xyz")
        >>> error
        "Unsupported file type: .xyz"
    """
```

**Requirements**:
- Accept both `str` and `Path` objects
- Extract suffix using `Path.suffix`
- Case-insensitive comparison (convert to lowercase)
- Error message format: `f"Unsupported file type: {suffix}"` (preserve original case)
- Return tuple: `(bool, Optional[str])`

---

## Error Format Specifications

### Format 1: Webhook Error Response
**Context**: `worker_webhook.py` - HTTP endpoint responses

**Format**:
```python
{
    "status": "skipped",
    "error": "Unsupported file type: .xyz"
}
```

**Requirements**:
- Status field: Must be `"skipped"` (not "failed", "error", etc.)
- Error field: Must match format `"Unsupported file type: {suffix}"`
- Suffix case: Preserve original case from file (e.g., `.PDF` → `.PDF`)
- JSON serializable

**Usage**:
- Returned from `/process` endpoint
- Logged and broadcast via WebSocket
- Displayed in UI monitoring

---

### Format 2: Watchdog Silent Failure
**Context**: `worker.py` - File system event handler

**Format**:
```python
logger.debug(f"Ignoring unsupported file type: {file_path}")
return
```

**Requirements**:
- Log level: `DEBUG` (not INFO, WARNING, ERROR)
- Message format: `f"Ignoring unsupported file type: {file_path}"`
- No exception raised
- Early return from handler

**Usage**:
- File system observer event filtering
- No user-facing error
- Debug logging only

---

## Configuration Variables

### Environment Variable: `SUPPORTED_FORMATS`

**Current Usage**:
- **worker_webhook.py**: Line 73
- **worker.py**: Line 48

**Specification**:
```yaml
name: SUPPORTED_FORMATS
type: string
format: comma-separated list (no dots, no spaces recommended)
default: "pdf,docx,pptx,xlsx,html,xhtml,md,asciidoc,csv,mp3,wav,vtt,png,jpg,jpeg,tiff,bmp,webp"
example_valid: "pdf,docx,pptx"
example_invalid: ".pdf,.docx,.pptx"  # Dots not supported
case_sensitivity: case-insensitive (converted to lowercase)
parsing_logic: split(','), strip(), add '.', lowercase()
```

**Processing Algorithm**:
```python
formats = os.getenv("SUPPORTED_FORMATS", "pdf,docx,...")
extensions = {f".{fmt.strip().lower()}" for fmt in formats.split(",")}
```

**Migration Path**:
1. `file_validator` reads same environment variable
2. Identical processing logic (backward compatible)
3. Workers import centralized implementation
4. No configuration changes required

---

## Integration Dependencies

### Import Order
```python
# Module-level imports (add after existing processing imports)
from .file_validator import get_supported_extensions, validate_file_type
```

### Initialization Order
```python
# Module-level configuration
SUPPORTED_EXTENSIONS = get_supported_extensions()  # Called at import time
```

### Runtime Dependencies
- No circular imports (file_validator has no dependencies on workers)
- No async requirements (all validation is synchronous)
- Thread-safe (immutable set returned by get_supported_extensions)

---

## Testing Requirements

### Test Coverage Required

#### Unit Tests: `file_validator`
1. **Environment variable parsing**
   - Default formats
   - Custom formats
   - Edge cases (empty string, single format, whitespace)

2. **Extension format conversion**
   - Dot prefix addition
   - Case normalization
   - Whitespace stripping

3. **File validation**
   - Supported extensions (all 18 defaults)
   - Unsupported extensions
   - Case insensitivity (.PDF == .pdf)
   - Path vs str input
   - Error message format

#### Integration Tests: Workers
1. **worker_webhook.py**
   - Supported file processing
   - Unsupported file rejection
   - Error response format
   - Configuration loading

2. **worker.py**
   - Supported file detection
   - Unsupported file filtering
   - Debug logging
   - Configuration loading

#### Validation Tests
1. **Error format preservation**
   - Webhook: `{"status": "skipped", "error": "Unsupported file type: .xyz"}`
   - Watchdog: Debug log format

2. **Configuration compatibility**
   - Same results as old implementation
   - Environment variable handling
   - Default formats

---

## Migration Checklist

### Phase 1: Implementation (file-validator-agent)
- [ ] Create `src/processing/file_validator.py`
- [ ] Implement `get_supported_extensions()`
- [ ] Implement `validate_file_type()`
- [ ] Write unit tests
- [ ] Validate against this specification

### Phase 2: Integration (worker-integrator-agent)
- [ ] Add imports to `worker_webhook.py`
- [ ] Replace Site 1.1 (configuration loading)
- [ ] Replace Site 1.2 (runtime validation)
- [ ] Add imports to `worker.py`
- [ ] Replace Site 2.1 (configuration loading)
- [ ] Replace Site 2.2 (runtime validation)
- [ ] Run integration tests

### Phase 3: Validation (validator-agent)
- [ ] Verify error format preservation
- [ ] Test all 18 supported formats
- [ ] Test unsupported formats
- [ ] Verify configuration loading
- [ ] Validate logging behavior
- [ ] Run end-to-end tests

### Phase 4: Cleanup (orchestrator)
- [ ] Remove duplicate validation code
- [ ] Update documentation
- [ ] Archive old implementation
- [ ] Mark wave complete

---

## Risk Assessment

### Low Risk
- Configuration loading replacement (simple import swap)
- No functional changes (identical logic)
- No API changes (internal refactor only)

### Medium Risk
- Error message format preservation (critical for UI)
- Thread safety (module-level initialization)

### Mitigation Strategies
1. **Extensive testing**: Unit + integration + end-to-end
2. **Error format validation**: Automated tests for exact format match
3. **Gradual rollout**: Test with webhook worker first, then legacy worker
4. **Rollback plan**: Keep original code commented until validation complete

---

## Success Criteria

### Functional Requirements
- ✓ All 4 validation sites successfully replaced
- ✓ Identical behavior to original implementation
- ✓ Error formats preserved exactly
- ✓ Configuration loading works identically

### Non-Functional Requirements
- ✓ No performance regression
- ✓ Thread-safe operation
- ✓ No circular dependencies
- ✓ Clean import structure

### Testing Requirements
- ✓ 100% unit test coverage for file_validator
- ✓ Integration tests pass for both workers
- ✓ Error format validation tests pass
- ✓ Configuration compatibility verified

---

## Appendix A: Code Context

### Full Function: `process_document_sync()` (worker_webhook.py)
```python
def process_document_sync(file_path: str, filename: str, doc_id: str = None) -> Dict[str, Any]:
    """
    Process a document (runs in thread pool).

    Args:
        file_path: Absolute path to document
        filename: Original filename
        doc_id: Optional pre-generated document ID (SHA-256 hash)

    Returns:
        Processing result dict
    """
    try:
        # Verify file exists
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Check extension [VALIDATION SITE 1.2]
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return {
                "status": "skipped",
                "error": f"Unsupported file type: {path.suffix}"
            }

        # ... rest of processing logic
```

### Full Function: `on_created()` (worker.py)
```python
def on_created(self, event: FileCreatedEvent):
    """Handle file creation events."""
    if event.is_directory:
        return

    file_path = Path(event.src_path)

    # Check if supported file type [VALIDATION SITE 2.2]
    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        logger.debug(f"Ignoring unsupported file type: {file_path}")
        return

    # Skip temp files
    if file_path.name.startswith('.') or file_path.name.startswith('~'):
        return

    logger.info(f"New upload detected: {file_path}")

    # Wait a moment for file write to complete
    time.sleep(2)

    # Add to processing queue
    self.processing_queue.append(file_path)
    self.process_file(file_path)
```

---

## Appendix B: Supported Formats Reference

### Default Formats (18 total)
```
Documents:  pdf, docx, pptx, xlsx, html, xhtml, md, asciidoc, csv
Audio:      mp3, wav, vtt
Images:     png, jpg, jpeg, tiff, bmp, webp
```

### Extension Conversion Examples
```
Input (env var):     "pdf,docx,pptx"
Output (set):        {'.pdf', '.docx', '.pptx'}

Input (env var):     "PDF, DOCX , pptx"
Output (set):        {'.pdf', '.docx', '.pptx'}  # Normalized

Input (env var):     ""
Output (set):        {'.pdf', '.docx', ...}      # Uses default
```

---

## Document Metadata

**Author**: worker-analysis-agent
**Reviewers**: file-validator-agent, worker-integrator-agent
**Approval**: Orchestrator
**Version**: 1.0
**Status**: Complete - Ready for Wave 1 handoff

---

**End of Specification**
