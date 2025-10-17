"""
Collection lifecycle management for ChromaDB.

This module provides utilities for managing ChromaDB collections,
including initialization, reset, backup, and maintenance operations.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .chroma_client import ChromaClient, StorageError

# Configure logging
logger = logging.getLogger(__name__)


class CollectionManager:
    """Manage ChromaDB collection lifecycle operations.

    Provides utilities for:
    - Collection initialization and validation
    - Collection reset and cleanup
    - Collection metadata management
    - Health checks and diagnostics
    """

    def __init__(self, client: ChromaClient):
        """Initialize collection manager.

        Args:
            client: Initialized ChromaClient instance
        """
        self.client = client
        logger.info("CollectionManager initialized")

    def validate_collections(self) -> Dict[str, Any]:
        """Validate collection setup and health.

        Returns:
            Validation report with status and issues:
            {
                "status": "healthy" | "degraded" | "unhealthy",
                "visual_collection": {
                    "exists": bool,
                    "count": int,
                    "issues": List[str]
                },
                "text_collection": {
                    "exists": bool,
                    "count": int,
                    "issues": List[str]
                },
                "issues": List[str],
                "timestamp": str
            }
        """
        report: Dict[str, Any] = {
            "status": "healthy",
            "visual_collection": {"exists": False, "count": 0, "issues": []},
            "text_collection": {"exists": False, "count": 0, "issues": []},
            "issues": [],
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            # Check visual collection
            visual_count = self.client._visual_collection.count()
            report["visual_collection"]["exists"] = True
            report["visual_collection"]["count"] = visual_count

            # Check text collection
            text_count = self.client._text_collection.count()
            report["text_collection"]["exists"] = True
            report["text_collection"]["count"] = text_count

            # Validate metadata structure on sample documents
            if visual_count > 0:
                visual_sample = self.client._visual_collection.get(limit=1, include=["metadatas"])
                if visual_sample["metadatas"]:
                    issues = self._validate_metadata(visual_sample["metadatas"][0], "visual")
                    report["visual_collection"]["issues"].extend(issues)

            if text_count > 0:
                text_sample = self.client._text_collection.get(limit=1, include=["metadatas"])
                if text_sample["metadatas"]:
                    issues = self._validate_metadata(text_sample["metadatas"][0], "text")
                    report["text_collection"]["issues"].extend(issues)

            # Determine overall status
            all_issues = report["visual_collection"]["issues"] + report["text_collection"]["issues"]
            if all_issues:
                report["status"] = "degraded"
                report["issues"] = all_issues

            logger.info(f"Collection validation: {report['status']}")

        except Exception as e:
            report["status"] = "unhealthy"
            report["issues"].append(f"Validation failed: {str(e)}")
            logger.error(f"Collection validation failed: {str(e)}")

        return report

    def _validate_metadata(self, metadata: Dict[str, Any], collection_type: str) -> List[str]:
        """Validate metadata structure.

        Args:
            metadata: Metadata dict to validate
            collection_type: "visual" or "text"

        Returns:
            List of validation issues (empty if valid)
        """
        issues = []

        # Common required fields
        common_required = [
            "doc_id",
            "type",
            "full_embeddings",
            "seq_length",
            "embedding_shape",
            "timestamp",
            "filename",
            "source_path",
        ]

        for field in common_required:
            if field not in metadata:
                issues.append(f"Missing required field: {field}")

        # Type-specific fields
        if collection_type == "visual":
            if "page" not in metadata:
                issues.append("Missing required field: page")
        elif collection_type == "text":
            if "chunk_id" not in metadata:
                issues.append("Missing required field: chunk_id")
            if "page" not in metadata:
                issues.append("Missing required field: page")

        # Validate type field
        if metadata.get("type") != collection_type:
            issues.append(
                f"Type mismatch: expected '{collection_type}', " f"got '{metadata.get('type')}'"
            )

        return issues

    def reset_collection(self, collection: str, confirm: bool = False) -> Dict[str, Any]:
        """Reset a collection (delete all data).

        Args:
            collection: "visual", "text", or "all"
            confirm: Must be True to proceed (safety check)

        Returns:
            Reset report:
            {
                "status": "success" | "failed",
                "collections_reset": List[str],
                "items_deleted": int,
                "timestamp": str
            }

        Raises:
            ValueError: If confirm is False
            StorageError: If reset fails
        """
        if not confirm:
            raise ValueError("Reset requires explicit confirmation (confirm=True)")

        report = {
            "status": "success",
            "collections_reset": [],
            "items_deleted": 0,
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            if collection in ["visual", "all"]:
                visual_count = self.client._visual_collection.count()
                if visual_count > 0:
                    # Delete all items
                    all_ids = self.client._visual_collection.get(include=[])["ids"]
                    self.client._visual_collection.delete(ids=all_ids)
                    report["collections_reset"].append("visual")
                    report["items_deleted"] += visual_count
                    logger.info(f"Reset visual collection: {visual_count} items deleted")

            if collection in ["text", "all"]:
                text_count = self.client._text_collection.count()
                if text_count > 0:
                    # Delete all items
                    all_ids = self.client._text_collection.get(include=[])["ids"]
                    self.client._text_collection.delete(ids=all_ids)
                    report["collections_reset"].append("text")
                    report["items_deleted"] += text_count
                    logger.info(f"Reset text collection: {text_count} items deleted")

            logger.info(f"Collection reset complete: {report['items_deleted']} items deleted")

        except Exception as e:
            report["status"] = "failed"
            report["error"] = str(e)
            logger.error(f"Collection reset failed: {str(e)}")
            raise StorageError(f"Collection reset failed: {str(e)}") from e

        return report

    def get_document_list(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get list of all documents with metadata.

        Args:
            limit: Optional limit on number of documents

        Returns:
            List of document summaries:
            [
                {
                    "doc_id": str,
                    "filename": str,
                    "visual_pages": int,
                    "text_chunks": int,
                    "timestamp": str,
                    "source_path": str
                },
                ...
            ]
        """
        try:
            # Get all visual embeddings (one per page)
            visual_results = self.client._visual_collection.get(include=["metadatas"])

            # Group by doc_id
            doc_map: Dict[str, Dict[str, Any]] = {}

            for metadata in visual_results["metadatas"] or []:
                doc_id = metadata.get("doc_id")
                if not doc_id:
                    continue

                if doc_id not in doc_map:
                    doc_map[doc_id] = {
                        "doc_id": doc_id,
                        "filename": metadata.get("filename", "unknown"),
                        "visual_pages": 0,
                        "text_chunks": 0,
                        "timestamp": metadata.get("timestamp", ""),
                        "source_path": metadata.get("source_path", ""),
                    }

                doc_map[doc_id]["visual_pages"] += 1

            # Get text chunk counts
            text_results = self.client._text_collection.get(include=["metadatas"])

            for metadata in text_results["metadatas"] or []:
                doc_id = metadata.get("doc_id")
                if doc_id and doc_id in doc_map:
                    doc_map[doc_id]["text_chunks"] += 1

            # Convert to list and sort by timestamp (newest first)
            documents = sorted(doc_map.values(), key=lambda x: x["timestamp"], reverse=True)

            # Apply limit if specified
            if limit:
                documents = documents[:limit]

            logger.info(f"Retrieved {len(documents)} documents")

            return documents

        except Exception as e:
            error_msg = f"Failed to get document list: {str(e)}"
            logger.error(error_msg)
            raise StorageError(error_msg) from e

    def get_orphaned_embeddings(self) -> Dict[str, List[str]]:
        """Find embeddings with missing or invalid metadata.

        Returns:
            Report of orphaned embeddings:
            {
                "visual_orphans": List[str],  # IDs of orphaned visual embeddings
                "text_orphans": List[str],    # IDs of orphaned text embeddings
                "count": int
            }
        """
        orphans = {"visual_orphans": [], "text_orphans": [], "count": 0}

        try:
            # Check visual collection
            visual_results = self.client._visual_collection.get(include=["metadatas"])

            for i, metadata in enumerate(visual_results["metadatas"] or []):
                issues = self._validate_metadata(metadata, "visual")
                if issues:
                    embedding_id = visual_results["ids"][i]
                    orphans["visual_orphans"].append(embedding_id)
                    orphans["count"] += 1

            # Check text collection
            text_results = self.client._text_collection.get(include=["metadatas"])

            for i, metadata in enumerate(text_results["metadatas"] or []):
                issues = self._validate_metadata(metadata, "text")
                if issues:
                    embedding_id = text_results["ids"][i]
                    orphans["text_orphans"].append(embedding_id)
                    orphans["count"] += 1

            logger.info(f"Found {orphans['count']} orphaned embeddings")

            return orphans

        except Exception as e:
            error_msg = f"Failed to find orphaned embeddings: {str(e)}"
            logger.error(error_msg)
            raise StorageError(error_msg) from e

    def cleanup_orphaned_embeddings(self, confirm: bool = False) -> Dict[str, Any]:
        """Delete orphaned embeddings with invalid metadata.

        Args:
            confirm: Must be True to proceed (safety check)

        Returns:
            Cleanup report:
            {
                "status": "success" | "failed",
                "visual_deleted": int,
                "text_deleted": int,
                "total_deleted": int
            }

        Raises:
            ValueError: If confirm is False
        """
        if not confirm:
            raise ValueError("Cleanup requires explicit confirmation (confirm=True)")

        report = {"status": "success", "visual_deleted": 0, "text_deleted": 0, "total_deleted": 0}

        try:
            # Find orphans
            orphans = self.get_orphaned_embeddings()

            # Delete visual orphans
            if orphans["visual_orphans"]:
                self.client._visual_collection.delete(ids=orphans["visual_orphans"])
                report["visual_deleted"] = len(orphans["visual_orphans"])

            # Delete text orphans
            if orphans["text_orphans"]:
                self.client._text_collection.delete(ids=orphans["text_orphans"])
                report["text_deleted"] = len(orphans["text_orphans"])

            report["total_deleted"] = report["visual_deleted"] + report["text_deleted"]

            logger.info(f"Cleaned up {report['total_deleted']} orphaned embeddings")

        except Exception as e:
            report["status"] = "failed"
            report["error"] = str(e)
            logger.error(f"Cleanup failed: {str(e)}")

        return report

    def export_collection_metadata(
        self, collection: str = "all"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Export collection metadata for backup/analysis.

        Args:
            collection: "visual", "text", or "all"

        Returns:
            Metadata export:
            {
                "visual": [metadata_dict, ...],
                "text": [metadata_dict, ...],
                "export_timestamp": str
            }
        """
        export: Dict[str, Any] = {
            "visual": [],
            "text": [],
            "export_timestamp": datetime.utcnow().isoformat(),
        }

        try:
            if collection in ["visual", "all"]:
                visual_results = self.client._visual_collection.get(include=["metadatas"])
                export["visual"] = visual_results["metadatas"] or []

            if collection in ["text", "all"]:
                text_results = self.client._text_collection.get(include=["metadatas"])
                export["text"] = text_results["metadatas"] or []

            logger.info(
                f"Exported metadata: {len(export['visual'])} visual, " f"{len(export['text'])} text"
            )

            return export

        except Exception as e:
            error_msg = f"Failed to export metadata: {str(e)}"
            logger.error(error_msg)
            raise StorageError(error_msg) from e
