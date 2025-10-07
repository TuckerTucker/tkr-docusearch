"""
Result ranking and merging module for two-stage search.

This module handles:
- Score normalization across collections
- Visual + text result merging
- Deduplication by document ID
- Final result ranking

Usage:
    >>> from src.search.result_ranker import ResultRanker
    >>> ranker = ResultRanker()
    >>> merged = ranker.merge_results(visual_results, text_results, n_results=10)
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)


class ResultRanker:
    """
    Result ranker for merging and ranking visual + text search results.

    Responsibilities:
    - Normalize scores within each collection
    - Merge visual and text results by score
    - Deduplicate by document ID
    - Format final search results
    """

    def __init__(self, score_normalization: str = "min_max"):
        """
        Initialize result ranker.

        Args:
            score_normalization: Normalization method ("min_max", "z_score", "none")
        """
        self.score_normalization = score_normalization

        logger.info(
            f"Initialized ResultRanker (normalization={score_normalization})"
        )

    def merge_results(
        self,
        visual_results: List[Dict[str, Any]],
        text_results: List[Dict[str, Any]],
        n_results: int = 10,
        deduplicate: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Merge visual and text results.

        Strategy:
        1. Normalize scores within each collection
        2. Combine lists and sort by normalized_score (descending)
        3. Deduplicate: Keep highest score per doc_id
        4. Return top-n results

        Args:
            visual_results: Ranked visual results with scores
            text_results: Ranked text results with scores
            n_results: Final result count
            deduplicate: If True, keep only highest scoring result per document

        Returns:
            Merged and ranked results
        """
        # Normalize scores
        if visual_results:
            visual_results = self._normalize_scores(visual_results, "visual")

        if text_results:
            text_results = self._normalize_scores(text_results, "text")

        # Combine and sort
        combined = visual_results + text_results
        combined.sort(key=lambda x: x.get("normalized_score", x["score"]), reverse=True)

        # Deduplicate by doc_id if requested
        if deduplicate:
            combined = self._deduplicate_by_doc(combined)

        # Return top-n
        results = combined[:n_results]

        logger.debug(
            f"Merged {len(visual_results)} visual + {len(text_results)} text "
            f"results into {len(results)} final results"
        )

        return results

    def _normalize_scores(
        self,
        results: List[Dict[str, Any]],
        collection: str
    ) -> List[Dict[str, Any]]:
        """
        Normalize scores to [0, 1] range within collection.

        This ensures fair comparison between visual and text results.

        Args:
            results: Results with "score" field
            collection: Collection name ("visual" or "text")

        Returns:
            Results with added "normalized_score" field
        """
        if not results:
            return results

        scores = np.array([r["score"] for r in results])

        if self.score_normalization == "min_max":
            # Min-max normalization to [0, 1]
            min_score = np.min(scores)
            max_score = np.max(scores)

            if max_score > min_score:
                normalized = (scores - min_score) / (max_score - min_score)
            else:
                # All scores are equal
                normalized = np.ones_like(scores) * 0.5

        elif self.score_normalization == "z_score":
            # Z-score normalization
            mean_score = np.mean(scores)
            std_score = np.std(scores)

            if std_score > 0:
                normalized = (scores - mean_score) / std_score
                # Shift to [0, 1] range approximately
                normalized = 1 / (1 + np.exp(-normalized))
            else:
                normalized = np.ones_like(scores) * 0.5

        elif self.score_normalization == "none":
            # No normalization
            normalized = scores

        else:
            logger.warning(
                f"Unknown normalization method '{self.score_normalization}', "
                f"using min_max"
            )
            min_score = np.min(scores)
            max_score = np.max(scores)
            normalized = (scores - min_score) / (max_score - min_score) if max_score > min_score else np.ones_like(scores) * 0.5

        # Add normalized scores to results
        for i, result in enumerate(results):
            result["normalized_score"] = float(normalized[i])
            result["original_score"] = result["score"]
            result["collection"] = collection

        return results

    def _deduplicate_by_doc(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Deduplicate results by document ID.

        Keeps the highest scoring result for each document.

        Args:
            results: Sorted results (highest score first)

        Returns:
            Deduplicated results
        """
        seen_docs = set()
        deduplicated = []

        for result in results:
            doc_id = result.get("metadata", {}).get("doc_id")

            if doc_id is None:
                # No doc_id, keep result
                deduplicated.append(result)
                continue

            if doc_id not in seen_docs:
                deduplicated.append(result)
                seen_docs.add(doc_id)
            else:
                logger.debug(
                    f"Skipping duplicate doc_id={doc_id} "
                    f"(score={result.get('normalized_score', result['score']):.3f})"
                )

        return deduplicated

    def rank_by_late_interaction(
        self,
        candidates: List[Dict[str, Any]],
        late_interaction_scores: List[float]
    ) -> List[Dict[str, Any]]:
        """
        Update candidate scores with late interaction scores and re-rank.

        Args:
            candidates: Candidates from Stage 1
            late_interaction_scores: MaxSim scores from Stage 2

        Returns:
            Re-ranked candidates with updated scores

        Raises:
            ValueError: If lengths don't match
        """
        if len(candidates) != len(late_interaction_scores):
            raise ValueError(
                f"Candidates ({len(candidates)}) and scores ({len(late_interaction_scores)}) "
                f"must have same length"
            )

        # Update scores
        for candidate, score in zip(candidates, late_interaction_scores):
            candidate["stage1_score"] = candidate["score"]
            candidate["score"] = score

        # Re-rank by new scores
        candidates.sort(key=lambda x: x["score"], reverse=True)

        logger.debug(
            f"Re-ranked {len(candidates)} candidates with late interaction scores"
        )

        return candidates

    def format_search_result(
        self,
        candidate: Dict[str, Any],
        include_highlights: bool = True
    ) -> Dict[str, Any]:
        """
        Format candidate into SearchResult structure.

        Args:
            candidate: Raw candidate from search
            include_highlights: If True, extract highlights from metadata

        Returns:
            Formatted SearchResult
        """
        metadata = candidate.get("metadata", {})

        result = {
            "id": candidate["id"],
            "doc_id": metadata.get("doc_id", "unknown"),
            "type": metadata.get("type", "unknown"),
            "score": candidate["score"],
            "filename": metadata.get("filename", ""),
            "page": metadata.get("page", 0),
            "source_path": metadata.get("source_path", ""),
            "thumbnail_url": self._generate_thumbnail_url(candidate["id"], metadata),
            "text_preview": metadata.get("text_preview"),
            "highlights": self._extract_highlights(metadata) if include_highlights else [],
            "metadata": {
                "chunk_id": metadata.get("chunk_id"),
                "word_count": metadata.get("word_count"),
                "timestamp": metadata.get("timestamp"),
                "seq_length": metadata.get("seq_length"),
                "normalized_score": candidate.get("normalized_score"),
                "stage1_score": candidate.get("stage1_score")
            }
        }

        return result

    def _generate_thumbnail_url(
        self,
        embedding_id: str,
        metadata: Dict[str, Any]
    ) -> Optional[str]:
        """Generate thumbnail URL for visual results."""
        if metadata.get("type") == "visual":
            return f"/api/thumbnail/{embedding_id}"
        return None

    def _extract_highlights(self, metadata: Dict[str, Any]) -> List[str]:
        """
        Extract matching terms or phrases from metadata.

        This is a simplified version. Full implementation would analyze
        query tokens and find matches in text_preview.
        """
        highlights = []

        text_preview = metadata.get("text_preview", "")
        if text_preview:
            # Extract first few significant words as highlights
            words = text_preview.split()
            highlights = [w.strip(".,!?;:") for w in words[:5] if len(w) > 3]

        return highlights[:10]  # Limit to 10 highlights
