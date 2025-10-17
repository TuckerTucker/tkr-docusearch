"""
Two-stage semantic search engine for DocuSearch MVP.

This module implements the main SearchEngine class that orchestrates:
- Stage 1: Fast retrieval with representative vectors
- Stage 2: Late interaction re-ranking with full multi-vectors
- Result merging and formatting

Usage:
    >>> from src.search.search_engine import SearchEngine
    >>> from src.search.mocks import MockEmbeddingEngine, MockStorageClient
    >>>
    >>> engine = SearchEngine(
    ...     storage_client=MockStorageClient(),
    ...     embedding_engine=MockEmbeddingEngine()
    ... )
    >>>
    >>> response = engine.search(
    ...     query="quarterly revenue growth",
    ...     n_results=10,
    ...     search_mode="hybrid"
    ... )
"""

import logging
import time
from typing import Any, Dict, List, Literal, Optional

import numpy as np

from .query_processor import QueryProcessingError, QueryProcessor
from .result_ranker import ResultRanker

logger = logging.getLogger(__name__)


class SearchEngine:
    """
    Two-stage semantic search engine.

    Implements hybrid visual + text search with:
    - Stage 1: Fast approximate retrieval (HNSW index)
    - Stage 2: Precise re-ranking (late interaction MaxSim)
    - Result merging and formatting
    """

    def __init__(
        self,
        storage_client,
        embedding_engine,
        default_n_results: int = 10,
        default_candidates: int = 100,
    ):
        """
        Initialize search engine.

        Args:
            storage_client: ChromaDB client for retrieval (or MockStorageClient)
            embedding_engine: ColPali engine for query embedding (or MockEmbeddingEngine)
            default_n_results: Default number of results to return
            default_candidates: Default Stage 1 candidates
        """
        self.storage = storage_client
        self.embedding = embedding_engine

        self.default_n_results = default_n_results
        self.default_candidates = default_candidates

        # Initialize components
        self.query_processor = QueryProcessor(embedding_engine)
        self.result_ranker = ResultRanker(score_normalization="min_max")

        # Statistics tracking
        self._stats = {
            "total_queries": 0,
            "stage1_times": [],
            "stage2_times": [],
            "total_times": [],
        }

        logger.info(
            f"Initialized SearchEngine (default_results={default_n_results}, "
            f"default_candidates={default_candidates})"
        )

    def search(
        self,
        query: str,
        n_results: Optional[int] = None,
        search_mode: Literal["hybrid", "visual_only", "text_only"] = "hybrid",
        filters: Optional[Dict[str, Any]] = None,
        enable_reranking: bool = True,
        rerank_candidates: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Execute two-stage semantic search.

        Args:
            query: Natural language search query
            n_results: Number of final results (default: self.default_n_results)
            search_mode: "hybrid", "visual_only", or "text_only"
            filters: Metadata filters (e.g., {"filename": "report.pdf"})
            enable_reranking: Enable Stage 2 late interaction (default: True)
            rerank_candidates: Stage 1 candidates (default: self.default_candidates)

        Returns:
            SearchResponse with ranked results and timing info

        Raises:
            ValueError: If query is empty or invalid
            SearchError: If search execution fails

        Workflow:
            1. Embed query with ColPali engine
            2. Stage 1: Retrieve top candidates from ChromaDB
            3. (Optional) Stage 2: Re-rank with late interaction
            4. Merge visual + text results
            5. Return top-n ranked results
        """
        # Set defaults
        n_results = n_results or self.default_n_results
        rerank_candidates = rerank_candidates or self.default_candidates

        # Validate inputs
        if search_mode not in ["hybrid", "visual_only", "text_only"]:
            raise ValueError(
                f"search_mode must be 'hybrid', 'visual_only', or 'text_only', "
                f"got '{search_mode}'"
            )

        total_start = time.time()

        try:
            # Step 1: Process query and generate embeddings
            logger.info(f"Processing query: '{query}' (mode={search_mode})")
            query_result = self.query_processor.process_query(query)

            query_embeddings = query_result["embeddings"]  # Full multi-vector
            query_cls = query_result["cls_token"]  # Representative vector

            # Step 2: Stage 1 - Fast retrieval
            stage1_start = time.time()
            candidates = self._stage1_retrieval(
                query_embedding=query_cls,
                search_mode=search_mode,
                filters=filters,
                n_candidates=rerank_candidates,
            )
            stage1_time = (time.time() - stage1_start) * 1000

            logger.info(f"Stage 1 retrieved {len(candidates)} candidates in {stage1_time:.1f}ms")

            # Step 3: Stage 2 - Late interaction re-ranking (optional)
            stage2_time = 0.0
            if enable_reranking and candidates:
                stage2_start = time.time()
                candidates = self._stage2_reranking(
                    query_embeddings=query_embeddings, candidates=candidates
                )
                stage2_time = (time.time() - stage2_start) * 1000

                logger.info(
                    f"Stage 2 re-ranked {len(candidates)} candidates in {stage2_time:.1f}ms"
                )

            # Step 4: Format results
            results = [
                self.result_ranker.format_search_result(candidate)
                for candidate in candidates[:n_results]
            ]

            # Calculate total time
            total_time = (time.time() - total_start) * 1000

            # Update statistics
            self._update_stats(stage1_time, stage2_time, total_time)

            # Build response
            response = {
                "results": results,
                "total_results": len(candidates),
                "query": query,
                "search_mode": search_mode,
                "stage1_time_ms": stage1_time,
                "stage2_time_ms": stage2_time,
                "total_time_ms": total_time,
                "candidates_retrieved": len(candidates),
                "reranked_count": len(candidates) if enable_reranking else 0,
            }

            logger.info(
                f"Search completed: {len(results)} results in {total_time:.1f}ms "
                f"(stage1={stage1_time:.1f}ms, stage2={stage2_time:.1f}ms)"
            )

            return response

        except QueryProcessingError as e:
            logger.error(f"Query processing failed: {e}")
            raise ValueError(f"Invalid query: {e}") from e

        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            raise SearchError(f"Search execution failed: {e}") from e

    def _stage1_retrieval(
        self,
        query_embedding: np.ndarray,
        search_mode: str,
        filters: Optional[Dict[str, Any]],
        n_candidates: int,
    ) -> List[Dict[str, Any]]:
        """
        Stage 1: Fast approximate retrieval using representative vectors.

        Args:
            query_embedding: Query embedding (CLS token), shape (768,)
            search_mode: "hybrid", "visual_only", or "text_only"
            filters: Metadata filters
            n_candidates: Number of candidates to retrieve

        Returns:
            List of candidates with metadata and embeddings

        Performance Target: <200ms
        """
        visual_results = []
        text_results = []

        try:
            # Query collections based on mode
            if search_mode in ["hybrid", "visual_only"]:
                visual_results = self.storage.search_visual(
                    query_embedding=query_embedding, n_results=n_candidates, filters=filters
                )
                logger.debug(f"Visual search returned {len(visual_results)} candidates")

            if search_mode in ["hybrid", "text_only"]:
                text_results = self.storage.search_text(
                    query_embedding=query_embedding, n_results=n_candidates, filters=filters
                )
                logger.debug(f"Text search returned {len(text_results)} candidates")

            # Merge results if hybrid mode
            if search_mode == "hybrid":
                candidates = self.result_ranker.merge_results(
                    visual_results=visual_results,
                    text_results=text_results,
                    n_results=n_candidates * 2,  # Keep more for Stage 2
                    deduplicate=False,  # Don't deduplicate yet
                )
            else:
                candidates = visual_results + text_results

            return candidates

        except Exception as e:
            logger.error(f"Stage 1 retrieval failed: {e}")
            raise RetrievalError(f"Stage 1 retrieval failed: {e}") from e

    def _stage2_reranking(
        self, query_embeddings: np.ndarray, candidates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Stage 2: Precise re-ranking using late interaction.

        Args:
            query_embeddings: Full multi-vector query, shape (seq_length, 768)
            candidates: Stage 1 candidates with full embeddings in metadata

        Returns:
            Candidates with updated scores (MaxSim)

        Performance Target: <100ms for 100 candidates
        """
        if not candidates:
            return candidates

        try:
            # Extract full embeddings from candidates
            document_embeddings = []
            for candidate in candidates:
                # Full embeddings should be in the candidate dict
                full_emb = candidate.get("full_embeddings")
                if full_emb is None:
                    logger.warning(
                        f"Candidate {candidate['id']} missing full_embeddings, "
                        f"skipping re-ranking"
                    )
                    # Use Stage 1 score as fallback
                    continue

                document_embeddings.append(full_emb)

            if not document_embeddings:
                logger.warning("No candidates have full embeddings, skipping Stage 2")
                return candidates

            # Compute late interaction scores
            scoring_output = self.embedding.score_multi_vector(
                query_embeddings=query_embeddings,
                document_embeddings=document_embeddings,
                use_gpu=True,
            )

            late_interaction_scores = scoring_output["scores"]

            # Update candidate scores and re-rank
            reranked_candidates = self.result_ranker.rank_by_late_interaction(
                candidates=candidates[: len(late_interaction_scores)],
                late_interaction_scores=late_interaction_scores,
            )

            return reranked_candidates

        except Exception as e:
            logger.warning(f"Stage 2 re-ranking failed: {e}, returning Stage 1 results")
            # Fallback: return Stage 1 results without re-ranking
            return candidates

    def _merge_results(
        self,
        visual_results: List[Dict[str, Any]],
        text_results: List[Dict[str, Any]],
        n_results: int,
    ) -> List[Dict[str, Any]]:
        """
        Merge and rank visual + text results.

        Args:
            visual_results: Ranked visual results
            text_results: Ranked text results
            n_results: Final result count

        Returns:
            Merged and ranked results

        Algorithm:
            1. Normalize scores to [0, 1] within each collection
            2. Merge by score (interleave visual and text)
            3. Deduplicate by doc_id (keep highest scoring per document)
            4. Return top-n results
        """
        return self.result_ranker.merge_results(
            visual_results=visual_results,
            text_results=text_results,
            n_results=n_results,
            deduplicate=True,
        )

    def _format_result(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format candidate into SearchResult structure.

        Args:
            candidate: Raw candidate from ChromaDB

        Returns:
            Formatted SearchResult with all required fields
        """
        return self.result_ranker.format_search_result(candidate)

    def _update_stats(self, stage1_time: float, stage2_time: float, total_time: float):
        """Update internal statistics."""
        self._stats["total_queries"] += 1
        self._stats["stage1_times"].append(stage1_time)
        self._stats["stage2_times"].append(stage2_time)
        self._stats["total_times"].append(total_time)

        # Keep only last 1000 queries
        for key in ["stage1_times", "stage2_times", "total_times"]:
            if len(self._stats[key]) > 1000:
                self._stats[key] = self._stats[key][-1000:]

    def get_search_stats(self) -> Dict[str, Any]:
        """
        Get search performance statistics.

        Returns:
            {
                "total_queries": int,
                "avg_stage1_ms": float,
                "avg_stage2_ms": float,
                "avg_total_ms": float,
                "p95_total_ms": float
            }
        """
        if self._stats["total_queries"] == 0:
            return {
                "total_queries": 0,
                "avg_stage1_ms": 0.0,
                "avg_stage2_ms": 0.0,
                "avg_total_ms": 0.0,
                "p95_total_ms": 0.0,
            }

        return {
            "total_queries": self._stats["total_queries"],
            "avg_stage1_ms": np.mean(self._stats["stage1_times"]),
            "avg_stage2_ms": np.mean(self._stats["stage2_times"]),
            "avg_total_ms": np.mean(self._stats["total_times"]),
            "p95_total_ms": np.percentile(self._stats["total_times"], 95),
        }


class SearchError(Exception):
    """Base exception for search operations."""


class RetrievalError(SearchError):
    """Stage 1 retrieval failed."""


class RerankingError(SearchError):
    """Stage 2 re-ranking failed."""


class ResultFormattingError(SearchError):
    """Failed to format results."""
