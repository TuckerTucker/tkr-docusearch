"""
End-to-end tests for enhanced mode document processing.

Tests the complete pipeline from document upload through structure extraction,
enhanced metadata storage, and structure API retrieval.

Test Scenarios:
1. Upload document with enhanced mode enabled
2. Wait for processing to complete
3. Verify enhanced visual metadata stored in ChromaDB
4. Verify enhanced text metadata stored in ChromaDB
5. Query structure API endpoint
6. Validate bboxes, chunk IDs, and context present
7. Test page→chunk mapping
8. Test structure compression/decompression
"""

import json
from pathlib import Path
from typing import Optional

import httpx
import pytest

from tkr_docusearch.storage.chroma_client import ChromaClient
from tkr_docusearch.storage.compression import decompress_structure_metadata
from tkr_docusearch.storage.metadata_schema import DocumentStructure


class TestEnhancedModeE2E:
    """End-to-end tests for enhanced mode document processing"""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_upload_and_process_with_enhanced_mode(
        self,
        worker_api_client: httpx.Client,
        chromadb_client: ChromaClient,
        sample_pdf_with_structure: Optional[Path],
        test_doc_ids: list[str],
        wait_for_processing_helper,
    ):
        """
        Test complete pipeline from upload to enhanced metadata storage.

        Steps:
        1. Upload test document with enhanced mode
        2. Wait for processing to complete
        3. Query ChromaDB for visual embeddings
        4. Verify enhanced visual metadata present
        5. Query ChromaDB for text embeddings
        6. Verify enhanced text metadata present
        """
        if sample_pdf_with_structure is None:
            pytest.skip("Sample PDF with structure not available")

        # Step 1: Upload document (simulated - would use webhook in real scenario)
        # For E2E testing, we need a real document to be processed
        # This test assumes a document has been processed or can be triggered
        pytest.skip(
            "Full upload E2E requires running copyparty webhook integration. "
            "See test_structure_retrieval_* for database-level validation."
        )

    @pytest.mark.integration
    def test_structure_retrieval_with_decompression(
        self, chromadb_client: ChromaClient, skip_if_services_unavailable
    ):
        """
        Test retrieval and decompression of structure metadata.

        This test validates:
        1. Structure metadata can be retrieved from ChromaDB
        2. Compressed structure can be decompressed
        3. All structure elements are preserved (headings, tables, pictures)
        4. Bboxes are valid
        """
        # Create sample structure for testing
        from tkr_docusearch.storage.metadata_schema import (
            HeadingInfo,
            HeadingLevel,
            PictureInfo,
            PictureType,
            TableInfo,
        )

        structure = DocumentStructure(
            headings=[
                HeadingInfo(
                    text="Introduction",
                    level=HeadingLevel.SECTION_HEADER,
                    page_num=1,
                    section_path="1. Introduction",
                    bbox=(72.0, 100.5, 540.0, 125.3),
                ),
                HeadingInfo(
                    text="Methodology",
                    level=HeadingLevel.SECTION_HEADER,
                    page_num=2,
                    section_path="2. Methodology",
                    bbox=(72.0, 650.0, 540.0, 675.0),
                ),
            ],
            tables=[
                TableInfo(
                    page_num=2,
                    caption="Experimental Results",
                    num_rows=10,
                    num_cols=5,
                    has_header=True,
                    table_id="table-0",
                    bbox=(100.0, 200.0, 500.0, 450.0),
                )
            ],
            pictures=[
                PictureInfo(
                    page_num=1,
                    picture_type=PictureType.CHART,
                    caption="Figure 1: Growth chart",
                    confidence=0.95,
                    picture_id="picture-0",
                    bbox=(150.0, 300.0, 450.0, 500.0),
                )
            ],
        )
        structure.total_sections = 2
        structure.max_heading_depth = 1

        # Compress structure
        from tkr_docusearch.storage.compression import compress_structure_metadata

        compressed = compress_structure_metadata(structure.to_dict())

        # Simulate storing in ChromaDB
        doc_id = "test-doc-e2e-structure"
        metadata = {
            "doc_id": doc_id,
            "filename": "test_report.pdf",
            "page": 1,
            "has_structure": True,
            "structure": compressed,
            "image_width": 1700,
            "image_height": 2200,
        }

        # Store in visual collection
        import numpy as np

        embedding = np.random.randn(1031, 128).astype(np.float32)
        chromadb_client.add_visual_embedding(
            doc_id=doc_id, page_num=1, embedding=embedding, metadata=metadata
        )

        # Step 1: Retrieve from ChromaDB
        results = chromadb_client._visual_collection.get(
            where={"doc_id": doc_id, "page": 1}, include=["metadatas"]
        )

        assert len(results["ids"]) == 1, "Should retrieve one visual embedding"
        retrieved_metadata = results["metadatas"][0]

        # Step 2: Verify enhanced metadata present
        assert retrieved_metadata["has_structure"] is True
        assert "structure" in retrieved_metadata
        assert retrieved_metadata["image_width"] == 1700
        assert retrieved_metadata["image_height"] == 2200

        # Step 3: Decompress structure
        decompressed = decompress_structure_metadata(retrieved_metadata["structure"])

        # Step 4: Validate structure elements
        assert "headings" in decompressed
        assert len(decompressed["headings"]) == 2
        assert decompressed["headings"][0]["text"] == "Introduction"
        assert decompressed["headings"][1]["text"] == "Methodology"

        assert "tables" in decompressed
        assert len(decompressed["tables"]) == 1
        assert decompressed["tables"][0]["caption"] == "Experimental Results"
        assert decompressed["tables"][0]["table_id"] == "table-0"

        assert "pictures" in decompressed
        assert len(decompressed["pictures"]) == 1
        assert decompressed["pictures"][0]["picture_type"] == "chart"
        assert decompressed["pictures"][0]["picture_id"] == "picture-0"

        # Step 5: Validate bboxes
        intro_bbox = decompressed["headings"][0]["bbox"]
        assert intro_bbox == [72.0, 100.5, 540.0, 125.3]
        assert len(intro_bbox) == 4  # [left, bottom, right, top]

        table_bbox = decompressed["tables"][0]["bbox"]
        assert table_bbox == [100.0, 200.0, 500.0, 450.0]

        picture_bbox = decompressed["pictures"][0]["bbox"]
        assert picture_bbox == [150.0, 300.0, 450.0, 500.0]

        # Cleanup
        chromadb_client._visual_collection.delete(where={"doc_id": doc_id})

    @pytest.mark.integration
    def test_page_chunk_mapping(self, chromadb_client: ChromaClient, skip_if_services_unavailable):
        """
        Test querying chunks by page number.

        Validates:
        1. Can query all chunks on a specific page
        2. Chunk context includes page information
        3. Multi-page chunks are handled correctly
        """
        doc_id = "test-doc-page-chunks"

        # Create test data: multiple chunks on page 1 and 2
        import numpy as np

        # Page 1 chunks
        for chunk_num in [1, 2, 3]:
            chunk_id = f"{doc_id}-chunk{chunk_num:04d}"
            metadata = {
                "doc_id": doc_id,
                "filename": "test.pdf",
                "chunk_id": chunk_id,
                "page": 1,
                "has_context": True,
                "parent_heading": "Introduction",
                "section_path": "1. Introduction",
                "page_nums": json.dumps([1]),
            }
            embedding = np.random.randn(30, 128).astype(np.float32)
            chromadb_client.add_text_embedding(
                doc_id=doc_id,
                chunk_id=chunk_id,
                text=f"Chunk {chunk_num} content",
                embedding=embedding,
                metadata=metadata,
            )

        # Page 2 chunks
        for chunk_num in [4, 5]:
            chunk_id = f"{doc_id}-chunk{chunk_num:04d}"
            metadata = {
                "doc_id": doc_id,
                "filename": "test.pdf",
                "chunk_id": chunk_id,
                "page": 2,
                "has_context": True,
                "parent_heading": "Methods",
                "section_path": "2. Methods",
                "page_nums": json.dumps([2]),
            }
            embedding = np.random.randn(30, 128).astype(np.float32)
            chromadb_client.add_text_embedding(
                doc_id=doc_id,
                chunk_id=chunk_id,
                text=f"Chunk {chunk_num} content",
                embedding=embedding,
                metadata=metadata,
            )

        # Multi-page chunk (spans pages 2-3)
        chunk_id = f"{doc_id}-chunk0006"
        metadata = {
            "doc_id": doc_id,
            "filename": "test.pdf",
            "chunk_id": chunk_id,
            "page": 2,  # Primary page
            "has_context": True,
            "parent_heading": "Methods",
            "section_path": "2. Methods",
            "page_nums": json.dumps([2, 3]),
            "is_page_boundary": True,
        }
        embedding = np.random.randn(30, 128).astype(np.float32)
        chromadb_client.add_text_embedding(
            doc_id=doc_id,
            chunk_id=chunk_id,
            text="Multi-page chunk content",
            embedding=embedding,
            metadata=metadata,
        )

        # Test 1: Query chunks on page 1
        page1_results = chromadb_client._text_collection.get(
            where={"doc_id": doc_id, "page": 1}, include=["metadatas"]
        )

        assert len(page1_results["ids"]) == 3, "Should have 3 chunks on page 1"
        for metadata in page1_results["metadatas"]:
            page_nums = json.loads(metadata["page_nums"])
            assert 1 in page_nums, "Page 1 chunks should include page 1 in page_nums"

        # Test 2: Query chunks on page 2
        page2_results = chromadb_client._text_collection.get(
            where={"doc_id": doc_id, "page": 2}, include=["metadatas"]
        )

        assert len(page2_results["ids"]) == 3, "Should have 3 chunks on page 2"

        # Test 3: Verify multi-page chunk
        multi_page_chunk = next(
            m for m in page2_results["metadatas"] if m.get("is_page_boundary") is True
        )
        page_nums = json.loads(multi_page_chunk["page_nums"])
        assert page_nums == [2, 3], "Multi-page chunk should span pages 2 and 3"

        # Cleanup
        chromadb_client._text_collection.delete(where={"doc_id": doc_id})

    @pytest.mark.integration
    def test_enhanced_visual_metadata_fields(
        self, chromadb_client: ChromaClient, skip_if_services_unavailable
    ):
        """
        Test all enhanced visual metadata fields are stored correctly.

        Validates:
        - has_structure flag
        - num_headings, num_tables, num_pictures counts
        - max_heading_depth
        - image_width, image_height
        - structure compression
        """
        from tkr_docusearch.processing.handlers.enhanced_metadata import prepare_enhanced_visual_metadata
        from tkr_docusearch.storage.metadata_schema import HeadingInfo, HeadingLevel, PictureInfo, PictureType

        # Create structure
        structure = DocumentStructure(
            headings=[
                HeadingInfo(
                    text="Title",
                    level=HeadingLevel.TITLE,
                    page_num=1,
                    section_path="Title",
                    bbox=(72.0, 700.0, 540.0, 750.0),
                ),
                HeadingInfo(
                    text="Section 1",
                    level=HeadingLevel.SECTION_HEADER,
                    page_num=1,
                    section_path="Title > Section 1",
                    bbox=(72.0, 600.0, 540.0, 620.0),
                ),
                HeadingInfo(
                    text="Subsection 1.1",
                    level=HeadingLevel.SUBSECTION_HEADER,
                    page_num=1,
                    section_path="Title > Section 1 > Subsection 1.1",
                    bbox=(72.0, 500.0, 540.0, 515.0),
                ),
            ],
            pictures=[
                PictureInfo(
                    page_num=1,
                    picture_type=PictureType.PHOTOGRAPH,
                    picture_id="pic-0",
                    bbox=(100.0, 200.0, 400.0, 450.0),
                )
            ],
        )
        structure.total_sections = 1
        structure.max_heading_depth = 3

        # Prepare enhanced metadata
        base_metadata = {
            "filename": "test_visual.pdf",
            "page": 1,
            "doc_id": "test-visual-meta",
            "source_path": "/data/uploads/test_visual.pdf",
        }

        enhanced = prepare_enhanced_visual_metadata(
            base_metadata=base_metadata,
            structure=structure,
            image_width=1700,
            image_height=2200,
        )

        # Verify enhanced fields
        assert enhanced["has_structure"] is True
        assert enhanced["num_headings"] == 3
        assert enhanced["num_tables"] == 0
        assert enhanced["num_pictures"] == 1
        assert enhanced["max_heading_depth"] == 3
        assert enhanced["image_width"] == 1700
        assert enhanced["image_height"] == 2200
        assert "structure" in enhanced

        # Store and retrieve
        import numpy as np

        embedding = np.random.randn(1031, 128).astype(np.float32)
        chromadb_client.add_visual_embedding(
            doc_id=base_metadata["doc_id"],
            page_num=1,
            embedding=embedding,
            metadata=enhanced,
        )

        # Retrieve and validate
        results = chromadb_client._visual_collection.get(
            where={"doc_id": base_metadata["doc_id"]}, include=["metadatas"]
        )

        stored_metadata = results["metadatas"][0]
        assert stored_metadata["has_structure"] is True
        assert stored_metadata["num_headings"] == 3
        assert stored_metadata["num_pictures"] == 1
        assert stored_metadata["max_heading_depth"] == 3

        # Cleanup
        chromadb_client._visual_collection.delete(where={"doc_id": base_metadata["doc_id"]})

    @pytest.mark.integration
    def test_enhanced_text_metadata_fields(
        self, chromadb_client: ChromaClient, skip_if_services_unavailable
    ):
        """
        Test all enhanced text metadata fields are stored correctly.

        Validates:
        - has_context flag
        - parent_heading, parent_heading_level
        - section_path
        - element_type
        - related_tables, related_pictures (JSON arrays)
        - page_nums (JSON array)
        - is_page_boundary flag
        """
        from tkr_docusearch.processing.handlers.enhanced_metadata import prepare_enhanced_text_metadata
        from tkr_docusearch.storage.metadata_schema import ChunkContext

        # Create chunk context
        context = ChunkContext(
            parent_heading="Introduction",
            parent_heading_level=1,
            section_path="Report > Introduction",
            element_type="text",
            related_tables=["table-0", "table-1"],
            related_pictures=["picture-0"],
            page_nums=[1, 2],
            is_page_boundary=True,
        )

        # Prepare enhanced metadata
        base_metadata = {
            "filename": "test_text.pdf",
            "chunk_id": "test-text-meta-chunk0001",
            "page": 1,
            "doc_id": "test-text-meta",
            "text_preview": "Introduction text preview...",
            "full_text": "Introduction text content that spans multiple pages",
            "word_count": 8,
        }

        enhanced = prepare_enhanced_text_metadata(base_metadata=base_metadata, context=context)

        # Verify enhanced fields
        assert enhanced["has_context"] is True
        assert enhanced["parent_heading"] == "Introduction"
        assert enhanced["parent_heading_level"] == 1
        assert enhanced["section_path"] == "Report > Introduction"
        assert enhanced["element_type"] == "text"
        assert enhanced["is_page_boundary"] is True

        # Verify JSON arrays
        related_tables = json.loads(enhanced["related_tables"])
        assert related_tables == ["table-0", "table-1"]

        related_pictures = json.loads(enhanced["related_pictures"])
        assert related_pictures == ["picture-0"]

        page_nums = json.loads(enhanced["page_nums"])
        assert page_nums == [1, 2]

        # Store and retrieve
        import numpy as np

        embedding = np.random.randn(30, 128).astype(np.float32)
        chromadb_client.add_text_embedding(
            doc_id=base_metadata["doc_id"],
            chunk_id=base_metadata["chunk_id"],
            text=base_metadata["full_text"],
            embedding=embedding,
            metadata=enhanced,
        )

        # Retrieve and validate
        results = chromadb_client._text_collection.get(
            where={"doc_id": base_metadata["doc_id"]}, include=["metadatas"]
        )

        stored_metadata = results["metadatas"][0]
        assert stored_metadata["has_context"] is True
        assert stored_metadata["parent_heading"] == "Introduction"
        assert stored_metadata["section_path"] == "Report > Introduction"
        assert stored_metadata["is_page_boundary"] is True

        # Verify JSON arrays round-trip correctly
        assert json.loads(stored_metadata["related_tables"]) == ["table-0", "table-1"]
        assert json.loads(stored_metadata["page_nums"]) == [1, 2]

        # Cleanup
        chromadb_client._text_collection.delete(where={"doc_id": base_metadata["doc_id"]})


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
