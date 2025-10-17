"""
Mock implementations for embedding and storage interfaces.

These mocks are used during Wave 2 development to simulate dependencies
that will be implemented in Wave 3.

Usage:
    >>> from src.search.mocks import MockEmbeddingEngine, MockStorageClient
    >>> engine = MockEmbeddingEngine()
    >>> storage = MockStorageClient()
"""

import logging
import time
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class MockEmbeddingEngine:
    """
    Mock ColPali embedding engine for testing.

    Simulates the ColPaliEngine interface defined in embedding-interface.md
    without requiring the actual model. Uses random embeddings with consistent
    dimensions and behavior.
    """

    def __init__(
        self,
        model_name: str = "nomic-ai/colnomic-embed-multimodal-7b",
        device: str = "mps",
        embedding_dim: int = 768,
        simulate_latency: bool = True,
    ):
        """
        Initialize mock embedding engine.

        Args:
            model_name: Model identifier (not used, for interface compatibility)
            device: Device string (not used, for interface compatibility)
            embedding_dim: Embedding dimension (default: 768)
            simulate_latency: If True, add realistic latency to operations
        """
        self.model_name = model_name
        self.device = device
        self.embedding_dim = embedding_dim
        self.simulate_latency = simulate_latency
        self.is_loaded = True

        logger.info(
            f"Initialized MockEmbeddingEngine (dim={embedding_dim}, " f"latency={simulate_latency})"
        )

    def embed_query(self, query: str) -> Dict[str, Any]:
        """
        Generate mock multi-vector embedding for search query.

        Args:
            query: Natural language search query

        Returns:
            EmbeddingOutput with:
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
        """
        Mock late interaction scoring using MaxSim algorithm.

        Args:
            query_embeddings: Query multi-vector, shape (query_tokens, 768)
            document_embeddings: List of document multi-vectors, each (doc_tokens, 768)
            use_gpu: Use GPU for scoring (not used in mock)

        Returns:
            ScoringOutput with:
            - scores: List of MaxSim scores (0-1 range)
            - scoring_time_ms: Simulated time
            - num_candidates: len(document_embeddings)

        Raises:
            ValueError: If embedding shapes incompatible
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
        """
        Compute MaxSim score between query and document.

        For each query token:
            Find max cosine similarity with any document token
        Sum these max similarities across all query tokens
        Normalize to [0, 1]
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
        """Get mock model configuration."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "dtype": "float32",
            "quantization": None,
            "memory_allocated_mb": 0.0,
            "is_loaded": self.is_loaded,
            "cache_dir": "/models",
            "is_mock": True,
        }


class MockStorageClient:
    """
    Mock ChromaDB storage client for testing.

    Simulates the ChromaClient interface defined in storage-interface.md
    without requiring a real ChromaDB instance. Uses in-memory dictionaries
    for storage.
    """

    def __init__(
        self,
        host: str = "chromadb",
        port: int = 8000,
        visual_collection: str = "visual_collection",
        text_collection: str = "text_collection",
        simulate_latency: bool = True,
    ):
        """
        Initialize mock storage client.

        Args:
            host: ChromaDB server host (not used)
            port: ChromaDB server port (not used)
            visual_collection: Name of visual embeddings collection
            text_collection: Name of text embeddings collection
            simulate_latency: If True, add realistic latency to operations
        """
        self.host = host
        self.port = port
        self.visual_collection_name = visual_collection
        self.text_collection_name = text_collection
        self.simulate_latency = simulate_latency

        # In-memory storage
        self._visual_store: Dict[str, Dict[str, Any]] = {}
        self._text_store: Dict[str, Dict[str, Any]] = {}

        # Generate mock data on initialization
        self._generate_mock_data()

        logger.info(
            f"Initialized MockStorageClient with {len(self._visual_store)} "
            f"visual and {len(self._text_store)} text embeddings"
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

                self._visual_store[emb_id] = {
                    "id": emb_id,
                    "embeddings": embeddings,
                    "representative_vector": embeddings[0],
                    "metadata": {
                        "filename": filename,
                        "page": page,
                        "doc_id": doc_id,
                        "type": "visual",
                        "seq_length": seq_length,
                        "embedding_shape": f"({seq_length}, 768)",
                        "timestamp": "2023-10-06T15:30:00Z",
                        "source_path": f"/data/uploads/{filename}",
                        "file_size": 1024 * (i + 1) * 100,
                    },
                }

            # Text embeddings (10 chunks per document)
            for chunk_id in range(10):
                emb_id = f"{doc_id}-chunk{chunk_id:04d}"
                seq_length = np.random.randint(50, 80)
                embeddings = self._generate_mock_embedding(seq_length, seed=hash(emb_id))
                page = (chunk_id // 3) + 1

                self._text_store[emb_id] = {
                    "id": emb_id,
                    "embeddings": embeddings,
                    "representative_vector": embeddings[0],
                    "metadata": {
                        "filename": filename,
                        "chunk_id": chunk_id,
                        "page": page,
                        "doc_id": doc_id,
                        "type": "text",
                        "seq_length": seq_length,
                        "embedding_shape": f"({seq_length}, 768)",
                        "text_preview": f"Sample text from {filename} chunk {chunk_id}...",
                        "word_count": 250,
                        "timestamp": "2023-10-06T15:30:00Z",
                        "source_path": f"/data/uploads/{filename}",
                    },
                }

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

    def search_visual(
        self,
        query_embedding: np.ndarray,
        n_results: int = 100,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Mock Stage 1 search: Fast retrieval using representative vectors.

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

        # Filter results
        candidates = []
        for emb_id, data in self._visual_store.items():
            # Apply filters
            if filters and not self._matches_filters(data["metadata"], filters):
                continue

            # Compute cosine similarity with representative vector
            score = self._cosine_similarity(query_embedding, data["representative_vector"])

            candidates.append(
                {
                    "id": emb_id,
                    "score": float(score),
                    "metadata": data["metadata"],
                    "representative_vector": data["representative_vector"].tolist(),
                    "full_embeddings": data["embeddings"],  # Include for Stage 2
                }
            )

        # Sort by score and return top-n
        candidates.sort(key=lambda x: x["score"], reverse=True)
        results = candidates[:n_results]

        # Simulate latency (~100ms)
        if self.simulate_latency:
            time.sleep(0.1)

        logger.debug(
            f"Visual search returned {len(results)} results in {(time.time()-start_time)*1000:.1f}ms"
        )
        return results

    def search_text(
        self,
        query_embedding: np.ndarray,
        n_results: int = 100,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Mock Stage 1 search for text collection."""
        start_time = time.time()

        if query_embedding.ndim != 1 or query_embedding.shape[0] != 768:
            raise ValueError(f"Query embedding must have shape (768,), got {query_embedding.shape}")

        # Filter results
        candidates = []
        for emb_id, data in self._text_store.items():
            # Apply filters
            if filters and not self._matches_filters(data["metadata"], filters):
                continue

            # Compute cosine similarity with representative vector
            score = self._cosine_similarity(query_embedding, data["representative_vector"])

            candidates.append(
                {
                    "id": emb_id,
                    "score": float(score),
                    "metadata": data["metadata"],
                    "representative_vector": data["representative_vector"].tolist(),
                    "full_embeddings": data["embeddings"],  # Include for Stage 2
                }
            )

        # Sort by score and return top-n
        candidates.sort(key=lambda x: x["score"], reverse=True)
        results = candidates[:n_results]

        # Simulate latency (~100ms)
        if self.simulate_latency:
            time.sleep(0.1)

        logger.debug(
            f"Text search returned {len(results)} results in {(time.time()-start_time)*1000:.1f}ms"
        )
        return results

    def _matches_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if metadata matches filters."""
        for key, value in filters.items():
            if key == "date_range":
                # Skip date range filtering in mock
                continue
            elif key == "page_range":
                page = metadata.get("page")
                if page is None:
                    return False
                if page < value.get("min", 0) or page > value.get("max", float("inf")):
                    return False
            elif key not in metadata or metadata[key] != value:
                return False
        return True

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        vec1_norm = vec1 / np.linalg.norm(vec1)
        vec2_norm = vec2 / np.linalg.norm(vec2)
        return float(np.dot(vec1_norm, vec2_norm))

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get mock collection statistics."""
        unique_docs = set()
        for data in self._visual_store.values():
            unique_docs.add(data["metadata"]["doc_id"])
        for data in self._text_store.values():
            unique_docs.add(data["metadata"]["doc_id"])

        return {
            "visual_count": len(self._visual_store),
            "text_count": len(self._text_store),
            "total_documents": len(unique_docs),
            "storage_size_mb": 0.0,
            "is_mock": True,
        }
