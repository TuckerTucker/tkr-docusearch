"""
Tests for centralized URL builder.

Validates URL construction for all parameter combinations and edge cases.
"""

import pytest

from tkr_docusearch.utils.url_builder import add_details_url_to_source, build_details_url


class TestBuildDetailsUrl:
    """Tests for build_details_url() function."""

    def test_basic_url_absolute(self):
        """Test basic URL with doc_id only (absolute)."""
        url = build_details_url("abc123", absolute=True)
        assert url == "http://localhost:3000/details/abc123"

    def test_basic_url_relative(self):
        """Test basic URL with doc_id only (relative)."""
        url = build_details_url("abc123", absolute=False)
        assert url == "/details/abc123"

    def test_url_with_page_absolute(self):
        """Test URL with page parameter (absolute)."""
        url = build_details_url("abc123", page=5, absolute=True)
        assert url == "http://localhost:3000/details/abc123?page=5"

    def test_url_with_page_relative(self):
        """Test URL with page parameter (relative)."""
        url = build_details_url("abc123", page=5, absolute=False)
        assert url == "/details/abc123?page=5"

    def test_url_with_chunk_absolute(self):
        """Test URL with chunk_id parameter (absolute)."""
        url = build_details_url("abc123", chunk_id="abc123-chunk0042", absolute=True)
        assert url == "http://localhost:3000/details/abc123?chunk=abc123-chunk0042"

    def test_url_with_chunk_relative(self):
        """Test URL with chunk_id parameter (relative)."""
        url = build_details_url("abc123", chunk_id="abc123-chunk0042", absolute=False)
        assert url == "/details/abc123?chunk=abc123-chunk0042"

    def test_url_with_page_and_chunk_absolute(self):
        """Test URL with both page and chunk_id (absolute)."""
        url = build_details_url("abc123", page=5, chunk_id="abc123-page5", absolute=True)
        assert url == "http://localhost:3000/details/abc123?page=5&chunk=abc123-page5"

    def test_url_with_page_and_chunk_relative(self):
        """Test URL with both page and chunk_id (relative)."""
        url = build_details_url("abc123", page=5, chunk_id="abc123-page5", absolute=False)
        assert url == "/details/abc123?page=5&chunk=abc123-page5"

    def test_url_with_first_page(self):
        """Test URL with page=1 (first page)."""
        url = build_details_url("abc123", page=1, absolute=False)
        assert url == "/details/abc123?page=1"

    def test_url_with_large_page_number(self):
        """Test URL with large page number."""
        url = build_details_url("abc123", page=999, absolute=False)
        assert url == "/details/abc123?page=999"

    def test_empty_chunk_id_ignored(self):
        """Test that empty chunk_id is ignored."""
        url = build_details_url("abc123", page=5, chunk_id="", absolute=False)
        assert url == "/details/abc123?page=5"

    def test_whitespace_chunk_id_ignored(self):
        """Test that whitespace-only chunk_id is ignored."""
        url = build_details_url("abc123", page=5, chunk_id="   ", absolute=False)
        assert url == "/details/abc123?page=5"

    def test_chunk_id_with_whitespace_trimmed(self):
        """Test that chunk_id with leading/trailing whitespace is trimmed."""
        url = build_details_url("abc123", chunk_id="  abc123-chunk0042  ", absolute=False)
        assert url == "/details/abc123?chunk=abc123-chunk0042"

    def test_none_chunk_id_ignored(self):
        """Test that None chunk_id is ignored."""
        url = build_details_url("abc123", page=5, chunk_id=None, absolute=False)
        assert url == "/details/abc123?page=5"

    def test_none_page_ignored(self):
        """Test that None page is ignored."""
        url = build_details_url("abc123", page=None, chunk_id="abc123-chunk0042", absolute=False)
        assert url == "/details/abc123?chunk=abc123-chunk0042"

    def test_invalid_page_zero_ignored(self):
        """Test that page=0 is ignored (invalid)."""
        url = build_details_url("abc123", page=0, absolute=False)
        assert url == "/details/abc123"

    def test_invalid_page_negative_ignored(self):
        """Test that negative page is ignored (invalid)."""
        url = build_details_url("abc123", page=-5, absolute=False)
        assert url == "/details/abc123"

    def test_missing_doc_id_raises_error(self):
        """Test that missing doc_id raises ValueError."""
        with pytest.raises(ValueError, match="doc_id is required"):
            build_details_url("", absolute=False)

    def test_none_doc_id_raises_error(self):
        """Test that None doc_id raises ValueError."""
        with pytest.raises(ValueError, match="doc_id is required"):
            build_details_url(None, absolute=False)

    def test_special_characters_in_chunk_id(self):
        """Test URL encoding of special characters in chunk_id."""
        # Spaces and special chars should be URL-encoded
        url = build_details_url("abc123", chunk_id="abc123-chunk 0042", absolute=False)
        assert "chunk=abc123-chunk+0042" in url or "chunk=abc123-chunk%200042" in url

    def test_long_doc_id(self):
        """Test URL with long doc_id (SHA-256 hash)."""
        long_doc_id = "929a4b57-aedc-44cf-a686-b19cb50466ae"
        url = build_details_url(long_doc_id, page=13, absolute=False)
        assert url == f"/details/{long_doc_id}?page=13"

    def test_environment_variable_override(self, monkeypatch):
        """Test that FRONTEND_URL environment variable is respected."""
        monkeypatch.setenv("FRONTEND_URL", "https://docusearch.example.com")

        # Need to reimport to pick up new environment variable
        import importlib

        from src.utils import url_builder

        importlib.reload(url_builder)

        url = url_builder.build_details_url("abc123", absolute=True)
        assert url == "https://docusearch.example.com/details/abc123"

        # Reset to default
        monkeypatch.delenv("FRONTEND_URL", raising=False)
        importlib.reload(url_builder)

    def test_absolute_default_is_true(self):
        """Test that absolute defaults to True."""
        url = build_details_url("abc123")
        assert url.startswith("http://")


class TestAddDetailsUrlToSource:
    """Tests for add_details_url_to_source() helper function."""

    def test_add_url_to_source_absolute(self):
        """Test adding absolute URL to source dict."""
        source = {"doc_id": "abc123", "page": 5, "chunk_id": "abc123-chunk0042"}
        result = add_details_url_to_source(source, absolute=True)

        assert result is source  # Mutates in place
        assert (
            result["details_url"]
            == "http://localhost:3000/details/abc123?page=5&chunk=abc123-chunk0042"
        )

    def test_add_url_to_source_relative(self):
        """Test adding relative URL to source dict."""
        source = {"doc_id": "abc123", "page": 5, "chunk_id": "abc123-chunk0042"}
        result = add_details_url_to_source(source, absolute=False)

        assert result["details_url"] == "/details/abc123?page=5&chunk=abc123-chunk0042"

    def test_add_url_without_page(self):
        """Test adding URL when page is missing."""
        source = {"doc_id": "abc123", "chunk_id": "abc123-chunk0042"}
        result = add_details_url_to_source(source, absolute=False)

        assert result["details_url"] == "/details/abc123?chunk=abc123-chunk0042"

    def test_add_url_without_chunk(self):
        """Test adding URL when chunk_id is missing."""
        source = {"doc_id": "abc123", "page": 5}
        result = add_details_url_to_source(source, absolute=False)

        assert result["details_url"] == "/details/abc123?page=5"

    def test_add_url_minimal_source(self):
        """Test adding URL with only doc_id."""
        source = {"doc_id": "abc123"}
        result = add_details_url_to_source(source, absolute=False)

        assert result["details_url"] == "/details/abc123"

    def test_preserves_other_fields(self):
        """Test that other source fields are preserved."""
        source = {
            "doc_id": "abc123",
            "page": 5,
            "chunk_id": "abc123-chunk0042",
            "filename": "report.pdf",
            "relevance_score": 0.92,
        }
        result = add_details_url_to_source(source, absolute=False)

        assert result["filename"] == "report.pdf"
        assert result["relevance_score"] == 0.92
        assert "details_url" in result
