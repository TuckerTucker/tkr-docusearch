"""
Visual processing pipeline for document pages.

This module handles the visual embedding generation for document pages,
coordinating with the embedding agent and preparing results for storage.
"""

import logging
import time
from typing import List, Dict, Any
from dataclasses import dataclass
import numpy as np

from .docling_parser import Page

logger = logging.getLogger(__name__)


@dataclass
class VisualEmbeddingResult:
    """Result from visual embedding processing.

    Attributes:
        doc_id: Document identifier
        page_num: Page number (1-indexed)
        embedding: Full multi-vector sequence
        cls_token: Representative CLS token vector
        seq_length: Number of tokens
        processing_time_ms: Time taken for embedding
    """

    doc_id: str
    page_num: int
    embedding: np.ndarray  # Shape: (seq_length, 768)
    cls_token: np.ndarray  # Shape: (768,)
    seq_length: int
    processing_time_ms: float


class VisualProcessor:
    """Visual processing pipeline for document pages.

    Handles page-level visual embedding generation using the embedding agent.
    """

    def __init__(self, embedding_engine, batch_size: int = 4):
        """Initialize visual processor.

        Args:
            embedding_engine: Embedding engine instance (real or mock)
            batch_size: Number of pages to process at once
        """
        self.embedding_engine = embedding_engine
        self.batch_size = batch_size
        logger.info(f"Initialized VisualProcessor (batch_size={batch_size})")

    def process_pages(
        self,
        pages: List[Page],
        doc_id: str
    ) -> List[VisualEmbeddingResult]:
        """Process pages and generate visual embeddings.

        Args:
            pages: List of Page objects
            doc_id: Document identifier

        Returns:
            List of VisualEmbeddingResult objects

        Raises:
            ValueError: If pages list is empty
            Exception: If embedding generation fails
        """
        if not pages:
            raise ValueError("Pages list cannot be empty")

        logger.info(
            f"Processing {len(pages)} pages for visual embeddings "
            f"(batch_size={self.batch_size})"
        )

        all_results = []
        total_pages = len(pages)

        # Process in batches
        for batch_start in range(0, total_pages, self.batch_size):
            batch_end = min(batch_start + self.batch_size, total_pages)
            batch_pages = pages[batch_start:batch_end]

            logger.debug(
                f"Processing batch {batch_start//self.batch_size + 1}: "
                f"pages {batch_start+1}-{batch_end}"
            )

            # Extract images from pages
            images = [page.image for page in batch_pages]

            # Generate embeddings
            start_time = time.time()
            batch_output = self.embedding_engine.embed_images(
                images=images,
                batch_size=self.batch_size
            )
            elapsed_ms = (time.time() - start_time) * 1000

            logger.debug(
                f"Generated embeddings for {len(images)} pages "
                f"in {elapsed_ms:.0f}ms"
            )

            # Create results
            for idx, page in enumerate(batch_pages):
                result = VisualEmbeddingResult(
                    doc_id=doc_id,
                    page_num=page.page_num,
                    embedding=batch_output['embeddings'][idx],
                    cls_token=batch_output['cls_tokens'][idx],
                    seq_length=batch_output['seq_lengths'][idx],
                    processing_time_ms=elapsed_ms / len(images)
                )
                all_results.append(result)

        logger.info(
            f"Completed visual processing: {len(all_results)} pages"
        )

        return all_results

    def get_processing_stats(
        self,
        results: List[VisualEmbeddingResult]
    ) -> Dict[str, Any]:
        """Get statistics from processing results.

        Args:
            results: List of VisualEmbeddingResult objects

        Returns:
            Statistics dictionary
        """
        if not results:
            return {
                "num_pages": 0,
                "total_time_ms": 0.0,
                "avg_time_per_page_ms": 0.0,
                "total_tokens": 0,
                "avg_tokens_per_page": 0.0
            }

        total_time = sum(r.processing_time_ms for r in results)
        total_tokens = sum(r.seq_length for r in results)

        return {
            "num_pages": len(results),
            "total_time_ms": total_time,
            "avg_time_per_page_ms": total_time / len(results),
            "total_tokens": total_tokens,
            "avg_tokens_per_page": total_tokens / len(results),
            "min_tokens": min(r.seq_length for r in results),
            "max_tokens": max(r.seq_length for r in results)
        }
