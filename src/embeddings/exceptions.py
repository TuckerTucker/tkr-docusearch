"""
Exceptions for embedding operations.

This module defines exception hierarchy for embedding-related errors.
"""


class EmbeddingError(Exception):
    """Base exception for embedding operations."""
    pass


class ModelLoadError(EmbeddingError):
    """Failed to load ColPali model."""
    pass


class DeviceError(EmbeddingError):
    """Requested device not available."""
    pass


class EmbeddingGenerationError(EmbeddingError):
    """Embedding computation failed."""
    pass


class ScoringError(EmbeddingError):
    """Late interaction scoring failed."""
    pass


class QuantizationError(EmbeddingError):
    """Model quantization failed."""
    pass
