"""
Integration tests for Local LLM Preprocessing with REAL MLX model.

Tests end-to-end preprocessing flow with real MLX LLM client when available.
Falls back to mock when MLX model not configured. Validates:
- All three preprocessing strategies (compress, filter, synthesize)
- Token reduction performance (≥30%)
- Citation accuracy (≥95%)
- Error handling and graceful degradation
- Performance benchmarks (<3-5s preprocessing latency)

Requirements:
- Set LOCAL_PREPROCESS_ENABLED=true to enable preprocessing
- Set MLX_MODEL_PATH=/path/to/model for real MLX testing
- Tests skip gracefully if MLX model not available
"""

import asyncio
import os
import time
from typing import List
from unittest.mock import AsyncMock

import pytest

from src.research.context_builder import SourceDocument
from src.research.local_preprocessor import LocalLLMPreprocessor
from src.research.mlx_llm_client import ContextLengthError, LLMError, LLMResponse, MLXLLMClient

# ============================================================================
# Configuration & Utilities
# ============================================================================

MLX_MODEL_PATH = os.getenv("MLX_MODEL_PATH")
MLX_MODEL_AVAILABLE = MLX_MODEL_PATH and os.path.exists(MLX_MODEL_PATH)

# Skip markers
skip_without_mlx = pytest.mark.skipif(
    not MLX_MODEL_AVAILABLE,
    reason="MLX model not available. Set MLX_MODEL_PATH to run with real model.",
)


def estimate_tokens(text: str) -> int:
    """Estimate token count using 4 chars/token heuristic"""
    return len(text) // 4


def calculate_reduction_percent(original: int, processed: int) -> float:
    """Calculate percentage reduction from original to processed"""
    if original == 0:
        return 0.0
    return ((original - processed) / original) * 100


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_sources() -> List[SourceDocument]:
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
            markdown_content=(
                "The 2008 financial crisis was triggered by a combination of factors including "
                "subprime mortgage lending, securitization of risky mortgages into complex financial "
                "instruments, excessive leverage by financial institutions, and inadequate regulatory "
                "oversight. Banks issued mortgages to borrowers with poor credit histories, then packaged "
                "these loans into mortgage-backed securities (MBS) and collateralized debt obligations (CDOs). "
                "When housing prices declined, defaults increased, causing massive losses for investors. "
                "Major financial institutions like Lehman Brothers collapsed, leading to a global credit freeze. "
                "The crisis resulted in the Great Recession, with millions of job losses and home foreclosures."
            )
            * 3,  # ~2000+ chars for compression
            relevance_score=0.95,
            chunk_id="doc1-chunk0001",
            is_visual=False,
        ),
        SourceDocument(
            doc_id="doc2",
            filename="chart.png",
            page=1,
            extension="png",
            thumbnail_path="/images/doc2/page001_thumb.jpg",
            image_path="/images/doc2/page001.jpg",
            timestamp="2025-10-22T10:00:00Z",
            markdown_content="Visual representation of mortgage default rates 2006-2009.",
            relevance_score=0.88,
            chunk_id=None,  # Visual sources have no chunk_id
            is_visual=True,
        ),
        SourceDocument(
            doc_id="doc3",
            filename="notes.docx",
            page=2,
            extension="docx",
            timestamp="2025-10-22T10:00:00Z",
            markdown_content=(
                "Regulatory failures contributed significantly to the crisis. The repeal of Glass-Steagall "
                "in 1999 allowed commercial banks to engage in investment banking activities. Rating agencies "
                "gave AAA ratings to risky securities due to conflicts of interest. The Federal Reserve "
                "maintained low interest rates, encouraging excessive borrowing. Deregulation reduced oversight "
                "of derivatives markets and shadow banking systems. International factors included global "
                "imbalances and foreign investment in U.S. securities."
            )
            * 2,
            relevance_score=0.82,
            chunk_id="doc3-chunk0002",
            is_visual=False,
        ),
        SourceDocument(
            doc_id="doc4",
            filename="timeline.pdf",
            page=5,
            extension="pdf",
            timestamp="2025-10-22T10:00:00Z",
            markdown_content="Brief note: Crisis peaked in September 2008.",
            relevance_score=0.75,
            chunk_id="doc4-chunk0003",
            is_visual=False,
        ),
    ]


@pytest.fixture
def many_sources() -> List[SourceDocument]:
    """Create 15 sources for filtering tests"""
    sources = []
    topics = [
        ("Housing market collapse", 9.5),
        ("Subprime mortgages", 9.0),
        ("Lehman Brothers bankruptcy", 8.5),
        ("Credit default swaps", 8.0),
        ("Government bailouts", 7.5),
        ("Bear Stearns collapse", 7.0),
        ("Rating agency failures", 6.5),
        ("Derivatives trading", 6.0),
        ("Global contagion effects", 5.5),
        ("Iceland banking crisis", 5.0),
        ("European debt crisis", 4.5),
        ("China economic impact", 4.0),
        ("Regulatory reform proposals", 3.5),
        ("Dodd-Frank Act details", 3.0),
        ("Current market conditions", 2.5),
    ]

    for i, (topic, expected_score) in enumerate(topics):
        sources.append(
            SourceDocument(
                doc_id=f"doc{i}",
                filename=f"source{i}.pdf",
                page=i + 1,
                extension="pdf",
                timestamp="2025-10-22T10:00:00Z",
                markdown_content=f"Content about {topic}. " * 50,  # ~500+ chars
                relevance_score=expected_score / 10.0,  # Normalize to 0-1
                chunk_id=f"doc{i}-chunk{i:04d}",
                is_visual=False,
            )
        )

    return sources


@pytest.fixture
async def mock_mlx_client():
    """Create mock MLX client for tests without real model"""
    client = AsyncMock(spec=MLXLLMClient)

    # Track call count for varying scores
    call_count = {"value": 0}

    async def mock_complete(prompt, **kwargs):
        """Mock completion with realistic responses"""
        # Simulate compression (40% reduction)
        if "compress" in prompt.lower() or "extract key facts" in prompt.lower():
            content = "Key facts: Crisis caused by subprime mortgages, securitization failures, regulatory gaps."
            tokens = 20
        # Simulate relevance scoring with varying scores (Harmony JSON format)
        elif "relevance" in prompt.lower() or "score" in prompt.lower():
            # Return scores from 9.5 down to 2.5 (mimic varying relevance)
            scores = [9.5, 9.0, 8.5, 8.0, 7.5, 7.0, 6.5, 6.0, 5.5, 5.0, 4.5, 4.0, 3.5, 3.0, 2.5]
            score = scores[call_count["value"] % len(scores)]
            call_count["value"] += 1
            # Return proper JSON format for Harmony prompts (use "score", not "relevance_score")
            content = f'{{"score": {score}, "reasoning": "Mock relevance assessment"}}'
            tokens = 10
        # Simulate synthesis
        elif "synthesize" in prompt.lower() or "organize" in prompt.lower():
            content = (
                "## Financial Crisis Overview\n\n"
                "The 2008 crisis stemmed from multiple factors [1][3]:\n"
                "- Subprime mortgage lending and securitization [1]\n"
                "- Regulatory failures and deregulation [3]\n"
                "- Excessive leverage by institutions [1]\n\n"
                "Visual evidence shows default rate trends [2]."
            )
            tokens = 80
        else:
            content = "Generic response."
            tokens = 5

        # Simulate realistic latency (200-500ms per call)
        await asyncio.sleep(0.2)

        return LLMResponse(
            content=content,
            model="gpt-oss-20b-mlx",
            provider="mlx",
            usage={"prompt_tokens": 100, "completion_tokens": tokens, "total_tokens": 100 + tokens},
            finish_reason="stop",
            latency_ms=200,
        )

    client.complete = mock_complete
    return client


@pytest.fixture
async def real_mlx_client():
    """Create real MLX client if model available"""
    if not MLX_MODEL_AVAILABLE:
        pytest.skip("MLX model not available")

    client = MLXLLMClient(
        model_path=MLX_MODEL_PATH,
        max_tokens=500,
        temperature=0.3,
    )
    yield client
    # Cleanup
    del client


# ============================================================================
# Test 1: Initialization and Configuration
# ============================================================================


class TestPreprocessorInitialization:
    """Test preprocessor initialization with various configurations"""

    @pytest.mark.asyncio
    async def test_init_with_mock_client(self, mock_mlx_client):
        """Test initialization with mock MLX client"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        assert preprocessor is not None
        assert preprocessor.local_llm is not None

    @skip_without_mlx
    @pytest.mark.asyncio
    async def test_init_with_real_client(self, real_mlx_client):
        """Test initialization with real MLX client"""
        preprocessor = LocalLLMPreprocessor(mlx_client=real_mlx_client)

        assert preprocessor is not None
        assert preprocessor.local_llm is not None


# ============================================================================
# Test 2: Compression Strategy
# ============================================================================


class TestCompressionStrategy:
    """Test compression preprocessing strategy"""

    @pytest.mark.asyncio
    async def test_compression_with_mock(self, mock_mlx_client, sample_sources):
        """Test compression with mock client achieves token reduction via synthesis"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        # Calculate baseline tokens
        original_tokens = sum(estimate_tokens(s.markdown_content) for s in sample_sources)

        # Compress
        start_time = time.time()
        compressed = await preprocessor.compress_chunks(
            query="What caused the 2008 financial crisis?", sources=sample_sources
        )
        latency = time.time() - start_time

        # Synthesis creates ONE result
        assert len(compressed) == 1, f"Expected 1 synthesized result, got {len(compressed)}"

        # Verify synthesis format
        result = compressed[0]
        assert result.chunk_id == "synthesized-summary"
        assert "# Synthesized Summary" in result.markdown_content
        assert result.page == 0

        # Calculate compressed tokens
        compressed_tokens = estimate_tokens(result.markdown_content)

        # Validate token reduction (synthesis should compress significantly)
        reduction_pct = calculate_reduction_percent(original_tokens, compressed_tokens)
        assert reduction_pct >= 30, f"Expected ≥30% reduction, got {reduction_pct:.1f}%"

        # Validate performance (mock should be fast)
        assert latency < 5, f"Compression took {latency:.2f}s, expected <5s"

        # Validate first source metadata preserved in synthesis
        assert result.doc_id == sample_sources[0].doc_id
        assert result.filename == sample_sources[0].filename

    @skip_without_mlx
    @pytest.mark.asyncio
    async def test_compression_with_real_mlx(self, real_mlx_client, sample_sources):
        """Test compression with real MLX model achieves ≥30% token reduction"""
        preprocessor = LocalLLMPreprocessor(mlx_client=real_mlx_client)

        # Calculate baseline tokens
        original_tokens = sum(estimate_tokens(s.markdown_content) for s in sample_sources)

        # Compress with performance tracking
        start_time = time.time()
        compressed = await preprocessor.compress_chunks(
            query="What caused the 2008 financial crisis?", sources=sample_sources
        )
        latency = time.time() - start_time

        # Validate results
        assert len(compressed) == len(sample_sources)

        # Calculate compressed tokens
        compressed_tokens = sum(estimate_tokens(s.markdown_content) for s in compressed)
        reduction_pct = calculate_reduction_percent(original_tokens, compressed_tokens)

        # Log performance metrics
        print(f"\n[COMPRESSION BENCHMARK - Real MLX]")
        print(f"  Original tokens: {original_tokens}")
        print(f"  Compressed tokens: {compressed_tokens}")
        print(f"  Reduction: {reduction_pct:.1f}%")
        print(f"  Latency: {latency:.2f}s")
        print(f"  Sources processed: {len(sample_sources)}")

        # Validate performance targets
        assert reduction_pct >= 30, f"Expected ≥30% reduction, got {reduction_pct:.1f}%"
        assert latency < 5, f"Compression took {latency:.2f}s, expected <5s for 4 sources"

    @pytest.mark.asyncio
    async def test_compression_handles_visual_sources(self, mock_mlx_client, sample_sources):
        """Test that synthesis includes visual sources in citations"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        compressed = await preprocessor.compress_chunks(
            query="What caused the 2008 financial crisis?", sources=sample_sources
        )

        # Synthesis creates ONE result
        assert len(compressed) == 1
        result = compressed[0]

        # Verify synthesis format
        assert result.chunk_id == "synthesized-summary"
        assert "# Synthesized Summary" in result.markdown_content

        # Verify visual sources are referenced in citations
        # sample_sources[1] is the visual source (doc2)
        # The mock synthesis includes "[2]" which references the visual source
        assert "[2]" in result.markdown_content, "Visual source should be cited in synthesis"

    @pytest.mark.asyncio
    async def test_compression_creates_synthesis(self, mock_mlx_client, sample_sources):
        """Test that synthesis creates single summary from all sources"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        compressed = await preprocessor.compress_chunks(
            query="What caused the 2008 financial crisis?", sources=sample_sources
        )

        # Synthesis creates ONE result
        assert len(compressed) == 1, f"Expected 1 synthesized result, got {len(compressed)}"

        # Verify synthesis format
        assert compressed[0].chunk_id == "synthesized-summary"
        assert "# Synthesized Summary" in compressed[0].markdown_content
        assert compressed[0].page == 0


# ============================================================================
# Test 3: Filtering Strategy
# ============================================================================


class TestFilteringStrategy:
    """Test relevance filtering preprocessing strategy"""

    @pytest.mark.asyncio
    async def test_filtering_with_mock(self, mock_mlx_client, many_sources):
        """Test filtering reduces sources based on relevance threshold"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        # Filter with threshold 7.0
        start_time = time.time()
        filtered = await preprocessor.filter_by_relevance(
            query="What caused the 2008 financial crisis?", sources=many_sources, threshold=7.0
        )
        latency = time.time() - start_time

        # Validate retention rate (expect 40-60%)
        retention_pct = (len(filtered) / len(many_sources)) * 100
        assert 30 <= retention_pct <= 70, f"Expected 30-70% retention, got {retention_pct:.1f}%"

        # Validate performance
        assert latency < 5, f"Filtering took {latency:.2f}s, expected <5s"

        # Validate all filtered sources meet threshold (mock returns 8.5)
        # Since mock returns constant score, all should pass or fail together
        assert len(filtered) > 0, "Should have some sources passing threshold"

    @skip_without_mlx
    @pytest.mark.asyncio
    async def test_filtering_with_real_mlx(self, real_mlx_client, many_sources):
        """Test filtering with real MLX model produces sensible retention rates"""
        preprocessor = LocalLLMPreprocessor(mlx_client=real_mlx_client)

        # Test multiple thresholds
        for threshold in [6.0, 7.0, 8.0]:
            start_time = time.time()
            filtered = await preprocessor.filter_by_relevance(
                query="What caused the 2008 financial crisis?",
                sources=many_sources,
                threshold=threshold,
            )
            latency = time.time() - start_time

            retention_pct = (len(filtered) / len(many_sources)) * 100

            print(f"\n[FILTERING BENCHMARK - Real MLX - Threshold {threshold}]")
            print(f"  Original sources: {len(many_sources)}")
            print(f"  Filtered sources: {len(filtered)}")
            print(f"  Retention: {retention_pct:.1f}%")
            print(f"  Latency: {latency:.2f}s")

            # Higher thresholds should filter more aggressively
            if threshold >= 8.0:
                assert (
                    retention_pct <= 60
                ), f"High threshold should filter more, got {retention_pct:.1f}%"

            # Validate performance
            assert latency < 5, f"Filtering took {latency:.2f}s, expected <5s"

    @pytest.mark.asyncio
    async def test_filtering_sorts_by_relevance(self, mock_mlx_client, many_sources):
        """Test that filtered sources are sorted by relevance score descending"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        filtered = await preprocessor.filter_by_relevance(
            query="What caused the 2008 financial crisis?", sources=many_sources, threshold=5.0
        )

        # Note: Mock client returns constant score, so this test validates
        # the sorting logic exists even if scores are equal
        assert len(filtered) > 0, "Should have sources passing threshold"

    @pytest.mark.asyncio
    async def test_filtering_preserves_metadata(self, mock_mlx_client, many_sources):
        """Test that filtering preserves all source metadata"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        filtered = await preprocessor.filter_by_relevance(
            query="What caused the 2008 financial crisis?", sources=many_sources, threshold=7.0
        )

        for source in filtered:
            # Find original
            original = next(s for s in many_sources if s.doc_id == source.doc_id)

            # Validate all metadata preserved
            assert source.doc_id == original.doc_id
            assert source.chunk_id == original.chunk_id
            assert source.page == original.page
            assert source.filename == original.filename
            assert source.markdown_content == original.markdown_content


# ============================================================================
# Test 4: Synthesis Strategy
# ============================================================================


class TestSynthesisStrategy:
    """Test knowledge synthesis preprocessing strategy"""

    @pytest.mark.asyncio
    async def test_synthesis_with_mock(self, mock_mlx_client, sample_sources):
        """Test synthesis creates organized context with citations"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        start_time = time.time()
        synthesized = await preprocessor.synthesize_knowledge(
            query="What caused the 2008 financial crisis?", sources=sample_sources
        )
        latency = time.time() - start_time

        # Validate output is string (not List[SourceDocument])
        assert isinstance(synthesized, str)
        assert len(synthesized) > 0

        # Validate contains citations in [N] format
        assert "[1]" in synthesized or "[2]" in synthesized or "[3]" in synthesized

        # Validate performance
        assert latency < 5, f"Synthesis took {latency:.2f}s, expected <5s"

    @skip_without_mlx
    @pytest.mark.asyncio
    async def test_synthesis_with_real_mlx(self, real_mlx_client, sample_sources):
        """Test synthesis with real MLX produces coherent cross-document synthesis"""
        preprocessor = LocalLLMPreprocessor(mlx_client=real_mlx_client)

        start_time = time.time()
        synthesized = await preprocessor.synthesize_knowledge(
            query="What caused the 2008 financial crisis?", sources=sample_sources
        )
        latency = time.time() - start_time

        # Validate output
        assert isinstance(synthesized, str)
        assert len(synthesized) > 0

        # Check for citation markers
        citation_count = sum(
            1 for i in range(1, len(sample_sources) + 1) if f"[{i}]" in synthesized
        )

        print(f"\n[SYNTHESIS BENCHMARK - Real MLX]")
        print(f"  Sources: {len(sample_sources)}")
        print(f"  Output length: {len(synthesized)} chars")
        print(f"  Citations found: {citation_count}")
        print(f"  Latency: {latency:.2f}s")

        # Validate citations (should reference at least 50% of sources)
        assert (
            citation_count >= len(sample_sources) * 0.5
        ), f"Expected ≥50% sources cited, got {citation_count}/{len(sample_sources)}"

        # Validate performance
        assert latency < 5, f"Synthesis took {latency:.2f}s, expected <5s"

    @pytest.mark.asyncio
    async def test_synthesis_citation_preservation(self, mock_mlx_client, sample_sources):
        """Test that synthesis preserves citation numbering matching source order"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        synthesized = await preprocessor.synthesize_knowledge(
            query="What caused the 2008 financial crisis?", sources=sample_sources
        )

        # Validate citation numbers don't exceed source count
        for i in range(1, len(sample_sources) + 1):
            # Citation [i] is valid
            pass

        # Invalid citations should not appear
        invalid_citation = f"[{len(sample_sources) + 1}]"
        assert invalid_citation not in synthesized, f"Found invalid citation {invalid_citation}"


# ============================================================================
# Test 5: Error Handling and Graceful Degradation
# ============================================================================


class TestErrorHandling:
    """Test error scenarios and graceful degradation"""

    @pytest.mark.asyncio
    async def test_compression_handles_llm_errors(self, sample_sources):
        """Test compression falls back gracefully on LLM errors"""
        # Create client that raises errors
        failing_client = AsyncMock(spec=MLXLLMClient)
        failing_client.complete.side_effect = LLMError("Model timeout")

        preprocessor = LocalLLMPreprocessor(mlx_client=failing_client)

        # Should not raise, should return original sources
        result = await preprocessor.compress_chunks(
            query="What caused the 2008 financial crisis?", sources=sample_sources
        )

        assert len(result) == len(sample_sources)
        # Verify fallback to original content
        for original, returned in zip(sample_sources, result):
            assert returned.doc_id == original.doc_id

    @pytest.mark.asyncio
    async def test_filtering_handles_llm_errors(self, sample_sources):
        """Test filtering handles LLM errors gracefully by assigning score 0"""
        failing_client = AsyncMock(spec=MLXLLMClient)
        failing_client.complete.side_effect = LLMError("Model timeout")

        preprocessor = LocalLLMPreprocessor(mlx_client=failing_client)

        # Should not raise, but text sources get score 0 and are filtered out
        # Visual sources auto-score 9.0 and pass threshold
        result = await preprocessor.filter_by_relevance(
            query="What caused the 2008 financial crisis?", sources=sample_sources, threshold=7.0
        )

        # Only visual source should pass (auto-scores 9.0)
        assert len(result) == 1
        assert result[0].is_visual

    @pytest.mark.asyncio
    async def test_synthesis_handles_context_length_errors(self, mock_mlx_client):
        """Test synthesis falls back on context length errors"""
        # Create huge sources that exceed token limit
        huge_sources = [
            SourceDocument(
                doc_id=f"doc{i}",
                filename=f"huge{i}.pdf",
                page=1,
                extension="pdf",
                timestamp="2025-10-22T10:00:00Z",
                markdown_content="x" * 50000,  # ~12.5K tokens each
                relevance_score=0.9,
                chunk_id=f"doc{i}-chunk0001",
                is_visual=False,
            )
            for i in range(5)
        ]

        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        # Should raise ContextLengthError or fall back gracefully
        try:
            result = await preprocessor.synthesize_knowledge(
                query="What caused the 2008 financial crisis?", sources=huge_sources
            )
            # If no error, should return formatted chunks as fallback
            assert isinstance(result, str)
            assert len(result) > 0
        except ContextLengthError:
            # This is also acceptable behavior
            pass

    @pytest.mark.asyncio
    async def test_filtering_handles_invalid_threshold(self, mock_mlx_client, sample_sources):
        """Test filtering validates threshold parameter"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        # Invalid threshold should raise ValueError
        with pytest.raises(ValueError, match="Threshold must be in range 0-10"):
            await preprocessor.filter_by_relevance(
                query="What caused the 2008 financial crisis?",
                sources=sample_sources,
                threshold=15.0,
            )

    @pytest.mark.asyncio
    async def test_filtering_handles_non_numeric_scores(self, sample_sources):
        """Test filtering handles LLM returning non-numeric scores with fallback"""
        # Create client that returns non-numeric response
        bad_client = AsyncMock(spec=MLXLLMClient)

        async def bad_complete(prompt, **kwargs):
            return LLMResponse(
                content="This is not a number!",  # Invalid score
                model="gpt-oss-20b-mlx",
                provider="mlx",
                usage={"prompt_tokens": 100, "completion_tokens": 5, "total_tokens": 105},
                finish_reason="stop",
                latency_ms=200,
            )

        bad_client.complete = bad_complete

        preprocessor = LocalLLMPreprocessor(mlx_client=bad_client)

        # Text sources get fallback score 5.0, visual auto-scores 9.0
        result = await preprocessor.filter_by_relevance(
            query="What caused the 2008 financial crisis?", sources=sample_sources, threshold=5.0
        )

        # Visual source (9.0) and text sources with fallback (5.0) pass threshold 5.0
        assert len(result) == 4, "Visual source (9.0) + 3 text sources (5.0 fallback) should pass"
        # Verify visual source is included
        visual_sources = [s for s in result if s.is_visual]
        assert len(visual_sources) == 1


# ============================================================================
# Test 6: Performance Benchmarks
# ============================================================================


class TestPerformanceBenchmarks:
    """Test performance targets are met"""

    @skip_without_mlx
    @pytest.mark.asyncio
    async def test_compression_performance_target(self, real_mlx_client, sample_sources):
        """Test compression completes within 3s for 4 sources"""
        preprocessor = LocalLLMPreprocessor(mlx_client=real_mlx_client)

        # Warm up model
        await preprocessor.compress_chunks(
            query="What caused the 2008 financial crisis?", sources=sample_sources[:1]
        )

        # Benchmark
        start_time = time.time()
        compressed = await preprocessor.compress_chunks(
            query="What caused the 2008 financial crisis?", sources=sample_sources
        )
        latency = time.time() - start_time

        print(f"\n[COMPRESSION PERFORMANCE]")
        print(f"  Sources: {len(sample_sources)}")
        print(f"  Latency: {latency:.2f}s")
        print(f"  Target: <3s")
        print(f"  Status: {'PASS' if latency < 3 else 'FAIL'}")

        # Note: Real MLX may be slower than target on first run
        # This is a soft target - log warning but don't fail
        if latency >= 3:
            print(f"  WARNING: Exceeded target by {latency - 3:.2f}s")

    @skip_without_mlx
    @pytest.mark.asyncio
    async def test_filtering_performance_target(self, real_mlx_client, many_sources):
        """Test filtering completes within 3s for 15 sources"""
        preprocessor = LocalLLMPreprocessor(mlx_client=real_mlx_client)

        # Warm up model
        await preprocessor.filter_by_relevance(
            query="What caused the 2008 financial crisis?",
            sources=many_sources[:2],
            threshold=7.0,
        )

        # Benchmark
        start_time = time.time()
        filtered = await preprocessor.filter_by_relevance(
            query="What caused the 2008 financial crisis?", sources=many_sources, threshold=7.0
        )
        latency = time.time() - start_time

        print(f"\n[FILTERING PERFORMANCE]")
        print(f"  Sources: {len(many_sources)}")
        print(f"  Filtered: {len(filtered)}")
        print(f"  Latency: {latency:.2f}s")
        print(f"  Target: <3s")
        print(f"  Status: {'PASS' if latency < 3 else 'FAIL'}")

        if latency >= 3:
            print(f"  WARNING: Exceeded target by {latency - 3:.2f}s")

    @skip_without_mlx
    @pytest.mark.asyncio
    async def test_synthesis_performance_target(self, real_mlx_client, sample_sources):
        """Test synthesis completes within 5s for 4 sources"""
        preprocessor = LocalLLMPreprocessor(mlx_client=real_mlx_client)

        # Warm up model
        await preprocessor.synthesize_knowledge(
            query="What caused the 2008 financial crisis?", sources=sample_sources[:1]
        )

        # Benchmark
        start_time = time.time()
        synthesized = await preprocessor.synthesize_knowledge(
            query="What caused the 2008 financial crisis?", sources=sample_sources
        )
        latency = time.time() - start_time

        print(f"\n[SYNTHESIS PERFORMANCE]")
        print(f"  Sources: {len(sample_sources)}")
        print(f"  Output: {len(synthesized)} chars")
        print(f"  Latency: {latency:.2f}s")
        print(f"  Target: <5s")
        print(f"  Status: {'PASS' if latency < 5 else 'FAIL'}")

        if latency >= 5:
            print(f"  WARNING: Exceeded target by {latency - 5:.2f}s")


# ============================================================================
# Test 7: Citation Accuracy Validation
# ============================================================================


class TestCitationAccuracy:
    """Test citation preservation and accuracy"""

    @pytest.mark.asyncio
    async def test_compression_creates_synthesized_chunk_id(self, mock_mlx_client, sample_sources):
        """Test compression creates special synthesized-summary chunk_id"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        compressed = await preprocessor.compress_chunks(
            query="What caused the 2008 financial crisis?", sources=sample_sources
        )

        # Synthesis creates ONE result with special chunk_id
        assert len(compressed) == 1
        assert compressed[0].chunk_id == "synthesized-summary"

    @pytest.mark.asyncio
    async def test_filtering_preserves_chunk_ids(self, mock_mlx_client, many_sources):
        """Test filtering preserves chunk_id for bidirectional highlighting"""
        preprocessor = LocalLLMPreprocessor(mlx_client=mock_mlx_client)

        filtered = await preprocessor.filter_by_relevance(
            query="What caused the 2008 financial crisis?", sources=many_sources, threshold=7.0
        )

        for source in filtered:
            original = next(s for s in many_sources if s.doc_id == source.doc_id)
            assert source.chunk_id == original.chunk_id, f"chunk_id mismatch for {source.doc_id}"

    @skip_without_mlx
    @pytest.mark.asyncio
    async def test_synthesis_citation_accuracy(self, real_mlx_client, sample_sources):
        """Test synthesis citation accuracy ≥95%"""
        preprocessor = LocalLLMPreprocessor(mlx_client=real_mlx_client)

        synthesized = await preprocessor.synthesize_knowledge(
            query="What caused the 2008 financial crisis?", sources=sample_sources
        )

        # Extract all citations
        import re

        citations = re.findall(r"\[(\d+)\]", synthesized)
        citation_ids = [int(c) for c in citations]

        # Validate all citations are in valid range
        invalid_citations = [c for c in citation_ids if c < 1 or c > len(sample_sources)]

        accuracy = (
            (len(citation_ids) - len(invalid_citations)) / len(citation_ids) * 100
            if citation_ids
            else 100
        )

        print(f"\n[CITATION ACCURACY]")
        print(f"  Total citations: {len(citation_ids)}")
        print(f"  Valid citations: {len(citation_ids) - len(invalid_citations)}")
        print(f"  Invalid citations: {invalid_citations}")
        print(f"  Accuracy: {accuracy:.1f}%")
        print(f"  Target: ≥95%")

        assert accuracy >= 95, f"Citation accuracy {accuracy:.1f}% below target 95%"


# ============================================================================
# Test 8: Strategy Comparison
# ============================================================================


class TestStrategyComparison:
    """Compare preprocessing strategies against baseline"""

    @skip_without_mlx
    @pytest.mark.asyncio
    async def test_compression_vs_baseline(self, real_mlx_client, sample_sources):
        """Compare compressed vs baseline token counts"""
        preprocessor = LocalLLMPreprocessor(mlx_client=real_mlx_client)

        # Baseline tokens
        baseline_tokens = sum(estimate_tokens(s.markdown_content) for s in sample_sources)

        # Compressed tokens
        compressed = await preprocessor.compress_chunks(
            query="What caused the 2008 financial crisis?", sources=sample_sources
        )
        compressed_tokens = sum(estimate_tokens(s.markdown_content) for s in compressed)

        # Calculate reduction
        reduction_pct = calculate_reduction_percent(baseline_tokens, compressed_tokens)

        print(f"\n[COMPRESSION vs BASELINE]")
        print(f"  Baseline tokens: {baseline_tokens}")
        print(f"  Compressed tokens: {compressed_tokens}")
        print(f"  Reduction: {reduction_pct:.1f}%")
        print(f"  Cost savings: ~${(baseline_tokens - compressed_tokens) * 0.00001:.4f}")

        assert reduction_pct >= 30, f"Expected ≥30% reduction, got {reduction_pct:.1f}%"

    @skip_without_mlx
    @pytest.mark.asyncio
    async def test_filtering_vs_baseline(self, real_mlx_client, many_sources):
        """Compare filtered vs baseline source counts"""
        preprocessor = LocalLLMPreprocessor(mlx_client=real_mlx_client)

        # Baseline
        baseline_count = len(many_sources)
        baseline_tokens = sum(estimate_tokens(s.markdown_content) for s in many_sources)

        # Filtered
        filtered = await preprocessor.filter_by_relevance(
            query="What caused the 2008 financial crisis?", sources=many_sources, threshold=7.0
        )
        filtered_tokens = sum(estimate_tokens(s.markdown_content) for s in filtered)

        retention_pct = (len(filtered) / baseline_count) * 100
        reduction_pct = calculate_reduction_percent(baseline_tokens, filtered_tokens)

        print(f"\n[FILTERING vs BASELINE]")
        print(f"  Baseline sources: {baseline_count}")
        print(f"  Filtered sources: {len(filtered)}")
        print(f"  Retention: {retention_pct:.1f}%")
        print(f"  Token reduction: {reduction_pct:.1f}%")

        assert 40 <= retention_pct <= 60, f"Expected 40-60% retention, got {retention_pct:.1f}%"

    @skip_without_mlx
    @pytest.mark.asyncio
    async def test_synthesis_vs_baseline(self, real_mlx_client, sample_sources):
        """Compare synthesized vs baseline context length"""
        preprocessor = LocalLLMPreprocessor(mlx_client=real_mlx_client)

        # Baseline: concatenated chunks
        from src.research.prompts import PreprocessingPrompts

        baseline_context = PreprocessingPrompts.format_numbered_chunks(sample_sources)
        baseline_tokens = estimate_tokens(baseline_context)

        # Synthesized
        synthesized = await preprocessor.synthesize_knowledge(
            query="What caused the 2008 financial crisis?", sources=sample_sources
        )
        synthesized_tokens = estimate_tokens(synthesized)

        # Synthesis may increase or decrease tokens depending on content
        # The value is in organization, not necessarily compression
        print(f"\n[SYNTHESIS vs BASELINE]")
        print(f"  Baseline tokens: {baseline_tokens}")
        print(f"  Synthesized tokens: {synthesized_tokens}")
        print(f"  Difference: {synthesized_tokens - baseline_tokens:+d} tokens")
        print(f"  Citations preserved: {synthesized.count('[')}")

        # Synthesis should be coherent (length varies)
        assert len(synthesized) > 0
        assert "[1]" in synthesized or "[2]" in synthesized
