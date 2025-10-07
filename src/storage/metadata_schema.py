"""
Metadata schema definitions for enhanced document processing.

This module defines data structures and validation functions for storing
rich document structure and chunk context in ChromaDB metadata.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import json


class HeadingLevel(Enum):
    """Hierarchical heading levels."""
    TITLE = 0
    SECTION_HEADER = 1
    SUB_SECTION_HEADER = 2
    PARAGRAPH_HEADER = 3


class PictureType(Enum):
    """Picture classification types from Docling."""
    CHART = "chart"  # Bar chart, line chart, pie chart
    DIAGRAM = "diagram"  # Flow diagram, architecture diagram
    PHOTO = "photo"  # Photograph
    LOGO = "logo"  # Company/product logo
    SIGNATURE = "signature"  # Handwritten signature
    OTHER = "other"  # Unknown/other type


@dataclass
class HeadingInfo:
    """Information about a document heading.

    Attributes:
        text: Heading text content
        level: Hierarchical level
        page_num: Page number where heading appears
        bbox: Bounding box (x1, y1, x2, y2) if available
        section_path: Hierarchical path (e.g., "1.2.3" or "Introduction > Methods")
    """
    text: str
    level: HeadingLevel
    page_num: int
    bbox: Optional[tuple[float, float, float, float]] = None
    section_path: str = ""


@dataclass
class TableInfo:
    """Information about a document table.

    Attributes:
        page_num: Page number where table appears
        caption: Table caption if available
        num_rows: Number of rows
        num_cols: Number of columns
        has_header: Whether table has a header row
        bbox: Bounding box if available
        table_id: Unique identifier (e.g., "table-0")
    """
    page_num: int
    caption: Optional[str] = None
    num_rows: int = 0
    num_cols: int = 0
    has_header: bool = False
    bbox: Optional[tuple[float, float, float, float]] = None
    table_id: str = ""


@dataclass
class PictureInfo:
    """Information about a document picture.

    Attributes:
        page_num: Page number where picture appears
        picture_type: Classification type
        caption: Picture caption if available
        confidence: Classification confidence (0-1)
        bbox: Bounding box if available
        picture_id: Unique identifier (e.g., "picture-0")
    """
    page_num: int
    picture_type: PictureType
    caption: Optional[str] = None
    confidence: float = 0.0
    bbox: Optional[tuple[float, float, float, float]] = None
    picture_id: str = ""


@dataclass
class CodeBlockInfo:
    """Information about a code block (if code enrichment enabled).

    Attributes:
        page_num: Page number where code appears
        language: Detected programming language
        num_lines: Number of lines
        bbox: Bounding box if available
    """
    page_num: int
    language: Optional[str] = None
    num_lines: int = 0
    bbox: Optional[tuple[float, float, float, float]] = None


@dataclass
class FormulaInfo:
    """Information about a formula (if formula enrichment enabled).

    Attributes:
        page_num: Page number where formula appears
        latex: LaTeX representation of formula
        bbox: Bounding box if available
    """
    page_num: int
    latex: Optional[str] = None
    bbox: Optional[tuple[float, float, float, float]] = None


@dataclass
class DocumentStructure:
    """Complete document structure metadata.

    Attributes:
        headings: List of document headings
        tables: List of tables
        pictures: List of pictures
        code_blocks: List of code blocks
        formulas: List of formulas
        total_sections: Total number of sections
        max_heading_depth: Maximum heading nesting depth
        has_table_of_contents: Whether document has a TOC
    """
    headings: List[HeadingInfo] = field(default_factory=list)
    tables: List[TableInfo] = field(default_factory=list)
    pictures: List[PictureInfo] = field(default_factory=list)
    code_blocks: List[CodeBlockInfo] = field(default_factory=list)
    formulas: List[FormulaInfo] = field(default_factory=list)

    # Summary statistics
    total_sections: int = 0
    max_heading_depth: int = 0
    has_table_of_contents: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "headings": [
                {
                    "text": h.text,
                    "level": h.level.name,
                    "page": h.page_num,
                    "section_path": h.section_path,
                    "bbox": h.bbox
                }
                for h in self.headings
            ],
            "tables": [
                {
                    "page": t.page_num,
                    "caption": t.caption,
                    "rows": t.num_rows,
                    "cols": t.num_cols,
                    "has_header": t.has_header,
                    "table_id": t.table_id,
                    "bbox": t.bbox
                }
                for t in self.tables
            ],
            "pictures": [
                {
                    "page": p.page_num,
                    "type": p.picture_type.value,
                    "caption": p.caption,
                    "confidence": p.confidence,
                    "picture_id": p.picture_id,
                    "bbox": p.bbox
                }
                for p in self.pictures
            ],
            "code_blocks": [
                {
                    "page": c.page_num,
                    "language": c.language,
                    "lines": c.num_lines,
                    "bbox": c.bbox
                }
                for c in self.code_blocks
            ],
            "formulas": [
                {
                    "page": f.page_num,
                    "latex": f.latex,
                    "bbox": f.bbox
                }
                for f in self.formulas
            ],
            "summary": {
                "total_sections": self.total_sections,
                "max_depth": self.max_heading_depth,
                "has_toc": self.has_table_of_contents
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentStructure":
        """Create from dictionary."""
        structure = cls()

        # Parse headings
        for h in data.get("headings", []):
            structure.headings.append(HeadingInfo(
                text=h["text"],
                level=HeadingLevel[h["level"]],
                page_num=h["page"],
                section_path=h.get("section_path", ""),
                bbox=tuple(h["bbox"]) if h.get("bbox") else None
            ))

        # Parse tables
        for t in data.get("tables", []):
            structure.tables.append(TableInfo(
                page_num=t["page"],
                caption=t.get("caption"),
                num_rows=t.get("rows", 0),
                num_cols=t.get("cols", 0),
                has_header=t.get("has_header", False),
                table_id=t.get("table_id", ""),
                bbox=tuple(t["bbox"]) if t.get("bbox") else None
            ))

        # Parse pictures
        for p in data.get("pictures", []):
            structure.pictures.append(PictureInfo(
                page_num=p["page"],
                picture_type=PictureType(p["type"]),
                caption=p.get("caption"),
                confidence=p.get("confidence", 0.0),
                picture_id=p.get("picture_id", ""),
                bbox=tuple(p["bbox"]) if p.get("bbox") else None
            ))

        # Parse code blocks
        for c in data.get("code_blocks", []):
            structure.code_blocks.append(CodeBlockInfo(
                page_num=c["page"],
                language=c.get("language"),
                num_lines=c.get("lines", 0),
                bbox=tuple(c["bbox"]) if c.get("bbox") else None
            ))

        # Parse formulas
        for f in data.get("formulas", []):
            structure.formulas.append(FormulaInfo(
                page_num=f["page"],
                latex=f.get("latex"),
                bbox=tuple(f["bbox"]) if f.get("bbox") else None
            ))

        # Parse summary
        summary = data.get("summary", {})
        structure.total_sections = summary.get("total_sections", 0)
        structure.max_heading_depth = summary.get("max_depth", 0)
        structure.has_table_of_contents = summary.get("has_toc", False)

        return structure

    def size_estimate_kb(self) -> float:
        """Estimate serialized size in KB."""
        serialized = json.dumps(self.to_dict())
        return len(serialized) / 1024


@dataclass
class ChunkContext:
    """Contextual metadata for a text chunk.

    Attributes:
        parent_heading: Immediate parent heading text
        parent_heading_level: Parent heading level (0=title, 1=section, etc.)
        section_path: Breadcrumb of headings (e.g., "Intro > Methods > Data")
        element_type: Type of element (text, list_item, table_cell, etc.)
        related_tables: IDs of tables mentioned in chunk
        related_pictures: IDs of pictures mentioned in chunk
        page_nums: Pages spanned by chunk (usually 1)
        is_page_boundary: True if chunk crosses page boundary
    """
    parent_heading: Optional[str] = None
    parent_heading_level: Optional[int] = None
    section_path: str = ""
    element_type: str = "text"
    related_tables: List[str] = field(default_factory=list)
    related_pictures: List[str] = field(default_factory=list)
    page_nums: List[int] = field(default_factory=list)
    is_page_boundary: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "parent_heading": self.parent_heading,
            "parent_heading_level": self.parent_heading_level,
            "section_path": self.section_path,
            "element_type": self.element_type,
            "related_tables": self.related_tables,
            "related_pictures": self.related_pictures,
            "page_nums": self.page_nums,
            "is_page_boundary": self.is_page_boundary
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChunkContext":
        """Create from dictionary."""
        return cls(
            parent_heading=data.get("parent_heading"),
            parent_heading_level=data.get("parent_heading_level"),
            section_path=data.get("section_path", ""),
            element_type=data.get("element_type", "text"),
            related_tables=data.get("related_tables", []),
            related_pictures=data.get("related_pictures", []),
            page_nums=data.get("page_nums", []),
            is_page_boundary=data.get("is_page_boundary", False)
        )


def estimate_metadata_size(metadata: dict) -> int:
    """Estimate serialized metadata size in bytes.

    Args:
        metadata: Metadata dictionary

    Returns:
        Estimated size in bytes
    """
    serialized = json.dumps(metadata, default=str)
    return len(serialized.encode('utf-8'))


def validate_metadata_size(metadata: dict, max_size_kb: int = 50) -> None:
    """Validate metadata size within limits.

    Args:
        metadata: Metadata dictionary
        max_size_kb: Maximum allowed size in KB

    Raises:
        ValueError: If metadata exceeds size limit
    """
    size_bytes = estimate_metadata_size(metadata)
    size_kb = size_bytes / 1024

    if size_kb > max_size_kb:
        raise ValueError(
            f"Metadata size {size_kb:.1f}KB exceeds limit {max_size_kb}KB"
        )


def validate_document_structure(structure: DocumentStructure) -> None:
    """Validate document structure consistency.

    Args:
        structure: DocumentStructure to validate

    Raises:
        AssertionError: If structure is invalid
    """
    # Check heading consistency
    assert all(h.page_num > 0 for h in structure.headings), \
        "Invalid page numbers in headings"
    assert all(h.text.strip() for h in structure.headings), \
        "Empty heading text"

    # Check table consistency
    assert all(t.num_rows >= 0 for t in structure.tables), \
        "Invalid row count in tables"
    assert all(t.num_cols >= 0 for t in structure.tables), \
        "Invalid column count in tables"

    # Check picture consistency
    assert all(0 <= p.confidence <= 1 for p in structure.pictures), \
        "Invalid confidence values in pictures"

    # Check size limit
    size_kb = structure.size_estimate_kb()
    assert size_kb < 200, f"Structure size {size_kb:.1f}KB too large"


def validate_chunk_context(context: ChunkContext) -> None:
    """Validate chunk context consistency.

    Args:
        context: ChunkContext to validate

    Raises:
        AssertionError: If context is invalid
    """
    # Check heading level
    if context.parent_heading_level is not None:
        assert 0 <= context.parent_heading_level <= 10, \
            f"Invalid heading level: {context.parent_heading_level}"

    # Check section path length
    if context.section_path:
        assert len(context.section_path) < 500, \
            "Section path too long"

    # Check element type
    valid_types = ["text", "list_item", "table_cell", "caption", "code", "formula"]
    assert context.element_type in valid_types, \
        f"Invalid element type: {context.element_type}"

    # Check page numbers
    assert all(p > 0 for p in context.page_nums), \
        "Invalid page numbers"
