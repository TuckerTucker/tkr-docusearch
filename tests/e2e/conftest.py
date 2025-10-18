"""
Pytest fixtures for E2E tests.

Provides shared fixtures for integration testing including:
- Service health checks
- Test document helpers
- API clients
- Database cleanup utilities
"""

import os
import time
from pathlib import Path
from typing import Optional

import httpx
import pytest
from fastapi.testclient import TestClient

# ============================================================================
# Service Health Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def chromadb_host() -> str:
    """ChromaDB host from environment."""
    return os.getenv("CHROMA_HOST", "localhost")


@pytest.fixture(scope="session")
def chromadb_port() -> int:
    """ChromaDB port from environment."""
    return int(os.getenv("CHROMA_PORT", 8001))


@pytest.fixture(scope="session")
def worker_api_url() -> str:
    """Worker API base URL."""
    return os.getenv("WORKER_API_URL", "http://localhost:8002")


@pytest.fixture(scope="session")
def copyparty_url() -> str:
    """Copyparty UI base URL."""
    return os.getenv("COPYPARTY_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def chromadb_url(chromadb_host: str, chromadb_port: int) -> str:
    """ChromaDB base URL."""
    return f"http://{chromadb_host}:{chromadb_port}"


@pytest.fixture(scope="session")
def services_available(chromadb_url: str, worker_api_url: str) -> bool:
    """Check if required services are running."""
    try:
        # Check ChromaDB
        response = httpx.get(f"{chromadb_url}/api/v1/heartbeat", timeout=5)
        chromadb_ok = response.status_code == 200

        # Check Worker API
        response = httpx.get(f"{worker_api_url}/health", timeout=5)
        worker_ok = response.status_code == 200

        return chromadb_ok and worker_ok
    except Exception:
        return False


@pytest.fixture
def skip_if_services_unavailable(services_available: bool):
    """Skip test if required services are not running."""
    if not services_available:
        pytest.skip("Required services not running. Run ./scripts/start-all.sh first.")


# ============================================================================
# API Client Fixtures
# ============================================================================


@pytest.fixture
def chromadb_client(chromadb_host: str, chromadb_port: int, skip_if_services_unavailable):
    """Real ChromaDB client for E2E tests."""
    from src.storage.chroma_client import ChromaClient

    return ChromaClient(host=chromadb_host, port=chromadb_port)


@pytest.fixture
def worker_api_client(worker_api_url: str, skip_if_services_unavailable):
    """HTTP client for Worker API."""
    return httpx.Client(base_url=worker_api_url, timeout=30)


@pytest.fixture
def research_api_client(skip_if_services_unavailable):
    """FastAPI test client for Research API."""
    from src.api.research import app

    return TestClient(app)


# ============================================================================
# Test Document Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Fixtures directory path."""
    return Path(__file__).parent


@pytest.fixture(scope="session")
def sample_documents_dir(fixtures_dir: Path) -> Path:
    """Sample documents directory."""
    docs_dir = fixtures_dir / "sample_documents"
    docs_dir.mkdir(parents=True, exist_ok=True)
    return docs_dir


@pytest.fixture
def sample_pdf_with_structure(sample_documents_dir: Path) -> Optional[Path]:
    """
    Sample PDF with complex structure (headings, tables, pictures).

    Returns None if not available - test should create or skip.
    """
    pdf_path = sample_documents_dir / "complex_pdf.pdf"
    return pdf_path if pdf_path.exists() else None


@pytest.fixture
def sample_simple_pdf(sample_documents_dir: Path) -> Optional[Path]:
    """
    Sample PDF without structure (plain text).

    Returns None if not available - test should create or skip.
    """
    pdf_path = sample_documents_dir / "simple_text.pdf"
    return pdf_path if pdf_path.exists() else None


# ============================================================================
# Test Data Management
# ============================================================================


@pytest.fixture
def test_doc_ids() -> list[str]:
    """
    Track document IDs created during test for cleanup.

    Usage:
        def test_something(test_doc_ids):
            doc_id = upload_document(...)
            test_doc_ids.append(doc_id)
            # Test runs
            # Cleanup happens automatically
    """
    doc_ids = []
    yield doc_ids
    # Cleanup happens in separate fixture


@pytest.fixture(autouse=True)
def cleanup_test_documents(test_doc_ids: list[str], chromadb_client):
    """
    Auto-cleanup test documents after each test.

    Removes all documents tracked in test_doc_ids from ChromaDB.
    """
    yield  # Test runs first

    # Cleanup after test
    for doc_id in test_doc_ids:
        try:
            # Delete from visual collection
            chromadb_client._visual_collection.delete(where={"doc_id": doc_id})
            # Delete from text collection
            chromadb_client._text_collection.delete(where={"doc_id": doc_id})
        except Exception as e:
            print(f"Warning: Failed to cleanup doc_id {doc_id}: {e}")


# ============================================================================
# Helper Functions
# ============================================================================


def wait_for_processing(
    worker_api_client: httpx.Client, doc_id: str, timeout: int = 60, poll_interval: float = 1.0
) -> bool:
    """
    Wait for document processing to complete.

    Args:
        worker_api_client: HTTP client for Worker API
        doc_id: Document ID to monitor
        timeout: Maximum seconds to wait
        poll_interval: Seconds between status checks

    Returns:
        True if processing completed successfully, False if failed or timeout
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = worker_api_client.get(f"/status/document/{doc_id}")
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get("status")

                if status == "completed":
                    return True
                elif status == "failed":
                    print(f"Processing failed: {status_data.get('error')}")
                    return False

        except Exception as e:
            print(f"Error checking status: {e}")

        time.sleep(poll_interval)

    print(f"Timeout waiting for processing of {doc_id}")
    return False


@pytest.fixture
def wait_for_processing_helper(worker_api_client: httpx.Client):
    """Fixture providing wait_for_processing helper function."""
    return lambda doc_id, timeout=60: wait_for_processing(worker_api_client, doc_id, timeout)
