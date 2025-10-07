"""
Verification script for embedding-agent implementation.

This script validates that all requirements from the integration contract
have been met and the implementation is ready for integration.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from embeddings import (
    ColPaliEngine,
    EmbeddingOutput,
    BatchEmbeddingOutput,
    ScoringOutput,
    EmbeddingError,
    ModelLoadError,
    DeviceError,
    EmbeddingGenerationError,
    ScoringError,
    QuantizationError,
    maxsim_score,
    batch_maxsim_scores,
    validate_embedding_shape,
    load_model
)
from config import ModelConfig
from PIL import Image
import numpy as np


def check_section(title):
    """Print section header."""
    print("\n" + "="*70)
    print(f"✓ {title}")
    print("="*70)


def verify_imports():
    """Verify all required exports are available."""
    check_section("Verifying Imports")

    required = [
        'ColPaliEngine',
        'EmbeddingOutput',
        'BatchEmbeddingOutput',
        'ScoringOutput',
        'EmbeddingError',
        'ModelLoadError',
        'DeviceError',
        'EmbeddingGenerationError',
        'ScoringError',
        'QuantizationError',
        'maxsim_score',
        'batch_maxsim_scores',
        'validate_embedding_shape',
        'load_model',
    ]

    print(f"Checking {len(required)} required exports...")
    for name in required:
        assert name in globals(), f"Missing export: {name}"
        print(f"  ✓ {name}")

    print(f"\n✅ All {len(required)} exports available")


def verify_api_structure():
    """Verify ColPaliEngine has all required methods."""
    check_section("Verifying API Structure")

    engine = ColPaliEngine(device="cpu")

    required_methods = [
        '__init__',
        'embed_images',
        'embed_texts',
        'embed_query',
        'score_multi_vector',
        'get_model_info',
        'clear_cache',
    ]

    print(f"Checking {len(required_methods)} required methods...")
    for method_name in required_methods:
        assert hasattr(engine, method_name), f"Missing method: {method_name}"
        method = getattr(engine, method_name)
        assert callable(method), f"Not callable: {method_name}"
        print(f"  ✓ {method_name}()")

    print(f"\n✅ All {len(required_methods)} methods present")


def verify_output_shapes():
    """Verify output shapes match contract."""
    check_section("Verifying Output Shapes")

    engine = ColPaliEngine(device="cpu")

    # Test image embedding
    print("\nTesting image embedding output shapes...")
    images = [Image.new("RGB", (100, 100)) for _ in range(3)]
    img_result = engine.embed_images(images)

    assert isinstance(img_result, dict)
    assert 'embeddings' in img_result
    assert 'cls_tokens' in img_result
    assert 'seq_lengths' in img_result
    assert len(img_result['embeddings']) == 3
    assert img_result['cls_tokens'].shape == (3, 768)
    for emb in img_result['embeddings']:
        assert emb.shape[1] == 768, f"Expected 768 dims, got {emb.shape[1]}"
    print("  ✓ Image embeddings: (seq_length, 768)")
    print("  ✓ CLS tokens: (batch_size, 768)")

    # Test text embedding
    print("\nTesting text embedding output shapes...")
    texts = ["Test text 1", "Test text 2"]
    text_result = engine.embed_texts(texts)

    assert len(text_result['embeddings']) == 2
    assert text_result['cls_tokens'].shape == (2, 768)
    for emb in text_result['embeddings']:
        assert emb.shape[1] == 768
    print("  ✓ Text embeddings: (seq_length, 768)")
    print("  ✓ CLS tokens: (batch_size, 768)")

    # Test query embedding
    print("\nTesting query embedding output shapes...")
    query_result = engine.embed_query("test query")

    assert query_result['embeddings'].ndim == 2
    assert query_result['embeddings'].shape[1] == 768
    assert query_result['cls_token'].shape == (768,)
    print("  ✓ Query embeddings: (seq_length, 768)")
    print("  ✓ Query CLS token: (768,)")

    # Test scoring
    print("\nTesting scoring output...")
    score_result = engine.score_multi_vector(
        query_result['embeddings'],
        text_result['embeddings']
    )

    assert 'scores' in score_result
    assert 'scoring_time_ms' in score_result
    assert 'num_candidates' in score_result
    assert len(score_result['scores']) == 2
    for score in score_result['scores']:
        assert 0.0 <= score <= 1.0, f"Score {score} not in [0, 1]"
    print("  ✓ Scores in [0, 1] range")
    print("  ✓ Correct number of scores")

    print("\n✅ All output shapes correct")


def verify_sequence_lengths():
    """Verify sequence lengths are in expected ranges."""
    check_section("Verifying Sequence Lengths")

    engine = ColPaliEngine(device="cpu")

    # Visual embeddings
    print("\nTesting visual sequence lengths...")
    images = [Image.new("RGB", (100, 100)) for _ in range(5)]
    img_result = engine.embed_images(images)

    visual_range = (80, 120)
    for i, seq_len in enumerate(img_result['seq_lengths']):
        assert visual_range[0] <= seq_len <= visual_range[1], \
            f"Visual seq_len {seq_len} not in range {visual_range}"
    print(f"  ✓ Visual: {visual_range} tokens ✓")
    print(f"    Actual: {img_result['seq_lengths']}")

    # Text embeddings
    print("\nTesting text sequence lengths...")
    texts = ["Sample text " * 10 for _ in range(5)]
    text_result = engine.embed_texts(texts)

    text_range = (50, 80)
    for i, seq_len in enumerate(text_result['seq_lengths']):
        assert text_range[0] <= seq_len <= text_range[1], \
            f"Text seq_len {seq_len} not in range {text_range}"
    print(f"  ✓ Text: {text_range} tokens ✓")
    print(f"    Actual: {text_result['seq_lengths']}")

    # Query embeddings
    print("\nTesting query sequence lengths...")
    queries = ["short query", "somewhat longer query with more words"]
    for query in queries:
        result = engine.embed_query(query)
        assert result['seq_length'] <= 80, \
            f"Query seq_len {result['seq_length']} exceeds 80"
    print(f"  ✓ Query: ≤80 tokens ✓")

    print("\n✅ All sequence lengths in expected ranges")


def verify_error_handling():
    """Verify error handling works correctly."""
    check_section("Verifying Error Handling")

    engine = ColPaliEngine(device="cpu")

    # Test empty inputs
    print("\nTesting error handling...")
    try:
        engine.embed_images([])
        assert False, "Should raise ValueError on empty images"
    except ValueError:
        print("  ✓ Empty images raises ValueError")

    try:
        engine.embed_texts([])
        assert False, "Should raise ValueError on empty texts"
    except ValueError:
        print("  ✓ Empty texts raises ValueError")

    try:
        engine.embed_query("")
        assert False, "Should raise ValueError on empty query"
    except ValueError:
        print("  ✓ Empty query raises ValueError")

    # Test invalid shapes
    try:
        bad_emb = np.random.randn(10, 512).astype(np.float32)  # Wrong dim
        validate_embedding_shape(bad_emb)
        assert False, "Should raise ValueError on wrong dimension"
    except ValueError:
        print("  ✓ Wrong embedding dim raises ValueError")

    print("\n✅ Error handling works correctly")


def verify_maxsim_algorithm():
    """Verify MaxSim algorithm correctness."""
    check_section("Verifying MaxSim Algorithm")

    print("\nTesting MaxSim properties...")

    # Test 1: Identical embeddings should score ~1.0
    emb = np.random.randn(10, 768).astype(np.float32)
    score = maxsim_score(emb, emb)
    assert score > 0.95, f"Identical embeddings should score >0.95, got {score}"
    print(f"  ✓ Identical embeddings: {score:.4f} (>0.95)")

    # Test 2: Random embeddings should score moderate
    emb1 = np.random.randn(10, 768).astype(np.float32)
    emb2 = np.random.randn(20, 768).astype(np.float32)
    score = maxsim_score(emb1, emb2)
    assert 0.0 <= score <= 1.0, f"Score {score} not in [0, 1]"
    print(f"  ✓ Random embeddings: {score:.4f} (in [0, 1])")

    # Test 3: Batch scoring
    query = np.random.randn(10, 768).astype(np.float32)
    docs = [np.random.randn(20, 768).astype(np.float32) for _ in range(5)]
    scores = batch_maxsim_scores(query, docs)
    assert len(scores) == 5
    assert all(0.0 <= s <= 1.0 for s in scores)
    print(f"  ✓ Batch scoring: {len(scores)} scores")

    print("\n✅ MaxSim algorithm verified")


def verify_device_management():
    """Verify device management and fallback."""
    check_section("Verifying Device Management")

    print("\nTesting device configurations...")

    # CPU device
    engine_cpu = ColPaliEngine(device="cpu")
    assert engine_cpu.config.device == "cpu"
    print("  ✓ CPU device initialization")

    # Config with fallback
    config = ModelConfig(device="cuda", auto_fallback=True)
    # Should fallback to CPU if CUDA unavailable
    assert config.device in ["cuda", "cpu"]
    print(f"  ✓ Device fallback: {config.device}")

    # Get model info
    info = engine_cpu.get_model_info()
    assert 'device' in info
    assert 'memory_allocated_mb' in info
    print("  ✓ Model info retrieval")

    print("\n✅ Device management verified")


def verify_quantization():
    """Verify quantization support."""
    check_section("Verifying Quantization Support")

    print("\nTesting quantization modes...")

    # FP16
    engine_fp16 = ColPaliEngine(precision="fp16")
    assert not engine_fp16.config.is_quantized
    info_fp16 = engine_fp16.get_model_info()
    print(f"  ✓ FP16: {info_fp16['memory_allocated_mb']:.0f}MB")

    # INT8
    engine_int8 = ColPaliEngine(precision="int8")
    assert engine_int8.config.is_quantized
    info_int8 = engine_int8.get_model_info()
    print(f"  ✓ INT8: {info_int8['memory_allocated_mb']:.0f}MB")

    # INT8 should use less memory
    assert info_int8['memory_allocated_mb'] < info_fp16['memory_allocated_mb']
    print("  ✓ INT8 uses less memory than FP16")

    print("\n✅ Quantization support verified")


def verify_cls_token_extraction():
    """Verify CLS token is correctly extracted."""
    check_section("Verifying CLS Token Extraction")

    engine = ColPaliEngine(device="cpu")

    print("\nTesting CLS token extraction...")

    # Images
    images = [Image.new("RGB", (100, 100))]
    img_result = engine.embed_images(images)
    np.testing.assert_array_almost_equal(
        img_result['cls_tokens'][0],
        img_result['embeddings'][0][0]
    )
    print("  ✓ Image CLS token = first token")

    # Text
    texts = ["Test text"]
    text_result = engine.embed_texts(texts)
    np.testing.assert_array_almost_equal(
        text_result['cls_tokens'][0],
        text_result['embeddings'][0][0]
    )
    print("  ✓ Text CLS token = first token")

    # Query
    query_result = engine.embed_query("test")
    np.testing.assert_array_almost_equal(
        query_result['cls_token'],
        query_result['embeddings'][0]
    )
    print("  ✓ Query CLS token = first token")

    print("\n✅ CLS token extraction verified")


def main():
    """Run all verification checks."""
    print("\n" + "="*70)
    print("Embedding-Agent Implementation Verification")
    print("="*70)
    print("\nRunning comprehensive verification...")

    try:
        verify_imports()
        verify_api_structure()
        verify_output_shapes()
        verify_sequence_lengths()
        verify_error_handling()
        verify_maxsim_algorithm()
        verify_device_management()
        verify_quantization()
        verify_cls_token_extraction()

        print("\n" + "="*70)
        print("✅ ALL VERIFICATION CHECKS PASSED")
        print("="*70)
        print("\nImplementation Status: READY FOR INTEGRATION")
        print("\nNext Steps:")
        print("  1. Processing-agent can import ColPaliEngine")
        print("  2. Search-agent can use MaxSim scoring")
        print("  3. Storage-agent can design two-stage search")
        print("\n" + "="*70 + "\n")

        return 0

    except AssertionError as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
