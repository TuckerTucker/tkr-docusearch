"""
Configuration for DocuSearch MCP Server.

Centralizes all configuration values for API endpoints, defaults, and URLs.
"""

import os

# API Endpoints
DOCUSEARCH_API_URL = os.getenv("DOCUSEARCH_API_URL", "http://localhost:8004")
WORKER_API_URL = os.getenv("WORKER_API_URL", "http://localhost:8002")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

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
