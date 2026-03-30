"""
Integration tests for the research sessions API router.

Tests endpoint flows using FastAPI TestClient with real SessionManager
and CitationParser, and mocked SubagentClient and ContextBuilder.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

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
# Fixtures
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
    content: str = "The answer is in the document [[1]](http://localhost:3333/details/doc1?page=1).",
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


@pytest.fixture
def test_app() -> FastAPI:
    """Create a test FastAPI app with the research sessions router.

    Sets up app.state with:
    - real SessionManager
    - mock SubagentClient
    - mock ContextBuilder
    - real CitationParser
    """
    app = FastAPI()
    app.include_router(router)

    # Real components
    app.state.session_manager = SessionManager(ttl_seconds=300)
    app.state.citation_parser = CitationParser()

    # Mock subagent
    mock_subagent = AsyncMock()
    mock_subagent.research_turn = AsyncMock(
        return_value=_build_mock_subagent_response()
    )
    app.state.subagent_client = mock_subagent

    # Mock context builder
    mock_context_builder = AsyncMock()
    mock_context_builder.build_context = AsyncMock(
        return_value=_build_mock_context()
    )
    app.state.context_builder = mock_context_builder

    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    """FastAPI TestClient for the test app."""
    return TestClient(test_app)


@pytest.fixture
def test_app_no_subagent() -> FastAPI:
    """Test app with subagent_client set to None (unavailable)."""
    app = FastAPI()
    app.include_router(router)

    app.state.session_manager = SessionManager()
    app.state.citation_parser = CitationParser()
    app.state.subagent_client = None
    app.state.context_builder = AsyncMock()

    return app


@pytest.fixture
def client_no_subagent(test_app_no_subagent: FastAPI) -> TestClient:
    """TestClient with subagent unavailable."""
    return TestClient(test_app_no_subagent)


# ---------------------------------------------------------------------------
# POST /api/research/sessions/create
# ---------------------------------------------------------------------------


class TestCreateSession:
    """Tests for the create session endpoint."""

    def test_returns_session_id(self, client: TestClient) -> None:
        """POST /create returns a session_id and created_at."""
        response = client.post("/api/research/sessions/create")

        assert response.status_code == 200
        body = response.json()
        assert "session_id" in body
        assert len(body["session_id"]) == 32  # uuid4 hex
        assert "created_at" in body
        assert "T" in body["created_at"]  # ISO format

    def test_returns_503_when_subagent_unavailable(
        self, client_no_subagent: TestClient
    ) -> None:
        """POST /create returns 503 when subagent_client is None."""
        response = client_no_subagent.post("/api/research/sessions/create")
        assert response.status_code == 503
        assert "subagent" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# POST /api/research/sessions/ask
# ---------------------------------------------------------------------------


class TestSessionAsk:
    """Tests for the ask endpoint."""

    def test_ask_without_session_id_creates_session(
        self, client: TestClient
    ) -> None:
        """POST /ask with no session_id auto-creates a session."""
        response = client.post(
            "/api/research/sessions/ask",
            json={"query": "What is machine learning?"},
        )

        assert response.status_code == 200
        body = response.json()
        assert "session_id" in body
        assert len(body["session_id"]) == 32
        assert body["turn"] == 1
        assert "answer" in body
        assert body["answer"] != ""

    def test_ask_with_existing_session_id(
        self, client: TestClient, test_app: FastAPI
    ) -> None:
        """POST /ask with existing session_id returns turn 2 on follow-up."""
        # First: create a session via /create
        create_resp = client.post("/api/research/sessions/create")
        session_id = create_resp.json()["session_id"]

        # First ask
        resp1 = client.post(
            "/api/research/sessions/ask",
            json={"query": "What is AI?", "session_id": session_id},
        )
        assert resp1.status_code == 200
        assert resp1.json()["turn"] == 1

        # Second ask (follow-up)
        resp2 = client.post(
            "/api/research/sessions/ask",
            json={
                "query": "Tell me more about that",
                "session_id": session_id,
            },
        )
        assert resp2.status_code == 200
        assert resp2.json()["turn"] == 2
        assert resp2.json()["session_id"] == session_id

    def test_ask_with_expired_session_returns_404(
        self, test_app: FastAPI
    ) -> None:
        """POST /ask with an expired session_id returns 404."""
        # Use a very short TTL
        test_app.state.session_manager = SessionManager(ttl_seconds=0)
        local_client = TestClient(test_app)

        # Create session
        create_resp = local_client.post("/api/research/sessions/create")
        session_id = create_resp.json()["session_id"]

        # Wait for expiry (TTL=0, any positive time means expired)
        import time

        time.sleep(0.05)

        # Ask with expired session
        resp = local_client.post(
            "/api/research/sessions/ask",
            json={"query": "Follow-up question", "session_id": session_id},
        )
        assert resp.status_code == 404
        assert "expired" in resp.json()["detail"].lower() or "not found" in resp.json()["detail"].lower()

    def test_ask_response_has_citations(self, client: TestClient) -> None:
        """POST /ask response includes parsed citations."""
        response = client.post(
            "/api/research/sessions/ask",
            json={"query": "What is in the document?"},
        )

        assert response.status_code == 200
        body = response.json()
        assert "citations" in body
        assert "citation_map" in body
        assert "sources" in body
        assert len(body["sources"]) > 0

    def test_ask_response_has_metadata(self, client: TestClient) -> None:
        """POST /ask response includes research metadata."""
        response = client.post(
            "/api/research/sessions/ask",
            json={"query": "What does the report say?"},
        )

        assert response.status_code == 200
        body = response.json()
        assert "metadata" in body
        meta = body["metadata"]
        assert "total_sources" in meta
        assert "processing_time_ms" in meta
        assert "model_used" in meta

    def test_ask_returns_503_when_subagent_unavailable(
        self, client_no_subagent: TestClient
    ) -> None:
        """POST /ask returns 503 when subagent_client is None."""
        response = client_no_subagent.post(
            "/api/research/sessions/ask",
            json={"query": "Hello?"},
        )
        assert response.status_code == 503

    def test_ask_validates_query_min_length(self, client: TestClient) -> None:
        """POST /ask rejects queries shorter than 3 characters."""
        response = client.post(
            "/api/research/sessions/ask",
            json={"query": "Hi"},
        )
        assert response.status_code == 422  # Validation error


# ---------------------------------------------------------------------------
# GET /api/research/sessions/{session_id}
# ---------------------------------------------------------------------------


class TestGetSessionHistory:
    """Tests for the get session history endpoint."""

    def test_returns_conversation_history(
        self, client: TestClient
    ) -> None:
        """GET /{session_id} returns the full conversation history."""
        # Create a session and ask a question
        create_resp = client.post("/api/research/sessions/create")
        session_id = create_resp.json()["session_id"]

        client.post(
            "/api/research/sessions/ask",
            json={"query": "What is AI?", "session_id": session_id},
        )

        # Retrieve history
        history_resp = client.get(
            f"/api/research/sessions/{session_id}"
        )

        assert history_resp.status_code == 200
        body = history_resp.json()
        assert body["session_id"] == session_id
        assert body["total_turns"] == 2  # user + assistant
        assert len(body["turns"]) == 2
        assert body["turns"][0]["role"] == "user"
        assert body["turns"][1]["role"] == "assistant"
        assert "created_at" in body

    def test_nonexistent_session_returns_404(
        self, client: TestClient
    ) -> None:
        """GET /{session_id} returns 404 for unknown session."""
        response = client.get(
            "/api/research/sessions/nonexistent-id-12345"
        )
        assert response.status_code == 404

    def test_returns_503_when_subagent_unavailable(
        self, client_no_subagent: TestClient
    ) -> None:
        """GET /{session_id} returns 503 when subagent_client is None."""
        response = client_no_subagent.get(
            "/api/research/sessions/some-id"
        )
        assert response.status_code == 503


# ---------------------------------------------------------------------------
# DELETE /api/research/sessions/{session_id}
# ---------------------------------------------------------------------------


class TestDeleteSession:
    """Tests for the delete session endpoint."""

    def test_deletes_existing_session(self, client: TestClient) -> None:
        """DELETE /{session_id} deletes the session and returns deleted=True."""
        # Create
        create_resp = client.post("/api/research/sessions/create")
        session_id = create_resp.json()["session_id"]

        # Delete
        delete_resp = client.delete(
            f"/api/research/sessions/{session_id}"
        )
        assert delete_resp.status_code == 200
        assert delete_resp.json()["deleted"] is True

        # Verify it's gone
        get_resp = client.get(
            f"/api/research/sessions/{session_id}"
        )
        assert get_resp.status_code == 404

    def test_delete_nonexistent_returns_false(
        self, client: TestClient
    ) -> None:
        """DELETE /{session_id} returns deleted=False for unknown session."""
        response = client.delete(
            "/api/research/sessions/nonexistent-id-12345"
        )
        assert response.status_code == 200
        assert response.json()["deleted"] is False

    def test_returns_503_when_subagent_unavailable(
        self, client_no_subagent: TestClient
    ) -> None:
        """DELETE /{session_id} returns 503 when subagent_client is None."""
        response = client_no_subagent.delete(
            "/api/research/sessions/some-id"
        )
        assert response.status_code == 503
