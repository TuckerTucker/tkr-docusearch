"""
Example usage of the ColPali embeddings module.

This script demonstrates the main workflows:
1. Initializing the engine
2. Embedding images
3. Embedding text
4. Embedding queries
5. Late interaction scoring (MaxSim)

NOTE: Wave 2 uses mock implementations. Install ColPali for production use.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from embeddings import ColPaliEngine
from config import ModelConfig
from PIL import Image
import numpy as np


def example_basic_initialization():
    """Example 1: Basic engine initialization."""
    print("\n" + "="*70)
    print("Example 1: Basic Initialization")
    print("="*70)

    # Initialize with defaults
    engine = ColPaliEngine()

    # Get model info
    info = engine.get_model_info()
    print(f"\nModel: {info['model_name']}")
    print(f"Device: {info['device']}")
    print(f"Precision: {info['dtype']}")
    print(f"Memory: {info['memory_allocated_mb']:.1f}MB")
    print(f"Quantized: {info['quantization'] or 'No'}")


def example_custom_config():
    """Example 2: Custom configuration."""
    print("\n" + "="*70)
    print("Example 2: Custom Configuration")
    print("="*70)

    # Create custom config
    config = ModelConfig(
        name="vidore/colqwen2-v0.1",
        device="cpu",  # Force CPU
        precision="int8",  # Use quantization
        batch_size_visual=2,
        batch_size_text=4
    )

    # Initialize engine with custom config
    engine = ColPaliEngine(config=config)

    print(f"\nCustom config applied:")
    print(f"  Device: {engine.config.device}")
    print(f"  Precision: {engine.config.precision}")
    print(f"  Batch size (visual): {engine.config.batch_size_visual}")
    print(f"  Batch size (text): {engine.config.batch_size_text}")
    print(f"  Estimated memory: {engine.config.memory_estimate_gb:.1f}GB")


def example_image_embedding():
    """Example 3: Embedding images."""
    print("\n" + "="*70)
    print("Example 3: Image Embedding")
    print("="*70)

    engine = ColPaliEngine(device="cpu", precision="fp16")

    # Create dummy images (in production, load from PDF pages)
    images = [
        Image.new("RGB", (1024, 1024), color="white"),
        Image.new("RGB", (1024, 1024), color="lightgray"),
        Image.new("RGB", (1024, 1024), color="silver"),
    ]

    # Embed images
    result = engine.embed_images(images, batch_size=2)

    print(f"\nEmbedded {len(images)} images:")
    print(f"  Processing time: {result['batch_processing_time_ms']:.1f}ms")
    print(f"  Input type: {result['input_type']}")
    print(f"  CLS tokens shape: {result['cls_tokens'].shape}")
    print(f"\nPer-image details:")
    for i, (emb, seq_len) in enumerate(zip(result['embeddings'], result['seq_lengths'])):
        print(f"  Image {i+1}: {emb.shape} ({seq_len} tokens)")


def example_text_embedding():
    """Example 4: Embedding text."""
    print("\n" + "="*70)
    print("Example 4: Text Embedding")
    print("="*70)

    engine = ColPaliEngine(device="cpu", precision="fp16")

    # Text chunks (in production, extracted from documents)
    texts = [
        "Quarterly revenue increased by 25% year-over-year, driven by strong growth in enterprise sales.",
        "The company's financial performance exceeded expectations with record earnings.",
        "Market conditions remain favorable for continued expansion in Q2."
    ]

    # Embed texts
    result = engine.embed_texts(texts, batch_size=2)

    print(f"\nEmbedded {len(texts)} text chunks:")
    print(f"  Processing time: {result['batch_processing_time_ms']:.1f}ms")
    print(f"  Input type: {result['input_type']}")
    print(f"  CLS tokens shape: {result['cls_tokens'].shape}")
    print(f"\nPer-chunk details:")
    for i, (emb, seq_len) in enumerate(zip(result['embeddings'], result['seq_lengths'])):
        print(f"  Chunk {i+1}: {emb.shape} ({seq_len} tokens)")
        print(f"    Text: {texts[i][:60]}...")


def example_query_embedding():
    """Example 5: Embedding search query."""
    print("\n" + "="*70)
    print("Example 5: Query Embedding")
    print("="*70)

    engine = ColPaliEngine(device="cpu", precision="fp16")

    # Search query
    query = "quarterly revenue growth"

    # Embed query
    result = engine.embed_query(query)

    print(f"\nQuery: '{query}'")
    print(f"  Embeddings shape: {result['embeddings'].shape}")
    print(f"  CLS token shape: {result['cls_token'].shape}")
    print(f"  Sequence length: {result['seq_length']} tokens")
    print(f"  Processing time: {result['processing_time_ms']:.1f}ms")


def example_late_interaction_scoring():
    """Example 6: Late interaction scoring with MaxSim."""
    print("\n" + "="*70)
    print("Example 6: Late Interaction Scoring (MaxSim)")
    print("="*70)

    engine = ColPaliEngine(device="cpu", precision="fp16")

    # Search query
    query = "revenue growth trends"

    # Document collection
    documents = [
        "Revenue increased by 25% in Q1 2024, showing strong growth momentum.",
        "The company reported declining sales in the last quarter.",
        "Weather conditions affected agricultural output in the region.",
        "Market analysis suggests continued revenue expansion opportunities.",
    ]

    # Embed query
    query_result = engine.embed_query(query)
    print(f"\nQuery: '{query}'")
    print(f"  Query embeddings: {query_result['embeddings'].shape}")

    # Embed documents
    doc_result = engine.embed_texts(documents)
    print(f"\nDocuments: {len(documents)}")
    for i, doc in enumerate(documents):
        print(f"  {i+1}. {doc[:60]}...")

    # Score documents against query
    score_result = engine.score_multi_vector(
        query_result['embeddings'],
        doc_result['embeddings'],
        use_gpu=True
    )

    print(f"\nScoring results:")
    print(f"  Scoring time: {score_result['scoring_time_ms']:.1f}ms")
    print(f"  Candidates scored: {score_result['num_candidates']}")

    # Rank documents by score
    ranked = sorted(enumerate(score_result['scores']), key=lambda x: x[1], reverse=True)

    print(f"\nRanked results:")
    for rank, (doc_idx, score) in enumerate(ranked, 1):
        print(f"  {rank}. Score: {score:.4f} - {documents[doc_idx][:60]}...")


def example_end_to_end_workflow():
    """Example 7: Complete end-to-end workflow."""
    print("\n" + "="*70)
    print("Example 7: End-to-End Search Workflow")
    print("="*70)

    # Initialize engine with INT8 for faster processing
    print("\nInitializing engine with INT8 quantization...")
    engine = ColPaliEngine(device="cpu", precision="int8")

    # Simulate document processing
    print("\n1. Processing documents...")

    # Create dummy document pages (visual)
    doc_pages = [Image.new("RGB", (1024, 1024), color=c)
                 for c in ["white", "lightgray", "silver"]]

    # Embed document pages
    page_embeddings = engine.embed_images(doc_pages, batch_size=2)
    print(f"   Embedded {len(doc_pages)} pages in {page_embeddings['batch_processing_time_ms']:.0f}ms")

    # Extract text content (in production, from OCR/PDF)
    text_chunks = [
        "Financial summary showing revenue and profit trends.",
        "Quarterly performance metrics and KPIs.",
        "Strategic initiatives for market expansion."
    ]

    # Embed text content
    text_embeddings = engine.embed_texts(text_chunks, batch_size=2)
    print(f"   Embedded {len(text_chunks)} text chunks in {text_embeddings['batch_processing_time_ms']:.0f}ms")

    # Combine all embeddings
    all_embeddings = page_embeddings['embeddings'] + text_embeddings['embeddings']

    # Search
    print("\n2. Processing search query...")
    query = "quarterly financial performance"
    query_result = engine.embed_query(query)
    print(f"   Query embedded in {query_result['processing_time_ms']:.0f}ms")

    # Score and rank
    print("\n3. Scoring and ranking results...")
    scores = engine.score_multi_vector(
        query_result['embeddings'],
        all_embeddings,
        use_gpu=True
    )
    print(f"   Scored {scores['num_candidates']} items in {scores['scoring_time_ms']:.0f}ms")

    # Display top results
    ranked = sorted(enumerate(scores['scores']), key=lambda x: x[1], reverse=True)
    print(f"\nTop 3 results for '{query}':")
    for rank, (idx, score) in enumerate(ranked[:3], 1):
        item_type = "Page" if idx < len(doc_pages) else "Text"
        content = text_chunks[idx - len(doc_pages)] if idx >= len(doc_pages) else f"Image {idx+1}"
        print(f"  {rank}. [{item_type}] Score: {score:.4f}")
        if item_type == "Text":
            print(f"      {content[:70]}...")

    # Memory management
    print("\n4. Cleanup...")
    engine.clear_cache()
    print("   GPU cache cleared")


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("ColPali Embeddings Module - Example Usage")
    print("="*70)
    print("\nNOTE: Wave 2 uses mock implementations.")
    print("Install ColPali for production: pip install git+https://github.com/illuin-tech/colpali.git")

    try:
        example_basic_initialization()
        example_custom_config()
        example_image_embedding()
        example_text_embedding()
        example_query_embedding()
        example_late_interaction_scoring()
        example_end_to_end_workflow()

        print("\n" + "="*70)
        print("All examples completed successfully!")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
