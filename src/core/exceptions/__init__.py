"""
Core exceptions module for DocuSearch.

This module provides shared exception classes used across the DocuSearch application.
Following Inversion of Control (IoC) principles, all specialized exceptions should
be defined here to avoid circular dependencies and provide a single source of truth.

Future Exception Categories:
    - Configuration exceptions (missing env vars, invalid config)
    - Processing exceptions (document processing failures)
    - Storage exceptions (ChromaDB, file system errors)
    - Search exceptions (query failures, embedding errors)
    - Research exceptions (LLM API errors, citation failures)

Design Principles:
    - All exceptions inherit from DocuSearchException base class
    - Include context-rich error messages
    - Support error chaining (cause tracking)
    - Provide machine-readable error codes
    - Log exceptions appropriately

Usage:
    >>> from src.core.exceptions import DocuSearchException
    >>> raise DocuSearchException("Something went wrong")

Note:
    This module is currently a placeholder for future centralized exception handling.
    As part of Quality Improvement Sprint Wave 2, exceptions will be migrated here
    from individual modules.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DocuSearchException(Exception):
    """
    Base exception class for all DocuSearch exceptions.

    All custom exceptions in the application should inherit from this class
    to enable consistent error handling and logging.

    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code (e.g., "CONFIG_001")
        cause: Optional underlying exception that caused this error
    """

    def __init__(
        self, message: str, error_code: Optional[str] = None, cause: Optional[Exception] = None
    ) -> None:
        """
        Initialize DocuSearchException.

        Args:
            message: Human-readable error message
            error_code: Optional machine-readable error code
            cause: Optional underlying exception
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "UNKNOWN"
        self.cause = cause

        # Log exception creation for debugging
        logger.debug(f"DocuSearchException created: {error_code} - {message}", exc_info=cause)

    def __str__(self) -> str:
        """String representation of exception."""
        if self.cause:
            return f"[{self.error_code}] {self.message} (caused by: {self.cause})"
        return f"[{self.error_code}] {self.message}"


# Placeholder for future exception classes
# These will be added during Wave 2 migration:
#
# class ConfigurationError(DocuSearchException):
#     """Raised when configuration is invalid or missing."""
#     pass
#
# class ProcessingError(DocuSearchException):
#     """Raised when document processing fails."""
#     pass
#
# class StorageError(DocuSearchException):
#     """Raised when storage operations fail."""
#     pass
#
# class SearchError(DocuSearchException):
#     """Raised when search operations fail."""
#     pass
#
# class ResearchError(DocuSearchException):
#     """Raised when research bot operations fail."""
#     pass


__all__ = [
    "DocuSearchException",
]
