"""
Context Builder for creating formatted LLM context from search results.

Retrieves search results, extracts metadata and markdown content,
and constructs formatted context strings with proper citations.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import structlog

from src.config.urls import get_service_urls
from src.utils.paths import convert_path_to_url

from .chunk_extractor import extract_chunk_id

logger = structlog.get_logger(__name__)


@dataclass
class SourceDocument:
    """Represents a source document for citation"""

    doc_id: str  # Unique document identifier
    filename: str  # Original filename (e.g., "report.pdf")
    page: int  # Page number (1-indexed)
    extension: str  # File extension ("pdf", "docx", etc.")

    # Paths for frontend display
    thumbnail_path: Optional[str] = None  # Path to thumbnail image
    image_path: Optional[str] = None  # Full page image

    # Metadata for context
    timestamp: str = ""  # Upload timestamp ISO format
    section_path: Optional[str] = None  # "Introduction > Methods"
    parent_heading: Optional[str] = None  # Immediate parent heading

    # Content
    markdown_content: str = ""  # Extracted text from page

    # Search relevance
    relevance_score: float = 0.0  # Search score (0-1)

    # Chunk identifier for bidirectional highlighting
    chunk_id: Optional[str] = None  # Format: "{doc_id}-chunk{NNNN}" for text, None for visual

    # Search type tracking for vision support
    is_visual: bool = False  # True if from visual collection, False if from text collection

    # Visual necessity detection (populated during preprocessing)
    has_visual_dependency: bool = (
        False  # True if chunk requires visual context (images/charts/tables)
    )
    related_pictures: List[str] = field(default_factory=list)  # Picture IDs from ChunkContext
    related_tables: List[str] = field(default_factory=list)  # Table IDs from ChunkContext

    # Raw ChromaDB metadata (for preprocessing analysis)
    raw_metadata: Dict[str, Any] = field(default_factory=dict)  # Complete metadata from ChromaDB

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict for API response"""
        return {
            "doc_id": self.doc_id,
            "filename": self.filename,
            "page": self.page,
            "extension": self.extension,
            "thumbnail_path": self.thumbnail_path,
            "image_path": self.image_path,
            "timestamp": self.timestamp,
            "section_path": self.section_path,
            "parent_heading": self.parent_heading,
            "relevance_score": self.relevance_score,
            "chunk_id": self.chunk_id,
        }


@dataclass
class ResearchContext:
    """Formatted context for LLM prompt"""

    formatted_text: str  # Context string with citations
    sources: List[SourceDocument]  # Source documents in citation order
    total_tokens: int  # Approximate token count
    truncated: bool  # Whether context was truncated to fit budget
    image_urls: List[str] = None  # URLs for visual sources (for multimodal LLM)

    def __post_init__(self):
        """Initialize image_urls if not provided"""
        if self.image_urls is None:
            self.image_urls = []

    def get_citation_map(self) -> Dict[int, SourceDocument]:
        """
        Map citation numbers to source documents

        Returns:
            Dict mapping citation IDs (1, 2, 3...) to SourceDocument
        """
        return {i + 1: source for i, source in enumerate(self.sources)}

    def get_visual_image_urls(self, base_url: Optional[str] = None) -> List[str]:
        """
        Extract absolute image URLs from visual sources

        Args:
            base_url: Base URL for worker API (default: from centralized config)

        Returns:
            List of absolute URLs to page thumbnails for visual sources

        Note:
            Converts relative paths like '/images/abc/page001_thumb.jpg'
            to absolute URLs like 'http://localhost:8002/images/abc/page001_thumb.jpg'

            Filters out unsupported formats (SVG) - OpenAI vision API only supports:
            png, jpeg, gif, webp
        """
        if base_url is None:
            base_url = get_service_urls().worker
        # OpenAI vision API supported formats
        SUPPORTED_IMAGE_FORMATS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

        urls = []
        for source in self.sources:
            if source.is_visual and source.thumbnail_path:
                # Skip unsupported formats (e.g., SVG)
                file_ext = source.thumbnail_path.lower().split(".")[-1]
                if f".{file_ext}" not in SUPPORTED_IMAGE_FORMATS:
                    logger.debug(
                        "Skipping unsupported image format for LLM vision",
                        path=source.thumbnail_path,
                        format=file_ext,
                        supported=list(SUPPORTED_IMAGE_FORMATS),
                    )
                    continue

                # Convert relative path to absolute URL
                if source.thumbnail_path.startswith("/"):
                    url = f"{base_url}{source.thumbnail_path}"
                else:
                    url = source.thumbnail_path
                urls.append(url)
        return urls


class ContextBuilder:
    """Builds formatted context from search results"""

    def __init__(
        self, search_engine, chroma_client, max_sources: int = 10, max_tokens: int = 10000
    ):
        """
        Initialize context builder

        Args:
            search_engine: Configured search engine instance
            chroma_client: ChromaDB client for metadata retrieval
            max_sources: Maximum number of sources to include (default: 10)
            max_tokens: Maximum context tokens (default: 10K for ~8K context)

        Note:
            max_tokens includes overhead for formatting, aim for ~80% of model's limit
        """
        self.search_engine = search_engine
        self.chroma_client = chroma_client
        self.max_sources = max_sources
        self.max_tokens = max_tokens

        logger.info("Context builder initialized", max_sources=max_sources, max_tokens=max_tokens)

    async def build_context(
        self,
        query: str,
        num_results: int = 10,
        include_text: bool = True,
        include_visual: bool = True,
    ) -> ResearchContext:
        """
        Build research context from search results

        Args:
            query: User's research question
            num_results: Number of search results to retrieve (default: 10)
            include_text: Include text collection results (default: True)
            include_visual: Include visual collection results (default: True)

        Returns:
            ResearchContext with formatted text and source documents

        Process:
            1. Execute semantic search via SearchEngine
            2. Deduplicate by (doc_id, page) keeping highest scores
            3. Retrieve full markdown via ChromaClient.get_document_markdown()
            4. Format as numbered citations [1], [2], etc.
            5. Truncate if exceeds max_tokens
        """
        logger.info(
            "Building context",
            query=query,
            num_results=num_results,
            include_text=include_text,
            include_visual=include_visual,
        )

        # Determine search mode
        if include_text and include_visual:
            search_mode = "hybrid"
        elif include_visual:
            search_mode = "visual_only"
        else:
            search_mode = "text_only"

        # Execute search
        search_response = self.search_engine.search(
            query=query, n_results=num_results, search_mode=search_mode
        )

        search_results = search_response.get("results", [])

        logger.debug(
            "Search complete",
            num_results=len(search_results),
            search_time_ms=search_response.get("total_time_ms", 0),
        )

        # Deduplicate by (doc_id, page)
        deduped_results = self.deduplicate_results(search_results)

        # Limit to max_sources
        deduped_results = deduped_results[: self.max_sources]

        # Build source documents
        sources = []
        for result in deduped_results:
            try:
                source = await self.get_source_metadata(
                    doc_id=result["doc_id"], page=result["page"], score=result.get("score", 0.0)
                )
                sources.append(source)

                # For visual matches in hybrid mode, also add the corresponding text chunk
                # This allows MLX preprocessing on text while keeping visual for foundation model
                if search_mode == "hybrid" and source.is_visual and source.markdown_content:
                    # Create a text version of the same page for preprocessing
                    text_source = await self._get_text_chunk_for_visual(source)
                    if text_source:
                        sources.append(text_source)
                        logger.info(
                            "Added text chunk for visual match",
                            doc_id=source.doc_id,
                            page=source.page,
                            text_length=len(text_source.markdown_content),
                            is_visual=text_source.is_visual,
                            chunk_id=text_source.chunk_id,
                        )
                    else:
                        logger.debug(
                            "Skipped text chunk (too short)",
                            doc_id=source.doc_id,
                            page=source.page,
                            content_length=(
                                len(source.markdown_content) if source.markdown_content else 0
                            ),
                        )

            except Exception as e:
                logger.warning(
                    "Failed to get source metadata",
                    doc_id=result.get("doc_id"),
                    page=result.get("page"),
                    error=str(e),
                )
                continue

        if not sources:
            logger.warning("No sources found for query")
            return ResearchContext(
                formatted_text="No relevant documents found.",
                sources=[],
                total_tokens=0,
                truncated=False,
            )

        # Format context
        formatted_text = self._format_context(sources)

        # Check token budget
        total_tokens = self.estimate_tokens(formatted_text)
        truncated = False

        if total_tokens > self.max_tokens:
            logger.info(
                "Context exceeds token budget, truncating",
                current_tokens=total_tokens,
                max_tokens=self.max_tokens,
            )
            sources = self.truncate_to_budget(sources, self.max_tokens)
            formatted_text = self._format_context(sources)
            total_tokens = self.estimate_tokens(formatted_text)
            truncated = True

        logger.info(
            "Context built successfully",
            num_sources=len(sources),
            total_tokens=total_tokens,
            truncated=truncated,
        )

        return ResearchContext(
            formatted_text=formatted_text,
            sources=sources,
            total_tokens=total_tokens,
            truncated=truncated,
        )

    async def _get_text_chunk_for_visual(
        self, visual_source: SourceDocument
    ) -> Optional[SourceDocument]:
        """
        Create a text-only version of a visual source for preprocessing.

        This allows MLX to compress the text chunk while the visual goes to the foundation model.

        Args:
            visual_source: Visual source document with markdown content

        Returns:
            SourceDocument marked as text (is_visual=False) with same content, or None if no text
        """
        # Skip if no meaningful text content (threshold is low to match preprocessor's 400 char minimum)
        # Note: preprocessor will further filter chunks < 400 chars
        if not visual_source.markdown_content or len(visual_source.markdown_content.strip()) < 100:
            return None

        # Create a copy of the visual source but mark it as text for preprocessing
        return SourceDocument(
            doc_id=visual_source.doc_id,
            filename=visual_source.filename,
            page=visual_source.page,
            extension=visual_source.extension,
            thumbnail_path=visual_source.thumbnail_path,
            image_path=visual_source.image_path,
            timestamp=visual_source.timestamp,
            section_path=visual_source.section_path,
            parent_heading=visual_source.parent_heading,
            markdown_content=visual_source.markdown_content,
            relevance_score=visual_source.relevance_score,
            chunk_id=f"{visual_source.doc_id}-page{visual_source.page}",  # Synthetic chunk_id for text version
            is_visual=False,  # Mark as text so it gets preprocessed
        )

    async def get_source_metadata(
        self, doc_id: str, page: int, score: float = 0.0
    ) -> SourceDocument:
        """
        Retrieve metadata for a single source document

        Args:
            doc_id: Document identifier
            page: Page number
            score: Relevance score from search

        Returns:
            SourceDocument with all available metadata

        Raises:
            ValueError: If document not found in ChromaDB
        """
        # Try visual collection first for page metadata
        visual_results = self.chroma_client._visual_collection.get(
            where={"$and": [{"doc_id": {"$eq": doc_id}}, {"page": {"$eq": page}}]},
            include=["metadatas"],
            limit=1,
        )

        metadata = None
        if visual_results["ids"]:
            metadata = visual_results["metadatas"][0]
        else:
            # Fallback to text collection if not in visual
            text_results = self.chroma_client._text_collection.get(
                where={"$and": [{"doc_id": {"$eq": doc_id}}, {"page": {"$eq": page}}]},
                include=["metadatas"],
                limit=1,
            )
            if text_results["ids"]:
                metadata = text_results["metadatas"][0]
            else:
                raise ValueError(
                    f"Document {doc_id} page {page} not found in visual or text collections"
                )

        # Get full markdown from file or compressed metadata
        full_markdown = None

        # Try to read from markdown file path (preferred)
        markdown_path = metadata.get("markdown_path")
        if markdown_path:
            try:
                import os

                if os.path.exists(markdown_path):
                    with open(markdown_path, "r", encoding="utf-8") as f:
                        full_markdown = f.read()
                    logger.debug(
                        "Loaded markdown from file",
                        path=markdown_path,
                        length=len(full_markdown),
                    )
            except Exception as e:
                logger.warning("Failed to read markdown file", path=markdown_path, error=str(e))

        # Fallback: try to get from compressed metadata
        if not full_markdown:
            try:
                full_markdown = self.chroma_client.get_document_markdown(doc_id)
            except Exception as e:
                logger.warning("Failed to get markdown from ChromaDB", doc_id=doc_id, error=str(e))

        # Last resort: use full_text from chunk metadata if available
        if not full_markdown:
            full_markdown = metadata.get("full_text", "")
            if full_markdown:
                logger.debug("Using full_text from metadata", length=len(full_markdown))

        # Extract page-specific content
        page_content = self._extract_page_from_markdown(full_markdown, page)

        # Extract chunk_id for bidirectional highlighting
        # Returns None for visual results, formatted string for text results
        chunk_id = extract_chunk_id(metadata, doc_id)

        # Determine if this is a visual or text result
        # Visual results have no chunk_id, text results have chunk_id format: "{doc_id}-chunk{NNNN}"
        is_visual = chunk_id is None

        # Get thumbnail path - prefer thumb_path (visual docs) or album_art_path (audio)
        thumbnail = metadata.get("thumb_path") or metadata.get("album_art_path")

        # Get extension - prefer extension field, fallback to format
        extension = metadata.get("extension") or metadata.get("format", "")

        return SourceDocument(
            doc_id=doc_id,
            filename=metadata.get("filename", "unknown"),
            page=page,
            extension=extension,
            thumbnail_path=convert_path_to_url(thumbnail),
            image_path=convert_path_to_url(metadata.get("image_path")),
            timestamp=metadata.get("timestamp", ""),
            section_path=metadata.get("section_path"),
            parent_heading=metadata.get("parent_heading"),
            markdown_content=page_content,
            relevance_score=score,
            chunk_id=chunk_id,
            is_visual=is_visual,
            raw_metadata=metadata,  # Pass through full ChromaDB metadata for preprocessing
        )

    def format_source_citation(self, source: SourceDocument, citation_num: int) -> str:
        """
        Format a single source as citation block

        Args:
            source: Source document to format
            citation_num: Citation number (1, 2, 3...)

        Returns:
            Formatted citation string

        Note:
            Adds [Visual Match] indicator for sources found via visual search
        """
        # Add visual indicator for visual search results
        match_type = "[Visual Match] " if source.is_visual else ""
        citation = f"{match_type}[Document {citation_num}: {source.filename}, Page {source.page}]\n"
        citation += source.markdown_content.strip()
        return citation

    def deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate (doc_id, page) pairs, keeping highest scores

        Args:
            results: Search results from SearchEngine

        Returns:
            Deduplicated results sorted by score descending
        """
        seen = {}  # (doc_id, page) -> result

        for result in results:
            key = (result.get("doc_id"), result.get("page"))

            if key not in seen:
                seen[key] = result
            else:
                # Keep higher score
                if result.get("score", 0) > seen[key].get("score", 0):
                    seen[key] = result

        # Sort by score descending
        deduped = sorted(seen.values(), key=lambda r: r.get("score", 0), reverse=True)

        logger.debug(
            "Deduplication complete", original_count=len(results), deduped_count=len(deduped)
        )

        return deduped

    def truncate_to_budget(
        self, sources: List[SourceDocument], max_tokens: int
    ) -> List[SourceDocument]:
        """
        Truncate sources to fit token budget

        Args:
            sources: Source documents sorted by relevance
            max_tokens: Maximum allowed tokens

        Returns:
            Truncated list of sources that fit within budget

        Process:
            1. Estimate tokens for each source (citation header + content)
            2. Add sources in order until budget exceeded
            3. Return sources that fit
        """
        truncated: List[SourceDocument] = []
        current_tokens = 0

        for source in sources:
            # Estimate tokens for this source
            citation_text = self.format_source_citation(source, len(truncated) + 1)
            source_tokens = self.estimate_tokens(citation_text)

            # Add separator tokens (newlines between sources)
            separator_tokens = 5

            if current_tokens + source_tokens + separator_tokens <= max_tokens:
                truncated.append(source)
                current_tokens += source_tokens + separator_tokens
            else:
                # Budget exceeded
                break

        logger.debug(
            "Truncated sources",
            original_count=len(sources),
            truncated_count=len(truncated),
            tokens_used=current_tokens,
        )

        return truncated

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text

        Args:
            text: Text to estimate

        Returns:
            Approximate token count

        Note:
            Uses simple heuristic: ~4 chars per token
            More accurate than char count, faster than tiktoken
        """
        return len(text) // 4

    def _format_context(self, sources: List[SourceDocument]) -> str:
        """
        Format sources as numbered citation blocks with SOURCE LINKS section.

        The format includes:
        1. Numbered citation blocks with document content
        2. SOURCE LINKS section with URLs for each source

        This allows the LLM to create markdown link citations like [[1]](url).
        """
        from src.utils.url_builder import build_details_url

        parts = []

        # Add numbered citation blocks
        for i, source in enumerate(sources, start=1):
            citation = self.format_source_citation(source, i)
            parts.append(citation)

        # Add SOURCE LINKS section
        parts.append("\n---\n")
        parts.append("SOURCE LINKS:\n")

        for i, source in enumerate(sources, start=1):
            # Build URL for this source
            url = build_details_url(
                doc_id=source.doc_id,
                # Audio documents don't use page navigation (use time-based chunks)
                page=source.page if source.extension not in ["mp3", "wav"] else None,
                chunk_id=source.chunk_id,
                absolute=True,  # Use absolute URLs for LLM citations
            )

            # Format: [N] filename url
            visual_tag = "[Visual Match] " if source.is_visual else ""
            parts.append(f"[{i}] {visual_tag}{source.filename} {url}")

        return "\n\n".join(parts)

    def _extract_page_from_markdown(self, markdown: Optional[str], page: int) -> str:
        """
        Extract page-specific content from full markdown

        Args:
            markdown: Full document markdown
            page: Page number to extract

        Returns:
            Page-specific content
        """
        if not markdown:
            return ""

        # Look for page markers in markdown (common format: ## Page N)
        page_pattern = rf"##\s*Page\s*{page}\b"
        next_page_pattern = rf"##\s*Page\s*{page + 1}\b"

        # Find current page marker
        page_match = re.search(page_pattern, markdown, re.IGNORECASE)
        if not page_match:
            # No page marker found, return portion of markdown
            # This is a fallback - estimate page content
            return self._estimate_page_content(markdown, page)

        # Find next page marker
        next_page_match = re.search(next_page_pattern, markdown[page_match.end() :], re.IGNORECASE)

        if next_page_match:
            # Extract between current and next page
            page_content = markdown[page_match.end() : page_match.end() + next_page_match.start()]
        else:
            # Last page, extract to end
            page_content = markdown[page_match.end() :]

        return page_content.strip()

    def _estimate_page_content(self, markdown: str, page: int) -> str:
        """
        Estimate page content when no page markers exist

        Args:
            markdown: Full document markdown
            page: Page number

        Returns:
            Estimated page content
        """
        # If markdown is short, return it all
        if len(markdown) < 1000:
            return markdown

        # Split by double newlines (paragraphs)
        paragraphs = [p for p in markdown.split("\n\n") if p.strip()]

        if not paragraphs:
            # No paragraph breaks, just chunk by characters
            chunk_size = 800
            start_idx = (page - 1) * chunk_size
            end_idx = page * chunk_size
            return (
                markdown[start_idx:end_idx] if start_idx < len(markdown) else markdown[:chunk_size]
            )

        # Estimate ~3 paragraphs per page
        paragraphs_per_page = 3
        start_idx = (page - 1) * paragraphs_per_page
        end_idx = page * paragraphs_per_page

        page_paragraphs = paragraphs[start_idx:end_idx]

        # If we're beyond the available paragraphs, use the last ones or first 500 chars
        if not page_paragraphs:
            # Return last few paragraphs or beginning of document
            if paragraphs:
                return "\n\n".join(paragraphs[-paragraphs_per_page:])
            return markdown[:800]

        return "\n\n".join(page_paragraphs)
