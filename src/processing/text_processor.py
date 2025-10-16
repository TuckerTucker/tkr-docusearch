"""
Text processing pipeline for document chunks.

This module handles text chunking and embedding generation for document text,
coordinating with the embedding agent and preparing results for storage.
"""

import logging
import re
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np

from .docling_parser import TextChunk

logger = logging.getLogger(__name__)


def extract_timestamps_from_text(text: str) -> Tuple[Optional[float], Optional[float], str]:
    """
    Extract [time: X-Y] timestamp markers from text.

    Args:
        text: Text potentially containing [time: START-END] marker at beginning

    Returns:
        Tuple of (start_time, end_time, cleaned_text):
        - start_time: float seconds or None if not found/invalid
        - end_time: float seconds or None if not found/invalid
        - cleaned_text: text with timestamp marker removed

    Parsing Rules:
        - Marker must be at start of text (after optional whitespace)
        - Format: [time: <float>-<float>]
        - Both timestamps must be valid floats
        - end_time must be > start_time
        - start_time must be >= 0.0
        - If invalid, return (None, None, original_text)

    Examples:
        >>> extract_timestamps_from_text("[time: 1.5-3.2] Hello")
        (1.5, 3.2, "Hello")

        >>> extract_timestamps_from_text("[time: 0.62-3.96]  Multiple spaces")
        (0.62, 3.96, "Multiple spaces")

        >>> extract_timestamps_from_text("No timestamp here")
        (None, None, "No timestamp here")

        >>> extract_timestamps_from_text("[time: 5.0-2.0] Invalid")
        (None, None, "[time: 5.0-2.0] Invalid")
    """
    # Match [time: X-Y] at start of text (don't consume trailing whitespace)
    pattern = r'^\s*\[time:\s*([\d.]+)-([\d.]+)\]'
    match = re.match(pattern, text)

    if not match:
        # No timestamp marker found
        return (None, None, text)

    try:
        # Parse timestamps
        start_time = float(match.group(1))
        end_time = float(match.group(2))

        # Validate timestamps
        if start_time < 0.0:
            logger.warning(f"Malformed timestamp in text (negative_start): {text[:50]}...")
            return (None, None, text)

        if end_time <= start_time:
            logger.warning(f"Malformed timestamp in text (invalid_duration): {text[:50]}...")
            return (None, None, text)

        # Remove timestamp marker from text (preserve trailing whitespace)
        cleaned_text = text[match.end():]

        logger.debug(f"Extracted timestamp: {start_time:.2f}-{end_time:.2f}")
        return (start_time, end_time, cleaned_text)

    except (ValueError, IndexError) as e:
        # Failed to parse numbers
        logger.warning(f"Malformed timestamp in text (parse_error): {text[:50]}... ({e})")
        return (None, None, text)


@dataclass
class TextEmbeddingResult:
    """Result from text embedding processing.

    Attributes:
        doc_id: Document identifier
        chunk_id: Unique chunk identifier
        page_num: Source page number
        embedding: Full multi-vector sequence
        cls_token: Representative CLS token vector
        seq_length: Number of tokens
        text: Original chunk text
        processing_time_ms: Time taken for embedding
    """

    doc_id: str
    chunk_id: str
    page_num: int
    embedding: np.ndarray  # Shape: (seq_length, 768)
    cls_token: np.ndarray  # Shape: (768,)
    seq_length: int
    text: str
    processing_time_ms: float


class TextProcessor:
    """Text processing pipeline for document chunks.

    Handles chunk-level text embedding generation using the embedding agent.
    """

    def __init__(self, embedding_engine, batch_size: int = 8):
        """Initialize text processor.

        Args:
            embedding_engine: Embedding engine instance (real or mock)
            batch_size: Number of chunks to process at once
        """
        self.embedding_engine = embedding_engine
        self.batch_size = batch_size
        logger.info(f"Initialized TextProcessor (batch_size={batch_size})")

    def process_chunks(
        self,
        chunks: List[TextChunk],
        doc_id: str,
        progress_callback=None
    ) -> List[TextEmbeddingResult]:
        """Process text chunks and generate embeddings.

        Args:
            chunks: List of TextChunk objects
            doc_id: Document identifier
            progress_callback: Optional callback(chunks_completed, total_chunks)

        Returns:
            List of TextEmbeddingResult objects

        Raises:
            ValueError: If chunks list is empty
            Exception: If embedding generation fails
        """
        if not chunks:
            raise ValueError("Chunks list cannot be empty")

        logger.info(
            f"Processing {len(chunks)} text chunks for embeddings "
            f"(batch_size={self.batch_size})"
        )

        all_results = []
        total_chunks = len(chunks)

        # Process in batches
        for batch_start in range(0, total_chunks, self.batch_size):
            batch_end = min(batch_start + self.batch_size, total_chunks)
            batch_chunks = chunks[batch_start:batch_end]

            batch_num = batch_start // self.batch_size + 1
            total_batches = (total_chunks + self.batch_size - 1) // self.batch_size

            logger.debug(
                f"Processing batch {batch_num}/{total_batches}: "
                f"chunks {batch_start+1}-{batch_end}"
            )

            # Extract text from chunks
            texts = [chunk.text for chunk in batch_chunks]

            # Generate embeddings
            start_time = time.time()
            batch_output = self.embedding_engine.embed_texts(
                texts=texts,
                batch_size=self.batch_size
            )
            elapsed_ms = (time.time() - start_time) * 1000

            logger.debug(
                f"Generated embeddings for {len(texts)} chunks "
                f"in {elapsed_ms:.0f}ms"
            )

            # Create results
            for idx, chunk in enumerate(batch_chunks):
                result = TextEmbeddingResult(
                    doc_id=doc_id,
                    chunk_id=chunk.chunk_id,
                    page_num=chunk.page_num,
                    embedding=batch_output['embeddings'][idx],
                    cls_token=batch_output['cls_tokens'][idx],
                    seq_length=batch_output['seq_lengths'][idx],
                    text=chunk.text,
                    processing_time_ms=elapsed_ms / len(texts)
                )
                all_results.append(result)

            # Report progress after each batch
            if progress_callback:
                try:
                    progress_callback(len(all_results), total_chunks)
                except Exception as e:
                    logger.warning(f"Progress callback failed: {e}")

        logger.info(
            f"Completed text processing: {len(all_results)} chunks"
        )

        return all_results

    def get_processing_stats(
        self,
        results: List[TextEmbeddingResult]
    ) -> Dict[str, Any]:
        """Get statistics from processing results.

        Args:
            results: List of TextEmbeddingResult objects

        Returns:
            Statistics dictionary
        """
        if not results:
            return {
                "num_chunks": 0,
                "total_time_ms": 0.0,
                "avg_time_per_chunk_ms": 0.0,
                "total_tokens": 0,
                "avg_tokens_per_chunk": 0.0
            }

        total_time = sum(r.processing_time_ms for r in results)
        total_tokens = sum(r.seq_length for r in results)

        return {
            "num_chunks": len(results),
            "total_time_ms": total_time,
            "avg_time_per_chunk_ms": total_time / len(results),
            "total_tokens": total_tokens,
            "avg_tokens_per_chunk": total_tokens / len(results),
            "min_tokens": min(r.seq_length for r in results),
            "max_tokens": max(r.seq_length for r in results),
            "total_text_chars": sum(len(r.text) for r in results)
        }
