"""
Unit tests for ColPali wrapper module.

Tests cover:
- Model initialization (CPU, MPS, CUDA)
- Image embedding generation (single and batch)
- Text embedding generation
- Query embedding generation
- Batch processing with various batch sizes
- Error handling (empty inputs, invalid data)
- Device selection and fallback
- Model configuration validation
- Embedding dimension verification
- Multi-vector scoring (MaxSim)
- Memory management

Target Coverage: 80%+
"""

from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest
from PIL import Image

from tkr_docusearch.config.model_config import ModelConfig
from tkr_docusearch.embeddings.colpali_wrapper import ColPaliEngine
from tkr_docusearch.embeddings.exceptions import EmbeddingGenerationError, ModelLoadError, ScoringError

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_torch():
    """Mock PyTorch for testing without actual GPU dependencies."""
    with patch("tkr_docusearch.embeddings.model_loader.torch") as mock_torch_module:
        # Configure MPS availability
        mock_torch_module.backends.mps.is_available.return_value = True
        mock_torch_module.cuda.is_available.return_value = False
        yield mock_torch_module


@pytest.fixture
def mock_model_loader():
    """Mock model loader to return mock model and processor."""
    with patch("tkr_docusearch.embeddings.colpali_wrapper.load_model") as mock_loader:
        # Create mock model
        mock_model = MagicMock()
        mock_model.embed_batch = Mock(
            side_effect=lambda inputs, input_type: _generate_mock_embeddings(
                len(inputs), input_type
            )
        )

        # Create mock processor
        mock_processor = MagicMock()

        mock_loader.return_value = (mock_model, mock_processor)
        yield mock_loader


@pytest.fixture
def mock_memory_estimate():
    """Mock memory estimation function."""
    with patch("tkr_docusearch.embeddings.colpali_wrapper.estimate_memory_usage") as mock_estimate:
        mock_estimate.return_value = 8000.0  # 8GB
        yield mock_estimate


@pytest.fixture
def engine(mock_model_loader, mock_memory_estimate):
    """Create a ColPaliEngine instance with mocked dependencies."""
    return ColPaliEngine(
        model_name="vidore/colqwen2-v0.1",
        device="mps",
        precision="fp16",
    )


@pytest.fixture
def sample_images():
    """Create sample PIL images for testing."""
    return [
        Image.new("RGB", (800, 1000), color="red"),
        Image.new("RGB", (800, 1000), color="green"),
        Image.new("RGB", (800, 1000), color="blue"),
    ]


@pytest.fixture
def sample_texts():
    """Create sample text chunks for testing."""
    return [
        "This is the first text chunk for embedding.",
        "Another sample text with different content.",
        "The third and final text sample.",
    ]


# ============================================================================
# Helper Functions
# ============================================================================


def _generate_mock_embeddings(batch_size: int, input_type: str):
    """Generate mock embeddings with realistic shapes."""
    embeddings = []
    seq_lengths = []

    for _ in range(batch_size):
        # Realistic sequence lengths
        if input_type == "visual":
            seq_len = np.random.randint(80, 120)
        else:
            seq_len = np.random.randint(50, 80)

        # Generate normalized random embeddings
        emb = np.random.randn(seq_len, 768).astype(np.float32)
        emb = emb / (np.linalg.norm(emb, axis=1, keepdims=True) + 1e-8)

        embeddings.append(emb)
        seq_lengths.append(seq_len)

    return embeddings, seq_lengths


# ============================================================================
# Tests for ColPaliEngine.__init__()
# ============================================================================


class TestColPaliEngineInit:
    """Test ColPaliEngine initialization."""

    def test_init_with_defaults(self, mock_model_loader, mock_memory_estimate):
        """Test initialization with default parameters."""
        engine = ColPaliEngine()

        assert engine.config.name == "vidore/colqwen2-v0.1"
        assert engine.config.device in ["mps", "cuda", "cpu"]
        assert engine.config.precision == "fp16"
        assert hasattr(engine, "model")
        assert hasattr(engine, "processor")

    def test_init_with_custom_config(self, mock_model_loader, mock_memory_estimate):
        """Test initialization with custom configuration."""
        config = ModelConfig(
            name="vidore/colpali-v1.2",
            device="cpu",
            precision="int8",
            batch_size_visual=2,
            batch_size_text=4,
        )

        engine = ColPaliEngine(config=config)

        assert engine.config.name == "vidore/colpali-v1.2"
        assert engine.config.device == "cpu"
        assert engine.config.precision == "int8"
        assert engine.config.batch_size_visual == 2
        assert engine.config.batch_size_text == 4

    def test_init_with_custom_params(self, mock_model_loader, mock_memory_estimate):
        """Test initialization with custom parameters."""
        engine = ColPaliEngine(
            model_name="custom-model",
            device="cpu",
            precision="int8",
            cache_dir="/custom/cache",
        )

        assert engine.config.name == "custom-model"
        assert engine.config.device == "cpu"
        assert engine.config.precision == "int8"
        assert engine.config.cache_dir == "/custom/cache"

    def test_init_with_quantization(self, mock_model_loader, mock_memory_estimate):
        """Test initialization with quantization parameter."""
        engine = ColPaliEngine(quantization="int8")

        assert engine.config.precision == "int8"
        assert engine.config.is_quantized is True

    def test_init_loads_model(self, mock_model_loader, mock_memory_estimate):
        """Test that initialization loads the model."""
        ColPaliEngine()

        mock_model_loader.assert_called_once()
        call_config = mock_model_loader.call_args[0][0]
        assert isinstance(call_config, ModelConfig)

    def test_init_estimates_memory(self, mock_model_loader, mock_memory_estimate):
        """Test that initialization estimates memory usage."""
        engine = ColPaliEngine()

        assert hasattr(engine, "_memory_allocated")
        assert engine._memory_allocated == 8000.0
        mock_memory_estimate.assert_called_once()

    def test_init_with_model_load_error(self, mock_memory_estimate):
        """Test initialization handles model load errors."""
        with patch("tkr_docusearch.embeddings.colpali_wrapper.load_model") as mock_loader:
            mock_loader.side_effect = ModelLoadError("Failed to load model")

            with pytest.raises(ModelLoadError):
                ColPaliEngine()


# ============================================================================
# Tests for embed_images()
# ============================================================================


class TestEmbedImages:
    """Test image embedding generation."""

    def test_embed_images_single(self, engine, sample_images):
        """Test embedding a single image."""
        result = engine.embed_images([sample_images[0]])

        assert "embeddings" in result
        assert "cls_tokens" in result
        assert "seq_lengths" in result
        assert "input_type" in result
        assert "batch_processing_time_ms" in result

        assert len(result["embeddings"]) == 1
        assert result["cls_tokens"].shape == (1, 768)
        assert len(result["seq_lengths"]) == 1
        assert result["input_type"] == "visual"
        assert result["batch_processing_time_ms"] > 0

    def test_embed_images_batch(self, engine, sample_images):
        """Test embedding multiple images."""
        result = engine.embed_images(sample_images)

        assert len(result["embeddings"]) == 3
        assert result["cls_tokens"].shape == (3, 768)
        assert len(result["seq_lengths"]) == 3

        # Check each embedding has correct shape
        for emb in result["embeddings"]:
            assert emb.ndim == 2
            assert emb.shape[1] == 768
            assert 80 <= emb.shape[0] <= 120  # Realistic seq_length

    def test_embed_images_custom_batch_size(self, engine, sample_images):
        """Test embedding with custom batch size."""
        # Create larger batch
        images = sample_images * 3  # 9 images

        result = engine.embed_images(images, batch_size=2)

        assert len(result["embeddings"]) == 9
        assert result["cls_tokens"].shape == (9, 768)

    def test_embed_images_uses_config_batch_size(self, engine, sample_images):
        """Test that None batch_size uses config default."""
        result = engine.embed_images(sample_images, batch_size=None)

        assert len(result["embeddings"]) == 3
        # Should use config.batch_size_visual (default 4)

    def test_embed_images_empty_list(self, engine):
        """Test that empty image list raises ValueError."""
        with pytest.raises(ValueError, match="Images list cannot be empty"):
            engine.embed_images([])

    def test_embed_images_cls_tokens_extracted(self, engine, sample_images):
        """Test that CLS tokens are properly extracted."""
        result = engine.embed_images(sample_images)

        # CLS tokens should be first token of each embedding
        for i, emb in enumerate(result["embeddings"]):
            assert np.allclose(result["cls_tokens"][i], emb[0])

    def test_embed_images_timing_recorded(self, engine, sample_images):
        """Test that processing time is recorded."""
        result = engine.embed_images(sample_images)

        assert "batch_processing_time_ms" in result
        assert result["batch_processing_time_ms"] > 0
        assert isinstance(result["batch_processing_time_ms"], float)

    def test_embed_images_error_handling(self, engine):
        """Test error handling when embedding generation fails."""
        engine.model.embed_batch = Mock(side_effect=RuntimeError("GPU OOM"))

        with pytest.raises(EmbeddingGenerationError, match="Failed to embed images"):
            engine.embed_images([Image.new("RGB", (800, 1000))])


# ============================================================================
# Tests for embed_texts()
# ============================================================================


class TestEmbedTexts:
    """Test text embedding generation."""

    def test_embed_texts_single(self, engine, sample_texts):
        """Test embedding a single text."""
        result = engine.embed_texts([sample_texts[0]])

        assert "embeddings" in result
        assert "cls_tokens" in result
        assert "seq_lengths" in result
        assert "input_type" in result
        assert "batch_processing_time_ms" in result

        assert len(result["embeddings"]) == 1
        assert result["cls_tokens"].shape == (1, 768)
        assert result["input_type"] == "text"

    def test_embed_texts_batch(self, engine, sample_texts):
        """Test embedding multiple texts."""
        result = engine.embed_texts(sample_texts)

        assert len(result["embeddings"]) == 3
        assert result["cls_tokens"].shape == (3, 768)
        assert len(result["seq_lengths"]) == 3

        # Check each embedding has correct shape
        for emb in result["embeddings"]:
            assert emb.ndim == 2
            assert emb.shape[1] == 768
            assert 50 <= emb.shape[0] <= 80  # Realistic text seq_length

    def test_embed_texts_custom_batch_size(self, engine, sample_texts):
        """Test embedding with custom batch size."""
        texts = sample_texts * 4  # 12 texts

        result = engine.embed_texts(texts, batch_size=3)

        assert len(result["embeddings"]) == 12
        assert result["cls_tokens"].shape == (12, 768)

    def test_embed_texts_empty_list(self, engine):
        """Test that empty text list raises ValueError."""
        with pytest.raises(ValueError, match="Texts list cannot be empty"):
            engine.embed_texts([])

    def test_embed_texts_empty_string(self, engine):
        """Test that empty strings raise ValueError."""
        with pytest.raises(ValueError, match="Text chunks cannot be empty strings"):
            engine.embed_texts(["valid text", "", "another text"])

    def test_embed_texts_whitespace_only(self, engine):
        """Test that whitespace-only strings raise ValueError."""
        with pytest.raises(ValueError, match="Text chunks cannot be empty strings"):
            engine.embed_texts(["valid text", "   ", "another text"])

    def test_embed_texts_uses_config_batch_size(self, engine, sample_texts):
        """Test that None batch_size uses config default."""
        result = engine.embed_texts(sample_texts, batch_size=None)

        assert len(result["embeddings"]) == 3
        # Should use config.batch_size_text (default 8)

    def test_embed_texts_cls_tokens_extracted(self, engine, sample_texts):
        """Test that CLS tokens are properly extracted."""
        result = engine.embed_texts(sample_texts)

        # CLS tokens should be first token of each embedding
        for i, emb in enumerate(result["embeddings"]):
            assert np.allclose(result["cls_tokens"][i], emb[0])

    def test_embed_texts_error_handling(self, engine):
        """Test error handling when embedding generation fails."""
        engine.model.embed_batch = Mock(side_effect=RuntimeError("Processing failed"))

        with pytest.raises(EmbeddingGenerationError, match="Failed to embed texts"):
            engine.embed_texts(["sample text"])


# ============================================================================
# Tests for embed_query()
# ============================================================================


class TestEmbedQuery:
    """Test query embedding generation."""

    def test_embed_query_basic(self, engine):
        """Test basic query embedding."""
        result = engine.embed_query("What is machine learning?")

        assert "embeddings" in result
        assert "cls_token" in result
        assert "seq_length" in result
        assert "input_type" in result
        assert "processing_time_ms" in result

        assert result["embeddings"].ndim == 2
        assert result["embeddings"].shape[1] == 768
        assert result["cls_token"].shape == (768,)
        assert result["input_type"] == "text"

    def test_embed_query_extracts_cls_token(self, engine):
        """Test that CLS token is extracted from embeddings."""
        result = engine.embed_query("test query")

        # CLS token should be first token
        assert np.allclose(result["cls_token"], result["embeddings"][0])

    def test_embed_query_empty_string(self, engine):
        """Test that empty query raises ValueError."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            engine.embed_query("")

    def test_embed_query_whitespace_only(self, engine):
        """Test that whitespace-only query raises ValueError."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            engine.embed_query("   \n\t  ")

    def test_embed_query_long_query(self, engine):
        """Test embedding a long query."""
        long_query = "What is the relationship between " * 20

        result = engine.embed_query(long_query)

        assert result["embeddings"].ndim == 2
        assert result["seq_length"] > 0

    def test_embed_query_timing_recorded(self, engine):
        """Test that processing time is recorded."""
        result = engine.embed_query("test query")

        assert result["processing_time_ms"] > 0
        assert isinstance(result["processing_time_ms"], float)

    def test_embed_query_error_handling(self, engine):
        """Test error handling when query embedding fails."""
        engine.model.embed_batch = Mock(side_effect=RuntimeError("Failed"))

        with pytest.raises(EmbeddingGenerationError, match="Failed to embed query"):
            engine.embed_query("test query")


# ============================================================================
# Tests for score_multi_vector()
# ============================================================================


class TestScoreMultiVector:
    """Test multi-vector scoring with MaxSim."""

    def test_score_multi_vector_basic(self, engine):
        """Test basic multi-vector scoring."""
        # Create mock embeddings
        query_emb = np.random.randn(10, 768).astype(np.float32)
        doc_embs = [
            np.random.randn(50, 768).astype(np.float32),
            np.random.randn(60, 768).astype(np.float32),
            np.random.randn(55, 768).astype(np.float32),
        ]

        with patch("tkr_docusearch.embeddings.colpali_wrapper.batch_maxsim_scores") as mock_scores:
            mock_scores.return_value = [0.85, 0.72, 0.91]

            result = engine.score_multi_vector(query_emb, doc_embs)

            assert "scores" in result
            assert "scoring_time_ms" in result
            assert "num_candidates" in result

            assert len(result["scores"]) == 3
            assert result["num_candidates"] == 3
            assert result["scoring_time_ms"] > 0

    def test_score_multi_vector_validates_query(self, engine):
        """Test that invalid query embeddings are rejected."""
        # Invalid shape (1D instead of 2D)
        invalid_query = np.random.randn(768).astype(np.float32)
        doc_embs = [np.random.randn(50, 768).astype(np.float32)]

        with pytest.raises(ValueError):
            engine.score_multi_vector(invalid_query, doc_embs)

    def test_score_multi_vector_validates_documents(self, engine):
        """Test that invalid document embeddings are rejected."""
        query_emb = np.random.randn(10, 768).astype(np.float32)

        # Invalid document shape
        invalid_doc = np.random.randn(768).astype(np.float32)

        with pytest.raises(ValueError):
            engine.score_multi_vector(query_emb, [invalid_doc])

    def test_score_multi_vector_gpu_flag(self, engine):
        """Test that GPU flag is passed through."""
        query_emb = np.random.randn(10, 768).astype(np.float32)
        doc_embs = [np.random.randn(50, 768).astype(np.float32)]

        with patch("tkr_docusearch.embeddings.colpali_wrapper.batch_maxsim_scores") as mock_scores:
            mock_scores.return_value = [0.85]

            engine.score_multi_vector(query_emb, doc_embs, use_gpu=False)

            mock_scores.assert_called_once()
            assert mock_scores.call_args[1]["use_gpu"] is False

    def test_score_multi_vector_single_document(self, engine):
        """Test scoring with a single document."""
        query_emb = np.random.randn(10, 768).astype(np.float32)
        doc_embs = [np.random.randn(50, 768).astype(np.float32)]

        with patch("tkr_docusearch.embeddings.colpali_wrapper.batch_maxsim_scores") as mock_scores:
            mock_scores.return_value = [0.85]

            result = engine.score_multi_vector(query_emb, doc_embs)

            assert len(result["scores"]) == 1
            assert result["num_candidates"] == 1
            assert result["scores"][0] == 0.85

    def test_score_multi_vector_error_handling(self, engine):
        """Test error handling when scoring fails."""
        query_emb = np.random.randn(10, 768).astype(np.float32)
        doc_embs = [np.random.randn(50, 768).astype(np.float32)]

        with patch("tkr_docusearch.embeddings.colpali_wrapper.batch_maxsim_scores") as mock_scores:
            mock_scores.side_effect = RuntimeError("Scoring failed")

            with pytest.raises(ScoringError, match="Failed to score documents"):
                engine.score_multi_vector(query_emb, doc_embs)


# ============================================================================
# Tests for get_model_info()
# ============================================================================


class TestGetModelInfo:
    """Test model information retrieval."""

    def test_get_model_info_structure(self, engine):
        """Test that model info has correct structure."""
        info = engine.get_model_info()

        assert "model_name" in info
        assert "device" in info
        assert "dtype" in info
        assert "quantization" in info
        assert "memory_allocated_mb" in info
        assert "is_loaded" in info
        assert "cache_dir" in info
        assert "batch_size_visual" in info
        assert "batch_size_text" in info

    def test_get_model_info_values(self, engine):
        """Test that model info contains correct values."""
        info = engine.get_model_info()

        assert info["model_name"] == "vidore/colqwen2-v0.1"
        assert info["device"] in ["mps", "cuda", "cpu"]
        assert info["dtype"] == "fp16"
        assert info["memory_allocated_mb"] == 8000.0
        assert info["is_loaded"] is True

    def test_get_model_info_quantization_none(self, mock_model_loader, mock_memory_estimate):
        """Test quantization field when not quantized."""
        engine = ColPaliEngine(precision="fp16")
        info = engine.get_model_info()

        assert info["quantization"] is None

    def test_get_model_info_quantization_int8(self, mock_model_loader, mock_memory_estimate):
        """Test quantization field when quantized."""
        engine = ColPaliEngine(precision="int8")
        info = engine.get_model_info()

        assert info["quantization"] == "int8"

    def test_get_model_info_batch_sizes(self, mock_model_loader, mock_memory_estimate):
        """Test that batch sizes are correctly reported."""
        config = ModelConfig(batch_size_visual=2, batch_size_text=4)
        engine = ColPaliEngine(config=config)

        info = engine.get_model_info()

        assert info["batch_size_visual"] == 2
        assert info["batch_size_text"] == 4


# ============================================================================
# Tests for clear_cache()
# ============================================================================


class TestClearCache:
    """Test GPU cache clearing."""

    def test_clear_cache_mps(self, engine):
        """Test clearing MPS cache."""
        # Mock torch at the point it's imported inside clear_cache
        mock_torch = MagicMock()
        mock_torch.backends.mps.is_available.return_value = True
        mock_mps_cache = Mock()
        mock_torch.mps.empty_cache = mock_mps_cache

        with patch.dict("sys.modules", {"torch": mock_torch}):
            engine.config.device = "mps"
            engine.clear_cache()

            mock_mps_cache.assert_called_once()

    def test_clear_cache_cuda(self, engine):
        """Test clearing CUDA cache."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        mock_cuda_cache = Mock()
        mock_torch.cuda.empty_cache = mock_cuda_cache

        with patch.dict("sys.modules", {"torch": mock_torch}):
            engine.config.device = "cuda"
            engine.clear_cache()

            mock_cuda_cache.assert_called_once()

    def test_clear_cache_cpu(self, engine):
        """Test that CPU has no cache to clear."""
        mock_torch = MagicMock()

        with patch.dict("sys.modules", {"torch": mock_torch}):
            engine.config.device = "cpu"
            # Should not raise error, just log
            engine.clear_cache()

    def test_clear_cache_no_torch(self, engine):
        """Test cache clearing when PyTorch not available."""
        # Remove torch from sys.modules temporarily
        import sys

        torch_backup = sys.modules.get("torch")
        try:
            if "torch" in sys.modules:
                del sys.modules["torch"]

            # Monkey patch the import to raise ImportError
            import builtins

            original_import = builtins.__import__

            def mock_import(name, *args, **kwargs):
                if name == "torch":
                    raise ImportError("torch not available")
                return original_import(name, *args, **kwargs)

            with patch.object(builtins, "__import__", side_effect=mock_import):
                # Should not raise error
                engine.clear_cache()
        finally:
            if torch_backup is not None:
                sys.modules["torch"] = torch_backup

    def test_clear_cache_error_handling(self, engine):
        """Test error handling when cache clearing fails."""
        mock_torch = MagicMock()
        mock_torch.backends.mps.is_available.return_value = True
        mock_torch.mps.empty_cache.side_effect = RuntimeError("Cache error")

        with patch.dict("sys.modules", {"torch": mock_torch}):
            engine.config.device = "mps"

            # Should not raise, just log warning
            engine.clear_cache()


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for end-to-end workflows."""

    def test_embed_and_score_workflow(self, engine, sample_images):
        """Test complete workflow: embed query and images, then score."""
        # Embed images
        image_result = engine.embed_images(sample_images)

        # Embed query
        query_result = engine.embed_query("Find the blue image")

        # Score
        with patch("tkr_docusearch.embeddings.colpali_wrapper.batch_maxsim_scores") as mock_scores:
            mock_scores.return_value = [0.6, 0.7, 0.9]

            score_result = engine.score_multi_vector(
                query_result["embeddings"], image_result["embeddings"]
            )

            assert len(score_result["scores"]) == 3
            # Blue image should score highest (index 2)
            assert score_result["scores"][2] == 0.9

    def test_batch_processing_workflow(self, engine, sample_images, sample_texts):
        """Test processing multiple batches of images and texts."""
        # Process images in batches
        image_result = engine.embed_images(sample_images, batch_size=1)

        # Process texts in batches
        text_result = engine.embed_texts(sample_texts, batch_size=2)

        # Verify results
        assert len(image_result["embeddings"]) == 3
        assert len(text_result["embeddings"]) == 3

    def test_mixed_precision_workflow(self, mock_model_loader, mock_memory_estimate):
        """Test workflow with different precision settings."""
        # FP16 engine
        engine_fp16 = ColPaliEngine(precision="fp16")
        assert engine_fp16.config.precision == "fp16"

        # INT8 engine
        engine_int8 = ColPaliEngine(precision="int8")
        assert engine_int8.config.precision == "int8"

    def test_device_fallback_workflow(self):
        """Test device fallback mechanism."""
        # Mock torch at sys.modules level
        mock_torch = MagicMock()
        mock_torch.backends.mps.is_available.return_value = False
        mock_torch.cuda.is_available.return_value = False

        with patch.dict("sys.modules", {"torch": mock_torch}):
            with patch("tkr_docusearch.embeddings.colpali_wrapper.load_model") as mock_loader:
                mock_loader.return_value = (MagicMock(), MagicMock())

                with patch("tkr_docusearch.embeddings.colpali_wrapper.estimate_memory_usage") as mock_mem:
                    mock_mem.return_value = 8000.0

                    engine = ColPaliEngine(device="mps")

                    # Should have fallen back to CPU
                    assert engine.config.device == "cpu"


# ============================================================================
# Edge Cases and Error Conditions
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_single_token_embedding(self, engine):
        """Test handling of very short inputs resulting in single token."""
        with patch.object(engine.model, "embed_batch") as mock_embed:
            # Return single token embedding
            mock_embed.return_value = ([np.random.randn(1, 768).astype(np.float32)], [1])

            result = engine.embed_texts(["a"])

            assert result["embeddings"][0].shape[0] == 1
            assert result["seq_lengths"][0] == 1

    def test_very_long_sequence(self, engine):
        """Test handling of very long sequences."""
        long_text = "word " * 1000

        with patch.object(engine.model, "embed_batch") as mock_embed:
            # Return long sequence embedding
            mock_embed.return_value = ([np.random.randn(512, 768).astype(np.float32)], [512])

            result = engine.embed_texts([long_text])

            assert result["embeddings"][0].shape[0] == 512

    def test_batch_size_larger_than_data(self, engine, sample_images):
        """Test batch size larger than number of inputs."""
        # Only 3 images, batch size 10
        result = engine.embed_images(sample_images, batch_size=10)

        assert len(result["embeddings"]) == 3

    def test_batch_size_one(self, engine, sample_images):
        """Test batch size of 1 (no batching)."""
        result = engine.embed_images(sample_images, batch_size=1)

        assert len(result["embeddings"]) == 3
        # Should process each image individually

    def test_non_normalized_embeddings(self, engine):
        """Test handling of non-normalized embeddings in scoring."""
        # Create non-normalized embeddings
        query_emb = np.random.randn(10, 768).astype(np.float32) * 10
        doc_embs = [np.random.randn(50, 768).astype(np.float32) * 10]

        with patch("tkr_docusearch.embeddings.colpali_wrapper.batch_maxsim_scores") as mock_scores:
            mock_scores.return_value = [0.85]

            result = engine.score_multi_vector(query_emb, doc_embs)

            # Should still work (scoring function handles normalization)
            assert len(result["scores"]) == 1

    def test_zero_dimension_embedding(self, engine):
        """Test rejection of zero-dimension embeddings."""
        query_emb = np.random.randn(10, 768).astype(np.float32)
        invalid_doc = np.random.randn(0, 768).astype(np.float32)

        with pytest.raises(ValueError):
            engine.score_multi_vector(query_emb, [invalid_doc])

    def test_dimension_mismatch(self, engine):
        """Test rejection of dimension mismatch between query and doc."""
        query_emb = np.random.randn(10, 768).astype(np.float32)
        invalid_doc = np.random.randn(50, 512).astype(np.float32)  # Wrong dimension

        with pytest.raises(ValueError):
            engine.score_multi_vector(query_emb, [invalid_doc])
