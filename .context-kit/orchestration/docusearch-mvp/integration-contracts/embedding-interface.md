# Embedding Interface Contract

**Owner**: embedding-agent
**Consumers**: processing-agent, search-agent
**Purpose**: Define ColPali engine wrapper for multi-vector embedding generation and late interaction scoring

---

## Model Specification

### ColNomic 7B (ColQwen2_5)

- **Model ID**: `nomic-ai/colnomic-embed-multimodal-7b`
- **Architecture**: ColBERT-style multi-vector embeddings
- **Parameters**: 7 billion
- **Context Length**: 32,768 tokens
- **Embedding Dimension**: 768
- **Output**: Variable-length sequence of 768-dim vectors (one per token)

### Installation Requirements

```bash
# Install ColPali engine from source (required)
pip install git+https://github.com/illuin-tech/colpali.git

# Dependencies
pip install torch torchvision transformers pillow
```

### Model Loading

```python
from colpali_engine.models import ColQwen2_5, ColQwen2_5_Processor
import torch

model_name = "nomic-ai/colnomic-embed-multimodal-7b"

# Load model with Apple Silicon optimization
model = ColQwen2_5.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,  # or torch.float16 for INT8
    device_map="mps",  # Apple Silicon GPU
    attn_implementation=None,  # flash_attention_2 not available on MPS
).eval()

# Load processor
processor = ColQwen2_5_Processor.from_pretrained(model_name)
```

---

## Data Structures

### Input Types

```python
from PIL import Image
from typing import List, Union

# Visual inputs
ImageInput = Union[Image.Image, str]  # PIL Image or file path
ImageBatch = List[ImageInput]

# Text inputs
TextInput = str
TextBatch = List[TextInput]
```

### Output Types

```python
import numpy as np
from typing import TypedDict

class EmbeddingOutput(TypedDict):
    """Multi-vector embedding output."""
    embeddings: np.ndarray           # Shape: (seq_length, 768)
    cls_token: np.ndarray            # Shape: (768,) - representative vector
    seq_length: int                  # Number of tokens
    input_type: str                  # "visual" or "text"
    processing_time_ms: float        # Embedding generation time

class BatchEmbeddingOutput(TypedDict):
    """Batch embedding output."""
    embeddings: List[np.ndarray]     # List of (seq_length, 768) arrays
    cls_tokens: np.ndarray           # Shape: (batch_size, 768)
    seq_lengths: List[int]           # Token counts for each item
    input_type: str                  # "visual" or "text"
    batch_processing_time_ms: float  # Total batch time

class ScoringOutput(TypedDict):
    """Late interaction scoring output."""
    scores: List[float]              # MaxSim scores (0-1 range)
    scoring_time_ms: float           # Time for re-ranking
    num_candidates: int              # Number of documents scored
```

---

## API Interface

### ColPaliEngine Class

```python
from typing import List, Dict, Any, Optional
import torch
import numpy as np
from PIL import Image

class ColPaliEngine:
    """ColPali engine wrapper for multi-vector embeddings and late interaction."""

    def __init__(
        self,
        model_name: str = "nomic-ai/colnomic-embed-multimodal-7b",
        device: str = "mps",  # "mps", "cuda", or "cpu"
        dtype: torch.dtype = torch.bfloat16,  # or torch.float16 for INT8
        cache_dir: str = "/models",
        quantization: Optional[str] = None  # None, "int8"
    ):
        """
        Initialize ColPali model and processor.

        Args:
            model_name: HuggingFace model identifier
            device: Target device (mps for M1, cuda for NVIDIA, cpu for fallback)
            dtype: Model precision (bfloat16 for FP16, float16 for INT8)
            cache_dir: Directory for model caching
            quantization: Quantization mode (None, "int8")

        Raises:
            ModelLoadError: If model loading fails
            DeviceError: If requested device unavailable
        """
        pass

    def embed_images(
        self,
        images: List[Image.Image],
        batch_size: int = 4
    ) -> BatchEmbeddingOutput:
        """
        Generate multi-vector embeddings for image batch.

        Args:
            images: List of PIL Images (document pages)
            batch_size: Number of images to process at once

        Returns:
            BatchEmbeddingOutput with:
            - embeddings: List of (seq_length, 768) arrays
            - cls_tokens: (batch_size, 768) representative vectors
            - seq_lengths: Token counts (typically 80-120 per page)
            - input_type: "visual"

        Raises:
            ValueError: If images list is empty
            EmbeddingError: If embedding generation fails

        Performance:
            FP16: ~6s per image on M1
            INT8: ~3s per image on M1
        """
        pass

    def embed_texts(
        self,
        texts: List[str],
        batch_size: int = 8
    ) -> BatchEmbeddingOutput:
        """
        Generate multi-vector embeddings for text batch.

        Args:
            texts: List of text chunks (avg 250 words)
            batch_size: Number of texts to process at once

        Returns:
            BatchEmbeddingOutput with:
            - embeddings: List of (seq_length, 768) arrays
            - cls_tokens: (batch_size, 768) representative vectors
            - seq_lengths: Token counts (typically 50-80 per chunk)
            - input_type: "text"

        Raises:
            ValueError: If texts list is empty
            EmbeddingError: If embedding generation fails

        Performance:
            FP16: ~6s per chunk on M1
            INT8: ~3s per chunk on M1
        """
        pass

    def embed_query(
        self,
        query: str
    ) -> EmbeddingOutput:
        """
        Generate multi-vector embedding for search query.

        Args:
            query: Natural language search query

        Returns:
            EmbeddingOutput with:
            - embeddings: (seq_length, 768) multi-vector
            - cls_token: (768,) representative vector
            - seq_length: Query token count (typically 10-30)
            - input_type: "text"

        Raises:
            ValueError: If query is empty
            EmbeddingError: If embedding generation fails

        Performance:
            <100ms for typical queries on M1
        """
        pass

    def score_multi_vector(
        self,
        query_embeddings: np.ndarray,
        document_embeddings: List[np.ndarray],
        use_gpu: bool = True
    ) -> ScoringOutput:
        """
        Late interaction scoring using MaxSim algorithm.

        Computes maximum similarity between each query token and all document
        tokens, then sums across query tokens.

        Args:
            query_embeddings: Query multi-vector, shape (query_tokens, 768)
            document_embeddings: List of document multi-vectors, each (doc_tokens, 768)
            use_gpu: Use GPU for scoring (faster)

        Returns:
            ScoringOutput with:
            - scores: List of MaxSim scores (0-1 range, higher = better match)
            - scoring_time_ms: Time to score all documents
            - num_candidates: len(document_embeddings)

        Algorithm:
            For each document:
                score = sum over query_tokens of max(cosine_sim(q_token, d_token))

        Raises:
            ValueError: If embedding shapes incompatible
            ScoringError: If scoring computation fails

        Performance:
            ~1ms per document on M1 GPU
            100 documents: ~100ms total
        """
        pass

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model configuration and status.

        Returns:
            {
                "model_name": str,
                "device": str,
                "dtype": str,
                "quantization": Optional[str],
                "memory_allocated_mb": float,
                "is_loaded": bool,
                "cache_dir": str
            }
        """
        pass

    def clear_cache(self):
        """
        Clear GPU memory cache (useful between large batches).

        For MPS (M1):
            torch.mps.empty_cache()
        For CUDA:
            torch.cuda.empty_cache()
        """
        pass
```

---

## Multi-Vector Embedding Format

### Structure

```python
# Single embedding output
{
    "embeddings": np.ndarray([
        [0.234, -0.567, ...],  # Token 0 (CLS token)
        [0.123, 0.456, ...],   # Token 1
        [0.789, -0.234, ...],  # Token 2
        # ... more tokens
        [-0.456, 0.789, ...]   # Token N
    ]),  # Shape: (seq_length, 768)

    "cls_token": np.ndarray([0.234, -0.567, ...]),  # Shape: (768,)
    "seq_length": 100,  # Varies by input
    "input_type": "visual",  # or "text"
    "processing_time_ms": 6234.5
}
```

### Token Sequence Lengths

| Input Type | Typical Range | Average | Max |
|------------|---------------|---------|-----|
| **Visual (page image)** | 80-120 tokens | 100 | 150 |
| **Text (250 words)** | 50-80 tokens | 64 | 100 |
| **Query (search)** | 10-30 tokens | 20 | 50 |

---

## Late Interaction Scoring (MaxSim)

### Algorithm

```python
def maxsim_score(
    query_embeddings: np.ndarray,  # (Q, 768)
    doc_embeddings: np.ndarray     # (D, 768)
) -> float:
    """
    Compute MaxSim score between query and document.

    For each query token:
        Find max cosine similarity with any document token
    Sum these max similarities across all query tokens

    Returns:
        Score in range [0, Q] where Q = num query tokens
        Normalized to [0, 1] by dividing by Q
    """
    Q, _ = query_embeddings.shape
    D, _ = doc_embeddings.shape

    # Normalize embeddings
    query_norm = query_embeddings / np.linalg.norm(query_embeddings, axis=1, keepdims=True)
    doc_norm = doc_embeddings / np.linalg.norm(doc_embeddings, axis=1, keepdims=True)

    # Compute similarity matrix (Q x D)
    similarity_matrix = np.matmul(query_norm, doc_norm.T)

    # MaxSim: max over doc tokens for each query token, then sum
    max_similarities = np.max(similarity_matrix, axis=1)  # (Q,)
    score = np.sum(max_similarities)

    # Normalize by query length
    normalized_score = score / Q

    return float(normalized_score)
```

### Example Scores

```python
# Query: "quarterly revenue growth"
# Document 1: Financial report with "revenue" and "growth" in text
#   → Score: 0.92 (high - exact keyword matches)

# Document 2: Chart showing revenue trends (visual)
#   → Score: 0.85 (high - visual similarity to "growth" concept)

# Document 3: Unrelated legal document
#   → Score: 0.34 (low - no semantic match)
```

---

## Performance Characteristics

### Embedding Generation

**FP16 (Default - Best Quality)**:
```
Single image:  ~6s on M1
Batch of 4:    ~20s (5s per image avg)
Single text:   ~6s on M1
Batch of 8:    ~40s (5s per chunk avg)
```

**INT8 (Quantized - 2x Faster)**:
```
Single image:  ~3s on M1
Batch of 4:    ~10s (2.5s per image avg)
Single text:   ~3s on M1
Batch of 8:    ~20s (2.5s per chunk avg)
```

### Late Interaction Scoring

```
Single query vs 1 document:     ~1ms on M1 GPU
Single query vs 100 documents:  ~100ms on M1 GPU
Single query vs 1000 documents: ~1s on M1 GPU

# CPU fallback (if GPU fails):
Single query vs 100 documents:  ~500ms on M1 CPU (5x slower)
```

### Memory Usage

**FP16**:
- Model: ~14GB
- Per-image processing: +512MB peak
- Per-batch (4 images): +2GB peak

**INT8**:
- Model: ~7GB
- Per-image processing: +256MB peak
- Per-batch (4 images): +1GB peak

---

## Device Handling

### Device Priority

1. **MPS (Metal Performance Shaders)** - M1/M2/M3 Macs
   ```python
   if torch.backends.mps.is_available():
       device = "mps"
   ```

2. **CUDA** - NVIDIA GPUs
   ```python
   elif torch.cuda.is_available():
       device = "cuda"
   ```

3. **CPU** - Fallback (3-5x slower)
   ```python
   else:
       device = "cpu"
   ```

### Environment Variables

```bash
# Enable MPS fallback for unsupported ops
PYTORCH_ENABLE_MPS_FALLBACK=1

# Alternative: Use GPT4All Metal backend (native M1 support)
GPT4ALL_BACKEND=metal

# Model cache location
TRANSFORMERS_CACHE=/models
HF_HOME=/models
```

---

## Error Handling

### Exception Types

```python
class EmbeddingError(Exception):
    """Base exception for embedding operations."""
    pass

class ModelLoadError(EmbeddingError):
    """Failed to load ColPali model."""
    pass

class DeviceError(EmbeddingError):
    """Requested device not available."""
    pass

class EmbeddingGenerationError(EmbeddingError):
    """Embedding computation failed."""
    pass

class ScoringError(EmbeddingError):
    """Late interaction scoring failed."""
    pass

class QuantizationError(EmbeddingError):
    """Model quantization failed."""
    pass
```

### Validation Rules

1. **Image Inputs**:
   - Must be PIL Images or valid file paths
   - Recommended resolution: 1024x1024 (ColPali default)
   - Supported formats: PNG, JPEG, PDF pages

2. **Text Inputs**:
   - Must be non-empty strings
   - Recommended length: 100-500 words per chunk
   - Maximum length: 8192 tokens (auto-truncated)

3. **Embedding Shapes**:
   - Must be 2D: (seq_length, 768)
   - seq_length must be > 0
   - dtype must be float32 or float16

---

## Unit Test Requirements

embedding-agent must provide unit tests covering:

1. **Model Loading**
   - Load model successfully with MPS device
   - Handle missing model files gracefully
   - Fallback to CPU if MPS unavailable
   - INT8 quantization works correctly

2. **Image Embedding**
   - Embed single image returns correct shape
   - Batch embedding processes all images
   - CLS token extraction is correct
   - Processing time within expected range

3. **Text Embedding**
   - Embed single text returns correct shape
   - Batch embedding processes all texts
   - Empty text raises ValueError
   - Long text is auto-truncated

4. **Query Embedding**
   - Query embedding returns correct format
   - Query length within expected range

5. **Late Interaction Scoring**
   - Score computation returns values in [0, 1]
   - Higher scores for semantically similar documents
   - Batch scoring handles 100+ documents
   - GPU scoring faster than CPU

6. **Error Cases**
   - Invalid device raises DeviceError
   - Corrupted image raises EmbeddingGenerationError
   - Incompatible embedding shapes raise ValueError

---

## Integration Test Requirements

processing-agent and search-agent must validate:

1. **End-to-End Embedding**
   - Generate embeddings for sample PDF (10 pages)
   - All embeddings have correct shapes
   - Processing time within targets (FP16: 60s, INT8: 30s)

2. **Search Quality**
   - Query "revenue growth" returns financial pages
   - Visual query returns pages with charts
   - Scores correlate with human relevance judgments

3. **Performance**
   - Batch processing faster than sequential
   - GPU utilization >80% during embedding
   - Memory stays within limits (8GB for INT8, 16GB for FP16)

---

## Optimization Notes

### Batch Processing

Always use batching when processing multiple items:

```python
# GOOD: Batch processing (10x faster)
embeddings = engine.embed_images([img1, img2, img3, img4], batch_size=4)

# BAD: Sequential processing
embeddings = [engine.embed_images([img]) for img in [img1, img2, img3, img4]]
```

### GPU Memory Management

Clear cache between large batches:

```python
# After processing 50 pages
engine.clear_cache()
```

### Quantization Trade-offs

| Metric | FP16 (Default) | INT8 (Quantized) |
|--------|----------------|------------------|
| **Quality** | 100% | 90-95% |
| **Speed** | 1x (baseline) | 2x faster |
| **Memory** | 14GB | 7GB |
| **Use Case** | 16GB RAM, best quality | 8GB RAM, faster processing |

---

## Future Enhancements (Post-MVP)

1. **Model Caching**: Keep model loaded between requests (daemon mode)
2. **Async Processing**: Use asyncio for concurrent embedding generation
3. **Dynamic Batching**: Automatically adjust batch size based on memory
4. **Multi-GPU**: Distribute batch across multiple GPUs if available
5. **ONNX Export**: Export model to ONNX for faster inference

Current version: **1.0** (initial ColPali integration)
