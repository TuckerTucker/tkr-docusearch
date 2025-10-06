# Integration Guide: Complete Stack Setup

**Stack:** Copyparty + Docling + Embedding Models + ChromaDB + smolagents

This guide provides complete implementation details for building a semantic search system across all document types.

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Installation](#installation)
3. [Component Setup](#component-setup)
4. [Integration Patterns](#integration-patterns)
5. [Code Examples](#code-examples)
6. [Deployment](#deployment)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User / Agent                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     smolagents                               │
│  - CodeAgent orchestration                                   │
│  - Custom tools for semantic search                          │
│  - Query processing and result formatting                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     ChromaDB                                 │
│  - Vector storage and retrieval                              │
│  - Collections per modality                                  │
│  - Multi-vector storage (ColNomic)                          │
└────────────────────────┬────────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
┌──────────────────┐          ┌──────────────────┐
│ Embedding Models │          │   Copyparty      │
│ - ColNomic 7B    │          │ - File server    │
│ - VLM2Vec-V2.0   │◄─────────┤ - Event hooks    │
│ - Whisper        │          │ - HTTP API       │
└────────┬─────────┘          └────────┬─────────┘
         │                              │
         ▼                              ▼
┌──────────────────┐          ┌──────────────────┐
│    Docling       │          │   File Storage   │
│ - PDF parsing    │          │ - Documents      │
│ - DOCX/PPTX     │          │ - Images         │
│ - Structure     │          │ - Videos         │
└─────────────────┘          │ - Audio          │
                             └──────────────────┘
```

---

## Installation

### 1. System Requirements

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3.10 python3-pip git ffmpeg

# macOS
brew install python@3.10 git ffmpeg

# Python version check
python --version  # Should be 3.10+
```

### 2. Create Virtual Environment

```bash
cd /Volumes/tkr-riffic/@tkr-projects/tkr-smolagents

# Create environment
python -m venv venv

# Activate
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows
```

### 3. Install Core Dependencies

```bash
# Base packages
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# ChromaDB
pip install chromadb

# smolagents
pip install smolagents

# Docling
pip install docling

# Copyparty
pip install copyparty
```

### 4. Install Embedding Models

#### ColNomic 7B
```bash
pip install git+https://github.com/illuin-tech/colpali.git
pip install transformers pillow
pip install flash-attn --no-build-isolation  # Optional, for speed
```

#### VLM2Vec-V2.0
```bash
git clone https://github.com/TIGER-AI-Lab/VLM2Vec.git
cd VLM2Vec
pip install -r requirements.txt
cd ..
```

#### Whisper
```bash
pip install openai-whisper
```

### 5. Additional Tools

```bash
# PDF to image conversion
pip install pdf2image

# Poppler (required for pdf2image)
# Ubuntu/Debian
sudo apt-get install poppler-utils

# macOS
brew install poppler

# Video processing
# ffmpeg already installed above
```

---

## Component Setup

### 1. Copyparty Setup

```bash
# Create data directories
mkdir -p /data/copyparty/{uploads,processed}
mkdir -p /data/copyparty/hooks

# Start Copyparty server
copyparty \
  --e2dsa \
  --e2ts \
  --hook-on-upload /data/copyparty/hooks/process_upload.py \
  -v /uploads:/data/copyparty/uploads:rw,ed \
  -v /processed:/data/copyparty/processed:rw \
  --http-only \
  -p 8000
```

**Copyparty config file** (`/data/copyparty/config.yaml`):

```yaml
# Copyparty configuration
volumes:
  - path: /data/copyparty/uploads
    alias: uploads
    flags: rw,ed

  - path: /data/copyparty/processed
    alias: processed
    flags: rw

event-hooks:
  - event: upload
    script: /data/copyparty/hooks/process_upload.py

server:
  port: 8000
  host: 0.0.0.0
```

### 2. ChromaDB Setup

```python
# /data/scripts/setup_chromadb.py

import chromadb
from chromadb.config import Settings

# Initialize client
client = chromadb.PersistentClient(
    path="/data/chroma_db",
    settings=Settings(
        anonymized_telemetry=False,
        allow_reset=True
    )
)

# Create collections
collections = {
    "colnomic_visual_docs": {
        "metadata": {"description": "Visual documents with ColNomic embeddings"}
    },
    "vlm2vec_videos": {
        "metadata": {"description": "Videos with VLM2Vec embeddings"}
    },
    "text_transcripts": {
        "metadata": {"description": "Audio transcripts and text content"}
    }
}

for name, config in collections.items():
    try:
        client.create_collection(name=name, metadata=config["metadata"])
        print(f"✓ Created collection: {name}")
    except Exception as e:
        print(f"Collection {name} already exists")

print("\nChromaDB setup complete!")
```

Run setup:
```bash
python /data/scripts/setup_chromadb.py
```

### 3. Embedding Models Setup

```python
# /data/scripts/setup_models.py

import torch
from colpali_engine.models import ColQwen2_5, ColQwen2_5_Processor
import sys
sys.path.append('/path/to/VLM2Vec')
from src.arguments import ModelArguments, DataArguments
from src.model.model import MMEBModel
from src.model.processor import load_processor
import whisper

# Download and cache models
print("Loading ColNomic 7B...")
colnomic_model = ColQwen2_5.from_pretrained(
    "nomic-ai/colnomic-embed-multimodal-7b",
    torch_dtype=torch.bfloat16,
    device_map="cuda:0"
)
colnomic_processor = ColQwen2_5_Processor.from_pretrained(
    "nomic-ai/colnomic-embed-multimodal-7b"
)
print("✓ ColNomic ready")

print("Loading VLM2Vec-V2.0...")
vlm2vec_args = ModelArguments(
    model_name='Qwen/Qwen2-VL-2B-Instruct',
    checkpoint_path='VLM2Vec/VLM2Vec-V2.0',
    pooling='last',
    normalize=True,
    model_backbone='qwen2_vl',
    lora=True
)
vlm2vec_model = MMEBModel.load(vlm2vec_args).to('cuda', dtype=torch.bfloat16)
vlm2vec_processor = load_processor(vlm2vec_args, DataArguments())
print("✓ VLM2Vec ready")

print("Loading Whisper...")
whisper_model = whisper.load_model("base")
print("✓ Whisper ready")

print("\nAll models loaded successfully!")
```

---

## Integration Patterns

### Pattern 1: Copyparty Event Hook

```python
# /data/copyparty/hooks/process_upload.py

import sys
import os
import hashlib
import torch
from pathlib import Path

# Add paths
sys.path.append('/path/to/VLM2Vec')

# Imports
from docling.document_converter import DocumentConverter
from colpali_engine.models import ColQwen2_5, ColQwen2_5_Processor
from src.model.model import MMEBModel
from src.model.processor import load_processor
import chromadb
import whisper
from PIL import Image
from pdf2image import convert_from_path

# Initialize models (cached after first load)
class ModelCache:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_models()
        return cls._instance

    def _init_models(self):
        # ColNomic
        self.colnomic_model = ColQwen2_5.from_pretrained(
            "nomic-ai/colnomic-embed-multimodal-7b",
            torch_dtype=torch.bfloat16,
            device_map="cuda:0"
        ).eval()
        self.colnomic_processor = ColQwen2_5_Processor.from_pretrained(
            "nomic-ai/colnomic-embed-multimodal-7b"
        )

        # VLM2Vec (load on demand)
        self.vlm2vec_model = None
        self.vlm2vec_processor = None

        # Whisper
        self.whisper_model = whisper.load_model("base")

        # ChromaDB
        self.chroma_client = chromadb.PersistentClient(path="/data/chroma_db")

models = ModelCache()

def process_pdf(file_path: str, copyparty_url: str, metadata: dict):
    """Process PDF with Docling + ColNomic"""

    print(f"Processing PDF: {file_path}")

    # 1. Parse with Docling
    converter = DocumentConverter()
    result = converter.convert(file_path)

    # 2. Convert pages to images
    page_images = convert_from_path(file_path)

    # 3. Embed each page
    doc_id = hashlib.md5(file_path.encode()).hexdigest()
    collection = models.chroma_client.get_collection("colnomic_visual_docs")

    for page_num, page_img in enumerate(page_images):
        # Generate embedding
        batch_img = models.colnomic_processor.process_images([page_img]).to("cuda:0")

        with torch.no_grad():
            embedding = models.colnomic_model(**batch_img)
            # Pool to dense vector
            dense_embedding = torch.max(embedding, dim=1)[0].cpu().numpy()

        # Store in ChromaDB
        collection.add(
            embeddings=[dense_embedding.tolist()],
            documents=[f"Page {page_num+1} of {os.path.basename(file_path)}"],
            metadatas=[{
                "file_path": file_path,
                "copyparty_url": copyparty_url,
                "page": page_num + 1,
                "total_pages": len(page_images),
                "type": "pdf_page"
            }],
            ids=[f"{doc_id}_page_{page_num}"]
        )

    print(f"✓ Indexed {len(page_images)} pages")

def process_video(file_path: str, copyparty_url: str, metadata: dict):
    """Process video with VLM2Vec"""

    print(f"Processing video: {file_path}")

    # Load VLM2Vec on first video
    if models.vlm2vec_model is None:
        from src.arguments import ModelArguments, DataArguments
        vlm2vec_args = ModelArguments(
            model_name='Qwen/Qwen2-VL-2B-Instruct',
            checkpoint_path='VLM2Vec/VLM2Vec-V2.0',
            pooling='last',
            normalize=True,
            model_backbone='qwen2_vl',
            lora=True
        )
        models.vlm2vec_model = MMEBModel.load(vlm2vec_args).to('cuda', dtype=torch.bfloat16)
        models.vlm2vec_processor = load_processor(vlm2vec_args, DataArguments())

    # Embed video
    # ... (see previous examples)

    print(f"✓ Indexed video")

def process_audio(file_path: str, copyparty_url: str, metadata: dict):
    """Process audio with Whisper"""

    print(f"Processing audio: {file_path}")

    # Transcribe
    result = models.whisper_model.transcribe(file_path)
    transcript = result["text"]

    # Store transcript
    doc_id = hashlib.md5(file_path.encode()).hexdigest()
    collection = models.chroma_client.get_collection("text_transcripts")

    # Simple text embedding (can use any model)
    collection.add(
        documents=[transcript],
        metadatas=[{
            "file_path": file_path,
            "copyparty_url": copyparty_url,
            "type": "audio_transcript",
            "language": result.get("language", "unknown")
        }],
        ids=[f"{doc_id}_transcript"]
    )

    print(f"✓ Transcribed {len(transcript)} characters")

def on_upload(file_path: str, copyparty_url: str, metadata: dict):
    """Main hook called by Copyparty"""

    try:
        if file_path.endswith(('.pdf', '.docx', '.pptx')):
            process_pdf(file_path, copyparty_url, metadata)

        elif file_path.endswith(('.mp4', '.avi', '.mov', '.mkv')):
            process_video(file_path, copyparty_url, metadata)

        elif file_path.endswith(('.mp3', '.wav', '.flac', '.m4a')):
            process_audio(file_path, copyparty_url, metadata)

        else:
            print(f"Skipping unsupported file type: {file_path}")

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        import traceback
        traceback.print_exc()

# Hook interface for Copyparty
if __name__ == "__main__":
    # Copyparty calls with: file_path, url, metadata
    import json
    file_path = sys.argv[1]
    copyparty_url = sys.argv[2]
    metadata = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}

    on_upload(file_path, copyparty_url, metadata)
```

### Pattern 2: smolagents Tool

```python
# /data/smolagents_tools/semantic_search_tool.py

from smolagents import Tool
import chromadb
import torch
from colpali_engine.models import ColQwen2_5, ColQwen2_5_Processor
from typing import Optional

class SemanticSearchTool(Tool):
    name = "semantic_search"
    description = """Search across all documents (PDFs, videos, audio) using natural language.
    Returns relevant content with source references."""

    inputs = {
        "query": {
            "type": "string",
            "description": "Natural language search query"
        },
        "content_type": {
            "type": "string",
            "description": "Filter by: 'documents', 'videos', 'audio', or 'all'"
        },
        "n_results": {
            "type": "integer",
            "description": "Number of results to return (default: 5)"
        }
    }
    output_type = "string"

    def __init__(self):
        super().__init__()

        # Load ColNomic for queries
        self.model = ColQwen2_5.from_pretrained(
            "nomic-ai/colnomic-embed-multimodal-7b",
            torch_dtype=torch.bfloat16,
            device_map="cuda:0"
        ).eval()
        self.processor = ColQwen2_5_Processor.from_pretrained(
            "nomic-ai/colnomic-embed-multimodal-7b"
        )

        # Connect to ChromaDB
        self.client = chromadb.PersistentClient(path="/data/chroma_db")

    def forward(
        self,
        query: str,
        content_type: str = "all",
        n_results: int = 5
    ) -> str:

        # Generate query embedding
        batch_query = self.processor.process_queries([query]).to("cuda:0")

        with torch.no_grad():
            query_embedding = self.model(**batch_query)
            dense_query = torch.max(query_embedding, dim=1)[0].cpu().numpy()

        # Search relevant collections
        all_results = []

        if content_type in ["documents", "all"]:
            doc_coll = self.client.get_collection("colnomic_visual_docs")
            doc_results = doc_coll.query(
                query_embeddings=[dense_query.tolist()],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            all_results.append(("Documents", doc_results))

        if content_type in ["videos", "all"]:
            vid_coll = self.client.get_collection("vlm2vec_videos")
            vid_results = vid_coll.query(
                query_embeddings=[dense_query.tolist()],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            all_results.append(("Videos", vid_results))

        if content_type in ["audio", "all"]:
            audio_coll = self.client.get_collection("text_transcripts")
            audio_results = audio_coll.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            all_results.append(("Audio", audio_results))

        return self._format_results(all_results, query)

    def _format_results(self, all_results, query):
        output = [f"# Search Results for: '{query}'\n"]

        for content_type, results in all_results:
            if not results['documents'][0]:
                continue

            output.append(f"\n## {content_type}\n")

            for i, (doc, meta, dist) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                similarity = 1 - dist
                output.append(f"""
### {i+1}. {meta.get('type', 'Unknown')} (Relevance: {similarity:.1%})
**File:** {meta['file_path']}
**URL:** {meta['copyparty_url']}
**Preview:** {doc[:200]}...
""")

        return "\n".join(output)
```

### Pattern 3: Agent Setup

```python
# /data/scripts/run_agent.py

from smolagents import CodeAgent, InferenceClientModel
import sys
sys.path.append('/data/smolagents_tools')

from semantic_search_tool import SemanticSearchTool

# Initialize model
model = InferenceClientModel(
    model_id="Qwen/Qwen2.5-Coder-32B-Instruct"
)

# Create agent
agent = CodeAgent(
    tools=[
        SemanticSearchTool(),
        # Add more tools as needed
    ],
    model=model,
    stream_outputs=True
)

# Run query
if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("Enter your query: ")

    result = agent.run(query)
    print("\n" + "="*80)
    print("RESULT:")
    print("="*80)
    print(result)
```

---

## Deployment

### Docker Compose Setup

```yaml
# docker-compose.yml

version: '3.8'

services:
  copyparty:
    image: copyparty/copyparty:latest
    ports:
      - "8000:8000"
    volumes:
      - ./data/copyparty/uploads:/uploads
      - ./data/copyparty/processed:/processed
      - ./data/copyparty/hooks:/hooks
      - ./data/copyparty/config.yaml:/config.yaml
    command: --config /config.yaml
    restart: unless-stopped

  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"
    volumes:
      - ./data/chroma_db:/chroma/chroma
    environment:
      - IS_PERSISTENT=TRUE
      - ANONYMIZED_TELEMETRY=FALSE
    restart: unless-stopped

  embedding-worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    volumes:
      - ./data:/data
      - ./VLM2Vec:/app/VLM2Vec
    environment:
      - CUDA_VISIBLE_DEVICES=0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped

  smolagents-api:
    build:
      context: .
      dockerfile: Dockerfile.agent
    ports:
      - "8002:8000"
    volumes:
      - ./data:/data
    environment:
      - CHROMADB_HOST=chromadb
      - CHROMADB_PORT=8000
    depends_on:
      - chromadb
      - embedding-worker
    restart: unless-stopped
```

### Systemd Service (Linux)

```ini
# /etc/systemd/system/copyparty.service

[Unit]
Description=Copyparty File Server
After=network.target

[Service]
Type=simple
User=tkr
WorkingDirectory=/data/copyparty
ExecStart=/usr/local/bin/copyparty --config /data/copyparty/config.yaml
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable copyparty
sudo systemctl start copyparty
sudo systemctl status copyparty
```

---

## Monitoring and Maintenance

### Health Check Script

```python
# /data/scripts/health_check.py

import requests
import chromadb

def check_copyparty():
    try:
        response = requests.get("http://localhost:8000")
        return response.status_code == 200
    except:
        return False

def check_chromadb():
    try:
        client = chromadb.HttpClient(host="localhost", port=8001)
        client.heartbeat()
        return True
    except:
        return False

if __name__ == "__main__":
    print("System Health Check")
    print("=" * 50)
    print(f"Copyparty:  {'✓' if check_copyparty() else '✗'}")
    print(f"ChromaDB:   {'✓' if check_chromadb() else '✗'}")
```

### Backup Script

```bash
#!/bin/bash
# /data/scripts/backup.sh

BACKUP_DIR="/backups/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Backup ChromaDB
echo "Backing up ChromaDB..."
tar -czf "$BACKUP_DIR/chroma_db.tar.gz" /data/chroma_db

# Backup Copyparty config
echo "Backing up Copyparty config..."
cp /data/copyparty/config.yaml "$BACKUP_DIR/"

echo "Backup complete: $BACKUP_DIR"
```

---

## Troubleshooting

### Common Issues

1. **CUDA Out of Memory**
   - Reduce batch size
   - Use FP16 instead of FP32
   - Process files sequentially

2. **ChromaDB Connection Issues**
   - Check if service is running: `sudo systemctl status chromadb`
   - Verify port: `lsof -i :8001`

3. **Copyparty Hook Failures**
   - Check logs: `/data/copyparty/logs/error.log`
   - Test hook manually: `python /data/copyparty/hooks/process_upload.py test.pdf`

4. **Model Download Failures**
   - Set HuggingFace cache: `export HF_HOME=/data/hf_cache`
   - Use offline mode after first download

---

## Next Steps

1. Test each component individually
2. Run integration tests
3. Monitor resource usage
4. Optimize performance
5. Add error handling and logging
6. Implement authentication
7. Set up monitoring dashboard
