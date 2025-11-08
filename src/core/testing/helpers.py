"""
Test helper functions for tkr-docusearch.

This module provides utility functions for common test operations including:
- File creation and manipulation
- Assertion helpers
- Performance measurement utilities
- Temporary resource management

Usage:
    >>> from src.core.testing.helpers import create_temp_pdf, assert_embeddings_valid
    >>> pdf_path = create_temp_pdf(num_pages=3)
    >>> embeddings = generate_embeddings(pdf_path)
    >>> assert_embeddings_valid(embeddings, expected_dim=768)
"""

import logging
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Union

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


# ============================================================================
# File Creation Helpers
# ============================================================================


def create_temp_image(
    width: int = 800, height: int = 600, color: str = "white", format: str = "PNG"
) -> str:
    """Create a temporary image file for testing.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        color: Background color (default: "white")
        format: Image format (PNG, JPEG, etc.)

    Returns:
        Path to temporary image file

    Example:
        >>> img_path = create_temp_image(1024, 768, "red")
        >>> print(Path(img_path).exists())
        True
    """
    img = Image.new("RGB", (width, height), color=color)
    with tempfile.NamedTemporaryFile(suffix=f".{format.lower()}", delete=False) as tmp:
        img.save(tmp.name, format=format)
        logger.debug(f"Created temp image: {tmp.name} ({width}x{height})")
        return tmp.name


def create_temp_pdf(
    num_pages: int = 1, width: int = 800, height: int = 600, color: str = "white"
) -> str:
    """Create a temporary PDF file for testing.

    Args:
        num_pages: Number of pages in PDF
        width: Page width in pixels
        height: Page height in pixels
        color: Background color

    Returns:
        Path to temporary PDF file

    Example:
        >>> pdf_path = create_temp_pdf(num_pages=3)
        >>> print(Path(pdf_path).suffix)
        .pdf
    """
    try:
        from PIL import Image

        # Create images for each page
        images = []
        for i in range(num_pages):
            img = Image.new("RGB", (width, height), color=color)
            images.append(img)

        # Save as PDF
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            if images:
                images[0].save(
                    tmp.name,
                    "PDF",
                    save_all=True,
                    append_images=images[1:] if len(images) > 1 else [],
                )
            logger.debug(f"Created temp PDF: {tmp.name} ({num_pages} pages)")
            return tmp.name
    except Exception as e:
        logger.error(f"Failed to create temp PDF: {e}")
        raise


def create_temp_text_file(content: str = "Sample text content", suffix: str = ".txt") -> str:
    """Create a temporary text file for testing.

    Args:
        content: Text content to write
        suffix: File suffix (default: ".txt")

    Returns:
        Path to temporary text file

    Example:
        >>> txt_path = create_temp_text_file("Hello World")
        >>> print(Path(txt_path).read_text())
        Hello World
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        logger.debug(f"Created temp text file: {tmp.name}")
        return tmp.name


# ============================================================================
# Assertion Helpers
# ============================================================================


def assert_embeddings_valid(
    embeddings: Union[np.ndarray, List[np.ndarray]],
    expected_dim: int = 768,
    expected_dtype: type = np.float32,
    min_norm: float = 0.9,
    max_norm: float = 1.1,
) -> None:
    """Assert that embeddings have valid shape, dtype, and normalization.

    Args:
        embeddings: Single embedding array or list of embeddings
        expected_dim: Expected embedding dimension
        expected_dtype: Expected numpy dtype
        min_norm: Minimum acceptable L2 norm
        max_norm: Maximum acceptable L2 norm

    Raises:
        AssertionError: If embeddings are invalid

    Example:
        >>> emb = np.random.randn(100, 768).astype(np.float32)
        >>> assert_embeddings_valid(emb, expected_dim=768)
    """
    if isinstance(embeddings, list):
        for i, emb in enumerate(embeddings):
            assert isinstance(emb, np.ndarray), f"Embedding {i} is not numpy array"
            assert emb.ndim == 2, f"Embedding {i} must be 2D, got {emb.ndim}D"
            assert emb.shape[1] == expected_dim, (
                f"Embedding {i} dimension mismatch: " f"expected {expected_dim}, got {emb.shape[1]}"
            )
            assert emb.dtype == expected_dtype, (
                f"Embedding {i} dtype mismatch: " f"expected {expected_dtype}, got {emb.dtype}"
            )

            # Check normalization (optional)
            if min_norm is not None and max_norm is not None:
                norms = np.linalg.norm(emb, axis=1)
                assert np.all(
                    (norms >= min_norm) & (norms <= max_norm)
                ), f"Embedding {i} has invalid norms"
    else:
        assert isinstance(embeddings, np.ndarray), "Embedding is not numpy array"
        assert embeddings.ndim == 2, f"Embedding must be 2D, got {embeddings.ndim}D"
        assert embeddings.shape[1] == expected_dim, (
            f"Embedding dimension mismatch: " f"expected {expected_dim}, got {embeddings.shape[1]}"
        )
        assert embeddings.dtype == expected_dtype, (
            f"Embedding dtype mismatch: " f"expected {expected_dtype}, got {embeddings.dtype}"
        )

        # Check normalization (optional)
        if min_norm is not None and max_norm is not None:
            norms = np.linalg.norm(embeddings, axis=1)
            assert np.all((norms >= min_norm) & (norms <= max_norm)), "Embedding has invalid norms"


def assert_metadata_valid(metadata: Dict[str, Any], required_keys: List[str]) -> None:
    """Assert that metadata contains all required keys.

    Args:
        metadata: Metadata dictionary
        required_keys: List of required key names

    Raises:
        AssertionError: If any required key is missing

    Example:
        >>> meta = {"filename": "test.pdf", "page": 1, "doc_id": "doc001"}
        >>> assert_metadata_valid(meta, ["filename", "page", "doc_id"])
    """
    assert isinstance(metadata, dict), "Metadata must be a dictionary"
    for key in required_keys:
        assert key in metadata, f"Required metadata key missing: {key}"


def assert_search_results_valid(
    results: List[Dict[str, Any]],
    min_score: float = 0.0,
    max_score: float = 1.0,
    required_keys: Optional[List[str]] = None,
) -> None:
    """Assert that search results have valid structure and scores.

    Args:
        results: List of search result dictionaries
        min_score: Minimum valid score
        max_score: Maximum valid score
        required_keys: Optional list of required keys in each result

    Raises:
        AssertionError: If results are invalid

    Example:
        >>> results = [{"id": "doc1", "score": 0.95, "metadata": {}}]
        >>> assert_search_results_valid(results, required_keys=["id", "score"])
    """
    assert isinstance(results, list), "Results must be a list"

    default_keys = ["id", "score", "metadata"]
    keys_to_check = required_keys if required_keys is not None else default_keys

    for i, result in enumerate(results):
        assert isinstance(result, dict), f"Result {i} must be a dictionary"

        for key in keys_to_check:
            assert key in result, f"Result {i} missing required key: {key}"

        # Validate score
        if "score" in result:
            score = result["score"]
            assert isinstance(score, (int, float)), f"Result {i} score must be numeric"
            assert min_score <= score <= max_score, (
                f"Result {i} score out of range: " f"{score} not in [{min_score}, {max_score}]"
            )


# ============================================================================
# Performance Measurement
# ============================================================================


@contextmanager
def measure_time(operation_name: str = "Operation") -> Generator[Dict[str, float], None, None]:
    """Context manager to measure execution time.

    Args:
        operation_name: Name of operation being measured

    Yields:
        Dictionary that will be populated with timing info

    Example:
        >>> with measure_time("embedding") as timing:
        ...     # do some work
        ...     pass
        >>> print(f"Took {timing['duration_ms']:.2f}ms")
    """
    timing_info = {}
    start_time = time.time()

    try:
        yield timing_info
    finally:
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        timing_info["duration_ms"] = duration_ms
        timing_info["duration_s"] = end_time - start_time
        logger.debug(f"{operation_name} took {duration_ms:.2f}ms")


def assert_performance(
    duration_ms: float, max_duration_ms: float, operation_name: str = "Operation"
) -> None:
    """Assert that an operation completed within expected time.

    Args:
        duration_ms: Actual duration in milliseconds
        max_duration_ms: Maximum acceptable duration
        operation_name: Name of operation for error message

    Raises:
        AssertionError: If duration exceeds maximum

    Example:
        >>> with measure_time() as timing:
        ...     # do work
        ...     pass
        >>> assert_performance(timing['duration_ms'], 100.0, "search")
    """
    assert duration_ms <= max_duration_ms, (
        f"{operation_name} took too long: " f"{duration_ms:.2f}ms > {max_duration_ms:.2f}ms"
    )


# ============================================================================
# Temporary Resource Management
# ============================================================================


@contextmanager
def temp_directory() -> Generator[Path, None, None]:
    """Context manager for temporary directory that auto-cleans.

    Yields:
        Path to temporary directory

    Example:
        >>> with temp_directory() as tmpdir:
        ...     (tmpdir / "test.txt").write_text("content")
        ...     print(tmpdir.exists())
        True
        # Directory is cleaned up after context exit
    """
    tmpdir = Path(tempfile.mkdtemp())
    try:
        logger.debug(f"Created temp directory: {tmpdir}")
        yield tmpdir
    finally:
        # Clean up directory
        import shutil

        if tmpdir.exists():
            shutil.rmtree(tmpdir)
            logger.debug(f"Cleaned up temp directory: {tmpdir}")


# ============================================================================
# Mock Data Generation
# ============================================================================


def generate_random_embedding(
    seq_length: int, dim: int = 768, seed: Optional[int] = None
) -> np.ndarray:
    """Generate random normalized embedding.

    Args:
        seq_length: Sequence length (number of tokens)
        dim: Embedding dimension
        seed: Optional random seed for reproducibility

    Returns:
        Normalized embedding array of shape (seq_length, dim)

    Example:
        >>> emb = generate_random_embedding(100, 768, seed=42)
        >>> print(emb.shape)
        (100, 768)
    """
    rng = np.random.default_rng(seed)
    embedding = rng.standard_normal((seq_length, dim)).astype(np.float32)
    # Normalize to unit vectors
    embedding = embedding / np.linalg.norm(embedding, axis=1, keepdims=True)
    return embedding


def generate_mock_search_results(
    num_results: int = 10, doc_id_prefix: str = "doc", score_range: tuple = (0.5, 1.0)
) -> List[Dict[str, Any]]:
    """Generate mock search results for testing.

    Args:
        num_results: Number of results to generate
        doc_id_prefix: Prefix for document IDs
        score_range: Tuple of (min_score, max_score)

    Returns:
        List of mock search result dictionaries

    Example:
        >>> results = generate_mock_search_results(5)
        >>> print(len(results))
        5
    """
    results = []
    min_score, max_score = score_range

    for i in range(num_results):
        # Generate decreasing scores
        score = max_score - (i / num_results) * (max_score - min_score)

        results.append(
            {
                "id": f"{doc_id_prefix}{i+1:03d}",
                "score": score,
                "metadata": {
                    "filename": f"document_{i+1}.pdf",
                    "page": (i % 10) + 1,
                    "doc_id": f"{doc_id_prefix}{i+1:03d}",
                },
            }
        )

    return results
