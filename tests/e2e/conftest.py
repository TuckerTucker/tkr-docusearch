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
def worker_api_url() -> str:
    """Worker API base URL."""
    return os.getenv("WORKER_API_URL", "http://localhost:8002")


@pytest.fixture(scope="session")
def koji_db_path() -> str:
    """Koji database path from environment."""
    return os.getenv("KOJI_DB_PATH", "data/koji.db")


@pytest.fixture(scope="session")
def services_available(worker_api_url: str) -> bool:
    """Check if required services are running."""
    try:
        response = httpx.get(f"{worker_api_url}/health", timeout=5)
        return response.status_code == 200
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
def koji_client(skip_if_services_unavailable, tmp_path):
    """KojiClient for E2E tests backed by a temporary database."""
    from tkr_docusearch.config.koji_config import KojiConfig
    from tkr_docusearch.storage.koji_client import KojiClient

    config = KojiConfig(db_path=str(tmp_path / "e2e_test.db"))
    client = KojiClient(config)
    client.open()
    yield client
    client.close()


@pytest.fixture
def worker_api_client(worker_api_url: str, skip_if_services_unavailable):
    """HTTP client for Worker API."""
    return httpx.Client(base_url=worker_api_url, timeout=30)


@pytest.fixture
def research_api_client(skip_if_services_unavailable):
    """FastAPI test client for Research API."""
    from tkr_docusearch.api.research import app

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
def cleanup_test_documents(test_doc_ids: list[str]):
    """
    Auto-cleanup test documents after each test.

    Note: With Koji, cleanup is handled by the temporary database
    created per-test via the koji_client fixture.
    """
    yield  # Test runs first
    # No explicit cleanup needed — temp DB is discarded on fixture teardown


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
