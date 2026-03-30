"""
Consolidated mock implementations for testing.

This module provides unified mock implementations for all external dependencies
in the tkr-docusearch system. Consolidates mocks from:
- src/processing/mocks.py (embedding and storage mocks)
- src/search/mocks.py (search engine mocks)

All mocks follow the Inversion of Control (IoC) principle and match their
respective interface contracts defined in the project documentation.

Usage:
    >>> from src.core.testing.mocks import MockColPaliModel, MockKojiClient
    >>> model = MockColPaliModel()
    >>> embeddings = model.embed_images([image1, image2])

Classes:
    MockColPaliModel: Mock ColPali embedding model
    MockEmbeddingEngine: Mock embedding engine (alias for MockColPaliModel)
    MockKojiClient: Mock Koji storage client
    MockStorageClient: Mock storage client (alias for MockKojiClient)
    MockSearchEngine: Mock two-stage search engine
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class BatchEmbeddingOutput:
    """Batch embedding output matching embedding interface.

    Attributes:
        embeddings: List of multi-vector embeddings, each (seq_length, 768)
        cls_tokens: Representative vectors, shape (batch_size, 768)
        seq_lengths: Token counts for each item
        input_type: "visual" or "text"
        batch_processing_time_ms: Total batch processing time
    """

    embeddings: List[np.ndarray]
    cls_tokens: np.ndarray
    seq_lengths: List[int]
    input_type: str
    batch_processing_time_ms: float


# ============================================================================
# Mock Embedding Models
# ============================================================================


class MockEmbeddingModel:
    """Mock multimodal embedding model for testing.

    Simulates the Shikomi embedding service with deterministic random embeddings,
    realistic shapes, and timing.

    This mock supports both visual (image) and text embeddings with configurable
    dimensions and latency simulation.

    Attributes:
        model_name: Model identifier
        device: Target device (e.g., "mps", "cuda", "cpu")
        embedding_dim: Embedding dimension (default: 768)
        simulate_latency: Whether to add realistic processing delays
        is_loaded: Whether model is loaded (always True for mock)

    Example:
        >>> model = MockColPaliModel(device="mps")
        >>> images = [Image.new("RGB", (224, 224))]
        >>> output = model.embed_images(images)
        >>> print(output.embeddings[0].shape)
        (100, 768)  # approximately
    """

    def __init__(
        self,
        model_name: str = "nomic-ai/colnomic-embed-multimodal-7b",
        device: str = "mps",
        embedding_dim: int = 768,
        simulate_latency: bool = True,
        **kwargs,
    ):
        """Initialize mock ColPali model.

        Args:
            model_name: Model identifier (ignored in mock)
            device: Target device (ignored in mock)
            embedding_dim: Embedding dimension (default: 768)
            simulate_latency: If True, add realistic latency to operations
            **kwargs: Additional arguments (ignored in mock)
        """
        self.model_name = model_name
        self.device = device
        self.embedding_dim = embedding_dim
        self.simulate_latency = simulate_latency
        self.is_loaded = True
        logger.info(
            f"Initialized MockColPaliModel (device={device}, dim={embedding_dim}, "
            f"latency={simulate_latency})"
        )

    def embed_images(self, images: List[Image.Image], batch_size: int = 4) -> BatchEmbeddingOutput:
        """Generate mock multi-vector embeddings for images.

        Args:
            images: List of PIL Images (document pages)
            batch_size: Number of images to process at once (ignored in mock)

        Returns:
            BatchEmbeddingOutput with mock embeddings

        Raises:
            ValueError: If images list is empty

        Performance simulation:
            - Typical token count: 100 per page (range 80-120)
            - Simulates ~6s per image for FP16 (if latency enabled)
        """
        if not images:
            raise ValueError("Images list cannot be empty")

        num_images = len(images)
        logger.debug(f"Embedding {num_images} images (mock)")

        embeddings = []
        seq_lengths = []

        for _ in images:
            # Visual embeddings typically have 80-120 tokens
            seq_length = np.random.randint(80, 121)
            seq_lengths.append(seq_length)

            # Generate random multi-vector embedding
            embedding = np.random.randn(seq_length, self.embedding_dim).astype(np.float32)
            # Normalize to unit vectors
            embedding = embedding / np.linalg.norm(embedding, axis=1, keepdims=True)
            embeddings.append(embedding)

        # CLS tokens are first token of each embedding
        cls_tokens = np.array([emb[0] for emb in embeddings], dtype=np.float32)

        # Simulate processing time
        if self.simulate_latency:
            time.sleep(0.02 * num_images)  # 20ms per image
        simulated_time_ms = num_images * 6000.0 if self.simulate_latency else 0.0

        return BatchEmbeddingOutput(
            embeddings=embeddings,
            cls_tokens=cls_tokens,
            seq_lengths=seq_lengths,
            input_type="visual",
            batch_processing_time_ms=simulated_time_ms,
        )

    def embed_texts(self, texts: List[str], batch_size: int = 8) -> BatchEmbeddingOutput:
        """Generate mock multi-vector embeddings for texts.

        Args:
            texts: List of text chunks (avg 250 words)
            batch_size: Number of texts to process at once (ignored in mock)

        Returns:
            BatchEmbeddingOutput with mock embeddings

        Raises:
            ValueError: If texts list is empty

        Performance simulation:
            - Typical token count: 64 per chunk (range 50-80)
            - Simulates ~2s per chunk for FP16 (if latency enabled)
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")

        num_texts = len(texts)
        logger.debug(f"Embedding {num_texts} text chunks (mock)")

        embeddings = []
        seq_lengths = []

        for _ in texts:
            # Text embeddings typically have 50-80 tokens
            seq_length = np.random.randint(50, 81)
            seq_lengths.append(seq_length)

            # Generate random multi-vector embedding
            embedding = np.random.randn(seq_length, self.embedding_dim).astype(np.float32)
            # Normalize to unit vectors
            embedding = embedding / np.linalg.norm(embedding, axis=1, keepdims=True)
            embeddings.append(embedding)

        # CLS tokens are first token of each embedding
        cls_tokens = np.array([emb[0] for emb in embeddings], dtype=np.float32)

        # Simulate processing time
        if self.simulate_latency:
            time.sleep(0.01 * num_texts)  # 10ms per text
        simulated_time_ms = num_texts * 2000.0 if self.simulate_latency else 0.0

        return BatchEmbeddingOutput(
            embeddings=embeddings,
            cls_tokens=cls_tokens,
            seq_lengths=seq_lengths,
            input_type="text",
            batch_processing_time_ms=simulated_time_ms,
        )

    def embed_query(self, query: str) -> list[list[float]]:
        """Generate mock multi-vector embedding for search query.

        Returns list[list[float]] matching the embedding engine contract.

        Args:
            query: Natural language search query.

        Returns:
            Multi-vector embedding as nested list of floats.

        Raises:
            ValueError: If query is empty.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        query_words = query.strip().split()
        seq_length = min(max(len(query_words) + 5, 10), 30)

        seed = hash(query) % (2**31)
        rng = np.random.default_rng(seed)

        embeddings = rng.standard_normal((seq_length, self.embedding_dim)).astype(np.float32)
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        return embeddings.tolist()

    def score_multi_vector(
        self,
        query_embeddings: np.ndarray,
        document_embeddings: List[np.ndarray],
        use_gpu: bool = True,
    ) -> Dict[str, Any]:
        """Mock late interaction scoring using MaxSim algorithm.

        Args:
            query_embeddings: Query multi-vector, shape (query_tokens, 768)
            document_embeddings: List of document multi-vectors, each (doc_tokens, 768)
            use_gpu: Use GPU for scoring (not used in mock)

        Returns:
            Dictionary with:
            - scores: List of MaxSim scores (0-1 range)
            - scoring_time_ms: Simulated time
            - num_candidates: len(document_embeddings)

        Raises:
            ValueError: If embedding shapes are incompatible
        """
        if query_embeddings.ndim != 2 or query_embeddings.shape[1] != self.embedding_dim:
            raise ValueError(
                f"Query embeddings must have shape (seq_length, {self.embedding_dim}), "
                f"got {query_embeddings.shape}"
            )

        start_time = time.time()

        scores = []
        for doc_emb in document_embeddings:
            if doc_emb.ndim != 2 or doc_emb.shape[1] != self.embedding_dim:
                raise ValueError(
                    f"Document embeddings must have shape (seq_length, {self.embedding_dim}), "
                    f"got {doc_emb.shape}"
                )

            # Compute MaxSim score
            score = self._maxsim_score(query_embeddings, doc_emb)
            scores.append(float(score))

        # Simulate latency (~1ms per document)
        if self.simulate_latency:
            time.sleep(0.001 * len(document_embeddings))

        scoring_time = (time.time() - start_time) * 1000

        return {
            "scores": scores,
            "scoring_time_ms": scoring_time,
            "num_candidates": len(document_embeddings),
        }

    def _maxsim_score(self, query_emb: np.ndarray, doc_emb: np.ndarray) -> float:
        """Compute MaxSim score between query and document.

        For each query token:
            Find max cosine similarity with any document token
        Sum these max similarities across all query tokens
        Normalize to [0, 1]

        Args:
            query_emb: Query embeddings (Q, dim)
            doc_emb: Document embeddings (D, dim)

        Returns:
            Normalized MaxSim score
        """
        Q, _ = query_emb.shape

        # Normalize embeddings
        query_norm = query_emb / np.linalg.norm(query_emb, axis=1, keepdims=True)
        doc_norm = doc_emb / np.linalg.norm(doc_emb, axis=1, keepdims=True)

        # Compute similarity matrix (Q x D)
        similarity_matrix = np.matmul(query_norm, doc_norm.T)

        # MaxSim: max over doc tokens for each query token, then sum
        max_similarities = np.max(similarity_matrix, axis=1)
        score = np.sum(max_similarities)

        # Normalize by query length to [0, 1]
        normalized_score = score / Q

        return normalized_score

    def get_model_info(self) -> Dict[str, Any]:
        """Get mock model configuration.

        Returns:
            Dictionary with model metadata
        """
        return {
            "model_name": self.model_name,
            "device": self.device,
            "dtype": "bfloat16",
            "quantization": None,
            "memory_allocated_mb": 0.0,
            "is_loaded": self.is_loaded,
            "cache_dir": "/models",
            "is_mock": True,
            "mock": True,
        }

    def clear_cache(self):
        """Mock cache clearing (no-op)."""
        logger.debug("Cache clear requested (mock - no-op)")


# Aliases for backwards compatibility
MockEmbeddingEngine = MockEmbeddingModel
MockColPaliModel = MockEmbeddingModel


# ============================================================================
# Mock Storage Clients
# ============================================================================


class MockKojiClient:
    """In-memory mock of KojiClient for testing.

    Mirrors the public API of ``src.storage.koji_client.KojiClient`` so that
    any code accepting a KojiClient via dependency injection can be tested
    without a real Koji database.

    Attributes:
        _documents: In-memory document store keyed by doc_id.
        _pages: In-memory list of page dicts.
        _chunks: In-memory list of chunk dicts.
        _relations: In-memory list of relation dicts.
        _open: Whether the mock client is "connected".

    Example:
        >>> client = MockKojiClient()
        >>> client.open()
        >>> client.create_document("doc1", "test.pdf", "pdf")
        >>> client.get_document("doc1")["filename"]
        'test.pdf'
    """

    def __init__(self) -> None:
        """Initialize mock Koji client with empty in-memory stores."""
        self._documents: Dict[str, Dict[str, Any]] = {}
        self._pages: List[Dict[str, Any]] = []
        self._chunks: List[Dict[str, Any]] = []
        self._relations: List[Dict[str, Any]] = []
        self._open: bool = False

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    def open(self) -> None:
        """Mark the mock client as connected."""
        self._open = True

    def close(self) -> None:
        """Mark the mock client as disconnected."""
        self._open = False

    def sync(self) -> None:
        """No-op — in-memory store requires no syncing."""

    # ------------------------------------------------------------------
    # Health / introspection
    # ------------------------------------------------------------------

    def health_check(self) -> Dict[str, Any]:
        """Return mock health status.

        Returns:
            Dictionary with connection status and table list.
        """
        return {
            "connected": self._open,
            "db_path": ":memory:",
            "tables": ["documents", "pages", "chunks", "doc_relations"],
        }

    # ------------------------------------------------------------------
    # Document CRUD
    # ------------------------------------------------------------------

    def create_document(
        self,
        doc_id: str,
        filename: str,
        format: str,
        num_pages: Optional[int] = None,
        markdown: Optional[str] = None,
        metadata: Optional[str] = None,
        project_id: str = "default",
    ) -> None:
        """Create a document record.

        Args:
            doc_id: Unique document identifier (primary key).
            filename: Original filename.
            format: File format (e.g. "pdf", "docx").
            num_pages: Number of pages (optional).
            markdown: Extracted markdown content (optional).
            metadata: JSON-encoded metadata string (optional).
            project_id: Project to assign the document to.
        """
        from datetime import datetime, timezone

        self._documents[doc_id] = {
            "doc_id": doc_id,
            "project_id": project_id,
            "filename": filename,
            "format": format,
            "num_pages": num_pages,
            "markdown": markdown,
            "metadata": metadata,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a document by ID.

        Args:
            doc_id: Document identifier.

        Returns:
            Document dict or ``None`` if not found.
        """
        return self._documents.get(doc_id)

    def list_documents(
        self,
        format: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List documents with optional format and project filters.

        Args:
            format: Filter by file format (optional).
            project_id: Filter by project (optional).
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            List of document dicts.
        """
        docs = list(self._documents.values())
        if format:
            docs = [d for d in docs if d["format"] == format]
        if project_id is not None:
            docs = [d for d in docs if d.get("project_id") == project_id]
        return docs[offset : offset + limit]

    def update_document(self, doc_id: str, **fields: Any) -> None:
        """Update fields on an existing document.

        Args:
            doc_id: Document identifier.
            **fields: Key-value pairs to update.
        """
        if doc_id in self._documents:
            self._documents[doc_id].update(fields)

    def delete_document(self, doc_id: str) -> None:
        """Delete a document and all associated pages, chunks, and relations.

        Args:
            doc_id: Document identifier.
        """
        self._documents.pop(doc_id, None)
        self._pages = [p for p in self._pages if p.get("doc_id") != doc_id]
        self._chunks = [c for c in self._chunks if c.get("doc_id") != doc_id]
        self._relations = [
            r
            for r in self._relations
            if r.get("src_doc_id") != doc_id and r.get("dst_doc_id") != doc_id
        ]

    # ------------------------------------------------------------------
    # Page operations
    # ------------------------------------------------------------------

    def insert_pages(self, pages: List[Dict[str, Any]]) -> None:
        """Insert page records.

        Args:
            pages: List of page dicts (must include ``id``, ``doc_id``, ``page_num``).
        """
        self._pages.extend(pages)

    def get_pages_for_document(self, doc_id: str) -> List[Dict[str, Any]]:
        """Get all pages for a document, sorted by page number.

        Args:
            doc_id: Document identifier.

        Returns:
            Sorted list of page dicts.
        """
        return sorted(
            [p for p in self._pages if p.get("doc_id") == doc_id],
            key=lambda p: p.get("page_num", 0),
        )

    def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get a single page by ID.

        Args:
            page_id: Page identifier.

        Returns:
            Page dict or ``None`` if not found.
        """
        return next((p for p in self._pages if p.get("id") == page_id), None)

    # ------------------------------------------------------------------
    # Chunk operations
    # ------------------------------------------------------------------

    def insert_chunks(self, chunks: List[Dict[str, Any]]) -> None:
        """Insert chunk records.

        Args:
            chunks: List of chunk dicts (must include ``id``, ``doc_id``, ``page_num``).
        """
        self._chunks.extend(chunks)

    def get_chunks_for_document(self, doc_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a document, sorted by page then chunk ID.

        Args:
            doc_id: Document identifier.

        Returns:
            Sorted list of chunk dicts.
        """
        return sorted(
            [c for c in self._chunks if c.get("doc_id") == doc_id],
            key=lambda c: (c.get("page_num", 0), c.get("id", "")),
        )

    def get_chunk(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Get a single chunk by ID.

        Args:
            chunk_id: Chunk identifier.

        Returns:
            Chunk dict or ``None`` if not found.
        """
        return next((c for c in self._chunks if c.get("id") == chunk_id), None)

    # ------------------------------------------------------------------
    # Relation operations
    # ------------------------------------------------------------------

    def create_relation(
        self,
        src_doc_id: str,
        dst_doc_id: str,
        relation_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Create a relationship between two documents.

        Args:
            src_doc_id: Source document identifier.
            dst_doc_id: Destination document identifier.
            relation_type: Relationship type (e.g. ``references``, ``version_of``).
            metadata: Optional metadata dict.

        Raises:
            ValueError: If either document does not exist.
            KojiDuplicateError: If the relation already exists.
        """
        from src.storage.koji_client import KojiDuplicateError

        if src_doc_id not in self._documents:
            raise ValueError(f"Source document {src_doc_id} not found")
        if dst_doc_id not in self._documents:
            raise ValueError(f"Destination document {dst_doc_id} not found")

        for r in self._relations:
            if (
                r["src_doc_id"] == src_doc_id
                and r["dst_doc_id"] == dst_doc_id
                and r["relation_type"] == relation_type
            ):
                raise KojiDuplicateError(
                    f"Relation {src_doc_id} -{relation_type}-> {dst_doc_id} already exists"
                )

        self._relations.append({
            "src_doc_id": src_doc_id,
            "dst_doc_id": dst_doc_id,
            "relation_type": relation_type,
            "metadata": metadata,
        })

    def get_relations(
        self,
        doc_id: str,
        relation_type: Optional[str] = None,
        direction: str = "both",
    ) -> List[Dict[str, Any]]:
        """Get relations for a document.

        Args:
            doc_id: Document identifier.
            relation_type: Optional filter by relation type.
            direction: ``"outgoing"``, ``"incoming"``, or ``"both"``.

        Returns:
            List of matching relation dicts.
        """
        results: List[Dict[str, Any]] = []

        for r in self._relations:
            if direction in ("outgoing", "both") and r["src_doc_id"] == doc_id:
                results.append(r)
            elif direction in ("incoming", "both") and r["dst_doc_id"] == doc_id:
                if r not in results:
                    results.append(r)

        if relation_type is not None:
            results = [r for r in results if r["relation_type"] == relation_type]

        return results

    def delete_relation(
        self,
        src_doc_id: str,
        dst_doc_id: str,
        relation_type: str,
    ) -> None:
        """Delete a specific relationship. Idempotent.

        Args:
            src_doc_id: Source document identifier.
            dst_doc_id: Destination document identifier.
            relation_type: Relationship type.
        """
        self._relations = [
            r
            for r in self._relations
            if not (
                r["src_doc_id"] == src_doc_id
                and r["dst_doc_id"] == dst_doc_id
                and r["relation_type"] == relation_type
            )
        ]

    def get_related_documents(
        self,
        root_doc_id: str,
        max_depth: int = 3,
    ) -> List[Dict[str, Any]]:
        """Find all documents related to a root document via graph traversal.

        BFS over outgoing edges in ``_relations``, up to ``max_depth`` hops.

        Args:
            root_doc_id: Starting document identifier.
            max_depth: Maximum traversal depth.

        Returns:
            List of related document dicts with ``depth`` and ``relation_type``.
        """
        from collections import deque

        visited: set[str] = {root_doc_id}
        queue: deque[tuple[str, int, str]] = deque()

        # Seed with direct outgoing neighbors
        for r in self._relations:
            if r["src_doc_id"] == root_doc_id and r["dst_doc_id"] not in visited:
                queue.append((r["dst_doc_id"], 1, r["relation_type"]))
                visited.add(r["dst_doc_id"])

        results: List[Dict[str, Any]] = []
        while queue:
            doc_id, depth, rel_type = queue.popleft()
            doc = self._documents.get(doc_id)
            if doc is not None:
                result = dict(doc)
                result["depth"] = depth
                result["relation_type"] = rel_type
                results.append(result)

            if depth < max_depth:
                for r in self._relations:
                    if r["src_doc_id"] == doc_id and r["dst_doc_id"] not in visited:
                        queue.append((r["dst_doc_id"], depth + 1, r["relation_type"]))
                        visited.add(r["dst_doc_id"])

        results.sort(key=lambda r: r["depth"])
        return results

    # ------------------------------------------------------------------
    # Graph operations
    # ------------------------------------------------------------------

    def graph_pagerank(
        self,
        damping: float = 0.85,
        max_iterations: int = 100,
        tolerance: float = 1e-6,
        project_id: Optional[str] = None,
    ) -> dict[str, float]:
        """Compute PageRank scores for all documents in the graph.

        Simple iterative PageRank over ``_relations`` treated as directed
        edges.  Scores sum to approximately 1.0.

        Args:
            damping: Damping factor (0-1). Higher values follow links more.
            max_iterations: Maximum PageRank iterations.
            tolerance: Convergence threshold.

        Returns:
            Mapping of doc_id to PageRank score (float).
        """
        if not self._documents:
            return {}

        n = len(self._documents)
        doc_ids = sorted(self._documents)
        scores: dict[str, float] = {d: 1.0 / n for d in doc_ids}

        # Build adjacency: outgoing edges per doc
        out_edges: dict[str, list[str]] = {d: [] for d in doc_ids}
        for r in self._relations:
            src, dst = r["src_doc_id"], r["dst_doc_id"]
            if src in out_edges:
                out_edges[src].append(dst)

        for _ in range(max_iterations):
            new_scores: dict[str, float] = {}
            for doc_id in doc_ids:
                rank_sum = 0.0
                for r in self._relations:
                    if r["dst_doc_id"] == doc_id:
                        src = r["src_doc_id"]
                        out_count = len(out_edges.get(src, []))
                        if out_count > 0:
                            rank_sum += scores.get(src, 0.0) / out_count
                new_scores[doc_id] = (1 - damping) / n + damping * rank_sum

            # Check convergence
            diff = sum(abs(new_scores[d] - scores[d]) for d in doc_ids)
            scores = new_scores
            if diff < tolerance:
                break

        return scores

    def graph_label_propagation(
        self,
        max_iterations: int = 100,
        project_id: Optional[str] = None,
    ) -> dict[str, int]:
        """Assign community labels to documents via union-find on relations.

        Groups connected doc_ids into communities by treating all relations
        as undirected edges.  Each connected component receives a sequential
        integer label starting at 0.

        Args:
            max_iterations: Maximum iterations (unused in mock — included
                for API compatibility with the real client).

        Returns:
            Mapping of doc_id to community label (int).
        """
        parent: dict[str, str] = {doc_id: doc_id for doc_id in self._documents}

        def _find(x: str) -> str:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def _union(a: str, b: str) -> None:
            ra, rb = _find(a), _find(b)
            if ra != rb:
                parent[ra] = rb

        for r in self._relations:
            src, dst = r["src_doc_id"], r["dst_doc_id"]
            if src in parent and dst in parent:
                _union(src, dst)

        # Map each root to a sequential label
        root_to_label: dict[str, int] = {}
        label_counter = 0
        result: dict[str, int] = {}
        for doc_id in sorted(self._documents):
            root = _find(doc_id)
            if root not in root_to_label:
                root_to_label[root] = label_counter
                label_counter += 1
            result[doc_id] = root_to_label[root]

        return result

    def graph_shortest_paths(
        self,
        source_doc_id: str,
        project_id: Optional[str] = None,
    ) -> dict[str, float]:
        """Compute shortest-path distances from a source document via BFS.

        Traverses outgoing edges in ``_relations``.  Each hop counts as
        distance 1.  Documents unreachable from the source are omitted.

        Args:
            source_doc_id: Starting document identifier.

        Returns:
            Mapping of reachable doc_id to hop-count distance (float).
            The source itself is included with distance 0.0.

        Raises:
            ValueError: If source_doc_id does not exist.
        """
        from collections import deque

        if source_doc_id not in self._documents:
            raise ValueError(f"Source document {source_doc_id} not found")

        distances: dict[str, float] = {source_doc_id: 0.0}
        queue: deque[str] = deque([source_doc_id])

        while queue:
            current = queue.popleft()
            current_dist = distances[current]
            for r in self._relations:
                if r["src_doc_id"] == current and r["dst_doc_id"] not in distances:
                    distances[r["dst_doc_id"]] = current_dist + 1.0
                    queue.append(r["dst_doc_id"])

        return distances

    def graph_scc(self, project_id: Optional[str] = None) -> dict[str, int]:
        """Return strongly-connected-component labels for all documents.

        This mock treats every document as its own SCC (component label
        equals the document's sorted index).  A real implementation would
        use Tarjan's algorithm.

        Returns:
            Mapping of doc_id to SCC label (int).
        """
        return {
            doc_id: idx
            for idx, doc_id in enumerate(sorted(self._documents))
        }

    def graph_topological_sort(self, project_id: Optional[str] = None) -> list[str]:
        """Return a topological ordering of document IDs.

        This mock returns doc_ids sorted alphabetically.  A real
        implementation would perform a depth-first topological sort
        on the directed relation graph.

        Returns:
            List of doc_ids in sorted order.
        """
        return sorted(self._documents)

    def graph_has_cycle(self, project_id: Optional[str] = None) -> bool:
        """Detect whether the directed relation graph contains a cycle.

        Performs iterative DFS with three-color marking (white/gray/black)
        over outgoing edges in ``_relations``.

        Returns:
            ``True`` if a cycle exists, ``False`` otherwise.
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {doc_id: WHITE for doc_id in self._documents}

        # Build adjacency list for efficient traversal
        adj: dict[str, list[str]] = {doc_id: [] for doc_id in self._documents}
        for r in self._relations:
            src, dst = r["src_doc_id"], r["dst_doc_id"]
            if src in adj:
                adj[src].append(dst)

        for start in self._documents:
            if color[start] != WHITE:
                continue
            stack: list[tuple[str, int]] = [(start, 0)]
            color[start] = GRAY
            while stack:
                node, idx = stack.pop()
                if idx < len(adj[node]):
                    stack.append((node, idx + 1))
                    neighbor = adj[node][idx]
                    if neighbor not in color:
                        continue
                    if color[neighbor] == GRAY:
                        return True
                    if color[neighbor] == WHITE:
                        color[neighbor] = GRAY
                        stack.append((neighbor, 0))
                else:
                    color[node] = BLACK

        return False

    def delete_relations_by_type(self, relation_type: str) -> int:
        """Delete all relations matching a given type.

        Args:
            relation_type: The relation type to remove (e.g. ``"references"``).

        Returns:
            Number of relations removed.
        """
        original_count = len(self._relations)
        self._relations = [
            r for r in self._relations if r["relation_type"] != relation_type
        ]
        return original_count - len(self._relations)

    # ------------------------------------------------------------------
    # Raw operations (not supported in mock)
    # ------------------------------------------------------------------

    def query(self, sql: str, params: Optional[List[Any]] = None) -> Any:
        """Not supported in mock — raises ``KojiQueryError``.

        Mirrors the real KojiClient contract where ``query()`` raises
        ``KojiQueryError`` on failure, so callers that catch
        ``KojiQueryError`` behave correctly under test.

        Args:
            sql: SQL query string.
            params: Optional query parameters.

        Raises:
            KojiQueryError: Always — raw SQL is not supported in mock.
        """
        from src.storage.koji_client import KojiQueryError

        raise KojiQueryError("MockKojiClient does not support raw SQL")

    def insert(self, table: str, data: Any) -> None:
        """Not supported in mock — raises ``NotImplementedError``.

        Args:
            table: Target table name.
            data: Data to insert.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError("MockKojiClient does not support raw insert")


# Alias for backwards compatibility and generic naming
MockStorageClient = MockKojiClient


# ============================================================================
# Mock Search Engine
# ============================================================================


class MockSearchEngine:
    """Mock two-stage search engine for testing.

    Simulates the complete two-stage search pipeline:
    - Stage 1: Fast retrieval using HNSW with representative vectors
    - Stage 2: Precise re-ranking using MaxSim with full embeddings

    Attributes:
        embedding_engine: Mock embedding engine
        storage_client: Mock storage client
        simulate_latency: Whether to add realistic processing delays

    Example:
        >>> engine = MockSearchEngine()
        >>> results = engine.search("quarterly earnings", limit=10)
        >>> print(len(results))
        10
    """

    def __init__(
        self,
        embedding_engine: Optional[MockColPaliModel] = None,
        storage_client: Any = None,
        simulate_latency: bool = False,
    ):
        """Initialize mock search engine.

        Args:
            embedding_engine: Mock embedding engine (creates new if None)
            storage_client: Storage client instance (accepts any implementation)
            simulate_latency: If True, add realistic latency to operations
        """
        self.embedding_engine = embedding_engine or MockColPaliModel(
            simulate_latency=simulate_latency
        )
        self.storage_client = storage_client
        self.simulate_latency = simulate_latency
        logger.info(f"Initialized MockSearchEngine (latency={simulate_latency})")

    def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        search_visual: bool = True,
        search_text: bool = True,
    ) -> List[Dict[str, Any]]:
        """Execute two-stage search.

        Args:
            query: Natural language search query
            limit: Number of final results to return
            filters: Optional metadata filters
            search_visual: Whether to search visual embeddings
            search_text: Whether to search text embeddings

        Returns:
            List of search results with scores and metadata

        Raises:
            ValueError: If query is empty or both search types are False
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if not search_visual and not search_text:
            raise ValueError("At least one of search_visual or search_text must be True")

        # Embed query — returns list[list[float]] per engine contract
        query_vecs = self.embedding_engine.embed_query(query)
        query_full = np.array(query_vecs, dtype=np.float32)
        query_cls = query_full[0]  # First token as representative vector

        # Stage 1: Fast retrieval
        stage1_limit = limit * 10  # Retrieve 10x for re-ranking
        candidates = []

        if search_visual:
            visual_candidates = self.storage_client.search_visual(
                query_cls, n_results=stage1_limit, filters=filters
            )
            candidates.extend(visual_candidates)

        if search_text:
            text_candidates = self.storage_client.search_text(
                query_cls, n_results=stage1_limit, filters=filters
            )
            candidates.extend(text_candidates)

        # Stage 2: MaxSim re-ranking
        doc_embeddings = []
        for candidate in candidates:
            full_emb = candidate.get("full_embeddings")
            if full_emb is not None:
                doc_embeddings.append(full_emb)
            else:
                # Fallback: use CLS token repeated
                doc_embeddings.append(np.array([candidate["metadata"]["representative_vector"]]))

        scoring_output = self.embedding_engine.score_multi_vector(query_full, doc_embeddings)

        # Update scores and sort
        for i, candidate in enumerate(candidates):
            candidate["stage1_score"] = candidate["score"]
            candidate["stage2_score"] = scoring_output["scores"][i]
            candidate["score"] = scoring_output["scores"][i]  # Use Stage 2 score

        candidates.sort(key=lambda x: x["score"], reverse=True)

        # Return top-n
        return candidates[:limit]


# ============================================================================
# Mock Shikomi Ingester & ColNomic Engine
# ============================================================================


class MockColNomicEngine:
    """Mock ColNomicEngine for testing.

    Provides encode_queries, encode_documents, and encode_images
    methods that return deterministic MultiVectorEmbedding objects.

    Args:
        embedding_dim: Dimension of generated embeddings.
    """

    def __init__(self, embedding_dim: int = 128):
        self.embedding_dim = embedding_dim

    async def encode_queries(self, texts):
        return self._make_embeddings(texts, num_tokens=32)

    async def encode_documents(self, texts):
        return self._make_embeddings(texts, num_tokens=64)

    async def encode_images(self, images):
        return self._make_embeddings(images, num_tokens=48)

    def _make_embeddings(self, items, num_tokens=64):
        from shikomi.types import MultiVectorEmbedding
        results = []
        for _ in items:
            data = np.random.randn(num_tokens, self.embedding_dim).astype(np.float32)
            data = data / np.linalg.norm(data, axis=1, keepdims=True)
            results.append(MultiVectorEmbedding(
                num_tokens=num_tokens,
                dim=self.embedding_dim,
                data=data,
            ))
        return results


class MockShikomiIngester:
    """Mock ShikomiIngester for testing without GPU/model loading.

    Returns deterministic IngestResult objects with controllable
    chunk counts and embedding dimensions.

    Args:
        mock_result: Optional pre-built IngestResult to return.
        num_chunks: Number of chunks to generate (default 3).
        embedding_dim: Embedding dimension (default 128).
    """

    def __init__(
        self,
        mock_result=None,
        num_chunks: int = 3,
        embedding_dim: int = 128,
    ):
        self._result = mock_result
        self._num_chunks = num_chunks
        self._embedding_dim = embedding_dim
        self.engine = MockColNomicEngine(embedding_dim=embedding_dim)
        self._connected = False

    def connect(self):
        self._connected = True

    def close(self):
        self._connected = False

    def health_check(self):
        return {"connected": self._connected, "device": "mock", "quantization": "mock", "mode": "mock"}

    def process(self, file_path: str, status_bridge=None) -> "IngestResult":
        if self._result is not None:
            return self._result
        return _make_default_ingest_result(
            file_path, self._num_chunks, self._embedding_dim,
        )

    def _run_async(self, coro):
        """Sync stub -- mock doesn't need async bridging."""
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


def _make_default_ingest_result(
    file_path: str,
    num_chunks: int = 3,
    embedding_dim: int = 128,
) -> "IngestResult":
    """Build a deterministic IngestResult for testing."""
    import hashlib
    import os
    from shikomi import IngestResult
    from shikomi.types import MultiVectorEmbedding, TextChunk, ChunkContext

    filename = os.path.basename(file_path)
    content_hash = hashlib.sha256(file_path.encode()).hexdigest()

    chunks = []
    text_embeddings = []
    for i in range(num_chunks):
        chunk_id = f"{content_hash[:16]}-chunk{i:03d}"
        chunks.append(TextChunk(
            id=chunk_id,
            content=f"Mock chunk {i} content from {filename}.",
            source_path=file_path,
            start_char=i * 100,
            end_char=(i + 1) * 100,
            page=1,
            context=ChunkContext(
                parent_heading=f"Section {i}",
                section_path=f"Doc > Section {i}",
                element_type="text",
            ),
        ))

        data = np.random.randn(64, embedding_dim).astype(np.float32)
        data = data / np.linalg.norm(data, axis=1, keepdims=True)
        text_embeddings.append(MultiVectorEmbedding(
            num_tokens=64, dim=embedding_dim, data=data,
        ))

    return IngestResult(
        chunks=chunks,
        text_embeddings=text_embeddings,
        metadata={"filename": filename, "format_type": "document"},
        source_path=file_path,
        source_type="document",
        content_hash=content_hash,
        chunk_count=num_chunks,
        processing_time_ms=100.0,
    )
