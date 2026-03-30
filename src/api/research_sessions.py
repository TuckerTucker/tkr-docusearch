"""
Session-based research API endpoints.

Provides multi-turn research conversations backed by Claude Code subagents.
"""

import datetime
import time
from typing import Dict, List, Literal, Optional

import structlog
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from tkr_docusearch.api.research_models import (
    CitationInfo,
    ResearchMetadata,
    SentenceInfo,
    SourceInfo,
)
from tkr_docusearch.research.session_manager import ConversationTurn
from tkr_docusearch.research.subagent_client import SubagentError
from tkr_docusearch.utils.url_builder import build_details_url

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/research/sessions", tags=["research-sessions"])


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class SessionCreateResponse(BaseModel):
    """Response for session creation."""

    session_id: str
    created_at: str  # ISO format


class SessionAskRequest(BaseModel):
    """Request for a session research turn."""

    session_id: Optional[str] = None  # None = auto-create
    query: str = Field(..., min_length=3, max_length=500)
    num_sources: int = Field(default=10, ge=1, le=20)
    search_mode: Literal["visual", "text", "hybrid"] = "hybrid"


class SessionAskResponse(BaseModel):
    """Response for a session research turn."""

    session_id: str
    turn: int  # 1-indexed turn number (counts only assistant turns)
    answer: str
    citations: List[CitationInfo]
    citation_map: Dict[str, List[SentenceInfo]]
    sources: List[SourceInfo]
    metadata: ResearchMetadata


class SessionHistoryTurn(BaseModel):
    """A single turn in session history."""

    role: Literal["user", "assistant"]
    content: str
    sources: List[SourceInfo] = []
    timestamp: str


class SessionHistoryResponse(BaseModel):
    """Full session history."""

    session_id: str
    turns: List[SessionHistoryTurn]
    created_at: str
    total_turns: int


class SessionDeleteResponse(BaseModel):
    """Response for session deletion."""

    deleted: bool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _check_subagent(request: Request) -> None:
    """Raise 503 if the Claude subagent client is not available.

    Args:
        request: The incoming FastAPI request.

    Raises:
        HTTPException: 503 when the subagent client is None.
    """
    if request.app.state.subagent_client is None:
        raise HTTPException(
            status_code=503,
            detail="Claude subagent not available. Install claude-code-sdk.",
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/create", response_model=SessionCreateResponse)
async def create_session(request: Request) -> SessionCreateResponse:
    """Create a new multi-turn research session.

    Returns:
        SessionCreateResponse with the new session_id and created_at timestamp.
    """
    _check_subagent(request)

    session_manager = request.app.state.session_manager
    session = session_manager.create_session()

    created_at = datetime.datetime.fromtimestamp(
        session.created_at, tz=datetime.timezone.utc
    ).isoformat()

    logger.info("session_endpoint.create", session_id=session.session_id)

    return SessionCreateResponse(
        session_id=session.session_id,
        created_at=created_at,
    )


@router.post("/ask", response_model=SessionAskResponse)
async def session_ask(
    request: Request,
    body: SessionAskRequest,
) -> SessionAskResponse:
    """Submit a research question within a session.

    Searches documents, invokes the Claude subagent with conversation context,
    parses citations, and records the turn in the session history.

    Args:
        request: The incoming FastAPI request.
        body: The research question and parameters.

    Returns:
        SessionAskResponse with the answer, citations, sources, and metadata.
    """
    _check_subagent(request)

    overall_start = time.time()
    session_manager = request.app.state.session_manager
    subagent = request.app.state.subagent_client
    context_builder = request.app.state.context_builder
    citation_parser = request.app.state.citation_parser

    try:
        # 1. Get or create session -------------------------------------------
        session = None
        if body.session_id:
            session = session_manager.get_session(body.session_id)
            if not session:
                raise HTTPException(
                    status_code=404,
                    detail=f"Session not found or expired: {body.session_id}",
                )
        if not session:
            session = session_manager.create_session()

        logger.info(
            "session_endpoint.ask.start",
            session_id=session.session_id,
            query_length=len(body.query),
            search_mode=body.search_mode,
        )

        # 2. Record user turn ------------------------------------------------
        user_turn = ConversationTurn(role="user", content=body.query)
        session_manager.add_turn(session.session_id, user_turn)

        # 3. Search & build context ------------------------------------------
        search_start = time.time()
        context = await context_builder.build_context(
            query=body.query,
            num_results=body.num_sources,
            include_text=body.search_mode in ("text", "hybrid"),
            include_visual=body.search_mode in ("visual", "hybrid"),
        )
        search_latency = int((time.time() - search_start) * 1000)

        # 4. Call subagent ---------------------------------------------------
        llm_start = time.time()
        subagent_response = await subagent.research_turn(
            query=body.query,
            formatted_context=context.formatted_text,
            resume_session_id=session.claude_session_id,
        )
        llm_latency = int((time.time() - llm_start) * 1000)

        # 5. Store SDK session_id for future resume --------------------------
        if subagent_response.session_id:
            session_manager.set_claude_session_id(
                session.session_id, subagent_response.session_id
            )

        # 6. Parse citations -------------------------------------------------
        parsed = citation_parser.parse(
            text=subagent_response.content,
            num_sources=len(context.sources),
        )

        # 7. Build source list -----------------------------------------------
        sources: List[SourceInfo] = []
        for idx, src in enumerate(context.sources):
            source_info = SourceInfo(
                id=idx + 1,
                doc_id=src.doc_id,
                filename=src.filename,
                page=src.page,
                extension=src.extension,
                thumbnail_path=src.thumbnail_path,
                date_added=src.timestamp or "",
                relevance_score=src.relevance_score,
                chunk_id=src.chunk_id,
                details_url=build_details_url(
                    doc_id=src.doc_id,
                    page=src.page if src.extension not in ("mp3", "wav") else None,
                    chunk_id=src.chunk_id,
                    absolute=False,
                ),
                related_doc_ids=getattr(src, "related_doc_ids", []),
                relationship_types=getattr(src, "relationship_types", []),
                cluster_id=getattr(src, "cluster_id", None),
            )
            sources.append(source_info)

        # 8. Build citations list --------------------------------------------
        citations = [
            CitationInfo(
                id=c.citation_id,
                start=c.start_pos,
                end=c.end_pos,
                marker=c.marker,
            )
            for c in parsed.citations
        ]

        # 9. Build citation_map ----------------------------------------------
        citation_map: Dict[str, List[SentenceInfo]] = {}
        for cid, sentences in parsed.citation_to_sentences.items():
            citation_map[str(cid)] = [
                SentenceInfo(
                    sentence_index=parsed.sentences.index(s),
                    sentence_text=s.text,
                )
                for s in sentences
            ]

        # 10. Build metadata -------------------------------------------------
        processing_time = int((time.time() - overall_start) * 1000)
        metadata = ResearchMetadata(
            total_sources=len(context.sources),
            context_tokens=context.total_tokens,
            context_truncated=context.truncated,
            model_used=subagent_response.model or "claude-subagent",
            search_mode=body.search_mode,
            processing_time_ms=processing_time,
            llm_latency_ms=llm_latency,
            search_latency_ms=search_latency,
        )

        # 11. Record assistant turn ------------------------------------------
        assistant_turn = ConversationTurn(
            role="assistant",
            content=parsed.original_text,
            sources=[s.model_dump() for s in sources],
            citations=[c.model_dump() for c in citations],
            metadata=metadata.model_dump(),
        )
        session_manager.add_turn(session.session_id, assistant_turn)

        # 12. Count assistant turns for turn number --------------------------
        assistant_turn_count = sum(
            1 for t in session.turns if t.role == "assistant"
        )

        logger.info(
            "session_endpoint.ask.done",
            session_id=session.session_id,
            turn=assistant_turn_count,
            num_sources=len(sources),
            processing_time_ms=processing_time,
        )

        return SessionAskResponse(
            session_id=session.session_id,
            turn=assistant_turn_count,
            answer=parsed.original_text,
            citations=citations,
            citation_map=citation_map,
            sources=sources,
            metadata=metadata,
        )

    except HTTPException:
        raise
    except SubagentError as exc:
        logger.error(
            "session_endpoint.ask.subagent_error",
            session_id=body.session_id,
            error=str(exc),
        )
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except KeyError as exc:
        logger.warning(
            "session_endpoint.ask.session_not_found",
            error=str(exc),
        )
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(
            "session_endpoint.ask.unexpected_error",
            session_id=body.session_id,
            error=str(exc),
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Internal error: {exc}"
        ) from exc


@router.get("/{session_id}", response_model=SessionHistoryResponse)
async def get_session_history(
    request: Request,
    session_id: str,
) -> SessionHistoryResponse:
    """Retrieve the full conversation history for a session.

    Args:
        request: The incoming FastAPI request.
        session_id: The session identifier.

    Returns:
        SessionHistoryResponse with all turns and metadata.
    """
    _check_subagent(request)

    session_manager = request.app.state.session_manager
    session = session_manager.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session not found or expired: {session_id}",
        )

    turns: List[SessionHistoryTurn] = []
    for turn in session.turns:
        sources: List[SourceInfo] = []
        if turn.role == "assistant" and turn.sources:
            sources = [SourceInfo(**s) for s in turn.sources]

        turns.append(
            SessionHistoryTurn(
                role=turn.role,
                content=turn.content,
                sources=sources,
                timestamp=turn.timestamp,
            )
        )

    created_at = datetime.datetime.fromtimestamp(
        session.created_at, tz=datetime.timezone.utc
    ).isoformat()

    logger.info(
        "session_endpoint.get_history",
        session_id=session_id,
        total_turns=len(turns),
    )

    return SessionHistoryResponse(
        session_id=session.session_id,
        turns=turns,
        created_at=created_at,
        total_turns=len(turns),
    )


@router.delete("/{session_id}", response_model=SessionDeleteResponse)
async def delete_session(
    request: Request,
    session_id: str,
) -> SessionDeleteResponse:
    """Delete a research session and its conversation history.

    Args:
        request: The incoming FastAPI request.
        session_id: The session identifier.

    Returns:
        SessionDeleteResponse indicating whether the session was found and deleted.
    """
    _check_subagent(request)

    session_manager = request.app.state.session_manager
    deleted = session_manager.delete_session(session_id)

    logger.info(
        "session_endpoint.delete",
        session_id=session_id,
        deleted=deleted,
    )

    return SessionDeleteResponse(deleted=deleted)
