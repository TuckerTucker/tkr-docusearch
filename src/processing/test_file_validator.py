"""
Tests for file_validator module.

Tests cover:
- Normal cases for all validation functions
- Edge cases (no extension, multiple dots, case sensitivity)
- Environment variable override
- Error message content
"""

import os
from unittest.mock import patch

import pytest

from processing.file_validator import (
    get_supported_extensions,
    validate_file,
    validate_file_size,
    validate_file_type,
)


class TestGetSupportedExtensions:
    """Tests for get_supported_extensions()."""

    def test_default_extensions(self):
        """Test that default extensions are loaded correctly."""
        extensions = get_supported_extensions()

        # Check it's a set
        assert isinstance(extensions, set)

        # Check some expected extensions
        assert ".pdf" in extensions
        assert ".png" in extensions
        assert ".docx" in extensions
        assert ".csv" in extensions

        # Check all have dot prefix
        for ext in extensions:
            assert ext.startswith(".")

        # Check all are lowercase
        for ext in extensions:
            assert ext == ext.lower()

    def test_environment_override(self):
        """Test that environment variable overrides defaults."""
        with patch.dict(os.environ, {"SUPPORTED_FORMATS": "pdf,png,txt"}):
            extensions = get_supported_extensions()

            assert extensions == {".pdf", ".png", ".txt"}

    def test_environment_with_whitespace(self):
        """Test that whitespace in env var is handled correctly."""
        with patch.dict(os.environ, {"SUPPORTED_FORMATS": " pdf , png , txt "}):
            extensions = get_supported_extensions()

            assert extensions == {".pdf", ".png", ".txt"}

    def test_environment_case_insensitive(self):
        """Test that extensions are normalized to lowercase."""
        with patch.dict(os.environ, {"SUPPORTED_FORMATS": "PDF,PNG,TxT"}):
            extensions = get_supported_extensions()

            assert extensions == {".pdf", ".png", ".txt"}

    def test_empty_environment(self):
        """Test handling of empty environment variable."""
        with patch.dict(os.environ, {"SUPPORTED_FORMATS": ""}):
            extensions = get_supported_extensions()

            # Empty string splits to one empty element
            assert extensions == {"."} or len(extensions) == 0


class TestValidateFileType:
    """Tests for validate_file_type()."""

    def test_valid_pdf(self):
        """Test valid PDF file."""
        valid, msg = validate_file_type("document.pdf")

        assert valid is True
        assert msg == ""

    def test_valid_png(self):
        """Test valid PNG file."""
        valid, msg = validate_file_type("image.png")

        assert valid is True
        assert msg == ""

    def test_valid_docx(self):
        """Test valid DOCX file."""
        valid, msg = validate_file_type("report.docx")

        assert valid is True
        assert msg == ""

    def test_invalid_extension(self):
        """Test invalid file extension."""
        valid, msg = validate_file_type("malware.exe")

        assert valid is False
        assert "Unsupported file type" in msg
        assert ".exe" in msg

    def test_no_extension(self):
        """Test file with no extension."""
        valid, msg = validate_file_type("file_no_ext")

        assert valid is False
        assert "no extension" in msg.lower()

    def test_case_insensitive(self):
        """Test that extension checking is case-insensitive."""
        # Uppercase extension should still be valid
        valid, msg = validate_file_type("document.PDF")

        assert valid is True
        assert msg == ""

    def test_multiple_dots(self):
        """Test file with multiple dots in name."""
        valid, msg = validate_file_type("my.document.backup.pdf")

        assert valid is True
        assert msg == ""

    def test_absolute_path(self):
        """Test validation with absolute path."""
        valid, msg = validate_file_type("/path/to/document.pdf")

        assert valid is True
        assert msg == ""

    def test_relative_path(self):
        """Test validation with relative path."""
        valid, msg = validate_file_type("../docs/report.docx")

        assert valid is True
        assert msg == ""

    def test_path_with_spaces(self):
        """Test validation with spaces in path."""
        valid, msg = validate_file_type("/my documents/file name.pdf")

        assert valid is True
        assert msg == ""

    def test_hidden_file(self):
        """Test validation of hidden file (dot prefix)."""
        valid, msg = validate_file_type(".hidden.pdf")

        assert valid is True
        assert msg == ""

    def test_environment_override_validation(self):
        """Test that custom supported formats work correctly."""
        with patch.dict(os.environ, {"SUPPORTED_FORMATS": "pdf,txt"}):
            # PDF should be valid
            valid, msg = validate_file_type("doc.pdf")
            assert valid is True

            # PNG should be invalid (not in custom list)
            valid, msg = validate_file_type("image.png")
            assert valid is False
            assert "Unsupported file type" in msg


class TestValidateFileSize:
    """Tests for validate_file_size()."""

    def test_valid_small_file(self):
        """Test valid small file (1 KB)."""
        valid, msg = validate_file_size(1024)

        assert valid is True
        assert msg == ""

    def test_valid_medium_file(self):
        """Test valid medium file (50 MB)."""
        valid, msg = validate_file_size(50 * 1024 * 1024)

        assert valid is True
        assert msg == ""

    def test_valid_at_limit(self):
        """Test file exactly at size limit (100 MB)."""
        valid, msg = validate_file_size(100 * 1024 * 1024, max_mb=100)

        assert valid is True
        assert msg == ""

    def test_invalid_exceeds_limit(self):
        """Test file exceeding size limit."""
        valid, msg = validate_file_size(150 * 1024 * 1024, max_mb=100)

        assert valid is False
        assert "exceeds maximum" in msg
        assert "150" in msg
        assert "100 MB" in msg

    def test_invalid_just_over_limit(self):
        """Test file just over size limit."""
        valid, msg = validate_file_size(100 * 1024 * 1024 + 1, max_mb=100)

        assert valid is False
        assert "exceeds maximum" in msg

    def test_zero_size(self):
        """Test zero-size file (should be valid)."""
        valid, msg = validate_file_size(0)

        assert valid is True
        assert msg == ""

    def test_negative_size(self):
        """Test negative file size (should be invalid)."""
        valid, msg = validate_file_size(-1)

        assert valid is False
        assert "Invalid file size" in msg

    def test_custom_max_size(self):
        """Test custom maximum size limit."""
        # 10 MB file with 20 MB limit - valid
        valid, msg = validate_file_size(10 * 1024 * 1024, max_mb=20)
        assert valid is True

        # 30 MB file with 20 MB limit - invalid
        valid, msg = validate_file_size(30 * 1024 * 1024, max_mb=20)
        assert valid is False
        assert "20 MB" in msg

    def test_small_max_size(self):
        """Test small maximum size (1 MB)."""
        # 512 KB - valid
        valid, msg = validate_file_size(512 * 1024, max_mb=1)
        assert valid is True

        # 2 MB - invalid
        valid, msg = validate_file_size(2 * 1024 * 1024, max_mb=1)
        assert valid is False

    def test_large_file(self):
        """Test very large file size."""
        # 500 MB file
        valid, msg = validate_file_size(500 * 1024 * 1024, max_mb=100)

        assert valid is False
        assert "500" in msg


class TestValidateFile:
    """Tests for validate_file() - combined validation."""

    def test_valid_file(self):
        """Test completely valid file (type and size)."""
        valid, msg = validate_file("document.pdf", 10 * 1024 * 1024)

        assert valid is True
        assert msg == ""

    def test_invalid_type_valid_size(self):
        """Test invalid type but valid size."""
        valid, msg = validate_file("malware.exe", 1024)

        assert valid is False
        assert "Unsupported file type" in msg

    def test_valid_type_invalid_size(self):
        """Test valid type but invalid size."""
        valid, msg = validate_file("document.pdf", 150 * 1024 * 1024, max_mb=100)

        assert valid is False
        assert "exceeds maximum" in msg

    def test_invalid_type_and_size(self):
        """Test both type and size invalid (should fail on type first)."""
        valid, msg = validate_file("malware.exe", 150 * 1024 * 1024, max_mb=100)

        assert valid is False
        # Should fail on type check first
        assert "Unsupported file type" in msg

    def test_no_extension_small_size(self):
        """Test file with no extension but valid size."""
        valid, msg = validate_file("file_no_ext", 1024)

        assert valid is False
        assert "no extension" in msg.lower()

    def test_custom_max_size(self):
        """Test combined validation with custom max size."""
        # Valid with 50 MB limit
        valid, msg = validate_file("document.pdf", 30 * 1024 * 1024, max_mb=50)
        assert valid is True

        # Invalid with 20 MB limit
        valid, msg = validate_file("document.pdf", 30 * 1024 * 1024, max_mb=20)
        assert valid is False
        assert "exceeds maximum" in msg

    def test_edge_case_zero_size(self):
        """Test valid file type with zero size."""
        valid, msg = validate_file("document.pdf", 0)

        assert valid is True
        assert msg == ""

    def test_multiple_validations(self):
        """Test that all supported file types work with size validation."""
        test_files = [
            "doc.pdf",
            "sheet.xlsx",
            "presentation.pptx",
            "image.png",
            "image.jpg",
            "data.csv",
            "page.html",
            "audio.mp3",
        ]

        for file_path in test_files:
            valid, msg = validate_file(file_path, 10 * 1024 * 1024)
            assert valid is True, f"Failed for {file_path}: {msg}"

    def test_combined_with_environment_override(self):
        """Test combined validation with custom supported formats."""
        with patch.dict(os.environ, {"SUPPORTED_FORMATS": "pdf,txt"}):
            # PDF with valid size - valid
            valid, msg = validate_file("doc.pdf", 1024)
            assert valid is True

            # PNG with valid size - invalid (type not supported)
            valid, msg = validate_file("image.png", 1024)
            assert valid is False
            assert "Unsupported file type" in msg

            # PDF with invalid size - invalid (size exceeds)
            valid, msg = validate_file("doc.pdf", 150 * 1024 * 1024, max_mb=100)
            assert valid is False
            assert "exceeds maximum" in msg


class TestErrorMessages:
    """Tests to verify error message quality."""

    def test_unsupported_type_message_includes_supported(self):
        """Test that unsupported type error includes list of supported types."""
        valid, msg = validate_file_type("file.exe")

        assert valid is False
        assert "Supported:" in msg
        assert ".pdf" in msg

    def test_size_error_includes_actual_and_max(self):
        """Test that size error includes both actual and maximum size."""
        valid, msg = validate_file_size(150 * 1024 * 1024, max_mb=100)

        assert valid is False
        assert "150" in msg  # Actual size
        assert "100 MB" in msg  # Maximum size

    def test_no_extension_message_includes_filename(self):
        """Test that no extension error includes the filename."""
        valid, msg = validate_file_type("my_file")

        assert valid is False
        assert "my_file" in msg


class TestIntegration:
    """Integration tests for realistic scenarios."""

    def test_typical_document_upload(self):
        """Test typical document upload scenario."""
        # PDF document, 5 MB
        valid, msg = validate_file("report_2024.pdf", 5 * 1024 * 1024)
        assert valid is True

        # DOCX document, 2 MB
        valid, msg = validate_file("proposal.docx", 2 * 1024 * 1024)
        assert valid is True

        # PNG image, 3 MB
        valid, msg = validate_file("screenshot.png", 3 * 1024 * 1024)
        assert valid is True

    def test_rejection_scenarios(self):
        """Test common rejection scenarios."""
        # Executable file
        valid, msg = validate_file("virus.exe", 1024)
        assert valid is False

        # Too large file
        valid, msg = validate_file("huge.pdf", 200 * 1024 * 1024)
        assert valid is False

        # No extension
        valid, msg = validate_file("README", 1024)
        assert valid is False

    def test_case_variations(self):
        """Test that case variations work correctly."""
        test_cases = [
            "document.PDF",
            "document.Pdf",
            "document.pdf",
            "IMAGE.PNG",
            "Image.Png",
            "image.png",
        ]

        for file_path in test_cases:
            valid, msg = validate_file(file_path, 1024)
            assert valid is True, f"Failed for {file_path}: {msg}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=file_validator", "--cov-report=term-missing"])
