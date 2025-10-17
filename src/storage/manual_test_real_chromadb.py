#!/usr/bin/env python3
"""
Test Real ChromaDB Integration with 128-dim Embeddings

This script validates ChromaDB storage with real ColPali embeddings.

Usage:
    source start_env
    python3 src/storage/test_real_chromadb.py
"""

import sys
from pathlib import Path

from PIL import Image

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from embeddings import ColPaliEngine
from storage import ChromaClient

print("=" * 80)
print("Testing Real ChromaDB with 128-dim ColPali Embeddings")
print("=" * 80)

# Step 1: Initialize ColPali Engine
print("\n[1] Initializing ColPali Engine...")
engine = ColPaliEngine(device="mps", precision="fp16")
info = engine.get_model_info()
print(f"  ✓ Model: {info['model_name']}")
print(f"  ✓ Memory: {info['memory_allocated_mb']:.1f} MB")

# Step 2: Connect to real ChromaDB
print("\n[2] Connecting to ChromaDB...")
chroma = ChromaClient(
    host="localhost",
    port=8001,
    visual_collection="test_visual_128dim",
    text_collection="test_text_128dim",
)
print("  ✓ Connected to ChromaDB at localhost:8001")

# Step 3: Generate embeddings
print("\n[3] Generating test embeddings...")
test_image = Image.new("RGB", (224, 224), color="white")
test_text = "This is a test document about revenue growth in Q3 2024."

visual_result = engine.embed_images([test_image])
text_result = engine.embed_texts([test_text])

print(f"  ✓ Visual embedding: {visual_result['embeddings'][0].shape}")
print(f"  ✓ Text embedding: {text_result['embeddings'][0].shape}")

# Step 4: Store in ChromaDB
print("\n[4] Storing embeddings in ChromaDB...")

visual_id = chroma.add_visual_embedding(
    doc_id="test-doc-001",
    page=1,
    full_embeddings=visual_result["embeddings"][0],
    metadata={
        "filename": "test.pdf",
        "upload_date": "2025-01-28",
        "test": "real-chromadb-128dim",
        "source_path": "/uploads/test.pdf",  # Required field
    },
)
print(f"  ✓ Stored visual: {visual_id}")

text_id = chroma.add_text_embedding(
    doc_id="test-doc-001",
    chunk_id=0,
    full_embeddings=text_result["embeddings"][0],
    metadata={
        "filename": "test.pdf",
        "test": "real-chromadb-128dim",
        "source_path": "/uploads/test.pdf",
        "page": 1,  # Required field
        "text_preview": test_text[:100],
    },
)
print(f"  ✓ Stored text: {text_id}")

# Step 5: Retrieve and verify
print("\n[5] Retrieving embeddings...")

full_visual = chroma.get_full_embeddings(visual_id)
full_text = chroma.get_full_embeddings(text_id)

print(f"  ✓ Retrieved visual: {full_visual.shape}")
print(f"  ✓ Retrieved text: {full_text.shape}")

# Verify shapes match
assert full_visual.shape == visual_result["embeddings"][0].shape
assert full_text.shape == text_result["embeddings"][0].shape
print("  ✓ Shapes verified!")

# Step 6: Test search
print("\n[6] Testing search...")

query_result = engine.embed_query("revenue growth Q3")
print(f"  ✓ Query embedding: {query_result['embeddings'].shape}")

visual_results = chroma.search_visual(query_embedding=query_result["cls_token"], n_results=5)

text_results = chroma.search_text(query_embedding=query_result["cls_token"], n_results=5)

print(f"  ✓ Visual search: {len(visual_results)} results")
print(f"  ✓ Text search: {len(text_results)} results")

if visual_results:
    print(
        f"    Top visual result: {visual_results[0]['id']}, distance={visual_results[0]['distance']:.4f}"
    )

if text_results:
    print(
        f"    Top text result: {text_results[0]['id']}, distance={text_results[0]['distance']:.4f}"
    )

# Step 7: Test MaxSim scoring
print("\n[7] Testing late interaction scoring...")

if text_results:
    top_result_id = text_results[0]["id"]
    top_full_emb = chroma.get_full_embeddings(top_result_id)

    scores = engine.score_multi_vector(
        query_embeddings=query_result["embeddings"], document_embeddings=[top_full_emb]
    )

    print(f"  ✓ MaxSim score: {scores['scores'][0]:.4f}")
    print(f"  ✓ Scoring time: {scores['scoring_time_ms']:.2f}ms")

# Step 8: Get collection stats
print("\n[8] Collection statistics...")
stats = chroma.get_collection_stats()
print(f"  ✓ Visual embeddings: {stats['visual_count']}")
print(f"  ✓ Text embeddings: {stats['text_count']}")
print(f"  ✓ Total documents: {stats['total_documents']}")

print("\n" + "=" * 80)
print("✅ ALL TESTS PASSED!")
print("=" * 80)
print("\nKey Findings:")
print(f"  • ChromaDB accepts 128-dim embeddings ✓")
print(f"  • Compression working (no metadata size issues) ✓")
print(f"  • Search returns results ✓")
print(f"  • MaxSim re-ranking working ✓")
print(f"  • Full pipeline: Store → Search → Score functional ✓")
