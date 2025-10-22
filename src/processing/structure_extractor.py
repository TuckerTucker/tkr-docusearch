"""
Document structure extraction from DoclingDocument.

This module extracts hierarchical document structure including headings,
tables, pictures, code blocks, and formulas from Docling's parsed output.
"""

import logging
from typing import List

from docling_core.types.doc import DoclingDocument

from src.config.processing_config import EnhancedModeConfig
from src.storage.metadata_schema import (
    CodeBlockInfo,
    DocumentStructure,
    FormulaInfo,
    HeadingInfo,
    HeadingLevel,
    PictureInfo,
    PictureType,
    TableInfo,
)

logger = logging.getLogger(__name__)


class StructureExtractionError(Exception):
    """Raised when structure extraction fails."""


def extract_document_structure(
    doc: DoclingDocument, config: EnhancedModeConfig
) -> DocumentStructure:
    """Extract document structure from DoclingDocument.

    Args:
        doc: Parsed DoclingDocument from Docling
        config: Enhanced mode configuration

    Returns:
        DocumentStructure with all extracted elements

    Raises:
        StructureExtractionError: If extraction fails or size limit exceeded
    """
    try:
        structure = DocumentStructure()

        # Extract headings (always enabled)
        structure.headings = _extract_headings(doc)
        logger.debug(f"Extracted {len(structure.headings)} headings")

        # Extract tables (if enabled)
        if config.enable_table_structure:
            structure.tables = _extract_tables(doc)
            logger.debug(f"Extracted {len(structure.tables)} tables")

        # Extract pictures (if enabled)
        if config.enable_picture_classification:
            structure.pictures = _extract_pictures(doc)
            logger.debug(f"Extracted {len(structure.pictures)} pictures")

        # Extract code blocks (if enabled)
        if config.enable_code_enrichment:
            structure.code_blocks = _extract_code_blocks(doc)
            logger.debug(f"Extracted {len(structure.code_blocks)} code blocks")

        # Extract formulas (if enabled)
        if config.enable_formula_enrichment:
            structure.formulas = _extract_formulas(doc)
            logger.debug(f"Extracted {len(structure.formulas)} formulas")

        # Calculate summary statistics
        structure.total_sections = len(structure.headings)
        structure.max_heading_depth = _calculate_max_depth(structure.headings)
        structure.has_table_of_contents = _detect_toc(structure.headings)

        # Validate size
        size_kb = structure.size_estimate_kb()
        if size_kb > config.max_structure_size_kb:
            raise StructureExtractionError(
                f"Structure size {size_kb:.1f}KB exceeds " f"limit {config.max_structure_size_kb}KB"
            )

        logger.info(
            f"Structure extraction complete: {len(structure.headings)} headings, "
            f"{len(structure.tables)} tables, {len(structure.pictures)} pictures, "
            f"size={size_kb:.1f}KB"
        )

        return structure

    except Exception as e:
        logger.error(f"Structure extraction failed: {e}")
        raise StructureExtractionError(f"Failed to extract structure: {e}") from e


def _extract_headings(doc: DoclingDocument) -> List[HeadingInfo]:
    """Extract hierarchical headings from document.

    Args:
        doc: DoclingDocument

    Returns:
        List of HeadingInfo objects
    """
    headings: List[HeadingInfo] = []

    # Map Docling labels to heading levels
    LABEL_TO_LEVEL = {
        "title": HeadingLevel.TITLE,
        "section_header": HeadingLevel.SECTION_HEADER,
        "page_header": HeadingLevel.SECTION_HEADER,
        "subtitle": HeadingLevel.SUB_SECTION_HEADER,
    }

    if not hasattr(doc, "texts") or not doc.texts:
        return headings

    for text_item in doc.texts:
        # Check if this is a heading
        label = text_item.label.lower() if hasattr(text_item, "label") else None
        if label not in LABEL_TO_LEVEL:
            continue

        # Get page number from provenance
        page_num = 1
        if hasattr(text_item, "prov") and text_item.prov:
            page_num = text_item.prov[0].page_no if hasattr(text_item.prov[0], "page_no") else 1

        # Get bounding box if available
        bbox = None
        if hasattr(text_item, "prov") and text_item.prov:
            prov = text_item.prov[0]
            if hasattr(prov, "bbox"):
                try:
                    prov_bbox = prov.bbox
                    bbox = (prov_bbox.l, prov_bbox.t, prov_bbox.r, prov_bbox.b)
                except (AttributeError, TypeError):
                    pass

        # Build section path
        section_path = _build_section_path(text_item, doc, headings)

        heading = HeadingInfo(
            text=text_item.text if hasattr(text_item, "text") else "",
            level=LABEL_TO_LEVEL[label],
            page_num=page_num,
            bbox=bbox,
            section_path=section_path,
        )
        headings.append(heading)

    return headings


def _extract_tables(doc: DoclingDocument) -> List[TableInfo]:
    """Extract table metadata from document.

    Args:
        doc: DoclingDocument

    Returns:
        List of TableInfo objects
    """
    tables: List[TableInfo] = []

    if not hasattr(doc, "tables") or not doc.tables:
        return tables

    for idx, table_item in enumerate(doc.tables):
        # Get page number
        page_num = 1
        if hasattr(table_item, "prov") and table_item.prov:
            page_num = table_item.prov[0].page_no if hasattr(table_item.prov[0], "page_no") else 1

        # Get caption
        caption = None
        if hasattr(table_item, "caption") and table_item.caption:
            caption = str(table_item.caption)

        # Get table dimensions
        num_rows = 0
        num_cols = 0
        has_header = False

        if hasattr(table_item, "data") and table_item.data:
            # Try to get dimensions from table data
            try:
                if hasattr(table_item.data, "num_rows"):
                    num_rows = table_item.data.num_rows
                if hasattr(table_item.data, "num_cols"):
                    num_cols = table_item.data.num_cols
                # Check for header row
                if hasattr(table_item.data, "grid") and table_item.data.grid:
                    # Heuristic: if first row cells have different formatting, likely header
                    has_header = True
            except (AttributeError, TypeError):
                pass

        # Get bbox
        bbox = None
        if hasattr(table_item, "prov") and table_item.prov:
            prov = table_item.prov[0]
            if hasattr(prov, "bbox"):
                try:
                    prov_bbox = prov.bbox
                    bbox = (prov_bbox.l, prov_bbox.t, prov_bbox.r, prov_bbox.b)
                except (AttributeError, TypeError):
                    pass

        table = TableInfo(
            page_num=page_num,
            caption=caption,
            num_rows=num_rows,
            num_cols=num_cols,
            has_header=has_header,
            bbox=bbox,
            table_id=f"table-{idx}",
        )
        tables.append(table)

    return tables


def _extract_pictures(doc: DoclingDocument) -> List[PictureInfo]:
    """Extract picture metadata with classification.

    Args:
        doc: DoclingDocument

    Returns:
        List of PictureInfo objects
    """
    pictures: List[PictureInfo] = []

    if not hasattr(doc, "pictures") or not doc.pictures:
        return pictures

    for idx, picture_item in enumerate(doc.pictures):
        # Get page number
        page_num = 1
        if hasattr(picture_item, "prov") and picture_item.prov:
            page_num = (
                picture_item.prov[0].page_no if hasattr(picture_item.prov[0], "page_no") else 1
            )

        # Get classification if available
        picture_type = PictureType.OTHER
        confidence = 0.0

        if hasattr(picture_item, "annotations") and picture_item.annotations:
            # Docling stores classification in annotations
            for annotation in picture_item.annotations:
                if hasattr(annotation, "label") and hasattr(annotation, "score"):
                    # Map Docling label to PictureType
                    picture_type = _map_picture_type(annotation.label)
                    confidence = float(annotation.score)
                    break

        # Get caption
        caption = None
        if hasattr(picture_item, "caption") and picture_item.caption:
            caption = str(picture_item.caption)

        # Get bbox
        bbox = None
        if hasattr(picture_item, "prov") and picture_item.prov:
            prov = picture_item.prov[0]
            if hasattr(prov, "bbox"):
                try:
                    prov_bbox = prov.bbox
                    bbox = (prov_bbox.l, prov_bbox.t, prov_bbox.r, prov_bbox.b)
                except (AttributeError, TypeError):
                    pass

        picture = PictureInfo(
            page_num=page_num,
            picture_type=picture_type,
            caption=caption,
            confidence=confidence,
            bbox=bbox,
            picture_id=f"picture-{idx}",
        )
        pictures.append(picture)

    return pictures


def _extract_code_blocks(doc: DoclingDocument) -> List[CodeBlockInfo]:
    """Extract code block information.

    Args:
        doc: DoclingDocument

    Returns:
        List of CodeBlockInfo objects
    """
    code_blocks: List[CodeBlockInfo] = []

    if not hasattr(doc, "texts") or not doc.texts:
        return code_blocks

    for text_item in doc.texts:
        # Check if this is a code block
        if not hasattr(text_item, "label"):
            continue

        label = text_item.label.lower()
        if label != "code":
            continue

        # Get page number
        page_num = 1
        if hasattr(text_item, "prov") and text_item.prov:
            page_num = text_item.prov[0].page_no if hasattr(text_item.prov[0], "page_no") else 1

        # Get language (if detected)
        language = None
        if hasattr(text_item, "metadata") and text_item.metadata:
            language = text_item.metadata.get("language")

        # Get number of lines
        num_lines = 0
        if hasattr(text_item, "text") and text_item.text:
            num_lines = len(text_item.text.split("\n"))

        # Get bbox
        bbox = None
        if hasattr(text_item, "prov") and text_item.prov:
            prov = text_item.prov[0]
            if hasattr(prov, "bbox"):
                try:
                    prov_bbox = prov.bbox
                    bbox = (prov_bbox.l, prov_bbox.t, prov_bbox.r, prov_bbox.b)
                except (AttributeError, TypeError):
                    pass

        code_block = CodeBlockInfo(
            page_num=page_num, language=language, num_lines=num_lines, bbox=bbox
        )
        code_blocks.append(code_block)

    return code_blocks


def _extract_formulas(doc: DoclingDocument) -> List[FormulaInfo]:
    """Extract formula information.

    Args:
        doc: DoclingDocument

    Returns:
        List of FormulaInfo objects
    """
    formulas: List[FormulaInfo] = []

    if not hasattr(doc, "texts") or not doc.texts:
        return formulas

    for text_item in doc.texts:
        # Check if this is a formula
        if not hasattr(text_item, "label"):
            continue

        label = text_item.label.lower()
        if label != "formula":
            continue

        # Get page number
        page_num = 1
        if hasattr(text_item, "prov") and text_item.prov:
            page_num = text_item.prov[0].page_no if hasattr(text_item.prov[0], "page_no") else 1

        # Get LaTeX (if extracted)
        latex = None
        if hasattr(text_item, "text") and text_item.text:
            latex = text_item.text

        # Get bbox
        bbox = None
        if hasattr(text_item, "prov") and text_item.prov:
            prov = text_item.prov[0]
            if hasattr(prov, "bbox"):
                try:
                    prov_bbox = prov.bbox
                    bbox = (prov_bbox.l, prov_bbox.t, prov_bbox.r, prov_bbox.b)
                except (AttributeError, TypeError):
                    pass

        formula = FormulaInfo(page_num=page_num, latex=latex, bbox=bbox)
        formulas.append(formula)

    return formulas


def _map_picture_type(docling_label: str) -> PictureType:
    """Map Docling picture classification label to PictureType.

    Args:
        docling_label: Label from Docling classifier

    Returns:
        Corresponding PictureType
    """
    label_lower = docling_label.lower()

    # Map common Docling labels
    if any(word in label_lower for word in ["chart", "graph", "plot"]):
        return PictureType.CHART
    elif any(word in label_lower for word in ["diagram", "flow", "architecture"]):
        return PictureType.DIAGRAM
    elif any(word in label_lower for word in ["photo", "image"]):
        return PictureType.PHOTO
    elif "logo" in label_lower:
        return PictureType.LOGO
    elif "signature" in label_lower:
        return PictureType.SIGNATURE
    else:
        return PictureType.OTHER


def _build_section_path(
    text_item, doc: DoclingDocument, previous_headings: List[HeadingInfo]
) -> str:
    """Build hierarchical section path for a heading.

    Args:
        text_item: Current text item
        doc: DoclingDocument
        previous_headings: Previously extracted headings

    Returns:
        Section path string (e.g., "1. Introduction" or "Intro > Methods")
    """
    # Simple implementation: use heading text
    # More sophisticated version would track hierarchy
    if hasattr(text_item, "text") and text_item.text:
        return text_item.text
    return ""


def _calculate_max_depth(headings: List[HeadingInfo]) -> int:
    """Calculate maximum heading nesting depth.

    Args:
        headings: List of headings

    Returns:
        Maximum depth (0-based)
    """
    if not headings:
        return 0

    return max(h.level.value for h in headings)


def _detect_toc(headings: List[HeadingInfo]) -> bool:
    """Detect if document has a table of contents.

    Args:
        headings: List of headings

    Returns:
        True if TOC detected
    """
    # Simple heuristic: look for "table of contents" or "contents" heading
    for heading in headings:
        text_lower = heading.text.lower()
        if any(word in text_lower for word in ["table of contents", "contents"]):
            if heading.level in [HeadingLevel.TITLE, HeadingLevel.SECTION_HEADER]:
                return True

    return False
