"""Embedding engine factory.

Reads ``ShikomiConfig.mode`` and returns the appropriate engine instance.
Centralizes the gRPC vs in-process decision so startup sites don't
duplicate the logic.
"""

from __future__ import annotations

import structlog
import torch

from ..config.koji_config import ShikomiConfig

logger = structlog.get_logger(__name__)


def _resolve_device(device: str) -> str:
    """Resolve ``"auto"`` to an actual PyTorch device string.

    Args:
        device: Device string from config (``auto``, ``mps``, ``cuda``, ``cpu``).

    Returns:
        A valid PyTorch device string.
    """
    if device != "auto":
        return device

    if torch.backends.mps.is_available():
        resolved = "mps"
    elif torch.cuda.is_available():
        resolved = "cuda"
    else:
        resolved = "cpu"

    logger.info("embedding_factory.device_resolved", requested=device, resolved=resolved)
    return resolved


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

        resolved_device = _resolve_device(config.device)
        engine = InProcessEmbeddingEngine(
            device=resolved_device,
            quantization=config.quantization,
        )
        engine.connect()
        logger.info(
            "embedding_factory.created",
            mode="in_process",
            device=resolved_device,
            quantization=config.quantization,
        )
        return engine

    raise ValueError(
        f"Unknown SHIKOMI_MODE '{config.mode}'. "
        "Must be 'grpc' or 'in_process'."
    )
