"""
Exceptions for embedding operations.

This module defines exception hierarchy for embedding-related errors.
"""


class EmbeddingError(Exception):
    """Base exception for embedding operations."""


class ModelLoadError(EmbeddingError):
    """Failed to load ColPali model."""


class DeviceError(EmbeddingError):
    """Requested device not available."""


class EmbeddingGenerationError(EmbeddingError):
    """Embedding computation failed."""


class ScoringError(EmbeddingError):
    """Late interaction scoring failed."""


class QuantizationError(EmbeddingError):
    """Model quantization failed."""
