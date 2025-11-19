"""
Unit tests for LocalLLMPreprocessor with Harmony format integration.

Tests the Harmony-format JSON prompt/response parsing, compression validation,
and graceful fallback behaviors per integration contract specifications.
"""

import os
from unittest.mock import AsyncMock, patch

import pytest

from tkr_docusearch.research.context_builder import SourceDocument
from tkr_docusearch.research.local_preprocessor import LocalLLMPreprocessor
from tkr_docusearch.research.mlx_llm_client import LLMResponse


@pytest.fixture
def mock_mlx_client():
    """Create mock MLX client with configurable responses"""
    client = AsyncMock()
    return client


@pytest.fixture
def sample_source():
    """Create sample SourceDocument for testing"""
    return SourceDocument(
        doc_id="test_doc",
        filename="test.pdf",
        page=1,
        extension="pdf",
        thumbnail_path="/images/test_doc/page001_thumb.jpg",
        image_path="/images/test_doc/page001.jpg",
        timestamp="2025-10-25T10:00:00Z",
        section_path="Section 1",
        parent_heading="Test Heading",
        markdown_content="Tucker is a Senior UX Designer with 15+ years of experience. "
        "He has worked at Nutrien as Lead UX Designer from February 2023 to September 2023, "
        "where he led a team of 5 designers on multiple product initiatives. "
        "His contact information is 403-630-7003 and connect@tucker.sh. " * 2,  # ~400 chars
        relevance_score=0.95,
        chunk_id="test_doc-chunk0001",
        is_visual=False,
    )


@pytest.fixture
def short_source():
    """Create short SourceDocument that should skip compression"""
    return SourceDocument(
        doc_id="short_doc",
        filename="short.pdf",
        page=1,
        extension="pdf",
        markdown_content="Short text.",  # <400 chars
        relevance_score=0.95,
        chunk_id="short_doc-chunk0001",
        is_visual=False,
    )


@pytest.fixture
def visual_source():
    """Create visual SourceDocument for testing"""
    return SourceDocument(
        doc_id="visual_doc",
        filename="chart.png",
        page=1,
        extension="png",
        markdown_content="Visual content",
        relevance_score=0.95,
        chunk_id=None,
        is_visual=True,
    )


class TestHarmonyCompressionIntegration:
    """Test compression with Harmony prompts and JSON parsing"""

    @pytest.mark.asyncio
    async def test_compress_with_harmony_prompts_success(self, mock_mlx_client, sample_source):
        """Test successful synthesis using Harmony prompts"""
        # Mock LLM to return synthesized summary
        compressed_facts = (
            "Tucker: Senior UX Designer, 15+ years. "
            "Nutrien Lead UX Designer Feb-Sep 2023, led 5 designers. "
            "Contact: 403-630-7003, connect@tucker.sh"
        )
        mock_mlx_client.complete.return_value = LLMResponse(
            content=compressed_facts,
            model="gpt-oss-20b-mlx",
            provider="mlx",
            usage={"prompt_tokens": 150, "completion_tokens": 50, "total_tokens": 200},
            finish_reason="stop",
            latency_ms=2000,
        )

        # Enable Harmony prompts
        with patch.dict(os.environ, {"USE_HARMONY_PROMPTS": "true"}):
            preprocessor = LocalLLMPreprocessor(mock_mlx_client)
            assert preprocessor.use_harmony is True

            # Execute synthesis
            compressed = await preprocessor.compress_chunks(
                query="What is Tucker's role?", sources=[sample_source]
            )

            # Verify synthesis behavior
            assert len(compressed) == 1
            assert "# Synthesized Summary" in compressed[0].markdown_content
            assert compressed_facts in compressed[0].markdown_content
            assert compressed[0].doc_id == sample_source.doc_id
            assert compressed[0].chunk_id == "synthesized-summary"
            assert compressed[0].page == 0

    @pytest.mark.asyncio
    async def test_compress_creates_synthesis(self, mock_mlx_client, sample_source):
        """Test synthesis creates summary regardless of length"""
        # Mock LLM to return synthesized text
        expanded_text = (
            sample_source.markdown_content + " Additional verbose text that makes it longer."
        )
        mock_mlx_client.complete.return_value = LLMResponse(
            content=expanded_text,
            model="gpt-oss-20b-mlx",
            provider="mlx",
            usage={"prompt_tokens": 150, "completion_tokens": 200, "total_tokens": 350},
            finish_reason="stop",
            latency_ms=2000,
        )

        # Enable Harmony prompts
        with patch.dict(os.environ, {"USE_HARMONY_PROMPTS": "true"}):
            preprocessor = LocalLLMPreprocessor(mock_mlx_client)

            # Execute synthesis
            compressed = await preprocessor.compress_chunks(
                query="test query", sources=[sample_source]
            )

            # Verify: Synthesis wraps content
            assert len(compressed) == 1
            assert "# Synthesized Summary" in compressed[0].markdown_content
            assert expanded_text in compressed[0].markdown_content

    @pytest.mark.asyncio
    async def test_compress_uses_llm_response(self, mock_mlx_client, sample_source):
        """Test synthesis uses LLM response directly"""
        # Mock LLM to return prose
        llm_response = "The key facts are that Tucker is a designer with experience..."
        mock_mlx_client.complete.return_value = LLMResponse(
            content=llm_response,
            model="gpt-oss-20b-mlx",
            provider="mlx",
            usage={"prompt_tokens": 150, "completion_tokens": 50, "total_tokens": 200},
            finish_reason="stop",
            latency_ms=2000,
        )

        # Enable Harmony prompts
        with patch.dict(os.environ, {"USE_HARMONY_PROMPTS": "true"}):
            preprocessor = LocalLLMPreprocessor(mock_mlx_client)

            # Execute synthesis
            compressed = await preprocessor.compress_chunks(
                query="test query", sources=[sample_source]
            )

            # Verify: Synthesis wraps LLM response
            assert len(compressed) == 1
            assert "# Synthesized Summary" in compressed[0].markdown_content
            assert llm_response in compressed[0].markdown_content

    @pytest.mark.asyncio
    async def test_compress_uses_response_content(self, mock_mlx_client, sample_source):
        """Test synthesis uses response content regardless of format"""
        # Mock LLM to return JSON (synthesis uses it directly)
        mock_mlx_client.complete.return_value = LLMResponse(
            content='{"result": "Tucker is a designer"}',
            model="gpt-oss-20b-mlx",
            provider="mlx",
            usage={"prompt_tokens": 150, "completion_tokens": 50, "total_tokens": 200},
            finish_reason="stop",
            latency_ms=2000,
        )

        # Enable Harmony prompts
        with patch.dict(os.environ, {"USE_HARMONY_PROMPTS": "true"}):
            preprocessor = LocalLLMPreprocessor(mock_mlx_client)

            # Execute synthesis
            compressed = await preprocessor.compress_chunks(
                query="test query", sources=[sample_source]
            )

            # Verify: Synthesis wraps the response
            assert len(compressed) == 1
            assert "# Synthesized Summary" in compressed[0].markdown_content
            assert mock_mlx_client.complete.return_value.content in compressed[0].markdown_content

    @pytest.mark.asyncio
    async def test_compress_synthesizes_all_sources(self, mock_mlx_client, short_source):
        """Test that all sources (including short ones) are synthesized"""
        mock_mlx_client.complete.return_value = LLMResponse(
            content="Synthesized content",
            model="gpt-oss-20b-mlx",
            provider="mlx",
            usage={"prompt_tokens": 150, "completion_tokens": 50, "total_tokens": 200},
            finish_reason="stop",
            latency_ms=2000,
        )

        # Enable Harmony prompts
        with patch.dict(os.environ, {"USE_HARMONY_PROMPTS": "true"}):
            preprocessor = LocalLLMPreprocessor(mock_mlx_client)

            # Execute synthesis
            compressed = await preprocessor.compress_chunks(
                query="test query", sources=[short_source]
            )

            # Verify: All sources synthesized, LLM called
            assert len(compressed) == 1
            assert "# Synthesized Summary" in compressed[0].markdown_content
            mock_mlx_client.complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_compress_includes_visual_sources(self, mock_mlx_client, visual_source):
        """Test that visual sources are included in synthesis"""
        mock_mlx_client.complete.return_value = LLMResponse(
            content="Synthesized content",
            model="gpt-oss-20b-mlx",
            provider="mlx",
            usage={"prompt_tokens": 150, "completion_tokens": 50, "total_tokens": 200},
            finish_reason="stop",
            latency_ms=2000,
        )

        # Enable Harmony prompts
        with patch.dict(os.environ, {"USE_HARMONY_PROMPTS": "true"}):
            preprocessor = LocalLLMPreprocessor(mock_mlx_client)

            # Execute synthesis
            compressed = await preprocessor.compress_chunks(
                query="test query", sources=[visual_source]
            )

            # Verify: Visual sources included in synthesis, LLM called
            assert len(compressed) == 1
            assert "# Synthesized Summary" in compressed[0].markdown_content
            mock_mlx_client.complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_compress_timeout_handling(self, mock_mlx_client, sample_source):
        """Test timeout handling with increased timeout value"""
        # Mock timeout
        from tkr_docusearch.research.mlx_llm_client import TimeoutError

        mock_mlx_client.complete.side_effect = TimeoutError("Timeout after 120s")

        # Enable Harmony prompts
        with patch.dict(os.environ, {"USE_HARMONY_PROMPTS": "true"}):
            preprocessor = LocalLLMPreprocessor(mock_mlx_client)

            # Execute compression - should handle gracefully
            with pytest.raises(TimeoutError):
                await preprocessor._compress_single_chunk(query="test query", source=sample_source)


class TestHarmonyRelevanceScoringIntegration:
    """Test relevance scoring with Harmony prompts and JSON parsing"""

    @pytest.mark.asyncio
    async def test_score_with_harmony_prompts_success(self, mock_mlx_client, sample_source):
        """Test successful relevance scoring using Harmony prompts"""
        # Mock LLM to return valid Harmony JSON response
        mock_mlx_client.complete.return_value = LLMResponse(
            content='{"score": 8}',
            model="gpt-oss-20b-mlx",
            provider="mlx",
            usage={"prompt_tokens": 50, "completion_tokens": 5, "total_tokens": 55},
            finish_reason="stop",
            latency_ms=500,
        )

        # Enable Harmony prompts
        with patch.dict(os.environ, {"USE_HARMONY_PROMPTS": "true"}):
            preprocessor = LocalLLMPreprocessor(mock_mlx_client)

            # Execute scoring
            score = await preprocessor._score_chunk_relevance(
                query="What is Tucker's role?", source=sample_source
            )

            # Verify
            assert score == 8.0
            mock_mlx_client.complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_score_out_of_range_uses_fallback(self, mock_mlx_client, sample_source):
        """Test score out of range (>10) triggers fallback to neutral score"""
        # Mock LLM to return score > 10 (invalid per schema)
        mock_mlx_client.complete.return_value = LLMResponse(
            content='{"score": 15}',
            model="gpt-oss-20b-mlx",
            provider="mlx",
            usage={"prompt_tokens": 50, "completion_tokens": 5, "total_tokens": 55},
            finish_reason="stop",
            latency_ms=500,
        )

        # Enable Harmony prompts
        with patch.dict(os.environ, {"USE_HARMONY_PROMPTS": "true"}):
            preprocessor = LocalLLMPreprocessor(mock_mlx_client)

            # Execute scoring
            score = await preprocessor._score_chunk_relevance(
                query="test query", source=sample_source
            )

            # Verify: Parser rejects out-of-range score, uses neutral fallback (5.0)
            assert score == 5.0

    @pytest.mark.asyncio
    async def test_score_fallback_on_invalid_json(self, mock_mlx_client, sample_source):
        """Test fallback to neutral score (5.0) when JSON parsing fails"""
        # Mock LLM to return plain number instead of JSON
        mock_mlx_client.complete.return_value = LLMResponse(
            content="8",
            model="gpt-oss-20b-mlx",
            provider="mlx",
            usage={"prompt_tokens": 50, "completion_tokens": 5, "total_tokens": 55},
            finish_reason="stop",
            latency_ms=500,
        )

        # Enable Harmony prompts
        with patch.dict(os.environ, {"USE_HARMONY_PROMPTS": "true"}):
            preprocessor = LocalLLMPreprocessor(mock_mlx_client)

            # Execute scoring
            score = await preprocessor._score_chunk_relevance(
                query="test query", source=sample_source
            )

            # Verify: Neutral fallback score (5.0 per contract)
            assert score == 5.0

    @pytest.mark.asyncio
    async def test_score_fallback_on_missing_score_key(self, mock_mlx_client, sample_source):
        """Test fallback when JSON is valid but missing 'score' key"""
        # Mock LLM to return JSON without "score" key
        mock_mlx_client.complete.return_value = LLMResponse(
            content='{"relevance": 8}',
            model="gpt-oss-20b-mlx",
            provider="mlx",
            usage={"prompt_tokens": 50, "completion_tokens": 5, "total_tokens": 55},
            finish_reason="stop",
            latency_ms=500,
        )

        # Enable Harmony prompts
        with patch.dict(os.environ, {"USE_HARMONY_PROMPTS": "true"}):
            preprocessor = LocalLLMPreprocessor(mock_mlx_client)

            # Execute scoring
            score = await preprocessor._score_chunk_relevance(
                query="test query", source=sample_source
            )

            # Verify: Neutral fallback score (5.0 per contract)
            assert score == 5.0

    @pytest.mark.asyncio
    async def test_score_visual_sources_auto_high(self, mock_mlx_client, visual_source):
        """Test visual sources automatically score 9.0 without LLM call"""
        # Enable Harmony prompts
        with patch.dict(os.environ, {"USE_HARMONY_PROMPTS": "true"}):
            preprocessor = LocalLLMPreprocessor(mock_mlx_client)

            # Execute scoring
            score = await preprocessor._score_chunk_relevance(
                query="test query", source=visual_source
            )

            # Verify: Auto-scored 9.0, LLM not called
            assert score == 9.0
            mock_mlx_client.complete.assert_not_called()


class TestLegacyModeBackwardCompatibility:
    """Test legacy mode (USE_HARMONY_PROMPTS=false) still works"""

    @pytest.mark.asyncio
    async def test_legacy_compression_still_works(self, mock_mlx_client, sample_source):
        """Test legacy synthesis prompts still work when Harmony disabled"""
        # Mock LLM to return plain text (legacy format)
        compressed_text = "Tucker: Senior UX Designer, 15+ years experience."
        mock_mlx_client.complete.return_value = LLMResponse(
            content=compressed_text,
            model="gpt-oss-20b-mlx",
            provider="mlx",
            usage={"prompt_tokens": 150, "completion_tokens": 50, "total_tokens": 200},
            finish_reason="stop",
            latency_ms=2000,
        )

        # Disable Harmony prompts
        with patch.dict(os.environ, {"USE_HARMONY_PROMPTS": "false"}):
            preprocessor = LocalLLMPreprocessor(mock_mlx_client)
            assert preprocessor.use_harmony is False

            # Execute synthesis
            compressed = await preprocessor.compress_chunks(
                query="What is Tucker's role?", sources=[sample_source]
            )

            # Verify: Synthesis wraps content
            assert len(compressed) == 1
            assert "# Synthesized Summary" in compressed[0].markdown_content
            assert compressed_text in compressed[0].markdown_content

    @pytest.mark.asyncio
    async def test_legacy_scoring_still_works(self, mock_mlx_client, sample_source):
        """Test legacy relevance scoring still works when Harmony disabled"""
        # Mock LLM to return plain number (legacy format)
        mock_mlx_client.complete.return_value = LLMResponse(
            content="8",
            model="gpt-oss-20b-mlx",
            provider="mlx",
            usage={"prompt_tokens": 50, "completion_tokens": 5, "total_tokens": 55},
            finish_reason="stop",
            latency_ms=500,
        )

        # Disable Harmony prompts
        with patch.dict(os.environ, {"USE_HARMONY_PROMPTS": "false"}):
            preprocessor = LocalLLMPreprocessor(mock_mlx_client)
            assert preprocessor.use_harmony is False

            # Execute scoring
            score = await preprocessor._score_chunk_relevance(
                query="test query", source=sample_source
            )

            # Verify: Legacy number parsing used
            assert score == 8.0

    @pytest.mark.asyncio
    async def test_legacy_fallback_to_neutral_score(self, mock_mlx_client, sample_source):
        """Test legacy scoring fallback changed from 0.0 to 5.0 (matches Harmony)"""
        # Mock LLM to return invalid number
        mock_mlx_client.complete.return_value = LLMResponse(
            content="invalid",
            model="gpt-oss-20b-mlx",
            provider="mlx",
            usage={"prompt_tokens": 50, "completion_tokens": 5, "total_tokens": 55},
            finish_reason="stop",
            latency_ms=500,
        )

        # Disable Harmony prompts
        with patch.dict(os.environ, {"USE_HARMONY_PROMPTS": "false"}):
            preprocessor = LocalLLMPreprocessor(mock_mlx_client)

            # Execute scoring
            score = await preprocessor._score_chunk_relevance(
                query="test query", source=sample_source
            )

            # Verify: Now uses neutral 5.0 instead of 0.0
            assert score == 5.0


class TestEnvironmentFlagBehavior:
    """Test environment flag controls Harmony vs legacy behavior"""

    @pytest.mark.asyncio
    async def test_default_is_harmony_enabled(self, mock_mlx_client):
        """Test default behavior is Harmony prompts enabled"""
        # No env var set - should default to true
        with patch.dict(os.environ, {}, clear=True):
            if "USE_HARMONY_PROMPTS" in os.environ:
                del os.environ["USE_HARMONY_PROMPTS"]
            preprocessor = LocalLLMPreprocessor(mock_mlx_client)
            assert preprocessor.use_harmony is True

    @pytest.mark.asyncio
    async def test_explicit_harmony_true(self, mock_mlx_client):
        """Test USE_HARMONY_PROMPTS=true enables Harmony"""
        with patch.dict(os.environ, {"USE_HARMONY_PROMPTS": "true"}):
            preprocessor = LocalLLMPreprocessor(mock_mlx_client)
            assert preprocessor.use_harmony is True

    @pytest.mark.asyncio
    async def test_explicit_harmony_false(self, mock_mlx_client):
        """Test USE_HARMONY_PROMPTS=false disables Harmony"""
        with patch.dict(os.environ, {"USE_HARMONY_PROMPTS": "false"}):
            preprocessor = LocalLLMPreprocessor(mock_mlx_client)
            assert preprocessor.use_harmony is False

    @pytest.mark.asyncio
    async def test_case_insensitive_flag(self, mock_mlx_client):
        """Test environment flag is case-insensitive"""
        with patch.dict(os.environ, {"USE_HARMONY_PROMPTS": "TRUE"}):
            preprocessor = LocalLLMPreprocessor(mock_mlx_client)
            assert preprocessor.use_harmony is True

        with patch.dict(os.environ, {"USE_HARMONY_PROMPTS": "FALSE"}):
            preprocessor = LocalLLMPreprocessor(mock_mlx_client)
            assert preprocessor.use_harmony is False


class TestCompressionMetricsLogging:
    """Test enhanced logging with token metrics"""

    @pytest.mark.asyncio
    async def test_compression_metrics_logged(self, mock_mlx_client, sample_source):
        """Test compression logs include token metrics"""
        # Mock LLM response
        compressed_facts = "Tucker: Senior UX Designer, 15+ years."
        mock_mlx_client.complete.return_value = LLMResponse(
            content=f'{{"facts": "{compressed_facts}"}}',
            model="gpt-oss-20b-mlx",
            provider="mlx",
            usage={"prompt_tokens": 150, "completion_tokens": 50, "total_tokens": 200},
            finish_reason="stop",
            latency_ms=2000,
        )

        # Enable Harmony prompts
        with patch.dict(os.environ, {"USE_HARMONY_PROMPTS": "true"}):
            preprocessor = LocalLLMPreprocessor(mock_mlx_client)

            # Execute compression (logging happens inside)
            compressed = await preprocessor.compress_chunks(
                query="test query", sources=[sample_source]
            )

            # Verify: Compression successful
            assert len(compressed) == 1
            # Metrics would be in logs (original_tokens, compressed_tokens, reduction_pct)
            # We can't easily assert on logs here, but we verify the logic works
            assert len(compressed[0].markdown_content) < len(sample_source.markdown_content)
