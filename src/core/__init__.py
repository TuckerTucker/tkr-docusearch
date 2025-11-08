"""
Core module for DocuSearch.

This module provides the foundational infrastructure for the DocuSearch application,
following Inversion of Control (IoC) and DRY (Don't Repeat Yourself) principles.

The core module consolidates:
    - Shared exceptions (src.core.exceptions)
    - Shared types and type definitions (src.core.types)
    - Cross-cutting utility functions (src.core.utils)

By centralizing these components, we:
    1. Eliminate circular dependencies
    2. Reduce code duplication
    3. Improve maintainability
    4. Enable consistent error handling and type checking
    5. Provide a single source of truth for shared functionality

Architecture:
    ```
    src/core/
    ├── __init__.py           # This file - core module interface
    ├── exceptions/           # Shared exception classes
    │   └── __init__.py
    ├── types/                # Shared type definitions
    │   └── __init__.py
    └── utils/                # Cross-cutting utilities
        └── __init__.py
    ```

Usage:
    >>> from src.core.exceptions import DocuSearchException
    >>> from src.core.types import DocID, DocType
    >>> from src.core.utils import sanitize_filename

Migration Plan (Quality Improvement Sprint Wave 2):
    - Phase 1: Migrate exceptions from individual modules
    - Phase 2: Migrate type definitions to TypedDict/dataclasses
    - Phase 3: Extract and consolidate duplicate utility functions
    - Phase 4: Update all imports to use core module

Note:
    This module is currently a placeholder infrastructure. The actual migration
    of exceptions, types, and utilities will occur during Wave 2 of the
    Quality Improvement Sprint.
"""

# Import core components for convenience
from src.core.exceptions import DocuSearchException
from src.core.types import ChunkID, DocID, DocType, EmbeddingVector, ProcessingStatus, Score

# Note: utils exports will be added during Wave 2 migration

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Exceptions
    "DocuSearchException",
    # Types
    "DocID",
    "ChunkID",
    "EmbeddingVector",
    "Score",
    "DocType",
    "ProcessingStatus",
    # Utils will be added during Wave 2
]
