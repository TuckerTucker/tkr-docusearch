"""
Koji database client for DocuSearch.

This module provides the primary interface between DocuSearch and the Koji
hybrid database (SQL + vector + graph). It handles document, page, and chunk
persistence with multi-vector embedding support.

All persistence operations flow through this client. It handles:
- Connection lifecycle (open, close, sync)
- Schema synchronization with foreign key registration
- Document, page, and chunk CRUD operations
- PyArrow conversion for Koji insert operations
- Multi-vector embedding binary packing/unpacking
"""

from __future__ import annotations

import json
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pyarrow as pa
import structlog
import koji
from koji._koji import ForeignKey

from ..config.koji_config import KojiConfig

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

_SAFE_IDENTIFIER = __import__("re").compile(r"^[a-zA-Z0-9_\-]{1,128}$")


class _SafeEncoder(json.JSONEncoder):
    """JSON encoder that coerces non-serializable values instead of raising.

    Handles common types found in document metadata:
    ``bytes``/``bytearray`` are dropped, ``Path`` and ``datetime`` are
    stringified, and anything else falls back to ``str()``.
    """

    def default(self, o: Any) -> Any:
        if isinstance(o, (bytes, bytearray)):
            return None  # drop binary blobs
        if isinstance(o, Path):
            return str(o)
        # datetime, date, time
        if hasattr(o, "isoformat"):
            return o.isoformat()
        # sets → lists
        if isinstance(o, (set, frozenset)):
            return list(o)
        return str(o)


def _safe_json(obj: Any) -> str | None:
    """Serialize an arbitrary object to JSON, tolerating non-standard types.

    Args:
        obj: Value to serialize (dict, list, or scalar).

    Returns:
        JSON string, or ``None`` if *obj* is falsy.
    """
    if not obj:
        return None
    return json.dumps(obj, cls=_SafeEncoder)


def _serialize_metadata(metadata: dict | None) -> str | None:
    """Serialize a metadata dict to JSON for storage.

    Strips ``bytes``/``bytearray`` values entirely (transient binary
    data like album art) and coerces other non-standard types via
    :class:`_SafeEncoder`.

    Args:
        metadata: Arbitrary metadata dict.

    Returns:
        JSON string or ``None``.
    """
    if not metadata:
        return None
    clean = {
        k: v for k, v in metadata.items()
        if not isinstance(v, (bytes, bytearray))
    }
    return json.dumps(clean, cls=_SafeEncoder)


def _sanitize_sql_value(value: str) -> str:
    """Sanitize a value for safe interpolation into SQL WHERE clauses.

    Only allows alphanumeric characters, hyphens, and underscores.
    Raises ValueError if the value contains unsafe characters.

    Args:
        value: String value to sanitize.

    Returns:
        The original value if safe.

    Raises:
        ValueError: If value contains characters outside [a-zA-Z0-9_-].
    """
    if not _SAFE_IDENTIFIER.match(value):
        raise ValueError(
            f"Unsafe value for SQL interpolation: {value!r}. "
            "Only alphanumeric characters, hyphens, and underscores are allowed."
        )
    return value


class KojiClientError(Exception):
    """Base exception for Koji client operations."""


class KojiConnectionError(KojiClientError):
    """Failed to connect to or operate on the Koji database."""


class KojiQueryError(KojiClientError):
    """SQL query execution failed."""


class KojiDuplicateError(KojiClientError):
    """Attempted to insert a duplicate primary key."""


# ---------------------------------------------------------------------------
# Schema Definition
# ---------------------------------------------------------------------------

DOCUSEARCH_SCHEMA: dict = {
    "projects": {
        "columns": {
            "project_id": {"type": "text", "primary_key": True},
            "name": {"type": "text"},
            "description": {"type": "text"},
            "created_at": {"type": "text"},
            "metadata": {"type": "text"},
        },
    },
    "documents": {
        "columns": {
            "doc_id": {"type": "text", "primary_key": True},
            "project_id": {"type": "text"},
            "filename": {"type": "text"},
            "format": {"type": "text"},
            "num_pages": {"type": "integer"},
            "markdown": {"type": "text"},
            "metadata": {"type": "text"},
            "created_at": {"type": "text"},
        },
    },
    "pages": {
        "columns": {
            "id": {"type": "text", "primary_key": True},
            "doc_id": {"type": "text"},
            "page_num": {"type": "integer"},
            "image": {"type": "binary"},
            "thumb": {"type": "binary"},
            "embedding": {"type": "binary"},
            "structure": {"type": "text"},
            "width": {"type": "integer"},
            "height": {"type": "integer"},
        },
    },
    "chunks": {
        "columns": {
            "id": {"type": "text", "primary_key": True},
            "doc_id": {"type": "text"},
            "page_num": {"type": "integer"},
            "text": {"type": "text"},
            "embedding": {"type": "binary"},
            "context": {"type": "text"},
            "word_count": {"type": "integer"},
            "start_time": {"type": "float"},
            "end_time": {"type": "float"},
        },
    },
    "doc_relations": {
        "columns": {
            "src_doc_id": {"type": "text", "primary_key": True},
            "dst_doc_id": {"type": "text", "primary_key": True},
            "relation_type": {"type": "text", "primary_key": True},
            "metadata": {"type": "text"},
        },
    },
}

DOCUSEARCH_FOREIGN_KEYS = [
    ForeignKey(
        table="documents",
        columns=["project_id"],
        references_table="projects",
        references_columns=["project_id"],
        on_delete="cascade",
    ),
    ForeignKey(
        table="pages",
        columns=["doc_id"],
        references_table="documents",
        references_columns=["doc_id"],
        on_delete="cascade",
    ),
    ForeignKey(
        table="chunks",
        columns=["doc_id"],
        references_table="documents",
        references_columns=["doc_id"],
        on_delete="cascade",
    ),
    ForeignKey(
        table="doc_relations",
        columns=["src_doc_id"],
        references_table="documents",
        references_columns=["doc_id"],
        on_delete="cascade",
    ),
    ForeignKey(
        table="doc_relations",
        columns=["dst_doc_id"],
        references_table="documents",
        references_columns=["doc_id"],
        on_delete="cascade",
    ),
]


# ---------------------------------------------------------------------------
# Multi-vector packing utilities
# ---------------------------------------------------------------------------

def pack_multivec(embedding: list[list[float]]) -> bytes:
    """Pack multi-vector embedding into Koji binary format.

    Format:
        Header: num_tokens (u32 LE) + dim (u32 LE)
        Data: num_tokens * dim * f32 values (LE, row-major)

    Args:
        embedding: List of token vectors, each a list of floats.

    Returns:
        Packed binary blob compatible with Koji ``<~>`` operator.
    """
    num_tokens = len(embedding)
    dim = len(embedding[0])
    header = struct.pack("<II", num_tokens, dim)
    data = struct.pack(
        f"<{num_tokens * dim}f",
        *(val for vec in embedding for val in vec),
    )
    return header + data


def unpack_multivec(blob: bytes) -> list[list[float]]:
    """Unpack Koji binary format to multi-vector embedding.

    Args:
        blob: Packed binary blob from Koji.

    Returns:
        List of token vectors.
    """
    num_tokens, dim = struct.unpack("<II", blob[:8])
    values = struct.unpack(f"<{num_tokens * dim}f", blob[8:])
    return [list(values[i * dim : (i + 1) * dim]) for i in range(num_tokens)]


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class KojiClient:
    """Koji database client for DocuSearch.

    Manages the full lifecycle of the Koji database connection and provides
    typed CRUD operations for documents, pages, and chunks.

    Args:
        config: Koji database configuration.
    """

    def __init__(self, config: KojiConfig) -> None:
        self._config = config
        self._db: koji.Database | None = None
        self._write_count: int = 0

    # -- lifecycle -----------------------------------------------------------

    def open(self) -> None:
        """Open the Koji database and synchronize schema.

        Creates the database file and parent directories if they do not exist.
        Idempotent — calling open() on an already-open client is a no-op.

        Raises:
            KojiConnectionError: If the database cannot be opened.
        """
        if self._db is not None:
            return

        try:
            db_path = Path(self._config.db_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)

            self._db = koji.open(str(db_path))
            self._sync_schema()

            logger.info(
                "koji_client.opened",
                db_path=str(db_path),
                tables=self._db.list_tables(),
            )
        except Exception as exc:
            self._db = None
            raise KojiConnectionError(
                f"Failed to open Koji database at {self._config.db_path}: {exc}"
            ) from exc

    def close(self) -> None:
        """Sync and close the database connection.

        Safe to call even if the database is not open.
        """
        if self._db is None:
            return

        try:
            self._db.sync()
            logger.info("koji_client.closed", db_path=self._config.db_path)
        except Exception as exc:
            logger.warning("koji_client.close_error", error=str(exc))
        finally:
            self._db = None
            self._write_count = 0

    def sync(self) -> None:
        """Flush pending writes to disk."""
        self._require_open()
        self._db.sync()

    def health_check(self) -> dict[str, Any]:
        """Return database health status.

        Returns:
            Dictionary with connection status and table list.
        """
        if self._db is None:
            return {
                "connected": False,
                "db_path": self._config.db_path,
                "tables": [],
            }

        try:
            tables = self._db.list_tables()
            return {
                "connected": True,
                "db_path": self._config.db_path,
                "tables": tables,
            }
        except Exception:
            return {
                "connected": False,
                "db_path": self._config.db_path,
                "tables": [],
            }

    # -- raw SQL -------------------------------------------------------------

    def query(self, sql: str, params: list[Any] | None = None) -> pa.Table:
        """Execute a SQL query and return results as a PyArrow Table.

        Args:
            sql: SQL query string.
            params: Optional positional parameters (``?`` placeholders).

        Returns:
            Query results as a PyArrow Table.

        Raises:
            KojiQueryError: If the query fails.
        """
        self._require_open()
        try:
            return self._db.query(sql, params or [])
        except Exception as exc:
            raise KojiQueryError(f"Query failed: {exc}") from exc

    def insert(self, table: str, data: pa.Table | pa.RecordBatch) -> None:
        """Insert data into a table.

        Args:
            table: Target table name.
            data: PyArrow Table or RecordBatch to insert.

        Raises:
            KojiQueryError: If the insert fails.
        """
        self._require_open()
        try:
            self._db.insert(table, data)
            self._after_write()
        except Exception as exc:
            raise KojiQueryError(f"Insert into {table} failed: {exc}") from exc

    # -- document CRUD -------------------------------------------------------

    def create_document(
        self,
        doc_id: str,
        filename: str,
        format: str,
        num_pages: int | None = None,
        markdown: str | None = None,
        metadata: dict[str, Any] | None = None,
        project_id: str = "default",
    ) -> None:
        """Create a new document record.

        Args:
            doc_id: Unique document identifier.
            filename: Original filename.
            format: File format extension (e.g. ``pdf``, ``md``).
            num_pages: Number of pages (optional).
            markdown: Full document markdown (optional).
            metadata: Arbitrary metadata dict, stored as JSON (optional).
            project_id: Project to assign the document to.

        Raises:
            KojiDuplicateError: If ``doc_id`` already exists.
        """
        existing = self.get_document(doc_id)
        if existing is not None:
            raise KojiDuplicateError(f"Document {doc_id} already exists")

        now = datetime.now(timezone.utc).isoformat()
        # PKs are non-nullable in Koji; use explicit PA schema to match
        schema = pa.schema([
            pa.field("doc_id", pa.string(), nullable=False),
            pa.field("project_id", pa.string()),
            pa.field("filename", pa.string()),
            pa.field("format", pa.string()),
            pa.field("num_pages", pa.int64()),
            pa.field("markdown", pa.string()),
            pa.field("metadata", pa.string()),
            pa.field("created_at", pa.string()),
        ])
        table = pa.table(
            {
                "doc_id": [doc_id],
                "project_id": [project_id],
                "filename": [filename],
                "format": [format],
                "num_pages": [num_pages],
                "markdown": [markdown],
                "metadata": [_serialize_metadata(metadata)],
                "created_at": [now],
            },
            schema=schema,
        )
        self.insert("documents", table)

        logger.info(
            "koji_client.document_created",
            doc_id=doc_id,
            project_id=project_id,
            filename=filename,
            format=format,
        )

    def get_document(self, doc_id: str) -> dict[str, Any] | None:
        """Retrieve a document by ID.

        Args:
            doc_id: Document identifier.

        Returns:
            Document as a dictionary, or ``None`` if not found.
        """
        self._require_open()
        try:
            result = self.query(
                "SELECT * FROM documents WHERE doc_id = ?", [doc_id]
            )
            if result.num_rows == 0:
                return None
            rows = self._arrow_to_dicts(result, json_fields=["metadata"])
            return rows[0]
        except Exception:
            return None

    def get_document_markdown(self, doc_id: str) -> str | None:
        """Retrieve the markdown content for a document.

        Args:
            doc_id: Document identifier.

        Returns:
            Markdown string or ``None`` if document not found.
        """
        doc = self.get_document(doc_id)
        return doc.get("markdown") if doc else None

    def list_documents(
        self,
        format: str | None = None,
        project_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List documents with optional format and project filters.

        Args:
            format: Filter by file format (optional).
            project_id: Filter by project (optional). ``None`` returns all.
            limit: Maximum results to return.
            offset: Number of results to skip.

        Returns:
            List of document dictionaries ordered by ``created_at`` descending.
        """
        clauses: list[str] = []
        params: list[Any] = []

        if format:
            clauses.append("format = ?")
            params.append(format)
        if project_id is not None:
            clauses.append("project_id = ?")
            params.append(project_id)

        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"SELECT * FROM documents{where} ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        result = self.query(sql, params)
        return self._arrow_to_dicts(result, json_fields=["metadata"])

    def update_document(self, doc_id: str, **fields: Any) -> None:
        """Update fields on an existing document.

        Args:
            doc_id: Document identifier.
            **fields: Fields to update (must be valid column names).

        Raises:
            ValueError: If no fields provided or invalid field name.
        """
        if not fields:
            raise ValueError("No fields to update")

        valid_columns = {"filename", "format", "num_pages", "markdown", "metadata", "project_id"}
        invalid = set(fields.keys()) - valid_columns
        if invalid:
            raise ValueError(f"Invalid document fields: {invalid}")

        self._require_open()

        # Serialize metadata to JSON if present
        if "metadata" in fields and fields["metadata"] is not None:
            if not isinstance(fields["metadata"], str):
                fields["metadata"] = json.dumps(fields["metadata"], cls=_SafeEncoder)

        safe_id = _sanitize_sql_value(doc_id)
        result = self._db.update("documents", fields, f"doc_id = '{safe_id}'")
        if result.rows_updated > 0:
            self._after_write()

    def delete_document(self, doc_id: str) -> None:
        """Delete a document and all associated pages, chunks, and relations.

        Uses Koji cascade delete via registered foreign keys.
        Idempotent — no error if document does not exist.

        Args:
            doc_id: Document identifier to delete.
        """
        self._require_open()
        safe_id = _sanitize_sql_value(doc_id)
        try:
            self._db.delete_cascade("documents", f"doc_id = '{safe_id}'")
        except Exception:
            # Fallback: manual cascade (handles empty/non-materialized tables)
            for table, condition in [
                ("doc_relations", f"src_doc_id = '{safe_id}' OR dst_doc_id = '{safe_id}'"),
                ("chunks", f"doc_id = '{safe_id}'"),
                ("pages", f"doc_id = '{safe_id}'"),
                ("documents", f"doc_id = '{safe_id}'"),
            ]:
                self._delete_where(table, condition)
        self._after_write()
        logger.info("koji_client.document_deleted", doc_id=doc_id)

    # -- project CRUD --------------------------------------------------------

    def create_project(
        self,
        project_id: str,
        name: str,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new project.

        Args:
            project_id: Unique project slug (alphanumeric, hyphens, underscores).
            name: Human-readable project name.
            description: Optional project description.
            metadata: Arbitrary metadata dict, stored as JSON.

        Returns:
            The created project as a dictionary.

        Raises:
            ValueError: If ``project_id`` is invalid.
            KojiDuplicateError: If ``project_id`` already exists.
        """
        _sanitize_sql_value(project_id)

        existing = self.get_project(project_id)
        if existing is not None:
            raise KojiDuplicateError(f"Project {project_id!r} already exists")

        now = datetime.now(timezone.utc).isoformat()
        schema = pa.schema([
            pa.field("project_id", pa.string(), nullable=False),
            pa.field("name", pa.string()),
            pa.field("description", pa.string()),
            pa.field("created_at", pa.string()),
            pa.field("metadata", pa.string()),
        ])
        table = pa.table(
            {
                "project_id": [project_id],
                "name": [name],
                "description": [description],
                "created_at": [now],
                "metadata": [_serialize_metadata(metadata)],
            },
            schema=schema,
        )
        self.insert("projects", table)

        logger.info(
            "koji_client.project_created",
            project_id=project_id,
            name=name,
        )
        return {
            "project_id": project_id,
            "name": name,
            "description": description,
            "created_at": now,
            "metadata": metadata,
        }

    def get_project(self, project_id: str) -> dict[str, Any] | None:
        """Retrieve a project by ID.

        Args:
            project_id: Project identifier.

        Returns:
            Project as a dictionary, or ``None`` if not found.
        """
        self._require_open()
        try:
            result = self.query(
                "SELECT * FROM projects WHERE project_id = ?", [project_id]
            )
            if result.num_rows == 0:
                return None
            rows = self._arrow_to_dicts(result, json_fields=["metadata"])
            return rows[0]
        except Exception:
            return None

    def list_projects(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List all projects.

        Args:
            limit: Maximum results to return.
            offset: Number of results to skip.

        Returns:
            List of project dictionaries ordered by ``created_at`` descending.
        """
        result = self.query(
            "SELECT * FROM projects ORDER BY created_at DESC LIMIT ? OFFSET ?",
            [limit, offset],
        )
        return self._arrow_to_dicts(result, json_fields=["metadata"])

    def update_project(self, project_id: str, **fields: Any) -> None:
        """Update fields on an existing project.

        Args:
            project_id: Project identifier.
            **fields: Fields to update (``name``, ``description``, ``metadata``).

        Raises:
            ValueError: If no fields provided or invalid field name.
        """
        if not fields:
            raise ValueError("No fields to update")

        valid_columns = {"name", "description", "metadata"}
        invalid = set(fields.keys()) - valid_columns
        if invalid:
            raise ValueError(f"Invalid project fields: {invalid}")

        self._require_open()

        if "metadata" in fields and fields["metadata"] is not None:
            if not isinstance(fields["metadata"], str):
                fields["metadata"] = json.dumps(fields["metadata"], cls=_SafeEncoder)

        safe_id = _sanitize_sql_value(project_id)
        result = self._db.update("projects", fields, f"project_id = '{safe_id}'")
        if result.rows_updated > 0:
            self._after_write()

    def delete_project(self, project_id: str) -> int:
        """Delete a project and all its documents (cascade).

        The ``"default"`` project cannot be deleted.

        Args:
            project_id: Project identifier to delete.

        Returns:
            Number of documents that were deleted with the project.

        Raises:
            ValueError: If attempting to delete the ``"default"`` project.
        """
        if project_id == "default":
            raise ValueError("The 'default' project cannot be deleted")

        self._require_open()
        doc_count = self.count_documents_in_project(project_id)

        safe_id = _sanitize_sql_value(project_id)

        # Delete documents first (cascades to pages, chunks, relations)
        if doc_count > 0:
            docs = self.list_documents(project_id=project_id, limit=100000)
            for doc in docs:
                self.delete_document(doc["doc_id"])

        # Delete the project row
        self._delete_where("projects", f"project_id = '{safe_id}'")
        self._after_write()

        logger.info(
            "koji_client.project_deleted",
            project_id=project_id,
            documents_deleted=doc_count,
        )
        return doc_count

    def count_documents_in_project(self, project_id: str) -> int:
        """Count documents in a project.

        Args:
            project_id: Project identifier.

        Returns:
            Number of documents assigned to the project.
        """
        result = self.query(
            "SELECT COUNT(*) AS n FROM documents WHERE project_id = ?",
            [project_id],
        )
        d = result.to_pydict()
        return int(d["n"][0]) if d["n"] else 0

    # -- page operations -----------------------------------------------------

    def insert_pages(self, pages: list[dict[str, Any]]) -> None:
        """Insert page records.

        Accepts a list of dictionaries and converts to PyArrow internally.
        Required keys: ``id``, ``doc_id``, ``page_num``.
        Optional keys: ``image``, ``thumb``, ``embedding``, ``structure``,
        ``width``, ``height``.

        Args:
            pages: List of page data dictionaries.

        Raises:
            ValueError: If required fields are missing.
        """
        if not pages:
            return

        for p in pages:
            if not all(k in p for k in ("id", "doc_id", "page_num")):
                raise ValueError("Pages require id, doc_id, and page_num")

        schema = pa.schema([
            pa.field("id", pa.string(), nullable=False),
            pa.field("doc_id", pa.string()),
            pa.field("page_num", pa.int64()),
            pa.field("image", pa.binary()),
            pa.field("thumb", pa.binary()),
            pa.field("embedding", pa.binary()),
            pa.field("structure", pa.string()),
            pa.field("width", pa.int64()),
            pa.field("height", pa.int64()),
        ])
        table = pa.table(
            {
                "id": [p["id"] for p in pages],
                "doc_id": [p["doc_id"] for p in pages],
                "page_num": [p["page_num"] for p in pages],
                "image": [p.get("image") for p in pages],
                "thumb": [p.get("thumb") for p in pages],
                "embedding": [p.get("embedding") for p in pages],
                "structure": [
                    _safe_json(p.get("structure")) for p in pages
                ],
                "width": [p.get("width") for p in pages],
                "height": [p.get("height") for p in pages],
            },
            schema=schema,
        )
        self.insert("pages", table)

    def insert_chunks(self, chunks: list[dict[str, Any]]) -> None:
        """Insert chunk records.

        Accepts a list of dictionaries and converts to PyArrow internally.
        Required keys: ``id``, ``doc_id``, ``page_num``, ``text``.
        Optional keys: ``embedding``, ``context``, ``word_count``,
        ``start_time``, ``end_time``.

        Args:
            chunks: List of chunk data dictionaries.

        Raises:
            ValueError: If required fields are missing.
        """
        if not chunks:
            return

        for c in chunks:
            if not all(k in c for k in ("id", "doc_id", "page_num", "text")):
                raise ValueError("Chunks require id, doc_id, page_num, and text")

        schema = pa.schema([
            pa.field("id", pa.string(), nullable=False),
            pa.field("doc_id", pa.string()),
            pa.field("page_num", pa.int64()),
            pa.field("text", pa.string()),
            pa.field("embedding", pa.binary()),
            pa.field("context", pa.string()),
            pa.field("word_count", pa.int64()),
            pa.field("start_time", pa.float64()),
            pa.field("end_time", pa.float64()),
        ])
        table = pa.table(
            {
                "id": [c["id"] for c in chunks],
                "doc_id": [c["doc_id"] for c in chunks],
                "page_num": [c["page_num"] for c in chunks],
                "text": [c["text"] for c in chunks],
                "embedding": [c.get("embedding") for c in chunks],
                "context": [
                    _safe_json(c.get("context")) for c in chunks
                ],
                "word_count": [c.get("word_count") for c in chunks],
                "start_time": [c.get("start_time") for c in chunks],
                "end_time": [c.get("end_time") for c in chunks],
            },
            schema=schema,
        )
        self.insert("chunks", table)

    def get_pages_for_document(self, doc_id: str) -> list[dict[str, Any]]:
        """Retrieve all pages for a document, ordered by page number.

        Args:
            doc_id: Document identifier.

        Returns:
            List of page dictionaries.
        """
        result = self.query(
            "SELECT * FROM pages WHERE doc_id = ? ORDER BY page_num",
            [doc_id],
        )
        return self._arrow_to_dicts(result, json_fields=["structure"])

    def get_chunks_for_document(self, doc_id: str) -> list[dict[str, Any]]:
        """Retrieve all chunks for a document, ordered by page and chunk ID.

        Args:
            doc_id: Document identifier.

        Returns:
            List of chunk dictionaries.
        """
        result = self.query(
            "SELECT * FROM chunks WHERE doc_id = ? ORDER BY page_num, id",
            [doc_id],
        )
        return self._arrow_to_dicts(result, json_fields=["context"])

    def get_page(self, page_id: str) -> dict[str, Any] | None:
        """Retrieve a single page by ID.

        Args:
            page_id: Page identifier.

        Returns:
            Page dictionary or ``None``.
        """
        self._require_open()
        try:
            row = self._db.find_by_id("pages", page_id)
            if row is None:
                return None
            if row.get("structure") and isinstance(row["structure"], str):
                row["structure"] = json.loads(row["structure"])
            return row
        except Exception:
            return None

    def get_chunk(self, chunk_id: str) -> dict[str, Any] | None:
        """Retrieve a single chunk by ID.

        Args:
            chunk_id: Chunk identifier.

        Returns:
            Chunk dictionary or ``None``.
        """
        self._require_open()
        try:
            row = self._db.find_by_id("chunks", chunk_id)
            if row is None:
                return None
            if row.get("context") and isinstance(row["context"], str):
                row["context"] = json.loads(row["context"])
            return row
        except Exception:
            return None

    # -- relationship operations ---------------------------------------------

    def create_relation(
        self,
        src_doc_id: str,
        dst_doc_id: str,
        relation_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Create a relationship between two documents.

        Args:
            src_doc_id: Source document identifier.
            dst_doc_id: Destination document identifier.
            relation_type: Relationship type (``cites``, ``references``,
                ``related``, ``version_of``).
            metadata: Optional metadata dict, stored as JSON.

        Raises:
            KojiDuplicateError: If the relation already exists.
            ValueError: If either document does not exist.
        """
        if self.get_document(src_doc_id) is None:
            raise ValueError(f"Source document {src_doc_id} not found")
        if self.get_document(dst_doc_id) is None:
            raise ValueError(f"Destination document {dst_doc_id} not found")

        # Check for duplicate
        existing = self.query(
            "SELECT * FROM doc_relations "
            "WHERE src_doc_id = ? AND dst_doc_id = ? AND relation_type = ?",
            [src_doc_id, dst_doc_id, relation_type],
        )
        if existing.num_rows > 0:
            raise KojiDuplicateError(
                f"Relation {src_doc_id} -{relation_type}-> {dst_doc_id} already exists"
            )

        schema = pa.schema([
            pa.field("src_doc_id", pa.string(), nullable=False),
            pa.field("dst_doc_id", pa.string(), nullable=False),
            pa.field("relation_type", pa.string(), nullable=False),
            pa.field("metadata", pa.string()),
        ])
        table = pa.table(
            {
                "src_doc_id": [src_doc_id],
                "dst_doc_id": [dst_doc_id],
                "relation_type": [relation_type],
                "metadata": [_serialize_metadata(metadata)],
            },
            schema=schema,
        )
        self.insert("doc_relations", table)

        logger.info(
            "koji_client.relation_created",
            src=src_doc_id,
            dst=dst_doc_id,
            type=relation_type,
        )

    def get_relations(
        self,
        doc_id: str,
        relation_type: str | None = None,
        direction: str = "both",
    ) -> list[dict[str, Any]]:
        """Get relationships for a document.

        Args:
            doc_id: Document identifier.
            relation_type: Filter by type (optional).
            direction: ``outgoing``, ``incoming``, or ``both`` (default).

        Returns:
            List of relation dictionaries.
        """
        results: list[dict[str, Any]] = []

        if direction in ("outgoing", "both"):
            if relation_type:
                out = self.query(
                    "SELECT * FROM doc_relations "
                    "WHERE src_doc_id = ? AND relation_type = ?",
                    [doc_id, relation_type],
                )
            else:
                out = self.query(
                    "SELECT * FROM doc_relations WHERE src_doc_id = ?",
                    [doc_id],
                )
            results.extend(self._arrow_to_dicts(out, json_fields=["metadata"]))

        if direction in ("incoming", "both"):
            if relation_type:
                inc = self.query(
                    "SELECT * FROM doc_relations "
                    "WHERE dst_doc_id = ? AND relation_type = ?",
                    [doc_id, relation_type],
                )
            else:
                inc = self.query(
                    "SELECT * FROM doc_relations WHERE dst_doc_id = ?",
                    [doc_id],
                )
            results.extend(self._arrow_to_dicts(inc, json_fields=["metadata"]))

        return results

    def delete_relation(
        self,
        src_doc_id: str,
        dst_doc_id: str,
        relation_type: str,
    ) -> None:
        """Delete a specific relationship.

        Idempotent — no error if the relation does not exist.

        Args:
            src_doc_id: Source document identifier.
            dst_doc_id: Destination document identifier.
            relation_type: Relationship type.
        """
        self._require_open()
        safe_src = _sanitize_sql_value(src_doc_id)
        safe_dst = _sanitize_sql_value(dst_doc_id)
        safe_type = _sanitize_sql_value(relation_type)
        try:
            self._db.delete(
                "doc_relations",
                f"src_doc_id = '{safe_src}' "
                f"AND dst_doc_id = '{safe_dst}' "
                f"AND relation_type = '{safe_type}'",
            )
        except Exception as exc:
            logger.warning(
                "koji_client.delete_relation_error",
                src=src_doc_id, dst=dst_doc_id, rel=relation_type,
                error=str(exc),
            )
        self._after_write()

    def get_related_documents(
        self,
        root_doc_id: str,
        max_depth: int = 3,
    ) -> list[dict[str, Any]]:
        """Find all documents related to a root document via graph traversal.

        Uses iterative BFS queries — one hop per iteration — because
        Koji's recursive CTEs do not support arithmetic expressions
        in the recursive term (verified in Koji 0.2.0).

        Args:
            root_doc_id: Starting document identifier.
            max_depth: Maximum traversal depth.

        Returns:
            List of related document dicts with ``depth`` and ``relation_type``.
        """
        visited: set[str] = {root_doc_id}
        # (doc_id, relation_type, depth)
        found: list[tuple[str, str, int]] = []
        frontier = [root_doc_id]

        for depth in range(1, max_depth + 1):
            if not frontier:
                break

            placeholders = ", ".join("?" for _ in frontier)
            rows = self.query(
                f"SELECT dst_doc_id, relation_type FROM doc_relations "
                f"WHERE src_doc_id IN ({placeholders})",
                frontier,
            )
            d = rows.to_pydict()
            next_frontier: list[str] = []
            for i in range(rows.num_rows):
                dst = d["dst_doc_id"][i]
                rel_type = d["relation_type"][i]
                if dst not in visited:
                    visited.add(dst)
                    found.append((dst, rel_type, depth))
                    next_frontier.append(dst)
            frontier = next_frontier

        if not found:
            return []

        # Fetch full document records for discovered doc_ids
        doc_ids = [f[0] for f in found]
        placeholders = ", ".join("?" for _ in doc_ids)
        docs_result = self.query(
            f"SELECT * FROM documents WHERE doc_id IN ({placeholders})",
            doc_ids,
        )
        docs_by_id = {
            doc["doc_id"]: doc
            for doc in self._arrow_to_dicts(docs_result, json_fields=["metadata"])
        }

        results: list[dict[str, Any]] = []
        for doc_id, rel_type, depth in found:
            doc = docs_by_id.get(doc_id)
            if doc is not None:
                doc["depth"] = depth
                doc["relation_type"] = rel_type
                results.append(doc)

        results.sort(key=lambda r: r["depth"])
        return results

    # -- graph algorithms ----------------------------------------------------

    _GRAPH_EDGE_QUERY = (
        "WITH doc_map AS ("
        "  SELECT doc_id, ROW_NUMBER() OVER (ORDER BY doc_id) AS node_id"
        "  FROM documents"
        ") "
        "SELECT CAST(sm.node_id AS BIGINT) AS src, "
        "       CAST(dm.node_id AS BIGINT) AS dst "
        "FROM doc_relations r "
        "JOIN doc_map sm ON r.src_doc_id = sm.doc_id "
        "JOIN doc_map dm ON r.dst_doc_id = dm.doc_id"
    )

    def _project_graph_edge_query(self, project_id: str) -> str:
        """Build a project-scoped graph edge query.

        Args:
            project_id: Project identifier to scope the graph to.

        Returns:
            SQL edge query string scoped to the given project.
        """
        safe_pid = _sanitize_sql_value(project_id)
        return (
            "WITH doc_map AS ("
            "  SELECT doc_id, ROW_NUMBER() OVER (ORDER BY doc_id) AS node_id"
            f"  FROM documents WHERE project_id = '{safe_pid}'"
            ") "
            "SELECT CAST(sm.node_id AS BIGINT) AS src, "
            "       CAST(dm.node_id AS BIGINT) AS dst "
            "FROM doc_relations r "
            "JOIN doc_map sm ON r.src_doc_id = sm.doc_id "
            "JOIN doc_map dm ON r.dst_doc_id = dm.doc_id"
        )

    def _doc_id_int_mapping(
        self,
        project_id: str | None = None,
    ) -> dict[int, str]:
        """Build a reverse mapping from integer node IDs to text doc_ids.

        Uses ``ROW_NUMBER() OVER (ORDER BY doc_id)`` to assign stable integers
        matching the edge query used by graph algorithms.

        Args:
            project_id: Optional project scope. ``None`` includes all documents.

        Returns:
            Dict mapping integer node_id to text doc_id.
        """
        self._require_open()

        if project_id is not None:
            safe_pid = _sanitize_sql_value(project_id)
            sql = (
                "SELECT doc_id, ROW_NUMBER() OVER (ORDER BY doc_id) AS node_id "
                f"FROM documents WHERE project_id = '{safe_pid}'"
            )
        else:
            sql = (
                "SELECT doc_id, ROW_NUMBER() OVER (ORDER BY doc_id) AS node_id "
                "FROM documents"
            )
        result = self.query(sql)
        d = result.to_pydict()
        return {
            d["node_id"][i]: d["doc_id"][i]
            for i in range(result.num_rows)
        }

    def _run_graph_algorithm(
        self,
        algorithm: str,
        project_id: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """Run a Koji graph algorithm.

        Args:
            algorithm: Algorithm name (e.g. ``"pagerank"``).
            project_id: Optional project scope. ``None`` runs cross-project.
            **kwargs: Algorithm-specific parameters forwarded to
                ``Database.graph()``.

        Returns:
            PyArrow Table with algorithm-specific result columns.

        Raises:
            KojiQueryError: If the algorithm execution fails.
        """
        self._require_open()
        edge_query = (
            self._project_graph_edge_query(project_id)
            if project_id is not None
            else self._GRAPH_EDGE_QUERY
        )
        try:
            return self._db.graph(
                edge_query,
                algorithm,
                **kwargs,
            )
        except Exception as exc:
            raise KojiQueryError(
                f"Graph algorithm '{algorithm}' failed: {exc}"
            ) from exc

    def graph_pagerank(
        self,
        damping: float = 0.85,
        max_iterations: int = 100,
        tolerance: float = 1e-6,
        project_id: str | None = None,
    ) -> dict[str, float]:
        """Compute PageRank scores for documents in the graph.

        Uses the ``doc_relations`` table as the edge set and maps
        integer node IDs back to text ``doc_id`` values.

        Args:
            damping: Damping factor (0-1). Higher values follow links more.
            max_iterations: Maximum PageRank iterations.
            tolerance: Convergence threshold.
            project_id: Optional project scope. ``None`` runs cross-project.

        Returns:
            Dict mapping ``doc_id`` to PageRank score (scores sum to ~1.0).
        """
        id_map = self._doc_id_int_mapping(project_id=project_id)
        if not id_map:
            return {}

        result = self._run_graph_algorithm(
            "pagerank",
            project_id=project_id,
            damping=damping,
            max_iterations=max_iterations,
            tolerance=tolerance,
        )

        d = result.to_pydict()
        scores: dict[str, float] = {}
        for i in range(result.num_rows):
            node_id = d["node_id"][i]
            score = d["score"][i]
            doc_id = id_map.get(node_id)
            if doc_id is not None:
                scores[doc_id] = float(score)

        return scores

    def graph_communities(
        self,
        project_id: str | None = None,
    ) -> dict[str, int]:
        """Detect document communities using connected components.

        Treats the document relation graph as undirected and assigns
        each document to the connected component it belongs to.

        Args:
            project_id: Optional project scope. ``None`` runs cross-project.

        Returns:
            Dict mapping ``doc_id`` to integer component label.
        """
        id_map = self._doc_id_int_mapping(project_id=project_id)
        if not id_map:
            return {}

        result = self._run_graph_algorithm(
            "connected_components", project_id=project_id,
        )

        d = result.to_pydict()
        label_col = next(
            (c for c in ("component", "community", "label") if c in d),
            "component",
        )
        communities: dict[str, int] = {}
        for i in range(result.num_rows):
            node_id = d["node_id"][i]
            label = d[label_col][i]
            doc_id = id_map.get(node_id)
            if doc_id is not None:
                communities[doc_id] = int(label)

        return communities

    def graph_label_propagation(
        self,
        max_iterations: int = 100,
        project_id: str | None = None,
    ) -> dict[str, int]:
        """Detect document communities via label propagation.

        More granular than connected components — discovers densely
        connected sub-communities within connected components.

        Args:
            max_iterations: Maximum propagation iterations.
            project_id: Optional project scope. ``None`` runs cross-project.

        Returns:
            Dict mapping ``doc_id`` to community label (int).
        """
        id_map = self._doc_id_int_mapping(project_id=project_id)
        if not id_map:
            return {}

        result = self._run_graph_algorithm(
            "label_propagation",
            project_id=project_id,
            max_iterations=max_iterations,
        )

        d = result.to_pydict()
        label_col = next(
            (c for c in ("community", "label", "component") if c in d),
            "community",
        )
        communities: dict[str, int] = {}
        for i in range(result.num_rows):
            node_id = d["node_id"][i]
            label = d[label_col][i]
            doc_id = id_map.get(node_id)
            if doc_id is not None:
                communities[doc_id] = int(label)

        return communities

    def graph_shortest_paths(
        self,
        source_doc_id: str,
        project_id: str | None = None,
    ) -> dict[str, float]:
        """Shortest path distances from a source document to all others.

        Uses weighted Dijkstra. Unreachable nodes are omitted.

        Args:
            source_doc_id: Starting document identifier.
            project_id: Optional project scope. ``None`` runs cross-project.

        Returns:
            Dict mapping ``doc_id`` to distance (float).
        """
        id_map = self._doc_id_int_mapping(project_id=project_id)
        if not id_map:
            return {}

        # Reverse lookup: doc_id -> node_id
        doc_to_node = {v: k for k, v in id_map.items()}
        source_node = doc_to_node.get(source_doc_id)
        if source_node is None:
            return {}

        result = self._run_graph_algorithm(
            "shortest_paths",
            project_id=project_id,
            source_id=int(source_node),
        )

        d = result.to_pydict()
        distances: dict[str, float] = {}
        for i in range(result.num_rows):
            node_id = d["node_id"][i]
            score = d["score"][i]
            doc_id = id_map.get(node_id)
            if doc_id is not None and doc_id != source_doc_id:
                distances[doc_id] = float(score)

        return distances

    def graph_scc(
        self,
        project_id: str | None = None,
    ) -> dict[str, int]:
        """Detect strongly connected components (directed cycles).

        Args:
            project_id: Optional project scope. ``None`` runs cross-project.

        Returns:
            Dict mapping ``doc_id`` to SCC component label (int).
        """
        id_map = self._doc_id_int_mapping(project_id=project_id)
        if not id_map:
            return {}

        result = self._run_graph_algorithm("scc", project_id=project_id)

        d = result.to_pydict()
        label_col = next(
            (c for c in ("component", "community", "label") if c in d),
            "component",
        )
        components: dict[str, int] = {}
        for i in range(result.num_rows):
            node_id = d["node_id"][i]
            label = d[label_col][i]
            doc_id = id_map.get(node_id)
            if doc_id is not None:
                components[doc_id] = int(label)

        return components

    def graph_topological_sort(
        self,
        project_id: str | None = None,
    ) -> list[str]:
        """Topological ordering of documents (requires DAG).

        Args:
            project_id: Optional project scope. ``None`` runs cross-project.

        Returns:
            List of ``doc_id`` in topological order.

        Raises:
            KojiQueryError: If the graph contains cycles.
        """
        id_map = self._doc_id_int_mapping(project_id=project_id)
        if not id_map:
            return []

        result = self._run_graph_algorithm(
            "topological_sort", project_id=project_id,
        )

        d = result.to_pydict()
        order_col = next(
            (c for c in ("component", "order", "label") if c in d),
            "component",
        )

        # Build (order, doc_id) pairs and sort by order
        ordered: list[tuple[int, str]] = []
        for i in range(result.num_rows):
            node_id = d["node_id"][i]
            order_val = d[order_col][i]
            doc_id = id_map.get(node_id)
            if doc_id is not None:
                ordered.append((int(order_val), doc_id))

        ordered.sort(key=lambda x: x[0])
        return [doc_id for _, doc_id in ordered]

    def graph_has_cycle(
        self,
        project_id: str | None = None,
    ) -> bool:
        """Check if the document relation graph contains a cycle.

        Args:
            project_id: Optional project scope. ``None`` runs cross-project.

        Returns:
            True if a cycle exists, False otherwise.
        """
        id_map = self._doc_id_int_mapping(project_id=project_id)
        if not id_map:
            return False

        result = self._run_graph_algorithm("has_cycle", project_id=project_id)

        # Koji returns a plain bool for has_cycle, not a PyArrow Table
        if isinstance(result, bool):
            return result

        d = result.to_pydict()
        if "has_cycle" in d and result.num_rows > 0:
            return bool(d["has_cycle"][0])
        return False

    def delete_relations_by_type(self, relation_type: str) -> int:
        """Delete all relations of a given type.

        Used by graph enrichment to purge computed edges before
        recomputation (idempotency).

        Args:
            relation_type: The relation type to delete.

        Returns:
            Number of rows deleted.
        """
        safe_type = _sanitize_sql_value(relation_type)
        return self._delete_where(
            "doc_relations",
            f"relation_type = '{safe_type}'",
        )

    # -- internal helpers ----------------------------------------------------

    def _delete_where(self, table: str, condition: str) -> int:
        """Delete rows matching a SQL condition.

        Args:
            table: Table name.
            condition: SQL WHERE clause (e.g. ``"doc_id = 'abc'"``).

        Returns:
            Number of rows deleted.
        """
        self._require_open()
        try:
            result = self._db.delete(table, condition)
            return result.rows_deleted
        except Exception as exc:
            logger.warning(
                "koji_client._delete_where_error",
                table=table,
                condition=condition,
                error=str(exc),
            )
            return 0

    def _require_open(self) -> None:
        """Raise if the database is not open."""
        if self._db is None:
            raise KojiConnectionError("Database is not open. Call open() first.")

    def _sync_schema(self) -> None:
        """Synchronize database schema and register foreign keys."""
        self._db.sync_schema(DOCUSEARCH_SCHEMA)
        for fk in DOCUSEARCH_FOREIGN_KEYS:
            self._db.register_foreign_key(fk)

        self._ensure_default_project()

        logger.debug(
            "koji_client.schema_synced",
            tables=self._db.list_tables(),
        )

    def _ensure_default_project(self) -> None:
        """Seed the 'default' project if it does not exist."""
        result = self._db.query(
            "SELECT project_id FROM projects WHERE project_id = ?",
            ["default"],
        )
        if result.num_rows == 0:
            now = datetime.now(timezone.utc).isoformat()
            schema = pa.schema([
                pa.field("project_id", pa.string(), nullable=False),
                pa.field("name", pa.string()),
                pa.field("description", pa.string()),
                pa.field("created_at", pa.string()),
                pa.field("metadata", pa.string()),
            ])
            table = pa.table(
                {
                    "project_id": ["default"],
                    "name": ["Default"],
                    "description": ["Default project"],
                    "created_at": [now],
                    "metadata": [None],
                },
                schema=schema,
            )
            self._db.insert("projects", table)
            logger.info("koji_client.default_project_created")

    def _after_write(self) -> None:
        """Post-write hook: sync, compact, and prune old versions."""
        self._write_count += 1

        if self._config.sync_on_write:
            self._db.sync()

        if (
            self._config.compact_interval > 0
            and self._write_count % self._config.compact_interval == 0
        ):
            self._db.compact()
            try:
                self._db.cleanup_versions(keep_versions=2)
            except Exception:
                pass  # cleanup_versions may fail on empty tables
            logger.debug(
                "koji_client.compacted",
                write_count=self._write_count,
            )

    @staticmethod
    def _arrow_row_to_dict(result: pa.Table) -> dict[str, Any]:
        """Convert a single-row PyArrow Table to a dictionary.

        Args:
            result: PyArrow Table with exactly one row.

        Returns:
            Row as a dictionary.
        """
        if result.num_rows == 0:
            return {}
        return {
            col: result.column(col)[0].as_py()
            for col in result.column_names
        }

    @staticmethod
    def _arrow_to_dicts(
        result: pa.Table,
        json_fields: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Convert a PyArrow Table to a list of dictionaries.

        Args:
            result: PyArrow Table.
            json_fields: Column names containing JSON strings to parse.

        Returns:
            List of row dictionaries.
        """
        json_fields = json_fields or []
        rows = result.to_pydict()
        num_rows = result.num_rows
        out: list[dict[str, Any]] = []

        for i in range(num_rows):
            row = {col: rows[col][i] for col in result.column_names}
            for field in json_fields:
                if row.get(field):
                    try:
                        row[field] = json.loads(row[field])
                    except (json.JSONDecodeError, TypeError):
                        pass
            out.append(row)

        return out
