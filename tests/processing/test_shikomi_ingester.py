"""Tests for ShikomiIngester -- sync wrapper around shikomi.Ingester."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.processing.shikomi_ingester import ShikomiIngester, StatusBridge


# ---------------------------------------------------------------------------
# Lifecycle tests
# ---------------------------------------------------------------------------


class TestShikomiIngesterLifecycle:
    """Tests for connect / close lifecycle management."""

    @patch("src.processing.shikomi_ingester.Ingester")
    def test_connect_creates_event_loop(self, mock_ingester_cls: MagicMock) -> None:
        """connect() initializes a private event loop."""
        ingester = ShikomiIngester()
        assert ingester._loop is None

        ingester.connect()

        assert ingester._loop is not None
        ingester.close()

    @patch("src.processing.shikomi_ingester.Ingester")
    def test_connect_is_idempotent(self, mock_ingester_cls: MagicMock) -> None:
        """Calling connect() twice returns the same event loop."""
        ingester = ShikomiIngester()
        ingester.connect()
        first_loop = ingester._loop

        ingester.connect()

        assert ingester._loop is first_loop
        ingester.close()

    @patch("src.processing.shikomi_ingester.Ingester")
    def test_process_requires_connection(self, mock_ingester_cls: MagicMock) -> None:
        """process() raises RuntimeError before connect()."""
        ingester = ShikomiIngester()

        with pytest.raises(RuntimeError, match="not connected"):
            ingester.process("/tmp/test.pdf")

    @patch("src.processing.shikomi_ingester.Ingester")
    def test_close_cleans_up_loop(self, mock_ingester_cls: MagicMock) -> None:
        """close() sets _loop to None."""
        ingester = ShikomiIngester()
        ingester.connect()
        assert ingester._loop is not None

        ingester.close()

        assert ingester._loop is None

    @patch("src.processing.shikomi_ingester.Ingester")
    def test_close_idempotent(self, mock_ingester_cls: MagicMock) -> None:
        """close() can be called multiple times without error."""
        ingester = ShikomiIngester()
        ingester.connect()

        ingester.close()
        ingester.close()  # should not raise

        assert ingester._loop is None


# ---------------------------------------------------------------------------
# Engine property test
# ---------------------------------------------------------------------------


class TestShikomiIngesterEngine:
    """Tests for the engine property."""

    @patch("src.processing.shikomi_ingester.Ingester")
    def test_engine_property(self, mock_ingester_cls: MagicMock) -> None:
        """engine property delegates to the wrapped Ingester's engine."""
        mock_inner = MagicMock()
        mock_inner.engine = MagicMock(name="ColNomicEngine")
        mock_ingester_cls.return_value = mock_inner

        ingester = ShikomiIngester()

        assert ingester.engine is mock_inner.engine


# ---------------------------------------------------------------------------
# Health check test
# ---------------------------------------------------------------------------


class TestShikomiIngesterHealthCheck:
    """Tests for health_check."""

    @patch("src.processing.shikomi_ingester.Ingester")
    def test_health_check_before_connect(self, mock_ingester_cls: MagicMock) -> None:
        """health_check returns connected=False before connect()."""
        ingester = ShikomiIngester(device="cpu", quantization="fp16")
        status = ingester.health_check()

        assert status["connected"] is False
        assert status["device"] == "cpu"
        assert status["quantization"] == "fp16"
        assert status["mode"] == "shikomi_ingester"

    @patch("src.processing.shikomi_ingester.Ingester")
    def test_health_check_after_connect(self, mock_ingester_cls: MagicMock) -> None:
        """health_check returns connected=True after connect()."""
        ingester = ShikomiIngester(device="mps", quantization="4bit")
        ingester.connect()

        status = ingester.health_check()

        assert status["connected"] is True
        assert status["device"] == "mps"
        assert status["quantization"] == "4bit"
        ingester.close()


# ---------------------------------------------------------------------------
# Process delegation test
# ---------------------------------------------------------------------------


class TestShikomiIngesterProcess:
    """Tests for the process method."""

    @patch("src.processing.shikomi_ingester.Ingester")
    def test_process_delegates_to_ingester(
        self, mock_ingester_cls: MagicMock,
    ) -> None:
        """process() runs the inner Ingester.process coroutine on the loop."""
        mock_inner = MagicMock()
        mock_result = MagicMock(chunk_count=5, processing_time_ms=1200.0)

        # Make the inner process() return a coroutine
        async def _fake_process(path: str) -> MagicMock:
            return mock_result

        mock_inner.process = _fake_process
        mock_ingester_cls.return_value = mock_inner

        ingester = ShikomiIngester()
        ingester.connect()

        result = ingester.process("/tmp/doc.pdf")

        assert result is mock_result
        ingester.close()


# ---------------------------------------------------------------------------
# Renderer passthrough test
# ---------------------------------------------------------------------------


class TestShikomiIngesterRenderer:
    """Tests for renderer and visual embedding passthrough."""

    @patch("src.processing.shikomi_ingester.Ingester")
    def test_renderer_passed_to_ingester(
        self, mock_ingester_cls: MagicMock,
    ) -> None:
        """renderer kwarg is forwarded to the inner Ingester."""
        mock_renderer = MagicMock()

        ShikomiIngester(renderer=mock_renderer)

        call_kwargs = mock_ingester_cls.call_args
        assert call_kwargs.kwargs.get("renderer") is mock_renderer

    @patch("src.processing.shikomi_ingester.Ingester")
    def test_enable_visual_passed_to_ingester(
        self, mock_ingester_cls: MagicMock,
    ) -> None:
        """enable_visual_embeddings is forwarded to the inner Ingester."""
        ShikomiIngester(enable_visual_embeddings=False)

        call_kwargs = mock_ingester_cls.call_args
        assert call_kwargs.kwargs.get("enable_visual_embeddings") is False


# ---------------------------------------------------------------------------
# StatusBridge forwarding test
# ---------------------------------------------------------------------------


class TestStatusBridgeForwarding:
    """Tests for StatusBridge stage forwarding."""

    def test_forwarded_stages_include_embedding_visual(self) -> None:
        """StatusBridge forwards embedding_visual stage to DocuSearch."""
        assert "embedding_visual" in StatusBridge._FORWARDED

    def test_forwarded_stages(self) -> None:
        """StatusBridge forwards the expected set of stages."""
        assert StatusBridge._FORWARDED == frozenset({
            "parsing", "chunking", "embedding_text", "embedding_visual",
        })
