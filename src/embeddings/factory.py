"""Embedding engine factory.

Reads ``ShikomiConfig.mode`` and returns the appropriate engine instance.
Centralizes the gRPC vs in-process decision so startup sites don't
duplicate the logic.
"""

from __future__ import annotations

import structlog

from ..config.koji_config import ShikomiConfig

logger = structlog.get_logger(__name__)


def create_embedding_engine(config: ShikomiConfig):
    """Create and connect an embedding engine based on ``config.mode``.

    Args:
        config: Shikomi configuration with ``mode`` field.

    Returns:
        Connected embedding engine (``ShikomiClient`` or
        ``InProcessEmbeddingEngine``).

    Raises:
        ValueError: If ``config.mode`` is not recognized.
    """
    if config.mode == "grpc":
        from .shikomi_client import ShikomiClient

        engine = ShikomiClient(config=config)
        engine.connect()
        logger.info(
            "embedding_factory.created",
            mode="grpc",
            target=config.grpc_target,
        )
        return engine

    if config.mode == "in_process":
        from .in_process_engine import InProcessEmbeddingEngine

        engine = InProcessEmbeddingEngine(
            device=config.device,
            quantization=config.quantization,
        )
        engine.connect()
        logger.info(
            "embedding_factory.created",
            mode="in_process",
            device=config.device,
            quantization=config.quantization,
        )
        return engine

    raise ValueError(
        f"Unknown SHIKOMI_MODE '{config.mode}'. "
        "Must be 'grpc' or 'in_process'."
    )
