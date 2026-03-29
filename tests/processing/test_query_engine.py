"""Tests for QueryEngine -- search embedding via ColNomicEngine."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from shikomi.types import MultiVectorEmbedding

from src.embeddings.query_engine import QueryEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_engine() -> MagicMock:
    """Create a mock ColNomicEngine that returns a MultiVectorEmbedding."""
    engine = MagicMock()
    data = np.random.randn(32, 128).astype(np.float32)
    emb = MultiVectorEmbedding(num_tokens=32, dim=128, data=data)
    engine.encode_queries = AsyncMock(return_value=[emb])
    return engine


# ---------------------------------------------------------------------------
# embed_query tests
# ---------------------------------------------------------------------------


class TestEmbedQuery:
    """Tests for QueryEngine.embed_query."""

    def test_returns_nested_lists(self) -> None:
        """embed_query returns list[list[float]]."""
        engine = _make_mock_engine()
        qe = QueryEngine(engine=engine)
        qe.connect()

        result = qe.embed_query("what is the quarterly revenue?")

        assert isinstance(result, list)
        assert len(result) == 32
        assert isinstance(result[0], list)
        assert isinstance(result[0][0], float)

        qe.close()

    def test_empty_query_raises(self) -> None:
        """embed_query raises ValueError for empty string."""
        engine = _make_mock_engine()
        qe = QueryEngine(engine=engine)
        qe.connect()

        with pytest.raises(ValueError, match="Query cannot be empty"):
            qe.embed_query("")

        qe.close()

    def test_whitespace_only_raises(self) -> None:
        """embed_query raises ValueError for whitespace-only string."""
        engine = _make_mock_engine()
        qe = QueryEngine(engine=engine)
        qe.connect()

        with pytest.raises(ValueError, match="Query cannot be empty"):
            qe.embed_query("   \t\n  ")

        qe.close()


# ---------------------------------------------------------------------------
# Lifecycle tests
# ---------------------------------------------------------------------------


class TestQueryEngineLifecycle:
    """Tests for connect / close lifecycle."""

    def test_connect_required(self) -> None:
        """embed_query raises RuntimeError before connect()."""
        engine = _make_mock_engine()
        qe = QueryEngine(engine=engine)

        with pytest.raises(RuntimeError, match="not connected"):
            qe.embed_query("test query")

    def test_injected_engine_not_released_on_close(self) -> None:
        """When engine is injected, close() preserves the engine reference."""
        engine = _make_mock_engine()
        qe = QueryEngine(engine=engine)
        qe.connect()

        qe.close()

        # Engine still set because it was injected (caller owns it)
        assert qe._engine is engine

    @patch("src.embeddings.query_engine.ColNomicEngine", create=True)
    def test_self_created_engine_released_on_close(
        self, mock_engine_cls: MagicMock,
    ) -> None:
        """When no engine is injected, close() sets engine to None."""
        mock_instance = _make_mock_engine()
        mock_engine_cls.return_value = mock_instance

        # Patch the import inside connect()
        with patch.dict(
            "sys.modules",
            {"shikomi.embedding": MagicMock(ColNomicEngine=mock_engine_cls)},
        ):
            qe = QueryEngine(device="cpu", quantization="fp16")
            qe.connect()

            assert qe._engine is not None

            qe.close()

            assert qe._engine is None

    def test_connect_idempotent(self) -> None:
        """Calling connect() twice reuses the same loop."""
        engine = _make_mock_engine()
        qe = QueryEngine(engine=engine)
        qe.connect()
        first_loop = qe._loop

        qe.connect()

        assert qe._loop is first_loop
        qe.close()


# ---------------------------------------------------------------------------
# Health check tests
# ---------------------------------------------------------------------------


class TestQueryEngineHealthCheck:
    """Tests for health_check."""

    def test_health_check_before_connect(self) -> None:
        """health_check reports not connected before connect()."""
        qe = QueryEngine(engine=_make_mock_engine())
        status = qe.health_check()

        assert status["connected"] is False
        assert status["mode"] == "query_engine"

    def test_health_check_after_connect(self) -> None:
        """health_check reports connected after connect()."""
        qe = QueryEngine(engine=_make_mock_engine())
        qe.connect()

        status = qe.health_check()

        assert status["connected"] is True
        assert status["device"] == "mps"
        assert status["quantization"] == "4bit"
        qe.close()
