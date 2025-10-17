"""
Research module for AI-powered document search with citations.

This module provides:
- LiteLLM client for unified LLM interface
- Context builder for search result formatting
- Citation parser for answer analysis
"""

from src.research.citation_parser import Citation, CitationParser, ParsedAnswer
from src.research.context_builder import ContextBuilder, ResearchContext, SourceDocument
from src.research.litellm_client import LiteLLMClient, LLMResponse, ModelConfig

__all__ = [
    "LiteLLMClient",
    "ModelConfig",
    "LLMResponse",
    "ContextBuilder",
    "ResearchContext",
    "SourceDocument",
    "CitationParser",
    "ParsedAnswer",
    "Citation",
]
