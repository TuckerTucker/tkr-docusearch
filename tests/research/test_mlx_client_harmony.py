"""
Unit tests for MLX LLM Client Harmony enhancements.

Tests the MLXLLMClient's support for reasoning_effort parameter and
Harmony-formatted prompt integration. Validates backward compatibility
and new Harmony features.
"""

from unittest.mock import Mock, patch

import pytest

from src.research.mlx_llm_client import (
    LLMResponse,
    MLXLLMClient,
)


@pytest.fixture
def mock_mlx_lm():
    """Mock mlx_lm module - patch at import time"""
    # Mock model and tokenizer
    mock_model = Mock()
    mock_tokenizer = Mock()
    mock_tokenizer.encode = Mock(side_effect=lambda text: [0] * (len(text) // 4))

    # Create mock module
    mock_mlx = Mock()
    mock_mlx.load = Mock(return_value=(mock_model, mock_tokenizer))
    mock_mlx.generate = Mock(return_value='{"facts": "Compressed text here"}')

    return mock_mlx


@pytest.fixture
def mock_model_path(tmp_path):
    """Create temporary model path"""
    model_dir = tmp_path / "test-model"
    model_dir.mkdir()
    # Create a dummy file to make path exist
    (model_dir / "config.json").write_text("{}")
    return str(model_dir)


@pytest.fixture
async def mlx_client(mock_mlx_lm, mock_model_path):
    """Create MLX client with mocked dependencies"""
    # Patch the import statement inside __init__
    with patch.dict("sys.modules", {"mlx_lm": mock_mlx_lm}):
        client = MLXLLMClient(
            model_path=mock_model_path,
            max_tokens=100,
            temperature=0.3,
            reasoning_effort="low",
        )
        yield client
        # Cleanup
        if hasattr(client, "_executor"):
            client._executor.shutdown(wait=True)


class TestMLXClientReasoningEffortInitialization:
    """Test reasoning_effort parameter in __init__"""

    def test_default_reasoning_effort(self, mock_mlx_lm, mock_model_path):
        """Test default reasoning effort is 'low'"""
        with patch.dict("sys.modules", {"mlx_lm": mock_mlx_lm}):
            client = MLXLLMClient(model_path=mock_model_path)
            assert client.reasoning_effort == "low"

    def test_explicit_reasoning_effort_low(self, mock_mlx_lm, mock_model_path):
        """Test setting reasoning effort to 'low' in constructor"""
        with patch.dict("sys.modules", {"mlx_lm": mock_mlx_lm}):
            client = MLXLLMClient(
                model_path=mock_model_path,
                reasoning_effort="low"
            )
            assert client.reasoning_effort == "low"

    def test_explicit_reasoning_effort_medium(self, mock_mlx_lm, mock_model_path):
        """Test setting reasoning effort to 'medium' in constructor"""
        with patch.dict("sys.modules", {"mlx_lm": mock_mlx_lm}):
            client = MLXLLMClient(
                model_path=mock_model_path,
                reasoning_effort="medium"
            )
            assert client.reasoning_effort == "medium"

    def test_explicit_reasoning_effort_high(self, mock_mlx_lm, mock_model_path):
        """Test setting reasoning effort to 'high' in constructor"""
        with patch.dict("sys.modules", {"mlx_lm": mock_mlx_lm}):
            client = MLXLLMClient(
                model_path=mock_model_path,
                reasoning_effort="high"
            )
            assert client.reasoning_effort == "high"

    def test_invalid_reasoning_effort_constructor(self, mock_mlx_lm, mock_model_path):
        """Test invalid reasoning effort raises ValueError"""
        with pytest.raises(ValueError, match="reasoning_effort must be one of"):
            with patch.dict("sys.modules", {"mlx_lm": mock_mlx_lm}):
                MLXLLMClient(
                    model_path=mock_model_path,
                    reasoning_effort="extreme"
                )

    def test_invalid_reasoning_effort_empty_string(self, mock_mlx_lm, mock_model_path):
        """Test empty string reasoning effort raises ValueError"""
        with pytest.raises(ValueError, match="reasoning_effort must be one of"):
            with patch.dict("sys.modules", {"mlx_lm": mock_mlx_lm}):
                MLXLLMClient(
                    model_path=mock_model_path,
                    reasoning_effort=""
                )

    def test_invalid_reasoning_effort_case_sensitive(self, mock_mlx_lm, mock_model_path):
        """Test reasoning effort is case-sensitive"""
        with pytest.raises(ValueError, match="reasoning_effort must be one of"):
            with patch.dict("sys.modules", {"mlx_lm": mock_mlx_lm}):
                MLXLLMClient(
                    model_path=mock_model_path,
                    reasoning_effort="Low"  # Wrong case
                )


class TestMLXClientReasoningEffortComplete:
    """Test reasoning_effort parameter in complete() method"""

    @pytest.mark.asyncio
    async def test_reasoning_effort_uses_instance_default(self, mlx_client, mock_mlx_lm):
        """Test complete() uses instance default reasoning effort"""
        # mlx_client fixture has reasoning_effort="low"
        response = await mlx_client.complete(prompt="Test prompt")

        assert isinstance(response, LLMResponse)
        # Reasoning effort should be logged (verified in logging tests)

    @pytest.mark.asyncio
    async def test_reasoning_effort_override_to_medium(self, mlx_client, mock_mlx_lm):
        """Test overriding reasoning effort to 'medium' in complete()"""
        response = await mlx_client.complete(
            prompt="Test prompt",
            reasoning_effort="medium"
        )

        assert isinstance(response, LLMResponse)
        assert response.content == '{"facts": "Compressed text here"}'

    @pytest.mark.asyncio
    async def test_reasoning_effort_override_to_high(self, mlx_client, mock_mlx_lm):
        """Test overriding reasoning effort to 'high' in complete()"""
        response = await mlx_client.complete(
            prompt="Test prompt",
            reasoning_effort="high"
        )

        assert isinstance(response, LLMResponse)
        assert response.content == '{"facts": "Compressed text here"}'

    @pytest.mark.asyncio
    async def test_invalid_reasoning_effort_override(self, mlx_client):
        """Test invalid reasoning effort override raises ValueError"""
        with pytest.raises(ValueError, match="reasoning_effort must be one of"):
            await mlx_client.complete(
                prompt="Test prompt",
                reasoning_effort="invalid"
            )

    @pytest.mark.asyncio
    async def test_invalid_reasoning_effort_override_extreme(self, mlx_client):
        """Test 'extreme' reasoning effort override raises ValueError"""
        with pytest.raises(ValueError, match="reasoning_effort must be one of"):
            await mlx_client.complete(
                prompt="Test prompt",
                reasoning_effort="extreme"
            )

    @pytest.mark.asyncio
    async def test_reasoning_effort_override_empty_string(self, mlx_client):
        """Test empty string reasoning effort override raises ValueError"""
        with pytest.raises(ValueError, match="reasoning_effort must be one of"):
            await mlx_client.complete(
                prompt="Test prompt",
                reasoning_effort=""
            )


class TestMLXClientBackwardCompatibility:
    """Test backward compatibility with existing code"""

    @pytest.mark.asyncio
    async def test_complete_without_reasoning_effort_works(self, mock_mlx_lm, mock_model_path):
        """Test existing code without reasoning_effort still works"""
        with patch.dict("sys.modules", {"mlx_lm": mock_mlx_lm}):
            # Old-style initialization (no reasoning_effort)
            client = MLXLLMClient(
                model_path=mock_model_path,
                max_tokens=100,
                temperature=0.3
            )

            # Old-style call (no reasoning_effort)
            response = await client.complete(prompt="What is Python?")

            assert isinstance(response, LLMResponse)
            assert response.content == '{"facts": "Compressed text here"}'
            assert response.model == "gpt-oss-20b-mlx"
            assert response.provider == "mlx"

            # Cleanup
            client._executor.shutdown(wait=True)

    @pytest.mark.asyncio
    async def test_existing_kwargs_still_work(self, mlx_client, mock_mlx_lm):
        """Test existing kwargs (temperature, max_tokens) still work"""
        response = await mlx_client.complete(
            prompt="Test prompt",
            temperature=0.7,
            max_tokens=50,
            timeout=30
        )

        assert isinstance(response, LLMResponse)
        # Verify parameters were passed correctly
        call_args = mock_mlx_lm.generate.call_args
        assert call_args.kwargs["max_tokens"] == 50

    @pytest.mark.asyncio
    async def test_mixing_old_and_new_kwargs(self, mlx_client, mock_mlx_lm):
        """Test mixing old kwargs with new reasoning_effort"""
        response = await mlx_client.complete(
            prompt="Test prompt",
            temperature=0.7,
            max_tokens=50,
            reasoning_effort="high"
        )

        assert isinstance(response, LLMResponse)
        assert response.content == '{"facts": "Compressed text here"}'


class TestMLXClientValidReasoningEfforts:
    """Test VALID_REASONING_EFFORTS constant"""

    def test_valid_reasoning_efforts_constant(self):
        """Test VALID_REASONING_EFFORTS contains expected values"""
        assert MLXLLMClient.VALID_REASONING_EFFORTS == ["low", "medium", "high"]

    def test_valid_reasoning_efforts_is_list(self):
        """Test VALID_REASONING_EFFORTS is a list"""
        assert isinstance(MLXLLMClient.VALID_REASONING_EFFORTS, list)

    def test_valid_reasoning_efforts_count(self):
        """Test VALID_REASONING_EFFORTS has exactly 3 values"""
        assert len(MLXLLMClient.VALID_REASONING_EFFORTS) == 3


class TestMLXClientLogging:
    """Test that reasoning_effort is included in logs"""

    @pytest.mark.asyncio
    async def test_reasoning_effort_logged_in_debug(self, mlx_client, mock_mlx_lm):
        """Test reasoning_effort is logged in debug messages"""
        with patch("src.research.mlx_llm_client.logger") as mock_logger:
            await mlx_client.complete(prompt="Test prompt")

            # Check debug call
            debug_calls = [call for call in mock_logger.debug.call_args_list]
            assert len(debug_calls) > 0

            # Verify reasoning_effort is in the first debug call
            first_debug_call = debug_calls[0]
            assert "reasoning_effort" in first_debug_call[1]

    @pytest.mark.asyncio
    async def test_reasoning_effort_logged_in_info(self, mlx_client, mock_mlx_lm):
        """Test reasoning_effort is logged in info messages"""
        with patch("src.research.mlx_llm_client.logger") as mock_logger:
            await mlx_client.complete(prompt="Test prompt")

            # Check info call
            info_calls = [call for call in mock_logger.info.call_args_list]
            assert len(info_calls) > 0

            # Verify reasoning_effort is in the info call
            info_call = info_calls[0]
            assert "reasoning_effort" in info_call[1]

    @pytest.mark.asyncio
    async def test_overridden_reasoning_effort_logged(self, mlx_client, mock_mlx_lm):
        """Test overridden reasoning_effort value is logged"""
        with patch("src.research.mlx_llm_client.logger") as mock_logger:
            await mlx_client.complete(
                prompt="Test prompt",
                reasoning_effort="high"
            )

            # Check debug call has correct reasoning_effort
            debug_calls = [call for call in mock_logger.debug.call_args_list]
            first_debug_call = debug_calls[0]
            assert first_debug_call[1]["reasoning_effort"] == "high"


class TestMLXClientHarmonyIntegration:
    """Test integration with Harmony-formatted prompts"""

    @pytest.mark.asyncio
    async def test_harmony_prompt_response(self, mlx_client, mock_mlx_lm):
        """Test with Harmony-formatted prompt and response"""
        # Simulate Harmony prompt (with developer block)
        harmony_prompt = """
---
Task: Compress text
Reasoning: low
---

Compress this: Test content here.
"""

        # Simulate Harmony response (with channels)
        harmony_response = """
<|start|>assistant<|channel|>analysis<|message|>
Thinking about compression...
<|end|><|start|>assistant<|channel|>final<|message|>
{"facts": "Compressed content"}
"""
        mock_mlx_lm.generate.return_value = harmony_response

        response = await mlx_client.complete(prompt=harmony_prompt)

        assert isinstance(response, LLMResponse)
        # Response content is raw (caller will parse channels)
        assert "final" in response.content or "facts" in response.content

    @pytest.mark.asyncio
    async def test_non_harmony_prompt_still_works(self, mlx_client, mock_mlx_lm):
        """Test non-Harmony prompts still work (backward compatible)"""
        # Regular prompt without Harmony format
        regular_prompt = "What is Python?"

        # Regular response without Harmony markers
        regular_response = "Python is a programming language."
        mock_mlx_lm.generate.return_value = regular_response

        response = await mlx_client.complete(prompt=regular_prompt)

        assert isinstance(response, LLMResponse)
        assert response.content == regular_response
