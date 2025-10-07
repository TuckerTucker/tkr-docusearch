"""
Embeddings module for DocuSearch MVP.

This module provides ColPali multi-vector embeddings and late interaction scoring.

Main components:
- ColPaliEngine: Main API for embedding generation and scoring
- EmbeddingOutput, BatchEmbeddingOutput, ScoringOutput: Type definitions
- Exceptions: Error types for embedding operations

Example usage:
    >>> from embeddings import ColPaliEngine
    >>> from PIL import Image
    >>>
    >>> # Initialize engine
    >>> engine = ColPaliEngine(device="mps", precision="int8")
    >>>
    >>> # Embed images
    >>> images = [Image.open("page1.png"), Image.open("page2.png")]
    >>> result = engine.embed_images(images)
    >>>
    >>> # Embed query
    >>> query_result = engine.embed_query("quarterly revenue growth")
    >>>
    >>> # Score documents
    >>> scores = engine.score_multi_vector(
    ...     query_result['embeddings'],
    ...     result['embeddings']
    ... )
"""

from .colpali_wrapper import ColPaliEngine
from .types import EmbeddingOutput, BatchEmbeddingOutput, ScoringOutput
from .exceptions import (
    EmbeddingError,
    ModelLoadError,
    DeviceError,
    EmbeddingGenerationError,
    ScoringError,
    QuantizationError
)
from .scoring import maxsim_score, batch_maxsim_scores, validate_embedding_shape
from .model_loader import load_model

__all__ = [
    # Main API
    'ColPaliEngine',

    # Type definitions
    'EmbeddingOutput',
    'BatchEmbeddingOutput',
    'ScoringOutput',

    # Exceptions
    'EmbeddingError',
    'ModelLoadError',
    'DeviceError',
    'EmbeddingGenerationError',
    'ScoringError',
    'QuantizationError',

    # Utilities
    'maxsim_score',
    'batch_maxsim_scores',
    'validate_embedding_shape',
    'load_model',
]

__version__ = '1.0.0'
__author__ = 'DocuSearch Team'
