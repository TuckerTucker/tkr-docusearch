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

from tkr_docusearch.config.urls import get_service_urls
from tkr_docusearch.config.koji_config import KojiConfig
from tkr_docusearch.research.citation_parser import CitationParser
from tkr_docusearch.research.context_builder import ContextBuilder
from tkr_docusearch.storage.koji_client import KojiClient
from tkr_docusearch.utils.url_builder import build_details_url

logger = structlog.get_logger(__name__)


# Shared models (extracted to avoid circular import with research_sessions)
from tkr_docusearch.api.research_models import (  # noqa: E402
    CitationInfo,
    RelationshipEdge,
    ResearchMetadata,
    SentenceInfo,
    SourceInfo,
)


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
    preprocessing_enabled: Optional[bool] = Field(
        default=None,
        description="Enable local LLM preprocessing (default: from LOCAL_PREPROCESS_ENABLED env var). "
        "Reduces foundation model costs by ~50% but adds 70-90s latency.",
    )
    preprocessing_strategy: Optional[Literal["compress", "filter", "synthesize"]] = Field(
        default=None,
        description="Preprocessing strategy when enabled (default: from LOCAL_PREPROCESS_STRATEGY env var)",
    )


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


class LocalInferenceRequest(BaseModel):
    """Local MLX inference request"""

    prompt: str = Field(..., min_length=1, max_length=5000, description="Prompt text for MLX model")
    max_tokens: int = Field(default=500, ge=1, le=4000, description="Maximum tokens to generate")
    temperature: float = Field(
        default=0.3, ge=0.0, le=1.0, description="Sampling temperature (0.0-1.0)"
    )
    timeout: int = Field(default=60, ge=1, le=300, description="Request timeout in seconds")


class LocalInferenceResponse(BaseModel):
    """Local MLX inference response"""

    content: str
    metadata: Dict


# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - startup and shutdown"""
    logger.info("Initializing research API components")

    # Initialize Koji database (lightweight — just SQLite/Lance, no ML model)
    koji_config = KojiConfig.from_env()
    koji_client = KojiClient(koji_config)
    koji_client.open()
    app.state.koji_client = koji_client

    # Initialize search via HTTP to worker API (no model loading needed)
    from tkr_docusearch.research.http_search_client import HttpSearchClient

    worker_url = os.getenv("WORKER_API_URL", "http://localhost:8002")
    app.state.search_engine = HttpSearchClient(worker_url=worker_url)

    # Initialize context builder
    app.state.context_builder = ContextBuilder(
        search_engine=app.state.search_engine,
        storage_client=koji_client,
        max_sources=10,
        max_tokens=10000,
    )

    # Initialize local LLM preprocessor if enabled
    preprocessing_enabled = os.getenv("LOCAL_PREPROCESS_ENABLED", "false").lower() == "true"
    if preprocessing_enabled:
        preprocessing_strategy = os.getenv("LOCAL_PREPROCESS_STRATEGY", "compress")
        logger.info(
            "Local LLM preprocessing: ENABLED",
            strategy=preprocessing_strategy,
            note="Reduces costs ~50% but adds 70-90s latency",
        )
        model_path = os.getenv("MLX_MODEL_PATH")
        if not model_path or not os.path.exists(model_path):
            logger.warning("MLX preprocessing disabled: model path not found", path=model_path)
            app.state.local_preprocessor = None
        else:
            try:
                from src.research.local_preprocessor import LocalLLMPreprocessor
                from src.research.mlx_llm_client import MLXLLMClient

                app.state.local_llm = MLXLLMClient(
                    model_path=model_path, max_tokens=int(os.getenv("MLX_MAX_TOKENS", "4000"))
                )
                app.state.local_preprocessor = LocalLLMPreprocessor(mlx_client=app.state.local_llm)
                logger.info("Local LLM preprocessor initialized", model_path=model_path)
            except ImportError as e:
                logger.warning(
                    "MLX preprocessing disabled: mlx-lm not installed. Run: pip install mlx-lm>=0.26.3",
                    error=str(e),
                )
                app.state.local_preprocessor = None
            except Exception as e:
                logger.error("Failed to initialize MLX preprocessor", error=str(e))
                app.state.local_preprocessor = None
    else:
        logger.info(
            "Local LLM preprocessing: DISABLED (default)",
            note="Set LOCAL_PREPROCESS_ENABLED=true to enable cost optimization",
        )
        app.state.local_preprocessor = None

    # Initialize citation parser
    app.state.citation_parser = CitationParser()

    # Initialize session manager and subagent client (for multi-turn research)
    from tkr_docusearch.research.session_manager import SessionManager
    from tkr_docusearch.research.subagent_client import SubagentClient

    app.state.session_manager = SessionManager()
    await app.state.session_manager.start_cleanup_task()

    if not SubagentClient.is_available():
        raise RuntimeError(
            "claude-code-sdk is required but not installed. "
            "Install with: pip install claude-code-sdk"
        )

    from tkr_docusearch.research.session_prompt import SESSION_SYSTEM_PROMPT

    app.state.subagent_client = SubagentClient(system_prompt=SESSION_SYSTEM_PROMPT)
    logger.info("Claude subagent client initialized")

    logger.info("Research API components initialized successfully")

    yield

    # Shutdown
    logger.info("Shutting down research API")
    await app.state.session_manager.stop_cleanup_task()
    if hasattr(app.state, "koji_client") and app.state.koji_client:
        app.state.koji_client.close()


# Create FastAPI app
app = FastAPI(
    title="DocuSearch Research API",
    version="1.0.0",
    description="AI-powered document search with c4288ions",
    lifespan=lifespan,
)

# CORS middleware - build allow_origins from service URLs configuration
_urls = get_service_urls()
_frontend_port = os.getenv("VITE_FRONTEND_PORT", "3333")
_allowed_origins = [
    _urls.frontend,
    f"http://127.0.0.1:{_frontend_port}",  # React Frontend localhost (dynamic)
    _urls.worker,
    "http://127.0.0.1:8002",  # Worker API localhost
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.post("/api/research/context-only")
async def get_research_context(request: ResearchRequest):
    """
    Build research context WITHOUT calling external LLM.

    For use with MCP servers where the MCP client (Claude Desktop)
    will generate the answer itself.

    This endpoint:
    1. Searches your document collection for relevant sources
    2. Builds formatted context with numbered citations
    3. Extracts image URLs for visual sources (via ngrok)
    4. Returns context + system prompt + sources (NO LLM call)

    Returns:
    - formatted_context: Numbered sources ready for LLM
    - system_prompt: The prompt to use for answer generation
    - sources: Source metadata for citation mapping
    - image_urls: HTTPS URLs for visual sources (via ngrok)
    - metadata: Token counts, search latency, vision status

    Example request:
        POST /api/research/context-only
        {
            "query": "What caused the 2008 financial crisis?",
            "num_sources": 10,
            "search_mode": "hybrid"
        }
    """
    start_time = time.time()

    try:
        logger.info(
            "Building research context (MCP mode)",
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

        # Step 2: Extract image URLs for vision (same as /ask lines 518-544)
        vision_enabled = os.getenv("RESEARCH_VISION_ENABLED", "true").lower() == "true"
        max_images = int(os.getenv("RESEARCH_MAX_IMAGES", "10"))
        ngrok_url = os.getenv("NGROK_URL", "http://localhost:8002")

        # Validate vision setup
        if vision_enabled and not os.getenv("NGROK_URL"):
            logger.warning("Vision enabled but NGROK_URL not set - falling back to text-only")
            vision_enabled = False
        elif vision_enabled and ngrok_url and not ngrok_url.startswith("https://"):
            logger.warning("NGROK_URL should be HTTPS for Claude Desktop", ngrok_url=ngrok_url)

        image_urls = []
        if vision_enabled:
            all_image_urls = context.get_visual_image_urls(base_url=ngrok_url)
            image_urls = all_image_urls[:max_images]

            logger.debug(
                "Vision support (MCP mode)",
                enabled=vision_enabled,
                visual_sources=len(all_image_urls),
                images_to_send=len(image_urls),
                base_url=ngrok_url,
            )

        # Estimate image tokens (~1000 tokens per image for vision models)
        image_tokens = len(image_urls) * 1000 if image_urls else 0

        total_time = int((time.time() - start_time) * 1000)

        logger.info(
            "Research context ready for MCP client",
            total_time_ms=total_time,
            num_sources=len(context.sources),
            visual_sources=sum(1 for s in context.sources if s.is_visual),
            text_sources=sum(1 for s in context.sources if not s.is_visual),
            images_to_send=len(image_urls),
        )

        # Return context WITHOUT calling external LLM
        return {
            "formatted_context": context.formatted_text,
            "system_prompt": app.state.subagent_client._system_prompt,
            "sources": [
                {
                    "id": i + 1,
                    "doc_id": source.doc_id,
                    "filename": source.filename,
                    "page": source.page,
                    "extension": source.extension,
                    "chunk_id": source.chunk_id,
                    "is_visual": source.is_visual,
                    "thumbnail_path": source.thumbnail_path,
                    "relevance_score": source.relevance_score,
                    "date_added": source.timestamp,
                }
                for i, source in enumerate(context.sources)
            ],
            "image_urls": image_urls,
            "metadata": {
                "total_sources": len(context.sources),
                "visual_sources_count": sum(1 for s in context.sources if s.is_visual),
                "text_sources_count": sum(1 for s in context.sources if not s.is_visual),
                "context_tokens": context.total_tokens,
                "image_tokens": image_tokens,
                "total_tokens": context.total_tokens + image_tokens,
                "context_truncated": context.truncated,
                "search_mode": request.search_mode,
                "vision_enabled": vision_enabled,
                "images_sent": len(image_urls),
                "search_latency_ms": search_latency,
                "processing_time_ms": total_time,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Context building failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build context: {str(e)}",
        )


@app.post("/api/research/local-inference", response_model=LocalInferenceResponse)
async def local_inference(request: LocalInferenceRequest):
    """
    Direct MLX local inference with Harmony formatting.

    Test endpoint for evaluating local MLX model performance in isolation.
    This bypasses search, context building, and preprocessing, but wraps
    user prompts in Harmony format for better structured responses.

    The Harmony format prevents hallucination and code generation on simple queries
    by providing clear task framing to GPT-OSS-20B.

    Example request:
        POST /api/research/local-inference
        {
            "prompt": "What is the capital of France?",
            "max_tokens": 500,
            "temperature": 0.3
        }

    Returns:
        Generated text with performance metadata (latency, tokens/sec, token counts)
    """
    start_time = time.time()

    try:
        # Check if MLX client is available
        if not hasattr(app.state, "local_llm") or app.state.local_llm is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Local MLX inference is not enabled. Set LOCAL_PREPROCESS_ENABLED=true and configure MLX_MODEL_PATH.",
            )

        logger.info(
            "Local inference request",
            prompt_length=len(request.prompt),
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        # Wrap prompt in Harmony format for better structured responses
        # This prevents hallucination and code generation on simple queries
        from src.research.prompts import PreprocessingPrompts

        formatted_prompt = PreprocessingPrompts.get_harmony_chat_prompt(request.prompt)

        logger.debug(
            "Using Harmony-formatted prompt",
            original_length=len(request.prompt),
            formatted_length=len(formatted_prompt),
        )

        # Call MLX client with formatted prompt
        response = await app.state.local_llm.complete(
            prompt=formatted_prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            timeout=request.timeout,
        )

        total_time_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "Local inference complete",
            latency_ms=response.latency_ms,
            total_time_ms=total_time_ms,
            completion_tokens=response.usage["completion_tokens"],
            tokens_per_sec=(
                round(response.usage["completion_tokens"] / (response.latency_ms / 1000), 2)
                if response.latency_ms > 0
                else 0
            ),
        )

        return LocalInferenceResponse(
            content=response.content,
            metadata={
                "model": response.model,
                "provider": response.provider,
                "latency_ms": response.latency_ms,
                "total_time_ms": total_time_ms,
                "finish_reason": response.finish_reason,
                "usage": response.usage,
            },
        )

    except TimeoutError as e:
        logger.error("Local inference timeout", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Inference request timed out: {str(e)}",
        )

    except Exception as e:
        logger.error("Local inference failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference failed: {str(e)}",
        )


@app.get("/api/research/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring

    Returns the health status of all research API components:
    - Koji connection
    - Search engine
    - Claude subagent
    """
    try:
        # Check Koji database
        koji_health = app.state.koji_client.health_check()
        koji_healthy = koji_health.get("connected", False)

        # Check search engine (always healthy if Koji is)
        search_healthy = True

        # Check subagent client
        subagent_healthy = app.state.subagent_client is not None

        overall_status = (
            "healthy" if all([koji_healthy, search_healthy, subagent_healthy]) else "unhealthy"
        )

        return HealthResponse(
            status=overall_status,
            components={
                "koji": "healthy" if koji_healthy else "unhealthy",
                "search_engine": "healthy" if search_healthy else "unhealthy",
                "subagent": "healthy" if subagent_healthy else "unhealthy",
            },
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return HealthResponse(
            status="unhealthy",
            components={
                "koji": "unhealthy",
                "search_engine": "unknown",
                "subagent": "unknown",
            },
            timestamp=datetime.utcnow().isoformat() + "Z",
        )


# Mount session router
from tkr_docusearch.api.research_sessions import router as sessions_router  # noqa: E402

app.include_router(sessions_router)


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
