"""
Embeddings module for DocuSearch.

This module provides embedding engines for ColNomic multi-vector
embeddings — either via gRPC (ShikomiClient) or in-process
(InProcessEmbeddingEngine). Use ``create_embedding_engine`` to
select the appropriate engine based on configuration.

Components:
- ShikomiClient: gRPC client for remote embedding service
- InProcessEmbeddingEngine: In-process embedding via ColNomicEngine
- create_embedding_engine: Factory for engine selection
"""

from .factory import create_embedding_engine
from .in_process_engine import InProcessEmbeddingEngine
from .shikomi_client import ShikomiClient

__all__ = [
    "ShikomiClient",
    "InProcessEmbeddingEngine",
    "create_embedding_engine",
]
