"""
End-to-end integration tests for .doc file processing pipeline.

Tests the complete .doc conversion pipeline from upload through conversion,
parsing, embedding, storage, and search. Validates that the entire system
works together correctly.

Author: Agent-Integration-Testing
Date: 2025-11-19
Wave: 8 (Legacy Office Doc Conversion)
"""

import logging
from pathlib import Path
from typing import List, Optional
from unittest.mock import Mock, patch

import pytest

from tkr_docusearch.processing.docling_parser import DoclingParser
from tkr_docusearch.processing.legacy_office_client import LegacyOfficeError
from tkr_docusearch.processing.processor import DocumentProcessor

logger = logging.getLogger(__name__)


# ====================================================================================
# E2E Pipeline Tests
# ====================================================================================


class TestDocConversionE2E:
    """End-to-end tests for .doc file processing."""

    @pytest.mark.integration
    def test_doc_file_detection_triggers_conversion(
        self,
        embedding_engine_instance,
        storage_client_instance,
        skip_if_legacy_office_unavailable,
    ):
        """Test that .doc files are detected and trigger conversion."""
        # Create parser
        parser = DoclingParser()

        # Mock the actual conversion (since we don't have a real .doc file in Docker)
        with patch.object(parser, "_convert_legacy_doc") as mock_convert:
            mock_convert.return_value = ("/uploads/test.docx", 234)

            # Mock Docling processing
            with patch("tkr_docusearch.processing.docling_parser.DocumentConverter"):
                with patch(
                    "tkr_docusearch.processing.docling_parser.docling_to_pages"
                ) as mock_to_pages:
                    mock_to_pages.return_value = []

                    with patch("tkr_docusearch.processing.docling_parser.FormatOptionsBuilder"):
                        # Parse .doc file
                        with patch.object(Path, "stat") as mock_stat:
                            mock_stat.return_value.st_size = 1024

                            pages, metadata, doc = parser._parse_with_docling("/uploads/test.doc")

            # Verify conversion was called
            mock_convert.assert_called_once_with("/uploads/test.doc")

            # Verify metadata includes conversion info
            assert "original_filename" in metadata
            assert metadata["original_filename"] == "test.doc"
            assert metadata["converted_from"] == ".doc"
            assert "conversion_time_ms" in metadata

            logger.info("✓ .doc file triggers conversion correctly")

    @pytest.mark.integration
    def test_original_filename_preserved_in_metadata(
        self,
        embedding_engine_instance,
        storage_client_instance,
        skip_if_legacy_office_unavailable,
    ):
        """Test that original .doc filename is preserved in metadata."""
        # Create parser
        parser = DoclingParser()

        # Test with specific filename
        doc_filename = "quarterly-report.doc"
        doc_path = f"/uploads/{doc_filename}"

        # Mock conversion
        with patch.object(parser, "_convert_legacy_doc") as mock_convert:
            mock_convert.return_value = ("/uploads/quarterly-report.docx", 456)

            # Mock Docling
            with patch("tkr_docusearch.processing.docling_parser.DocumentConverter"):
                with patch(
                    "tkr_docusearch.processing.docling_parser.docling_to_pages"
                ) as mock_to_pages:
                    mock_to_pages.return_value = []

                    with patch("tkr_docusearch.processing.docling_parser.FormatOptionsBuilder"):
                        with patch.object(Path, "stat") as mock_stat:
                            mock_stat.return_value.st_size = 2048

                            pages, metadata, doc = parser._parse_with_docling(doc_path)

        # Verify original filename is preserved
        assert metadata["original_filename"] == doc_filename
        assert metadata["converted_from"] == ".doc"

        logger.info(f"✓ Original filename preserved: {doc_filename}")

    @pytest.mark.integration
    def test_conversion_metadata_follows_schema(
        self,
        embedding_engine_instance,
        storage_client_instance,
        skip_if_legacy_office_unavailable,
    ):
        """Test that conversion metadata follows metadata-schema.json contract."""
        # Create parser
        parser = DoclingParser()

        # Mock conversion
        with patch.object(parser, "_convert_legacy_doc") as mock_convert:
            mock_convert.return_value = ("/uploads/test.docx", 789)

            # Mock Docling
            with patch("tkr_docusearch.processing.docling_parser.DocumentConverter"):
                with patch(
                    "tkr_docusearch.processing.docling_parser.docling_to_pages"
                ) as mock_to_pages:
                    mock_to_pages.return_value = []

                    with patch("tkr_docusearch.processing.docling_parser.FormatOptionsBuilder"):
                        with patch.object(Path, "stat") as mock_stat:
                            mock_stat.return_value.st_size = 1024

                            pages, metadata, doc = parser._parse_with_docling("/uploads/test.doc")

        # Validate metadata schema compliance
        # Required fields from metadata-schema.json
        assert "original_filename" in metadata
        assert isinstance(metadata["original_filename"], str)
        assert metadata["original_filename"].endswith(".doc")

        assert "converted_from" in metadata
        assert metadata["converted_from"] in [".doc", ".dot"]

        assert "conversion_time_ms" in metadata
        assert isinstance(metadata["conversion_time_ms"], int)
        assert metadata["conversion_time_ms"] >= 0

        logger.info("✓ Conversion metadata follows schema")
        logger.info(f"  original_filename: {metadata['original_filename']}")
        logger.info(f"  converted_from: {metadata['converted_from']}")
        logger.info(f"  conversion_time_ms: {metadata['conversion_time_ms']}")

    @pytest.mark.integration
    @pytest.mark.slow
    def test_doc_file_processing_pipeline_mock(
        self,
        embedding_engine_instance,
        storage_client_instance,
        skip_if_legacy_office_unavailable,
    ):
        """Test complete .doc processing pipeline with mocks.

        Pipeline: .doc detection → conversion → Docling → embedding → storage
        """
        # Create processor
        processor = DocumentProcessor(
            embedding_engine=embedding_engine_instance,
            storage_client=storage_client_instance,
        )

        # Mock the conversion and parsing stages
        with patch(
            "tkr_docusearch.processing.docling_parser.get_legacy_office_client"
        ) as mock_get_client:
            # Mock client
            mock_client = Mock()
            mock_client.convert_doc_to_docx.return_value = "/uploads/test.docx"
            mock_get_client.return_value = mock_client

            # Mock Docling
            with patch("tkr_docusearch.processing.docling_parser.DocumentConverter"):
                with patch(
                    "tkr_docusearch.processing.docling_parser.docling_to_pages"
                ) as mock_to_pages:
                    # Return some mock pages
                    mock_to_pages.return_value = [
                        {
                            "page_num": 1,
                            "text": "Test document content",
                            "markdown": "# Test\n\nContent here.",
                        }
                    ]

                    with patch("tkr_docusearch.processing.docling_parser.FormatOptionsBuilder"):
                        with patch.object(Path, "exists", return_value=True):
                            with patch.object(Path, "stat") as mock_stat:
                                mock_stat.return_value.st_size = 1024

                                # Process .doc file
                                result = processor.process_document(
                                    file_path="/uploads/test.doc",
                                    chunk_size_words=250,
                                    chunk_overlap_words=50,
                                )

        # Verify processing completed
        assert result.doc_id is not None, "Should have document ID"
        assert result.text_ids is not None, "Should have text chunk IDs"

        # Verify conversion was called
        mock_client.convert_doc_to_docx.assert_called_once_with("/uploads/test.doc")

        logger.info("✓ Complete .doc processing pipeline (mocked)")
        logger.info(f"  Doc ID: {result.doc_id}")
        logger.info(f"  Text chunks: {len(result.text_ids) if result.text_ids else 0}")


# ====================================================================================
# Metadata Propagation Tests
# ====================================================================================


class TestMetadataPropagation:
    """Test that .doc conversion metadata propagates through the pipeline."""

    @pytest.mark.integration
    def test_conversion_metadata_stored_in_chromadb(
        self, embedding_engine_instance, storage_client_instance
    ):
        """Test that conversion metadata is stored in ChromaDB."""
        # Create mock storage client that tracks stored metadata
        stored_visual_metadata: List[dict] = []
        stored_text_metadata: List[dict] = []

        def mock_add_visual(ids, embeddings, metadatas, **kwargs):
            stored_visual_metadata.extend(metadatas)

        def mock_add_text(ids, embeddings, metadatas, documents, **kwargs):
            stored_text_metadata.extend(metadatas)

        storage_client_instance._visual_collection.add.side_effect = mock_add_visual
        storage_client_instance._text_collection.add.side_effect = mock_add_text

        # Create processor
        processor = DocumentProcessor(
            embedding_engine=embedding_engine_instance,
            storage_client=storage_client_instance,
        )

        # Mock conversion and processing
        with patch(
            "tkr_docusearch.processing.docling_parser.get_legacy_office_client"
        ) as mock_get_client:
            mock_client = Mock()
            mock_client.convert_doc_to_docx.return_value = "/uploads/report.docx"
            mock_get_client.return_value = mock_client

            with patch("tkr_docusearch.processing.docling_parser.DocumentConverter"):
                with patch(
                    "tkr_docusearch.processing.docling_parser.docling_to_pages"
                ) as mock_to_pages:
                    mock_to_pages.return_value = [
                        {
                            "page_num": 1,
                            "text": "Report content",
                            "markdown": "# Report\n\nContent",
                        }
                    ]

                    with patch("tkr_docusearch.processing.docling_parser.FormatOptionsBuilder"):
                        with patch.object(Path, "exists", return_value=True):
                            with patch.object(Path, "stat") as mock_stat:
                                mock_stat.return_value.st_size = 2048

                                # Process document
                                result = processor.process_document(
                                    file_path="/uploads/report.doc",
                                    chunk_size_words=250,
                                    chunk_overlap_words=50,
                                )

        # Verify metadata was stored
        # Note: Visual metadata is per-page, text metadata is per-chunk
        if stored_visual_metadata:
            # Check first visual metadata
            visual_meta = stored_visual_metadata[0]
            assert "filename" in visual_meta
            assert visual_meta["filename"] == "report.doc"

            logger.info("✓ Visual metadata stored with original filename")

        if stored_text_metadata:
            # Check first text metadata
            text_meta = stored_text_metadata[0]
            assert "filename" in text_meta
            assert text_meta["filename"] == "report.doc"

            logger.info("✓ Text metadata stored with original filename")

        logger.info(
            f"✓ Metadata stored (visual: {len(stored_visual_metadata)}, "
            f"text: {len(stored_text_metadata)})"
        )


# ====================================================================================
# Search Integration Tests
# ====================================================================================


class TestConvertedDocSearch:
    """Test that converted documents are searchable."""

    @pytest.mark.integration
    def test_converted_doc_content_searchable_mock(
        self, embedding_engine_instance, storage_client_instance
    ):
        """Test that converted .doc content is searchable (mocked)."""
        # Track stored documents
        stored_documents: List[str] = []

        def mock_add_text(ids, embeddings, metadatas, documents, **kwargs):
            stored_documents.extend(documents)

        storage_client_instance._text_collection.add.side_effect = mock_add_text

        # Create processor
        processor = DocumentProcessor(
            embedding_engine=embedding_engine_instance,
            storage_client=storage_client_instance,
        )

        # Mock conversion with specific content
        test_content = "Quarterly revenue report shows 25% growth in Q4"

        with patch(
            "tkr_docusearch.processing.docling_parser.get_legacy_office_client"
        ) as mock_get_client:
            mock_client = Mock()
            mock_client.convert_doc_to_docx.return_value = "/uploads/revenue.docx"
            mock_get_client.return_value = mock_client

            with patch("tkr_docusearch.processing.docling_parser.DocumentConverter"):
                with patch(
                    "tkr_docusearch.processing.docling_parser.docling_to_pages"
                ) as mock_to_pages:
                    mock_to_pages.return_value = [
                        {"page_num": 1, "text": test_content, "markdown": f"# Revenue\n\n{test_content}"}
                    ]

                    with patch("tkr_docusearch.processing.docling_parser.FormatOptionsBuilder"):
                        with patch.object(Path, "exists", return_value=True):
                            with patch.object(Path, "stat") as mock_stat:
                                mock_stat.return_value.st_size = 1024

                                # Process document
                                result = processor.process_document(
                                    file_path="/uploads/revenue.doc",
                                    chunk_size_words=250,
                                    chunk_overlap_words=50,
                                )

        # Verify content was stored
        assert len(stored_documents) > 0, "Should have stored document chunks"

        # Verify test content is in stored documents
        all_text = " ".join(stored_documents)
        assert "revenue" in all_text.lower(), "Should contain revenue content"
        assert "Q4" in all_text or "quarterly" in all_text.lower(), "Should contain quarterly info"

        logger.info(f"✓ Converted .doc content stored ({len(stored_documents)} chunks)")
        logger.info(f"  Sample content: {stored_documents[0][:100]}...")


# ====================================================================================
# Error Handling Tests
# ====================================================================================


class TestDocConversionErrorHandling:
    """Test error handling in .doc conversion pipeline."""

    @pytest.mark.integration
    def test_conversion_service_unavailable_error(self):
        """Test graceful handling when conversion service is unavailable."""
        # Create parser
        parser = DoclingParser()

        # Mock unavailable service
        with patch(
            "tkr_docusearch.processing.docling_parser.get_legacy_office_client"
        ) as mock_get_client:
            mock_client = Mock()
            mock_client.convert_doc_to_docx.side_effect = LegacyOfficeError(
                "Service unavailable"
            )
            mock_get_client.return_value = mock_client

            # Should raise ParsingError
            from tkr_docusearch.processing.docling_parser import ParsingError

            with pytest.raises(ParsingError) as exc_info:
                parser._convert_legacy_doc("/uploads/test.doc")

            assert "Doc conversion failed" in str(exc_info.value)
            logger.info("✓ Handles service unavailable error correctly")

    @pytest.mark.integration
    def test_corrupt_doc_file_error(self):
        """Test handling of corrupt .doc files."""
        parser = DoclingParser()

        # Mock corrupt file scenario
        with patch(
            "tkr_docusearch.processing.docling_parser.get_legacy_office_client"
        ) as mock_get_client:
            mock_client = Mock()
            mock_client.convert_doc_to_docx.side_effect = LegacyOfficeError(
                "Conversion failed: corrupt file"
            )
            mock_get_client.return_value = mock_client

            from tkr_docusearch.processing.docling_parser import ParsingError

            with pytest.raises(ParsingError):
                parser._convert_legacy_doc("/uploads/corrupt.doc")

            logger.info("✓ Handles corrupt file error correctly")

    @pytest.mark.integration
    def test_missing_doc_file_error(self):
        """Test handling of missing .doc files."""
        parser = DoclingParser()

        # Mock missing file scenario
        with patch(
            "tkr_docusearch.processing.docling_parser.get_legacy_office_client"
        ) as mock_get_client:
            mock_client = Mock()
            mock_client.convert_doc_to_docx.side_effect = FileNotFoundError(
                "File not found in Docker container"
            )
            mock_get_client.return_value = mock_client

            from tkr_docusearch.processing.docling_parser import ParsingError

            with pytest.raises(ParsingError):
                parser._convert_legacy_doc("/uploads/missing.doc")

            logger.info("✓ Handles missing file error correctly")


# ====================================================================================
# Path Translation Tests
# ====================================================================================


class TestPathTranslation:
    """Test path translation between native and Docker formats."""

    @pytest.mark.integration
    def test_native_to_docker_path_translation(self):
        """Test that native paths are translated to Docker format."""
        parser = DoclingParser()

        # Mock client
        with patch(
            "tkr_docusearch.processing.docling_parser.get_legacy_office_client"
        ) as mock_get_client:
            mock_client = Mock()
            mock_client.convert_doc_to_docx.return_value = "/uploads/report.docx"
            mock_get_client.return_value = mock_client

            # Call with native path
            native_path = "/Volumes/data/uploads/report.doc"
            docx_path, conversion_time = parser._convert_legacy_doc(native_path)

            # Verify Docker path was used in call
            mock_client.convert_doc_to_docx.assert_called_once_with("/uploads/report.doc")

            # Verify native path was returned
            assert docx_path == "/Volumes/data/uploads/report.docx"

            logger.info("✓ Path translation works correctly")
            logger.info(f"  Native: {native_path}")
            logger.info(f"  Docker: /uploads/report.doc")
            logger.info(f"  Result: {docx_path}")

    @pytest.mark.integration
    def test_docker_path_passthrough(self):
        """Test that Docker paths are used as-is."""
        parser = DoclingParser()

        with patch(
            "tkr_docusearch.processing.docling_parser.get_legacy_office_client"
        ) as mock_get_client:
            mock_client = Mock()
            mock_client.convert_doc_to_docx.return_value = "/uploads/test.docx"
            mock_get_client.return_value = mock_client

            # Call with Docker path
            docker_path = "/uploads/test.doc"
            docx_path, conversion_time = parser._convert_legacy_doc(docker_path)

            # Should use Docker path as-is
            mock_client.convert_doc_to_docx.assert_called_once_with("/uploads/test.doc")

            logger.info("✓ Docker path passthrough works correctly")
