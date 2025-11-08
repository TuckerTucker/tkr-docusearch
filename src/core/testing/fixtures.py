"""
Test fixtures and sample data for tkr-docusearch.

This module provides reusable test fixtures including:
- Sample documents and metadata
- Pre-generated embeddings
- Common test scenarios
- Fixture factories

Usage:
    >>> from src.core.testing.fixtures import sample_document, sample_visual_embedding
    >>> doc = sample_document()
    >>> embedding = sample_visual_embedding()
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

import numpy as np

logger = logging.getLogger(__name__)


# ============================================================================
# Document Fixtures
# ============================================================================


def sample_document(
    doc_id: str = "doc001", filename: str = "sample.pdf", num_pages: int = 3
) -> Dict[str, Any]:
    """Generate sample document metadata.

    Args:
        doc_id: Document identifier
        filename: Document filename
        num_pages: Number of pages

    Returns:
        Dictionary with document metadata

    Example:
        >>> doc = sample_document("doc123", "report.pdf", 5)
        >>> print(doc["filename"])
        report.pdf
    """
    return {
        "doc_id": doc_id,
        "filename": filename,
        "num_pages": num_pages,
        "file_size": 1024 * 500,  # 500 KB
        "upload_timestamp": datetime.now().isoformat(),
        "status": "processed",
        "source_path": f"/data/uploads/{filename}",
        "metadata": {
            "author": "Test Author",
            "title": f"Sample Document {doc_id}",
            "subject": "Testing",
            "created_date": "2023-10-01",
        },
    }


def sample_visual_metadata(
    doc_id: str = "doc001", page: int = 1, filename: str = "sample.pdf"
) -> Dict[str, Any]:
    """Generate sample visual embedding metadata.

    Args:
        doc_id: Document identifier
        page: Page number (1-indexed)
        filename: Document filename

    Returns:
        Dictionary with visual embedding metadata

    Example:
        >>> meta = sample_visual_metadata("doc001", 1)
        >>> print(meta["type"])
        visual
    """
    return {
        "doc_id": doc_id,
        "filename": filename,
        "page": page,
        "type": "visual",
        "embedding_id": f"{doc_id}-page{page:03d}",
        "image_path": f"/data/images/{doc_id}/page_{page:03d}.png",
        "thumbnail_path": f"/data/thumbnails/{doc_id}/page_{page:03d}.jpg",
        "width": 800,
        "height": 1000,
        "timestamp": datetime.now().isoformat(),
    }


def sample_text_metadata(
    doc_id: str = "doc001", chunk_id: int = 0, filename: str = "sample.pdf", page: int = 1
) -> Dict[str, Any]:
    """Generate sample text embedding metadata.

    Args:
        doc_id: Document identifier
        chunk_id: Chunk number (0-indexed)
        filename: Document filename
        page: Source page number

    Returns:
        Dictionary with text embedding metadata

    Example:
        >>> meta = sample_text_metadata("doc001", 0)
        >>> print(meta["type"])
        text
    """
    return {
        "doc_id": doc_id,
        "filename": filename,
        "chunk_id": chunk_id,
        "page": page,
        "type": "text",
        "embedding_id": f"{doc_id}-chunk{chunk_id:04d}",
        "text_preview": f"Sample text from {filename} chunk {chunk_id}...",
        "word_count": 250,
        "char_count": 1500,
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================================
# Embedding Fixtures
# ============================================================================


def sample_visual_embedding(seq_length: int = 100, dim: int = 768, seed: int = 42) -> np.ndarray:
    """Generate sample visual embedding.

    Args:
        seq_length: Sequence length (typical: 80-120 for images)
        dim: Embedding dimension
        seed: Random seed for reproducibility

    Returns:
        Normalized embedding array of shape (seq_length, dim)

    Example:
        >>> emb = sample_visual_embedding(100, 768)
        >>> print(emb.shape)
        (100, 768)
    """
    rng = np.random.default_rng(seed)
    embedding = rng.standard_normal((seq_length, dim)).astype(np.float32)
    # Normalize to unit vectors
    embedding = embedding / np.linalg.norm(embedding, axis=1, keepdims=True)
    return embedding


def sample_text_embedding(seq_length: int = 64, dim: int = 768, seed: int = 42) -> np.ndarray:
    """Generate sample text embedding.

    Args:
        seq_length: Sequence length (typical: 50-80 for text chunks)
        dim: Embedding dimension
        seed: Random seed for reproducibility

    Returns:
        Normalized embedding array of shape (seq_length, dim)

    Example:
        >>> emb = sample_text_embedding(64, 768)
        >>> print(emb.shape)
        (64, 768)
    """
    rng = np.random.default_rng(seed)
    embedding = rng.standard_normal((seq_length, dim)).astype(np.float32)
    # Normalize to unit vectors
    embedding = embedding / np.linalg.norm(embedding, axis=1, keepdims=True)
    return embedding


def sample_query_embedding(seq_length: int = 20, dim: int = 768, seed: int = 42) -> np.ndarray:
    """Generate sample query embedding.

    Args:
        seq_length: Sequence length (typical: 10-30 for queries)
        dim: Embedding dimension
        seed: Random seed for reproducibility

    Returns:
        Normalized embedding array of shape (seq_length, dim)

    Example:
        >>> emb = sample_query_embedding(20, 768)
        >>> print(emb.shape)
        (20, 768)
    """
    rng = np.random.default_rng(seed)
    embedding = rng.standard_normal((seq_length, dim)).astype(np.float32)
    # Normalize to unit vectors
    embedding = embedding / np.linalg.norm(embedding, axis=1, keepdims=True)
    return embedding


# ============================================================================
# Search Result Fixtures
# ============================================================================


def sample_search_result(
    doc_id: str = "doc001",
    page: int = 1,
    score: float = 0.95,
    result_type: str = "visual",
) -> Dict[str, Any]:
    """Generate sample search result.

    Args:
        doc_id: Document identifier
        page: Page number
        score: Relevance score (0-1)
        result_type: "visual" or "text"

    Returns:
        Dictionary with search result data

    Example:
        >>> result = sample_search_result("doc123", 5, 0.88)
        >>> print(result["score"])
        0.88
    """
    if result_type == "visual":
        embedding_id = f"{doc_id}-page{page:03d}"
        metadata = sample_visual_metadata(doc_id, page)
    else:
        chunk_id = (page - 1) * 3  # Approximate chunk from page
        embedding_id = f"{doc_id}-chunk{chunk_id:04d}"
        metadata = sample_text_metadata(doc_id, chunk_id, page=page)

    return {
        "id": embedding_id,
        "score": score,
        "metadata": metadata,
        "type": result_type,
    }


def sample_search_results(
    num_results: int = 10, doc_id_prefix: str = "doc", score_decay: float = 0.05
) -> List[Dict[str, Any]]:
    """Generate list of sample search results.

    Args:
        num_results: Number of results to generate
        doc_id_prefix: Prefix for document IDs
        score_decay: Score decrease per result

    Returns:
        List of search result dictionaries

    Example:
        >>> results = sample_search_results(5)
        >>> print(len(results))
        5
        >>> print(results[0]["score"] > results[1]["score"])
        True
    """
    results = []
    base_score = 0.95

    for i in range(num_results):
        doc_num = (i // 3) + 1  # 3 results per document
        page = (i % 3) + 1
        doc_id = f"{doc_id_prefix}{doc_num:03d}"
        score = max(0.5, base_score - (i * score_decay))
        result_type = "visual" if i % 2 == 0 else "text"

        results.append(sample_search_result(doc_id, page, score, result_type))

    return results


# ============================================================================
# Batch Data Fixtures
# ============================================================================


def sample_batch_embeddings(
    batch_size: int = 4, seq_length: int = 100, dim: int = 768, seed: int = 42
) -> List[np.ndarray]:
    """Generate batch of sample embeddings.

    Args:
        batch_size: Number of embeddings in batch
        seq_length: Sequence length for each embedding
        dim: Embedding dimension
        seed: Random seed for reproducibility

    Returns:
        List of normalized embedding arrays

    Example:
        >>> batch = sample_batch_embeddings(4, 100, 768)
        >>> print(len(batch))
        4
        >>> print(batch[0].shape)
        (100, 768)
    """
    embeddings = []
    rng = np.random.default_rng(seed)

    for i in range(batch_size):
        # Vary seq_length slightly for realism
        actual_seq_length = seq_length + rng.integers(-10, 11)
        embedding = rng.standard_normal((actual_seq_length, dim)).astype(np.float32)
        # Normalize to unit vectors
        embedding = embedding / np.linalg.norm(embedding, axis=1, keepdims=True)
        embeddings.append(embedding)

    return embeddings


def sample_cls_tokens(batch_size: int = 4, dim: int = 768, seed: int = 42) -> np.ndarray:
    """Generate batch of sample CLS tokens.

    Args:
        batch_size: Number of CLS tokens
        dim: Token dimension
        seed: Random seed for reproducibility

    Returns:
        Normalized CLS token array of shape (batch_size, dim)

    Example:
        >>> cls = sample_cls_tokens(4, 768)
        >>> print(cls.shape)
        (4, 768)
    """
    rng = np.random.default_rng(seed)
    cls_tokens = rng.standard_normal((batch_size, dim)).astype(np.float32)
    # Normalize to unit vectors
    cls_tokens = cls_tokens / np.linalg.norm(cls_tokens, axis=1, keepdims=True)
    return cls_tokens


# ============================================================================
# Query Fixtures
# ============================================================================


SAMPLE_QUERIES = [
    "quarterly earnings report",
    "product roadmap for 2024",
    "legal compliance requirements",
    "marketing campaign results",
    "technical architecture diagram",
    "employee benefits policy",
    "annual revenue growth",
    "customer satisfaction metrics",
    "security audit findings",
    "project timeline and milestones",
]


def sample_query(index: int = 0) -> str:
    """Get a sample query string.

    Args:
        index: Query index (0-9)

    Returns:
        Query string

    Example:
        >>> query = sample_query(0)
        >>> print(query)
        quarterly earnings report
    """
    return SAMPLE_QUERIES[index % len(SAMPLE_QUERIES)]


def sample_queries(num_queries: int = 5) -> List[str]:
    """Get multiple sample queries.

    Args:
        num_queries: Number of queries to return

    Returns:
        List of query strings

    Example:
        >>> queries = sample_queries(3)
        >>> print(len(queries))
        3
    """
    return [sample_query(i) for i in range(num_queries)]


# ============================================================================
# Collection Stats Fixtures
# ============================================================================


def sample_collection_stats(
    visual_count: int = 15, text_count: int = 50, num_documents: int = 5
) -> Dict[str, Any]:
    """Generate sample collection statistics.

    Args:
        visual_count: Number of visual embeddings
        text_count: Number of text embeddings
        num_documents: Number of unique documents

    Returns:
        Dictionary with collection statistics

    Example:
        >>> stats = sample_collection_stats()
        >>> print(stats["total_documents"])
        5
    """
    return {
        "visual_count": visual_count,
        "text_count": text_count,
        "total_embeddings": visual_count + text_count,
        "total_documents": num_documents,
        "storage_size_mb": (visual_count + text_count) * 0.5,  # Approximate
        "avg_embeddings_per_doc": (visual_count + text_count) / num_documents,
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================================
# Error Scenario Fixtures
# ============================================================================


def sample_error_cases() -> List[Dict[str, Any]]:
    """Generate sample error test cases.

    Returns:
        List of error scenario dictionaries

    Example:
        >>> cases = sample_error_cases()
        >>> print(cases[0]["name"])
        empty_query
    """
    return [
        {
            "name": "empty_query",
            "query": "",
            "expected_error": ValueError,
            "error_message": "Query cannot be empty",
        },
        {
            "name": "invalid_embedding_shape",
            "embedding": np.random.randn(768),  # 1D instead of 2D
            "expected_error": ValueError,
            "error_message": "Invalid embedding shape",
        },
        {
            "name": "invalid_embedding_dim",
            "embedding": np.random.randn(100, 512),  # Wrong dimension
            "expected_error": ValueError,
            "error_message": "Invalid embedding dimension",
        },
        {
            "name": "missing_metadata_keys",
            "metadata": {"filename": "test.pdf"},  # Missing required keys
            "expected_error": AssertionError,
            "error_message": "Required metadata key missing",
        },
    ]
