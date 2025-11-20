"""
Tests for PDF dimension repair functionality in DoclingParser.

These tests verify that DoclingParser correctly detects and repairs PDFs with
inherited page dimensions, following a retry-on-failure strategy:
1. Try Docling conversion first
2. If "page-dimensions" error occurs, force repair and retry
3. Only repair PDFs that actually fail
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from io import BytesIO

from tkr_docusearch.processing.docling_parser import DoclingParser, ParsingError


class TestPDFRepairRetryOnFailure:
    """Tests for retry-on-failure PDF repair strategy."""

    @patch("src.processing.parsers.SymlinkHelper.audio_file_symlink")
    @patch("src.processing.parsers.FormatOptionsBuilder")
    @patch("tkr_docusearch.processing.docling_parser.DocumentConverter")
    @patch("tkr_docusearch.processing.docling_parser.ensure_absolute")
    @patch("tkr_docusearch.processing.docling_parser.log_path_info")
    @patch("tkr_docusearch.processing.docling_parser.docling_to_pages")
    def test_pdf_dimension_error_triggers_repair_and_retry(
        self,
        mock_to_pages,
        mock_log_path,
        mock_ensure_abs,
        mock_converter_class,
        mock_format_builder,
        mock_symlink,
    ):
        """Test that PDF dimension errors trigger repair and retry."""
        # Setup mocks
        test_pdf_path = "/uploads/test.pdf"
        repaired_pdf_path = "/tmp/repaired_docling_12345.pdf"
        mock_ensure_abs.return_value = test_pdf_path

        # First conversion attempt fails with dimension error
        mock_converter_fail = Mock()
        mock_converter_fail.convert.side_effect = Exception(
            "Docling parsing failed: could not find the page-dimensions"
        )

        # Second conversion attempt succeeds
        mock_converter_success = Mock()
        mock_result = Mock()
        mock_doc = Mock()
        mock_doc.name = "Test Document"
        mock_doc.pages = {}
        mock_doc.export_to_text.return_value = "Test content"
        mock_doc.export_to_markdown.return_value = "# Test"
        mock_result.document = mock_doc
        mock_result.pages = []
        mock_converter_success.convert.return_value = mock_result

        # Mock DocumentConverter to return different instances
        mock_converter_class.side_effect = [mock_converter_fail, mock_converter_success]

        # Mock the symlink context manager
        mock_symlink.return_value.__enter__ = Mock()
        mock_symlink.return_value.__exit__ = Mock()

        # Mock to_pages conversion
        mock_to_pages.return_value = [Mock(page_number=1)]

        # Create parser
        parser = DoclingParser()

        # Mock the _repair_pdf_dimensions method to return repaired path
        with patch.object(parser, "_repair_pdf_dimensions", return_value=repaired_pdf_path):
            with patch.object(Path, "stat") as mock_stat:
                mock_stat.return_value.st_size = 1024

                # Parse document - should trigger repair
                pages, metadata, doc = parser._parse_with_docling(test_pdf_path)

        # Verify repair was called with original PDF path
        parser._repair_pdf_dimensions.assert_called_once_with(test_pdf_path)

        # Verify retry counter was incremented
        assert parser._pdfs_repaired == 1

        # Verify second conversion was attempted with repaired path
        # The mock_symlink should have been called twice (original + repaired)
        assert mock_symlink.call_count == 2

    @patch("src.processing.parsers.SymlinkHelper.audio_file_symlink")
    @patch("src.processing.parsers.FormatOptionsBuilder")
    @patch("tkr_docusearch.processing.docling_parser.DocumentConverter")
    @patch("tkr_docusearch.processing.docling_parser.ensure_absolute")
    @patch("tkr_docusearch.processing.docling_parser.log_path_info")
    @patch("tkr_docusearch.processing.docling_parser.docling_to_pages")
    def test_non_dimension_errors_not_caught(
        self,
        mock_to_pages,
        mock_log_path,
        mock_ensure_abs,
        mock_converter_class,
        mock_format_builder,
        mock_symlink,
    ):
        """Test that non-dimension errors are re-raised without repair."""
        # Setup mocks
        test_pdf_path = "/uploads/test.pdf"
        mock_ensure_abs.return_value = test_pdf_path

        # Conversion fails with different error (not dimension-related)
        mock_converter = Mock()
        mock_converter.convert.side_effect = Exception("File corrupted: invalid PDF structure")
        mock_converter_class.return_value = mock_converter

        # Mock the symlink context manager
        mock_symlink.return_value.__enter__ = Mock()
        mock_symlink.return_value.__exit__ = Mock()

        # Create parser
        parser = DoclingParser()

        # Mock the _repair_pdf_dimensions method
        with patch.object(parser, "_repair_pdf_dimensions") as mock_repair:
            with patch.object(Path, "stat") as mock_stat:
                mock_stat.return_value.st_size = 1024

                # Parse document - should raise the original error
                with pytest.raises(Exception) as exc_info:
                    parser._parse_with_docling(test_pdf_path)

        # Verify error message is correct
        assert "File corrupted" in str(exc_info.value)

        # Verify repair was NOT called
        mock_repair.assert_not_called()

        # Verify repair counter not incremented
        assert parser._pdfs_repaired == 0

    @patch("src.processing.parsers.SymlinkHelper.audio_file_symlink")
    @patch("src.processing.parsers.FormatOptionsBuilder")
    @patch("tkr_docusearch.processing.docling_parser.DocumentConverter")
    @patch("tkr_docusearch.processing.docling_parser.ensure_absolute")
    @patch("tkr_docusearch.processing.docling_parser.log_path_info")
    @patch("tkr_docusearch.processing.docling_parser.docling_to_pages")
    def test_successful_pdf_no_repair_needed(
        self,
        mock_to_pages,
        mock_log_path,
        mock_ensure_abs,
        mock_converter_class,
        mock_format_builder,
        mock_symlink,
    ):
        """Test that successful PDFs don't trigger repair."""
        # Setup mocks
        test_pdf_path = "/uploads/test.pdf"
        mock_ensure_abs.return_value = test_pdf_path

        # Conversion succeeds on first attempt
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

        # Mock the symlink context manager
        mock_symlink.return_value.__enter__ = Mock()
        mock_symlink.return_value.__exit__ = Mock()

        # Mock to_pages conversion
        mock_to_pages.return_value = [Mock(page_number=1)]

        # Create parser
        parser = DoclingParser()

        # Mock the _repair_pdf_dimensions method
        with patch.object(parser, "_repair_pdf_dimensions") as mock_repair:
            with patch.object(Path, "stat") as mock_stat:
                mock_stat.return_value.st_size = 1024

                # Parse document - should succeed without repair
                pages, metadata, doc = parser._parse_with_docling(test_pdf_path)

        # Verify repair was NOT called
        mock_repair.assert_not_called()

        # Verify repair counter not incremented
        assert parser._pdfs_repaired == 0

        # Verify document was processed successfully
        assert doc is not None
        assert len(pages) == 1


class TestPDFDimensionDetection:
    """Tests for PDF dimension detection."""

    def test_explicit_dimensions_detected(self):
        """Test detection of explicit MediaBox on page."""
        # Create a minimal PDF with explicit MediaBox
        from pypdf import PdfWriter

        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)

        # Write to temp file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            writer.write(f)
            temp_path = f.name

        try:
            # Create parser and test
            parser = DoclingParser()
            has_explicit = parser._pdf_has_explicit_dimensions(temp_path)

            # Should detect explicit dimensions
            assert has_explicit is True
        finally:
            # Clean up
            Path(temp_path).unlink()

    def test_no_dimensions_fallback(self):
        """Test that errors during dimension check return True (skip repair)."""
        parser = DoclingParser()

        # Test with non-existent file
        has_explicit = parser._pdf_has_explicit_dimensions("/nonexistent/file.pdf")

        # Should return True to skip repair on error
        assert has_explicit is True


class TestPDFDimensionRepair:
    """Tests for PDF dimension repair functionality."""

    def test_repair_creates_temp_file(self):
        """Test that repair creates a temporary file with explicit dimensions."""
        # Create a minimal PDF
        from pypdf import PdfWriter

        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)

        # Write to temp file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            writer.write(f)
            original_path = f.name

        try:
            # Create parser and repair
            parser = DoclingParser()
            repaired_path = parser._repair_pdf_dimensions(original_path)

            # Verify repaired file exists
            assert Path(repaired_path).exists()

            # Verify it's tracked for cleanup
            assert repaired_path in parser._temp_repair_files

            # Verify it's a different file
            assert repaired_path != original_path

            # Verify it starts with expected prefix
            assert "repaired_docling_" in repaired_path

            # Clean up repaired file
            parser._cleanup_temp_repairs()

            # Verify cleanup worked
            assert not Path(repaired_path).exists()
            assert len(parser._temp_repair_files) == 0

        finally:
            # Clean up original
            Path(original_path).unlink()

    def test_repair_increments_counter(self):
        """Test that successful repair increments counter."""
        # Create a minimal PDF
        from pypdf import PdfWriter

        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)

        # Write to temp file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            writer.write(f)
            temp_path = f.name

        try:
            # Create parser
            parser = DoclingParser()

            # Initial counter should be 0
            assert parser._pdfs_repaired == 0

            # Repair (note: counter is incremented in the retry logic, not in _repair_pdf_dimensions)
            repaired_path = parser._repair_pdf_dimensions(temp_path)

            # Counter should still be 0 (incremented in caller)
            assert parser._pdfs_repaired == 0

            # Clean up
            parser._cleanup_temp_repairs()

        finally:
            # Clean up
            Path(temp_path).unlink()

    def test_repair_handles_invalid_pdf(self):
        """Test that repair fails gracefully on invalid PDF."""
        # Create an invalid PDF file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False, mode="w") as f:
            f.write("This is not a valid PDF file")
            invalid_path = f.name

        try:
            # Create parser
            parser = DoclingParser()

            # Repair should raise ParsingError
            with pytest.raises(ParsingError) as exc_info:
                parser._repair_pdf_dimensions(invalid_path)

            # Verify error message
            assert "PDF dimension repair failed" in str(exc_info.value)

        finally:
            # Clean up
            Path(invalid_path).unlink()


class TestRepairMetrics:
    """Tests for repair metrics tracking."""

    def test_metrics_initial_state(self):
        """Test that metrics start at zero."""
        parser = DoclingParser()
        metrics = parser.get_repair_metrics()

        assert metrics["pdfs_processed"] == 0
        assert metrics["pdfs_repaired"] == 0
        assert metrics["repairs_failed"] == 0
        assert metrics["repair_rate"] == 0.0

    def test_metrics_after_repair(self):
        """Test that metrics are updated correctly after repair."""
        parser = DoclingParser()

        # Manually increment counters (as would happen during processing)
        parser._pdfs_processed = 10
        parser._pdfs_repaired = 3
        parser._repairs_failed = 1

        metrics = parser.get_repair_metrics()

        assert metrics["pdfs_processed"] == 10
        assert metrics["pdfs_repaired"] == 3
        assert metrics["repairs_failed"] == 1
        assert metrics["repair_rate"] == 0.3  # 3/10

    def test_repair_rate_calculation(self):
        """Test repair rate is calculated correctly."""
        parser = DoclingParser()

        # Test 50% repair rate
        parser._pdfs_processed = 4
        parser._pdfs_repaired = 2
        metrics = parser.get_repair_metrics()
        assert metrics["repair_rate"] == 0.5

        # Test 100% repair rate
        parser._pdfs_processed = 5
        parser._pdfs_repaired = 5
        metrics = parser.get_repair_metrics()
        assert metrics["repair_rate"] == 1.0

        # Test 0% repair rate
        parser._pdfs_processed = 10
        parser._pdfs_repaired = 0
        metrics = parser.get_repair_metrics()
        assert metrics["repair_rate"] == 0.0


class TestTempFileCleanup:
    """Tests for temporary repair file cleanup."""

    def test_cleanup_removes_all_temp_files(self):
        """Test that cleanup removes all tracked temp files."""
        from pypdf import PdfWriter

        parser = DoclingParser()

        # Create multiple temp repair files
        temp_files = []
        for i in range(3):
            writer = PdfWriter()
            writer.add_blank_page(width=612, height=792)

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                writer.write(f)
                temp_path = f.name
                temp_files.append(temp_path)
                parser._temp_repair_files.append(temp_path)

        # Verify all files exist
        for temp_path in temp_files:
            assert Path(temp_path).exists()

        # Clean up
        parser._cleanup_temp_repairs()

        # Verify all files removed
        for temp_path in temp_files:
            assert not Path(temp_path).exists()

        # Verify tracking list cleared
        assert len(parser._temp_repair_files) == 0

    def test_cleanup_handles_missing_files(self):
        """Test that cleanup handles files that don't exist."""
        parser = DoclingParser()

        # Add non-existent file to tracking list
        parser._temp_repair_files.append("/nonexistent/file.pdf")

        # Cleanup should not raise error
        parser._cleanup_temp_repairs()

        # Tracking list should be cleared
        assert len(parser._temp_repair_files) == 0

    def test_cleanup_safe_to_call_multiple_times(self):
        """Test that cleanup can be called multiple times safely."""
        parser = DoclingParser()

        # First cleanup (empty list)
        parser._cleanup_temp_repairs()
        assert len(parser._temp_repair_files) == 0

        # Second cleanup (should not error)
        parser._cleanup_temp_repairs()
        assert len(parser._temp_repair_files) == 0


class TestIntegrationScenarios:
    """End-to-end integration tests for PDF repair."""

    @patch("src.processing.parsers.SymlinkHelper.audio_file_symlink")
    @patch("src.processing.parsers.FormatOptionsBuilder")
    @patch("tkr_docusearch.processing.docling_parser.DocumentConverter")
    @patch("tkr_docusearch.processing.docling_parser.ensure_absolute")
    @patch("tkr_docusearch.processing.docling_parser.log_path_info")
    @patch("tkr_docusearch.processing.docling_parser.docling_to_pages")
    def test_multiple_pdfs_some_need_repair(
        self,
        mock_to_pages,
        mock_log_path,
        mock_ensure_abs,
        mock_converter_class,
        mock_format_builder,
        mock_symlink,
    ):
        """Test processing multiple PDFs where some need repair."""
        from pypdf import PdfWriter

        # Create parser
        parser = DoclingParser()

        # Mock common functionality
        mock_symlink.return_value.__enter__ = Mock()
        mock_symlink.return_value.__exit__ = Mock()
        mock_to_pages.return_value = [Mock(page_number=1)]

        # PDF 1: Success (no repair needed)
        pdf1_path = "/uploads/good.pdf"
        mock_ensure_abs.return_value = pdf1_path

        mock_converter_ok = Mock()
        mock_result_ok = Mock()
        mock_doc_ok = Mock()
        mock_doc_ok.name = "Good Document"
        mock_doc_ok.pages = {}
        mock_doc_ok.export_to_text.return_value = "Test"
        mock_doc_ok.export_to_markdown.return_value = "# Test"
        mock_result_ok.document = mock_doc_ok
        mock_result_ok.pages = []
        mock_converter_ok.convert.return_value = mock_result_ok

        # Create real temp PDF for repair test
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            writer.write(f)
            temp_pdf = f.name

        try:
            # Process first PDF (success)
            mock_converter_class.return_value = mock_converter_ok
            with patch.object(Path, "stat") as mock_stat:
                mock_stat.return_value.st_size = 1024
                pages1, metadata1, doc1 = parser._parse_with_docling(pdf1_path)

            # PDF 2: Needs repair
            pdf2_path = temp_pdf
            mock_ensure_abs.return_value = pdf2_path

            # First attempt fails
            mock_converter_fail = Mock()
            mock_converter_fail.convert.side_effect = Exception("page-dimensions error")

            # Second attempt succeeds
            mock_converter_retry = Mock()
            mock_result_retry = Mock()
            mock_doc_retry = Mock()
            mock_doc_retry.name = "Repaired Document"
            mock_doc_retry.pages = {}
            mock_doc_retry.export_to_text.return_value = "Test"
            mock_doc_retry.export_to_markdown.return_value = "# Test"
            mock_result_retry.document = mock_doc_retry
            mock_result_retry.pages = []
            mock_converter_retry.convert.return_value = mock_result_retry

            # Mock DocumentConverter to return fail then success
            mock_converter_class.side_effect = [mock_converter_fail, mock_converter_retry]

            # Process second PDF (needs repair)
            with patch.object(Path, "stat") as mock_stat:
                mock_stat.return_value.st_size = 1024
                pages2, metadata2, doc2 = parser._parse_with_docling(pdf2_path)

            # Verify metrics
            metrics = parser.get_repair_metrics()
            assert metrics["pdfs_repaired"] == 1  # Only second PDF was repaired

            # Verify cleanup
            temp_files_count = len(parser._temp_repair_files)
            parser._cleanup_temp_repairs()
            # All temp files should be removed
            for temp_file in parser._temp_repair_files:
                assert not Path(temp_file).exists()

        finally:
            # Clean up test PDF
            Path(temp_pdf).unlink(missing_ok=True)
