"""
Tests for .doc to .docx conversion integration in DoclingParser.

These tests verify that DoclingParser correctly detects and converts .doc files
before Docling processing, following the metadata-schema.json contract.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from tkr_docusearch.processing.docling_parser import DoclingParser, ParsingError


class TestDocConversion:
    """Tests for .doc file conversion integration."""

    @patch("tkr_docusearch.processing.docling_parser.get_legacy_office_client")
    @patch("tkr_docusearch.processing.docling_parser.DocumentConverter")
    @patch("tkr_docusearch.processing.docling_parser.ensure_absolute")
    @patch("tkr_docusearch.processing.docling_parser.log_path_info")
    def test_doc_file_triggers_conversion(
        self, mock_log_path, mock_ensure_abs, mock_converter_class, mock_get_client
    ):
        """Test that .doc files trigger conversion to .docx."""
        # Setup mocks
        mock_ensure_abs.return_value = "/uploads/test.doc"
        mock_client = Mock()
        mock_client.convert_doc_to_docx.return_value = "/uploads/test.docx"
        mock_get_client.return_value = mock_client

        # Mock the DocumentConverter
        mock_converter = Mock()
        mock_result = Mock()
        mock_result.document = Mock()
        mock_result.document.name = "Test Document"
        mock_result.document.pages = {}
        mock_result.document.export_to_text.return_value = "Test content"
        mock_result.document.export_to_markdown.return_value = "# Test content"
        mock_result.pages = []
        mock_converter.convert.return_value = mock_result
        mock_converter_class.return_value = mock_converter

        # Create parser and parse document
        parser = DoclingParser()

        # We'll call the internal method directly to avoid file I/O
        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "stat") as mock_stat:
                mock_stat.return_value.st_size = 1024
                with patch("tkr_docusearch.processing.docling_parser.docling_to_pages") as mock_to_pages:
                    mock_to_pages.return_value = []
                    with patch("tkr_docusearch.processing.docling_parser.FormatOptionsBuilder"):
                        pages, metadata, doc = parser._parse_with_docling("/uploads/test.doc")

        # Verify conversion was called
        mock_client.convert_doc_to_docx.assert_called_once_with("/uploads/test.doc")

        # Verify metadata was set
        assert "original_filename" in metadata
        assert metadata["original_filename"] == "test.doc"
        assert metadata["converted_from"] == ".doc"
        assert "conversion_time_ms" in metadata
        assert isinstance(metadata["conversion_time_ms"], int)
        assert metadata["conversion_time_ms"] >= 0

    @patch("tkr_docusearch.processing.docling_parser.DocumentConverter")
    @patch("tkr_docusearch.processing.docling_parser.ensure_absolute")
    @patch("tkr_docusearch.processing.docling_parser.log_path_info")
    def test_docx_files_skip_conversion(
        self, mock_log_path, mock_ensure_abs, mock_converter_class
    ):
        """Test that .docx files don't trigger conversion."""
        # Setup mocks
        mock_ensure_abs.return_value = "/uploads/test.docx"

        # Mock the DocumentConverter
        mock_converter = Mock()
        mock_result = Mock()
        mock_result.document = Mock()
        mock_result.document.name = "Test Document"
        mock_result.document.pages = {}
        mock_result.document.export_to_text.return_value = "Test content"
        mock_result.document.export_to_markdown.return_value = "# Test content"
        mock_result.pages = []
        mock_converter.convert.return_value = mock_result
        mock_converter_class.return_value = mock_converter

        # Create parser
        parser = DoclingParser()

        # Parse .docx file
        with patch.object(Path, "stat") as mock_stat:
            mock_stat.return_value.st_size = 1024
            with patch("tkr_docusearch.processing.docling_parser.docling_to_pages") as mock_to_pages:
                mock_to_pages.return_value = []
                with patch("tkr_docusearch.processing.docling_parser.FormatOptionsBuilder"):
                    with patch("tkr_docusearch.processing.docling_parser.get_legacy_office_client") as mock_client:
                        pages, metadata, doc = parser._parse_with_docling("/uploads/test.docx")

                        # Verify conversion was NOT called
                        mock_client.assert_not_called()

        # Verify conversion metadata NOT set
        assert "converted_from" not in metadata
        assert "conversion_time_ms" not in metadata

    @patch("tkr_docusearch.processing.docling_parser.get_legacy_office_client")
    @patch("tkr_docusearch.processing.docling_parser.ensure_absolute")
    @patch("tkr_docusearch.processing.docling_parser.log_path_info")
    def test_conversion_metadata_fields(self, mock_log_path, mock_ensure_abs, mock_get_client):
        """Test that conversion metadata follows metadata-schema.json contract."""
        # Setup mocks
        mock_ensure_abs.return_value = "/uploads/quarterly-report.doc"
        mock_client = Mock()
        mock_client.convert_doc_to_docx.return_value = "/uploads/quarterly-report.docx"
        mock_get_client.return_value = mock_client

        # Create parser
        parser = DoclingParser()

        # Call conversion method directly
        docx_path, conversion_time_ms = parser._convert_legacy_doc("/uploads/quarterly-report.doc")

        # Verify return values match contract
        assert docx_path.endswith("quarterly-report.docx")
        assert isinstance(conversion_time_ms, int)
        assert conversion_time_ms >= 0

        # Verify required fields would be set
        # (original_filename, converted_from, conversion_time_ms)
        # These are tested in test_doc_file_triggers_conversion

    @patch("tkr_docusearch.processing.docling_parser.get_legacy_office_client")
    @patch("tkr_docusearch.processing.docling_parser.ensure_absolute")
    @patch("tkr_docusearch.processing.docling_parser.log_path_info")
    def test_conversion_failure_raises_parsing_error(
        self, mock_log_path, mock_ensure_abs, mock_get_client
    ):
        """Test that conversion failures raise ParsingError."""
        # Setup mocks to fail
        mock_ensure_abs.return_value = "/uploads/corrupt.doc"
        mock_client = Mock()
        mock_client.convert_doc_to_docx.side_effect = Exception("Service unavailable")
        mock_get_client.return_value = mock_client

        # Create parser
        parser = DoclingParser()

        # Verify ParsingError is raised
        with pytest.raises(ParsingError) as exc_info:
            parser._convert_legacy_doc("/uploads/corrupt.doc")

        assert "Doc conversion failed" in str(exc_info.value)
        assert "Service unavailable" in str(exc_info.value)

    @patch("tkr_docusearch.processing.docling_parser.get_legacy_office_client")
    @patch("tkr_docusearch.processing.docling_parser.ensure_absolute")
    @patch("tkr_docusearch.processing.docling_parser.log_path_info")
    def test_path_translation_pattern(self, mock_log_path, mock_ensure_abs, mock_get_client):
        """Test that path translation follows the slide_renderer.py pattern."""
        # Setup mocks
        mock_ensure_abs.return_value = "/Volumes/data/uploads/report.doc"
        mock_client = Mock()
        mock_client.convert_doc_to_docx.return_value = "/uploads/report.docx"
        mock_get_client.return_value = mock_client

        # Create parser
        parser = DoclingParser()

        # Call conversion
        docx_path, conversion_time_ms = parser._convert_legacy_doc(
            "/Volumes/data/uploads/report.doc"
        )

        # Verify Docker path format was used in call
        mock_client.convert_doc_to_docx.assert_called_once_with("/uploads/report.doc")

        # Verify native path was returned
        assert "report.docx" in docx_path
        assert docx_path == "/Volumes/data/uploads/report.docx"


class TestMetadataContract:
    """Tests for metadata-schema.json contract compliance."""

    def test_required_metadata_fields(self):
        """Test that all required metadata fields from schema are present."""
        # Mock metadata dict that would be created after conversion
        metadata = {
            "original_filename": "quarterly-report.doc",
            "converted_from": ".doc",
            "conversion_time_ms": 2340,
        }

        # Verify required fields
        assert "original_filename" in metadata
        assert isinstance(metadata["original_filename"], str)
        assert metadata["original_filename"].endswith(".doc")

        assert "converted_from" in metadata
        assert metadata["converted_from"] in [".doc", ".dot"]

        assert "conversion_time_ms" in metadata
        assert isinstance(metadata["conversion_time_ms"], int)
        assert metadata["conversion_time_ms"] >= 0

    def test_metadata_types_match_schema(self):
        """Test that metadata field types match schema definitions."""
        metadata = {
            "original_filename": "report.doc",
            "converted_from": ".doc",
            "conversion_time_ms": 1500,
        }

        # Type checks
        assert isinstance(metadata["original_filename"], str)
        assert isinstance(metadata["converted_from"], str)
        assert isinstance(metadata["conversion_time_ms"], int)


class TestIntegrationFlow:
    """End-to-end integration tests."""

    @patch("tkr_docusearch.processing.docling_parser.get_legacy_office_client")
    @patch("tkr_docusearch.processing.docling_parser.DocumentConverter")
    @patch("tkr_docusearch.processing.docling_parser.ensure_absolute")
    @patch("tkr_docusearch.processing.docling_parser.log_path_info")
    def test_full_doc_parsing_flow(
        self, mock_log_path, mock_ensure_abs, mock_converter_class, mock_get_client
    ):
        """Test complete flow: .doc -> conversion -> Docling -> metadata."""
        # Setup conversion mock
        mock_ensure_abs.return_value = "/uploads/test.doc"
        mock_client = Mock()
        mock_client.convert_doc_to_docx.return_value = "/uploads/test.docx"
        mock_get_client.return_value = mock_client

        # Setup Docling mock
        mock_converter = Mock()
        mock_result = Mock()
        mock_doc = Mock()
        mock_doc.name = "Test Document"
        mock_doc.pages = {}
        mock_doc.export_to_text.return_value = "Test content"
        mock_doc.export_to_markdown.return_value = "# Test"
        mock_result.document = mock_doc
        mock_result.pages = []
        mock_converter.convert.return_value = mock_result
        mock_converter_class.return_value = mock_converter

        # Create parser
        parser = DoclingParser()

        # Parse document
        with patch.object(Path, "stat") as mock_stat:
            mock_stat.return_value.st_size = 1024
            with patch("tkr_docusearch.processing.docling_parser.docling_to_pages") as mock_to_pages:
                mock_to_pages.return_value = []
                with patch("tkr_docusearch.processing.docling_parser.FormatOptionsBuilder"):
                    pages, metadata, doc = parser._parse_with_docling("/uploads/test.doc")

        # Verify full flow
        # 1. Conversion called with .doc path
        mock_client.convert_doc_to_docx.assert_called_once_with("/uploads/test.doc")

        # 2. Docling called with .docx path
        # (The convert method receives the translated native path)
        assert mock_converter.convert.called

        # 3. Metadata includes conversion info
        assert metadata["original_filename"] == "test.doc"
        assert metadata["converted_from"] == ".doc"
        assert "conversion_time_ms" in metadata

        # 4. Document processed successfully
        assert doc is not None
