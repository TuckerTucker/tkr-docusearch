"""
tkr-docusearch: Local-first document intelligence application.

Ingests 23+ document formats, creates multimodal embeddings (visual + text),
and provides semantic search with visual citations and AI-powered research —
all running locally on Apple Silicon.

Main Components:
    - storage: Koji hybrid database (SQL + vector + graph)
    - embeddings: Shikomi gRPC client for ColNomic embeddings
    - search: Hybrid search over Koji + Shikomi
    - research: AI-powered research with LiteLLM and inline citations
    - processing: Document parsing (PDF, DOCX, PPTX, MP3, WAV)
    - api: FastAPI REST endpoints
"""

__version__ = "0.9.0"
__author__ = "TuckerTucker"

# Storage
from .storage import (
    KojiClient,
    KojiClientError,
    KojiConnectionError,
    KojiDuplicateError,
    KojiQueryError,
    pack_multivec,
    unpack_multivec,
)

# Search
from .search import KojiSearch

# Embeddings
from .embeddings import ShikomiClient

# AI research capabilities
from .research import (
    Citation,
    CitationParser,
    ContextBuilder,
    HarmonyResponseParser,
    LiteLLMClient,
    LLMResponse,
    ModelConfig,
    ParsedAnswer,
    ResearchContext,
    SourceDocument,
)

__all__ = [
    "__version__",
    "__author__",
    # Storage
    "KojiClient",
    "KojiClientError",
    "KojiConnectionError",
    "KojiQueryError",
    "KojiDuplicateError",
    "pack_multivec",
    "unpack_multivec",
    # Search
    "KojiSearch",
    # Embeddings
    "ShikomiClient",
    # Research
    "LiteLLMClient",
    "ModelConfig",
    "LLMResponse",
    "ContextBuilder",
    "ResearchContext",
    "SourceDocument",
    "CitationParser",
    "ParsedAnswer",
    "Citation",
    "HarmonyResponseParser",
]
