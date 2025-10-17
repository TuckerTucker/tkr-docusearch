# Research API Interface Contract

**Provider:** Agent 4 - Research API
**Consumers:** Agent 6 - Research Page Frontend
**File:** `src/api/research.py`
**Status:** Wave 2 Integration Layer
**Version:** 1.0
**Last Updated:** 2025-10-17

---

## Overview

The Research API provides HTTP endpoints for submitting research queries, retrieving AI-generated answers with inline citations, and managing research sessions. It orchestrates the context builder, LiteLLM client, and citation parser to deliver complete research responses.

---

## API Endpoints

### POST /api/research/ask

Submit a research question and receive an AI-generated answer with citations.

#### Request

```http
POST /api/research/ask HTTP/1.1
Content-Type: application/json

{
  "query": "What caused the 2008 financial crisis?",
  "num_sources": 10,
  "search_mode": "hybrid",
  "model": "gpt-4-turbo",
  "temperature": 0.3
}
```

**Request Body Schema:**

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal

class ResearchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Research question from user"
    )
    num_sources: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Maximum number of source documents to retrieve"
    )
    search_mode: Literal["visual", "text", "hybrid"] = Field(
        default="hybrid",
        description="Search collection mode"
    )
    model: Optional[str] = Field(
        default=None,
        description="LLM model to use (default from config)"
    )
    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="LLM temperature (default 0.3 for factual)"
    )
```

#### Response (Success)

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "answer": "The 2008 financial crisis was caused by a combination of factors [1]. Subprime mortgages played a key role [2][3]...",
  "citations": [
    {
      "id": 1,
      "start": 65,
      "end": 68,
      "marker": "[1]"
    },
    {
      "id": 2,
      "start": 102,
      "end": 105,
      "marker": "[2]"
    }
  ],
  "citation_map": {
    "1": [
      {
        "sentence_index": 0,
        "sentence_text": "The 2008 financial crisis was caused by a combination of factors [1]."
      }
    ],
    "2": [
      {
        "sentence_index": 1,
        "sentence_text": "Subprime mortgages played a key role [2][3]."
      }
    ]
  },
  "sources": [
    {
      "id": 1,
      "doc_id": "abc123",
      "filename": "crisis-report.pdf",
      "page": 3,
      "extension": "pdf",
      "thumbnail_path": "/data/images/abc123_page_003_thumb.jpg",
      "date_added": "2025-10-15T14:30:00Z",
      "relevance_score": 0.95
    },
    {
      "id": 2,
      "doc_id": "def456",
      "filename": "subprime-analysis.pdf",
      "page": 12,
      "extension": "pdf",
      "thumbnail_path": "/data/images/def456_page_012_thumb.jpg",
      "date_added": "2025-10-14T09:15:00Z",
      "relevance_score": 0.88
    }
  ],
  "metadata": {
    "total_sources": 10,
    "context_tokens": 8500,
    "context_truncated": false,
    "model_used": "gpt-4-turbo",
    "search_mode": "hybrid",
    "processing_time_ms": 2340,
    "llm_latency_ms": 1850,
    "search_latency_ms": 450
  }
}
```

**Response Body Schema:**

```python
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class CitationInfo(BaseModel):
    id: int
    start: int
    end: int
    marker: str

class SentenceInfo(BaseModel):
    sentence_index: int
    sentence_text: str

class SourceInfo(BaseModel):
    id: int  # Citation number (1-indexed)
    doc_id: str
    filename: str
    page: int
    extension: str
    thumbnail_path: Optional[str] = None
    date_added: str  # ISO format
    relevance_score: float

class ResearchMetadata(BaseModel):
    total_sources: int
    context_tokens: int
    context_truncated: bool
    model_used: str
    search_mode: str
    processing_time_ms: int
    llm_latency_ms: int
    search_latency_ms: int

class ResearchResponse(BaseModel):
    answer: str
    citations: List[CitationInfo]
    citation_map: Dict[str, List[SentenceInfo]]
    sources: List[SourceInfo]
    metadata: ResearchMetadata
```

#### Response (Error)

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": "Invalid request",
  "detail": "Query must be at least 3 characters",
  "status_code": 400
}
```

**Error Response Schema:**

```python
class ErrorResponse(BaseModel):
    error: str  # Error type
    detail: str  # Detailed message
    status_code: int
```

**Error Codes:**

- `400` - Invalid request (validation failed)
- `404` - No documents found for query
- `429` - Rate limit exceeded (too many requests)
- `500` - Internal server error (LLM failure, database error)
- `503` - Service unavailable (ChromaDB down)

---

### GET /api/research/health

Health check endpoint for monitoring.

#### Request

```http
GET /api/research/health HTTP/1.1
```

#### Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "healthy",
  "components": {
    "chromadb": "healthy",
    "llm_client": "healthy",
    "search_engine": "healthy"
  },
  "timestamp": "2025-10-17T10:30:00Z"
}
```

---

### GET /api/research/models

List available LLM models.

#### Request

```http
GET /api/research/models HTTP/1.1
```

#### Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "models": [
    {
      "provider": "openai",
      "name": "gpt-4-turbo",
      "context_window": 128000,
      "cost_per_1m_tokens": {"input": 10.0, "output": 30.0}
    },
    {
      "provider": "anthropic",
      "name": "claude-3-sonnet-20240229",
      "context_window": 200000,
      "cost_per_1m_tokens": {"input": 3.0, "output": 15.0}
    }
  ],
  "default": "gpt-4-turbo"
}
```

---

## Implementation

### FastAPI Application

```python
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time
import structlog

from src.research.litellm_client import LiteLLMClient, ModelConfig, LLMError
from src.research.context_builder import ContextBuilder
from src.research.citation_parser import CitationParser
from src.search.search_engine import SearchEngine
from src.storage.chroma_client import ChromaClient

logger = structlog.get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Initializing research API components")

    # Initialize ChromaDB
    app.state.chroma_client = ChromaClient(
        host=os.getenv("CHROMA_HOST", "localhost"),
        port=int(os.getenv("CHROMA_PORT", 8001))
    )

    # Initialize search engine
    app.state.search_engine = SearchEngine(
        chroma_client=app.state.chroma_client
    )

    # Initialize context builder
    app.state.context_builder = ContextBuilder(
        search_engine=app.state.search_engine,
        chroma_client=app.state.chroma_client,
        max_sources=10,
        max_tokens=10000
    )

    # Initialize LLM client
    app.state.llm_client = LiteLLMClient(
        ModelConfig(
            provider=os.getenv("LLM_PROVIDER", "openai"),
            model_name=os.getenv("LLM_MODEL", "gpt-4-turbo"),
            temperature=0.3
        )
    )

    # Initialize citation parser
    app.state.citation_parser = CitationParser()

    logger.info("Research API components initialized")

    yield

    # Shutdown
    logger.info("Shutting down research API")

app = FastAPI(
    title="DocuSearch Research API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],  # Copyparty UI
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)

# Research system prompt (from Agent 5)
RESEARCH_SYSTEM_PROMPT = """You are a research assistant helping users find information from their document collection.

RULES:
1. Answer ONLY using information from the provided context
2. If the context doesn't contain enough information, say so
3. Cite sources using [N] where N is the document number
4. Place citations immediately after the relevant facts
5. Be concise but complete
6. Use clear, professional language

CITATION FORMAT:
- Correct: "Paris is the capital of France [1]."
- Incorrect: "Paris is the capital of France. [1]"
- Multiple sources: "This is supported by research [1][2]."
"""

@app.post("/api/research/ask", response_model=ResearchResponse)
async def ask_research_question(request: ResearchRequest):
    """
    Submit research question and receive AI-generated answer with citations
    """
    start_time = time.time()

    try:
        logger.info(
            "Processing research query",
            query=request.query,
            num_sources=request.num_sources,
            search_mode=request.search_mode
        )

        # Step 1: Build context from search results
        search_start = time.time()
        context = await app.state.context_builder.build_context(
            query=request.query,
            num_results=request.num_sources,
            include_text=(request.search_mode in ["text", "hybrid"]),
            include_visual=(request.search_mode in ["visual", "hybrid"])
        )
        search_latency = int((time.time() - search_start) * 1000)

        logger.info(
            "Context built",
            num_sources=len(context.sources),
            total_tokens=context.total_tokens,
            truncated=context.truncated
        )

        # Check if any sources found
        if not context.sources:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No relevant documents found for your query"
            )

        # Step 2: Generate answer with LLM
        llm_start = time.time()
        llm_response = await app.state.llm_client.complete_with_context(
            query=request.query,
            context=context.formatted_text,
            system_message=RESEARCH_SYSTEM_PROMPT,
            temperature=request.temperature,
            model=request.model
        )
        llm_latency = int((time.time() - llm_start) * 1000)

        logger.info(
            "LLM response generated",
            model=llm_response.model,
            tokens=llm_response.usage["total_tokens"],
            latency_ms=llm_latency
        )

        # Step 3: Parse citations
        parsed_answer = app.state.citation_parser.parse(
            text=llm_response.content,
            num_sources=len(context.sources)
        )

        # Validate citations
        if not parsed_answer.validate(len(context.sources)):
            logger.warning("Invalid citations in LLM response")
            # Continue anyway, frontend will handle

        # Step 4: Format response
        frontend_data = app.state.citation_parser.format_for_frontend(parsed_answer)

        total_time = int((time.time() - start_time) * 1000)

        logger.info(
            "Research query completed",
            total_time_ms=total_time,
            num_citations=len(parsed_answer.citations)
        )

        return ResearchResponse(
            answer=parsed_answer.original_text,
            citations=frontend_data["citations"],
            citation_map=frontend_data["citation_map"],
            sources=[
                SourceInfo(
                    id=i + 1,
                    doc_id=source.doc_id,
                    filename=source.filename,
                    page=source.page,
                    extension=source.extension,
                    thumbnail_path=source.thumbnail_path,
                    date_added=source.timestamp,
                    relevance_score=source.relevance_score
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
                search_latency_ms=search_latency
            )
        )

    except HTTPException:
        raise
    except LLMError as e:
        logger.error("LLM error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM service error: {str(e)}"
        )
    except Exception as e:
        logger.error("Unexpected error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.get("/api/research/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check ChromaDB
        chroma_healthy = app.state.chroma_client.heartbeat()

        # Check LLM (simple check)
        llm_healthy = True  # Could ping API

        # Check search engine
        search_healthy = True  # Always healthy if ChromaDB is

        overall_status = "healthy" if all([
            chroma_healthy, llm_healthy, search_healthy
        ]) else "unhealthy"

        return {
            "status": overall_status,
            "components": {
                "chromadb": "healthy" if chroma_healthy else "unhealthy",
                "llm_client": "healthy" if llm_healthy else "unhealthy",
                "search_engine": "healthy" if search_healthy else "unhealthy"
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

@app.get("/api/research/models")
async def list_models():
    """List available LLM models"""
    return {
        "models": [
            {
                "provider": "openai",
                "name": "gpt-4-turbo",
                "context_window": 128000,
                "cost_per_1m_tokens": {"input": 10.0, "output": 30.0}
            },
            {
                "provider": "openai",
                "name": "gpt-3.5-turbo",
                "context_window": 16000,
                "cost_per_1m_tokens": {"input": 0.5, "output": 1.5}
            },
            {
                "provider": "anthropic",
                "name": "claude-3-opus-20240229",
                "context_window": 200000,
                "cost_per_1m_tokens": {"input": 15.0, "output": 75.0}
            },
            {
                "provider": "anthropic",
                "name": "claude-3-sonnet-20240229",
                "context_window": 200000,
                "cost_per_1m_tokens": {"input": 3.0, "output": 15.0}
            }
        ],
        "default": os.getenv("LLM_MODEL", "gpt-4-turbo")
    }
```

---

## Integration Points

### Consumed By: Research Page Frontend (Agent 6)

```javascript
// src/frontend/research.html + research-controller.js

async function submitResearchQuery(query) {
    const response = await fetch('/api/research/ask', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            query: query,
            num_sources: 10,
            search_mode: 'hybrid'
        })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail);
    }

    const data = await response.json();
    // data.answer, data.citations, data.sources, etc.

    return data;
}
```

### Depends On: Wave 1 Components

- **LiteLLM Client (Agent 1)** - `app.state.llm_client`
- **Context Builder (Agent 2)** - `app.state.context_builder`
- **Citation Parser (Agent 3)** - `app.state.citation_parser`
- **Search Engine (Existing)** - `app.state.search_engine`
- **ChromaDB Client (Existing)** - `app.state.chroma_client`

---

## Testing Requirements

### Unit Tests

1. **Request Validation**
   - Valid requests accepted
   - Invalid requests rejected (400)
   - Empty queries rejected
   - Out-of-range parameters rejected

2. **Response Formatting**
   - Response matches schema
   - All required fields present
   - Citations formatted correctly

3. **Error Handling**
   - No sources found → 404
   - LLM failure → 500
   - ChromaDB down → 503

### Integration Tests

1. **End-to-End Query**
   - Submit query → receive answer
   - Citations valid and mapped
   - Sources include thumbnails
   - Metadata accurate

2. **Health Check**
   - Healthy state returns 200
   - Unhealthy state detected

3. **Model Listing**
   - Models returned correctly
   - Default model indicated

---

## Performance Requirements

- **Total Latency:** <3s for typical query (10 sources, GPT-4)
  - Search: <500ms
  - LLM: <2s
  - Parsing: <10ms
  - Overhead: <500ms
- **Concurrent Requests:** Support 10 simultaneous queries
- **Rate Limiting:** 60 requests/minute per IP (configurable)

---

## Security Considerations

- **Input Validation:** Pydantic models validate all inputs
- **SQL Injection:** Not applicable (ChromaDB vector search)
- **API Keys:** Stored in environment variables, not exposed
- **CORS:** Restricted to localhost:8000 (Copyparty UI)
- **Rate Limiting:** Prevent abuse (implement in production)

---

## Validation Gates (Wave 2)

- [ ] All unit tests pass
- [ ] Integration test completes successfully
- [ ] Error handling covers all edge cases
- [ ] Response schema validated
- [ ] Performance requirements met
- [ ] Health check functional
- [ ] Model listing accurate
- [ ] CORS configured correctly

---

## Notes

- Runs on port 8002 (same as existing worker)
- Could be integrated into existing `src/api/server.py` or separate service
- RESEARCH_SYSTEM_PROMPT from Agent 5 (Prompt Engineering)
- Rate limiting recommended for production
- Consider caching common queries
- Monitor LLM costs (log token usage)
