"""
Markdown generation utilities for document export.

This module generates markdown files with YAML frontmatter from document chunks.
Used by the documents API to serve downloadable markdown versions.

Wave 2 - API Backend
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def generate_markdown_with_frontmatter(
    chunks: List[Dict[str, Any]],
    doc_metadata: Dict[str, Any],
    filename: str,
    doc_id: str
) -> str:
    """
    Generate markdown document with YAML frontmatter.

    Args:
        chunks: List of chunk dictionaries with text_content
        doc_metadata: Document metadata from ChromaDB
        filename: Original filename
        doc_id: Document identifier

    Returns:
        Complete markdown content with frontmatter

    Example frontmatter:
        ---
        filename: example.pdf
        doc_id: abc123...
        date_added: 2025-10-14T12:00:00Z
        page_count: 10
        chunk_count: 25
        has_timestamps: false
        ---
    """
    # Build YAML frontmatter
    frontmatter_lines = ["---"]
    frontmatter_lines.append(f"filename: {filename}")
    frontmatter_lines.append(f"doc_id: {doc_id}")

    # Add metadata fields
    if "timestamp" in doc_metadata:
        frontmatter_lines.append(f"date_added: {doc_metadata['timestamp']}")
    else:
        frontmatter_lines.append(f"date_added: {datetime.utcnow().isoformat()}Z")

    # Add audio metadata if present
    if doc_metadata.get("has_word_timestamps"):
        frontmatter_lines.append("has_timestamps: true")
        if "duration_seconds" in doc_metadata:
            frontmatter_lines.append(f"duration_seconds: {doc_metadata['duration_seconds']}")
        if "artist" in doc_metadata:
            frontmatter_lines.append(f"artist: {doc_metadata['artist']}")
        if "title" in doc_metadata:
            frontmatter_lines.append(f"title: {doc_metadata['title']}")
        if "album" in doc_metadata:
            frontmatter_lines.append(f"album: {doc_metadata['album']}")
    else:
        frontmatter_lines.append("has_timestamps: false")

    # Add page/chunk counts
    frontmatter_lines.append(f"chunk_count: {len(chunks)}")

    frontmatter_lines.append("---")
    frontmatter_lines.append("")  # Blank line after frontmatter

    # Add document title
    frontmatter_lines.append(f"# {filename}")
    frontmatter_lines.append("")

    # Add chunks (full text content)
    content_lines = []
    for i, chunk in enumerate(chunks, start=1):
        text = chunk.get("text_content", "").strip()
        if text:
            # Add chunk separator (optional, for readability)
            if i > 1:
                content_lines.append("")  # Blank line between chunks
            content_lines.append(text)

    # Combine frontmatter and content
    markdown_content = "\n".join(frontmatter_lines + content_lines)

    logger.debug(f"Generated markdown: {len(frontmatter_lines)} frontmatter lines, {len(chunks)} chunks")

    return markdown_content


def save_markdown(doc_id: str, markdown_content: str, output_dir: Optional[Path] = None) -> Path:
    """
    Save markdown content to filesystem.

    Args:
        doc_id: Document identifier (SHA-256 hash)
        markdown_content: Complete markdown file content
        output_dir: Optional output directory (default: data/markdown/)

    Returns:
        Path to saved markdown file

    Raises:
        IOError: If file write fails
    """
    try:
        # 1. Determine output directory
        if output_dir is None:
            output_dir = Path("data/markdown")

        # 2. Create directory if doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        # 3. Generate filename
        filename = f"{doc_id}.md"
        output_path = output_dir / filename

        # 4. Write file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        logger.info(f"Saved markdown file: {output_path}")

        # 5. Return path
        return output_path

    except Exception as e:
        raise IOError(f"Failed to save markdown file: {e}") from e


def get_markdown_path(doc_id: str, markdown_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Get path to markdown file if it exists.

    Args:
        doc_id: Document identifier
        markdown_dir: Optional markdown directory (default: data/markdown/)

    Returns:
        Path to markdown file if exists, None otherwise
    """
    if markdown_dir is None:
        markdown_dir = Path("data/markdown")

    markdown_path = markdown_dir / f"{doc_id}.md"

    if markdown_path.exists():
        return markdown_path
    else:
        return None
