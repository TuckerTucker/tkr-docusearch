"""
Tests for storage/metadata_schema.py module.

Tests cover:
- Data class creation and serialization
- DocumentStructure to_dict/from_dict
- ChunkContext to_dict/from_dict
- Metadata size estimation
- Metadata validation
- Document structure validation
- Chunk context validation
- Edge cases and error handling
"""

import pytest

from storage.metadata_schema import (
    ChunkContext,
    CodeBlockInfo,
    DocumentStructure,
    FormulaInfo,
    HeadingInfo,
    HeadingLevel,
    PictureInfo,
    PictureType,
    TableInfo,
    estimate_metadata_size,
    validate_chunk_context,
    validate_document_structure,
    validate_metadata_size,
)


class TestEnums:
    """Test enum definitions."""

    def test_heading_level_enum(self):
        """Test HeadingLevel enum values."""
        assert HeadingLevel.TITLE.value == 0
        assert HeadingLevel.SECTION_HEADER.value == 1
        assert HeadingLevel.SUB_SECTION_HEADER.value == 2
        assert HeadingLevel.PARAGRAPH_HEADER.value == 3

    def test_picture_type_enum(self):
        """Test PictureType enum values."""
        assert PictureType.CHART.value == "chart"
        assert PictureType.DIAGRAM.value == "diagram"
        assert PictureType.PHOTO.value == "photo"
        assert PictureType.LOGO.value == "logo"
        assert PictureType.SIGNATURE.value == "signature"
        assert PictureType.OTHER.value == "other"


class TestHeadingInfo:
    """Test HeadingInfo data class."""

    def test_heading_info_creation(self):
        """Test basic heading info creation."""
        heading = HeadingInfo(text="Introduction", level=HeadingLevel.SECTION_HEADER, page_num=1)

        assert heading.text == "Introduction"
        assert heading.level == HeadingLevel.SECTION_HEADER
        assert heading.page_num == 1
        assert heading.bbox is None
        assert heading.section_path == ""

    def test_heading_info_with_bbox(self):
        """Test heading info with bounding box."""
        heading = HeadingInfo(
            text="Methods",
            level=HeadingLevel.SUB_SECTION_HEADER,
            page_num=2,
            bbox=(10.0, 20.0, 100.0, 50.0),
            section_path="1.2",
        )

        assert heading.bbox == (10.0, 20.0, 100.0, 50.0)
        assert heading.section_path == "1.2"


class TestTableInfo:
    """Test TableInfo data class."""

    def test_table_info_creation(self):
        """Test basic table info creation."""
        table = TableInfo(page_num=3)

        assert table.page_num == 3
        assert table.caption is None
        assert table.num_rows == 0
        assert table.num_cols == 0
        assert table.has_header is False
        assert table.bbox is None
        assert table.table_id == ""

    def test_table_info_complete(self):
        """Test table info with all fields."""
        table = TableInfo(
            page_num=5,
            caption="Results Summary",
            num_rows=10,
            num_cols=5,
            has_header=True,
            bbox=(50.0, 100.0, 400.0, 300.0),
            table_id="table-0",
        )

        assert table.caption == "Results Summary"
        assert table.num_rows == 10
        assert table.num_cols == 5
        assert table.has_header is True
        assert table.table_id == "table-0"


class TestPictureInfo:
    """Test PictureInfo data class."""

    def test_picture_info_creation(self):
        """Test basic picture info creation."""
        picture = PictureInfo(page_num=7, picture_type=PictureType.CHART)

        assert picture.page_num == 7
        assert picture.picture_type == PictureType.CHART
        assert picture.caption is None
        assert picture.confidence == 0.0
        assert picture.bbox is None
        assert picture.picture_id == ""

    def test_picture_info_complete(self):
        """Test picture info with all fields."""
        picture = PictureInfo(
            page_num=8,
            picture_type=PictureType.DIAGRAM,
            caption="System Architecture",
            confidence=0.95,
            bbox=(100.0, 150.0, 500.0, 400.0),
            picture_id="picture-0",
        )

        assert picture.caption == "System Architecture"
        assert picture.confidence == 0.95
        assert picture.picture_id == "picture-0"


class TestCodeBlockInfo:
    """Test CodeBlockInfo data class."""

    def test_code_block_info_creation(self):
        """Test code block info creation."""
        code = CodeBlockInfo(page_num=10)

        assert code.page_num == 10
        assert code.language is None
        assert code.num_lines == 0
        assert code.bbox is None

    def test_code_block_info_complete(self):
        """Test code block info with all fields."""
        code = CodeBlockInfo(
            page_num=12, language="python", num_lines=25, bbox=(50.0, 200.0, 400.0, 500.0)
        )

        assert code.language == "python"
        assert code.num_lines == 25


class TestFormulaInfo:
    """Test FormulaInfo data class."""

    def test_formula_info_creation(self):
        """Test formula info creation."""
        formula = FormulaInfo(page_num=15)

        assert formula.page_num == 15
        assert formula.latex is None
        assert formula.bbox is None

    def test_formula_info_complete(self):
        """Test formula info with all fields."""
        formula = FormulaInfo(
            page_num=16, latex=r"\sum_{i=1}^{n} x_i", bbox=(100.0, 250.0, 300.0, 280.0)
        )

        assert formula.latex == r"\sum_{i=1}^{n} x_i"


class TestDocumentStructure:
    """Test DocumentStructure data class."""

    def test_document_structure_empty(self):
        """Test empty document structure."""
        structure = DocumentStructure()

        assert structure.headings == []
        assert structure.tables == []
        assert structure.pictures == []
        assert structure.code_blocks == []
        assert structure.formulas == []
        assert structure.total_sections == 0
        assert structure.max_heading_depth == 0
        assert structure.has_table_of_contents is False

    def test_document_structure_with_content(self):
        """Test document structure with content."""
        structure = DocumentStructure(
            headings=[
                HeadingInfo(text="Title", level=HeadingLevel.TITLE, page_num=1),
                HeadingInfo(text="Section 1", level=HeadingLevel.SECTION_HEADER, page_num=2),
            ],
            tables=[TableInfo(page_num=3, num_rows=5, num_cols=3)],
            pictures=[PictureInfo(page_num=4, picture_type=PictureType.CHART, confidence=0.9)],
            total_sections=2,
            max_heading_depth=1,
            has_table_of_contents=True,
        )

        assert len(structure.headings) == 2
        assert len(structure.tables) == 1
        assert len(structure.pictures) == 1
        assert structure.total_sections == 2
        assert structure.has_table_of_contents is True

    def test_document_structure_to_dict(self):
        """Test DocumentStructure serialization to dict."""
        structure = DocumentStructure(
            headings=[
                HeadingInfo(
                    text="Introduction",
                    level=HeadingLevel.SECTION_HEADER,
                    page_num=1,
                    section_path="1",
                )
            ],
            tables=[
                TableInfo(
                    page_num=2,
                    caption="Results",
                    num_rows=10,
                    num_cols=5,
                    has_header=True,
                    table_id="table-0",
                )
            ],
            pictures=[
                PictureInfo(
                    page_num=3,
                    picture_type=PictureType.DIAGRAM,
                    caption="Architecture",
                    confidence=0.85,
                    picture_id="picture-0",
                )
            ],
            code_blocks=[CodeBlockInfo(page_num=4, language="python", num_lines=20)],
            formulas=[FormulaInfo(page_num=5, latex=r"E = mc^2")],
            total_sections=3,
            max_heading_depth=2,
            has_table_of_contents=True,
        )

        data = structure.to_dict()

        # Check structure
        assert "headings" in data
        assert "tables" in data
        assert "pictures" in data
        assert "code_blocks" in data
        assert "formulas" in data
        assert "summary" in data

        # Check content
        assert len(data["headings"]) == 1
        assert data["headings"][0]["text"] == "Introduction"
        assert data["headings"][0]["level"] == "SECTION_HEADER"

        assert len(data["tables"]) == 1
        assert data["tables"][0]["caption"] == "Results"

        assert len(data["pictures"]) == 1
        assert data["pictures"][0]["type"] == "diagram"

        assert data["summary"]["total_sections"] == 3
        assert data["summary"]["has_toc"] is True

    def test_document_structure_from_dict(self):
        """Test DocumentStructure deserialization from dict."""
        data = {
            "headings": [
                {
                    "text": "Methods",
                    "level": "SUB_SECTION_HEADER",
                    "page": 2,
                    "section_path": "1.1",
                    "bbox": [10.0, 20.0, 100.0, 50.0],
                }
            ],
            "tables": [
                {
                    "page": 3,
                    "caption": "Data",
                    "rows": 15,
                    "cols": 4,
                    "has_header": True,
                    "table_id": "table-1",
                    "bbox": [50.0, 100.0, 400.0, 300.0],
                }
            ],
            "pictures": [
                {
                    "page": 4,
                    "type": "chart",
                    "caption": "Growth",
                    "confidence": 0.92,
                    "picture_id": "picture-1",
                    "bbox": [100.0, 150.0, 500.0, 400.0],
                }
            ],
            "code_blocks": [
                {
                    "page": 5,
                    "language": "javascript",
                    "lines": 30,
                    "bbox": [50.0, 200.0, 400.0, 500.0],
                }
            ],
            "formulas": [
                {
                    "page": 6,
                    "latex": r"\int_{0}^{\infty} e^{-x} dx",
                    "bbox": [100.0, 250.0, 300.0, 280.0],
                }
            ],
            "summary": {"total_sections": 5, "max_depth": 2, "has_toc": False},
        }

        structure = DocumentStructure.from_dict(data)

        # Check headings
        assert len(structure.headings) == 1
        assert structure.headings[0].text == "Methods"
        assert structure.headings[0].level == HeadingLevel.SUB_SECTION_HEADER
        assert structure.headings[0].page_num == 2

        # Check tables
        assert len(structure.tables) == 1
        assert structure.tables[0].num_rows == 15

        # Check pictures
        assert len(structure.pictures) == 1
        assert structure.pictures[0].picture_type == PictureType.CHART

        # Check summary
        assert structure.total_sections == 5
        assert structure.max_heading_depth == 2
        assert structure.has_table_of_contents is False

    def test_document_structure_round_trip(self):
        """Test DocumentStructure serialization round trip."""
        original = DocumentStructure(
            headings=[HeadingInfo(text="Test", level=HeadingLevel.TITLE, page_num=1)],
            total_sections=1,
        )

        data = original.to_dict()
        reconstructed = DocumentStructure.from_dict(data)

        assert len(reconstructed.headings) == 1
        assert reconstructed.headings[0].text == "Test"
        assert reconstructed.total_sections == 1

    def test_document_structure_size_estimate(self):
        """Test size estimation."""
        structure = DocumentStructure(
            headings=[
                HeadingInfo(text=f"Heading {i}", level=HeadingLevel.SECTION_HEADER, page_num=i)
                for i in range(1, 11)
            ]
        )

        size_kb = structure.size_estimate_kb()
        assert isinstance(size_kb, float)
        assert size_kb > 0


class TestChunkContext:
    """Test ChunkContext data class."""

    def test_chunk_context_empty(self):
        """Test empty chunk context."""
        context = ChunkContext()

        assert context.parent_heading is None
        assert context.parent_heading_level is None
        assert context.section_path == ""
        assert context.element_type == "text"
        assert context.related_tables == []
        assert context.related_pictures == []
        assert context.page_nums == []
        assert context.is_page_boundary is False

    def test_chunk_context_with_content(self):
        """Test chunk context with content."""
        context = ChunkContext(
            parent_heading="Introduction",
            parent_heading_level=1,
            section_path="1 > 1.1",
            element_type="list_item",
            related_tables=["table-0", "table-1"],
            related_pictures=["picture-0"],
            page_nums=[1, 2],
            is_page_boundary=True,
        )

        assert context.parent_heading == "Introduction"
        assert context.parent_heading_level == 1
        assert context.section_path == "1 > 1.1"
        assert context.element_type == "list_item"
        assert len(context.related_tables) == 2
        assert len(context.related_pictures) == 1
        assert context.page_nums == [1, 2]
        assert context.is_page_boundary is True

    def test_chunk_context_to_dict(self):
        """Test ChunkContext serialization."""
        context = ChunkContext(
            parent_heading="Methods",
            parent_heading_level=2,
            section_path="2 > 2.1 > 2.1.1",
            element_type="table_cell",
            related_tables=["table-2"],
            page_nums=[5],
        )

        data = context.to_dict()

        assert data["parent_heading"] == "Methods"
        assert data["parent_heading_level"] == 2
        assert data["section_path"] == "2 > 2.1 > 2.1.1"
        assert data["element_type"] == "table_cell"
        assert data["related_tables"] == ["table-2"]
        assert data["page_nums"] == [5]
        assert data["is_page_boundary"] is False

    def test_chunk_context_from_dict(self):
        """Test ChunkContext deserialization."""
        data = {
            "parent_heading": "Results",
            "parent_heading_level": 1,
            "section_path": "3",
            "element_type": "caption",
            "related_tables": [],
            "related_pictures": ["picture-5"],
            "page_nums": [10, 11],
            "is_page_boundary": True,
        }

        context = ChunkContext.from_dict(data)

        assert context.parent_heading == "Results"
        assert context.parent_heading_level == 1
        assert context.element_type == "caption"
        assert context.related_pictures == ["picture-5"]
        assert context.is_page_boundary is True

    def test_chunk_context_round_trip(self):
        """Test ChunkContext serialization round trip."""
        original = ChunkContext(parent_heading="Test", parent_heading_level=0, page_nums=[1])

        data = original.to_dict()
        reconstructed = ChunkContext.from_dict(data)

        assert reconstructed.parent_heading == "Test"
        assert reconstructed.parent_heading_level == 0
        assert reconstructed.page_nums == [1]


class TestMetadataUtilities:
    """Test metadata utility functions."""

    def test_estimate_metadata_size(self):
        """Test metadata size estimation."""
        metadata = {"key1": "value1", "key2": 123, "key3": [1, 2, 3]}

        size = estimate_metadata_size(metadata)
        assert isinstance(size, int)
        assert size > 0

    def test_estimate_metadata_size_empty(self):
        """Test size estimation of empty metadata."""
        size = estimate_metadata_size({})
        assert isinstance(size, int)
        assert size > 0  # Even "{}" has size

    def test_estimate_metadata_size_large(self):
        """Test size estimation of large metadata."""
        metadata = {"large_list": list(range(1000)), "large_string": "x" * 10000}

        size = estimate_metadata_size(metadata)
        assert size > 10000  # Should be reasonably large

    def test_validate_metadata_size_within_limit(self):
        """Test validation passes for small metadata."""
        metadata = {"key": "value"}

        # Should not raise
        validate_metadata_size(metadata, max_size_kb=50)

    def test_validate_metadata_size_exceeds_limit(self):
        """Test validation fails for oversized metadata."""
        # Create large metadata
        metadata = {"data": "x" * 100000}

        with pytest.raises(ValueError) as exc_info:
            validate_metadata_size(metadata, max_size_kb=50)

        assert "exceeds limit" in str(exc_info.value)

    def test_validate_metadata_size_custom_limit(self):
        """Test validation with custom limit."""
        metadata = {"data": "x" * 10000}

        # Should fail with low limit
        with pytest.raises(ValueError):
            validate_metadata_size(metadata, max_size_kb=5)

        # Should pass with high limit
        validate_metadata_size(metadata, max_size_kb=100)


class TestDocumentStructureValidation:
    """Test document structure validation."""

    def test_validate_valid_structure(self):
        """Test validation passes for valid structure."""
        structure = DocumentStructure(
            headings=[HeadingInfo(text="Title", level=HeadingLevel.TITLE, page_num=1)],
            tables=[TableInfo(page_num=2, num_rows=5, num_cols=3)],
            pictures=[PictureInfo(page_num=3, picture_type=PictureType.CHART, confidence=0.9)],
        )

        # Should not raise
        validate_document_structure(structure)

    def test_validate_invalid_heading_page_num(self):
        """Test validation fails for invalid page numbers."""
        structure = DocumentStructure(
            headings=[HeadingInfo(text="Title", level=HeadingLevel.TITLE, page_num=0)]
        )

        with pytest.raises(AssertionError) as exc_info:
            validate_document_structure(structure)

        assert "page" in str(exc_info.value).lower()

    def test_validate_empty_heading_text(self):
        """Test validation fails for empty heading text."""
        structure = DocumentStructure(
            headings=[HeadingInfo(text="  ", level=HeadingLevel.TITLE, page_num=1)]
        )

        with pytest.raises(AssertionError) as exc_info:
            validate_document_structure(structure)

        assert "heading" in str(exc_info.value).lower()

    def test_validate_invalid_table_rows(self):
        """Test validation fails for negative row count."""
        structure = DocumentStructure(tables=[TableInfo(page_num=1, num_rows=-1)])

        with pytest.raises(AssertionError) as exc_info:
            validate_document_structure(structure)

        assert "row" in str(exc_info.value).lower()

    def test_validate_invalid_table_cols(self):
        """Test validation fails for negative column count."""
        structure = DocumentStructure(tables=[TableInfo(page_num=1, num_cols=-5)])

        with pytest.raises(AssertionError) as exc_info:
            validate_document_structure(structure)

        assert "column" in str(exc_info.value).lower()

    def test_validate_invalid_picture_confidence(self):
        """Test validation fails for invalid confidence values."""
        # Confidence > 1
        structure = DocumentStructure(
            pictures=[PictureInfo(page_num=1, picture_type=PictureType.CHART, confidence=1.5)]
        )

        with pytest.raises(AssertionError) as exc_info:
            validate_document_structure(structure)

        assert "confidence" in str(exc_info.value).lower()

        # Confidence < 0
        structure = DocumentStructure(
            pictures=[PictureInfo(page_num=1, picture_type=PictureType.CHART, confidence=-0.5)]
        )

        with pytest.raises(AssertionError):
            validate_document_structure(structure)

    def test_validate_structure_too_large(self):
        """Test validation fails for oversized structure."""
        # Create very large structure
        structure = DocumentStructure(
            headings=[
                HeadingInfo(
                    text="x" * 10000, level=HeadingLevel.TITLE, page_num=i  # Very long text
                )
                for i in range(1, 100)
            ]
        )

        with pytest.raises(AssertionError) as exc_info:
            validate_document_structure(structure)

        assert "size" in str(exc_info.value).lower() or "large" in str(exc_info.value).lower()


class TestChunkContextValidation:
    """Test chunk context validation."""

    def test_validate_valid_context(self):
        """Test validation passes for valid context."""
        context = ChunkContext(
            parent_heading="Introduction",
            parent_heading_level=1,
            section_path="1 > 1.1",
            element_type="text",
            page_nums=[1, 2],
        )

        # Should not raise
        validate_chunk_context(context)

    def test_validate_invalid_heading_level(self):
        """Test validation fails for invalid heading level."""
        context = ChunkContext(parent_heading_level=99)

        with pytest.raises(AssertionError) as exc_info:
            validate_chunk_context(context)

        assert "heading level" in str(exc_info.value).lower()

    def test_validate_negative_heading_level(self):
        """Test validation fails for negative heading level."""
        context = ChunkContext(parent_heading_level=-1)

        with pytest.raises(AssertionError):
            validate_chunk_context(context)

    def test_validate_section_path_too_long(self):
        """Test validation fails for oversized section path."""
        context = ChunkContext(section_path="x" * 600)

        with pytest.raises(AssertionError) as exc_info:
            validate_chunk_context(context)

        assert (
            "section path" in str(exc_info.value).lower() or "long" in str(exc_info.value).lower()
        )

    def test_validate_invalid_element_type(self):
        """Test validation fails for invalid element type."""
        context = ChunkContext(element_type="invalid_type")

        with pytest.raises(AssertionError) as exc_info:
            validate_chunk_context(context)

        assert "element type" in str(exc_info.value).lower()

    def test_validate_valid_element_types(self):
        """Test validation passes for all valid element types."""
        valid_types = ["text", "list_item", "table_cell", "caption", "code", "formula"]

        for element_type in valid_types:
            context = ChunkContext(element_type=element_type, page_nums=[1])
            # Should not raise
            validate_chunk_context(context)

    def test_validate_invalid_page_numbers(self):
        """Test validation fails for invalid page numbers."""
        context = ChunkContext(page_nums=[0, -1, 5])

        with pytest.raises(AssertionError) as exc_info:
            validate_chunk_context(context)

        assert "page" in str(exc_info.value).lower()

    def test_validate_empty_context(self):
        """Test validation passes for minimal context."""
        context = ChunkContext()

        # Should not raise (defaults are valid)
        validate_chunk_context(context)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_document_structure_with_bbox_none(self):
        """Test structure with bbox=None."""
        structure = DocumentStructure(
            headings=[HeadingInfo(text="Test", level=HeadingLevel.TITLE, page_num=1, bbox=None)]
        )

        data = structure.to_dict()
        reconstructed = DocumentStructure.from_dict(data)

        assert reconstructed.headings[0].bbox is None

    def test_document_structure_empty_lists(self):
        """Test structure with empty lists."""
        structure = DocumentStructure()
        data = structure.to_dict()

        assert data["headings"] == []
        assert data["tables"] == []
        assert data["pictures"] == []

    def test_chunk_context_all_none(self):
        """Test chunk context with all optional fields as None."""
        context = ChunkContext(
            parent_heading=None, parent_heading_level=None, section_path="", element_type="text"
        )

        data = context.to_dict()
        reconstructed = ChunkContext.from_dict(data)

        assert reconstructed.parent_heading is None
        assert reconstructed.parent_heading_level is None

    def test_metadata_size_with_custom_objects(self):
        """Test size estimation handles custom objects."""

        class CustomObj:
            def __str__(self):
                return "custom"

        metadata = {"obj": CustomObj()}
        size = estimate_metadata_size(metadata)

        assert isinstance(size, int)
        assert size > 0
