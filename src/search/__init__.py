"""
Search module for DocuSearch.

This module provides hybrid search combining SQL filtering and vector
similarity via the Koji database and Shikomi embeddings.

Components:
- KojiSearch: Main search interface over Koji + Shikomi
"""

from .koji_search import KojiSearch

__all__ = [
    "KojiSearch",
]
