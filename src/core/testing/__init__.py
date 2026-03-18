"""
Core testing utilities for tkr-docusearch.

This module provides centralized test infrastructure including:
- Mock implementations of external dependencies
- Test fixtures and sample data
- Helper functions for common test operations

Usage:
    >>> from src.core.testing.mocks import MockEmbeddingModel, MockKojiClient
    >>> from src.core.testing.mocks import MockEmbeddingEngine, MockStorageClient

Example:
    # In a test file
    from src.core.testing.mocks import MockEmbeddingEngine, MockStorageClient

    def test_search_pipeline():
        engine = MockEmbeddingEngine()
        storage = MockStorageClient()
        # ... test code
"""

from tkr_docusearch.core.testing.mocks import (
    MockColPaliModel,
    MockEmbeddingEngine,
    MockEmbeddingModel,
    MockKojiClient,
    MockSearchEngine,
    MockStorageClient,
)

__all__ = [
    "MockEmbeddingModel",
    "MockColPaliModel",
    "MockKojiClient",
    "MockSearchEngine",
    "MockEmbeddingEngine",
    "MockStorageClient",
]
