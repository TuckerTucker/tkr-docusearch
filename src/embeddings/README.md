# ColPali Embeddings Module

**Wave 2 Implementation** - Mock API for DocuSearch MVP

This module provides multi-vector embeddings and late interaction scoring using the ColPali architecture. For Wave 2, mock implementations are used to validate the API structure without requiring full ColPali installation.

## Overview

### Architecture

- **Multi-vector embeddings**: Each document/query is represented by a sequence of 768-dim vectors
- **Late interaction**: MaxSim algorithm computes fine-grained similarity between query and document tokens
- **Multimodal**: Supports both visual (images) and text inputs
- **Device-aware**: Automatic fallback from MPS/CUDA to CPU

### Key Features

- ✅ **ColPaliEngine**: Main API for embedding generation and scoring
- ✅ **Image embeddings**: Process document pages as images
- ✅ **Text embeddings**: Process text chunks
- ✅ **Query embeddings**: Fast query processing
- ✅ **MaxSim scoring**: Late interaction scoring algorithm
- ✅ **Device management**: MPS/CUDA/CPU with automatic fallback
- ✅ **Quantization support**: FP16 (default) and INT8 modes
- ✅ **Comprehensive tests**: 29 unit tests with 100% pass rate

## Module Structure

```
src/embeddings/
├── __init__.py              # Module exports
├── colpali_wrapper.py       # Main ColPaliEngine class
├── model_loader.py          # Model initialization and device management
├── scoring.py               # MaxSim algorithm implementation
├── types.py                 # TypedDict definitions
├── exceptions.py            # Exception hierarchy
├── test_embeddings.py       # Unit tests (deprecated - use run_tests.py)
├── run_tests.py             # Test runner (29 tests)
├── example_usage.py         # Usage examples
└── README.md                # This file
```

## Installation

### Wave 2 (Mock Implementation - Current)

No additional dependencies required beyond NumPy and Pillow:

```bash
pip install numpy pillow
```

### Wave 3+ (Production)

For real ColPali integration:

```bash
# Install ColPali from source
pip install git+https://github.com/illuin-tech/colpali.git

# Install dependencies
pip install torch torchvision transformers pillow
```

## Quick Start

### Basic Usage

```python
from embeddings import ColPaliEngine
from PIL import Image

# Initialize engine
engine = ColPaliEngine(device="mps", precision="fp16")

# Embed images
images = [Image.open("page1.png"), Image.open("page2.png")]
image_result = engine.embed_images(images)

# Embed text
texts = ["Revenue increased by 25%.", "Quarterly earnings report."]
text_result = engine.embed_texts(texts)

# Embed query
query = "quarterly revenue"
query_result = engine.embed_query(query)

# Score documents
scores = engine.score_multi_vector(
    query_result['embeddings'],
    image_result['embeddings'] + text_result['embeddings']
)

# Get ranked results
ranked = sorted(enumerate(scores['scores']),
                key=lambda x: x[1], reverse=True)
```

### Custom Configuration

```python
from embeddings import ColPaliEngine
from config import ModelConfig

# Create custom config
config = ModelConfig(
    name="vidore/colqwen2-v0.1",
    device="cpu",           # or "mps", "cuda"
    precision="int8",       # or "fp16"
    batch_size_visual=4,
    batch_size_text=8,
    cache_dir="/models"
)

# Initialize with config
engine = ColPaliEngine(config=config)
```

## API Reference

### ColPaliEngine

Main class for embedding generation and scoring.

#### Methods

**`__init__(model_name, device, precision, cache_dir, quantization, config)`**
- Initialize ColPali model and processor
- Supports custom ModelConfig or individual parameters
- Automatic device fallback if requested device unavailable

**`embed_images(images, batch_size) -> BatchEmbeddingOutput`**
- Generate embeddings for list of PIL Images
- Returns embeddings, CLS tokens, sequence lengths
- Typical sequence length: 80-120 tokens per image

**`embed_texts(texts, batch_size) -> BatchEmbeddingOutput`**
- Generate embeddings for list of text strings
- Returns embeddings, CLS tokens, sequence lengths
- Typical sequence length: 50-80 tokens per chunk

**`embed_query(query) -> EmbeddingOutput`**
- Generate embedding for single search query
- Fast processing (<100ms for typical queries)
- Typical sequence length: 10-30 tokens

**`score_multi_vector(query_embeddings, document_embeddings, use_gpu) -> ScoringOutput`**
- Compute MaxSim scores for query vs documents
- Returns normalized scores in [0, 1] range
- Higher scores = better match

**`get_model_info() -> Dict`**
- Get model configuration and status
- Returns device, memory, quantization info

**`clear_cache()`**
- Clear GPU memory cache
- Useful between large batches

### Type Definitions

**`EmbeddingOutput`**
```python
{
    "embeddings": np.ndarray,        # (seq_length, 768)
    "cls_token": np.ndarray,         # (768,)
    "seq_length": int,
    "input_type": str,               # "visual" or "text"
    "processing_time_ms": float
}
```

**`BatchEmbeddingOutput`**
```python
{
    "embeddings": List[np.ndarray],  # List of (seq_length, 768)
    "cls_tokens": np.ndarray,        # (batch_size, 768)
    "seq_lengths": List[int],
    "input_type": str,
    "batch_processing_time_ms": float
}
```

**`ScoringOutput`**
```python
{
    "scores": List[float],           # [0, 1] range
    "scoring_time_ms": float,
    "num_candidates": int
}
```

### Exceptions

- `EmbeddingError`: Base exception
- `ModelLoadError`: Model loading failed
- `DeviceError`: Device unavailable
- `EmbeddingGenerationError`: Embedding computation failed
- `ScoringError`: Scoring failed
- `QuantizationError`: Quantization failed

## Testing

### Run All Tests

```bash
cd src/embeddings
python3 run_tests.py
```

Expected output:
```
Ran 29 tests in 0.3s
OK

Tests run: 29
Failures: 0
Errors: 0
Success rate: 100.0%
```

### Test Coverage

- ✅ Model loading and initialization (4 tests)
- ✅ Image embedding (4 tests)
- ✅ Text embedding (5 tests)
- ✅ Query embedding (3 tests)
- ✅ Late interaction scoring (5 tests)
- ✅ Embedding validation (4 tests)
- ✅ Error handling (2 tests)
- ✅ Configuration edge cases (2 tests)

## Examples

See `example_usage.py` for comprehensive examples:

```bash
cd src/embeddings
python3 example_usage.py
```

Examples cover:
1. Basic initialization
2. Custom configuration
3. Image embedding
4. Text embedding
5. Query embedding
6. Late interaction scoring
7. End-to-end workflow

## Performance Characteristics

### Wave 2 (Mock Implementation)

- Image embedding: ~1ms per image
- Text embedding: ~1ms per chunk
- Query embedding: <10ms
- Scoring: <1ms per document

### Wave 3+ (Production - ColPali)

**FP16 (Best Quality)**:
- Image: ~6s per image on M1
- Text: ~6s per chunk on M1
- Memory: ~14GB

**INT8 (2x Faster)**:
- Image: ~3s per image on M1
- Text: ~3s per chunk on M1
- Memory: ~7GB

**Scoring**:
- ~1ms per document on M1 GPU
- 100 documents: ~100ms

## Integration with Other Modules

### With Processing Module

```python
# processing-agent will call:
from embeddings import ColPaliEngine

engine = ColPaliEngine(precision="int8")
embeddings = engine.embed_images(pdf_pages)
```

### With Search Module

```python
# search-agent will call:
from embeddings import ColPaliEngine

engine = ColPaliEngine()
query_emb = engine.embed_query(user_query)
scores = engine.score_multi_vector(query_emb['embeddings'], doc_embeddings)
```

### With Storage Module

```python
# Store embeddings in ChromaDB:
# - Use CLS tokens as primary vectors
# - Store full multi-vectors as metadata
# - Use MaxSim for re-ranking
```

## Wave 2 Limitations

Current mock implementation:

- ✅ **Complete API structure** matching integration contract
- ✅ **Correct output shapes** (seq_length, 768)
- ✅ **Realistic sequence lengths** (visual: 80-120, text: 50-80)
- ✅ **Working MaxSim algorithm** with normalized scores
- ❌ **Random embeddings** (not semantically meaningful)
- ❌ **No actual model** (ColPali not loaded)

## Wave 3+ Roadmap

For production deployment:

1. **Install ColPali**: `pip install git+https://github.com/illuin-tech/colpali.git`
2. **Replace mock model**: Update `model_loader.py` to load real ColQwen2_5
3. **Test with real data**: Validate on sample PDFs
4. **Optimize batching**: Tune batch sizes for hardware
5. **Enable caching**: Keep model loaded in daemon mode
6. **Add async support**: For concurrent processing

## Configuration

### Environment Variables

```bash
# Model configuration
MODEL_NAME="vidore/colqwen2-v0.1"
MODEL_PRECISION="fp16"  # or "int8"
DEVICE="mps"            # or "cuda", "cpu"

# Batch sizes
BATCH_SIZE_VISUAL=4
BATCH_SIZE_TEXT=8

# Model cache
MODELS_CACHE="/models"
TRANSFORMERS_CACHE="/models"
HF_HOME="/models"

# PyTorch settings
PYTORCH_ENABLE_MPS_FALLBACK=1
```

### ModelConfig Defaults

```python
ModelConfig(
    name="vidore/colqwen2-v0.1",
    device="mps",
    precision="fp16",
    batch_size_visual=4,
    batch_size_text=8,
    cache_dir="/models",
    auto_fallback=True
)
```

## Troubleshooting

### Import Errors

If you get import errors, ensure the src directory is in your Python path:

```python
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
```

### Device Issues

If MPS/CUDA unavailable, engine will automatically fallback to CPU. Check logs:

```
Warning: Requested device 'cuda' not available, falling back to CPU
```

### Memory Issues

For low-memory systems, use INT8 quantization:

```python
engine = ColPaliEngine(precision="int8")  # Uses ~7GB instead of 14GB
```

## Contributing

When extending this module:

1. **Maintain API compatibility**: Don't break the integration contract
2. **Add tests**: All new functions must have unit tests
3. **Update docs**: Keep this README current
4. **Follow conventions**: PEP 8, type hints, docstrings (Google style)
5. **Log appropriately**: Use logging module, not print()

## License

Part of the DocuSearch MVP project.

## Contact

For questions or issues, contact the DocuSearch team.

---

**Last Updated**: 2025-10-06
**Version**: 1.0.0 (Wave 2)
**Status**: Mock Implementation - API Complete ✅
