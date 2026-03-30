"""
Shared Pydantic models for the Research API.

Extracted to avoid circular imports between research.py and research_sessions.py.
Both modules import these models from here.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel


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
    # Graph relationships
    related_doc_ids: List[str] = []
    relationship_types: List[str] = []
    cluster_id: Optional[int] = None


class RelationshipEdge(BaseModel):
    """Edge between two source documents in the result graph."""

    src_doc_id: str
    dst_doc_id: str
    relation_type: str


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
    # Graph metadata
    relationships: List[RelationshipEdge] = []
    graph_clusters: int = 0
    # Debug: Preprocessing flow
    preprocessing_original_context: Optional[str] = None
    preprocessing_compressed_context: Optional[str] = None
    preprocessing_model: Optional[str] = None
    preprocessing_per_chunk_stats: Optional[List[Dict]] = None
