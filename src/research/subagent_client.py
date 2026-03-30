"""
Subagent client for Claude Code SDK research sessions.

Wraps the claude-code-sdk Python package to provide multi-turn research
Q&A backed by a Claude subagent. The SDK is an optional dependency;
if not installed, ``is_available()`` returns False.
"""

from dataclasses import dataclass
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)


class SubagentError(Exception):
    """Error from a Claude subagent invocation."""


@dataclass
class SubagentResponse:
    """Response from a Claude subagent research turn."""

    content: str
    model: str
    session_id: str  # Claude SDK session_id for resume
    cost_usd: Optional[float] = None
    duration_ms: int = 0
    num_turns: int = 0
    usage: Optional[dict] = None


async def _iter_skip_parse_errors(aiter):
    """Wrap an async iterator to skip SDK MessageParseError exceptions.

    The claude-code-sdk may encounter unknown message types (e.g.
    ``rate_limit_event``) that its parser does not handle yet.  This
    wrapper catches those errors and continues iteration instead of
    aborting the entire stream.
    """
    while True:
        try:
            yield await aiter.__anext__()
        except StopAsyncIteration:
            break
        except Exception as exc:
            if "MessageParseError" in type(exc).__name__:
                logger.debug("skipping_unknown_sdk_message", error=str(exc))
                continue
            raise


class SubagentClient:
    """Wraps claude-code-sdk for multi-turn research sessions.

    Args:
        system_prompt: System instructions provided to the subagent on
            the first turn of a session.
    """

    def __init__(self, system_prompt: str) -> None:
        self._system_prompt = system_prompt

    async def research_turn(
        self,
        query: str,
        formatted_context: str,
        resume_session_id: Optional[str] = None,
    ) -> SubagentResponse:
        """Execute a research turn via Claude Code SDK.

        Args:
            query: The user's research question.
            formatted_context: Numbered source context from ContextBuilder.
            resume_session_id: SDK session_id to resume (for follow-up turns).

        Returns:
            SubagentResponse with answer text and session metadata.

        Raises:
            RuntimeError: If claude-code-sdk is not installed.
            SubagentError: If the subagent invocation fails.
        """
        logger.info(
            "subagent_client.research_turn.start",
            query_length=len(query),
            context_length=len(formatted_context),
            has_resume=resume_session_id is not None,
        )

        try:
            from claude_code_sdk import (
                AssistantMessage,
                ClaudeCodeOptions,
                ResultMessage,
                TextBlock,
            )
            from claude_code_sdk import query as claude_query
        except ImportError:
            raise RuntimeError(
                "claude-code-sdk is not installed. "
                "Install it with: pip install claude-code-sdk"
            )

        prompt = self._build_prompt(query, formatted_context)

        options = ClaudeCodeOptions(
            system_prompt=(
                self._system_prompt if resume_session_id is None else None
            ),
            max_turns=10,
            allowed_tools=[],
            resume=resume_session_id,
        )

        collected_text: list[str] = []
        session_id: str = ""
        cost_usd: Optional[float] = None
        duration_ms: int = 0
        num_turns: int = 0
        usage: Optional[dict] = None
        model: str = ""

        try:
            async for message in _iter_skip_parse_errors(
                claude_query(prompt=prompt, options=options)
            ):
                if isinstance(message, AssistantMessage):
                    if not model:
                        model = message.model
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            collected_text.append(block.text)

                elif isinstance(message, ResultMessage):
                    session_id = message.session_id
                    cost_usd = message.total_cost_usd
                    duration_ms = message.duration_ms
                    num_turns = message.num_turns
                    usage = message.usage

                    if message.is_error:
                        raise SubagentError(
                            message.result or "Subagent returned an error"
                        )
        except SubagentError:
            raise
        except Exception as exc:
            logger.error(
                "subagent_client.research_turn.error",
                error=str(exc),
                exc_info=True,
            )
            raise SubagentError(f"Subagent invocation failed: {exc}") from exc

        content = "\n".join(collected_text)

        logger.info(
            "subagent_client.research_turn.done",
            session_id=session_id,
            duration_ms=duration_ms,
            cost_usd=cost_usd,
            content_length=len(content),
        )

        return SubagentResponse(
            content=content,
            model=model,
            session_id=session_id,
            cost_usd=cost_usd,
            duration_ms=duration_ms,
            num_turns=num_turns,
            usage=usage,
        )

    def _build_prompt(self, query: str, formatted_context: str) -> str:
        """Build the user prompt with context and query.

        Args:
            query: The user's research question.
            formatted_context: Numbered source context from ContextBuilder.

        Returns:
            Combined prompt string with document context and question.
        """
        return (
            f"DOCUMENT CONTEXT:\n{formatted_context}\n\n"
            f"QUESTION:\n{query}"
        )

    @staticmethod
    def is_available() -> bool:
        """Check if claude-code-sdk is importable."""
        try:
            import claude_code_sdk  # noqa: F401

            return True
        except ImportError:
            return False
