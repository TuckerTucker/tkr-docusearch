"""
Markdown chunk marker insertion for bidirectional highlighting.

This module provides functions to insert chunk markers into markdown documents
to enable bidirectional highlighting between search results and document content.

Provider: storage-agent (Wave 7)
Consumers: documents-api, research-interface
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from tkr_docusearch.storage.chroma_client import ChromaClient

logger = logging.getLogger(__name__)


# ============================================================================
# Exception Classes
# ============================================================================


class ChunkMarkupError(Exception):
    """Base exception for chunk marker operations."""


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class ChunkMetadata:
    """Metadata for a text chunk from ChromaDB.

    Attributes:
        chunk_id: Unique chunk identifier (e.g., "doc123-chunk0000")
        embedding_id: ChromaDB embedding ID
        page: Page number where chunk appears
        section_path: Hierarchical section path (e.g., "Introduction > Methods")
        text_content: Full text content of the chunk
        text_start_pos: Estimated start position in markdown (computed)
        parent_heading: Immediate parent heading text
    """

    chunk_id: str
    embedding_id: str
    page: int
    section_path: str
    text_content: str
    text_start_pos: int = 0
    parent_heading: Optional[str] = None


# ============================================================================
# Core Functions
# ============================================================================


def get_chunks_for_document(doc_id: str, chroma_client: ChromaClient) -> List[ChunkMetadata]:
    """Query ChromaDB for all text chunks of a document.

    Args:
        doc_id: Document identifier
        chroma_client: ChromaDB client instance

    Returns:
        List of ChunkMetadata sorted by page and position

    Raises:
        ChunkMarkupError: If query fails

    Example:
        >>> client = ChromaClient(host='localhost', port=8001)
        >>> chunks = get_chunks_for_document('abc123', client)
        >>> print(f"Found {len(chunks)} chunks")
    """
    try:
        # Query text collection for all chunks of this document
        text_data = chroma_client._text_collection.get(where={"doc_id": doc_id})

        if not text_data or not text_data.get("ids"):
            logger.warning(f"No text chunks found for document: {doc_id}")
            return []

        # Extract chunk metadata
        chunks = []
        ids = text_data["ids"]
        metadatas = text_data.get("metadatas", [])

        for idx, embedding_id in enumerate(ids):
            metadata = metadatas[idx] if idx < len(metadatas) else {}

            # Parse chunk_id from embedding_id (format: "doc_id-chunk0000")
            chunk_id = embedding_id

            # Extract metadata fields
            page = metadata.get("page", 1)
            section_path = metadata.get("section_path", "")
            text_content = metadata.get("full_text") or metadata.get("text_preview", "")
            parent_heading = metadata.get("parent_heading")

            chunk = ChunkMetadata(
                chunk_id=chunk_id,
                embedding_id=embedding_id,
                page=page,
                section_path=section_path,
                text_content=text_content,
                parent_heading=parent_heading,
            )
            chunks.append(chunk)

        # Sort by page number, then by text length (proxy for position)
        # Note: ChromaDB doesn't store character offsets, so we estimate
        chunks.sort(key=lambda c: (c.page, len(c.text_content)))

        logger.info(f"Retrieved {len(chunks)} chunks for document {doc_id}")
        return chunks

    except Exception as e:
        logger.error(f"Failed to get chunks for document {doc_id}: {e}", exc_info=True)
        raise ChunkMarkupError(f"Failed to query chunks: {e}") from e


def _escape_html_in_markdown(text: str) -> str:
    """Escape HTML special characters but preserve markdown.

    Args:
        text: Text to escape

    Returns:
        Escaped text safe for HTML attributes
    """
    # Only escape double quotes for attribute values
    return text.replace('"', "&quot;")


def _find_chunk_position(markdown: str, chunk: ChunkMetadata) -> Optional[int]:
    """Find the position of chunk text in markdown.

    Args:
        markdown: Full markdown content
        chunk: Chunk metadata with text content

    Returns:
        Start position of chunk in markdown, or None if not found

    Note:
        This uses fuzzy matching to handle minor whitespace differences.
    """
    if not chunk.text_content.strip():
        return None

    # Get first ~100 chars of chunk as search anchor
    search_text = chunk.text_content[:100].strip()

    # Normalize whitespace for matching
    search_normalized = re.sub(r"\s+", " ", search_text)

    # Search for matching position
    pos = 0
    while pos < len(markdown):
        # Find next potential match
        match_pos = markdown.find(search_text[:20], pos)
        if match_pos == -1:
            break

        # Extract context and normalize
        context = markdown[match_pos : match_pos + len(search_text)]
        context_normalized = re.sub(r"\s+", " ", context)

        # Check if it matches
        if search_normalized in context_normalized:
            return match_pos

        pos = match_pos + 1

    logger.debug(f"Could not find position for chunk {chunk.chunk_id}")
    return None


def _extract_frontmatter(markdown: str) -> tuple[str, str]:
    """Extract YAML frontmatter from markdown.

    Args:
        markdown: Full markdown content

    Returns:
        Tuple of (frontmatter, content) where frontmatter includes delimiters
    """
    if not markdown.startswith("---"):
        return "", markdown

    # Find end of frontmatter
    end_match = re.search(r"\n---\n", markdown[3:])
    if not end_match:
        return "", markdown

    end_pos = end_match.end() + 3
    frontmatter = markdown[:end_pos]
    content = markdown[end_pos:]

    return frontmatter, content


def _update_frontmatter_chunk_count(frontmatter: str, chunk_count: int) -> str:
    """Add or update chunk_count in YAML frontmatter.

    Args:
        frontmatter: YAML frontmatter with delimiters
        chunk_count: Number of chunks

    Returns:
        Updated frontmatter
    """
    if not frontmatter:
        return frontmatter

    # Check if chunk_count already exists
    if re.search(r"^chunk_count:\s*\d+", frontmatter, re.MULTILINE):
        # Update existing
        frontmatter = re.sub(
            r"^(chunk_count:\s*)\d+", rf"\g<1>{chunk_count}", frontmatter, flags=re.MULTILINE
        )
    else:
        # Add before closing delimiter
        frontmatter = frontmatter.replace("---\n", f"chunk_count: {chunk_count}\n---\n", 1)

    return frontmatter


def insert_chunk_markers(
    markdown: str, chunks: List[ChunkMetadata], update_frontmatter: bool = True
) -> str:
    """Insert chunk markers into markdown for bidirectional highlighting.

    This function inserts HTML comment markers and div wrappers around each chunk
    in the markdown document to enable bidirectional highlighting between search
    results and document content.

    Args:
        markdown: Original markdown content
        chunks: List of ChunkMetadata sorted by position
        update_frontmatter: If True, add chunk_count to frontmatter

    Returns:
        Markdown with inserted chunk markers

    Raises:
        ChunkMarkupError: If marker insertion fails

    Example:
        >>> markdown = "# Title\\n\\nFirst paragraph..."
        >>> chunks = get_chunks_for_document('abc123', client)
        >>> marked_md = insert_chunk_markers(markdown, chunks)
        >>> print(marked_md)
        # Title

        <!-- chunk:abc123-chunk0000 page:1 section:"Title" -->
        <div data-chunk-id="abc123-chunk0000" data-page="1" data-section="Title">
        First paragraph...
        </div>
    """
    if not markdown.strip():
        logger.warning("Empty markdown provided")
        return markdown

    if not chunks:
        logger.info("No chunks provided, returning original markdown")
        return markdown

    try:
        # Extract frontmatter
        frontmatter, content = _extract_frontmatter(markdown)

        # Find positions for each chunk
        for chunk in chunks:
            pos = _find_chunk_position(content, chunk)
            if pos is not None:
                chunk.text_start_pos = pos
            else:
                # Mark as not found (will skip)
                chunk.text_start_pos = -1

        # Sort chunks by position (reverse order for insertion)
        valid_chunks = [c for c in chunks if c.text_start_pos >= 0]
        valid_chunks.sort(key=lambda c: c.text_start_pos, reverse=True)

        logger.info(
            f"Inserting markers for {len(valid_chunks)}/{len(chunks)} chunks "
            f"({len(chunks) - len(valid_chunks)} not found in markdown)"
        )

        # Insert markers in reverse order to preserve positions
        for chunk in valid_chunks:
            # Prepare marker attributes
            chunk_id = chunk.chunk_id
            page = chunk.page
            section = _escape_html_in_markdown(chunk.section_path or "")

            # Find end of chunk (approximate using text length)
            chunk_start = chunk.text_start_pos
            chunk_text_len = len(chunk.text_content)

            # Try to find exact end, or use approximate
            chunk_end = chunk_start + chunk_text_len

            # Ensure we don't exceed content length
            chunk_end = min(chunk_end, len(content))

            # Create marker HTML comment
            marker_comment = f'<!-- chunk:{chunk_id} page:{page} section:"{section}" -->\n'

            # Create opening div
            opening_div = (
                f'<div data-chunk-id="{chunk_id}" data-page="{page}" '
                f'data-section="{section}">\n'
            )

            # Create closing div
            closing_div = "\n</div>\n"

            # Insert markers around chunk
            # Note: We insert at approximate positions to avoid breaking markdown structure
            # For a more robust solution, we'd need to parse markdown AST
            content = (
                content[:chunk_start]
                + marker_comment
                + opening_div
                + content[chunk_start:chunk_end]
                + closing_div
                + content[chunk_end:]
            )

        # Update frontmatter if requested
        if update_frontmatter and frontmatter:
            frontmatter = _update_frontmatter_chunk_count(frontmatter, len(chunks))

        # Reconstruct full markdown
        result = frontmatter + content

        logger.info(f"Successfully inserted {len(valid_chunks)} chunk markers")
        return result

    except Exception as e:
        logger.error(f"Failed to insert chunk markers: {e}", exc_info=True)
        raise ChunkMarkupError(f"Failed to insert markers: {e}") from e


def validate_chunk_markers(markdown: str) -> Dict[str, any]:
    """Validate chunk markers in markdown.

    Args:
        markdown: Markdown content with chunk markers

    Returns:
        Dictionary with validation results:
            - valid: bool - True if all markers are valid
            - marker_count: int - Number of markers found
            - errors: List[str] - List of validation errors

    Example:
        >>> result = validate_chunk_markers(marked_markdown)
        >>> if not result['valid']:
        ...     print(f"Errors: {result['errors']}")
    """
    errors = []
    marker_count = 0

    # Pattern for HTML comment markers
    comment_pattern = r'<!-- chunk:([^\s]+) page:(\d+) section:"([^"]*)" -->'

    # Pattern for div tags
    div_open_pattern = r'<div data-chunk-id="([^"]+)" data-page="(\d+)" ' r'data-section="([^"]*)">'
    div_close_pattern = r"</div>"

    # Find all comment markers
    comments = re.findall(comment_pattern, markdown)
    marker_count = len(comments)

    # Find all div openings
    div_opens = re.findall(div_open_pattern, markdown)

    # Find all div closings
    div_closes = re.findall(div_close_pattern, markdown)

    # Validate counts match
    if len(comments) != len(div_opens):
        errors.append(
            f"Mismatch between comment markers ({len(comments)}) "
            f"and opening divs ({len(div_opens)})"
        )

    if len(div_opens) != len(div_closes):
        errors.append(
            f"Mismatch between opening divs ({len(div_opens)}) "
            f"and closing divs ({len(div_closes)})"
        )

    # Validate marker data matches
    for idx, (comment_data, div_data) in enumerate(zip(comments, div_opens)):
        if comment_data != div_data:
            errors.append(f"Marker {idx}: Comment and div attributes don't match")

    return {"valid": len(errors) == 0, "marker_count": marker_count, "errors": errors}


# ============================================================================
# Utility Functions
# ============================================================================


def strip_chunk_markers(markdown: str) -> str:
    """Remove all chunk markers from markdown.

    Args:
        markdown: Markdown with chunk markers

    Returns:
        Clean markdown without markers

    Example:
        >>> clean = strip_chunk_markers(marked_markdown)
    """
    # Remove HTML comments
    result = re.sub(
        r'<!-- chunk:[^\s]+ page:\d+ section:"[^"]*" -->\n?', "", markdown, flags=re.MULTILINE
    )

    # Remove opening divs
    result = re.sub(
        r'<div data-chunk-id="[^"]+" data-page="\d+" ' r'data-section="[^"]*">\n?',
        "",
        result,
        flags=re.MULTILINE,
    )

    # Remove closing divs
    result = re.sub(r"\n?</div>\n?", "", result, flags=re.MULTILINE)

    return result
