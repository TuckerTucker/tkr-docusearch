"""
Unit tests for SubagentClient.

Tests SDK availability checking, prompt building, and research_turn
behavior with mocked claude_code_sdk responses.

Note: In the test environment, the full claude_code_sdk import chain
fails because the ``mcp`` module is stubbed (conftest.py). We therefore
mock the entire ``claude_code_sdk`` module with lightweight stand-in
dataclasses that satisfy the isinstance checks in subagent_client.py.
"""

import sys
import types
from dataclasses import dataclass, field
from typing import Any, Optional
from unittest.mock import MagicMock

import pytest

from tkr_docusearch.research.subagent_client import (
    SubagentClient,
    SubagentError,
    SubagentResponse,
)


# ---------------------------------------------------------------------------
# Stand-in SDK types.  These mirror the claude_code_sdk dataclasses that
# subagent_client.py uses.  We inject them into sys.modules so that the
# ``from claude_code_sdk import ...`` inside research_turn resolves them.
# ---------------------------------------------------------------------------


@dataclass
class _TextBlock:
    text: str


@dataclass
class _AssistantMessage:
    content: list
    model: str
    parent_tool_use_id: Optional[str] = None


@dataclass
class _ResultMessage:
    subtype: str
    duration_ms: int
    duration_api_ms: int
    is_error: bool
    num_turns: int
    session_id: str
    total_cost_usd: Optional[float] = None
    usage: Optional[dict[str, Any]] = None
    result: Optional[str] = None


@dataclass
class _ClaudeCodeOptions:
    system_prompt: Optional[str] = None
    max_turns: int = 10
    allowed_tools: list = field(default_factory=list)
    resume: Optional[str] = None


def _build_sdk_module(query_fn=None):
    """Build a fake ``claude_code_sdk`` module with stand-in types.

    Args:
        query_fn: Optional async generator factory to use as ``query``.

    Returns:
        A ``types.ModuleType`` that can be injected into ``sys.modules``.
    """
    mod = types.ModuleType("claude_code_sdk")
    mod.TextBlock = _TextBlock
    mod.AssistantMessage = _AssistantMessage
    mod.ResultMessage = _ResultMessage
    mod.ClaudeCodeOptions = _ClaudeCodeOptions
    mod.query = query_fn
    return mod


# ---------------------------------------------------------------------------
# Helpers to construct mock async generators
# ---------------------------------------------------------------------------


def _make_mock_query(
    text: str = "Answer text.",
    session_id: str = "sdk-session-123",
    is_error: bool = False,
    error_result: Optional[str] = None,
    cost_usd: Optional[float] = 0.005,
    duration_ms: int = 1500,
    num_turns: int = 1,
    model: str = "claude-sonnet-4-20250514",
):
    """Return an async generator factory that yields stand-in SDK messages."""

    async def mock_query(prompt, options):
        yield _AssistantMessage(
            content=[_TextBlock(text=text)],
            model=model,
        )
        yield _ResultMessage(
            subtype="result",
            duration_ms=duration_ms,
            duration_api_ms=1200,
            is_error=is_error,
            num_turns=num_turns,
            session_id=session_id,
            total_cost_usd=cost_usd,
            usage={"input_tokens": 100, "output_tokens": 50},
            result=error_result if is_error else text,
        )

    return mock_query


@pytest.fixture(autouse=True)
def _inject_fake_sdk():
    """Inject (then remove) a fake claude_code_sdk for every test.

    Saves and restores whatever was previously in ``sys.modules`` under
    the ``claude_code_sdk`` key.
    """
    saved = sys.modules.get("claude_code_sdk")
    # Install a minimal module so is_available() succeeds
    sys.modules["claude_code_sdk"] = _build_sdk_module()
    yield
    # Restore
    if saved is not None:
        sys.modules["claude_code_sdk"] = saved
    else:
        sys.modules.pop("claude_code_sdk", None)


# ---------------------------------------------------------------------------
# is_available
# ---------------------------------------------------------------------------


class TestIsAvailable:
    """Tests for SubagentClient.is_available."""

    def test_returns_true_when_sdk_installed(self) -> None:
        """is_available returns True when claude_code_sdk is importable."""
        assert SubagentClient.is_available() is True

    def test_returns_false_when_import_fails(self) -> None:
        """is_available returns False when claude_code_sdk cannot be imported."""
        # Temporarily remove the fake module
        saved = sys.modules.pop("claude_code_sdk", None)
        try:
            # Use a broken module entry that will raise ImportError
            sys.modules["claude_code_sdk"] = None  # type: ignore[assignment]
            assert SubagentClient.is_available() is False
        finally:
            if saved is not None:
                sys.modules["claude_code_sdk"] = saved


# ---------------------------------------------------------------------------
# _build_prompt
# ---------------------------------------------------------------------------


class TestBuildPrompt:
    """Tests for SubagentClient._build_prompt."""

    def test_formats_context_and_query(self) -> None:
        """_build_prompt combines context and query with correct structure."""
        client = SubagentClient(system_prompt="You are a researcher.")
        prompt = client._build_prompt(
            query="What is machine learning?",
            formatted_context="[Document 1: report.pdf, Page 1]\nML is a subset of AI.",
        )

        assert "DOCUMENT CONTEXT:" in prompt
        assert "[Document 1: report.pdf, Page 1]" in prompt
        assert "ML is a subset of AI." in prompt
        assert "QUESTION:" in prompt
        assert "What is machine learning?" in prompt

    def test_context_comes_before_query(self) -> None:
        """Context section appears before the question section."""
        client = SubagentClient(system_prompt="sys")
        prompt = client._build_prompt(query="Q?", formatted_context="CTX")

        ctx_pos = prompt.index("DOCUMENT CONTEXT:")
        q_pos = prompt.index("QUESTION:")
        assert ctx_pos < q_pos


# ---------------------------------------------------------------------------
# research_turn — mocked SDK
# ---------------------------------------------------------------------------


class TestResearchTurn:
    """Tests for SubagentClient.research_turn with mocked SDK."""

    async def test_returns_subagent_response(self) -> None:
        """research_turn returns SubagentResponse with collected text."""
        mock_q = _make_mock_query(
            text="The answer is 42.",
            session_id="sdk-abc",
            model="claude-sonnet-4-20250514",
        )
        sys.modules["claude_code_sdk"] = _build_sdk_module(query_fn=mock_q)

        client = SubagentClient(system_prompt="You are a researcher.")
        response = await client.research_turn(
            query="What is the meaning?",
            formatted_context="[Doc 1]\nContext here.",
        )

        assert isinstance(response, SubagentResponse)
        assert response.content == "The answer is 42."
        assert response.session_id == "sdk-abc"
        assert response.model == "claude-sonnet-4-20250514"
        assert response.cost_usd == 0.005
        assert response.duration_ms == 1500

    async def test_captures_session_id_from_result(self) -> None:
        """research_turn captures session_id from ResultMessage."""
        mock_q = _make_mock_query(session_id="unique-sdk-id-999")
        sys.modules["claude_code_sdk"] = _build_sdk_module(query_fn=mock_q)

        client = SubagentClient(system_prompt="sys")
        response = await client.research_turn(
            query="Q",
            formatted_context="CTX",
        )

        assert response.session_id == "unique-sdk-id-999"

    async def test_raises_subagent_error_on_is_error(self) -> None:
        """research_turn raises SubagentError when ResultMessage.is_error is True."""
        mock_q = _make_mock_query(
            is_error=True,
            error_result="Something went wrong in subagent",
        )
        sys.modules["claude_code_sdk"] = _build_sdk_module(query_fn=mock_q)

        client = SubagentClient(system_prompt="sys")

        with pytest.raises(SubagentError, match="Something went wrong"):
            await client.research_turn(
                query="Q",
                formatted_context="CTX",
            )

    async def test_passes_system_prompt_on_first_turn(self) -> None:
        """system_prompt is passed when resume_session_id is None."""
        captured_options = {}

        async def capturing_query(prompt, options):
            captured_options["options"] = options
            yield _AssistantMessage(
                content=[_TextBlock(text="ok")],
                model="test-model",
            )
            yield _ResultMessage(
                subtype="result",
                duration_ms=100,
                duration_api_ms=80,
                is_error=False,
                num_turns=1,
                session_id="s1",
            )

        sys.modules["claude_code_sdk"] = _build_sdk_module(
            query_fn=capturing_query
        )

        client = SubagentClient(system_prompt="My system prompt")
        await client.research_turn(
            query="Q",
            formatted_context="CTX",
            resume_session_id=None,
        )

        opts = captured_options["options"]
        assert opts.system_prompt == "My system prompt"
        assert opts.resume is None

    async def test_passes_resume_without_system_prompt(self) -> None:
        """resume_session_id is passed; system_prompt is None for follow-ups."""
        captured_options = {}

        async def capturing_query(prompt, options):
            captured_options["options"] = options
            yield _AssistantMessage(
                content=[_TextBlock(text="ok")],
                model="test-model",
            )
            yield _ResultMessage(
                subtype="result",
                duration_ms=100,
                duration_api_ms=80,
                is_error=False,
                num_turns=1,
                session_id="s2",
            )

        sys.modules["claude_code_sdk"] = _build_sdk_module(
            query_fn=capturing_query
        )

        client = SubagentClient(system_prompt="My system prompt")
        await client.research_turn(
            query="Follow-up Q",
            formatted_context="CTX",
            resume_session_id="existing-session-xyz",
        )

        opts = captured_options["options"]
        assert opts.system_prompt is None
        assert opts.resume == "existing-session-xyz"

    async def test_collects_text_from_multiple_blocks(self) -> None:
        """research_turn concatenates text from multiple TextBlocks."""

        async def multi_block_query(prompt, options):
            yield _AssistantMessage(
                content=[
                    _TextBlock(text="Part one."),
                    _TextBlock(text=" Part two."),
                ],
                model="test-model",
            )
            yield _ResultMessage(
                subtype="result",
                duration_ms=200,
                duration_api_ms=180,
                is_error=False,
                num_turns=1,
                session_id="s3",
            )

        sys.modules["claude_code_sdk"] = _build_sdk_module(
            query_fn=multi_block_query
        )

        client = SubagentClient(system_prompt="sys")
        response = await client.research_turn(
            query="Q",
            formatted_context="CTX",
        )

        assert response.content == "Part one.\n Part two."

    async def test_wraps_unexpected_exception_as_subagent_error(self) -> None:
        """Unexpected exceptions are wrapped in SubagentError."""

        async def failing_query(prompt, options):
            raise ConnectionError("Network down")
            yield  # pragma: no cover -- makes this an async generator

        sys.modules["claude_code_sdk"] = _build_sdk_module(
            query_fn=failing_query
        )

        client = SubagentClient(system_prompt="sys")

        with pytest.raises(SubagentError, match="Subagent invocation failed"):
            await client.research_turn(
                query="Q",
                formatted_context="CTX",
            )

    async def test_runtime_error_when_sdk_not_installed(self) -> None:
        """research_turn raises RuntimeError when SDK cannot be imported."""
        # Remove the fake module so the import fails
        sys.modules["claude_code_sdk"] = None  # type: ignore[assignment]

        client = SubagentClient(system_prompt="sys")

        with pytest.raises(RuntimeError, match="claude-code-sdk is not installed"):
            await client.research_turn(
                query="Q",
                formatted_context="CTX",
            )
