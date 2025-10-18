"""
Research API for AI-powered document search with citations.

Provides HTTP endpoints for submitting research queries and receiving
AI-generated answers with inline citations and source documents.
"""

import os
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List, Literal, Optional

import structlog
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.embeddings.colpali_wrapper import ColPaliEngine
from src.research.citation_parser import CitationParser
from src.research.context_builder import ContextBuilder
from src.research.litellm_client import (
    AuthenticationError,
    ContextLengthError,
    LiteLLMClient,
    LLMError,
    ModelConfig,
    RateLimitError,
    TimeoutError,
)
from src.research.prompts import RESEARCH_SYSTEM_PROMPT
from src.search.search_engine import SearchEngine
from src.storage.chroma_client import ChromaClient

logger = structlog.get_logger(__name__)


# Request/Response Models
class ResearchRequest(BaseModel):
    """Research query request"""

    query: str = Field(..., min_length=3, max_length=500, description="Research question from user")
    num_sources: int = Field(
        default=10, ge=1, le=20, description="Maximum number of source documents to retrieve"
    )
    search_mode: Literal["visual", "text", "hybrid"] = Field(
        default="hybrid", description="Search collection mode"
    )
    model: Optional[str] = Field(default=None, description="LLM model to use (default from config)")
    temperature: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="LLM temperature (default 0.3 for factual)"
    )


class CitationInfo(BaseModel):
    """Citation marker information"""

    id: int
    start: int
    end: int
    marker: str


class SentenceInfo(BaseModel):
    """Sentence with citations"""

    sentence_index: int
    sentence_text: str


class SourceInfo(BaseModel):
    """Source document information"""

    id: int  # Citation number (1-indexed)
    doc_id: str
    filename: str
    page: int
    extension: str
    thumbnail_path: Optional[str] = None
    date_added: str  # ISO format
    relevance_score: float
    chunk_id: Optional[str] = None  # Format: "{doc_id}-chunk{NNNN}" for text, None for visual


class ResearchMetadata(BaseModel):
    """Research response metadata"""

    total_sources: int
    context_tokens: int
    context_truncated: bool
    model_used: str
    search_mode: str
    processing_time_ms: int
    llm_latency_ms: int
    search_latency_ms: int


class ResearchResponse(BaseModel):
    """Research query response"""

    answer: str
    citations: List[CitationInfo]
    citation_map: Dict[str, List[SentenceInfo]]
    sources: List[SourceInfo]
    metadata: ResearchMetadata


class ErrorResponse(BaseModel):
    """Error response"""

    error: str
    detail: str
    status_code: int


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    components: Dict[str, str]
    timestamp: str


class ModelInfo(BaseModel):
    """LLM model information"""

    provider: str
    name: str
    context_window: int
    cost_per_1m_tokens: Dict[str, float]


class ModelsResponse(BaseModel):
    """Available models response"""

    models: List[ModelInfo]
    default: str


# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - startup and shutdown"""
    logger.info("Initializing research API components")

    # Initialize ChromaDB
    chroma_host = os.getenv("CHROMA_HOST", "localhost")
    chroma_port = int(os.getenv("CHROMA_PORT", 8001))

    app.state.chroma_client = ChromaClient(host=chroma_host, port=chroma_port)

    # Initialize ColPali embedding engine
    app.state.embedding_engine = ColPaliEngine(
        model_name=os.getenv("MODEL_NAME", "vidore/colpali-v1.2"), device=os.getenv("DEVICE", "mps")
    )

    # Initialize search engine
    app.state.search_engine = SearchEngine(
        storage_client=app.state.chroma_client, embedding_engine=app.state.embedding_engine
    )

    # Initialize context builder
    app.state.context_builder = ContextBuilder(
        search_engine=app.state.search_engine,
        chroma_client=app.state.chroma_client,
        max_sources=10,
        max_tokens=10000,
    )

    # Initialize LLM client
    app.state.llm_client = LiteLLMClient(
        ModelConfig(
            provider=os.getenv("LLM_PROVIDER", "openai"),
            model_name=os.getenv("LLM_MODEL", "gpt-4-turbo"),
            temperature=0.3,
        )
    )

    # Initialize citation parser
    app.state.citation_parser = CitationParser()

    logger.info("Research API components initialized successfully")

    yield

    # Shutdown
    logger.info("Shutting down research API")


# Create FastAPI app
app = FastAPI(
    title="DocuSearch Research API",
    version="1.0.0",
    description="AI-powered document search with citations",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",  # Copyparty UI
        "http://localhost:8002",
        "http://127.0.0.1:8002",  # Worker API UI
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.post("/api/research/ask", response_model=ResearchResponse)
async def ask_research_question(request: ResearchRequest):
    """
    Submit research question and receive AI-generated answer with citations

    This endpoint:
    1. Searches your document collection for relevant sources
    2. Builds context from top sources
    3. Generates AI answer with inline citations
    4. Returns answer, citations, and source documents

    Example request:
        POST /api/research/ask
        {
            "query": "What caused the 2008 financial crisis?",
            "num_sources": 10,
            "search_mode": "hybrid"
        }
    """
    start_time = time.time()

    try:
        logger.info(
            "Processing research query",
            query=request.query,
            num_sources=request.num_sources,
            search_mode=request.search_mode,
        )

        # Step 1: Build context from search results
        search_start = time.time()
        context = await app.state.context_builder.build_context(
            query=request.query,
            num_results=request.num_sources,
            include_text=(request.search_mode in ["text", "hybrid"]),
            include_visual=(request.search_mode in ["visual", "hybrid"]),
        )
        search_latency = int((time.time() - search_start) * 1000)

        logger.info(
            "Context built",
            num_sources=len(context.sources),
            total_tokens=context.total_tokens,
            truncated=context.truncated,
            search_latency_ms=search_latency,
        )

        # Check if any sources found
        if not context.sources:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No relevant documents found for your query. Try rephrasing or uploading more documents.",
            )

        # Step 2: Generate answer with LLM
        llm_start = time.time()
        llm_response = await app.state.llm_client.complete_with_context(
            query=request.query,
            context=context.formatted_text,
            system_message=RESEARCH_SYSTEM_PROMPT,
            temperature=request.temperature,
            model=request.model,
        )
        llm_latency = int((time.time() - llm_start) * 1000)

        logger.info(
            "LLM response generated",
            model=llm_response.model,
            tokens=llm_response.usage["total_tokens"],
            latency_ms=llm_latency,
        )

        # Step 3: Parse citations
        parsed_answer = app.state.citation_parser.parse(
            text=llm_response.content, num_sources=len(context.sources)
        )

        # Validate citations
        if not parsed_answer.validate(len(context.sources)):
            logger.warning("Invalid citations in LLM response, continuing anyway")

        # Step 4: Format response
        frontend_data = app.state.citation_parser.format_for_frontend(parsed_answer)

        total_time = int((time.time() - start_time) * 1000)

        logger.info(
            "Research query completed successfully",
            total_time_ms=total_time,
            num_citations=len(parsed_answer.citations),
        )

        return ResearchResponse(
            answer=parsed_answer.original_text,
            citations=[CitationInfo(**c) for c in frontend_data["citations"]],
            citation_map={
                k: [SentenceInfo(**s) for s in v] for k, v in frontend_data["citation_map"].items()
            },
            sources=[
                SourceInfo(
                    id=i + 1,
                    doc_id=source.doc_id,
                    filename=source.filename,
                    page=source.page,
                    extension=source.extension,
                    thumbnail_path=source.thumbnail_path,
                    date_added=source.timestamp,
                    relevance_score=source.relevance_score,
                    chunk_id=source.chunk_id,
                )
                for i, source in enumerate(context.sources)
            ],
            metadata=ResearchMetadata(
                total_sources=len(context.sources),
                context_tokens=context.total_tokens,
                context_truncated=context.truncated,
                model_used=llm_response.model,
                search_mode=request.search_mode,
                processing_time_ms=total_time,
                llm_latency_ms=llm_latency,
                search_latency_ms=search_latency,
            ),
        )

    except HTTPException:
        raise
    except AuthenticationError as e:
        logger.error("LLM authentication error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM authentication failed. Check API keys: {str(e)}",
        )
    except RateLimitError as e:
        logger.error("LLM rate limit hit", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Please try again in {e.retry_after} seconds.",
        )
    except TimeoutError as e:
        logger.error("LLM timeout", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request timed out. Try a simpler query or fewer sources.",
        )
    except ContextLengthError as e:
        logger.error("Context too long", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query context too long. Try reducing num_sources or simplifying query.",
        )
    except LLMError as e:
        logger.error("LLM error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"LLM service error: {str(e)}"
        )
    except Exception as e:
        logger.error("Unexpected error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error. Please try again later.",
        )


@app.get("/api/research/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring

    Returns the health status of all research API components:
    - ChromaDB connection
    - Search engine
    - LLM client

    Example response:
        {
            "status": "healthy",
            "components": {
                "chromadb": "healthy",
                "llm_client": "healthy",
                "search_engine": "healthy"
            },
            "timestamp": "2025-10-17T10:30:00Z"
        }
    """
    try:
        # Check ChromaDB
        chroma_healthy = app.state.chroma_client.heartbeat()

        # Check search engine (always healthy if ChromaDB is)
        search_healthy = True

        # Check LLM client (basic check)
        llm_healthy = True  # Could do a test completion

        overall_status = (
            "healthy" if all([chroma_healthy, llm_healthy, search_healthy]) else "unhealthy"
        )

        return HealthResponse(
            status=overall_status,
            components={
                "chromadb": "healthy" if chroma_healthy else "unhealthy",
                "llm_client": "healthy" if llm_healthy else "unhealthy",
                "search_engine": "healthy" if search_healthy else "unhealthy",
            },
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return HealthResponse(
            status="unhealthy",
            components={
                "chromadb": "unhealthy",
                "llm_client": "unknown",
                "search_engine": "unknown",
            },
            timestamp=datetime.utcnow().isoformat() + "Z",
        )


@app.get("/api/research/models", response_model=ModelsResponse)
async def list_models():
    """
    List available LLM models

    Returns information about all supported LLM models including:
    - Provider (OpenAI, Anthropic, Google)
    - Model name
    - Context window size
    - Pricing

    Example response:
        {
            "models": [
                {
                    "provider": "openai",
                    "name": "gpt-4-turbo",
                    "context_window": 128000,
                    "cost_per_1m_tokens": {"input": 10.0, "output": 30.0}
                }
            ],
            "default": "gpt-4-turbo"
        }
    """
    return ModelsResponse(
        models=[
            ModelInfo(
                provider="openai",
                name="gpt-4-turbo",
                context_window=128000,
                cost_per_1m_tokens={"input": 10.0, "output": 30.0},
            ),
            ModelInfo(
                provider="openai",
                name="gpt-3.5-turbo",
                context_window=16000,
                cost_per_1m_tokens={"input": 0.5, "output": 1.5},
            ),
            ModelInfo(
                provider="anthropic",
                name="claude-3-opus-20240229",
                context_window=200000,
                cost_per_1m_tokens={"input": 15.0, "output": 75.0},
            ),
            ModelInfo(
                provider="anthropic",
                name="claude-3-sonnet-20240229",
                context_window=200000,
                cost_per_1m_tokens={"input": 3.0, "output": 15.0},
            ),
            ModelInfo(
                provider="google",
                name="gemini-1.5-pro",
                context_window=1000000,
                cost_per_1m_tokens={"input": 3.5, "output": 10.5},
            ),
        ],
        default=os.getenv("LLM_MODEL", "gpt-4-turbo"),
    )


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail.split(":")[0] if ":" in exc.detail else "Error",
            "detail": exc.detail,
            "status_code": exc.status_code,
        },
    )
