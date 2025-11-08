"""
Core testing utilities for tkr-docusearch.

This module provides centralized test infrastructure including:
- Mock implementations of external dependencies
- Test fixtures and sample data
- Helper functions for common test operations

Usage:
    >>> from src.core.testing.mocks import MockColPaliModel, MockChromaDBClient
    >>> from src.core.testing.fixtures import sample_document, sample_embeddings
    >>> from src.core.testing.helpers import create_temp_pdf, assert_embeddings_valid

Example:
    # In a test file
    from src.core.testing.mocks import MockEmbeddingEngine, MockStorageClient

    def test_search_pipeline():
        engine = MockEmbeddingEngine()
        storage = MockStorageClient()
        # ... test code
"""

from src.core.testing.mocks import (
    MockChromaDBClient,
    MockCollection,
    MockColPaliModel,
    MockEmbeddingEngine,
    MockSearchEngine,
    MockStorageClient,
)

__all__ = [
    "MockColPaliModel",
    "MockChromaDBClient",
    "MockCollection",
    "MockSearchEngine",
    "MockEmbeddingEngine",
    "MockStorageClient",
]
