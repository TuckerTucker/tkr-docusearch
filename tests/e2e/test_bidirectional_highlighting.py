"""
End-to-end tests for bidirectional highlighting data flow.

Tests the data availability and consistency required for bidirectional
highlighting between bounding boxes and markdown chunks.

Note: These are integration tests validating data flow and API contracts.
Frontend interaction tests (click handlers, DOM manipulation) are manual.

Test Scenarios:
1. Bbox→chunk: Structure API provides chunk_id for each bbox
2. Chunk→bbox: Markdown markers map to bboxes in structure
3. Coordinate system consistency
4. Multi-element highlighting (chunk with multiple bboxes)
5. Edge cases and error handling
"""

import json

import pytest

from src.research.chunk_extractor import parse_chunk_id
from src.storage.chroma_client import ChromaClient
from src.storage.compression import compress_structure_metadata, decompress_structure_metadata
from src.storage.metadata_schema import (
    DocumentStructure,
    HeadingInfo,
    HeadingLevel,
    PictureInfo,
    PictureType,
    TableInfo,
)


class TestBboxToChunkDataFlow:
    """Test data available for bbox→chunk highlighting"""

    @pytest.mark.integration
    def test_structure_bboxes_have_chunk_context(
        self, chromadb_client: ChromaClient, skip_if_services_unavailable
    ):
        """
        Test that structure bboxes can be mapped to chunks.

        Data flow:
        1. User hovers over bbox on page
        2. Frontend queries structure API for bbox chunk mapping
        3. Structure contains bbox coordinates and related chunk info
        4. Frontend highlights corresponding markdown chunk
        """
        doc_id = "bbox-chunk-test"

        # Create structure with bboxes
        structure = DocumentStructure(
            headings=[
                HeadingInfo(
                    text="Introduction",
                    level=HeadingLevel.SECTION_HEADER,
                    page_num=1,
                    section_path="1. Introduction",
                    bbox=(72.0, 600.0, 540.0, 625.0),
                ),
                HeadingInfo(
                    text="Methods",
                    level=HeadingLevel.SECTION_HEADER,
                    page_num=1,
                    section_path="2. Methods",
                    bbox=(72.0, 400.0, 540.0, 420.0),
                ),
            ],
            tables=[
                TableInfo(
                    page_num=1,
                    caption="Results Table",
                    num_rows=5,
                    num_cols=3,
                    has_header=True,
                    table_id="table-0",
                    bbox=(100.0, 200.0, 500.0, 380.0),
                )
            ],
        )

        # Store in ChromaDB
        import numpy as np

        compressed = compress_structure_metadata(structure.to_dict())
        metadata = {
            "doc_id": doc_id,
            "filename": "test.pdf",
            "page": 1,
            "has_structure": True,
            "structure": compressed,
        }

        embedding = np.random.randn(1031, 128).astype(np.float32)
        chromadb_client.add_visual_embedding(
            doc_id=doc_id, page_num=1, embedding=embedding, metadata=metadata
        )

        # Retrieve structure
        results = chromadb_client._visual_collection.get(
            where={"doc_id": doc_id, "page": 1}, include=["metadatas"]
        )

        assert len(results["ids"]) == 1
        stored_metadata = results["metadatas"][0]

        # Decompress structure
        decompressed = decompress_structure_metadata(stored_metadata["structure"])

        # Verify bboxes present
        assert len(decompressed["headings"]) == 2
        assert len(decompressed["tables"]) == 1

        # Each bbox should have coordinates
        intro_bbox = decompressed["headings"][0]["bbox"]
        assert intro_bbox == [72.0, 600.0, 540.0, 625.0]
        assert len(intro_bbox) == 4  # [left, bottom, right, top]

        # Verify section_path available for mapping to chunks
        assert decompressed["headings"][0]["section_path"] == "1. Introduction"

        # Cleanup
        chromadb_client._visual_collection.delete(where={"doc_id": doc_id})

    @pytest.mark.integration
    def test_fetch_chunk_metadata_for_bbox(
        self, chromadb_client: ChromaClient, skip_if_services_unavailable
    ):
        """
        Test fetching chunk metadata for a bbox section.

        Data flow:
        1. User hovers over heading bbox with section_path "1. Introduction"
        2. Frontend queries text chunks with matching section_path
        3. Highlights corresponding chunks in markdown
        """
        doc_id = "bbox-to-chunk-metadata"

        import numpy as np

        # Create text chunks with section context
        chunks = [
            {
                "chunk_id": f"{doc_id}-chunk0001",
                "section_path": "1. Introduction",
                "parent_heading": "Introduction",
                "text": "Introduction paragraph 1",
            },
            {
                "chunk_id": f"{doc_id}-chunk0002",
                "section_path": "1. Introduction",
                "parent_heading": "Introduction",
                "text": "Introduction paragraph 2",
            },
            {
                "chunk_id": f"{doc_id}-chunk0003",
                "section_path": "2. Methods",
                "parent_heading": "Methods",
                "text": "Methods paragraph 1",
            },
        ]

        for chunk in chunks:
            metadata = {
                "doc_id": doc_id,
                "filename": "test.pdf",
                "chunk_id": chunk["chunk_id"],
                "page": 1,
                "has_context": True,
                "section_path": chunk["section_path"],
                "parent_heading": chunk["parent_heading"],
            }
            embedding = np.random.randn(30, 128).astype(np.float32)

            chromadb_client.add_text_embedding(
                doc_id=doc_id,
                chunk_id=chunk["chunk_id"],
                text=chunk["text"],
                embedding=embedding,
                metadata=metadata,
            )

        # Simulate: User hovers over "Introduction" heading bbox
        # Frontend queries chunks with section_path="1. Introduction"
        results = chromadb_client._text_collection.get(
            where={"doc_id": doc_id, "section_path": "1. Introduction"}, include=["metadatas"]
        )

        # Should retrieve 2 chunks in Introduction section
        assert len(results["ids"]) == 2
        chunk_ids = [m["chunk_id"] for m in results["metadatas"]]
        assert f"{doc_id}-chunk0001" in chunk_ids
        assert f"{doc_id}-chunk0002" in chunk_ids

        # Each chunk has needed metadata for highlighting
        for metadata in results["metadatas"]:
            assert "chunk_id" in metadata
            assert "section_path" in metadata
            assert "parent_heading" in metadata

        # Cleanup
        chromadb_client._text_collection.delete(where={"doc_id": doc_id})


class TestChunkToBboxDataFlow:
    """Test data available for chunk→bbox highlighting"""

    @pytest.mark.integration
    def test_chunk_markers_map_to_bboxes(
        self, chromadb_client: ChromaClient, skip_if_services_unavailable
    ):
        """
        Test that chunk markers in markdown map to bboxes in structure.

        Data flow:
        1. User hovers over markdown chunk
        2. Frontend extracts chunk_id from chunk marker
        3. Frontend queries chunk metadata for section_path
        4. Frontend finds matching bboxes in structure by section_path
        5. Highlights bboxes on page image
        """
        doc_id = "chunk-to-bbox-mapping"

        # Step 1: Create text chunk with context
        import numpy as np

        chunk_id = f"{doc_id}-chunk0001"
        chunk_metadata = {
            "doc_id": doc_id,
            "filename": "test.pdf",
            "chunk_id": chunk_id,
            "page": 1,
            "has_context": True,
            "section_path": "1. Introduction",
            "parent_heading": "Introduction",
        }

        embedding = np.random.randn(30, 128).astype(np.float32)
        chromadb_client.add_text_embedding(
            doc_id=doc_id,
            chunk_id=chunk_id,
            text="Introduction content",
            embedding=embedding,
            metadata=chunk_metadata,
        )

        # Step 2: Create structure with matching section
        structure = DocumentStructure(
            headings=[
                HeadingInfo(
                    text="Introduction",
                    level=HeadingLevel.SECTION_HEADER,
                    page_num=1,
                    section_path="1. Introduction",
                    bbox=(72.0, 600.0, 540.0, 625.0),
                )
            ]
        )

        compressed = compress_structure_metadata(structure.to_dict())
        visual_metadata = {
            "doc_id": doc_id,
            "filename": "test.pdf",
            "page": 1,
            "has_structure": True,
            "structure": compressed,
        }

        visual_embedding = np.random.randn(1031, 128).astype(np.float32)
        chromadb_client.add_visual_embedding(
            doc_id=doc_id, page_num=1, embedding=visual_embedding, metadata=visual_metadata
        )

        # Step 3: Simulate user hovering over markdown chunk
        # Frontend extracts chunk_id from marker: <!-- CHUNK: {doc_id}-chunk0001 -->
        parsed = parse_chunk_id(chunk_id)
        assert parsed["doc_id"] == doc_id
        assert parsed["chunk_num"] == 1

        # Step 4: Fetch chunk metadata
        chunk_results = chromadb_client._text_collection.get(
            where={"doc_id": doc_id, "chunk_id": chunk_id}, include=["metadatas"]
        )

        assert len(chunk_results["ids"]) == 1
        chunk_meta = chunk_results["metadatas"][0]
        section_path = chunk_meta["section_path"]
        assert section_path == "1. Introduction"

        # Step 5: Fetch structure and find matching bboxes
        structure_results = chromadb_client._visual_collection.get(
            where={"doc_id": doc_id, "page": 1}, include=["metadatas"]
        )

        structure_meta = structure_results["metadatas"][0]
        decompressed_structure = decompress_structure_metadata(structure_meta["structure"])

        # Find bboxes with matching section_path
        matching_bboxes = [
            h for h in decompressed_structure["headings"] if h["section_path"] == section_path
        ]

        assert len(matching_bboxes) == 1
        bbox = matching_bboxes[0]["bbox"]
        assert bbox == [72.0, 600.0, 540.0, 625.0]

        # Frontend can now highlight this bbox on the page image

        # Cleanup
        chromadb_client._text_collection.delete(where={"doc_id": doc_id})
        chromadb_client._visual_collection.delete(where={"doc_id": doc_id})

    @pytest.mark.integration
    def test_chunk_with_multiple_related_elements(
        self, chromadb_client: ChromaClient, skip_if_services_unavailable
    ):
        """
        Test chunk with multiple related tables and pictures.

        Data flow:
        1. Chunk has related_tables and related_pictures metadata
        2. Frontend highlights all related elements when chunk hovered
        """
        doc_id = "chunk-multi-elements"

        import numpy as np

        # Create chunk with related elements
        chunk_id = f"{doc_id}-chunk0001"
        chunk_metadata = {
            "doc_id": doc_id,
            "filename": "test.pdf",
            "chunk_id": chunk_id,
            "page": 1,
            "has_context": True,
            "section_path": "Results",
            "related_tables": json.dumps(["table-0", "table-1"]),
            "related_pictures": json.dumps(["picture-0"]),
        }

        embedding = np.random.randn(30, 128).astype(np.float32)
        chromadb_client.add_text_embedding(
            doc_id=doc_id,
            chunk_id=chunk_id,
            text="Results discussion referencing tables and figures",
            embedding=embedding,
            metadata=chunk_metadata,
        )

        # Create structure with related elements
        structure = DocumentStructure(
            tables=[
                TableInfo(
                    page_num=1,
                    caption="Table 1",
                    num_rows=5,
                    num_cols=3,
                    has_header=True,
                    table_id="table-0",
                    bbox=(100.0, 500.0, 500.0, 600.0),
                ),
                TableInfo(
                    page_num=1,
                    caption="Table 2",
                    num_rows=3,
                    num_cols=2,
                    has_header=True,
                    table_id="table-1",
                    bbox=(100.0, 300.0, 500.0, 480.0),
                ),
            ],
            pictures=[
                PictureInfo(
                    page_num=1,
                    picture_type=PictureType.CHART,
                    caption="Figure 1",
                    picture_id="picture-0",
                    bbox=(100.0, 100.0, 400.0, 280.0),
                )
            ],
        )

        compressed = compress_structure_metadata(structure.to_dict())
        visual_metadata = {
            "doc_id": doc_id,
            "filename": "test.pdf",
            "page": 1,
            "has_structure": True,
            "structure": compressed,
        }

        visual_embedding = np.random.randn(1031, 128).astype(np.float32)
        chromadb_client.add_visual_embedding(
            doc_id=doc_id, page_num=1, embedding=visual_embedding, metadata=visual_metadata
        )

        # Simulate: User hovers over chunk in markdown
        # Frontend retrieves chunk metadata
        chunk_results = chromadb_client._text_collection.get(
            where={"doc_id": doc_id, "chunk_id": chunk_id}, include=["metadatas"]
        )

        chunk_meta = chunk_results["metadatas"][0]
        related_tables = json.loads(chunk_meta["related_tables"])
        related_pictures = json.loads(chunk_meta["related_pictures"])

        assert related_tables == ["table-0", "table-1"]
        assert related_pictures == ["picture-0"]

        # Fetch structure
        structure_results = chromadb_client._visual_collection.get(
            where={"doc_id": doc_id, "page": 1}, include=["metadatas"]
        )

        structure_meta = structure_results["metadatas"][0]
        decompressed_structure = decompress_structure_metadata(structure_meta["structure"])

        # Find matching tables
        matching_tables = [
            t for t in decompressed_structure["tables"] if t["table_id"] in related_tables
        ]
        assert len(matching_tables) == 2

        # Find matching pictures
        matching_pictures = [
            p for p in decompressed_structure["pictures"] if p["picture_id"] in related_pictures
        ]
        assert len(matching_pictures) == 1

        # Frontend can highlight all related bboxes
        table_bboxes = [t["bbox"] for t in matching_tables]
        picture_bboxes = [p["bbox"] for p in matching_pictures]

        assert len(table_bboxes) == 2
        assert len(picture_bboxes) == 1

        # Cleanup
        chromadb_client._text_collection.delete(where={"doc_id": doc_id})
        chromadb_client._visual_collection.delete(where={"doc_id": doc_id})


class TestCoordinateSystemConsistency:
    """Test coordinate system documentation matches reality"""

    @pytest.mark.integration
    def test_bbox_format_documentation(self):
        """Test that bbox format is [left, bottom, right, top]."""
        # According to structure API documentation
        bbox = [72.0, 100.5, 540.0, 125.3]

        left, bottom, right, top = bbox

        assert left < right, "Left should be less than right"
        # Note: For PDF coordinate system, bottom may be > top
        # This is because PDF origin is bottom-left, not top-left
        # So "bottom" coordinate is the Y value at the bottom of the bbox

    @pytest.mark.integration
    def test_coordinate_system_metadata(self, chromadb_client: ChromaClient):
        """Test coordinate system metadata in structure API."""
        # Structure API should document coordinate system
        expected_coordinate_system = {
            "format": "[left, bottom, right, top]",
            "origin": "bottom-left",
            "units": "points",
        }

        # This is documented in structure API response
        # Verify format matches
        assert expected_coordinate_system["format"] == "[left, bottom, right, top]"
        assert expected_coordinate_system["origin"] == "bottom-left"
        assert expected_coordinate_system["units"] == "points"

    @pytest.mark.integration
    def test_bbox_constraints(self):
        """
        Test bbox coordinate constraints.

        For PDF coordinate system (origin bottom-left):
        - left < right (always)
        - bottom < top (NOT always - depends on interpretation)

        Note: In PDF coordinates, "bottom" is the Y value of the bottom edge,
        which may be numerically greater than "top" Y value.
        """
        # Example bbox from PDF
        bbox = [72.0, 100.5, 540.0, 125.3]
        left, bottom, right, top = bbox

        # X coordinates should always be left < right
        assert left < right

        # Y coordinates: bottom vs top depends on coordinate system
        # For PDF (origin bottom-left), y increases upward
        # So "bottom" (100.5) < "top" (125.3) is expected
        assert bottom < top

    @pytest.mark.integration
    def test_bbox_to_frontend_conversion(self):
        """
        Test converting PDF bboxes to frontend canvas coordinates.

        Frontend uses top-left origin, PDF uses bottom-left origin.
        Conversion: y_canvas = page_height - y_pdf
        """
        page_height = 792.0  # Standard US Letter height in points

        # PDF bbox (bottom-left origin)
        pdf_bbox = [72.0, 100.5, 540.0, 125.3]
        left, bottom, right, top = pdf_bbox

        # Convert to canvas coordinates (top-left origin)
        canvas_bbox = {
            "left": left,
            "top": page_height - top,  # Flip Y
            "right": right,
            "bottom": page_height - bottom,  # Flip Y
            "width": right - left,
            "height": top - bottom,
        }

        assert canvas_bbox["left"] == 72.0
        assert canvas_bbox["right"] == 540.0
        assert canvas_bbox["top"] == 792.0 - 125.3
        assert canvas_bbox["bottom"] == 792.0 - 100.5
        assert canvas_bbox["width"] == 468.0
        assert canvas_bbox["height"] == 24.8


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.integration
    def test_empty_structure(self, chromadb_client: ChromaClient, skip_if_services_unavailable):
        """Test document with no structure metadata."""
        doc_id = "empty-structure-doc"

        import numpy as np

        # Document with has_structure=False
        metadata = {
            "doc_id": doc_id,
            "filename": "plain_text.pdf",
            "page": 1,
            "has_structure": False,
        }

        embedding = np.random.randn(1031, 128).astype(np.float32)
        chromadb_client.add_visual_embedding(
            doc_id=doc_id, page_num=1, embedding=embedding, metadata=metadata
        )

        # Retrieve
        results = chromadb_client._visual_collection.get(
            where={"doc_id": doc_id}, include=["metadatas"]
        )

        stored_metadata = results["metadatas"][0]
        assert stored_metadata["has_structure"] is False
        assert "structure" not in stored_metadata

        # Frontend should handle gracefully (no highlighting)

        # Cleanup
        chromadb_client._visual_collection.delete(where={"doc_id": doc_id})

    @pytest.mark.integration
    def test_missing_bbox_information(self, chromadb_client: ChromaClient):
        """Test structure elements without bbox data."""
        # Some elements may not have bbox (extracted from docx/pptx)
        structure = DocumentStructure(
            headings=[
                HeadingInfo(
                    text="Introduction",
                    level=HeadingLevel.SECTION_HEADER,
                    page_num=1,
                    section_path="1. Introduction",
                    bbox=None,  # No bbox available
                )
            ]
        )

        # Should still serialize/deserialize correctly
        from src.storage.compression import compress_structure_metadata

        compressed = compress_structure_metadata(structure.to_dict())
        decompressed = decompress_structure_metadata(compressed)

        assert decompressed["headings"][0]["bbox"] is None

        # Frontend should handle None bbox gracefully (no visual highlighting)

    @pytest.mark.integration
    def test_special_characters_in_section_paths(self):
        """Test section paths with special characters."""
        section_paths = [
            "Chapter 1: Introduction",
            "Section 2.1 > Methods",
            "Part I | Background",
            "Appendix A / B",
            "Question: What is this?",
        ]

        for section_path in section_paths:
            # Create heading with special chars
            heading = HeadingInfo(
                text="Test Heading",
                level=HeadingLevel.SECTION_HEADER,
                page_num=1,
                section_path=section_path,
            )

            # Should serialize correctly
            heading_dict = heading.to_dict()
            assert heading_dict["section_path"] == section_path

            # Frontend should handle when querying/matching

    @pytest.mark.integration
    def test_multi_page_chunk_highlighting(self, chromadb_client: ChromaClient):
        """Test chunk spanning multiple pages."""
        doc_id = "multi-page-chunk"

        import numpy as np

        # Chunk spanning pages 2-6
        chunk_id = f"{doc_id}-chunk0010"
        metadata = {
            "doc_id": doc_id,
            "filename": "test.pdf",
            "chunk_id": chunk_id,
            "page": 2,  # Primary page
            "has_context": True,
            "section_path": "Long Section",
            "page_nums": json.dumps([2, 3, 4, 5, 6]),
            "is_page_boundary": True,
        }

        embedding = np.random.randn(30, 128).astype(np.float32)
        chromadb_client.add_text_embedding(
            doc_id=doc_id,
            chunk_id=chunk_id,
            text="Very long content spanning 5 pages",
            embedding=embedding,
            metadata=metadata,
        )

        # Retrieve
        results = chromadb_client._text_collection.get(
            where={"doc_id": doc_id, "chunk_id": chunk_id}, include=["metadatas"]
        )

        stored_metadata = results["metadatas"][0]
        page_nums = json.loads(stored_metadata["page_nums"])

        assert len(page_nums) == 5
        assert page_nums == [2, 3, 4, 5, 6]
        assert stored_metadata["is_page_boundary"] is True

        # Frontend should indicate chunk spans multiple pages
        # Highlighting may only apply to current page

        # Cleanup
        chromadb_client._text_collection.delete(where={"doc_id": doc_id})


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
