# Configuration Integration Specification

**Agent**: config-analysis-agent
**Wave**: 1 (Analysis & Specification)
**Status**: Complete
**Date**: 2025-10-13

---

## Executive Summary

This specification documents how to consolidate configuration management by:
1. Making `ProcessingConfig.validate_file()` delegate to the shared `file_validator` module
2. Removing duplicate module-level configuration variables from workers
3. Integrating `ProcessingConfig` into worker startup lifecycle

**Key Finding**: We have **three separate implementations** of file validation logic that should be unified:
1. `src/processing/file_validator.py` (NEW - shared validator)
2. `src/config/processing_config.py` (ProcessingConfig class)
3. Module-level variables in workers (DUPLICATE - to be removed)

---

## Current Implementation Analysis

### 1. ProcessingConfig (src/config/processing_config.py)

**Location**: Lines 28-145

**Current Implementation**:
```python
@dataclass
class ProcessingConfig:
    """Document processing configuration."""

    # File handling
    max_file_size_mb: int = int(os.getenv('MAX_FILE_SIZE_MB', '100'))
    supported_formats: List[str] = None  # type: ignore
    upload_dir: str = os.getenv('UPLOAD_DIR', '/uploads')

    # Text processing
    chunk_size_words: int = int(os.getenv('TEXT_CHUNK_SIZE', '250'))
    chunk_overlap_words: int = int(os.getenv('TEXT_CHUNK_OVERLAP', '50'))

    # Visual processing
    page_render_dpi: int = int(os.getenv('PAGE_RENDER_DPI', '150'))

    # Worker configuration
    worker_threads: int = int(os.getenv('WORKER_THREADS', '1'))
    enable_queue: bool = os.getenv('ENABLE_QUEUE', 'false').lower() == 'true'

    # Logging
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    log_format: str = os.getenv('LOG_FORMAT', 'json')
    log_file: str = os.getenv('LOG_FILE', '/data/logs/worker.log')

    def __post_init__(self):
        """Initialize supported formats from environment."""
        if self.supported_formats is None:
            formats_str = os.getenv('SUPPORTED_FORMATS',
                'pdf,docx,pptx,xlsx,html,xhtml,md,asciidoc,csv,mp3,wav,vtt,png,jpg,jpeg,tiff,bmp,webp')
            self.supported_formats = [fmt.strip().lower() for fmt in formats_str.split(',')]

    def validate_file(self, filename: str, size_bytes: int) -> Tuple[bool, str]:
        """Validate uploaded file.

        Args:
            filename: Name of the uploaded file
            size_bytes: File size in bytes

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check extension
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if ext not in self.supported_formats:
            return False, f"Unsupported format: {ext}. Supported: {', '.join(self.supported_formats)}"

        # Check size
        size_mb = size_bytes / (1024 * 1024)
        if size_mb > self.max_file_size_mb:
            return False, f"File too large: {size_mb:.1f}MB > {self.max_file_size_mb}MB"

        return True, ""
```

**Analysis**:
- Implements its own validation logic (doesn't use file_validator)
- Stores formats as list without dot prefix: `['pdf', 'docx', ...]`
- Manual extension parsing: `filename.lower().split('.')[-1]`
- Size validation built-in

### 2. Shared File Validator (src/processing/file_validator.py)

**Location**: Lines 1-137

**Current Implementation**:
```python
DEFAULT_FORMATS = "pdf,docx,pptx,xlsx,html,xhtml,md,asciidoc,csv,mp3,wav,vtt,png,jpg,jpeg,tiff,bmp,webp"

def get_supported_extensions() -> Set[str]:
    """Load supported file extensions from environment.

    Returns:
        Set of extensions with dot prefix (e.g., {'.pdf', '.png'})
    """
    formats_str = os.getenv("SUPPORTED_FORMATS", DEFAULT_FORMATS)
    extensions = {f".{ext.strip().lower()}" for ext in formats_str.split(",")}
    return extensions

def validate_file_type(file_path: str) -> Tuple[bool, str]:
    """Validate file extension against supported formats."""
    path = Path(file_path)
    extension = path.suffix.lower()

    if not extension:
        return False, f"File has no extension: {file_path}"

    supported = get_supported_extensions()

    if extension not in supported:
        return False, f"Unsupported file type: {extension}. Supported: {', '.join(sorted(supported))}"

    return True, ""

def validate_file_size(size_bytes: int, max_mb: int = 100) -> Tuple[bool, str]:
    """Validate file size against limit."""
    if size_bytes < 0:
        return False, f"Invalid file size: {size_bytes} bytes"

    max_bytes = max_mb * 1024 * 1024

    if size_bytes > max_bytes:
        size_mb = size_bytes / (1024 * 1024)
        return False, f"File size {size_mb:.2f} MB exceeds maximum {max_mb} MB"

    return True, ""

def validate_file(file_path: str, size_bytes: int, max_mb: int = 100) -> Tuple[bool, str]:
    """Complete file validation (type + size)."""
    # Validate file type first
    type_valid, type_msg = validate_file_type(file_path)
    if not type_valid:
        return False, type_msg

    # Then validate size
    size_valid, size_msg = validate_file_size(size_bytes, max_mb)
    if not size_valid:
        return False, size_msg

    return True, ""
```

**Analysis**:
- Uses `Path.suffix` for robust extension parsing
- Stores formats as set with dot prefix: `{'.pdf', '.docx', ...}`
- Separate functions for type and size validation
- Proper error handling (negative size, missing extension)
- More comprehensive error messages

### 3. Worker Module-Level Configuration

#### worker_webhook.py (Lines 65-74)

**Current Implementation**:
```python
UPLOADS_DIR = Path(os.getenv("UPLOAD_DIR", "/uploads"))
CHROMA_HOST = os.getenv("CHROMA_HOST", "chromadb")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
DEVICE = os.getenv("DEVICE", "mps")
PRECISION = os.getenv("MODEL_PRECISION", "fp16")
WORKER_PORT = int(os.getenv("WORKER_PORT", "8002"))

# Load supported formats from environment
_formats_str = os.getenv("SUPPORTED_FORMATS", "pdf,docx,pptx,xlsx,html,xhtml,md,asciidoc,csv,mp3,wav,vtt,png,jpg,jpeg,tiff,bmp,webp")
SUPPORTED_EXTENSIONS = {f".{fmt.strip().lower()}" for fmt in _formats_str.split(",")}
```

**Usage**:
- Line 207: Extension check in `process_document_sync()`
  ```python
  if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
      return {"status": "skipped", "error": f"Unsupported file type: {path.suffix}"}
  ```
- Line 664: Logging during startup
  ```python
  logger.info(f"  Supported Extensions: {SUPPORTED_EXTENSIONS}")
  ```

#### worker.py (Lines 41-49)

**Current Implementation**:
```python
UPLOADS_DIR = Path(os.getenv("UPLOAD_DIR", "/uploads"))
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8001"))
DEVICE = os.getenv("DEVICE", "mps")
PRECISION = os.getenv("MODEL_PRECISION", "fp16")

# Load supported formats from environment
_formats_str = os.getenv("SUPPORTED_FORMATS", "pdf,docx,pptx,xlsx,html,xhtml,md,asciidoc,csv,mp3,wav,vtt,png,jpg,jpeg,tiff,bmp,webp")
SUPPORTED_EXTENSIONS = {f".{fmt.strip().lower()}" for fmt in _formats_str.split(",")}
```

**Usage**:
- Line 82: Extension check in `DocumentUploadHandler.on_created()`
  ```python
  if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
      logger.debug(f"Ignoring unsupported file type: {file_path}")
      return
  ```
- Line 188: Glob pattern for existing files
  ```python
  for ext in SUPPORTED_EXTENSIONS:
      existing_files.extend(uploads_dir.glob(f"*{ext}"))
  ```
- Line 211: Logging during startup
  ```python
  logger.info(f"  Supported Extensions: {SUPPORTED_EXTENSIONS}")
  ```

---

## Configuration Duplication Matrix

| Configuration Item | file_validator.py | ProcessingConfig | worker_webhook.py | worker.py |
|-------------------|-------------------|------------------|-------------------|-----------|
| `SUPPORTED_FORMATS` parsing | ✓ | ✓ | ✓ | ✓ |
| Extension validation | ✓ | ✓ | ✓ | ✓ |
| File size validation | ✓ | ✓ | ✗ | ✗ |
| Extension format | `.pdf` (set) | `pdf` (list) | `.pdf` (set) | `.pdf` (set) |
| Max file size | Param | Field | ✗ | ✗ |

**Technical Debt**: 4 separate implementations of format parsing, 4 implementations of extension checking.

---

## Refactoring Strategy

### Phase 1: Make ProcessingConfig delegate to file_validator

**Goal**: Eliminate duplicate validation logic in ProcessingConfig

**Changes to src/config/processing_config.py**:

```python
from pathlib import Path
from typing import List, Tuple
import os

# Import shared validator
from ..processing.file_validator import (
    get_supported_extensions,
    validate_file as validate_file_impl
)

@dataclass
class ProcessingConfig:
    """Document processing configuration."""

    # File handling
    max_file_size_mb: int = int(os.getenv('MAX_FILE_SIZE_MB', '100'))
    supported_formats: List[str] = None  # type: ignore
    upload_dir: str = os.getenv('UPLOAD_DIR', '/uploads')

    # ... rest of fields unchanged ...

    def __post_init__(self):
        """Initialize supported formats from environment."""
        if self.supported_formats is None:
            # Use file_validator to get extensions
            extensions_set = get_supported_extensions()
            # Convert {'.pdf', '.docx'} -> ['pdf', 'docx'] for backward compatibility
            self.supported_formats = [ext.lstrip('.') for ext in extensions_set]

    @property
    def supported_extensions_set(self) -> set:
        """Get supported extensions as set with dot prefix.

        Returns:
            Set like {'.pdf', '.docx', ...}
        """
        return {f".{fmt}" for fmt in self.supported_formats}

    def validate_file(self, filename: str, size_bytes: int) -> Tuple[bool, str]:
        """Validate uploaded file.

        Delegates to shared file_validator module for consistent validation.

        Args:
            filename: Name of the uploaded file
            size_bytes: File size in bytes

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Delegate to shared validator
        return validate_file_impl(filename, size_bytes, self.max_file_size_mb)
```

**Benefits**:
- ✓ Single source of truth for validation logic
- ✓ Maintains backward compatibility (supported_formats still a list)
- ✓ Same API signature for validate_file()
- ✓ ProcessingConfig now uses robust Path.suffix parsing
- ✓ Better error messages from file_validator

**Backward Compatibility**:
- `supported_formats` remains a list of strings without dots: `['pdf', 'docx']`
- `validate_file()` has identical signature and return type
- New property `supported_extensions_set` for code that needs set format

---

## Worker Integration Pattern

### Phase 2: Remove module-level config from workers

**Goal**: Replace hardcoded module-level configuration with ProcessingConfig

### worker_webhook.py Integration

**Lines to Remove** (65-74):
```python
# DELETE these module-level variables:
_formats_str = os.getenv("SUPPORTED_FORMATS", "...")
SUPPORTED_EXTENSIONS = {f".{fmt.strip().lower()}" for fmt in _formats_str.split(",")}
```

**Lines to Modify**:

1. **Line 25**: Add import
   ```python
   from ..config.processing_config import ProcessingConfig, EnhancedModeConfig
   ```

2. **Lines 79-82**: Update global variables section
   ```python
   # Global components (initialized at startup)
   document_processor: Optional[DocumentProcessor] = None
   parser: Optional[DoclingParser] = None
   status_manager: Optional[StatusManager] = None
   processing_config: Optional[ProcessingConfig] = None  # ADD THIS
   ```

3. **Lines 640-664**: Update startup_event() function
   ```python
   @app.on_event("startup")
   async def startup_event():
       """Initialize components on startup."""
       global document_processor, parser, status_manager, processing_config, _loop  # ADD processing_config

       # ... existing code ...

       # NEW: Initialize ProcessingConfig
       logger.info("Loading processing configuration...")
       processing_config = ProcessingConfig()
       logger.info(
           f"✓ Processing config loaded: "
           f"max_size={processing_config.max_file_size_mb}MB, "
           f"formats={len(processing_config.supported_formats)} types"
       )

       # Store in app.state for endpoint access
       app.state.processing_config = processing_config

       # ... rest of initialization ...

       # CHANGE: Use config for logging (line 664)
       logger.info(f"  Supported Extensions: {processing_config.supported_extensions_set}")
   ```

4. **Lines 206-211**: Update extension check in `process_document_sync()`
   ```python
   def process_document_sync(file_path: str, filename: str, doc_id: str = None) -> Dict[str, Any]:
       """Process a document (runs in thread pool)."""
       try:
           # ... existing code ...

           # CHANGE: Use config for validation
           if path.suffix.lower() not in processing_config.supported_extensions_set:
               return {
                   "status": "skipped",
                   "error": f"Unsupported file type: {path.suffix}"
               }

           # ... rest of function ...
   ```

**Alternative**: Use ProcessingConfig.validate_file() for comprehensive validation:
```python
def process_document_sync(file_path: str, filename: str, doc_id: str = None) -> Dict[str, Any]:
    """Process a document (runs in thread pool)."""
    try:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Use ProcessingConfig validation (type + size)
        is_valid, error_msg = processing_config.validate_file(filename, path.stat().st_size)
        if not is_valid:
            return {"status": "skipped", "error": error_msg}

        # ... rest of processing ...
```

### worker.py Integration (Legacy Worker)

**Lines to Remove** (47-49):
```python
# DELETE these module-level variables:
_formats_str = os.getenv("SUPPORTED_FORMATS", "...")
SUPPORTED_EXTENSIONS = {f".{fmt.strip().lower()}" for fmt in _formats_str.split(",")}
```

**Lines to Modify**:

1. **Add import after line 23**:
   ```python
   from ..config.processing_config import ProcessingConfig
   ```

2. **Add global variable after line 52**:
   ```python
   # Processing status tracking
   processing_status = {}
   processing_config = None  # ADD THIS
   ```

3. **Lines 199-249**: Update main() function
   ```python
   def main():
       """Main worker entry point."""
       global processing_config  # ADD THIS

       # ... existing logging ...

       # NEW: Initialize ProcessingConfig
       logger.info("Loading processing configuration...")
       processing_config = ProcessingConfig()
       logger.info(f"✓ Processing config loaded: {processing_config}")

       # ... rest of initialization ...

       # CHANGE: Use config for logging (line 211)
       logger.info(f"  Supported Extensions: {processing_config.supported_extensions_set}")
   ```

4. **Lines 82-84**: Update extension check in `DocumentUploadHandler.on_created()`
   ```python
   def on_created(self, event: FileCreatedEvent):
       """Handle file creation events."""
       # ... existing code ...

       # CHANGE: Use config for validation
       if file_path.suffix.lower() not in processing_config.supported_extensions_set:
           logger.debug(f"Ignoring unsupported file type: {file_path}")
           return

       # ... rest of function ...
   ```

5. **Lines 186-188**: Update glob pattern in `process_existing_files()`
   ```python
   def process_existing_files(handler: DocumentUploadHandler, uploads_dir: Path):
       """Process any existing files in uploads directory."""
       logger.info(f"Scanning {uploads_dir} for existing files...")

       existing_files = []
       # CHANGE: Use config for extensions
       for ext in processing_config.supported_extensions_set:
           existing_files.extend(uploads_dir.glob(f"*{ext}"))

       # ... rest of function ...
   ```

---

## Migration Checklist

### Wave 2: Core Refactoring

- [ ] **config-refactor-agent**: Update ProcessingConfig to delegate to file_validator
  - [ ] Add import: `from ..processing.file_validator import get_supported_extensions, validate_file as validate_file_impl`
  - [ ] Update `__post_init__()` to use `get_supported_extensions()`
  - [ ] Add `supported_extensions_set` property
  - [ ] Update `validate_file()` to delegate to `validate_file_impl()`
  - [ ] Add unit tests for backward compatibility

### Wave 3: Worker Integration

- [ ] **worker-integration-agent**: Update worker_webhook.py
  - [ ] Remove lines 72-74 (module-level config variables)
  - [ ] Add `processing_config` to global variables
  - [ ] Initialize ProcessingConfig in startup_event()
  - [ ] Update extension checks to use `processing_config.supported_extensions_set`
  - [ ] Update logging to use config values
  - [ ] Store config in app.state for endpoint access

- [ ] **worker-integration-agent**: Update worker.py (legacy)
  - [ ] Remove lines 47-49 (module-level config variables)
  - [ ] Add `processing_config` to global variables
  - [ ] Initialize ProcessingConfig in main()
  - [ ] Update extension checks in DocumentUploadHandler
  - [ ] Update glob patterns in process_existing_files()
  - [ ] Update logging to use config values

### Wave 4: Validation

- [ ] **test-agent**: Integration tests
  - [ ] Test ProcessingConfig validation with various file types
  - [ ] Test worker startup with ProcessingConfig
  - [ ] Test file rejection (unsupported types)
  - [ ] Test file rejection (size limits)
  - [ ] Test environment variable overrides
  - [ ] Verify no behavior changes from original implementation

---

## API Compatibility Matrix

### ProcessingConfig API (Before & After)

| Method/Property | Before | After | Compatible? |
|----------------|---------|-------|-------------|
| `__init__()` | Default values from env | Default values from env | ✓ Yes |
| `supported_formats` | `List[str]` (no dots) | `List[str]` (no dots) | ✓ Yes |
| `validate_file(filename, size_bytes)` | `Tuple[bool, str]` | `Tuple[bool, str]` | ✓ Yes |
| `max_file_size_mb` | `int` field | `int` field | ✓ Yes |
| `supported_extensions_set` | N/A | `Set[str]` (NEW) | ✓ New |

**Breaking Changes**: None
**New Features**: `supported_extensions_set` property for set-based lookups

### Worker Global Variables (Before & After)

| Variable | Before | After | Notes |
|----------|---------|-------|-------|
| `SUPPORTED_EXTENSIONS` | Module-level set | Removed | Use `processing_config.supported_extensions_set` |
| `_formats_str` | Module-level string | Removed | Internal parsing moved to config |
| `processing_config` | N/A | Global `ProcessingConfig` | NEW - initialized at startup |

---

## Testing Requirements

### Unit Tests (config-refactor-agent)

**File**: `src/config/test_processing_config.py`

```python
def test_validate_file_delegates_to_file_validator():
    """ProcessingConfig.validate_file() should delegate to file_validator."""
    config = ProcessingConfig()

    # Valid file
    valid, msg = config.validate_file("document.pdf", 1024 * 1024)
    assert valid is True
    assert msg == ""

    # Invalid extension
    valid, msg = config.validate_file("malware.exe", 1024)
    assert valid is False
    assert "Unsupported" in msg

    # Too large
    valid, msg = config.validate_file("huge.pdf", 200 * 1024 * 1024)
    assert valid is False
    assert "exceeds maximum" in msg


def test_supported_formats_backward_compatible():
    """supported_formats should remain a list without dots."""
    config = ProcessingConfig()

    # Should be list of strings without dots
    assert isinstance(config.supported_formats, list)
    assert "pdf" in config.supported_formats
    assert ".pdf" not in config.supported_formats


def test_supported_extensions_set_property():
    """New supported_extensions_set property should return set with dots."""
    config = ProcessingConfig()

    # Should be set with dots
    extensions = config.supported_extensions_set
    assert isinstance(extensions, set)
    assert ".pdf" in extensions
    assert "pdf" not in extensions
```

### Integration Tests (test-agent)

**File**: `src/processing/test_worker_config_integration.py`

```python
def test_worker_webhook_uses_processing_config():
    """worker_webhook should use ProcessingConfig for validation."""
    # Start worker (calls startup_event)
    # Verify processing_config is initialized
    # Verify SUPPORTED_EXTENSIONS is removed
    # Verify extension checks use processing_config
    pass


def test_worker_legacy_uses_processing_config():
    """worker.py should use ProcessingConfig for validation."""
    # Initialize worker main()
    # Verify processing_config is initialized
    # Verify extension validation uses config
    # Verify glob patterns use config
    pass
```

---

## Environment Variable Reference

### Configuration Variables

| Variable | Default | Used By | Purpose |
|----------|---------|---------|---------|
| `SUPPORTED_FORMATS` | `pdf,docx,pptx,...` | file_validator, ProcessingConfig | Comma-separated list of file extensions |
| `MAX_FILE_SIZE_MB` | `100` | ProcessingConfig | Maximum file size in MB |
| `UPLOAD_DIR` | `/uploads` | ProcessingConfig, workers | Upload directory path |
| `TEXT_CHUNK_SIZE` | `250` | ProcessingConfig | Words per text chunk |
| `TEXT_CHUNK_OVERLAP` | `50` | ProcessingConfig | Word overlap between chunks |
| `PAGE_RENDER_DPI` | `150` | ProcessingConfig | DPI for page rendering |
| `WORKER_THREADS` | `1` | ProcessingConfig | Number of parallel workers |
| `ENABLE_QUEUE` | `false` | ProcessingConfig | Enable processing queue |
| `LOG_LEVEL` | `INFO` | ProcessingConfig | Logging level |
| `LOG_FORMAT` | `json` | ProcessingConfig | Logging format |
| `LOG_FILE` | `/data/logs/worker.log` | ProcessingConfig | Log file path |

---

## Benefits of Consolidation

### Code Quality
- **Single Source of Truth**: One validation implementation (file_validator)
- **DRY Principle**: No duplicate format parsing across 4 locations
- **Robust Parsing**: Use Path.suffix instead of manual string splitting
- **Better Error Messages**: Comprehensive error messages from file_validator

### Maintainability
- **Centralized Updates**: Change validation logic in one place
- **Consistent Behavior**: All workers use same validation rules
- **Type Safety**: Proper typing with Tuple[bool, str] return type
- **Testability**: Easier to test centralized configuration

### Configuration Management
- **Runtime Flexibility**: Config loaded at startup, not module import
- **Environment Override**: All config via environment variables
- **Dependency Injection**: Config passed to components explicitly
- **State Management**: Config stored in app.state for FastAPI

---

## Risk Analysis

### Low Risk
- ✓ ProcessingConfig API remains unchanged (backward compatible)
- ✓ No changes to external interfaces (HTTP endpoints)
- ✓ No changes to database schema or storage format
- ✓ Incremental rollout possible (one worker at a time)

### Medium Risk
- ⚠ Workers depend on module-level variables at import time
  - **Mitigation**: Move initialization to startup functions
- ⚠ Tests may rely on module-level variables
  - **Mitigation**: Update test fixtures to use ProcessingConfig

### Testing Requirements
- Unit tests for ProcessingConfig delegation
- Integration tests for worker startup
- Regression tests for file validation behavior
- Environment variable override tests

---

## Dependencies

### Phase 1: Core Refactoring
- **Requires**: `src/processing/file_validator.py` (already exists)
- **Modifies**: `src/config/processing_config.py`
- **Blocks**: Phase 2 (worker integration)

### Phase 2: Worker Integration
- **Requires**: Phase 1 complete
- **Modifies**: `src/processing/worker_webhook.py`, `src/processing/worker.py`
- **Blocks**: None (end of refactoring chain)

---

## Success Criteria

### Phase 1 Complete When:
1. ✓ ProcessingConfig.validate_file() delegates to file_validator
2. ✓ ProcessingConfig.__post_init__() uses get_supported_extensions()
3. ✓ ProcessingConfig.supported_formats remains list (backward compatible)
4. ✓ New property supported_extensions_set returns set with dots
5. ✓ Unit tests pass with 100% coverage
6. ✓ No behavior changes from original implementation

### Phase 2 Complete When:
1. ✓ No module-level SUPPORTED_EXTENSIONS in workers
2. ✓ ProcessingConfig initialized at startup
3. ✓ All extension checks use processing_config
4. ✓ All workers use consistent validation
5. ✓ Integration tests pass
6. ✓ No regressions in file processing

---

## Code Review Checklist

### For config-refactor-agent:
- [ ] ProcessingConfig imports file_validator correctly
- [ ] validate_file() delegates properly with correct parameters
- [ ] supported_formats maintains list format (no dots)
- [ ] supported_extensions_set property returns set with dots
- [ ] All existing tests still pass
- [ ] New tests cover delegation behavior

### For worker-integration-agent:
- [ ] Module-level SUPPORTED_EXTENSIONS removed
- [ ] ProcessingConfig imported and initialized
- [ ] Global processing_config variable declared
- [ ] Startup functions initialize config
- [ ] All extension checks updated to use config
- [ ] Logging uses config values
- [ ] No hardcoded format lists remain
- [ ] Integration tests added and passing

---

## Related Documentation

- **Architecture**: `.context-kit/_context-kit.yml` (configuration patterns)
- **File Validator**: `src/processing/file_validator.py` (shared validation)
- **Processing Config**: `src/config/processing_config.py` (configuration class)
- **Worker Webhook**: `src/processing/worker_webhook.py` (HTTP worker)
- **Worker Legacy**: `src/processing/worker.py` (file system watcher)

---

## Status

**Wave 1**: ✓ Analysis Complete
**Wave 2**: Pending (config-refactor-agent)
**Wave 3**: Pending (worker-integration-agent)
**Wave 4**: Pending (test-agent)

---

**Last Updated**: 2025-10-13
**Reviewed By**: config-analysis-agent
**Next Action**: Assign config-refactor-agent for Wave 2 implementation
