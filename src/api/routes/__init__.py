"""
API routes package.

Contains route definitions organized by resource type.
"""

from .markdown import router as markdown_router
from .documents import router as documents_router
from .projects import router as projects_router

__all__ = ["markdown_router", "documents_router", "projects_router"]
