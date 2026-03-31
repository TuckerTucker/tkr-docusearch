"""
Integration flow tests for multi-turn research sessions.

Tests multi-step interactions across the research session endpoints:
create, ask, get history, and delete. Uses real SessionManager and
CitationParser with mocked SubagentClient and ContextBuilder.
"""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Import research module first to avoid circular import between
# research.py and research_sessions.py (research.py mounts the
# sessions router at module level).
import tkr_docusearch.api.research  # noqa: F401
from tkr_docusearch.api.research_sessions import router
from tkr_docusearch.research.citation_parser import CitationParser
from tkr_docusearch.research.context_builder import ResearchContext, SourceDocument
from tkr_docusearch.research.session_manager import SessionManager
from tkr_docusearch.research.subagent_client import SubagentResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_mock_context() -> ResearchContext:
    """Build a fixed ResearchContext for tests."""
    return ResearchContext(
        formatted_text=(
            "[Document 1: test.pdf, Page 1]\n"
            "Test content about machine learning.\n\n"
            "---\n"
            "SOURCE LINKS:\n"
            "[1] test.pdf http://localhost:3333/details/doc1?page=1"
        ),
        sources=[
            SourceDocument(
                doc_id="doc1",
                filename="test.pdf",
                page=1,
                extension="pdf",
                markdown_content="Test content about machine learning.",
                relevance_score=0.9,
            ),
        ],
        total_tokens=100,
        truncated=False,
    )


def _build_mock_subagent_response(
    content: str = (
        "The answer is in the document "
        "[[1]](http://localhost:3333/details/doc1?page=1)."
    ),
    session_id: str = "sdk-session-abc",
) -> SubagentResponse:
    """Build a fixed SubagentResponse for tests."""
    return SubagentResponse(
        content=content,
        model="claude-sonnet-4-20250514",
        session_id=session_id,
        cost_usd=0.005,
        duration_ms=1500,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def flow_app() -> FastAPI:
    """Create a test FastAPI app wired for multi-step session flows.

    Uses real SessionManager (300 s TTL) and real CitationParser.
    SubagentClient and ContextBuilder are async mocks.
    """
    app = FastAPI()
    app.include_router(router)

    # Real components
    app.state.session_manager = SessionManager(ttl_seconds=300)
    app.state.citation_parser = CitationParser()

    # Mock subagent — returns a fresh response per call so that each
    # turn receives an independent SubagentResponse instance.
    mock_subagent = AsyncMock()
    mock_subagent.research_turn = AsyncMock(
        side_effect=lambda **kwargs: _build_mock_subagent_response()
    )
    app.state.subagent_client = mock_subagent

    # Mock context builder
    mock_context_builder = AsyncMock()
    mock_context_builder.build_context = AsyncMock(
        return_value=_build_mock_context()
    )
    app.state.context_builder = mock_context_builder

    return app


@pytest.fixture()
def client(flow_app: FastAPI) -> TestClient:
    """FastAPI TestClient for flow tests."""
    return TestClient(flow_app)


# ---------------------------------------------------------------------------
# Flow Tests
# ---------------------------------------------------------------------------


class TestResearchSessionFlow:
    """Multi-step flow tests for the research session lifecycle."""

    def test_create_session_ask_get_history(self, client: TestClient) -> None:
        """Create a session, ask a question, then retrieve history.

        Verifies that the user turn and assistant turn both appear in
        the session history with the correct role and content.
        """
        # Step 1 — create session
        create_resp = client.post("/api/research/sessions/create")
        assert create_resp.status_code == 200
        session_id = create_resp.json()["session_id"]

        # Step 2 — ask a question
        ask_resp = client.post(
            "/api/research/sessions/ask",
            json={"query": "What is machine learning?", "session_id": session_id},
        )
        assert ask_resp.status_code == 200
        ask_body = ask_resp.json()
        assert ask_body["session_id"] == session_id
        assert ask_body["turn"] == 1
        assert ask_body["answer"] != ""

        # Step 3 — retrieve history
        history_resp = client.get(f"/api/research/sessions/{session_id}")
        assert history_resp.status_code == 200
        history = history_resp.json()

        assert history["session_id"] == session_id
        assert history["total_turns"] == 2  # user + assistant

        user_turn = history["turns"][0]
        assistant_turn = history["turns"][1]

        assert user_turn["role"] == "user"
        assert user_turn["content"] == "What is machine learning?"

        assert assistant_turn["role"] == "assistant"
        assert "document" in assistant_turn["content"].lower()

    def test_multi_turn_session_ordering(self, client: TestClient) -> None:
        """Ask three questions in the same session.

        Verifies that history returns all six turns (3 user + 3 assistant)
        in chronological order with correct roles.
        """
        # Create session
        create_resp = client.post("/api/research/sessions/create")
        session_id = create_resp.json()["session_id"]

        queries = [
            "What is deep learning?",
            "How does backpropagation work?",
            "Explain gradient descent.",
        ]

        for idx, query in enumerate(queries, start=1):
            resp = client.post(
                "/api/research/sessions/ask",
                json={"query": query, "session_id": session_id},
            )
            assert resp.status_code == 200
            assert resp.json()["turn"] == idx

        # Retrieve full history
        history_resp = client.get(f"/api/research/sessions/{session_id}")
        assert history_resp.status_code == 200
        history = history_resp.json()

        # 3 user turns + 3 assistant turns = 6 total
        assert history["total_turns"] == 6

        # Verify alternating roles starting with user
        expected_roles = ["user", "assistant"] * 3
        actual_roles = [t["role"] for t in history["turns"]]
        assert actual_roles == expected_roles

        # Verify each user turn has the correct query
        user_turns = [t for t in history["turns"] if t["role"] == "user"]
        for user_turn, original_query in zip(user_turns, queries):
            assert user_turn["content"] == original_query

    def test_session_deletion_clears_history(self, client: TestClient) -> None:
        """Create a session, add turns, delete it, then verify GET returns 404."""
        # Create and populate session
        create_resp = client.post("/api/research/sessions/create")
        session_id = create_resp.json()["session_id"]

        client.post(
            "/api/research/sessions/ask",
            json={"query": "Tell me about neural networks.", "session_id": session_id},
        )

        # Confirm history exists
        history_resp = client.get(f"/api/research/sessions/{session_id}")
        assert history_resp.status_code == 200
        assert history_resp.json()["total_turns"] == 2

        # Delete session
        delete_resp = client.delete(f"/api/research/sessions/{session_id}")
        assert delete_resp.status_code == 200
        assert delete_resp.json()["deleted"] is True

        # GET after deletion returns 404
        gone_resp = client.get(f"/api/research/sessions/{session_id}")
        assert gone_resp.status_code == 404

    def test_auto_create_session_on_ask(self, client: TestClient) -> None:
        """POST /sessions/ask without a session_id auto-creates a session.

        Verifies that the returned session_id is valid and can be used
        to retrieve the session history via GET.
        """
        # Ask without explicit session_id
        ask_resp = client.post(
            "/api/research/sessions/ask",
            json={"query": "What are transformers?"},
        )
        assert ask_resp.status_code == 200
        ask_body = ask_resp.json()

        session_id = ask_body["session_id"]
        assert len(session_id) == 32  # uuid4 hex
        assert ask_body["turn"] == 1

        # The auto-created session should be retrievable
        history_resp = client.get(f"/api/research/sessions/{session_id}")
        assert history_resp.status_code == 200
        history = history_resp.json()

        assert history["session_id"] == session_id
        assert history["total_turns"] == 2  # user + assistant

    def test_ask_returns_citations(self) -> None:
        """Ask a question and verify that the response includes parsed citations.

        Uses a plain ``[1]`` citation format so the real CitationParser
        can map the citation to the containing sentence (the ``[[1]](url)``
        format spans a URL that contains ``?``, which the sentence-boundary
        regex splits on, preventing a clean sentence-to-citation mapping).
        """
        # Build an app whose subagent returns a simple [1] citation.
        app = FastAPI()
        app.include_router(router)
        app.state.session_manager = SessionManager(ttl_seconds=300)
        app.state.citation_parser = CitationParser()

        citation_response = _build_mock_subagent_response(
            content=(
                "Machine learning is discussed in the document [1]. "
                "It covers neural networks and deep learning."
            ),
        )
        mock_subagent = AsyncMock()
        mock_subagent.research_turn = AsyncMock(return_value=citation_response)
        app.state.subagent_client = mock_subagent

        mock_context_builder = AsyncMock()
        mock_context_builder.build_context = AsyncMock(
            return_value=_build_mock_context()
        )
        app.state.context_builder = mock_context_builder

        citation_client = TestClient(app)

        ask_resp = citation_client.post(
            "/api/research/sessions/ask",
            json={"query": "What does the document say?"},
        )
        assert ask_resp.status_code == 200
        body = ask_resp.json()

        # Citations list should contain the [1] marker
        assert len(body["citations"]) > 0
        first_citation = body["citations"][0]
        assert first_citation["id"] == 1
        assert first_citation["marker"] == "[1]"

        # Citation map should map "1" to at least one sentence
        assert "1" in body["citation_map"]
        assert len(body["citation_map"]["1"]) > 0

        # Sources should be populated from the mock context
        assert len(body["sources"]) > 0
        assert body["sources"][0]["doc_id"] == "doc1"
        assert body["sources"][0]["filename"] == "test.pdf"
