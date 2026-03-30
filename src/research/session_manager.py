"""
In-memory session manager for multi-turn research conversations.

Manages research sessions with TTL-based expiry and LRU eviction.
Each session tracks conversation history, source documents referenced,
and an optional Claude SDK session_id for conversation resume.
"""

import asyncio
import datetime
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, Set

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ConversationTurn:
    """A single turn in a research conversation."""

    role: Literal["user", "assistant"]
    content: str
    sources: List[dict] = field(default_factory=list)
    citations: List[dict] = field(default_factory=list)
    metadata: Optional[dict] = None
    timestamp: str = ""


@dataclass
class ResearchSession:
    """A multi-turn research session with conversation history."""

    session_id: str
    turns: List[ConversationTurn] = field(default_factory=list)
    created_at: float = 0.0
    last_active_at: float = 0.0
    all_source_doc_ids: Set[str] = field(default_factory=set)
    claude_session_id: Optional[str] = None


class SessionManager:
    """Manages in-memory research sessions with TTL-based expiry.

    Sessions are automatically expired after ``ttl_seconds`` of inactivity.
    When the number of active sessions reaches ``max_sessions``, the least
    recently used session is evicted to make room for new ones.

    Args:
        ttl_seconds: Seconds of inactivity before a session expires.
        max_sessions: Maximum number of concurrent sessions.
    """

    def __init__(self, ttl_seconds: int = 1800, max_sessions: int = 50) -> None:
        self._sessions: Dict[str, ResearchSession] = {}
        self._ttl: int = ttl_seconds
        self._max_sessions: int = max_sessions
        self._cleanup_task: Optional[asyncio.Task] = None

    def create_session(self) -> ResearchSession:
        """Create a new research session.

        Evicts the least recently used session if at capacity.

        Returns:
            The newly created ResearchSession.
        """
        if len(self._sessions) >= self._max_sessions:
            self._evict_lru()

        session_id = uuid.uuid4().hex
        now = time.time()
        session = ResearchSession(
            session_id=session_id,
            created_at=now,
            last_active_at=now,
        )
        self._sessions[session_id] = session

        logger.info(
            "session_created",
            session_id=session_id,
            active_sessions=len(self._sessions),
        )
        return session

    def get_session(self, session_id: str) -> Optional[ResearchSession]:
        """Get a session by ID, updating its last-active timestamp.

        Returns None if the session does not exist or has expired past
        the configured TTL.

        Args:
            session_id: The session identifier.

        Returns:
            The ResearchSession if found and still active, otherwise None.
        """
        session = self._sessions.get(session_id)
        if session is None:
            return None

        now = time.time()
        if now - session.last_active_at > self._ttl:
            logger.info(
                "session_expired",
                session_id=session_id,
                idle_seconds=now - session.last_active_at,
            )
            del self._sessions[session_id]
            return None

        session.last_active_at = now
        return session

    def add_turn(self, session_id: str, turn: ConversationTurn) -> None:
        """Add a conversation turn to an existing session.

        Automatically sets the turn's timestamp to the current UTC time
        in ISO format. For assistant turns that include sources, the
        referenced document IDs are tracked on the session.

        Args:
            session_id: The session identifier.
            turn: The conversation turn to append.

        Raises:
            KeyError: If the session does not exist.
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"Session not found: {session_id}")

        turn.timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        session.turns.append(turn)

        if turn.role == "assistant" and turn.sources:
            for source in turn.sources:
                doc_id = source.get("doc_id")
                if doc_id:
                    session.all_source_doc_ids.add(doc_id)

        session.last_active_at = time.time()

        logger.info(
            "turn_added",
            session_id=session_id,
            role=turn.role,
            turn_count=len(session.turns),
        )

    def set_claude_session_id(
        self, session_id: str, claude_session_id: str
    ) -> None:
        """Store the Claude SDK session_id for conversation resume.

        Args:
            session_id: The session identifier.
            claude_session_id: The Claude SDK session identifier.

        Raises:
            KeyError: If the session does not exist.
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"Session not found: {session_id}")

        session.claude_session_id = claude_session_id
        logger.info(
            "claude_session_id_set",
            session_id=session_id,
            claude_session_id=claude_session_id,
        )

    def delete_session(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: The session identifier.

        Returns:
            True if the session was found and deleted, False otherwise.
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(
                "session_deleted",
                session_id=session_id,
                active_sessions=len(self._sessions),
            )
            return True
        return False

    def get_session_count(self) -> int:
        """Return the current number of active sessions."""
        return len(self._sessions)

    def _evict_lru(self) -> None:
        """Remove the least recently used session."""
        if not self._sessions:
            return

        lru_id = min(
            self._sessions,
            key=lambda sid: self._sessions[sid].last_active_at,
        )
        logger.info(
            "session_evicted_lru",
            session_id=lru_id,
            active_sessions=len(self._sessions),
        )
        del self._sessions[lru_id]

    def _sweep_expired(self) -> int:
        """Remove all expired sessions.

        Returns:
            The number of sessions removed.
        """
        now = time.time()
        expired_ids = [
            sid
            for sid, session in self._sessions.items()
            if now - session.last_active_at > self._ttl
        ]
        for sid in expired_ids:
            del self._sessions[sid]

        if expired_ids:
            logger.info(
                "sessions_swept",
                removed=len(expired_ids),
                remaining=len(self._sessions),
            )
        return len(expired_ids)

    async def start_cleanup_task(self) -> None:
        """Start a background task that sweeps expired sessions every 5 minutes."""
        if self._cleanup_task is not None:
            logger.warning("cleanup_task_already_running")
            return

        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("cleanup_task_started", interval_seconds=300)

    async def stop_cleanup_task(self) -> None:
        """Stop the background cleanup task."""
        if self._cleanup_task is None:
            return

        self._cleanup_task.cancel()
        try:
            await self._cleanup_task
        except asyncio.CancelledError:
            pass
        self._cleanup_task = None
        logger.info("cleanup_task_stopped")

    async def _cleanup_loop(self) -> None:
        """Background loop that sweeps expired sessions periodically."""
        try:
            while True:
                await asyncio.sleep(300)
                self._sweep_expired()
        except asyncio.CancelledError:
            logger.info("cleanup_loop_cancelled")
            raise
