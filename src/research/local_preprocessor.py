"""
Local LLM Preprocessing Engine for Research Bot.

Implements three preprocessing strategies to optimize context before sending to foundation models:
1. Compression: Extract key facts from chunks, reducing token count 30-50%
2. Filtering: Score and filter chunks by relevance, retaining 40-60% of sources
3. Synthesis: Cross-document knowledge synthesis with citation preservation

All strategies preserve metadata for proper citation tracking and bidirectional highlighting.
"""

import asyncio
import os
from typing import List

import structlog

from src.research.context_builder import SourceDocument
from src.research.mlx_llm_client import ContextLengthError, MLXLLMClient
from src.research.prompts import PreprocessingPrompts
from src.research.response_parsers import HarmonyResponseParser

logger = structlog.get_logger(__name__)


class LocalLLMPreprocessor:
    """Pre-process search results using local LLM before foundation model."""

    def __init__(self, mlx_client: MLXLLMClient):
        """
        Initialize preprocessor with local LLM client.

        Args:
            mlx_client: Initialized MLXLLMClient instance

        Side Effects:
            - Stores reference to MLX client
            - Initializes performance tracking metrics
            - Reads USE_HARMONY_PROMPTS env var (default: true)
        """
        self.local_llm = mlx_client
        # Check environment flag for Harmony prompts (default: true)
        self.use_harmony = os.getenv("USE_HARMONY_PROMPTS", "true").lower() == "true"
        logger.info(
            "LocalLLMPreprocessor initialized",
            use_harmony_prompts=self.use_harmony
        )

    async def compress_chunks(
        self, query: str, sources: List[SourceDocument]
    ) -> List[SourceDocument]:
        """
        Compress each source chunk to extract key facts, reducing token count.

        Args:
            query: User's research question (for context-aware compression)
            sources: List of SourceDocument objects from search results

        Returns:
            List[SourceDocument] with compressed markdown_content,
            all other metadata preserved (doc_id, chunk_id, page, etc.)

        Performance:
            - Target: 30-50% token reduction per chunk
            - Latency: <3 seconds total for 10 chunks
            - Parallelizable: Process chunks concurrently

        Raises:
            LLMError: If local LLM fails (handled gracefully with fallback)
        """
        logger.info(
            "Starting chunk compression",
            query=query,
            num_sources=len(sources),
        )

        try:
            # Build index mapping: track which sources need compression
            # This preserves original order while allowing parallel processing
            source_index_map = (
                []
            )  # List of (index, source, needs_compression, original_token_count)
            tasks = []
            original_token_count = 0

            for idx, source in enumerate(sources):
                source_tokens = len(source.markdown_content) // 4

                # Skip visual sources (no text to compress)
                if source.is_visual:
                    source_index_map.append((idx, source, False, 0))
                    logger.debug(
                        "Skipping visual source",
                        doc_id=source.doc_id,
                        page=source.page,
                    )
                    continue

                # Skip very short chunks (<400 chars ≈ 100 tokens)
                if len(source.markdown_content) < 400:
                    source_index_map.append((idx, source, False, 0))
                    logger.info(
                        "Skipping short chunk (below 400 char threshold)",
                        doc_id=source.doc_id,
                        page=source.page,
                        length=len(source.markdown_content),
                        is_visual=source.is_visual,
                        chunk_id=source.chunk_id,
                    )
                    continue

                # Queue compression task and track original tokens
                source_index_map.append((idx, source, True, source_tokens))
                original_token_count += source_tokens
                tasks.append(self._compress_single_chunk(query, source))
                logger.info(
                    "Queuing chunk for compression",
                    doc_id=source.doc_id,
                    page=source.page,
                    length=len(source.markdown_content),
                    tokens=source_tokens,
                    is_visual=source.is_visual,
                    chunk_id=source.chunk_id,
                )

            # Process all compression tasks in parallel
            compressed_results = []
            if tasks:
                logger.debug("Processing compression tasks", num_tasks=len(tasks))
                compressed_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Reconstruct result list in original order
            compressed = [None] * len(sources)
            task_idx = 0

            for idx, source, needs_compression, _ in source_index_map:
                if not needs_compression:
                    # Use original source (visual or short)
                    compressed[idx] = source
                else:
                    # Use compressed result or fallback to original on error
                    result = compressed_results[task_idx]
                    if isinstance(result, Exception):
                        logger.warning(
                            "Compression failed for chunk, using original",
                            error=str(result),
                            doc_id=source.doc_id,
                            page=source.page,
                        )
                        compressed[idx] = source
                    else:
                        compressed[idx] = result
                    task_idx += 1

            # Calculate overall compression metrics
            # Only count sources that were actually processed
            compressed_token_count = sum(
                len(compressed[idx].markdown_content) // 4
                for idx, _, needs_compression, _ in source_index_map
                if needs_compression
            )
            reduction_pct = (
                (1 - compressed_token_count / original_token_count) * 100
                if original_token_count > 0
                else 0.0
            )

            logger.info(
                "Chunk compression complete",
                num_sources=len(sources),
                num_compressed=len(compressed),
                original_tokens=original_token_count,
                compressed_tokens=compressed_token_count,
                reduction_pct=round(reduction_pct, 1),
            )

            return compressed

        except Exception as e:
            logger.error("Compression failed, returning uncompressed sources", error=str(e))
            # Graceful degradation: return original sources
            return sources

    async def filter_by_relevance(
        self, query: str, sources: List[SourceDocument], threshold: float = 7.0
    ) -> List[SourceDocument]:
        """
        Score each source by relevance, filter out low-scoring chunks.

        Args:
            query: User's research question
            sources: List of SourceDocument objects from search results
            threshold: Minimum relevance score (0-10 scale, default: 7.0)

        Returns:
            Filtered list of SourceDocument objects where score >= threshold,
            sorted by relevance score descending

        Performance:
            - Target: Complete in <3 seconds for 20 chunks
            - Expected retention rate: 40-60% of sources
            - Parallelizable: Score chunks concurrently

        Raises:
            LLMError: If local LLM fails (handled gracefully with fallback)
            ValueError: If threshold not in range 0-10
        """
        # Validate threshold
        if not (0.0 <= threshold <= 10.0):
            raise ValueError(f"Threshold must be in range 0-10, got: {threshold}")

        logger.info(
            "Starting relevance filtering",
            query=query,
            num_sources=len(sources),
            threshold=threshold,
        )

        try:
            # Score all chunks in parallel
            scoring_tasks = [self._score_chunk_relevance(query, source) for source in sources]

            scores = await asyncio.gather(*scoring_tasks, return_exceptions=True)

            # Build scored sources (handle exceptions)
            scored_sources = []
            for source, score in zip(sources, scores):
                if isinstance(score, Exception):
                    logger.warning(
                        "Scoring failed for chunk, assigning score 0",
                        doc_id=source.doc_id,
                        page=source.page,
                        error=str(score),
                    )
                    score = 0.0

                # Add LLM relevance score to metadata
                # Note: This doesn't modify the SourceDocument dataclass directly,
                # but we'll track it for sorting/filtering
                scored_sources.append((source, score))

            # Filter by threshold
            filtered = [(source, score) for source, score in scored_sources if score >= threshold]

            # Sort by score descending
            filtered.sort(key=lambda x: x[1], reverse=True)

            # Extract sources (without scores for return)
            filtered_sources = [source for source, score in filtered]

            # Calculate retention rate
            retention_pct = (len(filtered_sources) / len(sources) * 100) if sources else 0

            logger.info(
                "Relevance filtering complete",
                num_original=len(sources),
                num_filtered=len(filtered_sources),
                retention_pct=round(retention_pct, 1),
                threshold=threshold,
            )

            return filtered_sources

        except Exception as e:
            logger.error("Filtering failed, returning unfiltered sources", error=str(e))
            # Graceful degradation: return original sources
            return sources

    async def synthesize_knowledge(self, query: str, sources: List[SourceDocument]) -> str:
        """
        Cross-document synthesis with source tracking.

        Args:
            query: User's research question
            sources: List of SourceDocument objects from search results

        Returns:
            Synthesized context string (markdown formatted) with:
            - Thematic organization of facts
            - Source citations in [N] format matching source order
            - Contradictions noted
            - Information gaps identified

        Performance:
            - Target: Complete in <5 seconds for 15 sources
            - Single LLM call (all chunks in one synthesis)
            - Token limit: ~10K input, ~500 output

        Raises:
            LLMError: If local LLM fails (handled gracefully with fallback)
            ContextLengthError: If combined sources exceed model limit
        """
        logger.info(
            "Starting knowledge synthesis",
            query=query,
            num_sources=len(sources),
        )

        # Format sources as numbered chunks
        numbered_chunks = PreprocessingPrompts.format_numbered_chunks(sources)

        # Check token limit (~10K tokens)
        # MUST raise ContextLengthError if exceeded (contract requirement)
        estimated_tokens = len(numbered_chunks) // 4
        if estimated_tokens > 10000:
            logger.error(
                "Combined sources exceed token limit",
                estimated_tokens=estimated_tokens,
                limit=10000,
                exceeded_by=estimated_tokens - 10000,
            )
            raise ContextLengthError(
                f"Combined sources exceed token limit: {estimated_tokens} > 10000",
                exceeded_by=estimated_tokens - 10000,
            )

        try:
            # Build synthesis prompt
            prompt = PreprocessingPrompts.get_synthesis_prompt(query, numbered_chunks)

            logger.debug(
                "Calling LLM for synthesis",
                estimated_tokens=estimated_tokens,
            )

            # Call local LLM (single call with all chunks)
            response = await self.local_llm.complete(
                prompt=prompt,
                max_tokens=500,  # Synthesis should be concise
            )

            synthesized_text = response.content

            logger.info(
                "Knowledge synthesis complete",
                num_sources=len(sources),
                synthesis_tokens=response.usage["completion_tokens"],
                latency_ms=response.latency_ms,
            )

            return synthesized_text

        except Exception as e:
            logger.error("Synthesis failed, returning formatted chunks", error=str(e))
            # Graceful degradation: return formatted chunks (only for LLM errors, not context length)
            return numbered_chunks

    # ============================================================================
    # Private Helper Methods
    # ============================================================================

    async def _compress_single_chunk(self, query: str, source: SourceDocument) -> SourceDocument:
        """
        Compress a single chunk using local LLM with Harmony format.

        Args:
            query: User's research question
            source: SourceDocument to compress

        Returns:
            SourceDocument with compressed markdown_content, metadata preserved

        Raises:
            LLMError: If local LLM fails during compression

        Changes:
            - Uses Harmony-format prompt if use_harmony=True
            - Parses JSON response and validates compression
            - Falls back to original text if compression fails or expands
            - Enhanced logging with token metrics
        """
        logger.debug(
            "Compressing chunk",
            doc_id=source.doc_id,
            page=source.page,
            chunk_id=source.chunk_id,
            original_length=len(source.markdown_content),
            use_harmony=self.use_harmony,
        )

        # Build compression prompt (Harmony or legacy)
        if self.use_harmony:
            prompt = PreprocessingPrompts.get_harmony_compression_prompt(
                query=query, chunk_content=source.markdown_content
            )
        else:
            prompt = PreprocessingPrompts.get_compression_prompt(
                query=query, chunk_content=source.markdown_content
            )

        # Call local LLM with increased timeout for safety
        response = await self.local_llm.complete(
            prompt=prompt,
            max_tokens=500,
            timeout=120  # Increased from default 60s
        )

        # Parse response (Harmony JSON format or legacy plain text)
        if self.use_harmony:
            # Parse JSON response
            parsed_result = HarmonyResponseParser.parse_json_response(
                response=response.content,
                schema_type="compression",
                doc_id=source.doc_id,
                chunk_id=source.chunk_id,
            )
            compressed_text = parsed_result["facts"]

            # Validate compression effectiveness
            is_valid = HarmonyResponseParser.validate_compression(
                compressed=compressed_text,
                original=source.markdown_content,
            )

            # Use original if compression failed (expansion detected)
            if not is_valid:
                logger.warning(
                    "Compression rejected (expansion detected), using original",
                    doc_id=source.doc_id,
                    chunk_id=source.chunk_id,
                    original_length=len(source.markdown_content),
                    compressed_length=len(compressed_text),
                )
                compressed_text = source.markdown_content
                compression_method = "rejected"
            else:
                compression_method = "harmony_json"
        else:
            # Legacy path: use response as-is
            compressed_text = response.content
            is_valid = len(compressed_text) < len(source.markdown_content)
            compression_method = "legacy"

        # Calculate compression metrics
        original_tokens = len(source.markdown_content) // 4
        compressed_tokens = len(compressed_text) // 4
        reduction_pct = (
            (1 - compressed_tokens / original_tokens) * 100 if original_tokens > 0 else 0
        )

        # Enhanced logging
        logger.info(
            "Chunk compressed",
            doc_id=source.doc_id,
            page=source.page,
            chunk_id=source.chunk_id,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            reduction_pct=round(reduction_pct, 1),
            compression_valid=is_valid,
            compression_method=compression_method,
            latency_ms=response.latency_ms,
        )

        # Create a new SourceDocument with compressed content
        # Must not mutate original to maintain immutability
        from dataclasses import replace

        compressed_source = replace(source, markdown_content=compressed_text)

        return compressed_source

    async def _score_chunk_relevance(self, query: str, source: SourceDocument) -> float:
        """
        Score a single chunk's relevance 0-10 using Harmony format.

        Args:
            query: User's research question
            source: SourceDocument to score

        Returns:
            Relevance score (0-10 scale)

        Note:
            Visual sources always score 9.0 (preserve visual matches)

        Changes:
            - Uses Harmony-format relevance prompt if use_harmony=True
            - Parses JSON response: {"score": int}
            - Falls back to neutral score (5.0) on parse failure (per contract)
        """
        # Visual sources always score high (preserve visual matches)
        if source.is_visual:
            logger.debug(
                "Visual source auto-scored",
                doc_id=source.doc_id,
                page=source.page,
                score=9.0,
            )
            return 9.0

        logger.debug(
            "Scoring chunk relevance",
            doc_id=source.doc_id,
            page=source.page,
            chunk_id=source.chunk_id,
            use_harmony=self.use_harmony,
        )

        # Build relevance prompt (Harmony or legacy)
        if self.use_harmony:
            prompt = PreprocessingPrompts.get_harmony_relevance_prompt(
                query=query, chunk_content=source.markdown_content
            )
            max_tokens = 10  # Allow for JSON format
        else:
            prompt = PreprocessingPrompts.get_relevance_prompt(
                query=query, chunk_content=source.markdown_content
            )
            max_tokens = 5  # Only need 1-2 digits

        # Call local LLM
        response = await self.local_llm.complete(
            prompt=prompt,
            max_tokens=max_tokens,
            timeout=30
        )

        # Parse response (Harmony JSON format or legacy plain number)
        if self.use_harmony:
            # Parse JSON response
            try:
                parsed_result = HarmonyResponseParser.parse_json_response(
                    response=response.content,
                    schema_type="relevance",
                    doc_id=source.doc_id,
                    chunk_id=source.chunk_id,
                )
                score = float(parsed_result["score"])
                # Clamp to 0-10 range
                score = max(0.0, min(10.0, score))

            except Exception as e:
                logger.warning(
                    "Relevance scoring failed, using neutral score",
                    doc_id=source.doc_id,
                    chunk_id=source.chunk_id,
                    error=str(e),
                )
                score = 5.0  # Neutral fallback (per contract)
        else:
            # Legacy path: parse plain number
            try:
                score = float(response.content.strip())
                # Clamp to 0-10 range
                score = max(0.0, min(10.0, score))
            except ValueError:
                logger.warning(
                    "Invalid score from LLM, assigning neutral score",
                    doc_id=source.doc_id,
                    page=source.page,
                    llm_response=response.content,
                )
                score = 5.0  # Changed from 0.0 to match Harmony fallback

        logger.debug(
            "Chunk scored",
            doc_id=source.doc_id,
            page=source.page,
            chunk_id=source.chunk_id,
            score=score,
        )

        return score
