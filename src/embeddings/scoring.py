"""
Late interaction scoring using MaxSim algorithm.

This module implements the MaxSim (Maximum Similarity) scoring algorithm
for multi-vector embeddings as used in ColBERT and ColPali.
"""

import numpy as np
from typing import List
import logging

try:
    from embeddings.exceptions import ScoringError
except ImportError:
    from .exceptions import ScoringError

logger = logging.getLogger(__name__)


def maxsim_score(
    query_embeddings: np.ndarray,
    doc_embeddings: np.ndarray
) -> float:
    """
    Compute MaxSim score between query and document.

    For each query token:
        Find max cosine similarity with any document token
    Sum these max similarities across all query tokens

    Args:
        query_embeddings: Query multi-vector, shape (Q, 768)
        doc_embeddings: Document multi-vector, shape (D, 768)

    Returns:
        Score in range [0, 1] where higher is better

    Raises:
        ScoringError: If computation fails
    """
    try:
        Q, dim_q = query_embeddings.shape
        D, dim_d = doc_embeddings.shape

        if dim_q != dim_d:
            raise ValueError(f"Dimension mismatch: query {dim_q} != doc {dim_d}")

        # ColPali models use 128 dimensions, mock models use 768
        if dim_q not in [128, 768]:
            raise ValueError(f"Expected dimension 128 or 768, got {dim_q}")

        # Normalize embeddings (L2 norm)
        query_norm = query_embeddings / (np.linalg.norm(query_embeddings, axis=1, keepdims=True) + 1e-8)
        doc_norm = doc_embeddings / (np.linalg.norm(doc_embeddings, axis=1, keepdims=True) + 1e-8)

        # Compute similarity matrix (Q x D)
        similarity_matrix = np.matmul(query_norm, doc_norm.T)

        # MaxSim: max over doc tokens for each query token, then sum
        max_similarities = np.max(similarity_matrix, axis=1)  # (Q,)
        score = np.sum(max_similarities)

        # Normalize by query length to get [0, 1] range
        normalized_score = score / Q

        return float(normalized_score)

    except Exception as e:
        logger.error(f"MaxSim scoring failed: {e}")
        raise ScoringError(f"Failed to compute MaxSim score: {e}") from e


def batch_maxsim_scores(
    query_embeddings: np.ndarray,
    document_embeddings: List[np.ndarray],
    use_gpu: bool = True
) -> List[float]:
    """
    Compute MaxSim scores for a query against multiple documents.

    Args:
        query_embeddings: Query multi-vector, shape (query_tokens, 768)
        document_embeddings: List of document multi-vectors, each (doc_tokens, 768)
        use_gpu: Use GPU acceleration if available (currently no-op, uses NumPy)

    Returns:
        List of MaxSim scores, one per document

    Raises:
        ScoringError: If computation fails
    """
    try:
        scores = []
        for doc_emb in document_embeddings:
            score = maxsim_score(query_embeddings, doc_emb)
            scores.append(score)
        return scores

    except Exception as e:
        logger.error(f"Batch MaxSim scoring failed: {e}")
        raise ScoringError(f"Failed to compute batch MaxSim scores: {e}") from e


def validate_embedding_shape(embeddings: np.ndarray, name: str = "embeddings") -> None:
    """
    Validate embedding shape and dtype.

    Args:
        embeddings: Embedding array to validate
        name: Name for error messages

    Raises:
        ValueError: If shape or dtype is invalid
    """
    if not isinstance(embeddings, np.ndarray):
        raise ValueError(f"{name} must be numpy array, got {type(embeddings)}")

    if embeddings.ndim != 2:
        raise ValueError(f"{name} must be 2D, got shape {embeddings.shape}")

    seq_length, dim = embeddings.shape
    if seq_length == 0:
        raise ValueError(f"{name} has zero sequence length")

    # ColPali models use 128 dimensions, mock models use 768
    if dim not in [128, 768]:
        raise ValueError(f"{name} must have dimension 128 or 768, got {dim}")

    if embeddings.dtype not in [np.float32, np.float16]:
        logger.warning(f"{name} has dtype {embeddings.dtype}, expected float32 or float16")
