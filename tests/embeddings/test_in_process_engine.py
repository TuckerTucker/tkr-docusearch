"""Tests for InProcessEmbeddingEngine adapter."""

import struct

import numpy as np
import pytest

from src.embeddings.in_process_engine import InProcessEmbeddingEngine


class MockColNomicEngine:
    """Mock ColNomicEngine that returns deterministic embeddings."""

    async def encode_documents(self, texts):
        from shikomi_ingest.types import MultiVectorEmbedding

        return [
            MultiVectorEmbedding(
                num_tokens=10,
                dim=128,
                data=np.random.randn(10, 128).astype(np.float32),
            )
            for _ in texts
        ]

    async def encode_queries(self, texts):
        return await self.encode_documents(texts)

    async def encode_images(self, images):
        from shikomi_ingest.types import MultiVectorEmbedding

        return [
            MultiVectorEmbedding(
                num_tokens=20,
                dim=128,
                data=np.random.randn(20, 128).astype(np.float32),
            )
            for _ in images
        ]


@pytest.fixture
def engine():
    """Create an InProcessEmbeddingEngine with mock ColNomicEngine."""
    eng = InProcessEmbeddingEngine(engine=MockColNomicEngine())
    eng.connect()
    yield eng
    eng.close()


@pytest.fixture
def disconnected_engine():
    """Create an InProcessEmbeddingEngine without connecting."""
    return InProcessEmbeddingEngine(engine=MockColNomicEngine())


class TestEmbedTexts:
    """Tests for embed_texts returning packed binary blobs."""

    def test_returns_list_of_bytes(self, engine):
        """embed_texts returns a list of bytes blobs."""
        blobs = engine.embed_texts(["hello world", "another sentence"])
        assert isinstance(blobs, list)
        assert len(blobs) == 2
        for blob in blobs:
            assert isinstance(blob, bytes)

    def test_blob_header_format(self, engine):
        """Each blob starts with u32 num_tokens and u32 dim in LE."""
        blobs = engine.embed_texts(["test text"])
        blob = blobs[0]

        num_tokens, dim = struct.unpack("<II", blob[:8])
        assert num_tokens == 10
        assert dim == 128

        expected_size = 8 + num_tokens * dim * 4  # header + f32 data
        assert len(blob) == expected_size

    def test_empty_input_returns_empty(self, engine):
        """Empty list returns empty list without error."""
        assert engine.embed_texts([]) == []


class TestEmbedImages:
    """Tests for embed_images returning packed binary blobs."""

    def test_returns_list_of_bytes(self, engine):
        """embed_images returns a list of bytes blobs."""
        from PIL import Image

        images = [Image.new("RGB", (100, 100)) for _ in range(3)]
        blobs = engine.embed_images(images)

        assert isinstance(blobs, list)
        assert len(blobs) == 3
        for blob in blobs:
            assert isinstance(blob, bytes)

    def test_blob_header_format(self, engine):
        """Image blobs have correct header with 20 tokens, 128 dim."""
        from PIL import Image

        images = [Image.new("RGB", (100, 100))]
        blobs = engine.embed_images(images)
        blob = blobs[0]

        num_tokens, dim = struct.unpack("<II", blob[:8])
        assert num_tokens == 20
        assert dim == 128

        expected_size = 8 + num_tokens * dim * 4
        assert len(blob) == expected_size

    def test_empty_input_returns_empty(self, engine):
        """Empty list returns empty list without error."""
        assert engine.embed_images([]) == []


class TestEmbedQuery:
    """Tests for embed_query returning nested float lists."""

    def test_returns_nested_lists(self, engine):
        """embed_query returns list[list[float]]."""
        result = engine.embed_query("test query")
        assert isinstance(result, list)
        assert len(result) > 0
        for vec in result:
            assert isinstance(vec, list)
            for val in vec:
                assert isinstance(val, float)

    def test_dimensions(self, engine):
        """Result has expected token count and vector dimension."""
        result = engine.embed_query("test query")
        assert len(result) == 10  # MockColNomicEngine returns 10 tokens
        assert len(result[0]) == 128  # dim=128

    def test_empty_query_raises(self, engine):
        """Empty string raises ValueError."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            engine.embed_query("")

    def test_whitespace_only_raises(self, engine):
        """Whitespace-only string raises ValueError."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            engine.embed_query("   ")


class TestLifecycle:
    """Tests for connect/close lifecycle."""

    def test_connect_idempotent(self):
        """Double connect does not error."""
        eng = InProcessEmbeddingEngine(engine=MockColNomicEngine())
        eng.connect()
        eng.connect()  # Second call is a no-op
        # Verify engine still works
        result = eng.embed_query("test")
        assert isinstance(result, list)
        eng.close()

    def test_methods_raise_before_connect(self, disconnected_engine):
        """Calling embed methods before connect raises RuntimeError."""
        with pytest.raises(RuntimeError, match="not connected"):
            disconnected_engine.embed_texts(["hello"])

        with pytest.raises(RuntimeError, match="not connected"):
            disconnected_engine.embed_query("hello")

        from PIL import Image

        with pytest.raises(RuntimeError, match="not connected"):
            disconnected_engine.embed_images([Image.new("RGB", (10, 10))])

    def test_close_allows_reconnect(self):
        """After close, connect re-initializes the engine."""
        eng = InProcessEmbeddingEngine(engine=MockColNomicEngine())
        eng.connect()
        eng.close()

        # Re-inject a fresh engine since close sets _engine to None
        eng._engine = MockColNomicEngine()
        eng.connect()
        result = eng.embed_query("test")
        assert isinstance(result, list)
        eng.close()

    def test_health_check(self):
        """Health check reports correct status."""
        eng = InProcessEmbeddingEngine(
            device="cpu",
            quantization="fp16",
            engine=MockColNomicEngine(),
        )
        health = eng.health_check()
        assert health["connected"] is True
        assert health["device"] == "cpu"
        assert health["mode"] == "in_process"

        eng.close()
        health = eng.health_check()
        assert health["connected"] is False
