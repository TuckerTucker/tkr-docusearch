"""
LiteLLM Client for unified LLM interface.

Supports OpenAI, Anthropic, Google, and local models through LiteLLM.
Provides consistent error handling, retry logic, and streaming support.
"""

import os
import time
from dataclasses import dataclass, field
from typing import AsyncIterator, Dict, Optional

import structlog

logger = structlog.get_logger(__name__)


# Exception hierarchy
class LLMError(Exception):
    """Base exception for LLM client errors"""



class RateLimitError(LLMError):
    """API rate limit exceeded"""

    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after


class TimeoutError(LLMError):
    """Request timeout"""



class InvalidModelError(LLMError):
    """Model not supported or invalid config"""



class AuthenticationError(LLMError):
    """API key missing or invalid"""



class ContextLengthError(LLMError):
    """Prompt exceeds model's context window"""

    def __init__(self, message: str, exceeded_by: int = 0):
        super().__init__(message)
        self.exceeded_by = exceeded_by


@dataclass
class ModelConfig:
    """Configuration for LLM model selection"""

    provider: str  # "openai", "anthropic", "google", "local"
    model_name: str  # e.g., "gpt-4", "claude-3-opus-20240229"
    temperature: float = 0.3  # Lower for factual responses
    max_tokens: int = 2000
    timeout: int = 30
    api_key: Optional[str] = None  # From env if not provided
    api_base: Optional[str] = None  # For local models

    def __post_init__(self):
        """Validate configuration"""
        valid_providers = ["openai", "anthropic", "google", "local"]
        if self.provider not in valid_providers:
            raise InvalidModelError(
                f"Invalid provider: {self.provider}. Must be one of {valid_providers}"
            )

        if self.temperature < 0.0 or self.temperature > 1.0:
            raise InvalidModelError("Temperature must be between 0.0 and 1.0")


@dataclass
class LLMResponse:
    """Standardized LLM response"""

    content: str  # Generated text
    model: str  # Actual model used
    provider: str  # Provider name
    usage: Dict[str, int] = field(default_factory=dict)  # Token usage
    finish_reason: str = "stop"  # "stop", "length", "error"
    latency_ms: int = 0  # Response time


class LiteLLMClient:
    """Unified LLM client using LiteLLM library"""

    # Model pricing (per 1M tokens)
    PRICING = {
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
        "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
        "claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0},
        "gemini-1.5-pro": {"input": 3.5, "output": 10.5},
    }

    def __init__(self, config: ModelConfig):
        """
        Initialize client with model configuration

        Args:
            config: ModelConfig with provider and model settings

        Raises:
            ValueError: If provider/model not supported
            ConnectionError: If API keys missing or invalid
        """
        self.config = config

        # Set API key from config or environment
        if not config.api_key:
            self._load_api_key_from_env()
        else:
            self._set_api_key(config.api_key)

        # Import litellm (lazy to avoid import errors if not installed)
        try:
            import litellm

            self.litellm = litellm
            # Configure litellm
            litellm.set_verbose = False  # Reduce logging
        except ImportError:
            raise InvalidModelError("LiteLLM not installed. Run: pip install litellm")

        logger.info("LiteLLM client initialized", provider=config.provider, model=config.model_name)

    def _load_api_key_from_env(self):
        """Load API key from environment variables"""
        key_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY",
        }

        if self.config.provider in key_map:
            env_key = key_map[self.config.provider]
            api_key = os.getenv(env_key)

            if not api_key and self.config.provider != "local":
                raise AuthenticationError(f"API key not found. Set {env_key} environment variable.")

            if api_key:
                self._set_api_key(api_key)

    def _set_api_key(self, api_key: str):
        """Set API key in environment for litellm"""
        key_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY",
        }

        if self.config.provider in key_map:
            os.environ[key_map[self.config.provider]] = api_key

    async def complete(
        self, prompt: str, system_message: Optional[str] = None, **kwargs
    ) -> LLMResponse:
        """
        Generate completion from LLM

        Args:
            prompt: User prompt/query
            system_message: System instructions (optional)
            **kwargs: Override config (temperature, max_tokens, etc.)

        Returns:
            LLMResponse with generated text and metadata

        Raises:
            RateLimitError: If API rate limit exceeded (auto-retry 3x)
            TimeoutError: If request exceeds timeout
            LLMError: For other API failures
        """
        start_time = time.time()

        # Build messages
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        # Merge config with kwargs
        params = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "timeout": kwargs.get("timeout", self.config.timeout),
        }

        # Override model if specified
        if "model" in kwargs:
            params["model"] = kwargs["model"]

        # Add API base for local models
        if self.config.api_base:
            params["api_base"] = self.config.api_base

        # Retry logic
        max_retries = 3
        retry_delays = [2, 4, 8]  # Exponential backoff

        for attempt in range(max_retries):
            try:
                logger.debug("Calling LLM", model=params["model"], attempt=attempt + 1)

                response = await self.litellm.acompletion(**params)

                latency_ms = int((time.time() - start_time) * 1000)

                llm_response = LLMResponse(
                    content=response.choices[0].message.content,
                    model=response.model,
                    provider=self.config.provider,
                    usage={
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                    },
                    finish_reason=response.choices[0].finish_reason,
                    latency_ms=latency_ms,
                )

                logger.info(
                    "LLM completion successful",
                    model=response.model,
                    tokens=llm_response.usage["total_tokens"],
                    latency_ms=latency_ms,
                )

                return llm_response

            except self.litellm.RateLimitError as e:
                if attempt < max_retries - 1:
                    delay = retry_delays[attempt]
                    logger.warning("Rate limit hit, retrying", attempt=attempt + 1, delay=delay)
                    await self._async_sleep(delay)
                else:
                    raise RateLimitError(str(e), retry_after=60)

            except self.litellm.Timeout as e:
                raise TimeoutError(f"Request timed out: {str(e)}")

            except self.litellm.AuthenticationError as e:
                raise AuthenticationError(f"Authentication failed: {str(e)}")

            except self.litellm.ContextWindowExceededError as e:
                # Try to extract how much we exceeded by
                raise ContextLengthError(str(e))

            except Exception as e:
                logger.error("LLM error", error=str(e), exc_info=True)
                if attempt < max_retries - 1:
                    delay = retry_delays[attempt]
                    logger.warning("Transient error, retrying", delay=delay)
                    await self._async_sleep(delay)
                else:
                    raise LLMError(f"LLM request failed: {str(e)}")

        raise LLMError("Max retries exceeded")

    async def complete_with_context(
        self, query: str, context: str, system_message: str, **kwargs
    ) -> LLMResponse:
        """
        Convenience method for research queries with context

        Args:
            query: User's research question
            context: Retrieved document context
            system_message: Research assistant instructions
            **kwargs: Override config

        Returns:
            LLMResponse with answer and citations
        """
        # Build full prompt
        full_prompt = f"{context}\n\nQuery: {query}"

        return await self.complete(prompt=full_prompt, system_message=system_message, **kwargs)

    async def stream_complete(
        self, prompt: str, system_message: Optional[str] = None, **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream completion tokens as they're generated

        Args:
            prompt: User prompt/query
            system_message: System instructions (optional)
            **kwargs: Override config

        Yields:
            str: Individual tokens/chunks as received

        Raises:
            Same exceptions as complete()
        """
        # Build messages
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        # Merge config with kwargs
        params = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "timeout": kwargs.get("timeout", self.config.timeout),
            "stream": True,
        }

        if self.config.api_base:
            params["api_base"] = self.config.api_base

        try:
            response = await self.litellm.acompletion(**params)

            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error("Streaming error", error=str(e))
            raise LLMError(f"Streaming failed: {str(e)}")

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate API cost for token usage

        Args:
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens

        Returns:
            float: Estimated cost in USD
        """
        if self.config.model_name not in self.PRICING:
            logger.warning("No pricing data for model", model=self.config.model_name)
            return 0.0

        pricing = self.PRICING[self.config.model_name]
        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text for budget management

        Args:
            text: Text to tokenize

        Returns:
            int: Approximate token count

        Note:
            Uses tiktoken for OpenAI models, approximate for others
        """
        if self.config.provider == "openai":
            try:
                import tiktoken

                encoding = tiktoken.encoding_for_model(self.config.model_name)
                return len(encoding.encode(text))
            except Exception as e:
                logger.warning("Tiktoken failed, using heuristic", error=str(e))

        # Heuristic: ~4 characters per token
        return len(text) // 4

    async def _async_sleep(self, seconds: int):
        """Async sleep helper"""
        import asyncio

        await asyncio.sleep(seconds)
