"""
Local LLM Preprocessing Engine for Research Bot.

Implements three preprocessing strategies to optimize context before sending to foundation models:
1. Compression: Extract key facts from chunks, reducing token count 30-50%
2. Filtering: Score and filter chunks by relevance, retaining 40-60% of sources
3. Synthesis: Cross-document knowledge synthesis with citation preservation

All strategies preserve metadata for proper citation tracking and bidirectional highlighting.
"""

import asyncio
import json
import os
import re
from typing import Any, Dict, List, Optional

import structlog

from tkr_docusearch.research.context_builder import SourceDocument
from tkr_docusearch.research.mlx_llm_client import ContextLengthError, MLXLLMClient
from tkr_docusearch.research.prompts import PreprocessingPrompts
from tkr_docusearch.research.response_parsers import HarmonyResponseParser
from tkr_docusearch.storage.metadata_schema import ChunkContext

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
        logger.info("LocalLLMPreprocessor initialized", use_harmony_prompts=self.use_harmony)

    @staticmethod
    def _parse_chunk_context(metadata: Dict[str, Any]) -> Optional[ChunkContext]:
        """
        Parse chunk_context_json from ChromaDB metadata.

        Args:
            metadata: Raw metadata dict from ChromaDB search result

        Returns:
            ChunkContext object if chunk_context_json exists, None otherwise

        Example:
            >>> metadata = {"chunk_context_json": '{"related_pictures": ["fig1.png"]}'}
            >>> context = LocalLLMPreprocessor._parse_chunk_context(metadata)
            >>> context.related_pictures
            ['fig1.png']
        """
        if "chunk_context_json" not in metadata:
            return None

        try:
            context_dict = json.loads(metadata["chunk_context_json"])
            return ChunkContext.from_dict(context_dict)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(
                "Failed to parse chunk_context_json",
                error=str(e),
                metadata_keys=list(metadata.keys()),
            )
            return None

    @staticmethod
    def _has_visual_dependency(
        chunk_context: Optional[ChunkContext],
        markdown_content: str,
        element_type: Optional[str] = None,
    ) -> bool:
        """
        Determine if a chunk requires visual context (images, charts, tables).

        Uses multiple heuristics:
        1. Docling metadata: related_pictures, related_tables, element_type
        2. Markdown analysis: visual references ("Figure", "Chart", "Table", "diagram")

        Args:
            chunk_context: Parsed ChunkContext from metadata (can be None)
            markdown_content: Text content of the chunk
            element_type: Element type from metadata (fallback if no chunk_context)

        Returns:
            True if chunk has visual dependencies, False otherwise

        Examples:
            Text with related images:
            >>> context = ChunkContext(related_pictures=["chart.png"])
            >>> LocalLLMPreprocessor._has_visual_dependency(context, "Revenue data", "text")
            True

            Text referencing a figure:
            >>> LocalLLMPreprocessor._has_visual_dependency(None, "As shown in Figure 3", "text")
            True

            Plain text:
            >>> LocalLLMPreprocessor._has_visual_dependency(None, "This is plain text", "text")
            False
        """
        # Heuristic 1: Docling metadata indicates visual relationships
        if chunk_context:
            if chunk_context.related_pictures:
                logger.debug(
                    "Visual dependency: related_pictures", count=len(chunk_context.related_pictures)
                )
                return True

            if chunk_context.related_tables:
                logger.debug(
                    "Visual dependency: related_tables", count=len(chunk_context.related_tables)
                )
                return True

            # Use chunk_context.element_type if available
            element_type = chunk_context.element_type

        # Heuristic 2: Element type suggests visual content
        visual_element_types = {"table", "list_item", "picture", "figure"}
        if element_type and element_type.lower() in visual_element_types:
            logger.debug("Visual dependency: element_type", element_type=element_type)
            return True

        # Heuristic 3: Markdown contains visual references
        visual_patterns = [
            r"\bfigure\s+\d+\b",  # "Figure 3"
            r"\btable\s+\d+\b",  # "Table 2"
            r"\bchart\b",  # "chart"
            r"\bdiagram\b",  # "diagram"
            r"\bgraph\b",  # "graph"
            r"\bsee\s+(figure|table|chart|diagram)\b",  # "see Figure"
            r"\bas\s+shown\s+in\s+(figure|table|chart)\b",  # "as shown in Figure"
            r"\bthe\s+(chart|diagram|graph)\s+shows\b",  # "the chart shows"
            r"\bthe\s+(chart|diagram|graph)\s+illustrates\b",  # "the chart illustrates"
        ]

        content_lower = markdown_content.lower()
        for pattern in visual_patterns:
            if re.search(pattern, content_lower):
                logger.debug(
                    "Visual dependency: markdown pattern",
                    pattern=pattern,
                    match=re.search(pattern, content_lower).group(),
                )
                return True

        return False

    async def compress_chunks(
        self, query: str, sources: List[SourceDocument]
    ) -> List[SourceDocument]:
        """
        Synthesize all source chunks into a single comprehensive summary.

        Instead of compressing each chunk individually, this creates ONE synthesized
        summary from ALL sources (including visual match text) and returns it as a
        single source. This dramatically reduces token count sent to foundation model.

        Args:
            query: User's research question (for context-aware synthesis)
            sources: List of SourceDocument objects from search results

        Returns:
            List with ONE SourceDocument containing the synthesized summary,
            preserving source tracking for citations

        Performance:
            - Target: 50-70% token reduction overall
            - Latency: Single LLM call for synthesis (~20-30s)
            - Output: ONE summary instead of N chunks

        Raises:
            LLMError: If local LLM fails (handled gracefully with fallback)
        """
        logger.info(
            "Starting synthesis-based compression",
            query=query,
            num_sources=len(sources),
            use_harmony=self.use_harmony,
        )

        try:
            # Calculate original token count for all sources
            original_token_count = sum(len(source.markdown_content) // 4 for source in sources)

            # Format ALL sources (including visual match text) as numbered chunks
            numbered_chunks = PreprocessingPrompts.format_numbered_chunks(sources)

            # Estimate tokens
            estimated_tokens = len(numbered_chunks) // 4
            logger.info(
                "Synthesis request",
                num_sources=len(sources),
                estimated_tokens=estimated_tokens,
                original_tokens=original_token_count,
                context_limit=128000,
            )

            # Check token limit
            if estimated_tokens > 100000:  # Leave room for output
                logger.warning(
                    "Context approaching limit, may need chunking",
                    estimated_tokens=estimated_tokens,
                    limit=128000,
                )

            # Call local LLM to synthesize all sources into one summary
            if self.use_harmony:
                prompt = PreprocessingPrompts.get_harmony_synthesis_prompt(
                    query=query, numbered_chunks=numbered_chunks
                )
            else:
                prompt = PreprocessingPrompts.get_synthesis_prompt(query, numbered_chunks)

            response = await self.local_llm.complete(
                prompt=prompt,
                max_tokens=2000,  # Synthesis should be comprehensive but concise
                timeout=180,
            )

            synthesized_text = response.content.strip()

            # Calculate token reduction
            synthesized_tokens = len(synthesized_text) // 4
            reduction_pct = (
                (1 - synthesized_tokens / original_token_count) * 100
                if original_token_count > 0
                else 0.0
            )

            logger.info(
                "Synthesis complete",
                original_sources=len(sources),
                original_tokens=original_token_count,
                synthesized_tokens=synthesized_tokens,
                reduction_pct=round(reduction_pct, 1),
                latency_ms=response.latency_ms,
            )

            # Create a single SourceDocument with the synthesized summary
            # This replaces ALL sources with ONE synthesized summary
            from dataclasses import replace

            # Use the first source as the template, update content to be the synthesis
            synthesized_source = replace(
                sources[0],
                markdown_content=f"# Synthesized Summary\n\n{synthesized_text}",
                chunk_id="synthesized-summary",
                page=0,  # Special marker for synthesized content
            )

            # Return list with just the one synthesized source
            return [synthesized_source]

        except Exception as e:
            logger.error("Synthesis failed, returning original sources", error=str(e))
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

    async def _compress_chunks_legacy(
        self, query: str, sources: List[SourceDocument]
    ) -> List[SourceDocument]:
        """
        Legacy individual chunk compression (fallback when Harmony prompts disabled).

        This is the original implementation that processes chunks in parallel but makes
        separate LLM calls for each chunk. Kept for backward compatibility.
        """
        logger.info("Using legacy individual chunk compression")

        # Build index mapping
        source_index_map = []
        tasks = []
        original_token_count = 0

        for idx, source in enumerate(sources):
            source_tokens = len(source.markdown_content) // 4

            if source.is_visual or len(source.markdown_content) < 400:
                source_index_map.append((idx, source, False, 0))
                continue

            chunk_context = self._parse_chunk_context(source.raw_metadata)
            has_visual_dep = self._has_visual_dependency(
                chunk_context, source.markdown_content, source.raw_metadata.get("element_type")
            )

            source.has_visual_dependency = has_visual_dep
            if chunk_context:
                source.related_pictures = chunk_context.related_pictures
                source.related_tables = chunk_context.related_tables

            source_index_map.append((idx, source, True, source_tokens))
            original_token_count += source_tokens
            tasks.append(self._compress_single_chunk(query, source))

        # Process all compression tasks in parallel
        compressed_results = []
        if tasks:
            compressed_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Reconstruct result list
        compressed = [None] * len(sources)
        task_idx = 0

        for idx, source, needs_compression, _ in source_index_map:
            if not needs_compression:
                compressed[idx] = source
            else:
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

        return compressed

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

        # Build compression prompt (Harmony or legacy, with visual-awareness)
        if self.use_harmony:
            prompt = PreprocessingPrompts.get_harmony_compression_prompt(
                query=query, chunk_content=source.markdown_content
            )
        else:
            prompt = PreprocessingPrompts.get_compression_prompt(
                query=query,
                chunk_content=source.markdown_content,
                has_visual_dependency=source.has_visual_dependency,
            )

        # Call local LLM with increased timeout for safety
        response = await self.local_llm.complete(
            prompt=prompt, max_tokens=500, timeout=120  # Increased from default 60s
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
        response = await self.local_llm.complete(prompt=prompt, max_tokens=max_tokens, timeout=30)

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
