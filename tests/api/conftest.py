"""Shared fixtures for API integration tests.

Provides real KojiClient instances (file-backed via tmp_path), seeded
databases, and FastAPI TestClient factories for the worker and main API
apps.  All fixtures run without GPU — mock embedding engines are used
where models would normally be required.
"""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Any, Generator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from tkr_docusearch.config.koji_config import KojiConfig
from tkr_docusearch.storage.koji_client import KojiClient

# ---------------------------------------------------------------------------
# Fixtures directory
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def sample_fixtures_dir() -> Path:
    """Path to tests/fixtures/ containing sample documents."""
    return FIXTURES_DIR


# ---------------------------------------------------------------------------
# Real Koji clients
# ---------------------------------------------------------------------------


@pytest.fixture
def koji_api_client(tmp_path: Path) -> Generator[KojiClient, None, None]:
    """Real KojiClient backed by a temporary file database."""
    config = KojiConfig(db_path=str(tmp_path / "api_test.db"))
    client = KojiClient(config)
    client.open()
    yield client
    client.close()


@pytest.fixture
def seeded_koji_client(tmp_path: Path) -> Generator[KojiClient, None, None]:
    """KojiClient pre-populated with 3 documents, pages, and chunks.

    Documents:
        - doc-alpha  (sample.pdf,  2 pages,  3 chunks)
        - doc-beta   (report.docx, 1 page,   2 chunks)
        - doc-gamma  (notes.md,    1 page,   1 chunk)
    """
    config = KojiConfig(db_path=str(tmp_path / "seeded_test.db"))
    client = KojiClient(config)
    client.open()

    _seed_documents(client)

    yield client
    client.close()


def _seed_documents(client: KojiClient) -> None:
    """Populate a KojiClient with test data."""
    docs = [
        ("doc-alpha", "sample.pdf", "pdf", 2),
        ("doc-beta", "report.docx", "docx", 1),
        ("doc-gamma", "notes.md", "md", 1),
    ]

    for doc_id, filename, fmt, num_pages in docs:
        client.create_document(
            doc_id=doc_id,
            filename=filename,
            format=fmt,
            num_pages=num_pages,
        )

        pages = []
        for page_num in range(1, num_pages + 1):
            pages.append({
                "id": f"{doc_id}-page-{page_num}",
                "doc_id": doc_id,
                "page_num": page_num,
            })
        if pages:
            client.insert_pages(pages)

    # Chunks for doc-alpha
    client.insert_chunks([
        {"id": "doc-alpha-chunk-1", "doc_id": "doc-alpha", "page_num": 1,
         "text": "Introduction to machine learning concepts.", "word_count": 5},
        {"id": "doc-alpha-chunk-2", "doc_id": "doc-alpha", "page_num": 1,
         "text": "Supervised learning uses labeled training data.", "word_count": 6},
        {"id": "doc-alpha-chunk-3", "doc_id": "doc-alpha", "page_num": 2,
         "text": "Neural networks are composed of layers.", "word_count": 6},
    ])

    # Chunks for doc-beta
    client.insert_chunks([
        {"id": "doc-beta-chunk-1", "doc_id": "doc-beta", "page_num": 1,
         "text": "Quarterly revenue report summary.", "word_count": 4},
        {"id": "doc-beta-chunk-2", "doc_id": "doc-beta", "page_num": 1,
         "text": "Growth exceeded expectations in Q3.", "word_count": 5},
    ])

    # Chunks for doc-gamma
    client.insert_chunks([
        {"id": "doc-gamma-chunk-1", "doc_id": "doc-gamma", "page_num": 1,
         "text": "Meeting notes from the design review.", "word_count": 6},
    ])
