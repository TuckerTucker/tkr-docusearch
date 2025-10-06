# Docling Model Requirements & Architecture

## Overview

Docling uses **AI models** for document parsing, specifically for layout analysis and table structure recognition. These models are automatically downloaded from HuggingFace when first used.

## Models Used by Docling

### 1. Layout Models (Required for PDF parsing)

**Purpose**: Detect document layout components (text blocks, tables, images, headers, etc.)

**Available Models** (from fastest to most accurate):
| Model | HuggingFace Repo | Size | Speed | Use Case |
|-------|------------------|------|-------|----------|
| **Heron** (default) | `ds4sd/docling-layout-heron` | ~100MB | Fast | Default for production |
| Heron-101 | `ds4sd/docling-layout-heron-101` | ~150MB | Medium | Better accuracy |
| Egret Medium | `ds4sd/docling-layout-egret-medium` | ~200MB | Medium | Higher quality |
| Egret Large | `ds4sd/docling-layout-egret-large` | ~300MB | Slower | Best accuracy |
| Egret XLarge | `ds4sd/docling-layout-egret-xlarge` | ~500MB | Slowest | Maximum accuracy |
| Layout V2 (old) | `ds4sd/docling-layout-old` | ~100MB | Fast | Legacy |

**What It Detects** (11 labels):
- Text blocks
- Tables
- Pictures/figures
- Section headers
- Page headers/footers
- Captions
- Footnotes
- Formulas
- List items
- Code blocks
- Titles

**Supported Devices**:
- ✅ CPU (all platforms)
- ✅ CUDA (NVIDIA GPUs)
- ✅ MPS (Apple Silicon)

**Performance**:
- ~1-2 seconds per page (CPU)
- ~0.3-0.5 seconds per page (GPU)
- Accuracy: 60-94% depending on element type (page headers/footers: 93-94%, titles: 60-72%)

### 2. TableFormer (Optional, for table structure)

**Purpose**: Extract table structure (cells, rows, columns) from detected table regions

**HuggingFace Repo**: `ds4sd/docling-models` (subfolder: `model_artifacts/tableformer`)

**Two Modes**:
- **Fast mode**: Quick table extraction (~200MB model)
- **Accurate mode**: High-quality table structure (~300MB model)

**Performance**:
- Simple tables: 95.4% accuracy
- Complex tables: 90.1% accuracy
- Overall: 93.6% accuracy

**Supported Devices**:
- ✅ CPU (all platforms)
- ✅ CUDA (NVIDIA GPUs)
- ⚠️ MPS (disabled - CPU fallback used, slower on Apple Silicon)

### 3. OCR Models (Optional, for scanned documents)

**Purpose**: Extract text from scanned PDFs and images

**Options**:
1. **EasyOCR** (default, bundled)
   - Multi-language support (80+ languages)
   - ~200-500MB per language model
   - CPU/GPU support
   - Good accuracy, slower

2. **Tesseract** (optional)
   - Traditional OCR engine
   - Requires system installation
   - Fast, lower accuracy

3. **RapidOCR** (optional)
   - ONNX-based OCR
   - ~50MB model
   - Fast inference
   - Good for Asian languages

4. **OCRmac** (macOS only)
   - Uses system OCR
   - No additional models
   - Fast, native integration

### 4. Visual Language Models (Optional, experimental)

**Purpose**: End-to-end document understanding using vision-language models

**Available VLMs**:
1. **GraniteDocling** (`ibm-granite/granite-docling-258M`)
   - 258M parameters
   - Specialized for document layout
   - ~500MB model size
   - MLX acceleration on Apple Silicon
   - Fast inference: ~0.35s per page (A100 GPU)

2. **Other VLMs** (via transformers)
   - Can use any Qwen-VL compatible model
   - Larger models (2B-7B parameters)
   - Higher memory requirements (4-14GB)

### 5. Code & Formula Models (Optional)

**Purpose**: Specialized extraction of code blocks and mathematical formulas

**Model**: Uses layout model predictions + specialized processing
**No additional downloads required**

### 6. Picture Classifier (Optional)

**Purpose**: Classify images into categories (charts, diagrams, photos, etc.)

**Model**: Lightweight CNN-based classifier
**Size**: ~50MB
**Use case**: Image categorization for better document understanding

### 7. ASR Models (Optional, for audio)

**Purpose**: Automatic Speech Recognition for audio files (MP3, WAV)

**Model**: OpenAI Whisper
**Options**:
- Tiny: 39M params, ~150MB
- Base: 74M params, ~290MB
- Small: 244M params, ~970MB
- Medium: 769M params, ~3GB
- Large: 1.5B params, ~6GB

## Total Storage Requirements

**Minimal Setup** (PDF + DOCX/PPTX only):
- Layout model (Heron): ~100MB
- Docling dependencies: ~500MB
- **Total**: ~600MB

**Standard Setup** (includes OCR for scanned PDFs):
- Layout model: ~100MB
- TableFormer (fast): ~200MB
- EasyOCR (English): ~200MB
- Docling dependencies: ~500MB
- **Total**: ~1GB

**Full Setup** (all features):
- Layout model (Egret Large): ~300MB
- TableFormer (accurate): ~300MB
- EasyOCR (multiple languages): ~500MB
- GraniteDocling VLM: ~500MB
- Whisper (small): ~970MB
- Other utilities: ~500MB
- **Total**: ~3GB

## Memory Requirements (RAM/VRAM)

### CPU-Only (M1 Mac)

| Configuration | RAM Required | Processing Speed |
|---------------|--------------|------------------|
| Minimal (layout only) | 2-4GB | 1-2s per page |
| Standard (layout + OCR) | 4-6GB | 2-3s per page |
| With TableFormer | 6-8GB | 3-4s per page |
| With VLM (GraniteDocling) | 8-12GB | 5-7s per page |

### GPU (CUDA/MPS)

| Configuration | VRAM Required | Processing Speed |
|---------------|---------------|------------------|
| Layout model | 1-2GB | 0.3-0.5s per page |
| + TableFormer | 2-3GB | 0.5-0.8s per page |
| + OCR | 3-4GB | 0.8-1.2s per page |
| VLM (GraniteDocling) | 2-3GB | 0.35s per page |

**Note**: M1/M2/M3 Macs with MPS:
- Layout models work well (~0.5s per page)
- TableFormer falls back to CPU (MPS disabled due to slowdown)
- VLMs use MLX acceleration (very fast, ~0.35s per page)

## Model Download Process

**Automatic Download**:
1. First time Docling runs, it checks for models in `~/.cache/huggingface/`
2. If not found, downloads from HuggingFace
3. Models are cached locally for future use

**Manual Download** (for air-gapped environments):
```bash
# Download layout model
docling-tools download-models --layout-model heron

# Download TableFormer
docling-tools download-models --tableformer

# Download all models
docling-tools download-models --all
```

**Custom Model Path**:
```python
from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions
from pathlib import Path

converter = DocumentConverter(
    pipeline_options=PdfPipelineOptions(
        artifacts_path=Path("/custom/path/to/models")
    )
)
```

## Impact on MVP Architecture

### Storage Impact

**For Our MVP** (copyparty/docling/chroma stack):

1. **Processing Worker Container Size**:
   - Base Python image: ~500MB
   - Docling + dependencies: ~1GB
   - Layout model (Heron): ~100MB
   - TableFormer (fast): ~200MB
   - EasyOCR (English): ~200MB
   - ColNomic 7B (INT8): ~7GB
   - **Total container**: ~9GB

2. **Cached Model Storage** (persistent volume):
   - Docling models: ~500MB
   - ColNomic embeddings: ~7GB
   - **Total**: ~7.5GB

### Memory Impact

**8GB M1 Mac**:
- System: 2GB
- Docling (layout + TableFormer): 4GB
- ColNomic 7B (INT8): 7GB
- **Problem**: 13GB needed, only 8GB available
- **Solution**: Disable TableFormer OR use lighter layout model OR process sequentially

**16GB M1 Mac**:
- System: 2GB
- Docling (full): 6GB
- ColNomic 7B (INT8): 7GB
- ChromaDB: 1GB
- **Total**: 16GB (tight but workable)

### Performance Impact

**Document Processing Pipeline** (with Docling):
1. **Docling parsing**: 2-3s per page (CPU) or 0.5s per page (MPS)
2. **ColNomic embedding**: 3s per page/chunk (INT8)
3. **Total**: ~5-6s per page (INT8)

**10-page PDF**:
- Docling: 5-20s (depending on CPU/GPU)
- ColNomic: 30s (INT8, parallel visual + text)
- **Total**: ~35-50s (vs 15s without Docling parsing overhead)

## Recommendations for MVP

### Option 1: Minimal Docling (Recommended for 8GB Macs)
```yaml
# Disable heavy models to save memory
PdfPipelineOptions(
    do_table_structure=False,  # Disable TableFormer (saves 2-3GB RAM)
    do_ocr=False,  # Disable OCR if native PDFs only (saves 2GB RAM)
    layout_model=DOCLING_LAYOUT_HERON,  # Lightest model
)
```
**Pros**: Fits in 8GB, still gets layout analysis
**Cons**: No table structure, no OCR for scanned docs

### Option 2: Standard Docling (Recommended for 16GB Macs)
```yaml
PdfPipelineOptions(
    do_table_structure=True,  # Enable TableFormer (fast mode)
    do_ocr=True,  # Enable EasyOCR
    layout_model=DOCLING_LAYOUT_HERON,
)
```
**Pros**: Full document understanding
**Cons**: Requires 16GB RAM

### Option 3: Sequential Processing (For 8GB Macs)
```python
# Process Docling and ColNomic sequentially, not in parallel
# 1. Parse document with Docling → unload models
# 2. Embed with ColNomic → store in ChromaDB
```
**Pros**: Fits in 8GB by not loading both simultaneously
**Cons**: Slower (5-10s per page vs 3-6s)

## Architecture Update Needed

**Current MVP assumes**: Docling is lightweight (no model overhead)
**Reality**: Docling adds ~4-6GB memory + ~500MB storage + 2-3s per page

**Proposed Update**:
1. **Memory section**: Note that 16GB RAM is recommended (vs 8GB minimum)
2. **Performance estimates**: Add 2-3s per page for Docling parsing
3. **Storage estimates**: Add ~500MB for Docling models
4. **Docker config**: Consider sequential processing option for 8GB systems
5. **Alternative**: Offer "fast mode" that skips table structure and OCR

## Bottom Line

**Docling is not just a parser** - it's a sophisticated AI pipeline with:
- Multiple deep learning models (layout detection, table structure, OCR)
- Significant memory requirements (4-6GB)
- HuggingFace model downloads (~500MB-1GB)
- Processing overhead (2-3s per page)

**For MVP**:
- ✅ Works great on 16GB M1 Macs
- ⚠️ Requires careful configuration on 8GB M1 Macs (disable TableFormer/OCR)
- ✅ Models cached locally (no internet needed after first run)
- ✅ MPS acceleration for layout models (fast)
- ⚠️ TableFormer fallback to CPU on MPS (slower)

This is **more complex** than initially assumed but still manageable with proper configuration.
