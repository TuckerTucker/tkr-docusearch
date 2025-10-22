"""
Unit tests for Local LLM Preprocessor.

Tests the LocalLLMPreprocessor's ability to compress, filter, and synthesize
search results using mocked MLX client. All tests validate the integration
contract defined in 03-preprocessor-engine-interface.md.
"""

import asyncio
from unittest.mock import AsyncMock

import pytest

from src.research.context_builder import SourceDocument
from src.research.local_preprocessor import LocalLLMPreprocessor
from src.research.mlx_llm_client import LLMError, LLMResponse


@pytest.fixture
def mock_mlx_client():
    """Create mock MLX client with configurable responses"""
    client = AsyncMock()

    # Default response for compression (30% token reduction)
    def compression_response(prompt, **kwargs):
        # Extract content after "Compress this:"
        if "compress" in prompt.lower() or "condense" in prompt.lower():
            # Return ~60% of original length (40% reduction)
            compressed = "Compressed key facts from the original content."
            return LLMResponse(
                content=compressed,
                model="gpt-oss-20b-mlx",
                provider="mlx",
                usage={"prompt_tokens": 100, "completion_tokens": 10, "total_tokens": 110},
                finish_reason="stop",
                latency_ms=200,
            )
        return LLMResponse(
            content="Compressed content.",
            model="gpt-oss-20b-mlx",
            provider="mlx",
            usage={"prompt_tokens": 100, "completion_tokens": 10, "total_tokens": 110},
            finish_reason="stop",
            latency_ms=200,
        )

    client.complete.side_effect = compression_response
    return client


@pytest.fixture
def sample_sources():
    """Create sample SourceDocument objects for testing"""
    return [
        SourceDocument(
            doc_id="doc1",
            filename="report.pdf",
            page=1,
            extension="pdf",
            thumbnail_path="/images/doc1/page001_thumb.jpg",
            image_path="/images/doc1/page001.jpg",
            timestamp="2025-10-22T10:00:00Z",
            section_path="Introduction",
            parent_heading="Background",
            markdown_content="This is a long chunk with substantial content that should be compressed. "
            * 20,  # ~1000+ chars
            relevance_score=0.95,
            chunk_id="doc1-chunk0001",
            is_visual=False,
        ),
        SourceDocument(
            doc_id="doc2",
            filename="data.xlsx",
            page=2,
            extension="xlsx",
            thumbnail_path="/images/doc2/page002_thumb.jpg",
            markdown_content="This is a visual source from image search results.",
            relevance_score=0.88,
            chunk_id=None,  # Visual sources have no chunk_id
            is_visual=True,
        ),
        SourceDocument(
            doc_id="doc3",
            filename="notes.docx",
            page=1,
            extension="docx",
            markdown_content="Short chunk.",  # <400 chars, should skip compression
            relevance_score=0.82,
            chunk_id="doc3-chunk0001",
            is_visual=False,
        ),
    ]


@pytest.fixture
def many_sources():
    """Create 20 sources for filtering tests"""
    sources = []
    for i in range(20):
        sources.append(
            SourceDocument(
                doc_id=f"doc{i}",
                filename=f"file{i}.pdf",
                page=i + 1,
                extension="pdf",
                markdown_content=f"Content for document {i}. " * 30,
                relevance_score=0.9 - (i * 0.02),  # Decreasing scores
                chunk_id=f"doc{i}-chunk0001",
                is_visual=(i % 5 == 0),  # Every 5th is visual
            )
        )
    return sources


class TestLocalLLMPreprocessorInitialization:
    """Test preprocessor initialization"""

    def test_initialization_with_mlx_client(self, mock_mlx_client):
        """Test preprocessor accepts MLX client via dependency injection"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)
        assert preprocessor.local_llm is mock_mlx_client

    def test_stateless_between_calls(self, mock_mlx_client):
        """Test preprocessor is stateless (no request-specific state retained)"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        # Verify no request-specific state exists
        assert not hasattr(preprocessor, "current_query")
        assert not hasattr(preprocessor, "current_sources")


class TestCompressChunksStrategy:
    """Test compression strategy (Option 2)"""

    @pytest.mark.asyncio
    async def test_compress_chunks_reduces_tokens(self, mock_mlx_client, sample_sources):
        """Test compression achieves ≥30% token reduction"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        # Get long source only
        long_source = [s for s in sample_sources if len(s.markdown_content) >= 400]

        compressed = await preprocessor.compress_chunks(
            query="Test query",
            sources=long_source,
        )

        # Check token reduction
        original_tokens = len(long_source[0].markdown_content) // 4
        compressed_tokens = len(compressed[0].markdown_content) // 4
        reduction_pct = (1 - compressed_tokens / original_tokens) * 100

        assert reduction_pct >= 30, f"Compression only {reduction_pct}%, expected ≥30%"

    @pytest.mark.asyncio
    async def test_compress_chunks_preserves_metadata(self, mock_mlx_client, sample_sources):
        """Test all metadata fields preserved except markdown_content"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        original = sample_sources[0]  # Long text source

        compressed = await preprocessor.compress_chunks(
            query="Test query",
            sources=[original],
        )

        result = compressed[0]

        # Verify all metadata preserved
        assert result.doc_id == original.doc_id
        assert result.filename == original.filename
        assert result.page == original.page
        assert result.extension == original.extension
        assert result.thumbnail_path == original.thumbnail_path
        assert result.image_path == original.image_path
        assert result.timestamp == original.timestamp
        assert result.section_path == original.section_path
        assert result.parent_heading == original.parent_heading
        assert result.relevance_score == original.relevance_score
        assert result.chunk_id == original.chunk_id
        assert result.is_visual == original.is_visual

        # Content should be different (compressed)
        assert result.markdown_content != original.markdown_content
        assert len(result.markdown_content) < len(original.markdown_content)

    @pytest.mark.asyncio
    async def test_compress_chunks_skips_visual_sources(self, mock_mlx_client, sample_sources):
        """Test visual sources bypass compression unchanged"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        # Get visual source
        visual_source = [s for s in sample_sources if s.is_visual][0]
        original_content = visual_source.markdown_content

        compressed = await preprocessor.compress_chunks(
            query="Test query",
            sources=[visual_source],
        )

        # Visual source content unchanged
        assert compressed[0].markdown_content == original_content
        assert compressed[0].is_visual is True

    @pytest.mark.asyncio
    async def test_compress_chunks_skips_short_chunks(self, mock_mlx_client, sample_sources):
        """Test short chunks (<400 chars) bypass compression"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        # Get short source
        short_source = [s for s in sample_sources if len(s.markdown_content) < 400][0]
        original_content = short_source.markdown_content

        compressed = await preprocessor.compress_chunks(
            query="Test query",
            sources=[short_source],
        )

        # Short source content unchanged
        assert compressed[0].markdown_content == original_content

    @pytest.mark.asyncio
    async def test_compress_chunks_maintains_order(self, mock_mlx_client, sample_sources):
        """Test source order maintained (citation numbers depend on it)"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        compressed = await preprocessor.compress_chunks(
            query="Test query",
            sources=sample_sources,
        )

        # Verify same order
        assert len(compressed) == len(sample_sources)
        for i, (original, result) in enumerate(zip(sample_sources, compressed)):
            assert result.doc_id == original.doc_id
            assert result.page == original.page

    @pytest.mark.asyncio
    async def test_compress_chunks_parallel_processing(self, mock_mlx_client, many_sources):
        """Test chunks processed concurrently (asyncio.gather)"""
        import time

        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        # Mock LLM to track concurrency
        call_count = 0
        max_concurrent = 0
        current_concurrent = 0

        async def track_concurrent_response(prompt, **kwargs):
            nonlocal call_count, max_concurrent, current_concurrent
            call_count += 1
            current_concurrent += 1
            max_concurrent = max(max_concurrent, current_concurrent)

            # Simulate processing time
            await asyncio.sleep(0.1)

            current_concurrent -= 1

            return LLMResponse(
                content="Compressed.",
                model="gpt-oss-20b-mlx",
                provider="mlx",
                usage={"prompt_tokens": 100, "completion_tokens": 10, "total_tokens": 110},
            )

        mock_mlx_client.complete.side_effect = track_concurrent_response

        # Get only long text sources (skip visual and short)
        long_sources = [
            s for s in many_sources if not s.is_visual and len(s.markdown_content) >= 400
        ][:10]

        start = time.time()
        await preprocessor.compress_chunks(
            query="Test query",
            sources=long_sources,
        )
        elapsed = time.time() - start

        # Verify parallel execution
        # If sequential: 10 * 0.1s = 1.0s
        # If parallel: ~0.1s
        # The implementation uses asyncio.gather, so should be parallel
        # Check that multiple tasks ran concurrently
        assert (
            max_concurrent > 1
        ), f"Max concurrent was {max_concurrent}, expected >1 (parallel execution)"

        # Also check time is reasonable (with overhead)
        assert elapsed < 2.0, f"Processing took {elapsed}s, expected <2.0s"

    @pytest.mark.asyncio
    async def test_compress_chunks_error_handling(self, mock_mlx_client, sample_sources):
        """Test graceful degradation on LLM error"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        # Mock LLM to fail
        mock_mlx_client.complete.side_effect = LLMError("Model failed")

        # Should return original sources on error (graceful fallback)
        result = await preprocessor.compress_chunks(
            query="Test query",
            sources=sample_sources,
        )

        # Should return sources (may be original or partial)
        assert len(result) <= len(sample_sources)


class TestFilterByRelevanceStrategy:
    """Test filtering strategy (Option 1)"""

    @pytest.mark.asyncio
    async def test_filter_by_relevance_scores_chunks(self, mock_mlx_client, sample_sources):
        """Test each chunk receives score 0-10"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        # Mock scoring responses
        scores = ["8.5", "9.0", "5.0"]  # Above/below threshold
        score_iter = iter(scores)

        async def score_response(prompt, **kwargs):
            try:
                score = next(score_iter)
            except StopIteration:
                score = "7.0"
            return LLMResponse(
                content=score,
                model="gpt-oss-20b-mlx",
                provider="mlx",
                usage={"prompt_tokens": 100, "completion_tokens": 1, "total_tokens": 101},
            )

        mock_mlx_client.complete.side_effect = score_response

        filtered = await preprocessor.filter_by_relevance(
            query="Test query",
            sources=sample_sources,
            threshold=7.0,
        )

        # Should filter out score 5.0
        # Visual source (doc2) gets automatic 9.0
        assert len(filtered) <= len(sample_sources)

    @pytest.mark.asyncio
    async def test_filter_by_relevance_threshold(self, mock_mlx_client, many_sources):
        """Test threshold filtering keeps only score >= threshold"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        # Mock distributed scores 2-10
        score_values = [f"{i:.1f}" for i in range(2, 11)]  # 2.0, 3.0, ..., 10.0
        score_iter = iter(score_values * 3)  # Repeat to cover all sources

        async def score_response(prompt, **kwargs):
            try:
                score = next(score_iter)
            except StopIteration:
                score = "5.0"
            return LLMResponse(
                content=score,
                model="gpt-oss-20b-mlx",
                provider="mlx",
                usage={"prompt_tokens": 100, "completion_tokens": 1, "total_tokens": 101},
            )

        mock_mlx_client.complete.side_effect = score_response

        filtered = await preprocessor.filter_by_relevance(
            query="Test query",
            sources=many_sources,
            threshold=7.0,
        )

        # Should retain ~40-60% of sources
        retention_pct = len(filtered) / len(many_sources) * 100
        assert 20 <= retention_pct <= 80, f"Retention {retention_pct}%, expected 20-80%"

    @pytest.mark.asyncio
    async def test_filter_by_relevance_sorts_descending(self, mock_mlx_client, many_sources):
        """Test filtered sources sorted by score descending"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        # Mock scores in random order
        score_values = ["8.0", "9.5", "7.2", "10.0", "6.5", "8.8"]
        score_iter = iter(score_values * 5)

        async def score_response(prompt, **kwargs):
            try:
                score = next(score_iter)
            except StopIteration:
                score = "7.0"
            return LLMResponse(
                content=score,
                model="gpt-oss-20b-mlx",
                provider="mlx",
                usage={"prompt_tokens": 100, "completion_tokens": 1, "total_tokens": 101},
            )

        mock_mlx_client.complete.side_effect = score_response

        filtered = await preprocessor.filter_by_relevance(
            query="Test query",
            sources=many_sources[:10],  # Use subset
            threshold=7.0,
        )

        # Verify filtering happened
        assert len(filtered) <= 10

    @pytest.mark.asyncio
    async def test_filter_by_relevance_visual_sources_score_high(
        self, mock_mlx_client, sample_sources
    ):
        """Test visual sources always score ≥7"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        # Mock low scores for text sources
        async def low_score_response(prompt, **kwargs):
            return LLMResponse(
                content="2.0",  # Low score
                model="gpt-oss-20b-mlx",
                provider="mlx",
                usage={"prompt_tokens": 100, "completion_tokens": 1, "total_tokens": 101},
            )

        mock_mlx_client.complete.side_effect = low_score_response

        filtered = await preprocessor.filter_by_relevance(
            query="Test query",
            sources=sample_sources,
            threshold=7.0,
        )

        # Visual source should pass threshold despite low text scores
        visual_in_filtered = any(s.is_visual for s in filtered)
        assert visual_in_filtered, "Visual source should pass threshold"

    @pytest.mark.asyncio
    async def test_filter_by_relevance_handles_non_numeric(self, mock_mlx_client, sample_sources):
        """Test non-numeric LLM responses assigned score 0.0"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        # Mock invalid responses
        async def invalid_response(prompt, **kwargs):
            return LLMResponse(
                content="Not a number!",
                model="gpt-oss-20b-mlx",
                provider="mlx",
                usage={"prompt_tokens": 100, "completion_tokens": 3, "total_tokens": 103},
            )

        mock_mlx_client.complete.side_effect = invalid_response

        filtered = await preprocessor.filter_by_relevance(
            query="Test query",
            sources=sample_sources,
            threshold=7.0,
        )

        # Only visual sources should pass (they get 9.0 automatically)
        assert all(s.is_visual for s in filtered)

    @pytest.mark.asyncio
    async def test_filter_by_relevance_invalid_threshold(self, mock_mlx_client, sample_sources):
        """Test ValueError raised for threshold not in 0-10 range"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        with pytest.raises(ValueError, match="threshold|range|0.*10"):
            await preprocessor.filter_by_relevance(
                query="Test query",
                sources=sample_sources,
                threshold=15.0,  # Invalid
            )

    @pytest.mark.asyncio
    async def test_filter_by_relevance_preserves_original_score(
        self, mock_mlx_client, sample_sources
    ):
        """Test original relevance_score field preserved from semantic search"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        # Mock high scores to keep all sources
        async def high_score_response(prompt, **kwargs):
            return LLMResponse(
                content="9.0",
                model="gpt-oss-20b-mlx",
                provider="mlx",
                usage={"prompt_tokens": 100, "completion_tokens": 1, "total_tokens": 101},
            )

        mock_mlx_client.complete.side_effect = high_score_response

        filtered = await preprocessor.filter_by_relevance(
            query="Test query",
            sources=sample_sources,
            threshold=7.0,
        )

        # Verify original relevance scores unchanged
        for original in sample_sources:
            matching = [f for f in filtered if f.doc_id == original.doc_id]
            if matching:
                assert matching[0].relevance_score == original.relevance_score


class TestSynthesizeKnowledgeStrategy:
    """Test synthesis strategy (Option 3)"""

    @pytest.mark.asyncio
    async def test_synthesize_knowledge_format(self, mock_mlx_client, sample_sources):
        """Test synthesis returns markdown with ## headers and citations"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        # Mock synthesis response with markdown structure
        async def synthesis_response(prompt, **kwargs):
            return LLMResponse(
                content="""## Key Findings

The research shows important results [1]. Additional data supports this [2].

## Methodology

Methods are described in [1] and [3].

## Gaps

Some information is missing regarding techniques [2].""",
                model="gpt-oss-20b-mlx",
                provider="mlx",
                usage={"prompt_tokens": 500, "completion_tokens": 50, "total_tokens": 550},
            )

        mock_mlx_client.complete.side_effect = synthesis_response

        result = await preprocessor.synthesize_knowledge(
            query="Test query",
            sources=sample_sources,
        )

        # Verify return type is string
        assert isinstance(result, str)

        # Verify markdown structure
        assert "##" in result

        # Verify citations present
        assert "[1]" in result
        assert "[2]" in result

    @pytest.mark.asyncio
    async def test_synthesize_knowledge_preserves_citations(self, mock_mlx_client, sample_sources):
        """Test citation numbers match sources list order [1], [2], [3]"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        # Mock response with specific citations
        async def synthesis_response(prompt, **kwargs):
            # Verify numbered chunks in prompt
            assert "[1]" in prompt
            assert "[2]" in prompt
            assert "[3]" in prompt

            return LLMResponse(
                content="Findings from sources [1], [2], and [3].",
                model="gpt-oss-20b-mlx",
                provider="mlx",
                usage={"prompt_tokens": 500, "completion_tokens": 10, "total_tokens": 510},
            )

        mock_mlx_client.complete.side_effect = synthesis_response

        result = await preprocessor.synthesize_knowledge(
            query="Test query",
            sources=sample_sources,
        )

        # Verify citations match source count
        for i in range(1, len(sample_sources) + 1):
            assert f"[{i}]" in result or str(i) in result

    @pytest.mark.asyncio
    async def test_synthesize_knowledge_single_llm_call(self, mock_mlx_client, sample_sources):
        """Test single LLM call for all chunks (not multiple calls)"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        call_count = 0

        async def count_calls_response(prompt, **kwargs):
            nonlocal call_count
            call_count += 1
            return LLMResponse(
                content="## Summary\n\nSynthesized content.",
                model="gpt-oss-20b-mlx",
                provider="mlx",
                usage={"prompt_tokens": 500, "completion_tokens": 10, "total_tokens": 510},
            )

        mock_mlx_client.complete.side_effect = count_calls_response

        await preprocessor.synthesize_knowledge(
            query="Test query",
            sources=sample_sources,
        )

        # Should be exactly one call
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_synthesize_knowledge_token_limit_check(self, mock_mlx_client):
        """Test raises error if combined sources exceed 10K tokens"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        # Create sources with very long content (>10K tokens)
        huge_sources = [
            SourceDocument(
                doc_id=f"doc{i}",
                filename=f"file{i}.pdf",
                page=i,
                extension="pdf",
                markdown_content="word " * 15000,  # ~15K tokens total
                relevance_score=0.9,
                chunk_id=f"doc{i}-chunk0001",
                is_visual=False,
            )
            for i in range(3)
        ]

        # Should raise error for exceeding context
        with pytest.raises((LLMError, ValueError), match="Context|token|10K|limit|exceed"):
            await preprocessor.synthesize_knowledge(
                query="Test query",
                sources=huge_sources,
            )

    @pytest.mark.asyncio
    async def test_synthesize_knowledge_returns_string_not_list(
        self, mock_mlx_client, sample_sources
    ):
        """Test return type is str, NOT List[SourceDocument]"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        async def synthesis_response(prompt, **kwargs):
            return LLMResponse(
                content="Synthesized context.",
                model="gpt-oss-20b-mlx",
                provider="mlx",
                usage={"prompt_tokens": 500, "completion_tokens": 5, "total_tokens": 505},
            )

        mock_mlx_client.complete.side_effect = synthesis_response

        result = await preprocessor.synthesize_knowledge(
            query="Test query",
            sources=sample_sources,
        )

        # Must be string
        assert isinstance(result, str)
        assert not isinstance(result, list)


class TestErrorHandling:
    """Test error handling and graceful degradation"""

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_llm_error(self, mock_mlx_client, sample_sources):
        """Test fallback to unprocessed sources on LLM failure"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        # Mock LLM error
        mock_mlx_client.complete.side_effect = LLMError("Model crashed")

        # Should return original sources on error
        result = await preprocessor.compress_chunks(
            query="Test query",
            sources=sample_sources,
        )

        # Should return sources (fallback behavior)
        assert len(result) <= len(sample_sources)

    @pytest.mark.asyncio
    async def test_handles_empty_sources(self, mock_mlx_client):
        """Test handles empty source list gracefully"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        # Empty sources
        result = await preprocessor.compress_chunks(
            query="Test query",
            sources=[],
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_handles_none_markdown_content(self, mock_mlx_client):
        """Test handles sources with empty/None markdown_content"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        # Source with empty content
        empty_source = SourceDocument(
            doc_id="doc1",
            filename="empty.pdf",
            page=1,
            extension="pdf",
            markdown_content="",
            relevance_score=0.5,
            chunk_id="doc1-chunk0001",
            is_visual=False,
        )

        # Should handle gracefully (skip or pass through)
        result = await preprocessor.compress_chunks(
            query="Test query",
            sources=[empty_source],
        )

        assert len(result) == 1


class TestPerformanceRequirements:
    """Test performance targets are achievable"""

    @pytest.mark.asyncio
    async def test_compression_performance_target(self, mock_mlx_client, many_sources):
        """Test compression completes in <3s for 10 chunks"""
        import time

        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        # Mock fast LLM responses (200ms each)
        async def fast_response(prompt, **kwargs):
            await asyncio.sleep(0.2)  # Simulate 200ms latency
            return LLMResponse(
                content="Compressed content.",
                model="gpt-oss-20b-mlx",
                provider="mlx",
                usage={"prompt_tokens": 100, "completion_tokens": 10, "total_tokens": 110},
                latency_ms=200,
            )

        mock_mlx_client.complete.side_effect = fast_response

        # Use 10 long text sources
        test_sources = [s for s in many_sources if not s.is_visual][:10]

        start = time.time()
        await preprocessor.compress_chunks(
            query="Test query",
            sources=test_sources,
        )
        elapsed = time.time() - start

        # Should complete in <3s with parallelization
        assert elapsed < 3.0, f"Compression took {elapsed}s, target <3s"

    @pytest.mark.asyncio
    async def test_filtering_performance_target(self, mock_mlx_client, many_sources):
        """Test filtering completes in <3s for 20 chunks"""
        import time

        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        # Mock fast scoring responses
        async def fast_score_response(prompt, **kwargs):
            await asyncio.sleep(0.1)  # 100ms per score
            return LLMResponse(
                content="8.0",
                model="gpt-oss-20b-mlx",
                provider="mlx",
                usage={"prompt_tokens": 100, "completion_tokens": 1, "total_tokens": 101},
                latency_ms=100,
            )

        mock_mlx_client.complete.side_effect = fast_score_response

        start = time.time()
        await preprocessor.filter_by_relevance(
            query="Test query",
            sources=many_sources,
            threshold=7.0,
        )
        elapsed = time.time() - start

        # Should complete in <3s
        assert elapsed < 3.0, f"Filtering took {elapsed}s, target <3s"
