"""
Type definitions for embedding operations.

This module defines TypedDicts and type aliases for embedding inputs and outputs.
"""

from typing import List, TypedDict
import numpy as np


class EmbeddingOutput(TypedDict):
    """Multi-vector embedding output."""
    embeddings: np.ndarray           # Shape: (seq_length, 768)
    cls_token: np.ndarray            # Shape: (768,) - representative vector
    seq_length: int                  # Number of tokens
    input_type: str                  # "visual" or "text"
    processing_time_ms: float        # Embedding generation time


class BatchEmbeddingOutput(TypedDict):
    """Batch embedding output."""
    embeddings: List[np.ndarray]     # List of (seq_length, 768) arrays
    cls_tokens: np.ndarray           # Shape: (batch_size, 768)
    seq_lengths: List[int]           # Token counts for each item
    input_type: str                  # "visual" or "text"
    batch_processing_time_ms: float  # Total batch time


class ScoringOutput(TypedDict):
    """Late interaction scoring output."""
    scores: List[float]              # MaxSim scores (0-1 range)
    scoring_time_ms: float           # Time for re-ranking
    num_candidates: int              # Number of documents scored
