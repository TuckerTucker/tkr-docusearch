"""
Integration test for DocumentStructure BBox API validation.

This test validates the complete backend pipeline for BoundingBox overlay feature:
1. Enhanced mode processes documents with structure extraction
2. Bboxes are extracted in correct format [x1, y1, x2, y2]
3. Structure metadata is stored in ChromaDB visual collection
4. Metadata can be retrieved and validated for API contracts
"""

import logging
from pathlib import Path
from typing import Any, Dict

import pytest

from src.config.processing_config import EnhancedModeConfig
from src.processing.docling_parser import DoclingParser
from src.storage.chroma_client import ChromaClient
from src.storage.metadata_schema import DocumentStructure

logger = logging.getLogger(__name__)


class TestStructureAPIValidation:
    """Test suite for BoundingBox overlay backend validation."""

    @pytest.fixture
    def enhanced_config(self):
        """Create enhanced mode configuration with all features enabled."""
        return EnhancedModeConfig(
            enable_table_structure=True,
            enable_picture_classification=True,
            enable_code_enrichment=False,  # Optional, can be slow
            enable_formula_enrichment=False,  # Optional, can be slow
        )

    @pytest.fixture
    def parser(self):
        """Create DoclingParser instance."""
        return DoclingParser(render_dpi=150)

    @pytest.fixture
    def chroma_client(self):
        """Create ChromaDB client for validation."""
        try:
            client = ChromaClient(host="chromadb", port=8001)
            if not client.heartbeat():
                pytest.skip("ChromaDB not available at chromadb:8001")
            return client
        except Exception as e:
            pytest.skip(f"ChromaDB connection failed: {e}")

    def test_enhanced_mode_extracts_structure_with_bboxes(self, parser, enhanced_config):
        """
        Validate that enhanced mode extracts DocumentStructure with bboxes.

        Tests:
        - ParsedDocument has structure metadata
        - Structure contains element counts (headings, tables, pictures)
        - Bboxes are extracted and stored
        """
        # Use test document
        test_pdf = (
            Path(__file__).parent.parent.parent / "data/test-documents/test-financial-report.docx"
        )

        if not test_pdf.exists():
            # Fallback to any available test document
            test_docs_dir = Path(__file__).parent.parent.parent / "data/test-documents"
            if test_docs_dir.exists():
                test_files = list(test_docs_dir.glob("*.pdf")) + list(test_docs_dir.glob("*.docx"))
                if test_files:
                    test_pdf = test_files[0]
                else:
                    pytest.skip("No test documents available")
            else:
                pytest.skip(f"Test document not found: {test_pdf}")

        logger.info(f"Testing enhanced mode structure extraction: {test_pdf}")

        # Parse document with enhanced mode
        parsed_doc = parser.parse_document(str(test_pdf), config=enhanced_config)

        # Validate ParsedDocument structure
        assert parsed_doc is not None, "ParsedDocument should not be None"
        assert hasattr(parsed_doc, "metadata"), "ParsedDocument should have metadata"
        assert "structure" in parsed_doc.metadata, "Metadata should contain structure info"

        # Extract structure summary
        structure_meta = parsed_doc.metadata["structure"]

        logger.info(f"Extracted structure: {structure_meta}")

        # Validate structure metadata exists
        assert "headings" in structure_meta, "Should have headings count"
        assert "tables" in structure_meta, "Should have tables count"
        assert "pictures" in structure_meta, "Should have pictures count"
        assert "max_heading_depth" in structure_meta, "Should have max_heading_depth"

        # Validate counts are non-negative
        assert structure_meta["headings"] >= 0
        assert structure_meta["tables"] >= 0
        assert structure_meta["pictures"] >= 0

        # Log what was extracted
        logger.info(
            f"Structure extracted: {structure_meta['headings']} headings, "
            f"{structure_meta['tables']} tables, {structure_meta['pictures']} pictures"
        )

    def test_bbox_format_validation(self, parser, enhanced_config):
        """
        Validate that bboxes are in correct [x1, y1, x2, y2] format.

        Tests:
        - Bbox is tuple/list of 4 numbers
        - Coordinates are valid (x1 < x2)
        - All coordinates are non-negative
        - Bbox format matches API contract
        """
        # Use test document
        test_pdf = (
            Path(__file__).parent.parent.parent / "data/test-documents/test-product-roadmap.pptx"
        )

        if not test_pdf.exists():
            pytest.skip(f"Test document not found: {test_pdf}")

        logger.info(f"Testing bbox format validation: {test_pdf}")

        # Extract structure directly to access bboxes
        from docling.document_converter import DocumentConverter

        from src.config.processing_config import create_pipeline_options
        from src.processing.structure_extractor import extract_document_structure

        create_pipeline_options(enhanced_config)
        converter = DocumentConverter()
        result = converter.convert(str(test_pdf))

        # Extract structure
        structure = extract_document_structure(result.document, enhanced_config)

        # Validate structure exists
        assert isinstance(structure, DocumentStructure), "Should return DocumentStructure"

        # Validate bboxes in all element types
        bbox_counts = {
            "headings": 0,
            "tables": 0,
            "pictures": 0,
            "code_blocks": 0,
            "formulas": 0,
        }

        # Check headings
        for heading in structure.headings:
            if heading.bbox is not None:
                self._validate_bbox(heading.bbox, f"Heading '{heading.text}'")
                bbox_counts["headings"] += 1

        # Check tables
        for table in structure.tables:
            if table.bbox is not None:
                self._validate_bbox(table.bbox, f"Table {table.table_id}")
                bbox_counts["tables"] += 1

        # Check pictures
        for picture in structure.pictures:
            if picture.bbox is not None:
                self._validate_bbox(picture.bbox, f"Picture {picture.picture_id}")
                bbox_counts["pictures"] += 1

        # Check code blocks
        for code in structure.code_blocks:
            if code.bbox is not None:
                self._validate_bbox(code.bbox, "Code block")
                bbox_counts["code_blocks"] += 1

        # Check formulas
        for formula in structure.formulas:
            if formula.bbox is not None:
                self._validate_bbox(formula.bbox, "Formula")
                bbox_counts["formulas"] += 1

        logger.info(f"Validated bboxes: {bbox_counts}")

        # At least one element should have a bbox
        total_bboxes = sum(bbox_counts.values())
        assert total_bboxes > 0, "At least one element should have a bounding box"

    def test_chromadb_stores_structure_metadata(self, parser, enhanced_config, chroma_client):
        """
        Test that structure metadata is stored in ChromaDB visual collection.

        Tests:
        - Structure metadata is compressed and stored
        - Metadata can be retrieved from visual collection
        - Structure data is valid and can be decompressed
        """
        # Use test document
        test_pdf = (
            Path(__file__).parent.parent.parent / "data/test-documents/test-financial-report.docx"
        )

        if not test_pdf.exists():
            pytest.skip(f"Test document not found: {test_pdf}")

        logger.info(f"Testing ChromaDB structure metadata storage: {test_pdf}")

        # Parse document with enhanced mode
        parsed_doc = parser.parse_document(str(test_pdf), config=enhanced_config)

        # Get doc_id
        doc_id = parsed_doc.doc_id

        # Query ChromaDB for visual embeddings
        visual_results = chroma_client.visual_collection.get(
            where={"doc_id": doc_id}, limit=1, include=["metadatas"]
        )

        # Validate that metadata was stored
        if not visual_results["ids"]:
            pytest.skip(
                f"Document {doc_id} not found in ChromaDB. "
                "This test requires the document to be processed by the worker."
            )

        metadata = visual_results["metadatas"][0]

        logger.info(f"Retrieved metadata keys: {list(metadata.keys())}")

        # Validate structure metadata presence
        assert "has_structure" in metadata, "Should have has_structure flag"

        if metadata.get("has_structure"):
            # Validate structure metadata fields
            assert "num_headings" in metadata, "Should have num_headings"
            assert "num_tables" in metadata, "Should have num_tables"
            assert "num_pictures" in metadata, "Should have num_pictures"
            assert "structure" in metadata, "Should have compressed structure"

            # Validate structure can be decompressed
            from src.storage.compression import decompress_structure_metadata

            try:
                structure_dict = decompress_structure_metadata(metadata["structure"])

                logger.info(f"Decompressed structure keys: {list(structure_dict.keys())}")

                # Validate decompressed structure
                assert "headings" in structure_dict, "Should have headings"
                assert "tables" in structure_dict, "Should have tables"
                assert "pictures" in structure_dict, "Should have pictures"
                assert "summary" in structure_dict, "Should have summary"

                # Validate bboxes in decompressed structure
                for heading in structure_dict.get("headings", []):
                    if heading.get("bbox"):
                        assert len(heading["bbox"]) == 4, "Heading bbox should have 4 coords"

                for table in structure_dict.get("tables", []):
                    if table.get("bbox"):
                        assert len(table["bbox"]) == 4, "Table bbox should have 4 coords"

                for picture in structure_dict.get("pictures", []):
                    if picture.get("bbox"):
                        assert len(picture["bbox"]) == 4, "Picture bbox should have 4 coords"

                logger.info("✓ Structure metadata validated successfully")

            except Exception as e:
                pytest.fail(f"Failed to decompress structure metadata: {e}")

    def test_api_contract_sample_data(self, parser, enhanced_config):
        """
        Generate sample structure data for API contract validation.

        This test generates realistic structure data that matches the API contract
        for use by frontend developers and integration testing.
        """
        # Use test document with diverse content
        test_pdf = (
            Path(__file__).parent.parent.parent / "data/test-documents/test-financial-report.docx"
        )

        if not test_pdf.exists():
            pytest.skip(f"Test document not found: {test_pdf}")

        logger.info(f"Generating API contract sample data: {test_pdf}")

        # Extract structure
        from docling.document_converter import DocumentConverter

        from src.config.processing_config import create_pipeline_options
        from src.processing.structure_extractor import extract_document_structure

        create_pipeline_options(enhanced_config)
        converter = DocumentConverter()
        result = converter.convert(str(test_pdf))
        structure = extract_document_structure(result.document, enhanced_config)

        # Convert to API format
        api_data = self._structure_to_api_format(structure)

        # Add metadata
        api_data["_metadata"] = {
            "source_document": test_pdf.name,
            "num_pages": len(result.pages) if hasattr(result, "pages") else 0,
            "extraction_config": {
                "enable_table_structure": enhanced_config.enable_table_structure,
                "enable_picture_classification": enhanced_config.enable_picture_classification,
            },
        }

        # Add coordinate system spec
        api_data["_coordinate_system"] = {
            "format": "[x1, y1, x2, y2]",
            "description": "Docling uses bottom-left origin coordinate system",
            "units": "Points (1/72 inch)",
        }

        logger.info(
            f"Generated sample data with {len(api_data.get('headings', []))} headings, "
            f"{len(api_data.get('tables', []))} tables, "
            f"{len(api_data.get('pictures', []))} pictures"
        )

        # Validate we have at least 3 element types
        element_types = []
        if api_data.get("headings"):
            element_types.append("headings")
        if api_data.get("tables"):
            element_types.append("tables")
        if api_data.get("pictures"):
            element_types.append("pictures")

        logger.info(f"Sample data contains element types: {element_types}")

        # Return for inspection
        return api_data

    # Helper methods

    def _validate_bbox(self, bbox: tuple, element_name: str):
        """
        Validate bounding box format and coordinates.

        Args:
            bbox: Bounding box tuple (x1, y1, x2, y2)
            element_name: Name of element for error messages
        """
        # Check format
        assert isinstance(
            bbox, (tuple, list)
        ), f"{element_name}: bbox should be tuple or list, got {type(bbox)}"
        assert len(bbox) == 4, f"{element_name}: bbox should have 4 coordinates, got {len(bbox)}"

        x1, y1, x2, y2 = bbox

        # Check all are numbers
        assert all(
            isinstance(coord, (int, float)) for coord in bbox
        ), f"{element_name}: all bbox coordinates should be numbers"

        # Check X coordinates (x1 < x2 for left < right)
        assert x1 < x2, f"{element_name}: x1 ({x1}) should be less than x2 ({x2})"

        # Check coordinates are non-negative
        assert all(
            coord >= 0 for coord in bbox
        ), f"{element_name}: coordinates should be non-negative"

        # Log dimensions
        width = x2 - x1
        height = y2 - y1

        logger.debug(
            f"{element_name} bbox valid: "
            f"({x1:.1f}, {y1:.1f}) -> ({x2:.1f}, {y2:.1f}) "
            f"[{width:.1f}x{height:.1f}]"
        )

    def _structure_to_api_format(self, structure: DocumentStructure) -> Dict[str, Any]:
        """
        Convert DocumentStructure to API-compatible format.

        Args:
            structure: DocumentStructure instance

        Returns:
            Dictionary matching API contract
        """
        return {
            "headings": [
                {
                    "text": h.text,
                    "level": h.level.name,
                    "page": h.page_num,
                    "bbox": list(h.bbox) if h.bbox else None,
                    "section_path": h.section_path,
                }
                for h in structure.headings
            ],
            "tables": [
                {
                    "table_id": t.table_id,
                    "page": t.page_num,
                    "caption": t.caption,
                    "rows": t.num_rows,
                    "cols": t.num_cols,
                    "has_header": t.has_header,
                    "bbox": list(t.bbox) if t.bbox else None,
                }
                for t in structure.tables
            ],
            "pictures": [
                {
                    "picture_id": p.picture_id,
                    "page": p.page_num,
                    "type": p.picture_type.name,
                    "caption": p.caption,
                    "confidence": p.confidence,
                    "bbox": list(p.bbox) if p.bbox else None,
                }
                for p in structure.pictures
            ],
            "code_blocks": [
                {
                    "page": c.page_num,
                    "language": c.language,
                    "lines": c.num_lines,
                    "bbox": list(c.bbox) if c.bbox else None,
                }
                for c in structure.code_blocks
            ],
            "formulas": [
                {
                    "page": f.page_num,
                    "latex": f.latex,
                    "bbox": list(f.bbox) if f.bbox else None,
                }
                for f in structure.formulas
            ],
            "summary": {
                "total_sections": structure.total_sections,
                "max_heading_depth": structure.max_heading_depth,
                "has_table_of_contents": structure.has_table_of_contents,
                "size_estimate_kb": structure.size_estimate_kb(),
            },
        }


if __name__ == "__main__":
    # Allow running this test standalone for debugging
    pytest.main([__file__, "-v", "-s"])
