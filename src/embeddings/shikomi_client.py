"""Shikomi embedding client for DocuSearch.

This module provides the interface between DocuSearch and Shikomi's
distributed embedding workers via gRPC. It replaces the ColPali wrapper
with ColNomic multi-vector embeddings.

Key design decisions:
- ``embed_images``/``embed_texts`` return ``list[bytes]`` (packed blobs for
  Koji binary column storage).
- ``embed_query`` returns ``list[list[float]]`` (Koji auto-detects this
  as a multi-vector parameter for the ``<~>`` operator).
"""

from __future__ import annotations

import io
import struct
from typing import Any

import grpc
import structlog
from PIL import Image

from ..config.koji_config import ShikomiConfig
from .proto import embedding_pb2, embedding_pb2_grpc

logger = structlog.get_logger(__name__)


def _multivec_to_blob(emb: embedding_pb2.MultiVectorEmbedding) -> bytes:
    """Convert a gRPC MultiVectorEmbedding to packed binary blob.

    Format: 8-byte header (num_tokens u32 LE + dim u32 LE) followed by
    packed f32 row-major LE data.

    Args:
        emb: gRPC MultiVectorEmbedding message.

    Returns:
        Packed binary blob.
    """
    header = struct.pack("<II", emb.num_tokens, emb.dim)
    return header + emb.data


def _multivec_to_list(emb: embedding_pb2.MultiVectorEmbedding) -> list[list[float]]:
    """Convert a gRPC MultiVectorEmbedding to nested list of floats.

    Args:
        emb: gRPC MultiVectorEmbedding message.

    Returns:
        List of token vectors, each a list of floats.
    """
    n_floats = emb.num_tokens * emb.dim
    floats = struct.unpack(f"<{n_floats}f", emb.data)
    return [
        list(floats[i * emb.dim : (i + 1) * emb.dim])
        for i in range(emb.num_tokens)
    ]


class ShikomiClient:
    """Client for Shikomi embedding workers via gRPC.

    Manages the gRPC channel lifecycle and provides typed embedding
    methods for images, text chunks, and search queries.

    Args:
        config: Shikomi embedding configuration.
    """

    def __init__(self, config: ShikomiConfig) -> None:
        self._config = config
        self._channel: grpc.Channel | None = None
        self._stub: embedding_pb2_grpc.EmbeddingServiceStub | None = None

    # -- lifecycle -----------------------------------------------------------

    def connect(self) -> None:
        """Create the gRPC channel and stub.

        Idempotent — calling connect() on an already-connected client is a no-op.
        """
        if self._channel is not None:
            return

        target = self._config.grpc_target
        self._channel = grpc.insecure_channel(target)
        self._stub = embedding_pb2_grpc.EmbeddingServiceStub(self._channel)

        logger.info(
            "shikomi_client.connected",
            target=target,
            model=self._config.model,
        )

    def close(self) -> None:
        """Close the gRPC channel.

        Safe to call even if not connected.
        """
        if self._channel is None:
            return

        try:
            self._channel.close()
            logger.info("shikomi_client.closed")
        except Exception as exc:
            logger.warning("shikomi_client.close_error", error=str(exc))
        finally:
            self._channel = None
            self._stub = None

    def health_check(self) -> dict[str, Any]:
        """Return embedding service health status.

        Returns:
            Dictionary with connection status, device, model info.
        """
        if self._stub is None:
            return {
                "connected": False,
                "model": self._config.model,
                "device": "unknown",
                "model_loaded": False,
            }

        try:
            resp = self._stub.HealthCheck(embedding_pb2.HealthRequest())
            return {
                "connected": resp.status == embedding_pb2.WORKER_STATUS_HEALTHY,
                "model": self._config.model,
                "device": resp.device,
                "model_loaded": resp.model_loaded,
                "queue_depth": resp.queue_depth,
                "avg_latency_ms": resp.avg_latency_ms,
            }
        except grpc.RpcError:
            return {
                "connected": False,
                "model": self._config.model,
                "device": "unknown",
                "model_loaded": False,
            }

    def detect_device(self) -> str:
        """Detect the best available compute device.

        Returns:
            Device string: ``mps``, ``cuda``, or ``cpu``.
        """
        try:
            import torch

            if torch.backends.mps.is_available():
                return "mps"
            if torch.cuda.is_available():
                return "cuda"
        except ImportError:
            pass
        return "cpu"

    # -- embedding methods ---------------------------------------------------

    def embed_images(
        self, images: list[Image.Image], batch_size: int = 4
    ) -> list[bytes]:
        """Embed page images via Shikomi workers.

        Accepts PIL Images (matching the existing ColPaliEngine interface).
        Returns packed multi-vector blobs for direct storage in Koji
        binary columns.

        Args:
            images: List of PIL Image objects.
            batch_size: Number of images per batch (unused, batching is
                handled server-side).

        Returns:
            List of packed binary blobs (one per image).
        """
        if not images:
            return []

        self._require_connected()

        image_inputs = [
            embedding_pb2.ImageInput(data=self._pil_to_bytes(img))
            for img in images
        ]
        request = embedding_pb2.ImageEncodeRequest(images=image_inputs)
        response = self._stub.EncodeImages(request)

        logger.debug(
            "shikomi_client.images_embedded",
            count=len(images),
        )

        return [_multivec_to_blob(emb) for emb in response.embeddings]

    def embed_texts(
        self, texts: list[str], batch_size: int = 8
    ) -> list[bytes]:
        """Embed text chunks via Shikomi workers.

        Returns packed multi-vector blobs for direct storage in Koji
        binary columns.

        Args:
            texts: List of text strings to embed.
            batch_size: Number of texts per batch (unused, batching is
                handled server-side).

        Returns:
            List of packed binary blobs (one per text chunk).
        """
        if not texts:
            return []

        self._require_connected()

        request = embedding_pb2.EncodeRequest(texts=texts)
        response = self._stub.EncodeDocuments(request)

        logger.debug(
            "shikomi_client.texts_embedded",
            count=len(texts),
        )

        return [_multivec_to_blob(emb) for emb in response.embeddings]

    def embed_query(self, query: str) -> list[list[float]]:
        """Embed a search query.

        Returns a nested list suitable for direct use as a Koji SQL
        parameter with the ``<~>`` MaxSim operator. Koji auto-detects
        ``list[list[float]]`` as a multi-vector parameter.

        Args:
            query: Search query string.

        Returns:
            Multi-vector embedding as ``list[list[float]]``.
        """
        self._require_connected()

        request = embedding_pb2.EncodeRequest(texts=[query])
        response = self._stub.EncodeQueries(request)
        result = _multivec_to_list(response.embeddings[0])

        logger.debug(
            "shikomi_client.query_embedded",
            query_len=len(query),
            num_tokens=len(result),
        )

        return result

    # -- internal helpers ----------------------------------------------------

    def _require_connected(self) -> None:
        """Raise if the gRPC stub is not initialized."""
        if self._stub is None:
            raise RuntimeError(
                "ShikomiClient is not connected. Call connect() first."
            )

    @staticmethod
    def _pil_to_bytes(image: Image.Image) -> bytes:
        """Convert a PIL Image to PNG bytes for gRPC transport.

        Args:
            image: PIL Image object.

        Returns:
            PNG-encoded image bytes.
        """
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()
