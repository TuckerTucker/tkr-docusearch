"""
tkr-docusearch: Production-ready local document search system.

A multimodal document search platform with real ColPali embeddings, ChromaDB
storage, two-stage semantic search, and hybrid Metal GPU/Docker architecture.

Main Components:
    - search: Two-stage semantic search with HNSW indexing and MaxSim re-ranking
    - research: AI-powered research with LiteLLM and inline citations
    - storage: ChromaDB vector database with compression
    - embeddings: ColPali multimodal embedding generation
    - processing: Document parsing (PDF, DOCX, PPTX, MP3, WAV)
    - api: FastAPI REST endpoints

Usage:
    >>> from tkr_docusearch import SearchEngine, ChromaClient
    >>> from tkr_docusearch import LiteLLMClient, ContextBuilder
    >>>
    >>> # Initialize storage and search
    >>> storage = ChromaClient()
    >>> search_engine = SearchEngine(storage_client=storage)
    >>>
    >>> # Execute search
    >>> results = search_engine.search("quarterly revenue growth", n_results=10)
    >>>
    >>> # AI-powered research
    >>> llm_client = LiteLLMClient()
    >>> context = ContextBuilder.from_search_results(results)
    >>> answer = llm_client.generate(query="...", context=context)
"""

__version__ = "0.9.0"
__author__ = "TuckerTucker"

# Core search functionality
from .search import (
    QueryProcessor,
    QueryProcessingError,
    RerankingError,
    ResultRanker,
    RetrievalError,
    SearchEngine,
    SearchError,
)

# Storage and database
from .storage import (
    ChromaClient,
    ChromaDBConnectionError,
    CollectionManager,
    DocumentNotFoundError,
    EmbeddingValidationError,
    MetadataCompressionError,
    StorageError,
    compress_embeddings,
    compression_ratio,
    decompress_embeddings,
    estimate_compressed_size,
)

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
    # Version info
    "__version__",
    "__author__",
    # Search
    "SearchEngine",
    "QueryProcessor",
    "ResultRanker",
    "SearchError",
    "RetrievalError",
    "RerankingError",
    "QueryProcessingError",
    # Storage
    "ChromaClient",
    "CollectionManager",
    "StorageError",
    "ChromaDBConnectionError",
    "EmbeddingValidationError",
    "MetadataCompressionError",
    "DocumentNotFoundError",
    "compress_embeddings",
    "decompress_embeddings",
    "estimate_compressed_size",
    "compression_ratio",
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
