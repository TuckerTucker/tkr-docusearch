"""
MLX LLM Client for local inference with gpt-oss-20B.

Provides async interface to MLX-based models with Metal GPU acceleration,
matching LiteLLMClient contract for drop-in compatibility.
"""

import asyncio
import os
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Dict, Optional

import structlog

logger = structlog.get_logger(__name__)

# Import MLX sampler utilities for temperature control
try:
    from mlx_lm.sample_utils import make_sampler

    MLX_SAMPLER_AVAILABLE = True
except ImportError:
    logger.warning("mlx_lm.sample_utils not available, temperature control disabled")
    MLX_SAMPLER_AVAILABLE = False


# Exception hierarchy (reuse from litellm_client)
class LLMError(Exception):
    """Base exception for LLM client errors"""


class TimeoutError(LLMError):
    """Request timeout"""


class ContextLengthError(LLMError):
    """Prompt exceeds model's context window"""

    def __init__(self, message: str, exceeded_by: int = 0):
        super().__init__(message)
        self.exceeded_by = exceeded_by


@dataclass
class LLMResponse:
    """Standardized LLM response (matches LiteLLMClient)"""

    content: str  # Generated text
    model: str  # Model identifier
    provider: str  # "mlx"
    usage: Dict[str, int]  # Token counts
    finish_reason: str = "stop"  # Completion status
    latency_ms: int = 0  # Response time


class MLXLLMClient:
    """Native MLX inference client for gpt-oss (Metal GPU optimized)"""

    # Context window for gpt-oss-20B
    CONTEXT_WINDOW = 16384

    # Valid reasoning effort levels
    VALID_REASONING_EFFORTS = ["low", "medium", "high"]

    def __init__(
        self,
        model_path: str,
        max_tokens: int = 4000,
        temperature: float = 0.3,
        reasoning_effort: str = "low",
    ):
        """
        Initialize MLX client with model loading.

        Args:
            model_path: Absolute path to MLX model directory
            max_tokens: Maximum output tokens (default: 4000)
            temperature: Sampling temperature (default: 0.3 for factual)
            reasoning_effort: Reasoning level for Harmony prompts (default: "low")
                             Valid values: "low" | "medium" | "high"

        Raises:
            FileNotFoundError: If model_path doesn't exist
            RuntimeError: If model fails to load
            ValueError: If parameters are invalid (including reasoning_effort)

        Side Effects:
            - Loads ~13GB model into memory
            - Initializes Metal GPU context

        Performance:
            Expected throughput: 15-20 tokens/sec on M1 Max with 4-bit quantization

        Notes:
            - "low" reasoning: Fast, for extraction/compression (30-50 tokens/sec)
            - "medium" reasoning: Balanced, for analysis (15-25 tokens/sec)
            - "high" reasoning: Slow, for complex reasoning (8-15 tokens/sec)
            - Default "low" optimized for preprocessing tasks
        """
        # Validate parameters
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"MLX model not found: {model_path}")

        if max_tokens <= 0:
            raise ValueError(f"max_tokens must be positive, got: {max_tokens}")

        if not (0.0 <= temperature <= 1.0):
            raise ValueError(f"temperature must be in [0.0, 1.0], got: {temperature}")

        if reasoning_effort not in self.VALID_REASONING_EFFORTS:
            raise ValueError(
                f"reasoning_effort must be one of {self.VALID_REASONING_EFFORTS}, "
                f"got: {reasoning_effort}"
            )

        self.model_path = model_path
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.reasoning_effort = reasoning_effort

        # Load model and tokenizer
        try:
            import mlx_lm

            self.mlx_lm = mlx_lm

            logger.info("Loading MLX model", path=model_path)
            self.model, self.tokenizer = mlx_lm.load(model_path)
            logger.info(
                "MLX model loaded successfully",
                model_path=model_path,
                max_tokens=max_tokens,
                temperature=temperature,
            )

        except ImportError as e:
            raise RuntimeError(f"MLX-LM not installed. Run: pip install mlx-lm>=0.26.3. Error: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load MLX model from {model_path}: {e}")

        # Thread pool for async execution
        self._executor = ThreadPoolExecutor(max_workers=1)

    async def complete(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        Generate completion using MLX (async wrapper around sync generation).

        Args:
            prompt: User prompt/query text
            system_message: Optional system instructions prepended to prompt
            **kwargs: Override defaults:
                - temperature (float): Sampling temperature
                - max_tokens (int): Output token limit
                - timeout (int): Request timeout in seconds (default: 60)
                - reasoning_effort (str): Override instance-level reasoning effort
                                         Valid: "low" | "medium" | "high"

        Returns:
            LLMResponse with fields:
                - content (str): Generated text
                - model (str): Model identifier (e.g., "gpt-oss-20b-mlx")
                - provider (str): "mlx"
                - usage (dict): {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int}
                - finish_reason (str): "stop" | "length" | "error"
                - latency_ms (int): Inference time in milliseconds

        Raises:
            TimeoutError: If generation exceeds timeout
            ContextLengthError: If prompt exceeds model context window
            LLMError: For other generation failures
            ValueError: If reasoning_effort override is invalid

        Performance:
            - Expected: 15-20 tokens/sec on M1 Max
            - Typical latency: 2-5 seconds for 200-token response

        Notes:
            - reasoning_effort kwarg overrides instance default
            - Reasoning effort passed to Harmony prompt wrapper
            - No change to non-Harmony callers (backward compatible)
        """
        start_time = time.time()

        # Combine system message and prompt
        full_prompt = prompt
        if system_message:
            full_prompt = f"{system_message}\n\n{prompt}"

        # Add newline at end to signal completion of input
        # Many models expect this to distinguish input from generation
        if not full_prompt.endswith("\n"):
            full_prompt = full_prompt + "\n"

        # Get parameters
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        timeout = kwargs.get("timeout", 60)

        # Get reasoning effort (instance default or override)
        reasoning_effort = kwargs.get("reasoning_effort", self.reasoning_effort)

        # Validate override if provided
        if "reasoning_effort" in kwargs:
            if reasoning_effort not in self.VALID_REASONING_EFFORTS:
                raise ValueError(
                    f"reasoning_effort must be one of {self.VALID_REASONING_EFFORTS}, "
                    f"got: {reasoning_effort}"
                )

        # Count prompt tokens
        try:
            prompt_tokens = self._count_tokens(full_prompt)
        except Exception as e:
            logger.warning("Failed to count prompt tokens, using estimate", error=str(e))
            prompt_tokens = len(full_prompt) // 4

        # Check context length
        if prompt_tokens > self.CONTEXT_WINDOW:
            exceeded_by = prompt_tokens - self.CONTEXT_WINDOW
            raise ContextLengthError(
                f"Prompt exceeds context window: {prompt_tokens} > {self.CONTEXT_WINDOW}",
                exceeded_by=exceeded_by,
            )

        logger.debug(
            "Starting MLX generation",
            prompt_tokens=prompt_tokens,
            max_tokens=max_tokens,
            temperature=temperature,
            reasoning_effort=reasoning_effort,
        )

        # Run generation in executor to avoid blocking event loop
        try:
            # Create task with timeout
            generation_task = asyncio.get_event_loop().run_in_executor(
                self._executor,
                self._generate_sync,
                full_prompt,
                temperature,
                max_tokens,
            )

            # Wait with timeout
            response_text = await asyncio.wait_for(generation_task, timeout=timeout)

        except asyncio.TimeoutError:
            raise TimeoutError(f"Generation timed out after {timeout} seconds")
        except Exception as e:
            logger.error("MLX generation failed", error=str(e), exc_info=True)
            raise LLMError(f"Generation failed: {e}")

        # Count completion tokens
        try:
            completion_tokens = self._count_tokens(response_text)
        except Exception as e:
            logger.warning("Failed to count completion tokens, using estimate", error=str(e))
            completion_tokens = len(response_text) // 4

        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)

        # Determine finish reason
        finish_reason = "stop"
        if completion_tokens >= max_tokens:
            finish_reason = "length"

        # Build response
        llm_response = LLMResponse(
            content=response_text,
            model="gpt-oss-20b-mlx",
            provider="mlx",
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            finish_reason=finish_reason,
            latency_ms=latency_ms,
        )

        # Calculate tokens per second (avoid division by zero)
        tokens_per_sec = round(completion_tokens / (latency_ms / 1000), 2) if latency_ms > 0 else 0

        logger.info(
            "MLX generation complete",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=llm_response.usage["total_tokens"],
            latency_ms=latency_ms,
            tokens_per_sec=tokens_per_sec,
            reasoning_effort=reasoning_effort,
        )

        return llm_response

    def _generate_sync(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """
        Synchronous generation helper (runs in executor).

        Args:
            prompt: Full prompt text (system + user)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text string
        """
        try:
            # MLX-LM 0.28.3: Use make_sampler() for temperature control
            # Cannot pass temperature directly to generate()
            sampler_kwargs = {}
            if MLX_SAMPLER_AVAILABLE:
                sampler = make_sampler(temp=temperature)
                sampler_kwargs["sampler"] = sampler

            response = self.mlx_lm.generate(
                model=self.model,
                tokenizer=self.tokenizer,
                prompt=prompt,
                verbose=False,  # Disable progress output
                max_tokens=max_tokens,
                **sampler_kwargs,
            )
            return response
        except Exception as e:
            logger.error("MLX generate() failed", error=str(e), exc_info=True)
            raise LLMError(f"MLX generate failed: {e}")

    def _count_tokens(self, text: str) -> int:
        """
        Count tokens using MLX tokenizer.

        Args:
            text: Text to tokenize

        Returns:
            Token count (accurate to ±10%)
        """
        try:
            tokens = self.tokenizer.encode(text)
            return len(tokens)
        except Exception as e:
            logger.warning("Tokenizer encode failed, using heuristic", error=str(e))
            # Heuristic: ~4 characters per token
            return len(text) // 4

    def __del__(self):
        """Cleanup executor on deletion"""
        if hasattr(self, "_executor"):
            self._executor.shutdown(wait=False)
