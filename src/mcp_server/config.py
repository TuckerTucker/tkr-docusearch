"""
Configuration for DocuSearch MCP Server.

Centralizes all configuration values for API endpoints, defaults, and URLs.
"""

from tkr_docusearch.config.urls import get_service_urls

# Get service URLs from centralized configuration
_urls = get_service_urls()

# API Endpoints
DOCUSEARCH_API_URL = _urls.research_api
WORKER_API_URL = _urls.worker
# NOTE: FRONTEND_URL in src.config.urls for centralized URL management

# Research API Endpoint
CONTEXT_ENDPOINT = f"{DOCUSEARCH_API_URL}/api/research/context-only"

# Tool Defaults
DEFAULT_NUM_SOURCES = 10
DEFAULT_SEARCH_MODE = "hybrid"  # visual | text | hybrid
VISION_ENABLED = True

# MCP Server Metadata
SERVER_NAME = "docusearch-mcp"
SERVER_VERSION = "0.1.0"
SERVER_DESCRIPTION = (
    "DocuSearch MCP Server - Multi-modal document search with ColPali "
    "embeddings and AI research capabilities"
)
