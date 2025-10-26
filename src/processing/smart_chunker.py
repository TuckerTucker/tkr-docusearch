"""
Smart document-aware chunking using Docling's HybridChunker.

This module provides intelligent text chunking that respects document
structure and boundaries, with rich contextual metadata for each chunk.
"""

import logging
import re
from typing import List

from docling.chunking import HybridChunker
from docling_core.types.doc import DoclingDocument
from transformers import AutoTokenizer

from src.config.processing_config import EnhancedModeConfig
from src.processing.types import Page, TextChunk
from src.storage.metadata_schema import ChunkContext, DocumentStructure

logger = logging.getLogger(__name__)


class ChunkingError(Exception):
    """Raised when chunking fails."""


class SmartChunker:
    """Document-aware chunker using Docling's HybridChunker.

    This chunker respects document structure (headings, sections) and
    creates chunks with rich contextual metadata.
    """

    def __init__(self, config: EnhancedModeConfig):
        """Initialize smart chunker.

        Args:
            config: Enhanced mode configuration
        """
        self.config = config

        # Initialize tokenizer (defaulting to bert-base-uncased)
        # TODO: Could be made configurable to match text embedding model
        self.tokenizer = self._init_tokenizer()

        # Initialize HybridChunker
        try:
            self.hybrid_chunker = HybridChunker(
                tokenizer=self.tokenizer,
                max_tokens=config.max_chunk_tokens,
                min_chunk_tokens=config.min_chunk_tokens,
                merge_peers=config.merge_peer_chunks,
            )
            logger.info(
                f"Initialized SmartChunker: "
                f"tokens={config.min_chunk_tokens}-{config.max_chunk_tokens}, "
                f"merge_peers={config.merge_peer_chunks}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize HybridChunker: {e}")
            raise ChunkingError(f"HybridChunker initialization failed: {e}") from e

    def _init_tokenizer(self):
        """Initialize tokenizer for chunking.

        Returns:
            Tokenizer instance
        """
        try:
            # Use a common tokenizer that works well for document chunking
            model_name = "bert-base-uncased"
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            logger.debug(f"Loaded tokenizer: {model_name}")
            return tokenizer
        except Exception as e:
            logger.error(f"Failed to load tokenizer: {e}")
            raise ChunkingError(f"Tokenizer initialization failed: {e}") from e

    def chunk_document(
        self, doc: DoclingDocument, doc_id: str, structure: DocumentStructure
    ) -> List[TextChunk]:
        """Chunk document using hybrid strategy.

        Args:
            doc: Parsed DoclingDocument
            doc_id: Document identifier
            structure: Extracted document structure

        Returns:
            List of TextChunk with context metadata

        Raises:
            ChunkingError: If chunking fails
        """
        try:
            chunks = []

            # Use HybridChunker to get base chunks
            logger.debug(f"Chunking document {doc_id} with HybridChunker")

            for idx, base_chunk in enumerate(self.hybrid_chunker.chunk(doc)):
                # Extract context from base chunk metadata
                context = self._extract_chunk_context(base_chunk, structure)

                # Determine primary page
                page_num = context.page_nums[0] if context.page_nums else 1

                # Extract timestamps from text (audio only)
                from src.processing.text_processor import extract_timestamps_from_text

                start_time, end_time, cleaned_text = extract_timestamps_from_text(base_chunk.text)
                if start_time is not None:
                    logger.info(f"[SMART CHUNKER] Extracted {start_time}-{end_time} from chunk")

                # Create enhanced TextChunk
                chunk = TextChunk(
                    chunk_id=f"{doc_id}-chunk{idx:04d}",
                    page_num=page_num,
                    text=cleaned_text,  # Use cleaned text without [time: X-Y] markers
                    start_offset=0,  # HybridChunker doesn't provide char offsets
                    end_offset=len(cleaned_text),
                    word_count=len(cleaned_text.split()),
                    context=context,
                    start_time=start_time,  # Extracted timestamp or None
                    end_time=end_time,  # Extracted timestamp or None
                )
                chunks.append(chunk)

            logger.info(f"Created {len(chunks)} chunks for document {doc_id}")
            return chunks

        except Exception as e:
            logger.error(f"Chunking failed for document {doc_id}: {e}")
            raise ChunkingError(f"Failed to chunk document: {e}") from e

    def _extract_chunk_context(self, base_chunk, structure: DocumentStructure) -> ChunkContext:
        """Extract contextual metadata from HybridChunker output.

        Args:
            base_chunk: Chunk from HybridChunker
            structure: Document structure

        Returns:
            ChunkContext with metadata
        """
        context = ChunkContext()

        # Extract from base_chunk.meta (provided by HybridChunker)
        if hasattr(base_chunk, "meta") and base_chunk.meta:
            meta = base_chunk.meta

            # Get parent headings
            if hasattr(meta, "headings") and meta.headings:
                # HybridChunker provides list of parent headings
                context.parent_heading = meta.headings[-1]  # Immediate parent
                context.section_path = " > ".join(meta.headings)

                # Look up heading level from structure
                for heading_info in structure.headings:
                    if heading_info.text == context.parent_heading:
                        context.parent_heading_level = heading_info.level.value
                        break

            # Get element type
            if hasattr(meta, "doc_items") and meta.doc_items:
                # Determine type from first doc item
                first_item = meta.doc_items[0]
                if hasattr(first_item, "label"):
                    context.element_type = self._map_element_type(first_item.label)

            # Get page numbers
            if hasattr(meta, "doc_items") and meta.doc_items:
                page_nums_set = set()
                for item in meta.doc_items:
                    if hasattr(item, "prov") and item.prov:
                        for prov in item.prov:
                            if hasattr(prov, "page_no"):
                                page_nums_set.add(prov.page_no)
                context.page_nums = sorted(list(page_nums_set))
                context.is_page_boundary = len(context.page_nums) > 1

        # Detect related tables/pictures (if chunk mentions them)
        context.related_tables = self._find_related_elements(
            base_chunk.text, structure.tables, "Table"
        )
        context.related_pictures = self._find_related_elements(
            base_chunk.text, structure.pictures, "Figure"
        )

        return context

    def _map_element_type(self, docling_label: str) -> str:
        """Map Docling label to element type.

        Args:
            docling_label: Label from Docling

        Returns:
            Element type string
        """
        label_lower = docling_label.lower()

        mapping = {
            "text": "text",
            "paragraph": "text",
            "list_item": "list_item",
            "table": "table_cell",
            "caption": "caption",
            "code": "code",
            "formula": "formula",
        }

        for key, value in mapping.items():
            if key in label_lower:
                return value

        return "text"

    def _find_related_elements(self, text: str, elements: List, prefix: str) -> List[str]:
        """Find references to tables/figures in chunk text.

        Args:
            text: Chunk text
            elements: List of elements (tables or pictures)
            prefix: Prefix to search for ("Table" or "Figure")

        Returns:
            List of element IDs mentioned in text
        """
        related = []

        # Look for "Table 1", "Figure 2", etc.
        pattern = rf"{prefix}\s+(\d+)"
        matches = re.findall(pattern, text, re.IGNORECASE)

        for match in matches:
            element_idx = int(match) - 1  # Convert to 0-indexed
            if 0 <= element_idx < len(elements):
                element = elements[element_idx]
                if hasattr(element, "table_id"):
                    related.append(element.table_id)
                elif hasattr(element, "picture_id"):
                    related.append(element.picture_id)

        return related


class LegacyChunker:
    """Backward-compatible word-based chunker.

    This maintains the original chunking behavior for compatibility.
    """

    def __init__(self, chunk_size_words: int = 250, chunk_overlap_words: int = 50):
        """Initialize legacy chunker.

        Args:
            chunk_size_words: Target words per chunk
            chunk_overlap_words: Word overlap between chunks
        """
        self.chunk_size_words = chunk_size_words
        self.chunk_overlap_words = chunk_overlap_words
        logger.info(
            f"Initialized LegacyChunker: " f"size={chunk_size_words}, overlap={chunk_overlap_words}"
        )

    def chunk_pages(self, pages: List[Page], doc_id: str) -> List[TextChunk]:
        """Chunk pages using word-based sliding window.

        Args:
            pages: List of Page objects
            doc_id: Document identifier

        Returns:
            List of TextChunk objects (without context)
        """
        chunks = []
        chunk_counter = 0

        for page in pages:
            if not page.text.strip():
                continue

            # Split into words
            words = page.text.split()

            # Create overlapping chunks
            start_idx = 0
            while start_idx < len(words):
                end_idx = min(start_idx + self.chunk_size_words, len(words))

                # Get chunk words
                chunk_words = words[start_idx:end_idx]
                chunk_text = " ".join(chunk_words)

                # Calculate character offsets (approximate)
                char_start = sum(len(w) + 1 for w in words[:start_idx])
                char_end = char_start + len(chunk_text)

                chunk = TextChunk(
                    chunk_id=f"{doc_id}-chunk{chunk_counter:04d}",
                    page_num=page.page_num,
                    text=chunk_text,
                    start_offset=char_start,
                    end_offset=char_end,
                    word_count=len(chunk_words),
                    context=None,  # Legacy chunks have no context
                )

                chunks.append(chunk)
                chunk_counter += 1

                # Move to next chunk with overlap
                if end_idx >= len(words):
                    break
                start_idx = end_idx - self.chunk_overlap_words

        logger.debug(f"Created {len(chunks)} legacy chunks from {len(pages)} pages")
        return chunks


def create_chunker(config: EnhancedModeConfig):
    """Create appropriate chunker based on configuration.

    Args:
        config: Enhanced mode configuration

    Returns:
        SmartChunker or LegacyChunker instance

    Raises:
        ChunkingError: If chunker creation fails
    """
    try:
        # Compare by enum value instead of identity to avoid module reload issues
        if config.chunking_strategy.value == "hybrid":
            logger.info("Creating SmartChunker with hybrid strategy")
            return SmartChunker(config)
        else:
            # Legacy strategy
            logger.info(f"Creating LegacyChunker (strategy={config.chunking_strategy.value})")
            return LegacyChunker(chunk_size_words=250, chunk_overlap_words=50)
    except Exception as e:
        logger.error(f"Failed to create chunker: {e}")
        raise ChunkingError(f"Chunker creation failed: {e}") from e


def contextualize_chunk(chunk: TextChunk) -> str:
    """Create context-enriched text for embedding.

    This prepends structural context to chunk text to improve embedding quality.

    Args:
        chunk: TextChunk with context metadata

    Returns:
        Contextualized text string
    """
    if not chunk.context:
        return chunk.text

    parts = []

    # Add section path
    if chunk.context.section_path:
        parts.append(f"[Section: {chunk.context.section_path}]")

    # Add element type if not plain text
    if chunk.context.element_type != "text":
        parts.append(f"[Type: {chunk.context.element_type}]")

    # Add related elements
    if chunk.context.related_tables:
        parts.append(f"[Refers to: {', '.join(chunk.context.related_tables)}]")
    if chunk.context.related_pictures:
        parts.append(f"[Refers to: {', '.join(chunk.context.related_pictures)}]")

    # Add original text
    parts.append(chunk.text)

    return " ".join(parts)
