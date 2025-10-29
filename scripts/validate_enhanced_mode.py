#!/usr/bin/env python3
"""
Validation script for Enhanced Mode structure extraction.

This script processes a sample document through the full pipeline and validates
that structure metadata with bounding boxes is correctly extracted and stored.

Usage:
    python scripts/validate_enhanced_mode.py [document_path]

If no document path is provided, uses test documents from data/test-documents/.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# noqa: E402 - imports after path modification
from docling.document_converter import DocumentConverter  # noqa: E402

from src.config.processing_config import EnhancedModeConfig  # noqa: E402
from src.processing.docling_parser import DoclingParser  # noqa: E402
from src.processing.structure_extractor import extract_document_structure  # noqa: E402
from src.storage.chroma_client import ChromaClient  # noqa: E402
from src.storage.compression import decompress_structure_metadata  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EnhancedModeValidator:
    """Validator for enhanced mode structure extraction."""

    def __init__(self):
        """Initialize validator."""
        self.parser = DoclingParser(render_dpi=150)
        self.config = EnhancedModeConfig(
            enable_table_structure=True,
            enable_picture_classification=True,
            enable_code_enrichment=False,
            enable_formula_enrichment=False,
        )
        self.chroma_client: Optional[ChromaClient] = None

    def validate_document(self, document_path: str) -> Dict[str, Any]:
        """
        Validate structure extraction for a document.

        Args:
            document_path: Path to document to validate

        Returns:
            Validation results dictionary
        """
        doc_path = Path(document_path)
        if not doc_path.exists():
            raise FileNotFoundError(f"Document not found: {document_path}")

        separator = "=" * 80
        logger.info(f"{separator}")
        logger.info("Validating Enhanced Mode Structure Extraction")
        logger.info(f"Document: {doc_path.name}")
        logger.info(f"{separator}")

        results = {
            "document": str(doc_path),
            "filename": doc_path.name,
            "parsing": {},
            "structure_extraction": {},
            "bbox_validation": {},
            "chromadb_storage": {},
            "summary": {},
        }

        # Step 1: Parse document
        logger.info("\n[1/4] Parsing document with enhanced mode...")
        try:
            parsed_doc = self.parser.parse_document(str(doc_path), config=self.config)
            results["parsing"]["status"] = "SUCCESS"
            results["parsing"]["num_pages"] = parsed_doc.num_pages
            results["parsing"]["num_chunks"] = len(parsed_doc.text_chunks)
            num_chunks = len(parsed_doc.text_chunks)
            logger.info(f"✓ Parsed successfully: {parsed_doc.num_pages} pages, {num_chunks} chunks")
        except Exception as e:
            results["parsing"]["status"] = "FAILED"
            results["parsing"]["error"] = str(e)
            logger.error(f"✗ Parsing failed: {e}")
            return results

        # Step 2: Extract structure directly
        logger.info("\n[2/4] Extracting document structure...")
        try:
            from src.config.processing_config import create_pipeline_options

            create_pipeline_options(self.config)
            converter = DocumentConverter()
            result = converter.convert(str(doc_path))
            structure = extract_document_structure(result.document, self.config)

            results["structure_extraction"]["status"] = "SUCCESS"
            results["structure_extraction"]["num_headings"] = len(structure.headings)
            results["structure_extraction"]["num_tables"] = len(structure.tables)
            results["structure_extraction"]["num_pictures"] = len(structure.pictures)
            results["structure_extraction"]["num_code_blocks"] = len(structure.code_blocks)
            results["structure_extraction"]["num_formulas"] = len(structure.formulas)
            results["structure_extraction"]["max_heading_depth"] = structure.max_heading_depth
            results["structure_extraction"]["has_toc"] = structure.has_table_of_contents
            results["structure_extraction"]["size_kb"] = structure.size_estimate_kb()

            num_headings = len(structure.headings)
            num_tables = len(structure.tables)
            num_pictures = len(structure.pictures)
            num_code_blocks = len(structure.code_blocks)
            num_formulas = len(structure.formulas)
            logger.info("✓ Structure extracted:")
            logger.info(f"  - {num_headings} headings")
            logger.info(f"  - {num_tables} tables")
            logger.info(f"  - {num_pictures} pictures")
            logger.info(f"  - {num_code_blocks} code blocks")
            logger.info(f"  - {num_formulas} formulas")
        except Exception as e:
            results["structure_extraction"]["status"] = "FAILED"
            results["structure_extraction"]["error"] = str(e)
            logger.error(f"✗ Structure extraction failed: {e}")
            return results

        # Step 3: Validate bounding boxes
        logger.info("\n[3/4] Validating bounding boxes...")
        try:
            bbox_stats = self._validate_bboxes(structure)
            results["bbox_validation"]["status"] = "SUCCESS"
            results["bbox_validation"]["stats"] = bbox_stats

            logger.info("✓ Bounding boxes validated:")
            for element_type, count in bbox_stats.items():
                logger.info(f"  - {element_type}: {count} with bboxes")
        except Exception as e:
            results["bbox_validation"]["status"] = "FAILED"
            results["bbox_validation"]["error"] = str(e)
            logger.error(f"✗ Bbox validation failed: {e}")

        # Step 4: Check ChromaDB storage (optional)
        logger.info("\n[4/4] Checking ChromaDB storage...")
        try:
            storage_results = self._check_chromadb_storage(parsed_doc.doc_id)
            results["chromadb_storage"] = storage_results

            if storage_results["status"] == "SUCCESS":
                has_structure = storage_results.get("has_structure", False)
                logger.info("✓ ChromaDB storage validated:")
                logger.info(f"  - Structure stored: {has_structure}")
                if storage_results.get("has_structure"):
                    logger.info(
                        f"  - Decompression: {storage_results.get('decompression_status', 'N/A')}"
                    )
            else:
                logger.warning(
                    f"⚠ ChromaDB validation skipped: {storage_results.get('message', 'Unknown')}"
                )
        except Exception as e:
            results["chromadb_storage"]["status"] = "SKIPPED"
            results["chromadb_storage"]["message"] = f"Error: {e}"
            logger.warning(f"⚠ ChromaDB check skipped: {e}")

        # Generate summary
        results["summary"] = self._generate_summary(results)

        separator = "=" * 80
        logger.info(f"\n{separator}")
        logger.info("Validation Summary")
        logger.info(f"{separator}")
        logger.info(f"Overall Status: {results['summary']['overall_status']}")
        logger.info(
            f"Tests Passed: {results['summary']['tests_passed']}/{results['summary']['tests_total']}"
        )
        logger.info(f"{separator}\n")

        return results

    def _validate_bboxes(self, structure) -> Dict[str, int]:
        """
        Validate bounding boxes in structure.

        Args:
            structure: DocumentStructure instance

        Returns:
            Dictionary with bbox counts per element type
        """
        bbox_stats = {
            "headings": 0,
            "tables": 0,
            "pictures": 0,
            "code_blocks": 0,
            "formulas": 0,
        }

        # Validate headings
        for heading in structure.headings:
            if heading.bbox is not None:
                self._validate_bbox_format(heading.bbox, f"Heading '{heading.text}'")
                bbox_stats["headings"] += 1

        # Validate tables
        for table in structure.tables:
            if table.bbox is not None:
                self._validate_bbox_format(table.bbox, f"Table {table.table_id}")
                bbox_stats["tables"] += 1

        # Validate pictures
        for picture in structure.pictures:
            if picture.bbox is not None:
                self._validate_bbox_format(picture.bbox, f"Picture {picture.picture_id}")
                bbox_stats["pictures"] += 1

        # Validate code blocks
        for code in structure.code_blocks:
            if code.bbox is not None:
                self._validate_bbox_format(code.bbox, "Code block")
                bbox_stats["code_blocks"] += 1

        # Validate formulas
        for formula in structure.formulas:
            if formula.bbox is not None:
                self._validate_bbox_format(formula.bbox, "Formula")
                bbox_stats["formulas"] += 1

        return bbox_stats

    def _validate_bbox_format(self, bbox: tuple, element_name: str):
        """
        Validate bbox format [x1, y1, x2, y2].

        Args:
            bbox: Bounding box tuple
            element_name: Element name for errors

        Raises:
            ValueError: If bbox format is invalid
        """
        if not isinstance(bbox, (tuple, list)):
            raise ValueError(f"{element_name}: bbox must be tuple or list, got {type(bbox)}")

        if len(bbox) != 4:
            raise ValueError(f"{element_name}: bbox must have 4 coordinates, got {len(bbox)}")

        x1, y1, x2, y2 = bbox

        if not all(isinstance(c, (int, float)) for c in bbox):
            raise ValueError(f"{element_name}: all bbox coordinates must be numbers")

        if x1 >= x2:
            raise ValueError(f"{element_name}: x1 ({x1}) must be less than x2 ({x2})")

        if any(c < 0 for c in bbox):
            raise ValueError(f"{element_name}: all coordinates must be non-negative")

    def _check_chromadb_storage(self, doc_id: str) -> Dict[str, Any]:
        """
        Check if structure metadata is stored in ChromaDB.

        Args:
            doc_id: Document ID to check

        Returns:
            Storage validation results
        """
        # Try to connect to ChromaDB
        if self.chroma_client is None:
            try:
                self.chroma_client = ChromaClient(host="chromadb", port=8001)
                if not self.chroma_client.heartbeat():
                    return {"status": "SKIPPED", "message": "ChromaDB not responding"}
            except Exception as e:
                return {"status": "SKIPPED", "message": f"ChromaDB connection failed: {e}"}

        # Query for document
        try:
            visual_results = self.chroma_client.visual_collection.get(
                where={"doc_id": doc_id}, limit=1, include=["metadatas"]
            )

            if not visual_results["ids"]:
                return {
                    "status": "SKIPPED",
                    "message": f"Document {doc_id} not found in ChromaDB (not yet processed by worker)",
                }

            metadata = visual_results["metadatas"][0]

            # Check for structure metadata
            has_structure = metadata.get("has_structure", False)

            result = {
                "status": "SUCCESS",
                "has_structure": has_structure,
            }

            if has_structure:
                # Try to decompress structure
                try:
                    structure_dict = decompress_structure_metadata(metadata["structure"])
                    result["decompression_status"] = "SUCCESS"
                    result["decompressed_keys"] = list(structure_dict.keys())
                except Exception as e:
                    result["decompression_status"] = "FAILED"
                    result["decompression_error"] = str(e)

            return result

        except Exception as e:
            return {"status": "FAILED", "error": str(e)}

    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate validation summary.

        Args:
            results: Validation results

        Returns:
            Summary dictionary
        """
        tests = [
            ("parsing", results["parsing"].get("status")),
            ("structure_extraction", results["structure_extraction"].get("status")),
            ("bbox_validation", results["bbox_validation"].get("status")),
        ]

        # ChromaDB is optional
        if results["chromadb_storage"].get("status") in ["SUCCESS", "FAILED"]:
            tests.append(("chromadb_storage", results["chromadb_storage"]["status"]))

        passed = sum(1 for _, status in tests if status == "SUCCESS")
        total = len(tests)

        overall_status = "PASS" if passed == total else "PARTIAL" if passed > 0 else "FAIL"

        return {
            "overall_status": overall_status,
            "tests_passed": passed,
            "tests_total": total,
            "tests": dict(tests),
        }


def main():
    """Run validation script for enhanced mode structure extraction."""
    # Parse arguments
    if len(sys.argv) > 1:
        document_path = sys.argv[1]
    else:
        # Use default test document
        test_docs_dir = project_root / "data/test-documents"
        if test_docs_dir.exists():
            # Find first available test document
            test_files = (
                list(test_docs_dir.glob("*.pdf"))
                + list(test_docs_dir.glob("*.docx"))
                + list(test_docs_dir.glob("*.pptx"))
            )
            if test_files:
                document_path = str(test_files[0])
            else:
                logger.error("No test documents found in data/test-documents/")
                sys.exit(1)
        else:
            logger.error(
                "Please provide a document path or add test documents to data/test-documents/"
            )
            sys.exit(1)

    # Run validation
    validator = EnhancedModeValidator()
    try:
        results = validator.validate_document(document_path)

        # Save results to JSON
        output_path = project_root / "integration-contracts/validation-results.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Validation results saved to: {output_path}")

        # Exit with appropriate code
        if results["summary"]["overall_status"] == "PASS":
            sys.exit(0)
        elif results["summary"]["overall_status"] == "PARTIAL":
            sys.exit(2)
        else:
            sys.exit(1)

    except Exception as e:
        logger.error(f"Validation failed with error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
