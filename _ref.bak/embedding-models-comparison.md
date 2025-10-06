# Multimodal Embedding Models Comparison

Research findings for embedding models to use with Copyparty + Docling + ChromaDB + smolagents stack.

**Date:** 2025-10-06
**Purpose:** Semantic search across text, images, video, and audio documents

---

## Executive Summary

We evaluated three state-of-the-art multimodal embedding models:

1. **Jina Embeddings v4** (3.8B params) - General-purpose text + image
2. **VLM2Vec-V2.0** (2B params) - Text + image + **native video**
3. **ColNomic Embed Multimodal 7B** (7B params) - Text + image with **ColBERT late interaction**

**Recommendation:** Use **ColNomic 7B** for visual document-heavy workloads, add **VLM2Vec-V2.0** for video support.

---

## Detailed Comparison

| Feature | ColNomic 7B | VLM2Vec-V2.0 | Jina v4 |
|---------|-------------|--------------|---------|
| **Text Embeddings** | ✅ | ✅ | ✅ |
| **Image Embeddings** | ✅ | ✅ | ✅ |
| **Video Embeddings** | ❌ | ✅ **Native** | ❌ |
| **Audio Embeddings** | ❌ | ❌ | ❌ |
| **Visual Documents** | ✅ **Best-in-class** | ✅ | ✅ |
| **Model Size** | 7B params | 2B params | 3.8B params |
| **Architecture** | ColBERT (multi-vector) | Dense embeddings | Dense embeddings |
| **Backbone** | Qwen2.5-VL-7B | Qwen2-VL-2B | Qwen2.5-VL-3B |
| **Languages** | 5 (EN, IT, FR, DE, ES) | Multilingual | 30+ languages |
| **Special Feature** | Late interaction | Native video | Most languages |
| **Best Benchmark** | Vidore-v2: **62.7 NDCG@5** | MMEB-V2 | - |
| **Released** | 2024 | 2025 | 2024 |

---

## Model 1: Jina Embeddings v4

**HuggingFace:** `jinaai/jina-embeddings-v4`
**Params:** 3.8B
**Backbone:** Qwen2.5-VL-3B-Instruct

### Supported Modalities
- ✅ Text (multilingual, 30+ languages)
- ✅ Images (photos, screenshots, charts)
- ✅ Visual documents (with charts, tables)
- ❌ Video (not supported)
- ❌ Audio (not supported)

### Key Features
- Multilingual support (30+ languages)
- Task-specific adapters (retrieval, text-matching, code)
- Flexible embedding dimensions (128-2048)
- Mean pooling strategy
- Max sequence length: 32,768 tokens

### Installation
```bash
pip install transformers>=4.52.0 torch>=2.6.0 peft>=0.15.2 torchvision pillow
```

### Usage Example
```python
from transformers import AutoModel

model = AutoModel.from_pretrained("jinaai/jina-embeddings-v4", trust_remote_code=True)

# Text embeddings
query_embeddings = model.encode_text(
    texts=["Climate change overview"],
    task="retrieval",
    prompt_name="query"
)

# Image embeddings
image_embeddings = model.encode_image(
    images=["image_url.jpg"],
    task="retrieval"
)
```

### Pros
- Excellent multilingual coverage
- Simple API
- Good for general-purpose text+image search
- Well-documented

### Cons
- No video support (need to extract frames)
- No late interaction (less precise for long documents)
- Larger model size

### Best Use Cases
- Multilingual document search
- General text+image retrieval
- When you need support for many languages

---

## Model 2: VLM2Vec-V2.0

**HuggingFace:** `VLM2Vec/VLM2Vec-V2.0`
**Params:** 2B
**Backbone:** Qwen2-VL-2B-Instruct
**Paper:** [arxiv:2507.04590](https://arxiv.org/abs/2507.04590)

### Supported Modalities
- ✅ Text
- ✅ Images
- ✅ **Video (native support!)** 🎥
- ✅ Visual documents
- ❌ Audio (not supported)

### Key Features
- **Native video embedding** (no frame extraction needed)
- Unified embedding space for text, images, videos
- Cross-modal retrieval (search text→find videos, etc.)
- Smallest model (2B params = fastest inference)
- MMEB-V2 benchmark with 78 diverse tasks

### Installation
```bash
git clone https://github.com/TIGER-AI-Lab/VLM2Vec.git
cd VLM2Vec
pip install -r requirements.txt
```

### Usage Example
```python
from src.arguments import ModelArguments, DataArguments
from src.model.model import MMEBModel
from src.model.processor import load_processor, VLM_VIDEO_TOKENS, QWEN2_VL
from src.model.vlm_backbone.qwen2_vl.qwen_vl_utils import process_vision_info

# Load model
model_args = ModelArguments(
    model_name='Qwen/Qwen2-VL-2B-Instruct',
    checkpoint_path='VLM2Vec/VLM2Vec-V2.0',
    pooling='last',
    normalize=True,
    model_backbone='qwen2_vl',
    lora=True
)
model = MMEBModel.load(model_args).to('cuda', dtype=torch.bfloat16)
processor = load_processor(model_args, DataArguments())

# Video embeddings
messages = [{
    "role": "user",
    "content": [
        {
            "type": "video",
            "video": "example.mp4",
            "max_pixels": 360 * 420,
            "fps": 1.0,
        },
        {"type": "text", "text": "Represent this video."},
    ],
}]

_, video_inputs = process_vision_info(messages)
inputs = processor(
    text=f'{VLM_VIDEO_TOKENS[QWEN2_VL]} Represent this video.',
    videos=video_inputs,
    return_tensors="pt"
)
inputs = {k: v.to('cuda') for k, v in inputs.items()}
embeddings = model(qry=inputs)["qry_reps"]
```

### Pros
- **Native video support** (unique!)
- Smallest model = fastest inference
- Cross-modal search capabilities
- State-of-the-art on MMEB-V2 benchmark
- Published 2025 (most recent)

### Cons
- More complex setup (requires custom repo)
- Less mature ecosystem than Jina
- Fewer supported languages

### Best Use Cases
- Video content retrieval
- Video moment/scene search
- Cross-modal applications (text→video search)
- When performance/speed is critical

---

## Model 3: ColNomic Embed Multimodal 7B

**HuggingFace:** `nomic-ai/colnomic-embed-multimodal-7b`
**Params:** 7B
**Backbone:** Qwen2.5-VL-7B-Instruct
**Architecture:** ColBERT (late interaction)

### Supported Modalities
- ✅ Text
- ✅ Images
- ✅ **Visual documents (BEST-IN-CLASS)** 📄
- ❌ Video (not supported)
- ❌ Audio (not supported)

### Key Features
- **ColBERT late interaction** = multi-vector embeddings
- **Vidore-v2 SOTA:** 62.7 NDCG@5 (best visual document retrieval)
- Preserves document layout understanding
- Excellent for tables, charts, diagrams
- Multilingual (English, Italian, French, German, Spanish)
- Unified text-image processing without preprocessing

### What is Late Interaction?

Traditional embeddings: 1 vector per document
**ColBERT:** Multiple vectors (1 per token)

**Benefits:**
- More precise matching (can match specific document sections)
- Better for long documents
- Contextual search within documents
- Finds relevant passages, not just whole documents

### Installation
```bash
pip install git+https://github.com/illuin-tech/colpali.git
pip install flash-attn --no-build-isolation  # Optional but recommended
```

### Usage Example
```python
import torch
from PIL import Image
from colpali_engine.models import ColQwen2_5, ColQwen2_5_Processor

model_name = "nomic-ai/colnomic-embed-multimodal-7b"

# Load model
model = ColQwen2_5.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    device_map="cuda:0",
).eval()
processor = ColQwen2_5_Processor.from_pretrained(model_name)

# Process documents (as images)
images = [Image.open("financial_report.pdf")]  # PDF pages as images
queries = ["What were Q4 revenue projections?"]

batch_images = processor.process_images(images).to(model.device)
batch_queries = processor.process_queries(queries).to(model.device)

# Generate multi-vector embeddings
with torch.no_grad():
    image_embeddings = model(**batch_images)
    query_embeddings = model(**batch_queries)

# Late interaction scoring (MaxSim)
scores = processor.score_multi_vector(query_embeddings, image_embeddings)
```

### Pros
- **Best visual document retrieval** (research papers, reports, presentations)
- Late interaction = more precise matching
- Understands document layout/structure
- Excellent for tables, charts, diagrams
- No preprocessing needed (treat PDFs as images)

### Cons
- Largest model (7B params)
- No video support
- More complex multi-vector storage
- Fewer languages than Jina

### Best Use Cases
- Financial reports with tables
- Research papers with charts
- Technical documentation
- Product catalogs
- Any document where layout/structure matters

---

## Audio Support (All Models)

**None of these models support audio natively.**

### Solution: Whisper + Text Embeddings

Use OpenAI Whisper for transcription, then embed the text:

```python
import whisper

# Transcribe audio
whisper_model = whisper.load_model("base")
result = whisper_model.transcribe("audio.mp3")
transcript = result["text"]

# Embed transcript with any model
embeddings = model.encode_text([transcript])
```

**Whisper installation:**
```bash
pip install openai-whisper
```

---

## Recommended Architecture

### Option 1: ColNomic-Focused (Best for Document-Heavy)

```
Copyparty (file storage)
    ↓
Docling (parse PDFs/DOCX)
    ↓
ColNomic 7B (visual docs) + Whisper (audio)
    ↓
ChromaDB (vector storage)
    ↓
smolagents (AI orchestration)
```

**Use when:**
- Primarily dealing with PDFs, reports, presentations
- Need to find specific tables/charts/sections
- Documents have complex layouts
- Working with research papers, financial docs

### Option 2: Hybrid Approach (Best for Mixed Content)

```
Copyparty (file storage)
    ↓
Docling (parse documents)
    ↓
┌────────────────────┬─────────────────┬──────────────┐
│ ColNomic 7B        │ VLM2Vec-V2.0   │ Whisper      │
│ (visual docs)      │ (videos)        │ (audio)      │
└────────────────────┴─────────────────┴──────────────┘
    ↓
ChromaDB (vector storage with separate collections)
    ↓
smolagents (AI orchestration)
```

**Use when:**
- Mix of documents, images, videos, audio
- Need video content retrieval
- Want best-in-class for each modality

### Option 3: Jina-Focused (Best for Simplicity + Multilingual)

```
Copyparty (file storage)
    ↓
Docling (parse documents)
    ↓
Jina v4 (text/images) + Whisper (audio) + Frame extraction (video)
    ↓
ChromaDB (vector storage)
    ↓
smolagents (AI orchestration)
```

**Use when:**
- Need 30+ language support
- Simpler deployment requirements
- Don't need late interaction precision
- Video support is nice-to-have (frame extraction okay)

---

## Implementation Code Snippets

### ChromaDB Integration Pattern

```python
import chromadb

# Create collections for different modalities
chroma_client = chromadb.PersistentClient(path="/data/chroma_db")

# Text collection
text_collection = chroma_client.get_or_create_collection(
    name="documents_text",
    embedding_function=your_embedding_function,
    metadata={"description": "Text documents"}
)

# Visual collection (images, video frames)
visual_collection = chroma_client.get_or_create_collection(
    name="documents_visual",
    metadata={"description": "Images and videos"}
)

# Add documents
text_collection.add(
    embeddings=[embedding_vector],
    documents=["document text"],
    metadatas=[{"file_path": "/path/to/doc.pdf", "page": 1}],
    ids=["doc1_page1"]
)

# Search
results = text_collection.query(
    query_embeddings=[query_embedding],
    n_results=5
)
```

### Copyparty Event Hook Pattern

```python
# bin/hooks/process_upload.py

def on_upload(file_path: str, copyparty_url: str, metadata: dict):
    """Called by Copyparty when file is uploaded"""

    if file_path.endswith(('.pdf', '.docx', '.pptx')):
        process_document(file_path, copyparty_url, metadata)

    elif file_path.endswith(('.mp4', '.avi', '.mov')):
        process_video(file_path, copyparty_url, metadata)

    elif file_path.endswith(('.mp3', '.wav', '.flac')):
        process_audio(file_path, copyparty_url, metadata)
```

### smolagents Tool Pattern

```python
from smolagents import Tool

class SemanticSearchTool(Tool):
    name = "semantic_search"
    description = "Search documents by meaning using natural language"

    inputs = {
        "query": {"type": "string", "description": "Search query"},
        "n_results": {"type": "integer", "description": "Number of results"}
    }
    output_type = "string"

    def forward(self, query: str, n_results: int = 5) -> str:
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])[0]

        # Search ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        return self._format_results(results)
```

---

## Performance Considerations

### Model Size vs Speed

| Model | Params | GPU Memory | Inference Speed* |
|-------|--------|------------|------------------|
| VLM2Vec-V2.0 | 2B | ~4GB | Fast |
| Jina v4 | 3.8B | ~8GB | Medium |
| ColNomic 7B | 7B | ~14GB | Slower |

*Approximate, depends on hardware and batch size

### Optimization Tips

1. **Use FP16/BF16:** Reduce memory by 50%
   ```python
   model = model.to(dtype=torch.bfloat16)
   ```

2. **Flash Attention 2:** Faster inference
   ```python
   model = Model.from_pretrained(
       model_name,
       attn_implementation="flash_attention_2"
   )
   ```

3. **Batch Processing:** Process multiple items at once
   ```python
   embeddings = model.encode_batch(texts, batch_size=32)
   ```

4. **GPU Selection:** Apple Silicon users can use MPS
   ```python
   device_map = "mps"  # For Apple M1/M2/M3
   ```

---

## Cost Analysis

### Deployment Options

1. **Self-hosted (Recommended)**
   - One-time GPU cost ($500-2000 for consumer GPU)
   - No per-query costs
   - Full data privacy
   - Best for: Regular usage, sensitive data

2. **Cloud GPU (AWS/GCP/Azure)**
   - ~$0.50-3.00/hour for GPU instances
   - Pay only when processing
   - Best for: Batch processing, irregular usage

3. **Managed Embedding API**
   - Jina has hosted API option
   - ~$0.0001-0.001 per embedding
   - Best for: Prototyping, low volume

### Hardware Requirements

**Minimum:**
- GPU: NVIDIA RTX 3060 (12GB VRAM)
- CPU: 8 cores
- RAM: 32GB
- Storage: 100GB SSD

**Recommended:**
- GPU: NVIDIA RTX 4090 / A100 (24GB+ VRAM)
- CPU: 16+ cores
- RAM: 64GB+
- Storage: 500GB NVMe SSD

**Budget Option:**
- Apple M1/M2/M3 with 16GB+ unified memory
- Works with all models using MPS backend

---

## Next Steps

### Phase 1: Proof of Concept
1. Set up Copyparty file server
2. Install Docling for document parsing
3. Deploy ColNomic 7B for visual documents
4. Set up ChromaDB for vector storage
5. Create basic smolagents tools

### Phase 2: Production
1. Add VLM2Vec-V2.0 for video support
2. Implement Whisper for audio transcription
3. Set up Copyparty event hooks
4. Build comprehensive smolagents workflow
5. Add monitoring and error handling

### Phase 3: Optimization
1. Implement two-stage retrieval (approximate + rerank)
2. Add caching for frequently accessed embeddings
3. Optimize batch processing
4. Set up distributed processing if needed
5. Fine-tune models on domain-specific data (optional)

---

## References

### Model Documentation
- **Jina v4:** https://huggingface.co/jinaai/jina-embeddings-v4
- **VLM2Vec-V2.0:** https://huggingface.co/VLM2Vec/VLM2Vec-V2.0
  - Paper: https://arxiv.org/abs/2507.04590
  - GitHub: https://github.com/TIGER-AI-Lab/VLM2Vec
- **ColNomic 7B:** https://huggingface.co/nomic-ai/colnomic-embed-multimodal-7b
  - ColPali Engine: https://github.com/illuin-tech/colpali

### Supporting Tools
- **Docling:** https://huggingface.co/docling-project/docling
  - Docs: https://docling-project.github.io/docling/
- **ChromaDB:** https://www.trychroma.com/
  - Docs: https://docs.trychroma.com/
- **smolagents:** https://huggingface.co/smolagents
  - Docs: https://huggingface.co/docs/smolagents
- **Copyparty:** https://github.com/9001/copyparty
- **Whisper:** https://github.com/openai/whisper

### Additional Reading
- ColBERT explanation: https://jina.ai/news/what-is-colbert-and-late-interaction-and-why-they-matter-in-search/
- Weaviate late interaction overview: https://weaviate.io/blog/late-interaction-overview

---

## Conclusion

**Final Recommendation: ColNomic 7B + VLM2Vec-V2.0 Hybrid**

- **ColNomic 7B** for all visual documents (PDFs, presentations, reports)
- **VLM2Vec-V2.0** for native video content
- **Whisper** for audio transcription
- **ChromaDB** with separate collections per modality
- **smolagents** for AI orchestration

This combination provides:
- Best-in-class visual document retrieval
- Native video support
- Complete modality coverage (text, images, video, audio)
- Flexibility to optimize per content type

Start with ColNomic 7B for immediate value on document-heavy workloads, then add VLM2Vec when video support is needed.
