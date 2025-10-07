"""
Query processing module for embedding generation and validation.

This module handles query embedding generation and preprocessing for the
two-stage search pipeline.

Usage:
    >>> from src.search.query_processor import QueryProcessor
    >>> processor = QueryProcessor(embedding_engine)
    >>> result = processor.process_query("quarterly revenue growth")
"""

import logging
from typing import Dict, Any
import numpy as np

logger = logging.getLogger(__name__)


class QueryProcessor:
    """
    Query processor for embedding generation and validation.

    Responsibilities:
    - Validate and preprocess query strings
    - Generate multi-vector query embeddings
    - Extract CLS token for Stage 1 retrieval
    - Cache frequently used queries (future enhancement)
    """

    def __init__(self, embedding_engine, max_query_length: int = 100):
        """
        Initialize query processor.

        Args:
            embedding_engine: ColPali engine or mock for query embedding
            max_query_length: Maximum query length in words (default: 100)
        """
        self.embedding_engine = embedding_engine
        self.max_query_length = max_query_length

        logger.info(
            f"Initialized QueryProcessor (max_length={max_query_length})"
        )

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process query and generate embeddings.

        Args:
            query: Natural language search query

        Returns:
            Dict with:
            - query: Original query string
            - processed_query: Preprocessed query
            - embeddings: Full multi-vector, shape (seq_length, 768)
            - cls_token: Representative vector, shape (768,)
            - seq_length: Number of tokens
            - processing_time_ms: Time taken

        Raises:
            ValueError: If query is empty or invalid
            QueryProcessingError: If embedding generation fails
        """
        # Validate query
        validated_query = self._validate_query(query)

        # Preprocess query
        processed_query = self._preprocess_query(validated_query)

        # Generate embeddings
        try:
            embedding_output = self.embedding_engine.embed_query(processed_query)

            return {
                "query": query,
                "processed_query": processed_query,
                "embeddings": embedding_output["embeddings"],
                "cls_token": embedding_output["cls_token"],
                "seq_length": embedding_output["seq_length"],
                "processing_time_ms": embedding_output["processing_time_ms"]
            }

        except Exception as e:
            logger.error(f"Query embedding failed: {e}")
            raise QueryProcessingError(f"Failed to embed query: {e}") from e

    def _validate_query(self, query: str) -> str:
        """
        Validate query string.

        Args:
            query: Raw query string

        Returns:
            Validated query

        Raises:
            ValueError: If query is invalid
        """
        if not query:
            raise ValueError("Query cannot be None")

        if not isinstance(query, str):
            raise ValueError(f"Query must be string, got {type(query)}")

        query = query.strip()

        if not query:
            raise ValueError("Query cannot be empty")

        if len(query) > 1000:
            logger.warning(f"Query exceeds 1000 characters, truncating")
            query = query[:1000]

        return query

    def _preprocess_query(self, query: str) -> str:
        """
        Preprocess query string.

        Preprocessing steps:
        - Remove extra whitespace
        - Truncate to max_query_length words
        - Remove special characters (optional, kept for semantic meaning)

        Args:
            query: Validated query string

        Returns:
            Preprocessed query
        """
        # Remove extra whitespace
        query = " ".join(query.split())

        # Truncate to max words
        words = query.split()
        if len(words) > self.max_query_length:
            logger.warning(
                f"Query exceeds {self.max_query_length} words, truncating from "
                f"{len(words)} words"
            )
            query = " ".join(words[:self.max_query_length])

        return query

    def validate_embedding(self, embeddings: np.ndarray, expected_dim: int = 768) -> bool:
        """
        Validate embedding shape and values.

        Args:
            embeddings: Embedding array to validate
            expected_dim: Expected embedding dimension (default: 768)

        Returns:
            True if valid

        Raises:
            ValueError: If embedding is invalid
        """
        if embeddings.ndim != 2:
            raise ValueError(
                f"Embeddings must be 2D array, got shape {embeddings.shape}"
            )

        seq_length, dim = embeddings.shape

        if dim != expected_dim:
            raise ValueError(
                f"Embeddings must have dimension {expected_dim}, got {dim}"
            )

        if seq_length == 0:
            raise ValueError("Embeddings cannot have zero sequence length")

        if not np.isfinite(embeddings).all():
            raise ValueError("Embeddings contain non-finite values")

        return True


class QueryProcessingError(Exception):
    """Exception raised when query processing fails."""
    pass
