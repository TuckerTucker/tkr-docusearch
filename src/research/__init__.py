"""
Research module for AI-powered document search with citations.

This module provides:
- LiteLLM client for unified LLM interface
- Context builder for search result formatting
- Citation parser for answer analysis
- Response parser for Harmony-format LLM responses
"""

from tkr_docusearch.research.citation_parser import Citation, CitationParser, ParsedAnswer
from tkr_docusearch.research.context_builder import ContextBuilder, ResearchContext, SourceDocument
from tkr_docusearch.research.litellm_client import LiteLLMClient, LLMResponse, ModelConfig
from tkr_docusearch.research.response_parsers import HarmonyResponseParser

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
    "HarmonyResponseParser",
]
