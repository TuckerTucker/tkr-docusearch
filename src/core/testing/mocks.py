"""
Consolidated mock implementations for testing.

This module provides unified mock implementations for all external dependencies
in the tkr-docusearch system. Consolidates mocks from:
- src/processing/mocks.py (embedding and storage mocks)
- src/search/mocks.py (search engine mocks)

All mocks follow the Inversion of Control (IoC) principle and match their
respective interface contracts defined in the project documentation.

Usage:
    >>> from src.core.testing.mocks import MockColPaliModel, MockChromaDBClient
    >>> model = MockColPaliModel()
    >>> embeddings = model.embed_images([image1, image2])

Classes:
    MockColPaliModel: Mock ColPali embedding model
    MockEmbeddingEngine: Mock embedding engine (legacy name, same as MockColPaliModel)
    MockChromaDBClient: Mock ChromaDB storage client
    MockStorageClient: Mock storage client (legacy name, same as MockChromaDBClient)
    MockCollection: Mock ChromaDB collection
    MockSearchEngine: Mock two-stage search engine
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

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


class MockColPaliModel:
    """Mock ColPali embedding model for testing.

    Simulates the ColPali embedding engine defined in embedding-interface.md.
    Generates deterministic random embeddings with realistic shapes and timing.

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

    def embed_query(self, query: str) -> Dict[str, Any]:
        """Generate mock multi-vector embedding for search query.

        Args:
            query: Natural language search query

        Returns:
            Dictionary with:
            - embeddings: (seq_length, 768) multi-vector
            - cls_token: (768,) representative vector
            - seq_length: Query token count
            - input_type: "text"
            - processing_time_ms: Simulated time

        Raises:
            ValueError: If query is empty
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        start_time = time.time()

        # Simulate query tokenization (10-30 tokens for typical queries)
        query_words = query.strip().split()
        seq_length = min(max(len(query_words) + 5, 10), 30)

        # Generate random embeddings with some structure
        # Use query hash as seed for reproducibility
        seed = hash(query) % (2**31)
        rng = np.random.default_rng(seed)

        embeddings = rng.standard_normal((seq_length, self.embedding_dim)).astype(np.float32)
        # Normalize to unit vectors
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        cls_token = embeddings[0].copy()

        # Simulate latency (< 100ms for queries)
        if self.simulate_latency:
            time.sleep(0.02)  # 20ms

        processing_time = (time.time() - start_time) * 1000

        return {
            "embeddings": embeddings,
            "cls_token": cls_token,
            "seq_length": seq_length,
            "input_type": "text",
            "processing_time_ms": processing_time,
        }

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


# Legacy alias for backwards compatibility
MockEmbeddingEngine = MockColPaliModel


# ============================================================================
# Mock Storage Clients
# ============================================================================


class MockCollection:
    """Mock ChromaDB collection.

    Simulates a ChromaDB collection with in-memory storage for testing.

    Attributes:
        name: Collection name
        metadata: Collection metadata
        _data: In-memory storage for embeddings
    """

    def __init__(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        """Initialize mock collection.

        Args:
            name: Collection name
            metadata: Optional collection metadata
        """
        self.name = name
        self.metadata = metadata or {}
        self._data: Dict[str, Dict[str, Any]] = {}
        logger.debug(f"Initialized MockCollection: {name}")

    def add(
        self,
        ids: List[str],
        embeddings: List[np.ndarray],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        documents: Optional[List[str]] = None,
    ):
        """Add embeddings to collection.

        Args:
            ids: List of unique IDs
            embeddings: List of embedding vectors
            metadatas: Optional list of metadata dicts
            documents: Optional list of document texts
        """
        for i, item_id in enumerate(ids):
            self._data[item_id] = {
                "id": item_id,
                "embedding": embeddings[i],
                "metadata": metadatas[i] if metadatas else {},
                "document": documents[i] if documents else None,
            }

    def query(
        self,
        query_embeddings: List[np.ndarray],
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, List[List[Any]]]:
        """Query collection for similar embeddings.

        Args:
            query_embeddings: List of query vectors
            n_results: Number of results to return
            where: Optional metadata filter

        Returns:
            Dictionary with ids, distances, metadatas, documents
        """
        results = {"ids": [], "distances": [], "metadatas": [], "documents": []}

        for query_emb in query_embeddings:
            # Compute similarities
            similarities = []
            for item_id, data in self._data.items():
                # Apply filters
                if where and not self._matches_filter(data["metadata"], where):
                    continue

                # Compute cosine similarity
                sim = self._cosine_similarity(query_emb, data["embedding"])
                similarities.append((item_id, sim, data))

            # Sort by similarity and get top-n
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_n = similarities[:n_results]

            # Format results
            results["ids"].append([item[0] for item in top_n])
            results["distances"].append([1.0 - item[1] for item in top_n])  # Convert to distance
            results["metadatas"].append([item[2]["metadata"] for item in top_n])
            results["documents"].append([item[2]["document"] for item in top_n])

        return results

    def get(self, ids: Optional[List[str]] = None) -> Dict[str, List[Any]]:
        """Get items by ID.

        Args:
            ids: Optional list of IDs to retrieve

        Returns:
            Dictionary with ids, embeddings, metadatas, documents
        """
        target_ids = ids if ids else list(self._data.keys())
        return {
            "ids": target_ids,
            "embeddings": [self._data[i]["embedding"] for i in target_ids if i in self._data],
            "metadatas": [self._data[i]["metadata"] for i in target_ids if i in self._data],
            "documents": [self._data[i]["document"] for i in target_ids if i in self._data],
        }

    def delete(self, ids: Optional[List[str]] = None, where: Optional[Dict[str, Any]] = None):
        """Delete items from collection.

        Args:
            ids: Optional list of IDs to delete
            where: Optional metadata filter for deletion
        """
        if ids:
            for item_id in ids:
                self._data.pop(item_id, None)
        elif where:
            to_delete = [
                item_id
                for item_id, data in self._data.items()
                if self._matches_filter(data["metadata"], where)
            ]
            for item_id in to_delete:
                del self._data[item_id]

    def count(self) -> int:
        """Get count of items in collection.

        Returns:
            Number of items
        """
        return len(self._data)

    def _matches_filter(self, metadata: Dict[str, Any], where: Dict[str, Any]) -> bool:
        """Check if metadata matches filter."""
        for key, value in where.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        vec1_flat = vec1.flatten() if vec1.ndim > 1 else vec1
        vec2_flat = vec2.flatten() if vec2.ndim > 1 else vec2

        vec1_norm = vec1_flat / np.linalg.norm(vec1_flat)
        vec2_norm = vec2_flat / np.linalg.norm(vec2_flat)
        return float(np.dot(vec1_norm, vec2_norm))


class MockChromaDBClient:
    """Mock ChromaDB client for testing.

    Simulates the ChromaDB storage client defined in storage-interface.md.
    Stores embeddings in memory using MockCollection instances.

    Attributes:
        host: ChromaDB server host
        port: ChromaDB server port
        visual_collection_name: Visual embeddings collection name
        text_collection_name: Text embeddings collection name
        simulate_latency: Whether to add realistic processing delays
        _visual_collection: Mock visual collection
        _text_collection: Mock text collection

    Example:
        >>> client = MockChromaDBClient()
        >>> client.add_visual_embedding("doc1", 1, embeddings, {"filename": "test.pdf"})
        'doc1-page001'
    """

    def __init__(
        self,
        host: str = "chromadb",
        port: int = 8000,
        visual_collection: str = "visual_collection",
        text_collection: str = "text_collection",
        simulate_latency: bool = False,
    ):
        """Initialize mock ChromaDB client.

        Args:
            host: ChromaDB server host (ignored in mock)
            port: ChromaDB server port (ignored in mock)
            visual_collection: Visual embeddings collection name
            text_collection: Text embeddings collection name
            simulate_latency: If True, add realistic latency to operations
        """
        self.host = host
        self.port = port
        self.visual_collection_name = visual_collection
        self.text_collection_name = text_collection
        self.simulate_latency = simulate_latency

        # Create mock collections
        self._visual_collection = MockCollection(visual_collection)
        self._text_collection = MockCollection(text_collection)

        # Generate initial mock data for search testing
        self._generate_mock_data()

        logger.info(
            f"Initialized MockChromaDBClient (host={host}, port={port}, "
            f"latency={simulate_latency})"
        )

    def _generate_mock_data(self):
        """Generate mock document data for testing."""
        # Create 5 mock documents with varying relevance
        doc_ids = ["doc001", "doc002", "doc003", "doc004", "doc005"]
        filenames = [
            "Q3-2023-Earnings.pdf",
            "Product-Roadmap.pdf",
            "Legal-Contract.pdf",
            "Marketing-Report.pdf",
            "Technical-Specs.pdf",
        ]

        for i, (doc_id, filename) in enumerate(zip(doc_ids, filenames)):
            # Visual embeddings (3 pages per document)
            for page in range(1, 4):
                emb_id = f"{doc_id}-page{page:03d}"
                seq_length = np.random.randint(80, 120)
                embeddings = self._generate_mock_embedding(seq_length, seed=hash(emb_id))

                self._visual_collection.add(
                    ids=[emb_id],
                    embeddings=[embeddings[0]],  # Store CLS token for Stage 1
                    metadatas=[
                        {
                            "filename": filename,
                            "page": page,
                            "doc_id": doc_id,
                            "type": "visual",
                            "seq_length": seq_length,
                            "full_embeddings": embeddings,  # Store full for Stage 2
                        }
                    ],
                )

            # Text embeddings (10 chunks per document)
            for chunk_id in range(10):
                emb_id = f"{doc_id}-chunk{chunk_id:04d}"
                seq_length = np.random.randint(50, 80)
                embeddings = self._generate_mock_embedding(seq_length, seed=hash(emb_id))
                page = (chunk_id // 3) + 1

                self._text_collection.add(
                    ids=[emb_id],
                    embeddings=[embeddings[0]],  # Store CLS token for Stage 1
                    metadatas=[
                        {
                            "filename": filename,
                            "chunk_id": chunk_id,
                            "page": page,
                            "doc_id": doc_id,
                            "type": "text",
                            "seq_length": seq_length,
                            "full_embeddings": embeddings,  # Store full for Stage 2
                            "text_preview": f"Sample text from {filename} chunk {chunk_id}...",
                        }
                    ],
                )

    def _generate_mock_embedding(self, seq_length: int, seed: int = None) -> np.ndarray:
        """Generate mock embedding with given sequence length."""
        if seed is not None:
            rng = np.random.default_rng(seed % (2**31))
        else:
            rng = np.random.default_rng()

        embeddings = rng.standard_normal((seq_length, 768)).astype(np.float32)
        # Normalize to unit vectors
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        return embeddings

    def add_visual_embedding(
        self, doc_id: str, page: int, full_embeddings: np.ndarray, metadata: Dict[str, Any]
    ) -> str:
        """Store visual embedding.

        Args:
            doc_id: Unique document identifier
            page: Page number (1-indexed)
            full_embeddings: Multi-vector sequence, shape (seq_length, 768)
            metadata: Additional metadata

        Returns:
            Embedding ID: "{doc_id}-page{page:03d}"

        Raises:
            ValueError: If embedding shape is invalid
        """
        # Validate shape
        if len(full_embeddings.shape) != 2:
            raise ValueError(
                f"Invalid embedding shape: {full_embeddings.shape}. Expected (seq_length, 768)"
            )

        seq_length, dim = full_embeddings.shape
        # Support both real ColPali (128) and mock (768) dimensions
        if dim not in [128, 768]:
            raise ValueError(f"Invalid embedding dimension: {dim}. Expected 128 or 768")

        # Generate ID
        embedding_id = f"{doc_id}-page{page:03d}"

        # Store in collection
        self._visual_collection.add(
            ids=[embedding_id],
            embeddings=[full_embeddings[0]],  # CLS token for Stage 1
            metadatas=[{**metadata, "full_embeddings": full_embeddings, "seq_length": seq_length}],
        )

        logger.debug(f"Stored visual embedding: {embedding_id} (shape={full_embeddings.shape})")

        return embedding_id

    def add_text_embedding(
        self, doc_id: str, chunk_id: int, full_embeddings: np.ndarray, metadata: Dict[str, Any]
    ) -> str:
        """Store text embedding.

        Args:
            doc_id: Unique document identifier
            chunk_id: Chunk number (0-indexed)
            full_embeddings: Multi-vector sequence, shape (seq_length, 768)
            metadata: Additional metadata

        Returns:
            Embedding ID: "{doc_id}-chunk{chunk_id:04d}"

        Raises:
            ValueError: If embedding shape is invalid
        """
        # Validate shape
        if len(full_embeddings.shape) != 2:
            raise ValueError(
                f"Invalid embedding shape: {full_embeddings.shape}. Expected (seq_length, 768)"
            )

        seq_length, dim = full_embeddings.shape
        # Support both real ColPali (128) and mock (768) dimensions
        if dim not in [128, 768]:
            raise ValueError(f"Invalid embedding dimension: {dim}. Expected 128 or 768")

        # Generate ID
        embedding_id = f"{doc_id}-chunk{chunk_id:04d}"

        # Store in collection
        self._text_collection.add(
            ids=[embedding_id],
            embeddings=[full_embeddings[0]],  # CLS token for Stage 1
            metadatas=[{**metadata, "full_embeddings": full_embeddings, "seq_length": seq_length}],
        )

        logger.debug(f"Stored text embedding: {embedding_id} (shape={full_embeddings.shape})")

        return embedding_id

    def search_visual(
        self,
        query_embedding: np.ndarray,
        n_results: int = 100,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Mock Stage 1 visual search using representative vectors.

        Args:
            query_embedding: Query embedding CLS token, shape (768,)
            n_results: Number of candidates to retrieve
            filters: Optional metadata filters

        Returns:
            List of candidates with scores and metadata
        """
        start_time = time.time()

        if query_embedding.ndim != 1 or query_embedding.shape[0] != 768:
            raise ValueError(f"Query embedding must have shape (768,), got {query_embedding.shape}")

        # Query collection
        results = self._visual_collection.query(
            query_embeddings=[query_embedding], n_results=n_results, where=filters
        )

        # Format results
        candidates = []
        for i, item_id in enumerate(results["ids"][0]):
            metadata = results["metadatas"][0][i]
            candidates.append(
                {
                    "id": item_id,
                    "score": 1.0 - results["distances"][0][i],  # Convert distance to score
                    "metadata": metadata,
                    "full_embeddings": metadata.get("full_embeddings"),
                }
            )

        # Simulate latency
        if self.simulate_latency:
            time.sleep(0.1)

        logger.debug(
            f"Visual search returned {len(candidates)} results in "
            f"{(time.time()-start_time)*1000:.1f}ms"
        )
        return candidates

    def search_text(
        self,
        query_embedding: np.ndarray,
        n_results: int = 100,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Mock Stage 1 text search using representative vectors.

        Args:
            query_embedding: Query embedding CLS token, shape (768,)
            n_results: Number of candidates to retrieve
            filters: Optional metadata filters

        Returns:
            List of candidates with scores and metadata
        """
        start_time = time.time()

        if query_embedding.ndim != 1 or query_embedding.shape[0] != 768:
            raise ValueError(f"Query embedding must have shape (768,), got {query_embedding.shape}")

        # Query collection
        results = self._text_collection.query(
            query_embeddings=[query_embedding], n_results=n_results, where=filters
        )

        # Format results
        candidates = []
        for i, item_id in enumerate(results["ids"][0]):
            metadata = results["metadatas"][0][i]
            candidates.append(
                {
                    "id": item_id,
                    "score": 1.0 - results["distances"][0][i],  # Convert distance to score
                    "metadata": metadata,
                    "full_embeddings": metadata.get("full_embeddings"),
                }
            )

        # Simulate latency
        if self.simulate_latency:
            time.sleep(0.1)

        logger.debug(
            f"Text search returned {len(candidates)} results in "
            f"{(time.time()-start_time)*1000:.1f}ms"
        )
        return candidates

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics.

        Returns:
            Dictionary with collection statistics
        """
        # Get unique doc_ids
        visual_data = self._visual_collection.get()
        text_data = self._text_collection.get()

        visual_docs = set(m.get("doc_id") for m in visual_data.get("metadatas", []))
        text_docs = set(m.get("doc_id") for m in text_data.get("metadatas", []))
        all_docs = visual_docs.union(text_docs)

        return {
            "visual_count": self._visual_collection.count(),
            "text_count": self._text_collection.count(),
            "total_documents": len(all_docs),
            "storage_size_mb": 0.0,  # Mock - no actual storage
            "is_mock": True,
            "mock": True,
        }

    def delete_document(self, doc_id: str) -> Tuple[int, int]:
        """Delete all embeddings for a document.

        Args:
            doc_id: Document identifier

        Returns:
            Tuple of (visual_count, text_count) deleted
        """
        # Delete from visual collection
        visual_data = self._visual_collection.get()
        visual_ids = [
            item_id
            for item_id, metadata in zip(visual_data["ids"], visual_data["metadatas"])
            if metadata.get("doc_id") == doc_id
        ]
        if visual_ids:
            self._visual_collection.delete(ids=visual_ids)

        # Delete from text collection
        text_data = self._text_collection.get()
        text_ids = [
            item_id
            for item_id, metadata in zip(text_data["ids"], text_data["metadatas"])
            if metadata.get("doc_id") == doc_id
        ]
        if text_ids:
            self._text_collection.delete(ids=text_ids)

        logger.info(f"Deleted document {doc_id}: {len(visual_ids)} visual, {len(text_ids)} text")

        return len(visual_ids), len(text_ids)

    def get_full_embeddings(self, embedding_id: str, collection: str = "visual") -> np.ndarray:
        """Retrieve full embeddings.

        Args:
            embedding_id: ID of the embedding
            collection: "visual" or "text"

        Returns:
            Full multi-vector embedding

        Raises:
            ValueError: If embedding_id not found
        """
        coll = self._visual_collection if collection == "visual" else self._text_collection
        data = coll.get(ids=[embedding_id])

        if not data["ids"]:
            raise ValueError(f"Embedding not found: {embedding_id}")

        return data["metadatas"][0].get("full_embeddings")


# Legacy alias for backwards compatibility
MockStorageClient = MockChromaDBClient


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
        storage_client: Optional[MockChromaDBClient] = None,
        simulate_latency: bool = False,
    ):
        """Initialize mock search engine.

        Args:
            embedding_engine: Mock embedding engine (creates new if None)
            storage_client: Mock storage client (creates new if None)
            simulate_latency: If True, add realistic latency to operations
        """
        self.embedding_engine = embedding_engine or MockColPaliModel(
            simulate_latency=simulate_latency
        )
        self.storage_client = storage_client or MockChromaDBClient(
            simulate_latency=simulate_latency
        )
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

        # Embed query
        query_output = self.embedding_engine.embed_query(query)
        query_cls = query_output["cls_token"]
        query_full = query_output["embeddings"]

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
