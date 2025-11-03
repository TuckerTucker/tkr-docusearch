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
from src.utils.url_builder import build_details_url

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
    preprocessing_enabled: Optional[bool] = Field(
        default=None,
        description="Enable local LLM preprocessing (default: from LOCAL_PREPROCESS_ENABLED env var). "
        "Reduces foundation model costs by ~50% but adds 70-90s latency.",
    )
    preprocessing_strategy: Optional[Literal["compress", "filter", "synthesize"]] = Field(
        default=None,
        description="Preprocessing strategy when enabled (default: from LOCAL_PREPROCESS_STRATEGY env var)",
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
    details_url: Optional[str] = None  # Frontend URL to document detail view


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
    # Vision metadata
    vision_enabled: bool = False
    images_sent: int = 0
    image_tokens: int = 0
    # Preprocessing metadata
    preprocessing_enabled: bool = False
    preprocessing_strategy: Optional[str] = None
    preprocessing_latency_ms: int = 0
    original_sources_count: int = 0
    token_reduction_percent: float = 0.0
    # Debug: Full inference flow
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    formatted_context: Optional[str] = None
    image_urls_sent: Optional[List[str]] = None
    llm_request_params: Optional[Dict] = None
    llm_raw_response: Optional[str] = None
    llm_usage_details: Optional[Dict] = None
    # Debug: Preprocessing flow
    preprocessing_original_context: Optional[str] = None
    preprocessing_compressed_context: Optional[str] = None
    preprocessing_model: Optional[str] = None
    preprocessing_per_chunk_stats: Optional[List[Dict]] = None


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
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4000")),
            timeout=int(os.getenv("LLM_TIMEOUT", "30")),
        )
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
        "http://localhost:3000",
        "http://127.0.0.1:3000",  # React Frontend
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

        # Step 1.5: Preprocessing with local LLM (if enabled)
        # Request parameter overrides environment variable
        preprocessing_enabled_env = os.getenv("LOCAL_PREPROCESS_ENABLED", "false").lower() == "true"
        preprocessing_enabled = (
            request.preprocessing_enabled
            if request.preprocessing_enabled is not None
            else preprocessing_enabled_env
        )

        preprocessing_strategy = None
        preprocessing_latency_ms = 0
        original_sources_count = len(context.sources)
        token_reduction_percent = 0.0
        preprocessing_original_context = None
        preprocessing_compressed_context = None
        preprocessing_model = None
        preprocessing_per_chunk_stats = []

        # Log preprocessing status for this request
        if request.preprocessing_enabled is not None:
            logger.info(
                "Using request-level preprocessing override",
                enabled=preprocessing_enabled,
                source="request_parameter",
            )
        elif preprocessing_enabled:
            logger.debug("Using environment-level preprocessing", enabled=True, source="env_var")

        if preprocessing_enabled and app.state.local_preprocessor:
            preprocessing_start = time.time()
            # Request parameter overrides environment variable
            strategy = (
                request.preprocessing_strategy
                if request.preprocessing_strategy is not None
                else os.getenv("LOCAL_PREPROCESS_STRATEGY", "compress")
            )
            preprocessing_strategy = strategy

            # Track original token count for reduction calculation
            original_tokens = context.total_tokens

            # Capture original context for debugging
            preprocessing_original_context = context.formatted_text
            preprocessing_model = os.getenv("MLX_MODEL_NAME", "gpt-oss-20b-4bit")

            try:
                if strategy == "compress":
                    logger.info(
                        "Applying compress preprocessing strategy", sources=len(context.sources)
                    )

                    # Store per-chunk stats before compression
                    for i, source in enumerate(context.sources):
                        preprocessing_per_chunk_stats.append(
                            {
                                "chunk_id": source.chunk_id or f"{source.doc_id}-page{source.page}",
                                "doc_id": source.doc_id,
                                "page": source.page,
                                "is_visual": source.is_visual,
                                "original_length": (
                                    len(source.markdown_content) if source.markdown_content else 0
                                ),
                                "original_tokens": (
                                    len(source.markdown_content) // 4
                                    if source.markdown_content
                                    else 0
                                ),
                            }
                        )

                    context.sources = await app.state.local_preprocessor.compress_chunks(
                        query=request.query, sources=context.sources
                    )

                    # Update stats with compressed lengths
                    for i, source in enumerate(context.sources):
                        if i < len(preprocessing_per_chunk_stats):
                            preprocessing_per_chunk_stats[i]["compressed_length"] = (
                                len(source.markdown_content) if source.markdown_content else 0
                            )
                            preprocessing_per_chunk_stats[i]["compressed_tokens"] = (
                                len(source.markdown_content) // 4 if source.markdown_content else 0
                            )
                            if preprocessing_per_chunk_stats[i]["original_tokens"] > 0:
                                preprocessing_per_chunk_stats[i]["reduction_percent"] = round(
                                    (
                                        preprocessing_per_chunk_stats[i]["original_tokens"]
                                        - preprocessing_per_chunk_stats[i]["compressed_tokens"]
                                    )
                                    / preprocessing_per_chunk_stats[i]["original_tokens"]
                                    * 100,
                                    1,
                                )

                    # Rebuild formatted_text from compressed sources
                    context.formatted_text = app.state.context_builder._format_context(
                        context.sources
                    )

                    # Capture compressed context for debugging
                    preprocessing_compressed_context = context.formatted_text

                elif strategy == "filter":
                    threshold = float(os.getenv("LOCAL_PREPROCESS_THRESHOLD", "7.0"))
                    logger.info(
                        "Applying filter preprocessing strategy",
                        sources=len(context.sources),
                        threshold=threshold,
                    )
                    context.sources = await app.state.local_preprocessor.filter_by_relevance(
                        query=request.query, sources=context.sources, threshold=threshold
                    )
                    context.formatted_text = app.state.context_builder._format_context(
                        context.sources
                    )

                elif strategy == "synthesize":
                    logger.info(
                        "Applying synthesize preprocessing strategy", sources=len(context.sources)
                    )
                    synthesized_text = await app.state.local_preprocessor.synthesize_knowledge(
                        query=request.query, sources=context.sources
                    )
                    # Replace formatted_text with synthesis
                    context.formatted_text = synthesized_text

                preprocessing_latency_ms = int((time.time() - preprocessing_start) * 1000)

                # Recalculate token count after preprocessing (using heuristic: ~4 chars per token)
                new_tokens = len(context.formatted_text) // 4

                # Calculate token reduction percentage
                if original_tokens > 0:
                    token_reduction_percent = (
                        (original_tokens - new_tokens) / original_tokens
                    ) * 100.0

                logger.info(
                    "Preprocessing completed",
                    strategy=strategy,
                    latency_ms=preprocessing_latency_ms,
                    original_sources=original_sources_count,
                    final_sources=len(context.sources),
                    original_tokens=original_tokens,
                    final_tokens=new_tokens,
                    reduction_percent=round(token_reduction_percent, 2),
                )

                # Update context token count
                context.total_tokens = new_tokens

            except Exception as e:
                logger.error("Preprocessing failed, using original context", error=str(e))
                preprocessing_enabled = False
                preprocessing_strategy = None

        # Step 2: Extract image URLs for vision-capable queries
        vision_enabled = os.getenv("RESEARCH_VISION_ENABLED", "true").lower() == "true"
        max_images = int(os.getenv("RESEARCH_MAX_IMAGES", "10"))

        # Get ngrok URL from environment, fallback to localhost
        ngrok_url = os.getenv("NGROK_URL", "http://localhost:8002")

        # Validate vision setup
        if vision_enabled and not os.getenv("NGROK_URL"):
            logger.warning("Vision enabled but NGROK_URL not set - falling back to text-only")
            vision_enabled = False
        elif vision_enabled and ngrok_url and not ngrok_url.startswith("https://"):
            logger.warning("NGROK_URL should be HTTPS for security", ngrok_url=ngrok_url)

        image_urls = []
        if vision_enabled:
            # Get absolute URLs for visual sources
            all_image_urls = context.get_visual_image_urls(base_url=ngrok_url)
            # Limit to max_images
            image_urls = all_image_urls[:max_images]

            logger.debug(
                "Vision support",
                enabled=vision_enabled,
                visual_sources=len(all_image_urls),
                images_to_send=len(image_urls),
                base_url=ngrok_url,
            )

        # Estimate image token cost
        image_tokens = 0
        if image_urls:
            image_tokens = app.state.llm_client.estimate_image_tokens(len(image_urls))

        # Step 3: Generate answer with LLM (with or without vision)
        llm_start = time.time()

        # Build the full prompt for debugging
        full_user_prompt = f"{context.formatted_text}\n\nQuery: {request.query}"

        llm_response = await app.state.llm_client.complete_with_context_and_images(
            query=request.query,
            context=context.formatted_text,
            image_urls=image_urls,
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
            vision_used=len(image_urls) > 0,
            images_sent=len(image_urls),
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
                    details_url=build_details_url(
                        doc_id=source.doc_id,
                        # Audio documents don't use page navigation (use time-based chunks instead)
                        page=source.page if source.extension not in ["mp3", "wav"] else None,
                        chunk_id=source.chunk_id,
                        absolute=False,  # Relative URLs for web frontend
                    ),
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
                vision_enabled=vision_enabled,
                images_sent=len(image_urls),
                image_tokens=image_tokens,
                preprocessing_enabled=preprocessing_enabled,
                preprocessing_strategy=preprocessing_strategy,
                preprocessing_latency_ms=preprocessing_latency_ms,
                original_sources_count=original_sources_count,
                token_reduction_percent=round(token_reduction_percent, 2),
                # Debug fields
                system_prompt=RESEARCH_SYSTEM_PROMPT,
                user_prompt=full_user_prompt,
                formatted_context=context.formatted_text,
                image_urls_sent=image_urls if image_urls else None,
                llm_request_params={
                    "model": request.model or llm_response.model,
                    "temperature": request.temperature or app.state.llm_client.config.temperature,
                    "max_tokens": app.state.llm_client.config.max_tokens,
                },
                llm_raw_response=llm_response.content,
                llm_usage_details=llm_response.usage,
                # Debug: Preprocessing fields
                preprocessing_original_context=preprocessing_original_context,
                preprocessing_compressed_context=preprocessing_compressed_context,
                preprocessing_model=preprocessing_model,
                preprocessing_per_chunk_stats=(
                    preprocessing_per_chunk_stats if preprocessing_per_chunk_stats else None
                ),
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

        # Estimate image tokens
        image_tokens = 0
        if image_urls:
            image_tokens = app.state.llm_client.estimate_image_tokens(len(image_urls))

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
            "system_prompt": RESEARCH_SYSTEM_PROMPT,
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
