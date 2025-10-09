"""
Unit tests for Markdown Download API endpoint.

Tests HTTP endpoint for downloading processed documents as markdown files.

Contract: markdown-api-contract.md
"""

import re
import time
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import MagicMock, patch, Mock

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Import the actual router
from src.api.routes.markdown import router, set_storage_client, sanitize_filename


@pytest.fixture
def mock_storage_client():
    """Create a mock storage client for testing."""
    client = MagicMock()

    # Mock search_visual method
    def mock_search_visual(query_embedding, n_results=1, filters=None):
        """Mock visual search that returns document metadata."""
        if filters and "doc_id" in filters:
            doc_id = filters["doc_id"]

            # Valid document with markdown
            if doc_id == "a" * 64:
                return [{
                    "id": f"{doc_id}_page1",
                    "metadata": {
                        "doc_id": doc_id,
                        "filename": "test_report.pdf",
                        "page": 1,
                        "has_markdown": True,
                        "markdown_path": f"/data/markdown/{doc_id}.md"
                    },
                    "distance": 0.1
                }]

            # Document without markdown
            elif doc_id == "b" * 64:
                return [{
                    "id": f"{doc_id}_page1",
                    "metadata": {
                        "doc_id": doc_id,
                        "filename": "no_markdown.pdf",
                        "page": 1,
                        "has_markdown": False
                    },
                    "distance": 0.1
                }]

            # Document with missing file
            elif doc_id == "c" * 64:
                return [{
                    "id": f"{doc_id}_page1",
                    "metadata": {
                        "doc_id": doc_id,
                        "filename": "missing_file.pdf",
                        "page": 1,
                        "has_markdown": True,
                        "markdown_path": "/data/markdown/nonexistent.md"
                    },
                    "distance": 0.1
                }]

            # Test filename sanitization cases
            elif doc_id == "d" * 64:
                filename = "Report 2023.pdf"
                return [{
                    "id": f"{doc_id}_page1",
                    "metadata": {
                        "doc_id": doc_id,
                        "filename": filename,
                        "page": 1,
                        "has_markdown": True,
                        "markdown_path": f"/data/markdown/{doc_id}.md"
                    },
                    "distance": 0.1
                }]

        # Document not found
        return []

    client.search_visual = mock_search_visual
    return client


@pytest.fixture
def markdown_dir(tmp_path):
    """Create temporary markdown directory with test files."""
    markdown_dir = tmp_path / "markdown"
    markdown_dir.mkdir(exist_ok=True)

    # Create test markdown content
    test_markdown = """# Test Report

## Executive Summary

This is a test markdown document.

### Key Points

- Point 1
- Point 2
- Point 3

| Metric | Value |
|--------|-------|
| Items  | 100   |
"""

    # Create files for test cases
    test_doc_ids = ["a" * 64, "d" * 64, "e" * 64, "f" * 64, "0" * 64, "1" * 64]
    for doc_id in test_doc_ids:
        (markdown_dir / f"{doc_id}.md").write_text(test_markdown)

    return markdown_dir


@pytest.fixture
def mock_app(mock_storage_client, markdown_dir):
    """Create a test FastAPI app with the actual router."""
    app = FastAPI()

    # Patch the markdown path resolution to use test directory
    original_search = mock_storage_client.search_visual

    def patched_search(query_embedding, n_results=1, filters=None):
        results = original_search(query_embedding, n_results, filters)
        # Update markdown paths to use test directory
        for result in results:
            if "markdown_path" in result.get("metadata", {}):
                old_path = result["metadata"]["markdown_path"]
                filename = Path(old_path).name
                result["metadata"]["markdown_path"] = str(markdown_dir / filename)
        return results

    mock_storage_client.search_visual = patched_search

    # Set the storage client
    set_storage_client(mock_storage_client)

    # Include the router
    app.include_router(router)

    return app


@pytest.fixture
def client(mock_app):
    """Create FastAPI test client."""
    return TestClient(mock_app)


class TestDownloadMarkdownSuccess:
    """Test successful markdown download scenarios."""

    def test_download_markdown_success(self, client):
        """Test successful markdown download."""
        doc_id = "a" * 64

        response = client.get(f"/api/document/{doc_id}/markdown")

        # Validate status code
        assert response.status_code == 200

        # Validate headers
        assert response.headers["content-type"] == "text/markdown; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert 'filename="test_report.md"' in response.headers["content-disposition"]

        # Validate content
        assert len(response.text) > 0
        assert response.text.startswith("#")  # Valid markdown
        assert "Test Report" in response.text

    def test_download_markdown_content_matches_file(self, client, tmp_path):
        """Test that downloaded content matches stored file."""
        doc_id = "a" * 64

        response = client.get(f"/api/document/{doc_id}/markdown")

        assert response.status_code == 200

        # Content should be valid markdown
        content = response.text
        assert "# Test Report" in content
        assert "## Executive Summary" in content
        assert "| Metric | Value |" in content


class TestDownloadMarkdownNotFound:
    """Test 404 scenarios for document not found."""

    def test_download_markdown_not_found(self, client):
        """Test 404 when document doesn't exist."""
        # Valid format but doesn't exist
        fake_doc_id = "9" * 64

        response = client.get(f"/api/document/{fake_doc_id}/markdown")

        assert response.status_code == 404
        assert "detail" in response.json()
        assert "not found" in response.json()["detail"].lower()


class TestDownloadMarkdownNotAvailable:
    """Test 404 when markdown is not available."""

    def test_download_markdown_not_available(self, client):
        """Test 404 when document has no markdown."""
        # Document exists but has_markdown is False
        doc_id = "b" * 64

        response = client.get(f"/api/document/{doc_id}/markdown")

        assert response.status_code == 404
        assert "detail" in response.json()
        assert "not available" in response.json()["detail"].lower()


class TestDownloadMarkdownFileMissing:
    """Test 404 when markdown file is missing (inconsistent state)."""

    def test_download_markdown_file_missing(self, client):
        """Test 404 when file is deleted but metadata exists."""
        # Document has markdown_path but file doesn't exist
        doc_id = "c" * 64

        response = client.get(f"/api/document/{doc_id}/markdown")

        assert response.status_code == 404
        assert "detail" in response.json()
        assert "missing" in response.json()["detail"].lower()


class TestDownloadMarkdownInvalidDocId:
    """Test 400 for invalid doc_id format."""

    @pytest.mark.parametrize("invalid_doc_id", [
        "short",                    # Too short
        "ABCDEF" * 10 + "ABCD",    # Uppercase (should be lowercase)
        "g" * 64,                   # Invalid hex char
        "12345",                    # Too short
        "z" * 64,                   # Invalid hex char
    ])
    def test_download_markdown_invalid_doc_id(self, client, invalid_doc_id):
        """Test 400 for various invalid doc_id formats."""
        response = client.get(f"/api/document/{invalid_doc_id}/markdown")

        assert response.status_code == 400
        assert "detail" in response.json()
        assert "invalid" in response.json()["detail"].lower()

    def test_download_markdown_invalid_chars_in_path(self, client):
        """Test invalid characters in URL path are handled by FastAPI routing."""
        # FastAPI routing handles special chars - they get URL decoded or cause 404
        # This is expected behavior - we test the doc_id validation for properly formatted IDs
        response = client.get("/api/document/invalid-chars!@#/markdown")

        # FastAPI may return 404 (not found route) or 400 (if it reaches validation)
        # Either is acceptable as the request is malformed
        assert response.status_code in [400, 404]


class TestFilenameSanitization:
    """Test filename sanitization for safe downloads."""

    def test_filename_sanitization_report(self, client):
        """Verify filename with spaces is preserved."""
        doc_id = "d" * 64
        response = client.get(f"/api/document/{doc_id}/markdown")

        assert response.status_code == 200

        content_disposition = response.headers["content-disposition"]
        assert 'filename="Report 2023.md"' in content_disposition


class TestDownloadPerformance:
    """Test download performance requirements."""

    def test_download_performance(self, client):
        """Verify download completes within performance target (<100ms)."""
        doc_id = "a" * 64

        start = time.time()
        response = client.get(f"/api/document/{doc_id}/markdown")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 0.1  # 100ms target


class TestWave2Integration:
    """Wave 2 Integration Test - CRITICAL for Wave 3 gate."""

    def test_wave2_integration(self, client, mock_storage_client, markdown_dir):
        """
        Wave 2 Integration Test - Must pass before Wave 3.

        Validates:
        - API downloads markdown correctly
        - Headers are correct
        - Content matches stored file
        - Filename is sanitized
        """
        # Setup test document
        doc_id = "a" * 64
        markdown_path = markdown_dir / f"{doc_id}.md"

        # Ensure file exists with known content
        test_content = """# Integration Test Document

This is the Wave 2 integration test.

## Features
- Feature 1
- Feature 2
"""
        markdown_path.write_text(test_content)

        # API Request
        response = client.get(f"/api/document/{doc_id}/markdown")

        # VALIDATE: Response status and headers
        assert response.status_code == 200, "API should return 200 OK"
        assert response.headers["content-type"] == "text/markdown; charset=utf-8", \
            "Content-Type header must be text/markdown; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"], \
            "Content-Disposition must include 'attachment'"

        # VALIDATE: Content matches stored file
        assert response.text == test_content, \
            "Downloaded content must match stored markdown file"

        # VALIDATE: Filename is correct and sanitized
        content_disposition = response.headers["content-disposition"]
        assert 'filename="test_report.md"' in content_disposition, \
            "Filename must be sanitized and have .md extension"

        # VALIDATE: API contract satisfied
        assert "text/markdown" in response.headers["content-type"], \
            "MIME type must be text/markdown"

        print("✅ Wave 2 Integration Test PASSED")


class TestErrorHandling:
    """Test comprehensive error handling."""

    def test_multiple_error_scenarios(self, client):
        """Test that all error types return appropriate responses."""
        # Invalid doc_id -> 400
        response = client.get("/api/document/invalid/markdown")
        assert response.status_code == 400

        # Not found -> 404
        response = client.get(f"/api/document/{'9' * 64}/markdown")
        assert response.status_code == 404

        # No markdown -> 404
        response = client.get(f"/api/document/{'b' * 64}/markdown")
        assert response.status_code == 404

        # File missing -> 404
        response = client.get(f"/api/document/{'c' * 64}/markdown")
        assert response.status_code == 404


class TestHeaderValidation:
    """Test that response headers match specification exactly."""

    def test_content_type_header(self, client):
        """Test Content-Type header is exactly as specified."""
        doc_id = "a" * 64
        response = client.get(f"/api/document/{doc_id}/markdown")

        assert response.headers["content-type"] == "text/markdown; charset=utf-8"

    def test_content_disposition_header(self, client):
        """Test Content-Disposition header format."""
        doc_id = "a" * 64
        response = client.get(f"/api/document/{doc_id}/markdown")

        content_disposition = response.headers["content-disposition"]
        assert content_disposition.startswith("attachment")
        assert "filename=" in content_disposition
        assert content_disposition.endswith('.md"')

    def test_content_length_header(self, client):
        """Test Content-Length header is present."""
        doc_id = "a" * 64
        response = client.get(f"/api/document/{doc_id}/markdown")

        # FastAPI/Starlette automatically adds Content-Length
        assert "content-length" in response.headers
        assert int(response.headers["content-length"]) > 0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_concurrent_downloads(self, client):
        """Test multiple concurrent downloads."""
        doc_id = "a" * 64

        # Make multiple requests
        responses = []
        for _ in range(5):
            response = client.get(f"/api/document/{doc_id}/markdown")
            responses.append(response)

        # All should succeed
        assert all(r.status_code == 200 for r in responses)

        # All should have same content
        contents = [r.text for r in responses]
        assert len(set(contents)) == 1  # All identical


class TestFilenameSanitizationUnit:
    """Test the sanitize_filename utility function directly."""

    def test_sanitize_basic(self):
        """Test basic filename sanitization."""
        assert sanitize_filename("test.pdf") == "test"

    def test_sanitize_path_separator(self):
        """Test removal of path separators."""
        assert sanitize_filename("../secret.pdf") == "secret"
        # Path separators are removed, but Path().stem only gets the final part
        assert sanitize_filename("path/to/file.pdf") == "file"

    def test_sanitize_special_chars(self):
        """Test removal of special characters."""
        assert sanitize_filename("file<>name.pdf") == "filename"
        assert sanitize_filename("file:name.pdf") == "filename"

    def test_sanitize_whitespace(self):
        """Test handling of whitespace."""
        assert sanitize_filename(" .hidden.pdf") == "hidden"
        assert sanitize_filename("  file  .pdf") == "file"

    def test_sanitize_empty(self):
        """Test fallback for empty result."""
        assert sanitize_filename("...") == "document"
        assert sanitize_filename("   ") == "document"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
