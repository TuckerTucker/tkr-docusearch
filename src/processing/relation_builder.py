"""Automatic document relation detection at ingest time.

After a document is stored in Koji, ``RelationBuilder`` scans for
relationships to existing documents and creates edges in the
``doc_relations`` table.

Supported relation types:

- **version_of**: Same base filename (case-insensitive, ignoring extension).
- **references**: Chunk text mentions the filename of another stored document.
"""

from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from src.storage.koji_client import KojiClient

logger = structlog.get_logger(__name__)


class RelationBuilder:
    """Detects and creates document relations after ingest.

    All methods are fault-tolerant — individual relation creation failures
    are logged but do not propagate.

    Args:
        storage_client: KojiClient instance (must be open).
    """

    def __init__(self, storage_client: "KojiClient") -> None:
        self._storage = storage_client

    def build_relations(
        self,
        doc_id: str,
        filename: str,
        chunks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Detect and create relations for a newly ingested document.

        Args:
            doc_id: The new document's identifier.
            filename: Original filename of the new document.
            chunks: List of chunk record dicts (must have ``text`` key).

        Returns:
            List of dicts describing created relations, each with
            ``src_doc_id``, ``dst_doc_id``, ``relation_type``.
        """
        created: list[dict[str, Any]] = []
        created.extend(self._detect_version_of(doc_id, filename))
        created.extend(self._detect_references(doc_id, filename, chunks))
        return created

    def _detect_version_of(
        self,
        doc_id: str,
        filename: str,
    ) -> list[dict[str, Any]]:
        """Find existing documents with the same base filename.

        Compares base names (filename without extension) case-insensitively.
        Creates a bidirectional ``version_of`` relation from the new doc
        to each match.
        """
        created: list[dict[str, Any]] = []
        new_base = os.path.splitext(filename)[0].lower()
        if not new_base:
            return created

        existing_docs = self._storage.list_documents(limit=10000)
        for doc in existing_docs:
            other_id = doc.get("doc_id", "")
            other_filename = doc.get("filename", "")
            if other_id == doc_id:
                continue

            other_base = os.path.splitext(other_filename)[0].lower()
            if other_base == new_base:
                rel = self._safe_create_relation(
                    doc_id, other_id, "version_of",
                )
                if rel is not None:
                    created.append(rel)

        return created

    def _detect_references(
        self,
        doc_id: str,
        filename: str,
        chunks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Scan chunk text for filenames of other stored documents.

        Builds a regex pattern from all known filenames (excluding the
        current document) and scans each chunk's text for matches.
        Deduplicates so only one ``references`` relation is created per
        target document.
        """
        created: list[dict[str, Any]] = []

        existing_docs = self._storage.list_documents(limit=10000)
        # Map filename → doc_id (excluding current doc)
        filename_to_id: dict[str, str] = {}
        for doc in existing_docs:
            other_id = doc.get("doc_id", "")
            other_filename = doc.get("filename", "")
            if other_id != doc_id and other_filename:
                filename_to_id[other_filename] = other_id

        if not filename_to_id:
            return created

        # Build regex: match any known filename with word boundaries
        escaped = [re.escape(fn) for fn in filename_to_id]
        pattern = re.compile(
            r"\b(" + "|".join(escaped) + r")\b",
            re.IGNORECASE,
        )

        # Scan chunks, deduplicate by target doc_id
        seen_targets: set[str] = set()
        for chunk in chunks:
            text = chunk.get("text", "")
            if not text:
                continue
            for match in pattern.finditer(text):
                matched_filename = match.group(0)
                # Case-insensitive lookup
                target_id = None
                for fn, tid in filename_to_id.items():
                    if fn.lower() == matched_filename.lower():
                        target_id = tid
                        break
                if target_id and target_id not in seen_targets:
                    seen_targets.add(target_id)
                    rel = self._safe_create_relation(
                        doc_id,
                        target_id,
                        "references",
                        metadata={
                            "matched_filename": matched_filename,
                            "chunk_id": chunk.get("id"),
                        },
                    )
                    if rel is not None:
                        created.append(rel)

        return created

    def _safe_create_relation(
        self,
        src_doc_id: str,
        dst_doc_id: str,
        relation_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Create a relation, swallowing duplicates and other errors.

        Returns:
            Relation dict on success, ``None`` on failure.
        """
        try:
            self._storage.create_relation(
                src_doc_id=src_doc_id,
                dst_doc_id=dst_doc_id,
                relation_type=relation_type,
                metadata=metadata,
            )
            logger.info(
                "relation_builder.created",
                src=src_doc_id,
                dst=dst_doc_id,
                type=relation_type,
            )
            return {
                "src_doc_id": src_doc_id,
                "dst_doc_id": dst_doc_id,
                "relation_type": relation_type,
            }
        except Exception as exc:
            logger.debug(
                "relation_builder.skipped",
                src=src_doc_id,
                dst=dst_doc_id,
                type=relation_type,
                reason=str(exc),
            )
            return None
