#!/usr/bin/env python3
"""
Validate enhanced mode migration.

This script validates that migration completed successfully by checking:
  - All documents have metadata_version field
  - Enhanced documents have has_structure=true
  - Structure data decompresses correctly
  - Chunk metadata includes required fields
  - Bounding boxes are valid

Usage:
    # Full validation
    python scripts/validate_migration.py

    # Count documents only
    python scripts/validate_migration.py --count-documents

    # Validate specific document
    python scripts/validate_migration.py --doc-id doc_12345

    # Generate report
    python scripts/validate_migration.py --report validation_report.txt
"""

import argparse
import gzip
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from storage.chroma_client import ChromaClient
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure to run from project root and have all dependencies installed.")
    sys.exit(1)

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of a validation check."""

    def __init__(self, name: str, passed: bool, message: str = "", details: Optional[Dict] = None):
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details or {}

    def __repr__(self):
        status = "✓ PASS" if self.passed else "✗ FAIL"
        msg = f": {self.message}" if self.message else ""
        return f"{status} - {self.name}{msg}"


class ValidationReport:
    """Collection of validation results."""

    def __init__(self):
        self.results: List[ValidationResult] = []
        self.stats = {
            "total_checks": 0,
            "passed": 0,
            "failed": 0,
            "total_documents": 0,
            "enhanced_documents": 0,
            "legacy_documents": 0,
        }

    def add_result(self, result: ValidationResult):
        """Add validation result."""
        self.results.append(result)
        self.stats["total_checks"] += 1

        if result.passed:
            self.stats["passed"] += 1
        else:
            self.stats["failed"] += 1

    def is_valid(self) -> bool:
        """Check if all validations passed."""
        return self.stats["failed"] == 0

    def summary(self) -> str:
        """Generate summary report."""
        return f"""
Validation Summary
{'=' * 70}
Total Checks:        {self.stats['total_checks']}
Passed:              {self.stats['passed']} ✓
Failed:              {self.stats['failed']} ✗

Document Statistics:
Total Documents:     {self.stats['total_documents']}
Enhanced (v1.0):     {self.stats['enhanced_documents']}
Legacy (v0.0):       {self.stats['legacy_documents']}

Status: {'✓ ALL CHECKS PASSED' if self.is_valid() else '✗ VALIDATION FAILED'}
"""

    def detailed_report(self) -> str:
        """Generate detailed validation report."""
        lines = ["Detailed Validation Report", "=" * 70, ""]

        # Group results by category
        categories = defaultdict(list)
        for result in self.results:
            category = result.name.split(":")[0] if ":" in result.name else "General"
            categories[category].append(result)

        # Print each category
        for category, results in sorted(categories.items()):
            lines.append(f"\n{category}")
            lines.append("-" * 70)

            for result in results:
                lines.append(str(result))

                if result.details:
                    for key, value in result.details.items():
                        lines.append(f"    {key}: {value}")

        lines.append("\n")
        lines.append(self.summary())

        return "\n".join(lines)


class MigrationValidator:
    """Validate enhanced mode migration."""

    def __init__(self):
        self.chroma_client = ChromaClient()
        self.report = ValidationReport()

    def validate_all(self) -> ValidationReport:
        """Run all validation checks."""
        logger.info("Starting validation...")

        # Document-level validations
        self.validate_metadata_versions()
        self.validate_enhanced_documents()
        self.validate_chunk_metadata()

        # Structure-level validations
        self.validate_structure_compression()
        self.validate_bounding_boxes()

        # Summary
        logger.info("Validation complete")
        return self.report

    def validate_metadata_versions(self):
        """Check that all documents have metadata_version field."""
        logger.info("Validating metadata versions...")

        try:
            # Get all documents
            visual_collection = self.chroma_client.get_collection("visual_embeddings")
            results = visual_collection.get()

            if not results or not results.get("metadatas"):
                self.report.add_result(
                    ValidationResult(
                        "Metadata Versions: No documents found",
                        False,
                        "ChromaDB returned no documents",
                    )
                )
                return

            metadatas = results["metadatas"]
            self.report.stats["total_documents"] = len(set(m.get("doc_id") for m in metadatas))

            # Check each document
            missing_version = []
            version_counts = defaultdict(int)

            for metadata in metadatas:
                doc_id = metadata.get("doc_id", "unknown")
                version = metadata.get("metadata_version")

                if not version:
                    missing_version.append(doc_id)
                else:
                    version_counts[version] += 1

            # Update stats
            self.report.stats["enhanced_documents"] = version_counts.get("1.0", 0)
            self.report.stats["legacy_documents"] = version_counts.get("0.0", 0)

            # Report results
            if missing_version:
                self.report.add_result(
                    ValidationResult(
                        "Metadata Versions: Missing version field",
                        False,
                        f"{len(missing_version)} chunks missing metadata_version",
                        {"sample_doc_ids": missing_version[:5]},
                    )
                )
            else:
                self.report.add_result(
                    ValidationResult(
                        "Metadata Versions: All chunks versioned",
                        True,
                        f"All chunks have metadata_version field",
                        {"version_distribution": dict(version_counts)},
                    )
                )

        except Exception as e:
            self.report.add_result(
                ValidationResult("Metadata Versions: Validation error", False, str(e))
            )

    def validate_enhanced_documents(self):
        """Verify enhanced documents have correct metadata."""
        logger.info("Validating enhanced documents...")

        try:
            visual_collection = self.chroma_client.get_collection("visual_embeddings")
            results = visual_collection.get(where={"metadata_version": "1.0"})

            if not results or not results.get("metadatas"):
                self.report.add_result(
                    ValidationResult(
                        "Enhanced Documents: No enhanced documents found",
                        True,
                        "No documents with metadata_version=1.0 (OK if no migration yet)",
                    )
                )
                return

            metadatas = results["metadatas"]

            # Check required fields
            missing_fields = defaultdict(list)
            required_fields = ["has_structure", "element_id", "element_type", "page"]

            for metadata in metadatas:
                doc_id = metadata.get("doc_id", "unknown")

                for field in required_fields:
                    if field not in metadata:
                        missing_fields[field].append(doc_id)

            # Report results
            if missing_fields:
                for field, doc_ids in missing_fields.items():
                    self.report.add_result(
                        ValidationResult(
                            f"Enhanced Documents: Missing {field} field",
                            False,
                            f"{len(doc_ids)} enhanced chunks missing {field}",
                            {"sample_doc_ids": doc_ids[:5]},
                        )
                    )
            else:
                self.report.add_result(
                    ValidationResult(
                        "Enhanced Documents: All required fields present",
                        True,
                        f"All {len(metadatas)} enhanced chunks have required fields",
                    )
                )

        except Exception as e:
            self.report.add_result(
                ValidationResult("Enhanced Documents: Validation error", False, str(e))
            )

    def validate_chunk_metadata(self):
        """Validate chunk-level metadata integrity."""
        logger.info("Validating chunk metadata...")

        try:
            # Get enhanced chunks
            visual_collection = self.chroma_client.get_collection("visual_embeddings")
            results = visual_collection.get(where={"has_structure": True}, limit=1000)  # Sample

            if not results or not results.get("metadatas"):
                self.report.add_result(
                    ValidationResult(
                        "Chunk Metadata: No enhanced chunks found",
                        True,
                        "No chunks with has_structure=true",
                    )
                )
                return

            metadatas = results["metadatas"]

            # Validate chunk IDs
            invalid_chunk_ids = []
            for metadata in metadatas:
                chunk_id = metadata.get("chunk_id")
                if not chunk_id or not chunk_id.startswith("chunk_"):
                    invalid_chunk_ids.append(chunk_id or "missing")

            if invalid_chunk_ids:
                self.report.add_result(
                    ValidationResult(
                        "Chunk Metadata: Invalid chunk IDs",
                        False,
                        f"{len(invalid_chunk_ids)} chunks have invalid IDs",
                        {"sample_invalid_ids": invalid_chunk_ids[:5]},
                    )
                )
            else:
                self.report.add_result(
                    ValidationResult(
                        "Chunk Metadata: Valid chunk IDs",
                        True,
                        f"All {len(metadatas)} chunks have valid IDs",
                    )
                )

            # Validate page numbers
            invalid_pages = []
            for metadata in metadatas:
                page = metadata.get("page")
                if not isinstance(page, int) or page < 1:
                    doc_id = metadata.get("doc_id", "unknown")
                    invalid_pages.append(f"{doc_id} (page={page})")

            if invalid_pages:
                self.report.add_result(
                    ValidationResult(
                        "Chunk Metadata: Invalid page numbers",
                        False,
                        f"{len(invalid_pages)} chunks have invalid pages",
                        {"sample_invalid": invalid_pages[:5]},
                    )
                )
            else:
                self.report.add_result(
                    ValidationResult(
                        "Chunk Metadata: Valid page numbers",
                        True,
                        f"All chunks have valid page numbers (≥1)",
                    )
                )

        except Exception as e:
            self.report.add_result(
                ValidationResult("Chunk Metadata: Validation error", False, str(e))
            )

    def validate_structure_compression(self):
        """Test that structure data decompresses correctly."""
        logger.info("Validating structure compression...")

        try:
            # Check if structure cache exists
            structure_cache_dir = Path(__file__).parent.parent / "data" / "structure_cache"

            if not structure_cache_dir.exists():
                self.report.add_result(
                    ValidationResult(
                        "Structure Compression: Cache directory missing",
                        True,
                        "No structure cache directory (OK if no enhanced docs)",
                    )
                )
                return

            # Test decompression of cached structures
            cache_files = list(structure_cache_dir.glob("*.gz"))

            if not cache_files:
                self.report.add_result(
                    ValidationResult(
                        "Structure Compression: No cached structures",
                        True,
                        "Cache directory empty (OK if no enhanced docs)",
                    )
                )
                return

            decompression_errors = []
            successful = 0

            for cache_file in cache_files[:10]:  # Sample first 10
                try:
                    with gzip.open(cache_file, "rb") as f:
                        data = f.read()
                        json.loads(data)  # Verify JSON is valid
                    successful += 1
                except Exception as e:
                    decompression_errors.append(f"{cache_file.name}: {str(e)}")

            if decompression_errors:
                self.report.add_result(
                    ValidationResult(
                        "Structure Compression: Decompression errors",
                        False,
                        f"{len(decompression_errors)} files failed to decompress",
                        {"errors": decompression_errors},
                    )
                )
            else:
                self.report.add_result(
                    ValidationResult(
                        "Structure Compression: All structures valid",
                        True,
                        f"Successfully decompressed {successful} cached structures",
                    )
                )

        except Exception as e:
            self.report.add_result(
                ValidationResult("Structure Compression: Validation error", False, str(e))
            )

    def validate_bounding_boxes(self):
        """Validate bounding box coordinates."""
        logger.info("Validating bounding boxes...")

        try:
            # Get chunks with bounding boxes
            visual_collection = self.chroma_client.get_collection("visual_embeddings")
            results = visual_collection.get(where={"has_structure": True}, limit=1000)  # Sample

            if not results or not results.get("metadatas"):
                self.report.add_result(
                    ValidationResult(
                        "Bounding Boxes: No bboxes found",
                        True,
                        "No chunks with bboxes (OK if no enhanced docs)",
                    )
                )
                return

            metadatas = results["metadatas"]

            # Validate bbox format and values
            invalid_bboxes = []

            for metadata in metadatas:
                bbox_str = metadata.get("bbox")

                if not bbox_str:
                    continue  # Skip chunks without bboxes

                try:
                    # Parse bbox (stored as "left,bottom,right,top")
                    bbox = self._parse_bbox(bbox_str)

                    # Validate bbox values
                    if not self._is_valid_bbox(bbox):
                        doc_id = metadata.get("doc_id", "unknown")
                        invalid_bboxes.append(f"{doc_id}: {bbox_str}")

                except Exception as e:
                    doc_id = metadata.get("doc_id", "unknown")
                    invalid_bboxes.append(f"{doc_id}: parse error - {str(e)}")

            if invalid_bboxes:
                self.report.add_result(
                    ValidationResult(
                        "Bounding Boxes: Invalid bboxes",
                        False,
                        f"{len(invalid_bboxes)} chunks have invalid bboxes",
                        {"sample_invalid": invalid_bboxes[:5]},
                    )
                )
            else:
                self.report.add_result(
                    ValidationResult(
                        "Bounding Boxes: All bboxes valid",
                        True,
                        f"All bboxes have valid coordinates",
                    )
                )

        except Exception as e:
            self.report.add_result(
                ValidationResult("Bounding Boxes: Validation error", False, str(e))
            )

    def validate_document(self, doc_id: str) -> ValidationReport:
        """Validate a specific document."""
        logger.info(f"Validating document: {doc_id}")

        try:
            # Get document metadata
            visual_collection = self.chroma_client.get_collection("visual_embeddings")
            results = visual_collection.get(where={"doc_id": doc_id})

            if not results or not results.get("metadatas"):
                self.report.add_result(
                    ValidationResult(
                        f"Document {doc_id}: Not found",
                        False,
                        "Document does not exist in ChromaDB",
                    )
                )
                return self.report

            metadatas = results["metadatas"]

            # Check metadata version
            version = metadatas[0].get("metadata_version", "unknown")
            has_structure = metadatas[0].get("has_structure", False)

            self.report.add_result(
                ValidationResult(
                    f"Document {doc_id}: Metadata version",
                    version in ["0.0", "1.0"],
                    f"Version: {version}, Has structure: {has_structure}",
                )
            )

            # If enhanced, validate structure
            if version == "1.0" and has_structure:
                # Check for required fields
                required_fields = ["element_id", "element_type", "page"]
                missing = [f for f in required_fields if f not in metadatas[0]]

                if missing:
                    self.report.add_result(
                        ValidationResult(
                            f"Document {doc_id}: Missing fields",
                            False,
                            f"Missing: {', '.join(missing)}",
                        )
                    )
                else:
                    self.report.add_result(
                        ValidationResult(
                            f"Document {doc_id}: All fields present",
                            True,
                            "Enhanced metadata complete",
                        )
                    )

            logger.info(f"Document {doc_id} validation complete")

        except Exception as e:
            self.report.add_result(
                ValidationResult(f"Document {doc_id}: Validation error", False, str(e))
            )

        return self.report

    def count_documents(self) -> Dict[str, int]:
        """Count documents by status."""
        try:
            visual_collection = self.chroma_client.get_collection("visual_embeddings")
            results = visual_collection.get()

            if not results or not results.get("metadatas"):
                return {"total": 0, "enhanced": 0, "legacy": 0, "unversioned": 0}

            # Count unique documents
            docs_by_version = defaultdict(set)

            for metadata in results["metadatas"]:
                doc_id = metadata.get("doc_id")
                version = metadata.get("metadata_version", "unversioned")
                docs_by_version[version].add(doc_id)

            return {
                "total": len(set(m.get("doc_id") for m in results["metadatas"])),
                "enhanced": len(docs_by_version.get("1.0", set())),
                "legacy": len(docs_by_version.get("0.0", set())),
                "unversioned": len(docs_by_version.get("unversioned", set())),
            }

        except Exception as e:
            logger.error(f"Failed to count documents: {e}")
            return {"error": str(e)}

    def _parse_bbox(self, bbox_str: str) -> Dict[str, float]:
        """Parse bbox string to dict."""
        if isinstance(bbox_str, dict):
            return bbox_str

        # Parse "left,bottom,right,top" format
        parts = bbox_str.split(",")
        if len(parts) != 4:
            raise ValueError(f"Invalid bbox format: {bbox_str}")

        return {
            "left": float(parts[0]),
            "bottom": float(parts[1]),
            "right": float(parts[2]),
            "top": float(parts[3]),
        }

    def _is_valid_bbox(self, bbox: Dict[str, float]) -> bool:
        """Check if bbox coordinates are valid."""
        # Check ordering
        if bbox["left"] >= bbox["right"]:
            return False
        if bbox["bottom"] >= bbox["top"]:
            return False

        # Check non-negative
        if any(v < 0 for v in bbox.values()):
            return False

        # Check reasonable bounds (typical PDF page is ~600-1000pt)
        if bbox["right"] > 10000 or bbox["top"] > 10000:
            return False

        return True


def main():
    """Main validation entry point."""
    parser = argparse.ArgumentParser(
        description="Validate enhanced mode migration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--doc-id", type=str, help="Validate specific document by ID")

    parser.add_argument(
        "--count-documents", action="store_true", help="Count documents by migration status"
    )

    parser.add_argument("--report", type=str, help="Save detailed report to file")

    args = parser.parse_args()

    # Create validator
    validator = MigrationValidator()

    try:
        if args.count_documents:
            # Just count documents
            counts = validator.count_documents()
            print("\nDocument Count")
            print("=" * 40)
            for key, value in counts.items():
                print(f"{key.capitalize():15} {value}")
            return

        # Run validation
        if args.doc_id:
            report = validator.validate_document(args.doc_id)
        else:
            report = validator.validate_all()

        # Print summary
        print(report.summary())

        # Save detailed report if requested
        if args.report:
            with open(args.report, "w") as f:
                f.write(report.detailed_report())
            logger.info(f"Detailed report saved to {args.report}")
        else:
            # Print detailed report to console
            print("\n" + report.detailed_report())

        # Exit with appropriate code
        sys.exit(0 if report.is_valid() else 1)

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
