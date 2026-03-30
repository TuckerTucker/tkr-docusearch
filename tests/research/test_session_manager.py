"""
Unit tests for SessionManager.

Tests session lifecycle, TTL-based expiry, LRU eviction,
conversation turn management, and background cleanup.
"""

import asyncio
import time

import pytest

from tkr_docusearch.research.session_manager import (
    ConversationTurn,
    ResearchSession,
    SessionManager,
)


# ---------------------------------------------------------------------------
# create_session
# ---------------------------------------------------------------------------


class TestCreateSession:
    """Tests for SessionManager.create_session."""

    def test_returns_valid_session(self) -> None:
        """create_session returns a ResearchSession with UUID, timestamps."""
        manager = SessionManager()
        session = manager.create_session()

        assert isinstance(session, ResearchSession)
        assert len(session.session_id) == 32  # uuid4.hex is 32 hex chars
        assert session.created_at > 0
        assert session.last_active_at > 0
        assert session.turns == []
        assert session.all_source_doc_ids == set()
        assert session.claude_session_id is None

    def test_session_ids_are_unique(self) -> None:
        """Each session gets a unique ID."""
        manager = SessionManager()
        s1 = manager.create_session()
        s2 = manager.create_session()

        assert s1.session_id != s2.session_id

    def test_session_count_increments(self) -> None:
        """Session count increases with each creation."""
        manager = SessionManager()
        assert manager.get_session_count() == 0

        manager.create_session()
        assert manager.get_session_count() == 1

        manager.create_session()
        assert manager.get_session_count() == 2

    def test_lru_eviction_at_capacity(self) -> None:
        """When at max_sessions, creating a new session evicts the oldest."""
        manager = SessionManager(max_sessions=2)

        s1 = manager.create_session()
        s1_id = s1.session_id

        # Nudge time forward so s1 is definitively the oldest
        s1.last_active_at -= 10

        s2 = manager.create_session()
        assert manager.get_session_count() == 2

        # Creating a third should evict s1 (oldest last_active_at)
        s3 = manager.create_session()
        assert manager.get_session_count() == 2

        assert manager.get_session(s1_id) is None
        assert manager.get_session(s2.session_id) is not None
        assert manager.get_session(s3.session_id) is not None


# ---------------------------------------------------------------------------
# get_session
# ---------------------------------------------------------------------------


class TestGetSession:
    """Tests for SessionManager.get_session."""

    def test_returns_session_and_updates_last_active(self) -> None:
        """get_session returns the session and bumps last_active_at."""
        manager = SessionManager()
        session = manager.create_session()
        original_active = session.last_active_at

        # Small delay so timestamp can differ
        time.sleep(0.01)

        retrieved = manager.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.session_id == session.session_id
        assert retrieved.last_active_at >= original_active

    def test_returns_none_for_nonexistent(self) -> None:
        """get_session returns None for an unknown session ID."""
        manager = SessionManager()
        assert manager.get_session("nonexistent-id") is None

    def test_returns_none_for_expired_session(self) -> None:
        """get_session returns None after the session TTL has elapsed."""
        manager = SessionManager(ttl_seconds=0)
        session = manager.create_session()

        # TTL is 0, so any positive elapsed time means expired
        time.sleep(0.05)

        assert manager.get_session(session.session_id) is None
        # Session should also be removed from the store
        assert manager.get_session_count() == 0


# ---------------------------------------------------------------------------
# add_turn
# ---------------------------------------------------------------------------


class TestAddTurn:
    """Tests for SessionManager.add_turn."""

    def test_appends_turn_with_timestamp(self) -> None:
        """add_turn appends the turn and sets an ISO timestamp."""
        manager = SessionManager()
        session = manager.create_session()

        turn = ConversationTurn(role="user", content="What is AI?")
        manager.add_turn(session.session_id, turn)

        assert len(session.turns) == 1
        assert session.turns[0].content == "What is AI?"
        assert session.turns[0].role == "user"
        assert turn.timestamp != ""
        assert "T" in turn.timestamp  # ISO format contains 'T'

    def test_multiple_turns_appended(self) -> None:
        """Multiple turns are appended in order."""
        manager = SessionManager()
        session = manager.create_session()

        t1 = ConversationTurn(role="user", content="Q1")
        t2 = ConversationTurn(role="assistant", content="A1")
        manager.add_turn(session.session_id, t1)
        manager.add_turn(session.session_id, t2)

        assert len(session.turns) == 2
        assert session.turns[0].role == "user"
        assert session.turns[1].role == "assistant"

    def test_tracks_doc_ids_from_assistant_sources(self) -> None:
        """Assistant turns with sources populate all_source_doc_ids."""
        manager = SessionManager()
        session = manager.create_session()

        turn = ConversationTurn(
            role="assistant",
            content="Answer",
            sources=[
                {"doc_id": "doc1", "filename": "a.pdf"},
                {"doc_id": "doc2", "filename": "b.pdf"},
                {"doc_id": "doc1", "filename": "a.pdf"},  # duplicate
            ],
        )
        manager.add_turn(session.session_id, turn)

        assert session.all_source_doc_ids == {"doc1", "doc2"}

    def test_user_turn_sources_not_tracked(self) -> None:
        """User turns do not populate all_source_doc_ids even if sources present."""
        manager = SessionManager()
        session = manager.create_session()

        turn = ConversationTurn(
            role="user",
            content="Q",
            sources=[{"doc_id": "doc1"}],
        )
        manager.add_turn(session.session_id, turn)

        assert session.all_source_doc_ids == set()

    def test_raises_key_error_for_missing_session(self) -> None:
        """add_turn raises KeyError for a non-existent session."""
        manager = SessionManager()
        turn = ConversationTurn(role="user", content="Q")

        with pytest.raises(KeyError, match="Session not found"):
            manager.add_turn("nonexistent-id", turn)


# ---------------------------------------------------------------------------
# set_claude_session_id
# ---------------------------------------------------------------------------


class TestSetClaudeSessionId:
    """Tests for SessionManager.set_claude_session_id."""

    def test_stores_claude_session_id(self) -> None:
        """set_claude_session_id persists the SDK session ID."""
        manager = SessionManager()
        session = manager.create_session()

        manager.set_claude_session_id(session.session_id, "sdk-abc-123")
        assert session.claude_session_id == "sdk-abc-123"

    def test_overwrites_previous_value(self) -> None:
        """Calling set_claude_session_id again overwrites the old value."""
        manager = SessionManager()
        session = manager.create_session()

        manager.set_claude_session_id(session.session_id, "old-id")
        manager.set_claude_session_id(session.session_id, "new-id")
        assert session.claude_session_id == "new-id"

    def test_raises_key_error_for_missing_session(self) -> None:
        """set_claude_session_id raises KeyError for non-existent session."""
        manager = SessionManager()

        with pytest.raises(KeyError, match="Session not found"):
            manager.set_claude_session_id("nonexistent-id", "sdk-123")


# ---------------------------------------------------------------------------
# delete_session
# ---------------------------------------------------------------------------


class TestDeleteSession:
    """Tests for SessionManager.delete_session."""

    def test_returns_true_when_found(self) -> None:
        """delete_session returns True and removes the session."""
        manager = SessionManager()
        session = manager.create_session()

        assert manager.delete_session(session.session_id) is True
        assert manager.get_session_count() == 0

    def test_returns_false_when_not_found(self) -> None:
        """delete_session returns False for non-existent session."""
        manager = SessionManager()

        assert manager.delete_session("nonexistent-id") is False


# ---------------------------------------------------------------------------
# _evict_lru
# ---------------------------------------------------------------------------


class TestEvictLru:
    """Tests for SessionManager._evict_lru."""

    def test_removes_oldest_session(self) -> None:
        """_evict_lru removes the session with the oldest last_active_at."""
        manager = SessionManager()

        s1 = manager.create_session()
        s1.last_active_at = 100.0

        s2 = manager.create_session()
        s2.last_active_at = 200.0

        s3 = manager.create_session()
        s3.last_active_at = 150.0

        manager._evict_lru()

        # s1 had the lowest last_active_at, should be removed
        assert manager.get_session_count() == 2
        assert manager._sessions.get(s1.session_id) is None
        assert manager._sessions.get(s2.session_id) is not None
        assert manager._sessions.get(s3.session_id) is not None

    def test_noop_on_empty_sessions(self) -> None:
        """_evict_lru does nothing when there are no sessions."""
        manager = SessionManager()
        manager._evict_lru()  # Should not raise
        assert manager.get_session_count() == 0


# ---------------------------------------------------------------------------
# _sweep_expired
# ---------------------------------------------------------------------------


class TestSweepExpired:
    """Tests for SessionManager._sweep_expired."""

    def test_removes_expired_sessions(self) -> None:
        """_sweep_expired removes sessions that have exceeded TTL."""
        manager = SessionManager(ttl_seconds=1)

        s1 = manager.create_session()
        s1.last_active_at = time.time() - 100  # Way past TTL

        s2 = manager.create_session()
        # s2 is fresh, not expired

        removed = manager._sweep_expired()

        assert removed == 1
        assert manager.get_session_count() == 1
        assert manager._sessions.get(s1.session_id) is None
        assert manager._sessions.get(s2.session_id) is not None

    def test_returns_zero_when_none_expired(self) -> None:
        """_sweep_expired returns 0 when no sessions are expired."""
        manager = SessionManager(ttl_seconds=3600)
        manager.create_session()
        manager.create_session()

        removed = manager._sweep_expired()
        assert removed == 0
        assert manager.get_session_count() == 2


# ---------------------------------------------------------------------------
# Cleanup task lifecycle
# ---------------------------------------------------------------------------


class TestCleanupTask:
    """Tests for start_cleanup_task / stop_cleanup_task lifecycle."""

    async def test_start_and_stop(self) -> None:
        """Cleanup task can be started and stopped without error."""
        manager = SessionManager()

        await manager.start_cleanup_task()
        assert manager._cleanup_task is not None
        assert not manager._cleanup_task.done()

        await manager.stop_cleanup_task()
        assert manager._cleanup_task is None

    async def test_start_idempotent(self) -> None:
        """Calling start_cleanup_task twice does not create a second task."""
        manager = SessionManager()

        await manager.start_cleanup_task()
        first_task = manager._cleanup_task

        await manager.start_cleanup_task()
        assert manager._cleanup_task is first_task

        await manager.stop_cleanup_task()

    async def test_stop_idempotent(self) -> None:
        """Calling stop_cleanup_task when no task is running is a no-op."""
        manager = SessionManager()
        await manager.stop_cleanup_task()  # Should not raise
        assert manager._cleanup_task is None
