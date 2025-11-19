"""
Pytest fixtures for .doc file conversion integration tests.

Provides reusable test data and setup for integration testing the
legacy .doc to .docx conversion pipeline.

Author: Agent-Integration-Testing
Date: 2025-11-19
Wave: 8 (Legacy Office Doc Conversion)
"""

import logging
import os
from pathlib import Path
from typing import Optional

import pytest

from tkr_docusearch.processing.legacy_office_client import (
    LegacyOfficeClient,
    get_legacy_office_client,
)

logger = logging.getLogger(__name__)


# ====================================================================================
# Legacy Office Service Fixtures
# ====================================================================================


@pytest.fixture(scope="session")
def legacy_office_host() -> str:
    """Legacy office service host from environment."""
    return os.getenv("LEGACY_OFFICE_HOST", "localhost")


@pytest.fixture(scope="session")
def legacy_office_port() -> int:
    """Legacy office service port from environment."""
    return int(os.getenv("LEGACY_OFFICE_PORT", "8003"))


@pytest.fixture(scope="session")
def legacy_office_url(legacy_office_host: str, legacy_office_port: int) -> str:
    """Legacy office service base URL."""
    return f"http://{legacy_office_host}:{legacy_office_port}"


@pytest.fixture
def legacy_office_client(legacy_office_host: str, legacy_office_port: int) -> LegacyOfficeClient:
    """Get legacy office client instance for testing.

    Returns:
        LegacyOfficeClient configured with test environment settings
    """
    return LegacyOfficeClient(host=legacy_office_host, port=legacy_office_port)


@pytest.fixture
def legacy_office_singleton() -> LegacyOfficeClient:
    """Get singleton legacy office client instance.

    Returns:
        LegacyOfficeClient singleton instance
    """
    return get_legacy_office_client()


@pytest.fixture(scope="session")
def legacy_office_available(legacy_office_url: str) -> bool:
    """Check if legacy office service is running.

    Returns:
        True if service is accessible, False otherwise
    """
    import requests

    try:
        response = requests.get(f"{legacy_office_url}/health", timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.warning(f"Legacy office service not available: {e}")
        return False


@pytest.fixture
def skip_if_legacy_office_unavailable(legacy_office_available: bool):
    """Skip test if legacy office service is not running.

    Usage:
        def test_something(skip_if_legacy_office_unavailable):
            # Test code that requires legacy-office-converter service
    """
    if not legacy_office_available:
        pytest.skip(
            "Legacy office service not running. "
            "Run 'docker compose up -d legacy-office-converter' first."
        )


# ====================================================================================
# Test Document Fixtures
# ====================================================================================


@pytest.fixture
def sample_doc_file(tmp_path: Path) -> Optional[Path]:
    """Create or locate a sample .doc file for testing.

    This fixture attempts to find an existing test .doc file, or returns
    a path where one should be created.

    Args:
        tmp_path: pytest temporary directory

    Returns:
        Path to sample .doc file if it exists, otherwise None
    """
    # Check if there's a test .doc file in fixtures
    fixtures_dir = Path(__file__).parent.parent / "fixtures"

    # Common test .doc filenames
    possible_names = ["sample.doc", "test.doc", "quarterly-report.doc"]

    for name in possible_names:
        doc_path = fixtures_dir / name
        if doc_path.exists() and doc_path.suffix.lower() == ".doc":
            logger.info(f"Found sample .doc file: {doc_path}")
            return doc_path

    # Could return tmp_path / "test.doc" for tests to create
    logger.warning("No sample .doc file found in fixtures")
    return None


@pytest.fixture
def docker_doc_path() -> str:
    """Get Docker path format for test .doc file.

    Returns:
        Docker-formatted path (e.g., /uploads/test.doc)
    """
    return "/uploads/test.doc"


@pytest.fixture
def docker_pptx_path() -> str:
    """Get Docker path format for test .pptx file.

    Returns:
        Docker-formatted path (e.g., /uploads/test.pptx)
    """
    return "/uploads/test.pptx"


# ====================================================================================
# Mock Fixtures
# ====================================================================================


@pytest.fixture
def mock_doc_conversion_result() -> dict:
    """Mock result from successful .doc to .docx conversion.

    Returns:
        Dictionary matching LegacyOfficeClient.convert_doc_to_docx response
    """
    return {
        "success": True,
        "docx_path": "/uploads/test.docx",
        "file_size_bytes": 15360,
        "conversion_time_ms": 234,
    }


@pytest.fixture
def mock_health_response() -> dict:
    """Mock health endpoint response from legacy office service.

    Returns:
        Dictionary with service capabilities
    """
    return {
        "service": "legacy-office-converter",
        "status": "healthy",
        "version": "1.0.0",
        "capabilities": ["pptx-rendering", "doc-conversion"],
    }


# ====================================================================================
# Storage Fixtures (for E2E tests)
# ====================================================================================


@pytest.fixture
def embedding_engine_instance():
    """Mock embedding engine for testing.

    Returns:
        Mock embedding engine with required interface
    """
    from unittest.mock import Mock

    engine = Mock()
    engine.generate_text_embeddings.return_value = [[0.1] * 128]
    engine.generate_image_embeddings.return_value = [[0.2] * 128]
    return engine


@pytest.fixture
def storage_client_instance():
    """Mock storage client for testing.

    Returns:
        Mock storage client with ChromaDB interface
    """
    from unittest.mock import Mock

    client = Mock()

    # Mock collection methods
    mock_collection = Mock()
    mock_collection.add.return_value = None
    mock_collection.get.return_value = {"metadatas": [], "documents": [], "ids": []}

    client._visual_collection = mock_collection
    client._text_collection = mock_collection
    client.get_collection.return_value = mock_collection

    return client


# ====================================================================================
# Cleanup Fixtures
# ====================================================================================


@pytest.fixture
def cleanup_converted_files():
    """Cleanup fixture to remove converted .docx files after test.

    Usage:
        def test_conversion(cleanup_converted_files):
            docx_path = convert_doc(...)
            cleanup_converted_files.append(docx_path)
            # Test runs
            # Files are deleted automatically
    """
    files_to_cleanup = []

    yield files_to_cleanup

    # Cleanup after test
    for file_path in files_to_cleanup:
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"Cleaned up: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {file_path}: {e}")
