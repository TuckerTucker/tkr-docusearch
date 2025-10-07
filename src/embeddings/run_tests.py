"""
Test runner for embeddings module.

Run this script to execute all unit tests:
    python3 run_tests.py
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import numpy as np
from PIL import Image

# Import modules
from embeddings.colpali_wrapper import ColPaliEngine
from embeddings.types import EmbeddingOutput, BatchEmbeddingOutput, ScoringOutput
from embeddings.exceptions import (
    EmbeddingGenerationError,
    ScoringError,
    ModelLoadError
)
from embeddings.scoring import maxsim_score, validate_embedding_shape
from config.model_config import ModelConfig


class TestModelLoading(unittest.TestCase):
    """Test model loading and initialization."""

    def test_default_initialization(self):
        """Test default model initialization."""
        engine = ColPaliEngine()
        self.assertIsNotNone(engine.model)
        self.assertIsNotNone(engine.processor)
        self.assertIsNotNone(engine.config)

    def test_custom_config(self):
        """Test initialization with custom config."""
        config = ModelConfig(
            name="vidore/colqwen2-v0.1",
            device="cpu",
            precision="int8",
            batch_size_visual=2,
            batch_size_text=4
        )
        engine = ColPaliEngine(config=config)
        self.assertEqual(engine.config.device, "cpu")
        self.assertEqual(engine.config.precision, "int8")
        self.assertEqual(engine.config.batch_size_visual, 2)

    def test_device_fallback(self):
        """Test device fallback to CPU."""
        # Request valid device that may not be available (e.g., cuda on Mac)
        config = ModelConfig(device="cuda", auto_fallback=True)
        # Should fallback to CPU if cuda not available
        self.assertIn(config.device, ["cuda", "cpu"])

    def test_get_model_info(self):
        """Test model info retrieval."""
        engine = ColPaliEngine()
        info = engine.get_model_info()

        self.assertIn("model_name", info)
        self.assertIn("device", info)
        self.assertIn("dtype", info)
        self.assertIn("memory_allocated_mb", info)
        self.assertIn("is_loaded", info)
        self.assertTrue(info["is_loaded"])


class TestImageEmbedding(unittest.TestCase):
    """Test image embedding generation."""

    def setUp(self):
        """Set up test engine."""
        self.engine = ColPaliEngine(device="cpu", precision="fp16")

    def test_single_image_embedding(self):
        """Test embedding single image."""
        # Create dummy image
        image = Image.new("RGB", (100, 100), color="white")

        result = self.engine.embed_images([image])

        self.assertIsInstance(result, dict)
        self.assertIn("embeddings", result)
        self.assertIn("cls_tokens", result)
        self.assertIn("seq_lengths", result)
        self.assertIn("input_type", result)

        # Check shapes
        self.assertEqual(len(result["embeddings"]), 1)
        self.assertEqual(result["embeddings"][0].shape[1], 768)
        self.assertEqual(result["cls_tokens"].shape, (1, 768))
        self.assertEqual(result["input_type"], "visual")

    def test_batch_image_embedding(self):
        """Test batch image embedding."""
        # Create dummy images
        images = [Image.new("RGB", (100, 100), color="white") for _ in range(5)]

        result = self.engine.embed_images(images, batch_size=2)

        self.assertEqual(len(result["embeddings"]), 5)
        self.assertEqual(len(result["seq_lengths"]), 5)
        self.assertEqual(result["cls_tokens"].shape[0], 5)

        # Check sequence lengths are realistic
        for seq_len in result["seq_lengths"]:
            self.assertGreaterEqual(seq_len, 80)
            self.assertLessEqual(seq_len, 120)

    def test_empty_image_list_error(self):
        """Test error on empty image list."""
        with self.assertRaises(ValueError):
            self.engine.embed_images([])

    def test_cls_token_extraction(self):
        """Test CLS token is first token of embeddings."""
        image = Image.new("RGB", (100, 100), color="white")
        result = self.engine.embed_images([image])

        # CLS token should match first token of embeddings
        np.testing.assert_array_almost_equal(
            result["cls_tokens"][0],
            result["embeddings"][0][0]
        )


class TestTextEmbedding(unittest.TestCase):
    """Test text embedding generation."""

    def setUp(self):
        """Set up test engine."""
        self.engine = ColPaliEngine(device="cpu", precision="fp16")

    def test_single_text_embedding(self):
        """Test embedding single text."""
        text = "This is a test document with some content."

        result = self.engine.embed_texts([text])

        self.assertIsInstance(result, dict)
        self.assertEqual(len(result["embeddings"]), 1)
        self.assertEqual(result["embeddings"][0].shape[1], 768)
        self.assertEqual(result["input_type"], "text")

    def test_batch_text_embedding(self):
        """Test batch text embedding."""
        texts = [
            "First document about revenue growth.",
            "Second document about quarterly earnings.",
            "Third document about financial performance."
        ]

        result = self.engine.embed_texts(texts, batch_size=2)

        self.assertEqual(len(result["embeddings"]), 3)
        self.assertEqual(result["cls_tokens"].shape[0], 3)

        # Check sequence lengths are realistic for text
        for seq_len in result["seq_lengths"]:
            self.assertGreaterEqual(seq_len, 50)
            self.assertLessEqual(seq_len, 80)

    def test_empty_text_list_error(self):
        """Test error on empty text list."""
        with self.assertRaises(ValueError):
            self.engine.embed_texts([])

    def test_empty_string_error(self):
        """Test error on empty string."""
        with self.assertRaises(ValueError):
            self.engine.embed_texts([""])

    def test_processing_time_recorded(self):
        """Test processing time is recorded."""
        texts = ["Test document."]
        result = self.engine.embed_texts(texts)

        self.assertIn("batch_processing_time_ms", result)
        self.assertGreater(result["batch_processing_time_ms"], 0)


class TestQueryEmbedding(unittest.TestCase):
    """Test query embedding generation."""

    def setUp(self):
        """Set up test engine."""
        self.engine = ColPaliEngine(device="cpu", precision="fp16")

    def test_query_embedding(self):
        """Test embedding search query."""
        query = "quarterly revenue growth"

        result = self.engine.embed_query(query)

        self.assertIsInstance(result, dict)
        self.assertIn("embeddings", result)
        self.assertIn("cls_token", result)
        self.assertIn("seq_length", result)
        self.assertIn("input_type", result)

        # Check shapes
        self.assertEqual(result["embeddings"].shape[1], 768)
        self.assertEqual(result["cls_token"].shape, (768,))
        self.assertEqual(result["input_type"], "text")

        # Query should be shorter than document
        self.assertLessEqual(result["seq_length"], 80)

    def test_empty_query_error(self):
        """Test error on empty query."""
        with self.assertRaises(ValueError):
            self.engine.embed_query("")

    def test_query_processing_time(self):
        """Test query processing is fast."""
        query = "test query"
        result = self.engine.embed_query(query)

        # Query processing should be fast (mock should be <1000ms)
        self.assertLess(result["processing_time_ms"], 1000)


class TestLateInteractionScoring(unittest.TestCase):
    """Test MaxSim late interaction scoring."""

    def setUp(self):
        """Set up test engine and embeddings."""
        self.engine = ColPaliEngine(device="cpu", precision="fp16")

    def test_single_document_scoring(self):
        """Test scoring single document."""
        # Generate query and document embeddings
        query = "test query"
        doc_text = "test document content"

        query_result = self.engine.embed_query(query)
        doc_result = self.engine.embed_texts([doc_text])

        # Score
        score_result = self.engine.score_multi_vector(
            query_result["embeddings"],
            doc_result["embeddings"]
        )

        self.assertIsInstance(score_result, dict)
        self.assertIn("scores", score_result)
        self.assertIn("scoring_time_ms", score_result)
        self.assertIn("num_candidates", score_result)

        self.assertEqual(len(score_result["scores"]), 1)
        self.assertEqual(score_result["num_candidates"], 1)

        # Score should be in [0, 1]
        score = score_result["scores"][0]
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_batch_document_scoring(self):
        """Test scoring multiple documents."""
        query_result = self.engine.embed_query("revenue growth")

        docs = [
            "Revenue increased by 20% this quarter.",
            "The company showed strong growth.",
            "Unrelated content about weather."
        ]
        doc_result = self.engine.embed_texts(docs)

        score_result = self.engine.score_multi_vector(
            query_result["embeddings"],
            doc_result["embeddings"]
        )

        self.assertEqual(len(score_result["scores"]), 3)

        # All scores should be in valid range
        for score in score_result["scores"]:
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)

    def test_maxsim_algorithm(self):
        """Test MaxSim algorithm directly."""
        # Create simple test embeddings
        query_emb = np.random.randn(10, 768).astype(np.float32)
        doc_emb = np.random.randn(20, 768).astype(np.float32)

        score = maxsim_score(query_emb, doc_emb)

        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_identical_embeddings_high_score(self):
        """Test identical embeddings produce high score."""
        # Create identical embeddings
        emb = np.random.randn(10, 768).astype(np.float32)

        score = maxsim_score(emb, emb)

        # Should be very close to 1.0 for identical embeddings
        self.assertGreater(score, 0.95)

    def test_scoring_time_performance(self):
        """Test scoring is fast."""
        query_result = self.engine.embed_query("test")

        # Create 10 documents
        docs = [f"Document {i}" for i in range(10)]
        doc_result = self.engine.embed_texts(docs)

        score_result = self.engine.score_multi_vector(
            query_result["embeddings"],
            doc_result["embeddings"]
        )

        # Should be fast (mock should be <1s for 10 docs)
        self.assertLess(score_result["scoring_time_ms"], 1000)


class TestEmbeddingValidation(unittest.TestCase):
    """Test embedding validation utilities."""

    def test_valid_embedding_shape(self):
        """Test validation passes for valid embeddings."""
        emb = np.random.randn(50, 768).astype(np.float32)
        # Should not raise
        validate_embedding_shape(emb)

    def test_wrong_dimensions_error(self):
        """Test error on wrong number of dimensions."""
        emb = np.random.randn(768)  # 1D instead of 2D
        with self.assertRaises(ValueError):
            validate_embedding_shape(emb)

    def test_wrong_embedding_dim_error(self):
        """Test error on wrong embedding dimension."""
        emb = np.random.randn(50, 512).astype(np.float32)  # 512 instead of 768
        with self.assertRaises(ValueError):
            validate_embedding_shape(emb)

    def test_zero_sequence_length_error(self):
        """Test error on zero sequence length."""
        emb = np.random.randn(0, 768).astype(np.float32)
        with self.assertRaises(ValueError):
            validate_embedding_shape(emb)


class TestErrorHandling(unittest.TestCase):
    """Test error handling."""

    def setUp(self):
        """Set up test engine."""
        self.engine = ColPaliEngine(device="cpu")

    def test_invalid_embedding_shapes_in_scoring(self):
        """Test error on incompatible embedding shapes."""
        query_emb = np.random.randn(10, 768).astype(np.float32)
        doc_emb = np.random.randn(20, 512).astype(np.float32)  # Wrong dim

        with self.assertRaises((ValueError, ScoringError)):
            self.engine.score_multi_vector(query_emb, [doc_emb])

    def test_clear_cache_no_error(self):
        """Test cache clearing doesn't error."""
        # Should not raise even if no GPU available
        self.engine.clear_cache()


class TestConfigurationEdgeCases(unittest.TestCase):
    """Test configuration edge cases."""

    def test_quantization_flag(self):
        """Test quantization flag is set correctly."""
        engine_fp16 = ColPaliEngine(precision="fp16")
        self.assertFalse(engine_fp16.config.is_quantized)

        engine_int8 = ColPaliEngine(precision="int8")
        self.assertTrue(engine_int8.config.is_quantized)

    def test_memory_estimate(self):
        """Test memory estimates are reasonable."""
        engine_fp16 = ColPaliEngine(precision="fp16")
        info_fp16 = engine_fp16.get_model_info()

        engine_int8 = ColPaliEngine(precision="int8")
        info_int8 = engine_int8.get_model_info()

        # INT8 should use roughly half the memory of FP16
        self.assertLess(
            info_int8["memory_allocated_mb"],
            info_fp16["memory_allocated_mb"]
        )


if __name__ == '__main__':
    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
    print("="*70)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
