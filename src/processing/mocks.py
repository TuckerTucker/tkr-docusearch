"""
Mock implementations for embedding and storage agents.

This module provides mock implementations matching the integration contracts
for independent Wave 2 development. These will be replaced with real
implementations in Wave 3.
"""

import uuid
import logging
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


# ============================================================================
# Mock Embedding Agent (matching embedding-interface.md)
# ============================================================================


@dataclass
class BatchEmbeddingOutput:
    """Batch embedding output matching embedding interface."""

    embeddings: List[np.ndarray]  # List of (seq_length, 768) arrays
    cls_tokens: np.ndarray  # Shape: (batch_size, 768)
    seq_lengths: List[int]  # Token counts for each item
    input_type: str  # "visual" or "text"
    batch_processing_time_ms: float  # Total batch time


class MockEmbeddingEngine:
    """Mock ColPali engine for Wave 2 development.

    Simulates the embedding-agent interface defined in embedding-interface.md.
    Returns dummy multi-vector embeddings with realistic shapes and timing.
    """

    def __init__(
        self,
        model_name: str = "nomic-ai/colnomic-embed-multimodal-7b",
        device: str = "mps",
        **kwargs
    ):
        """Initialize mock embedding engine.

        Args:
            model_name: Model identifier (ignored in mock)
            device: Target device (ignored in mock)
            **kwargs: Additional arguments (ignored in mock)
        """
        self.model_name = model_name
        self.device = device
        logger.info(f"Initialized MockEmbeddingEngine (device={device})")

    def embed_images(
        self,
        images: List[Image.Image],
        batch_size: int = 4
    ) -> BatchEmbeddingOutput:
        """Generate mock multi-vector embeddings for images.

        Args:
            images: List of PIL Images (document pages)
            batch_size: Number of images to process at once (ignored in mock)

        Returns:
            BatchEmbeddingOutput with mock embeddings

        Performance simulation:
            - Typical token count: 100 per page (range 80-120)
            - Simulates realistic processing time
        """
        if not images:
            raise ValueError("Images list cannot be empty")

        num_images = len(images)
        logger.info(f"Embedding {num_images} images (mock)")

        # Generate mock embeddings with realistic token counts
        embeddings = []
        seq_lengths = []

        for _ in images:
            # Visual embeddings typically have 80-120 tokens
            seq_length = np.random.randint(80, 121)
            seq_lengths.append(seq_length)

            # Generate random multi-vector embedding
            embedding = np.random.randn(seq_length, 768).astype(np.float32)
            embeddings.append(embedding)

        # CLS tokens are first token of each embedding
        cls_tokens = np.array([emb[0] for emb in embeddings], dtype=np.float32)

        # Simulate processing time (~6s per image for FP16)
        simulated_time_ms = num_images * 6000.0

        return BatchEmbeddingOutput(
            embeddings=embeddings,
            cls_tokens=cls_tokens,
            seq_lengths=seq_lengths,
            input_type="visual",
            batch_processing_time_ms=simulated_time_ms
        )

    def embed_texts(
        self,
        texts: List[str],
        batch_size: int = 8
    ) -> BatchEmbeddingOutput:
        """Generate mock multi-vector embeddings for texts.

        Args:
            texts: List of text chunks (avg 250 words)
            batch_size: Number of texts to process at once (ignored in mock)

        Returns:
            BatchEmbeddingOutput with mock embeddings

        Performance simulation:
            - Typical token count: 64 per chunk (range 50-80)
            - Simulates realistic processing time
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")

        num_texts = len(texts)
        logger.info(f"Embedding {num_texts} text chunks (mock)")

        # Generate mock embeddings with realistic token counts
        embeddings = []
        seq_lengths = []

        for _ in texts:
            # Text embeddings typically have 50-80 tokens
            seq_length = np.random.randint(50, 81)
            seq_lengths.append(seq_length)

            # Generate random multi-vector embedding
            embedding = np.random.randn(seq_length, 768).astype(np.float32)
            embeddings.append(embedding)

        # CLS tokens are first token of each embedding
        cls_tokens = np.array([emb[0] for emb in embeddings], dtype=np.float32)

        # Simulate processing time (~2s per chunk for FP16)
        simulated_time_ms = num_texts * 2000.0

        return BatchEmbeddingOutput(
            embeddings=embeddings,
            cls_tokens=cls_tokens,
            seq_lengths=seq_lengths,
            input_type="text",
            batch_processing_time_ms=simulated_time_ms
        )

    def get_model_info(self) -> Dict[str, Any]:
        """Get mock model configuration.

        Returns:
            Model information dictionary
        """
        return {
            "model_name": self.model_name,
            "device": self.device,
            "dtype": "bfloat16",
            "quantization": None,
            "memory_allocated_mb": 0.0,
            "is_loaded": True,
            "cache_dir": "/models",
            "mock": True
        }

    def clear_cache(self):
        """Mock cache clearing (no-op)."""
        logger.debug("Cache clear requested (mock - no-op)")


# ============================================================================
# Mock Storage Agent (matching storage-interface.md)
# ============================================================================


class MockStorageClient:
    """Mock ChromaDB client for Wave 2 development.

    Simulates the storage-agent interface defined in storage-interface.md.
    Stores embeddings in memory for testing purposes.
    """

    def __init__(
        self,
        host: str = "chromadb",
        port: int = 8000,
        visual_collection: str = "visual_collection",
        text_collection: str = "text_collection"
    ):
        """Initialize mock storage client.

        Args:
            host: ChromaDB server host (ignored in mock)
            port: ChromaDB server port (ignored in mock)
            visual_collection: Visual embeddings collection name
            text_collection: Text embeddings collection name
        """
        self.host = host
        self.port = port
        self.visual_collection = visual_collection
        self.text_collection = text_collection

        # In-memory storage for mocking
        self._visual_store: Dict[str, Dict[str, Any]] = {}
        self._text_store: Dict[str, Dict[str, Any]] = {}

        logger.info(
            f"Initialized MockStorageClient "
            f"(host={host}, port={port}, mock=True)"
        )

    def add_visual_embedding(
        self,
        doc_id: str,
        page: int,
        full_embeddings: np.ndarray,
        metadata: Dict[str, Any]
    ) -> str:
        """Store mock visual embedding.

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
                f"Invalid embedding shape: {full_embeddings.shape}. "
                "Expected (seq_length, 768)"
            )

        seq_length, dim = full_embeddings.shape
        # Support both real ColPali (128) and mock (768) dimensions
        if dim not in [128, 768]:
            raise ValueError(
                f"Invalid embedding dimension: {dim}. Expected 128 or 768"
            )

        # Generate ID
        embedding_id = f"{doc_id}-page{page:03d}"

        # Store in memory
        self._visual_store[embedding_id] = {
            "id": embedding_id,
            "doc_id": doc_id,
            "page": page,
            "full_embeddings": full_embeddings,
            "seq_length": seq_length,
            "metadata": metadata
        }

        logger.debug(
            f"Stored visual embedding: {embedding_id} "
            f"(shape={full_embeddings.shape})"
        )

        return embedding_id

    def add_text_embedding(
        self,
        doc_id: str,
        chunk_id: int,
        full_embeddings: np.ndarray,
        metadata: Dict[str, Any]
    ) -> str:
        """Store mock text embedding.

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
                f"Invalid embedding shape: {full_embeddings.shape}. "
                "Expected (seq_length, 768)"
            )

        seq_length, dim = full_embeddings.shape
        # Support both real ColPali (128) and mock (768) dimensions
        if dim not in [128, 768]:
            raise ValueError(
                f"Invalid embedding dimension: {dim}. Expected 128 or 768"
            )

        # Generate ID
        embedding_id = f"{doc_id}-chunk{chunk_id:04d}"

        # Store in memory
        self._text_store[embedding_id] = {
            "id": embedding_id,
            "doc_id": doc_id,
            "chunk_id": chunk_id,
            "full_embeddings": full_embeddings,
            "seq_length": seq_length,
            "metadata": metadata
        }

        logger.debug(
            f"Stored text embedding: {embedding_id} "
            f"(shape={full_embeddings.shape})"
        )

        return embedding_id

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get mock collection statistics.

        Returns:
            Collection statistics dictionary
        """
        # Count unique doc_ids
        visual_docs = set(item["doc_id"] for item in self._visual_store.values())
        text_docs = set(item["doc_id"] for item in self._text_store.values())
        all_docs = visual_docs.union(text_docs)

        return {
            "visual_count": len(self._visual_store),
            "text_count": len(self._text_store),
            "total_documents": len(all_docs),
            "storage_size_mb": 0.0,  # Mock - no actual storage
            "mock": True
        }

    def delete_document(self, doc_id: str) -> Tuple[int, int]:
        """Delete all embeddings for a document.

        Args:
            doc_id: Document identifier

        Returns:
            Tuple of (visual_count, text_count) deleted
        """
        # Delete visual embeddings
        visual_ids = [
            eid for eid, item in self._visual_store.items()
            if item["doc_id"] == doc_id
        ]
        for eid in visual_ids:
            del self._visual_store[eid]

        # Delete text embeddings
        text_ids = [
            eid for eid, item in self._text_store.items()
            if item["doc_id"] == doc_id
        ]
        for eid in text_ids:
            del self._text_store[eid]

        logger.info(
            f"Deleted document {doc_id}: "
            f"{len(visual_ids)} visual, {len(text_ids)} text"
        )

        return len(visual_ids), len(text_ids)

    def search_visual(
        self,
        query_embedding: np.ndarray,
        n_results: int = 100,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Mock visual search - returns stored embeddings with random distances.

        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return
            filters: Optional metadata filters (ignored in mock)

        Returns:
            List of dicts with 'id' and 'distance' keys
        """
        # Return stored embeddings with mock distances
        results = []
        for emb_id in list(self._visual_store.keys())[:n_results]:
            results.append({
                'id': emb_id,
                'distance': float(np.random.random()),  # Random distance for mock
                'metadata': self._visual_store[emb_id]['metadata']
            })

        # Sort by distance
        results.sort(key=lambda x: x['distance'])
        return results

    def search_text(
        self,
        query_embedding: np.ndarray,
        n_results: int = 100,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Mock text search - returns stored embeddings with random distances.

        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return
            filters: Optional metadata filters (ignored in mock)

        Returns:
            List of dicts with 'id' and 'distance' keys
        """
        # Return stored embeddings with mock distances
        results = []
        for emb_id in list(self._text_store.keys())[:n_results]:
            results.append({
                'id': emb_id,
                'distance': float(np.random.random()),  # Random distance for mock
                'metadata': self._text_store[emb_id]['metadata']
            })

        # Sort by distance
        results.sort(key=lambda x: x['distance'])
        return results

    def get_full_embeddings(
        self,
        embedding_id: str,
        collection: str = None
    ) -> np.ndarray:
        """Retrieve mock full embeddings.

        Args:
            embedding_id: ID of the embedding
            collection: "visual" or "text" (auto-detects if None)

        Returns:
            Full multi-vector embedding

        Raises:
            ValueError: If embedding_id not found
        """
        # Auto-detect collection if not specified
        if collection is None:
            if embedding_id in self._visual_store:
                store = self._visual_store
            elif embedding_id in self._text_store:
                store = self._text_store
            else:
                raise ValueError(f"Embedding not found: {embedding_id}")
        else:
            store = self._visual_store if collection == "visual" else self._text_store
            if embedding_id not in store:
                raise ValueError(f"Embedding not found: {embedding_id}")

        return store[embedding_id]["full_embeddings"]
