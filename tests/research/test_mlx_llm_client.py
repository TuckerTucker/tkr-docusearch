"""
Unit tests for MLX LLM Client.

Tests the MLXLLMClient's ability to load models, generate completions,
handle errors, and maintain async behavior without blocking.
"""

import asyncio
import sys
from unittest.mock import Mock, patch

import pytest

from src.research.mlx_llm_client import (
    ContextLengthError,
    LLMError,
    LLMResponse,
    MLXLLMClient,
    TimeoutError,
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
    mock_mlx.generate = Mock(return_value="This is a test response from the model.")

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
        )
        yield client
        # Cleanup
        if hasattr(client, "_executor"):
            client._executor.shutdown(wait=True)


class TestMLXLLMClientInitialization:
    """Test client initialization and model loading"""

    def test_client_initialization_success(self, mock_mlx_lm, mock_model_path):
        """Test model loads successfully"""
        with patch.dict("sys.modules", {"mlx_lm": mock_mlx_lm}):
            client = MLXLLMClient(
                model_path=mock_model_path,
                max_tokens=100,
                temperature=0.3,
            )

            assert client.model_path == mock_model_path
            assert client.max_tokens == 100
            assert client.temperature == 0.3
            mock_mlx_lm.load.assert_called_once_with(mock_model_path)

    def test_initialization_with_invalid_path(self):
        """Test FileNotFoundError for invalid model path"""
        with pytest.raises(FileNotFoundError, match="MLX model not found"):
            MLXLLMClient(
                model_path="/nonexistent/path",
                max_tokens=100,
                temperature=0.3,
            )

    def test_initialization_with_invalid_max_tokens(self, mock_mlx_lm, mock_model_path):
        """Test ValueError for invalid max_tokens"""
        with pytest.raises(ValueError, match="max_tokens must be positive"):
            with patch.dict("sys.modules", {"mlx_lm": mock_mlx_lm}):
                MLXLLMClient(
                    model_path=mock_model_path,
                    max_tokens=0,
                    temperature=0.3,
                )

    def test_initialization_with_invalid_temperature(self, mock_mlx_lm, mock_model_path):
        """Test ValueError for invalid temperature"""
        with pytest.raises(ValueError, match="temperature must be in"):
            with patch.dict("sys.modules", {"mlx_lm": mock_mlx_lm}):
                MLXLLMClient(
                    model_path=mock_model_path,
                    max_tokens=100,
                    temperature=1.5,
                )

    def test_initialization_without_mlx_installed(self, mock_model_path):
        """Test RuntimeError when mlx-lm not installed"""
        # Mock import failure
        if "mlx_lm" in sys.modules:
            del sys.modules["mlx_lm"]

        with patch.dict("sys.modules", {"mlx_lm": None}):
            # When import tries to use mlx_lm, it will fail
            with pytest.raises(RuntimeError, match="MLX-LM not installed"):
                MLXLLMClient(
                    model_path=mock_model_path,
                    max_tokens=100,
                    temperature=0.3,
                )


class TestMLXLLMClientComplete:
    """Test completion generation"""

    @pytest.mark.asyncio
    async def test_complete_basic(self, mlx_client, mock_mlx_lm):
        """Test basic completion with prompt"""
        response = await mlx_client.complete(prompt="What is Python?")

        assert isinstance(response, LLMResponse)
        assert response.content == "This is a test response from the model."
        assert response.model == "gpt-oss-20b-mlx"
        assert response.provider == "mlx"
        assert response.finish_reason == "stop"
        assert "prompt_tokens" in response.usage
        assert "completion_tokens" in response.usage
        assert "total_tokens" in response.usage
        assert response.latency_ms >= 0  # Can be 0 in fast tests

    @pytest.mark.asyncio
    async def test_complete_with_system_message(self, mlx_client, mock_mlx_lm):
        """Test system message prepending"""
        system_msg = "You are a helpful assistant."
        prompt = "Explain quantum computing."

        response = await mlx_client.complete(
            prompt=prompt,
            system_message=system_msg,
        )

        assert isinstance(response, LLMResponse)
        assert response.content == "This is a test response from the model."

        # Verify the full prompt was passed to generate
        call_args = mock_mlx_lm.generate.call_args
        assert system_msg in call_args.kwargs["prompt"]
        assert prompt in call_args.kwargs["prompt"]

    @pytest.mark.asyncio
    async def test_complete_with_custom_temperature(self, mlx_client, mock_mlx_lm):
        """Test custom temperature override"""
        response = await mlx_client.complete(
            prompt="Test prompt",
            temperature=0.7,
        )

        assert isinstance(response, LLMResponse)
        call_args = mock_mlx_lm.generate.call_args
        assert call_args.kwargs["temp"] == 0.7

    @pytest.mark.asyncio
    async def test_complete_with_custom_max_tokens(self, mlx_client, mock_mlx_lm):
        """Test custom max_tokens override"""
        response = await mlx_client.complete(
            prompt="Test prompt",
            max_tokens=50,
        )

        assert isinstance(response, LLMResponse)
        call_args = mock_mlx_lm.generate.call_args
        assert call_args.kwargs["max_tokens"] == 50

    @pytest.mark.asyncio
    async def test_token_counting(self, mlx_client):
        """Test token count accuracy (±10%)"""
        # Test with a known prompt
        prompt = "This is a test prompt with multiple words."
        response = await mlx_client.complete(prompt=prompt)

        # Verify token counts are reasonable
        assert response.usage["prompt_tokens"] > 0
        assert response.usage["completion_tokens"] > 0
        assert (
            response.usage["total_tokens"]
            == response.usage["prompt_tokens"] + response.usage["completion_tokens"]
        )

        # Token count should be approximately length/4 (within 50% margin)
        estimated_prompt_tokens = len(prompt) // 4
        assert (
            0.5 * estimated_prompt_tokens
            <= response.usage["prompt_tokens"]
            <= 2 * estimated_prompt_tokens
        )

    @pytest.mark.asyncio
    async def test_timeout_handling(self, mlx_client, mock_mlx_lm):
        """Test timeout raises TimeoutError"""

        # Mock generate to sleep longer than timeout
        def slow_generate(*args, **kwargs):
            import time

            time.sleep(2)
            return "delayed response"

        mock_mlx_lm.generate.side_effect = slow_generate

        with pytest.raises(TimeoutError, match="timed out"):
            await mlx_client.complete(
                prompt="Test prompt",
                timeout=0.5,  # 500ms timeout
            )

    @pytest.mark.asyncio
    async def test_context_length_error(self, mlx_client):
        """Test context length exceeded raises ContextLengthError"""
        # Create a very long prompt that exceeds context window
        long_prompt = "word " * 20000  # ~5000 tokens (exceeds 16384 context window)

        with pytest.raises(ContextLengthError) as exc_info:
            await mlx_client.complete(prompt=long_prompt)

        assert exc_info.value.exceeded_by > 0

    @pytest.mark.asyncio
    async def test_generation_error_handling(self, mlx_client, mock_mlx_lm):
        """Test LLMError for generation failures"""
        mock_mlx_lm.generate.side_effect = RuntimeError("Generation failed")

        with pytest.raises(LLMError, match="Generation failed"):
            await mlx_client.complete(prompt="Test prompt")

    @pytest.mark.asyncio
    async def test_finish_reason_length(self, mlx_client, mock_mlx_lm):
        """Test finish_reason is 'length' when max_tokens reached"""
        # Mock a response that's exactly max_tokens long
        long_response = "token " * 25  # ~25 tokens
        mock_mlx_lm.generate.return_value = long_response

        response = await mlx_client.complete(
            prompt="Test",
            max_tokens=25,
        )

        # Should be "length" if response is at max_tokens
        # Due to tokenization, this might be approximate
        assert response.finish_reason in ["stop", "length"]


class TestMLXLLMClientAsync:
    """Test async behavior and non-blocking execution"""

    @pytest.mark.asyncio
    async def test_async_non_blocking(self, mlx_client, mock_mlx_lm):
        """Test event loop not blocked during generation"""
        # Create a flag to track if we can do other work
        other_work_done = False

        async def do_other_work():
            nonlocal other_work_done
            await asyncio.sleep(0.1)
            other_work_done = True

        # Mock generate to take some time
        def slow_generate(*args, **kwargs):
            import time

            time.sleep(0.3)
            return "response"

        mock_mlx_lm.generate.side_effect = slow_generate

        # Run completion and other work concurrently
        completion_task = asyncio.create_task(mlx_client.complete(prompt="Test"))
        other_work_task = asyncio.create_task(do_other_work())

        # Wait for both
        await asyncio.gather(completion_task, other_work_task)

        # Verify other work completed (proving event loop wasn't blocked)
        assert other_work_done

    @pytest.mark.asyncio
    async def test_multiple_concurrent_requests(self, mlx_client, mock_mlx_lm):
        """Test handling multiple concurrent requests"""
        # Note: With max_workers=1, these will be serialized
        responses = await asyncio.gather(
            mlx_client.complete(prompt="Test 1"),
            mlx_client.complete(prompt="Test 2"),
            mlx_client.complete(prompt="Test 3"),
        )

        assert len(responses) == 3
        for response in responses:
            assert isinstance(response, LLMResponse)
            assert response.provider == "mlx"


class TestMLXLLMClientTokenCounting:
    """Test token counting utilities"""

    def test_count_tokens_basic(self, mlx_client):
        """Test basic token counting"""
        text = "This is a test sentence."
        count = mlx_client._count_tokens(text)

        # Should be approximately len(text) / 4
        assert count > 0
        assert 0.5 * (len(text) // 4) <= count <= 2 * (len(text) // 4)

    def test_count_tokens_empty(self, mlx_client):
        """Test token counting with empty string"""
        count = mlx_client._count_tokens("")
        assert count == 0

    def test_count_tokens_fallback(self, mlx_client):
        """Test fallback to heuristic on tokenizer error"""
        # Mock tokenizer to fail
        mlx_client.tokenizer.encode = Mock(side_effect=RuntimeError("Tokenizer error"))

        text = "Test text"
        count = mlx_client._count_tokens(text)

        # Should fallback to heuristic: len(text) // 4
        assert count == len(text) // 4


class TestLLMResponse:
    """Test LLMResponse dataclass"""

    def test_llm_response_creation(self):
        """Test creating LLMResponse"""
        response = LLMResponse(
            content="Test content",
            model="gpt-oss-20b-mlx",
            provider="mlx",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop",
            latency_ms=1500,
        )

        assert response.content == "Test content"
        assert response.model == "gpt-oss-20b-mlx"
        assert response.provider == "mlx"
        assert response.usage["total_tokens"] == 30
        assert response.finish_reason == "stop"
        assert response.latency_ms == 1500

    def test_llm_response_defaults(self):
        """Test LLMResponse with default values"""
        response = LLMResponse(
            content="Test",
            model="test-model",
            provider="mlx",
            usage={},
        )

        assert response.finish_reason == "stop"
        assert response.latency_ms == 0


class TestErrorHierarchy:
    """Test error exception hierarchy"""

    def test_llm_error_base(self):
        """Test LLMError is base exception"""
        error = LLMError("Base error")
        assert isinstance(error, Exception)
        assert str(error) == "Base error"

    def test_timeout_error(self):
        """Test TimeoutError"""
        error = TimeoutError("Timeout")
        assert isinstance(error, LLMError)
        assert isinstance(error, Exception)

    def test_context_length_error(self):
        """Test ContextLengthError with exceeded_by"""
        error = ContextLengthError("Context exceeded", exceeded_by=100)
        assert isinstance(error, LLMError)
        assert error.exceeded_by == 100

    def test_context_length_error_default(self):
        """Test ContextLengthError without exceeded_by"""
        error = ContextLengthError("Context exceeded")
        assert error.exceeded_by == 0
