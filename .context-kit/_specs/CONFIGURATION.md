# Configuration and File Validation Documentation

## Overview

This document provides comprehensive documentation for the DocuSearch configuration system and file validation utilities. The configuration architecture follows Inversion of Control (IoC) principles with centralized configuration management and reusable validation modules.

## Table of Contents

1. [Environment Variables](#environment-variables)
2. [ProcessingConfig API](#processingconfig-api)
3. [file_validator API](#file_validator-api)
4. [EnhancedModeConfig API](#enhancedmodeconfig-api)
5. [AsrConfig API](#asrconfig-api)
6. [Migration Guide](#migration-guide)

---

## Environment Variables

All configuration can be controlled via environment variables. This enables flexible deployment across different environments without code changes.

### File Handling

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MAX_FILE_SIZE_MB` | int | `100` | Maximum file size in megabytes |
| `SUPPORTED_FORMATS` | string | `pdf,docx,pptx,xlsx,html,xhtml,md,asciidoc,csv,mp3,wav,vtt,png,jpg,jpeg,tiff,bmp,webp` | Comma-separated list of supported file extensions |
| `UPLOAD_DIR` | string | `/uploads` | Directory for uploaded files |

### Text Processing

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `TEXT_CHUNK_SIZE` | int | `250` | Average words per text chunk |
| `TEXT_CHUNK_OVERLAP` | int | `50` | Word overlap between chunks |

### Visual Processing

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `PAGE_RENDER_DPI` | int | `150` | DPI for page rendering |

### Worker Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `WORKER_THREADS` | int | `1` | Number of parallel workers |
| `ENABLE_QUEUE` | bool | `false` | Enable processing queue (use `true`/`false`) |

### Logging

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LOG_LEVEL` | string | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |
| `LOG_FORMAT` | string | `json` | Logging format (`json` or `text`) |
| `LOG_FILE` | string | `/data/logs/worker.log` | Log file path |

### Enhanced Mode (Docling)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENABLE_TABLE_STRUCTURE` | bool | `true` | Enable table structure recognition with TableFormer |
| `ENABLE_PICTURE_CLASSIFICATION` | bool | `true` | Enable image type classification |
| `ENABLE_CODE_ENRICHMENT` | bool | `false` | Enable code block language detection (slower) |
| `ENABLE_FORMULA_ENRICHMENT` | bool | `false` | Enable formula LaTeX extraction (slower) |
| `CHUNKING_STRATEGY` | string | `hybrid` | Text chunking strategy (`legacy` or `hybrid`) |
| `MAX_CHUNK_TOKENS` | int | `512` | Maximum tokens per chunk (100-4096) |
| `MIN_CHUNK_TOKENS` | int | `100` | Minimum tokens per chunk (10-1000) |
| `MERGE_PEER_CHUNKS` | bool | `true` | Merge adjacent small chunks with same headings |
| `TABLE_STRUCTURE_MODE` | string | `accurate` | TableFormer mode (`fast` or `accurate`) |
| `IMAGES_SCALE` | float | `2.0` | Image generation scale factor (0.5-4.0) |

### ASR (Automatic Speech Recognition)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ASR_ENABLED` | bool | `true` | Enable ASR processing |
| `ASR_MODEL` | string | `turbo` | Whisper model (`turbo`, `base`, `small`, `medium`, `large`) |
| `ASR_LANGUAGE` | string | `en` | Language code (ISO 639-1) or `auto` for detection |
| `ASR_DEVICE` | string | `mps` | Compute device (`mps`, `cpu`, `cuda`) |
| `ASR_WORD_TIMESTAMPS` | bool | `true` | Enable word-level timestamps |
| `ASR_TEMPERATURE` | float | `0.0` | Sampling temperature (0.0-1.0, lower = more deterministic) |
| `ASR_MAX_TIME_CHUNK` | float | `30.0` | Maximum audio chunk duration in seconds |

### Example Configuration

```bash
# File handling
export MAX_FILE_SIZE_MB=200
export SUPPORTED_FORMATS="pdf,docx,pptx,png,jpg"
export UPLOAD_DIR="/data/uploads"

# Text processing
export TEXT_CHUNK_SIZE=300
export TEXT_CHUNK_OVERLAP=75

# Visual processing
export PAGE_RENDER_DPI=200

# Worker configuration
export WORKER_THREADS=4
export ENABLE_QUEUE=true

# Logging
export LOG_LEVEL=DEBUG
export LOG_FORMAT=json
export LOG_FILE="/var/log/docusearch/worker.log"

# Enhanced mode
export ENABLE_TABLE_STRUCTURE=true
export ENABLE_PICTURE_CLASSIFICATION=true
export CHUNKING_STRATEGY=hybrid
export MAX_CHUNK_TOKENS=512

# ASR
export ASR_ENABLED=true
export ASR_MODEL=turbo
export ASR_LANGUAGE=auto
```

---

## ProcessingConfig API

The `ProcessingConfig` class provides centralized configuration for document processing. All settings can be overridden via environment variables.

### Import

```python
from src.config.processing_config import ProcessingConfig
```

### Initialization

```python
# Initialize with defaults from environment
config = ProcessingConfig()

# Access configuration values
print(config.max_file_size_mb)  # 100
print(config.supported_formats)  # ['pdf', 'docx', 'pptx', ...]
print(config.chunk_size_words)   # 250
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `max_file_size_mb` | int | Maximum file size in MB |
| `supported_formats` | List[str] | List of supported file extensions (lowercase, no dots) |
| `upload_dir` | str | Directory for uploaded files |
| `chunk_size_words` | int | Average words per text chunk |
| `chunk_overlap_words` | int | Word overlap between chunks |
| `page_render_dpi` | int | DPI for page rendering |
| `worker_threads` | int | Number of parallel workers |
| `enable_queue` | bool | Enable processing queue |
| `log_level` | str | Logging level |
| `log_format` | str | Logging format |
| `log_file` | str | Log file path |

### Methods

#### `validate_file(filename: str, size_bytes: int) -> Tuple[bool, str]`

Validate uploaded file using the centralized file_validator module.

**Parameters:**
- `filename` (str): Name of the uploaded file
- `size_bytes` (int): File size in bytes

**Returns:**
- `Tuple[bool, str]`: `(is_valid, error_message)`
  - `(True, "")` if validation passes
  - `(False, "error message")` if validation fails

**Example:**
```python
config = ProcessingConfig()

# Validate a file
valid, error = config.validate_file("document.pdf", 1024 * 1024)  # 1 MB
if valid:
    print("File is valid")
else:
    print(f"Validation error: {error}")

# Example failures
valid, error = config.validate_file("file.exe", 1024)
# Returns: (False, "Unsupported file type: .exe. Supported: ...")

valid, error = config.validate_file("huge.pdf", 200 * 1024 * 1024)  # 200 MB
# Returns: (False, "File size 200.00 MB exceeds maximum 100 MB")
```

### Properties

#### `supported_extensions_set -> Set[str]`

Get supported file extensions as a set with dot prefix.

**Returns:**
- `Set[str]`: Extensions like `{'.pdf', '.docx', '.png', ...}`

**Example:**
```python
config = ProcessingConfig()

extensions = config.supported_extensions_set
print('.pdf' in extensions)  # True
print('.exe' in extensions)  # False
```

#### `max_file_size_bytes -> int`

Get maximum file size in bytes.

**Returns:**
- `int`: Maximum file size in bytes

**Example:**
```python
config = ProcessingConfig()

max_bytes = config.max_file_size_bytes
print(max_bytes)  # 104857600 (100 MB)
```

#### `chunk_overlap_ratio -> float`

Get chunk overlap as ratio of chunk size.

**Returns:**
- `float`: Overlap ratio (0.0 to 1.0)

**Example:**
```python
config = ProcessingConfig()

ratio = config.chunk_overlap_ratio
print(ratio)  # 0.2 (50/250)
```

#### `to_dict() -> dict`

Convert configuration to dictionary.

**Returns:**
- `dict`: Configuration as dictionary

**Example:**
```python
config = ProcessingConfig()

config_dict = config.to_dict()
print(config_dict)
# {
#     'max_file_size_mb': 100,
#     'max_file_size_bytes': 104857600,
#     'supported_formats': ['pdf', 'docx', ...],
#     'upload_dir': '/uploads',
#     'chunk_size_words': 250,
#     'chunk_overlap_words': 50,
#     'chunk_overlap_ratio': 0.2,
#     'page_render_dpi': 150,
#     'worker_threads': 1,
#     'enable_queue': False,
#     'log_level': 'INFO',
#     'log_format': 'json'
# }
```

---

## file_validator API

The `file_validator` module provides shared validation functions for file type and size checks. This eliminates duplicate validation code across workers.

### Import

```python
from src.processing.file_validator import (
    validate_file,
    validate_file_type,
    validate_file_size,
    get_supported_extensions
)
```

### Constants

#### `DEFAULT_FORMATS`

Default supported file formats (comma-separated string).

**Value:**
```python
"pdf,docx,pptx,xlsx,html,xhtml,md,asciidoc,csv,mp3,wav,vtt,png,jpg,jpeg,tiff,bmp,webp"
```

### Functions

#### `get_supported_extensions() -> Set[str]`

Load supported file extensions from environment.

Reads the `SUPPORTED_FORMATS` environment variable and returns a set of extensions with dot prefix for easy validation.

**Returns:**
- `Set[str]`: Extensions with dot prefix (e.g., `{'.pdf', '.png'}`)

**Example:**
```python
exts = get_supported_extensions()
print(exts)
# {'.pdf', '.docx', '.pptx', '.png', '.jpg', ...}

if '.pdf' in exts:
    print("PDF files are supported")
```

#### `validate_file_type(file_path: str) -> Tuple[bool, str]`

Validate file extension against supported formats.

**Parameters:**
- `file_path` (str): Path to file (can be absolute or relative)

**Returns:**
- `Tuple[bool, str]`: `(is_valid, error_message)`
  - `(True, "")` if file type is supported
  - `(False, "error message")` if file type is not supported

**Example:**
```python
# Valid file
valid, msg = validate_file_type("document.pdf")
print(valid)  # True
print(msg)    # ""

# Unsupported extension
valid, msg = validate_file_type("file.exe")
print(valid)  # False
print(msg)    # "Unsupported file type: .exe. Supported: .csv, .docx, ..."

# No extension
valid, msg = validate_file_type("README")
print(valid)  # False
print(msg)    # "File has no extension: README"
```

#### `validate_file_size(size_bytes: int, max_mb: int = 100) -> Tuple[bool, str]`

Validate file size against limit.

**Parameters:**
- `size_bytes` (int): File size in bytes
- `max_mb` (int, optional): Maximum size in MB (default: 100)

**Returns:**
- `Tuple[bool, str]`: `(is_valid, error_message)`
  - `(True, "")` if file size is within limit
  - `(False, "error message")` if file size exceeds limit

**Example:**
```python
# Valid size (1 MB)
valid, msg = validate_file_size(1024 * 1024)
print(valid)  # True
print(msg)    # ""

# Exceeds limit (200 MB)
valid, msg = validate_file_size(200 * 1024 * 1024)
print(valid)  # False
print(msg)    # "File size 200.00 MB exceeds maximum 100 MB"

# Custom limit (50 MB)
valid, msg = validate_file_size(60 * 1024 * 1024, max_mb=50)
print(valid)  # False
print(msg)    # "File size 60.00 MB exceeds maximum 50 MB"

# Invalid size
valid, msg = validate_file_size(-1)
print(valid)  # False
print(msg)    # "Invalid file size: -1 bytes"
```

#### `validate_file(file_path: str, size_bytes: int, max_mb: int = 100) -> Tuple[bool, str]`

Complete file validation (type + size).

Performs both file type and size validation. Returns on first failure.

**Parameters:**
- `file_path` (str): Path to file (can be absolute or relative)
- `size_bytes` (int): File size in bytes
- `max_mb` (int, optional): Maximum size in MB (default: 100)

**Returns:**
- `Tuple[bool, str]`: `(is_valid, error_message)`
  - `(True, "")` if all validations pass
  - `(False, "error message")` if any validation fails

**Example:**
```python
# Valid file
valid, msg = validate_file("document.pdf", 1024 * 1024)
print(valid)  # True
print(msg)    # ""

# Unsupported type
valid, msg = validate_file("file.exe", 1024)
print(valid)  # False
print(msg)    # "Unsupported file type: .exe. Supported: ..."

# Size exceeds limit
valid, msg = validate_file("huge.pdf", 200 * 1024 * 1024)
print(valid)  # False
print(msg)    # "File size 200.00 MB exceeds maximum 100 MB"

# Custom max size
valid, msg = validate_file("doc.pdf", 5 * 1024 * 1024, max_mb=2)
print(valid)  # False
print(msg)    # "File size 5.00 MB exceeds maximum 2 MB"
```

---

## EnhancedModeConfig API

Configuration for Docling enhanced mode features (table structure, picture classification, chunking, etc.).

### Import

```python
from src.config.processing_config import EnhancedModeConfig, ChunkingStrategy
```

### ChunkingStrategy Enum

```python
class ChunkingStrategy(Enum):
    LEGACY = "legacy"  # Word-based sliding window
    HYBRID = "hybrid"  # Document-aware hybrid chunker (recommended)
```

### Initialization

```python
# Load from environment variables
config = EnhancedModeConfig.from_env()

# Create with defaults
config = EnhancedModeConfig()

# Create with custom values
config = EnhancedModeConfig(
    enable_table_structure=True,
    enable_picture_classification=True,
    chunking_strategy=ChunkingStrategy.HYBRID,
    max_chunk_tokens=512,
    min_chunk_tokens=100
)
```

### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_table_structure` | bool | `True` | Enable table structure recognition with TableFormer |
| `enable_picture_classification` | bool | `True` | Enable image type classification |
| `enable_code_enrichment` | bool | `False` | Enable code block language detection (slower) |
| `enable_formula_enrichment` | bool | `False` | Enable formula LaTeX extraction (slower) |
| `chunking_strategy` | ChunkingStrategy | `HYBRID` | Text chunking strategy |
| `max_chunk_tokens` | int | `512` | Maximum tokens per chunk (100-4096) |
| `min_chunk_tokens` | int | `100` | Minimum tokens per chunk (10-1000) |
| `merge_peer_chunks` | bool | `True` | Merge adjacent small chunks with same headings |
| `table_structure_mode` | str | `"accurate"` | TableFormer mode (`"fast"` or `"accurate"`) |
| `images_scale` | float | `2.0` | Image generation scale factor (0.5-4.0) |
| `generate_page_images` | bool | `True` | Generate full page images |
| `generate_picture_images` | bool | `True` | Generate individual picture images |
| `max_structure_size_kb` | int | `100` | Maximum size of structure metadata |

### Methods

#### `from_env() -> EnhancedModeConfig` (classmethod)

Load configuration from environment variables with validation.

**Returns:**
- `EnhancedModeConfig`: Configuration instance loaded from environment

**Example:**
```python
import os

# Set environment variables
os.environ["ENABLE_TABLE_STRUCTURE"] = "true"
os.environ["CHUNKING_STRATEGY"] = "hybrid"
os.environ["MAX_CHUNK_TOKENS"] = "512"

# Load configuration
config = EnhancedModeConfig.from_env()
print(config.enable_table_structure)  # True
print(config.chunking_strategy)       # ChunkingStrategy.HYBRID
print(config.max_chunk_tokens)        # 512
```

---

## AsrConfig API

Configuration for Automatic Speech Recognition (Whisper) for audio file transcription.

### Import

```python
from src.config.processing_config import AsrConfig
```

### Initialization

```python
# Load from environment variables
config = AsrConfig.from_env()

# Create with defaults
config = AsrConfig()

# Create with custom values
config = AsrConfig(
    enabled=True,
    model="turbo",
    language="en",
    device="mps",
    word_timestamps=True,
    temperature=0.0,
    max_time_chunk=30.0
)
```

### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | bool | `True` | Whether ASR processing is enabled |
| `model` | str | `"turbo"` | Whisper model (`turbo`, `base`, `small`, `medium`, `large`) |
| `language` | str | `"en"` | Language code (ISO 639-1) or `"auto"` for detection |
| `device` | str | `"mps"` | Compute device (`mps`, `cpu`, `cuda`) |
| `word_timestamps` | bool | `True` | Enable word-level timestamps |
| `temperature` | float | `0.0` | Sampling temperature (0.0-1.0, lower = more deterministic) |
| `max_time_chunk` | float | `30.0` | Maximum audio chunk duration in seconds |

### Methods

#### `from_env() -> AsrConfig` (classmethod)

Load configuration from environment variables with validation.

**Returns:**
- `AsrConfig`: Configuration instance loaded from environment

**Example:**
```python
import os

# Set environment variables
os.environ["ASR_ENABLED"] = "true"
os.environ["ASR_MODEL"] = "turbo"
os.environ["ASR_LANGUAGE"] = "auto"

# Load configuration
config = AsrConfig.from_env()
print(config.enabled)   # True
print(config.model)     # "turbo"
print(config.language)  # "auto"
```

#### `to_docling_model_spec()`

Convert to Docling ASR model specification.

**Returns:**
- `InlineAsrNativeWhisperOptions`: Docling ASR options configured for Whisper

**Raises:**
- `ImportError`: If Docling ASR modules not available

**Example:**
```python
config = AsrConfig(model="turbo", language="en")
asr_options = config.to_docling_model_spec()
# Use with Docling pipeline
```

#### `to_dict() -> dict`

Convert configuration to dictionary.

**Returns:**
- `dict`: Configuration as dictionary

**Example:**
```python
config = AsrConfig()
config_dict = config.to_dict()
print(config_dict)
# {
#     'enabled': True,
#     'model': 'turbo',
#     'language': 'en',
#     'device': 'mps',
#     'word_timestamps': True,
#     'temperature': 0.0,
#     'max_time_chunk': 30.0
# }
```

---

## Migration Guide

### Migrating from Hardcoded Validation to Centralized Configuration

#### Before (Hardcoded Patterns)

```python
# worker.py (OLD PATTERN)
SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.pptx', '.png']
MAX_FILE_SIZE_MB = 100

def validate_upload(file_path, file_size):
    ext = Path(file_path).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return False, f"Unsupported: {ext}"

    if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        return False, f"Too large"

    return True, ""
```

#### After (Centralized Configuration)

```python
# worker.py (NEW PATTERN)
from src.config.processing_config import ProcessingConfig
from src.processing.file_validator import validate_file

config = ProcessingConfig()

def validate_upload(file_path, file_size):
    # Use centralized validator
    return validate_file(file_path, file_size, config.max_file_size_mb)

# Or use config method
def validate_upload_v2(filename, file_size):
    return config.validate_file(filename, file_size)
```

### FastAPI Integration Example

```python
from fastapi import FastAPI, UploadFile, HTTPException
from src.config.processing_config import ProcessingConfig

app = FastAPI()
config = ProcessingConfig()

@app.post("/upload")
async def upload_document(file: UploadFile):
    # Get file size
    contents = await file.read()
    file_size = len(contents)

    # Validate using centralized config
    valid, error = config.validate_file(file.filename, file_size)
    if not valid:
        raise HTTPException(status_code=400, detail=error)

    # Process file...
    return {"message": "Upload successful"}
```

### Regular Python Integration Example

```python
from pathlib import Path
from src.processing.file_validator import validate_file

def process_document(file_path: str):
    """Process a document with validation."""
    path = Path(file_path)

    # Check file exists
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Validate file type and size
    file_size = path.stat().st_size
    valid, error = validate_file(str(path), file_size)

    if not valid:
        raise ValueError(f"Invalid file: {error}")

    # Process document...
    print(f"Processing {path.name}...")
```

### Migration Checklist

- [ ] Replace hardcoded `SUPPORTED_EXTENSIONS` lists with `get_supported_extensions()`
- [ ] Replace hardcoded `MAX_FILE_SIZE_MB` with `ProcessingConfig.max_file_size_mb`
- [ ] Replace custom validation functions with `validate_file()`, `validate_file_type()`, or `validate_file_size()`
- [ ] Use `ProcessingConfig.validate_file()` for convenience method that integrates both
- [ ] Update tests to use centralized validation
- [ ] Set environment variables instead of changing code for configuration
- [ ] Remove duplicate validation code from workers

### Benefits of Migration

1. **Single Source of Truth**: All validation logic in one place
2. **Environment-Based Configuration**: No code changes needed for different deployments
3. **Consistency**: Same validation behavior across all workers
4. **Maintainability**: Fix bugs once, benefit everywhere
5. **Testability**: Easier to test centralized validation
6. **Flexibility**: Easy to add new formats or change limits via environment variables

---

## See Also

- [file-validator-usage.md](./file-validator-usage.md) - Practical usage examples and patterns
- [enhanced_mode_config.md](./enhanced_mode_config.md) - Detailed Docling enhanced mode documentation
- [TECHNICAL_DEBT.md](./TECHNICAL_DEBT.md) - Technical debt resolution tracking
