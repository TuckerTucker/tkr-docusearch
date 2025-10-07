# Structure Extraction Contract

**Contract ID**: STRUCT-001
**Version**: 1.0
**Status**: Specification
**Owner**: structure-agent
**Consumers**: metadata-agent, integration-agent

## Purpose

Define the data format and interface for document structure extraction from DoclingDocument, including hierarchical headings, tables, pictures, and other structural elements.

## Data Structures

### DocumentStructure

```python
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

class HeadingLevel(Enum):
    """Hierarchical heading levels."""
    TITLE = 0
    SECTION_HEADER = 1
    SUB_SECTION_HEADER = 2
    PARAGRAPH_HEADER = 3

class PictureType(Enum):
    """Picture classification types from Docling."""
    CHART = "chart"           # Bar chart, line chart, pie chart
    DIAGRAM = "diagram"       # Flow diagram, architecture diagram
    PHOTO = "photo"           # Photograph
    LOGO = "logo"             # Company/product logo
    SIGNATURE = "signature"   # Handwritten signature
    OTHER = "other"           # Unknown/other type

@dataclass
class HeadingInfo:
    """Information about a document heading."""
    text: str
    level: HeadingLevel
    page_num: int
    bbox: Optional[tuple[float, float, float, float]] = None  # (x1, y1, x2, y2)
    section_path: str = ""  # e.g., "1.2.3" or "Introduction > Methods"

@dataclass
class TableInfo:
    """Information about a document table."""
    page_num: int
    caption: Optional[str] = None
    num_rows: int = 0
    num_cols: int = 0
    has_header: bool = False
    bbox: Optional[tuple[float, float, float, float]] = None
    table_id: str = ""  # e.g., "table-0", "table-1"

@dataclass
class PictureInfo:
    """Information about a document picture."""
    page_num: int
    picture_type: PictureType
    caption: Optional[str] = None
    confidence: float = 0.0  # Classification confidence 0-1
    bbox: Optional[tuple[float, float, float, float]] = None
    picture_id: str = ""  # e.g., "picture-0", "picture-1"

@dataclass
class CodeBlockInfo:
    """Information about a code block (if code enrichment enabled)."""
    page_num: int
    language: Optional[str] = None
    num_lines: int = 0
    bbox: Optional[tuple[float, float, float, float]] = None

@dataclass
class FormulaInfo:
    """Information about a formula (if formula enrichment enabled)."""
    page_num: int
    latex: Optional[str] = None
    bbox: Optional[tuple[float, float, float, float]] = None

@dataclass
class DocumentStructure:
    """Complete document structure metadata."""
    headings: List[HeadingInfo]
    tables: List[TableInfo]
    pictures: List[PictureInfo]
    code_blocks: List[CodeBlockInfo]
    formulas: List[FormulaInfo]

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

    def size_estimate_kb(self) -> float:
        """Estimate serialized size in KB."""
        import json
        serialized = json.dumps(self.to_dict())
        return len(serialized) / 1024
```

## Extraction Interface

### Main Function

```python
def extract_document_structure(
    doc: DoclingDocument,
    config: EnhancedModeConfig
) -> DocumentStructure:
    """
    Extract document structure from DoclingDocument.

    Args:
        doc: Parsed DoclingDocument from Docling
        config: Enhanced mode configuration

    Returns:
        DocumentStructure with all extracted elements

    Raises:
        StructureExtractionError: If extraction fails
    """
    structure = DocumentStructure(
        headings=[],
        tables=[],
        pictures=[],
        code_blocks=[],
        formulas=[]
    )

    # Extract headings
    structure.headings = _extract_headings(doc)

    # Extract tables (if enabled)
    if config.enable_table_structure:
        structure.tables = _extract_tables(doc)

    # Extract pictures (if enabled)
    if config.enable_picture_classification:
        structure.pictures = _extract_pictures(doc)

    # Extract code blocks (if enabled)
    if config.enable_code_enrichment:
        structure.code_blocks = _extract_code_blocks(doc)

    # Extract formulas (if enabled)
    if config.enable_formula_enrichment:
        structure.formulas = _extract_formulas(doc)

    # Calculate summary statistics
    structure.total_sections = len(structure.headings)
    structure.max_heading_depth = _calculate_max_depth(structure.headings)
    structure.has_table_of_contents = _detect_toc(structure.headings)

    # Validate size
    if structure.size_estimate_kb() > config.max_structure_size_kb:
        raise StructureExtractionError(
            f"Structure size {structure.size_estimate_kb():.1f}KB exceeds "
            f"limit {config.max_structure_size_kb}KB"
        )

    return structure
```

## Extraction Details

### Heading Extraction

```python
def _extract_headings(doc: DoclingDocument) -> List[HeadingInfo]:
    """Extract hierarchical headings from document."""
    headings = []

    # Map Docling labels to heading levels
    LABEL_TO_LEVEL = {
        "TITLE": HeadingLevel.TITLE,
        "SECTION_HEADER": HeadingLevel.SECTION_HEADER,
        # Add more mappings based on Docling's actual labels
    }

    for text_item in doc.texts:
        if text_item.label in LABEL_TO_LEVEL:
            # Get page number from provenance
            page_num = text_item.prov[0].page_no if text_item.prov else 0

            # Get bounding box if available
            bbox = None
            if text_item.prov and hasattr(text_item.prov[0], 'bbox'):
                prov_bbox = text_item.prov[0].bbox
                bbox = (prov_bbox.l, prov_bbox.t, prov_bbox.r, prov_bbox.b)

            heading = HeadingInfo(
                text=text_item.text,
                level=LABEL_TO_LEVEL[text_item.label],
                page_num=page_num,
                bbox=bbox,
                section_path=_build_section_path(text_item, doc)
            )
            headings.append(heading)

    return headings
```

### Table Extraction

```python
def _extract_tables(doc: DoclingDocument) -> List[TableInfo]:
    """Extract table metadata from document."""
    tables = []

    for idx, table_item in enumerate(doc.tables):
        page_num = table_item.prov[0].page_no if table_item.prov else 0

        # Get table dimensions
        num_rows = 0
        num_cols = 0
        has_header = False
        if hasattr(table_item, 'data') and table_item.data:
            # Docling provides table data structure
            num_rows = len(table_item.data.table_cells) if hasattr(table_item.data, 'table_cells') else 0
            # Determine num_cols from data structure
            # Detect if first row is header

        # Get caption
        caption = None
        if hasattr(table_item, 'caption') and table_item.caption:
            caption = table_item.caption

        # Get bbox
        bbox = None
        if table_item.prov and hasattr(table_item.prov[0], 'bbox'):
            prov_bbox = table_item.prov[0].bbox
            bbox = (prov_bbox.l, prov_bbox.t, prov_bbox.r, prov_bbox.b)

        table = TableInfo(
            page_num=page_num,
            caption=caption,
            num_rows=num_rows,
            num_cols=num_cols,
            has_header=has_header,
            bbox=bbox,
            table_id=f"table-{idx}"
        )
        tables.append(table)

    return tables
```

### Picture Extraction

```python
def _extract_pictures(doc: DoclingDocument) -> List[PictureInfo]:
    """Extract picture metadata with classification."""
    pictures = []

    for idx, picture_item in enumerate(doc.pictures):
        page_num = picture_item.prov[0].page_no if picture_item.prov else 0

        # Get classification if available
        picture_type = PictureType.OTHER
        confidence = 0.0
        if hasattr(picture_item, 'classification') and picture_item.classification:
            # Map Docling classification to PictureType
            classification = picture_item.classification
            if hasattr(classification, 'label'):
                picture_type = _map_picture_type(classification.label)
            if hasattr(classification, 'confidence'):
                confidence = classification.confidence

        # Get caption
        caption = None
        if hasattr(picture_item, 'caption') and picture_item.caption:
            caption = picture_item.caption

        # Get bbox
        bbox = None
        if picture_item.prov and hasattr(picture_item.prov[0], 'bbox'):
            prov_bbox = picture_item.prov[0].bbox
            bbox = (prov_bbox.l, prov_bbox.t, prov_bbox.r, prov_bbox.b)

        picture = PictureInfo(
            page_num=page_num,
            picture_type=picture_type,
            caption=caption,
            confidence=confidence,
            bbox=bbox,
            picture_id=f"picture-{idx}"
        )
        pictures.append(picture)

    return pictures
```

## Integration with Docling Parser

### Updated docling_parser.py

```python
# In _parse_with_docling() method

from src.processing.structure_extractor import extract_document_structure
from src.config.processing_config import EnhancedModeConfig

def _parse_with_docling(self, file_path: str, config: EnhancedModeConfig) -> tuple:
    """Parse document using Docling with structure extraction."""

    # Create pipeline options from config
    pipeline_options = create_pipeline_options(config)

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    result = converter.convert(file_path)

    # Extract structure
    structure = extract_document_structure(result.document, config)

    # Convert to pages
    pages = docling_to_pages(result)

    # Build metadata including structure
    metadata = {
        "title": result.document.name if hasattr(result.document, 'name') else "",
        "format": Path(file_path).suffix.lower()[1:],
        "num_pages": len(pages),
        "structure": structure.to_dict()  # Add structure to metadata
    }

    return pages, metadata
```

## Validation Requirements

### Structure Validation

```python
def validate_structure(structure: DocumentStructure) -> None:
    """Validate extracted structure."""
    # Check heading consistency
    assert all(h.page_num > 0 for h in structure.headings), "Invalid page numbers"
    assert all(h.text.strip() for h in structure.headings), "Empty heading text"

    # Check table consistency
    assert all(t.num_rows >= 0 for t in structure.tables), "Invalid row count"
    assert all(t.num_cols >= 0 for t in structure.tables), "Invalid col count"

    # Check picture consistency
    assert all(0 <= p.confidence <= 1 for p in structure.pictures), "Invalid confidence"

    # Check size limit
    assert structure.size_estimate_kb() < 200, "Structure too large"
```

## Performance Requirements

- **Extraction time**: <5% of total processing time
- **Memory overhead**: <50MB for structure metadata
- **Size limit**: <100KB serialized (configurable)

## Testing Contract

### Unit Tests Required
- ✅ Extract headings from sample DoclingDocument
- ✅ Extract tables with correct dimensions
- ✅ Extract pictures with classifications
- ✅ Handle documents with no structure
- ✅ Handle documents with partial structure
- ✅ Size validation works correctly

### Integration Tests Required
- ✅ Structure extracted for real documents
- ✅ Structure stored in metadata successfully
- ✅ Structure size within limits
- ✅ Feature flags control extraction

## File Locations

- `src/processing/structure_extractor.py` - Main extraction logic
- `src/processing/docling_parser.py` - Integration point

## Version History

- **1.0** (2025-10-07): Initial specification
