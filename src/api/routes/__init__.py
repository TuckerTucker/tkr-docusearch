"""
API routes package.

Contains route definitions organized by resource type.
"""

from .markdown import router as markdown_router
from .documents import router as documents_router

__all__ = ["markdown_router", "documents_router"]
