# LiteLLM Client Interface Contract

**Provider:** Agent 1 - LiteLLM Integration
**Consumers:** Agent 4 - Research API, Agent 5 - Prompt Engineering
**File:** `src/research/litellm_client.py`
**Status:** Wave 1 Foundation Layer
**Version:** 1.0
**Last Updated:** 2025-10-17

---

## Overview

The LiteLLM client provides a unified interface for calling various LLM providers (OpenAI, Anthropic, Google, local models) with consistent error handling, retry logic, and streaming support.

---

## Interface Definition

### Class: `LiteLLMClient`

```python
from typing import Optional, Dict, Any, AsyncIterator
from dataclasses import dataclass

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

@dataclass
class LLMResponse:
    """Standardized LLM response"""
    content: str  # Generated text
    model: str  # Actual model used
    provider: str  # Provider name
    usage: Dict[str, int]  # {"prompt_tokens": N, "completion_tokens": N, "total_tokens": N}
    finish_reason: str  # "stop", "length", "error"
    latency_ms: int  # Response time

class LiteLLMClient:
    """Unified LLM client using LiteLLM library"""

    def __init__(self, config: ModelConfig):
        """
        Initialize client with model configuration

        Args:
            config: ModelConfig with provider and model settings

        Raises:
            ValueError: If provider/model not supported
            ConnectionError: If API keys missing or invalid
        """
        pass

    async def complete(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        **kwargs
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

        Example:
            >>> client = LiteLLMClient(ModelConfig(provider="openai", model_name="gpt-4"))
            >>> response = await client.complete(
            ...     prompt="What is quantum computing?",
            ...     system_message="You are a helpful research assistant."
            ... )
            >>> print(response.content)
            "Quantum computing uses quantum mechanics..."
        """
        pass

    async def complete_with_context(
        self,
        query: str,
        context: str,
        system_message: str,
        **kwargs
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

        Example:
            >>> response = await client.complete_with_context(
            ...     query="What caused the financial crisis?",
            ...     context="[Document 1: crisis.pdf, Page 3]\\n...",
            ...     system_message="Answer using ONLY provided context. Cite sources as [N]."
            ... )
        """
        pass

    async def stream_complete(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        **kwargs
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

        Example:
            >>> async for chunk in client.stream_complete(prompt="Explain AI"):
            ...     print(chunk, end="", flush=True)
        """
        pass

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate API cost for token usage

        Args:
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens

        Returns:
            float: Estimated cost in USD

        Example:
            >>> cost = client.estimate_cost(prompt_tokens=500, completion_tokens=200)
            >>> print(f"Estimated cost: ${cost:.4f}")
        """
        pass

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
        pass
```

---

## Configuration

### Environment Variables

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Google
GOOGLE_API_KEY=...

# Local Models (e.g., Ollama)
LOCAL_MODEL_BASE_URL=http://localhost:11434
```

### Supported Models

| Provider | Model Name | Context Window | Cost (per 1M tokens) |
|----------|------------|----------------|---------------------|
| OpenAI | gpt-4-turbo | 128K | $10/$30 (in/out) |
| OpenAI | gpt-3.5-turbo | 16K | $0.50/$1.50 |
| Anthropic | claude-3-opus-20240229 | 200K | $15/$75 |
| Anthropic | claude-3-sonnet-20240229 | 200K | $3/$15 |
| Google | gemini-1.5-pro | 1M | $3.50/$10.50 |
| Local | llama2:13b | 4K | Free |

---

## Error Handling

### Exception Hierarchy

```python
class LLMError(Exception):
    """Base exception for LLM client errors"""
    pass

class RateLimitError(LLMError):
    """API rate limit exceeded"""
    retry_after: int  # Seconds to wait

class TimeoutError(LLMError):
    """Request timeout"""
    pass

class InvalidModelError(LLMError):
    """Model not supported or invalid config"""
    pass

class AuthenticationError(LLMError):
    """API key missing or invalid"""
    pass

class ContextLengthError(LLMError):
    """Prompt exceeds model's context window"""
    exceeded_by: int  # Tokens over limit
```

### Retry Logic

- **Rate Limits:** Auto-retry 3 times with exponential backoff (2s, 4s, 8s)
- **Timeouts:** No retry, fail immediately
- **Transient Errors:** Retry 2 times with 1s delay
- **Authentication:** No retry, fail immediately

---

## Usage Examples

### Basic Completion

```python
from src.research.litellm_client import LiteLLMClient, ModelConfig

# Initialize with GPT-4
config = ModelConfig(
    provider="openai",
    model_name="gpt-4-turbo",
    temperature=0.3,
    max_tokens=2000
)
client = LiteLLMClient(config)

# Generate response
response = await client.complete(
    prompt="What is the capital of France?",
    system_message="You are a helpful assistant."
)

print(response.content)  # "The capital of France is Paris."
print(f"Tokens used: {response.usage['total_tokens']}")
print(f"Latency: {response.latency_ms}ms")
```

### Research Query with Context

```python
# Build context from search results
context = """
[Document 1: france-geography.pdf, Page 2]
France is a country in Western Europe. Its capital and largest city is Paris,
located on the Seine River in northern France.

[Document 2: european-capitals.pdf, Page 5]
Paris has been the capital of France since 987 AD. The city is known for
the Eiffel Tower, Louvre Museum, and Notre-Dame Cathedral.
"""

# Generate answer with citations
response = await client.complete_with_context(
    query="What is the capital of France and what is it known for?",
    context=context,
    system_message="""You are a research assistant. Answer the query using ONLY
    the provided context. Cite sources using [N] where N is the document number.
    Place citations immediately after the relevant facts."""
)

# Expected output:
# "The capital of France is Paris [1], located on the Seine River [1]. It has
# been the capital since 987 AD [2] and is known for landmarks like the Eiffel
# Tower, Louvre Museum, and Notre-Dame Cathedral [2]."
```

### Streaming Response

```python
async def stream_answer():
    async for chunk in client.stream_complete(
        prompt="Explain quantum computing in simple terms.",
        system_message="You are a science educator."
    ):
        print(chunk, end="", flush=True)
    print()  # Newline after stream completes

# Output streams token by token:
# "Quantum computing uses quantum mechanics to process information..."
```

### Cost Estimation

```python
# Estimate before calling
prompt = "Long research query..."
context = "Retrieved document context..."
full_prompt = f"{context}\n\nQuery: {prompt}"

prompt_tokens = client.count_tokens(full_prompt)
estimated_completion = 500  # Expected response length

cost = client.estimate_cost(prompt_tokens, estimated_completion)
print(f"Estimated cost: ${cost:.4f}")

if cost > 0.10:  # Budget check
    print("Switching to cheaper model")
    client = LiteLLMClient(ModelConfig(provider="openai", model_name="gpt-3.5-turbo"))
```

### Error Handling

```python
from src.research.litellm_client import RateLimitError, TimeoutError, LLMError

try:
    response = await client.complete(prompt="What is AI?")
except RateLimitError as e:
    print(f"Rate limited, retry after {e.retry_after}s")
    # Auto-retried 3x already, still failed
except TimeoutError:
    print("Request timed out")
except ContextLengthError as e:
    print(f"Prompt too long by {e.exceeded_by} tokens")
except LLMError as e:
    print(f"LLM error: {e}")
```

---

## Integration Points

### Consumed By: Research API (Agent 4)

```python
# src/api/research.py
from src.research.litellm_client import LiteLLMClient, ModelConfig

# Initialize in FastAPI app startup
@app.on_event("startup")
async def startup():
    app.state.llm_client = LiteLLMClient(
        ModelConfig(
            provider=os.getenv("LLM_PROVIDER", "openai"),
            model_name=os.getenv("LLM_MODEL", "gpt-4-turbo"),
            temperature=0.3
        )
    )

# Use in research endpoint
@app.post("/api/research/ask")
async def ask_research_question(request: ResearchRequest):
    # Context builder provides context
    context = await build_context(request.query)

    # LiteLLM client generates answer
    response = await app.state.llm_client.complete_with_context(
        query=request.query,
        context=context,
        system_message=RESEARCH_SYSTEM_PROMPT
    )

    return response.content
```

### Consumed By: Prompt Engineering (Agent 5)

```python
# src/research/prompts.py
from src.research.litellm_client import LiteLLMClient

class PromptTemplates:
    @staticmethod
    async def test_prompt(client: LiteLLMClient, template: str, test_query: str):
        """Test prompt template with sample query"""
        response = await client.complete(
            prompt=test_query,
            system_message=template
        )
        return response
```

---

## Testing Requirements

### Unit Tests

1. **Model Initialization**
   - Valid configs create client
   - Invalid providers raise `InvalidModelError`
   - Missing API keys raise `AuthenticationError`

2. **Completion**
   - Successful completions return `LLMResponse`
   - Rate limits trigger retries
   - Timeouts fail without retry

3. **Token Counting**
   - Accurate counts for various text lengths
   - Special characters handled correctly

4. **Cost Estimation**
   - Accurate for each provider
   - Matches published pricing

### Integration Tests

1. **Live API Calls** (with test API keys)
   - OpenAI GPT-3.5 completion
   - Anthropic Claude completion
   - Local model (if available)

2. **Streaming**
   - Tokens stream incrementally
   - Stream completes successfully

3. **Error Scenarios**
   - Invalid API key
   - Malformed request
   - Network timeout

---

## Performance Requirements

- **Latency:** <30s for completion (configurable timeout)
- **Token Throughput:** Stream at model's native speed
- **Retry Overhead:** <20s total for 3 retries (exponential backoff)
- **Token Counting:** <10ms for 10K characters

---

## Dependencies

```python
# requirements.txt
litellm>=1.0.0  # Unified LLM interface
tiktoken>=0.5.0  # Token counting for OpenAI models
```

---

## Validation Gates (Wave 1)

- [ ] All unit tests pass
- [ ] Integration test with real API succeeds
- [ ] Cost estimation accurate within 5%
- [ ] Token counting accurate within 2%
- [ ] Retry logic tested with rate limit simulation
- [ ] Streaming works for 1000+ token responses
- [ ] Error handling covers all exception types
- [ ] Documentation complete with examples

---

## Notes

- Default to GPT-4 for quality, fall back to GPT-3.5 for cost
- Use temperature 0.3 for factual research (not creative)
- Monitor token usage to avoid budget overruns
- Local models (Ollama) supported for offline/free usage
- Streaming recommended for UI responsiveness
