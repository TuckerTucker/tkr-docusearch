# DoclingParser Refactoring Contract

## Provider Agent
**complexity-refactor-agent** (Wave 2)

## Consumer Agents
- **test-infrastructure-agent** (validates with tests)
- **All processing module consumers** (maintains backward compatibility)

---

## Public Interface (Must Remain Unchanged)

### DoclingParser Class

```python
class DoclingParser:
    """
    Document parser using Docling library.

    This is the main entry point for document parsing. The internal
    implementation uses Strategy pattern but the public API remains stable.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        enable_ocr: bool = True,
        enable_table_extraction: bool = True,
        enable_asr: bool = False
    ):
        """
        Initialize parser with configuration.

        Args:
            chunk_size: Target size for text chunks
            chunk_overlap: Overlap between chunks
            enable_ocr: Enable OCR for images
            enable_table_extraction: Extract tables
            enable_asr: Enable audio transcription (requires MLX Whisper)

        Note: Implementation now uses strategy pattern internally.
        """
        pass

    def parse_document(self, file_path: str) -> DocumentParseResult:
        """
        Parse document and return structured result.

        THIS METHOD SIGNATURE MUST NOT CHANGE.

        Args:
            file_path: Absolute path to document file

        Returns:
            DocumentParseResult with pages and chunks

        Raises:
            FileNotFoundError: If file doesn't exist
            ParsingError: If parsing fails
            UnsupportedFormatError: If file type not supported
        """
        pass
```

### DocumentParseResult (No Changes)

```python
@dataclass
class DocumentParseResult:
    """Result of document parsing (unchanged)."""
    file_path: str
    num_pages: int
    pages: List[PageData]
    text_chunks: List[TextChunk]
    metadata: Dict[str, Any]
    parse_duration: float
```

---

## Internal Refactoring (New Strategy Pattern)

### New Files Created

#### 1. src/processing/parsers/__init__.py
```python
"""
Document parsing strategies.

This module contains strategy pattern implementations for different
document types. The public DoclingParser interface remains unchanged.
"""

from .pdf_parse_strategy import PdfParseStrategy
from .docx_parse_strategy import DocxParseStrategy
from .pptx_parse_strategy import PptxParseStrategy
from .asr_options_builder import AsrOptionsBuilder

__all__ = [
    "PdfParseStrategy",
    "DocxParseStrategy",
    "PptxParseStrategy",
    "AsrOptionsBuilder",
]
```

#### 2. src/processing/parsers/pdf_parse_strategy.py
```python
"""PDF parsing strategy."""

from typing import Optional
from docling.document_converter import DocumentConverter
from ..types import DocumentParseResult


class PdfParseStrategy:
    """Strategy for parsing PDF files."""

    def __init__(
        self,
        enable_ocr: bool = True,
        enable_table_extraction: bool = True,
        enable_asr: bool = False
    ):
        """
        Initialize PDF parsing strategy.

        Args:
            enable_ocr: Enable OCR for scanned PDFs
            enable_table_extraction: Extract tables
            enable_asr: Enable audio transcription
        """
        self.enable_ocr = enable_ocr
        self.enable_table_extraction = enable_table_extraction
        self.enable_asr = enable_asr

    def parse(self, file_path: str) -> DocumentParseResult:
        """
        Parse PDF document.

        Args:
            file_path: Path to PDF file

        Returns:
            DocumentParseResult with parsed content

        Raises:
            ParsingError: If PDF parsing fails
        """
        # Implementation details...
        pass
```

#### 3. src/processing/parsers/docx_parse_strategy.py
```python
"""DOCX parsing strategy."""

from typing import Optional
from ..types import DocumentParseResult


class DocxParseStrategy:
    """Strategy for parsing DOCX files."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize DOCX parsing strategy.

        Args:
            chunk_size: Target size for text chunks
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def parse(self, file_path: str) -> DocumentParseResult:
        """
        Parse DOCX document.

        Args:
            file_path: Path to DOCX file

        Returns:
            DocumentParseResult with parsed content

        Raises:
            ParsingError: If DOCX parsing fails
        """
        # Implementation details...
        pass
```

#### 4. src/processing/parsers/pptx_parse_strategy.py
```python
"""PPTX parsing strategy."""

from typing import Optional
from ..types import DocumentParseResult


class PptxParseStrategy:
    """Strategy for parsing PPTX files."""

    def __init__(
        self,
        enable_ocr: bool = True,
        slide_render_enabled: bool = True
    ):
        """
        Initialize PPTX parsing strategy.

        Args:
            enable_ocr: Enable OCR for slide images
            slide_render_enabled: Render slides as images
        """
        self.enable_ocr = enable_ocr
        self.slide_render_enabled = slide_render_enabled

    def parse(self, file_path: str) -> DocumentParseResult:
        """
        Parse PPTX document.

        Args:
            file_path: Path to PPTX file

        Returns:
            DocumentParseResult with parsed content

        Raises:
            ParsingError: If PPTX parsing fails
        """
        # Implementation details...
        pass
```

#### 5. src/processing/parsers/asr_options_builder.py
```python
"""ASR options builder for audio transcription."""

from typing import Optional
from docling.datamodel.pipeline_options import AsrOptions


class AsrOptionsBuilder:
    """Builder for ASR (audio transcription) options."""

    @staticmethod
    def build_asr_options(
        enabled: bool = False,
        model_name: Optional[str] = None
    ) -> Optional[AsrOptions]:
        """
        Build ASR options for Docling.

        Args:
            enabled: Whether ASR is enabled
            model_name: MLX Whisper model name

        Returns:
            AsrOptions if enabled, None otherwise
        """
        if not enabled:
            return None

        # Implementation details...
        pass
```

---

## Refactored DoclingParser Implementation

```python
class DoclingParser:
    """Document parser using Docling with Strategy pattern."""

    def __init__(self, **config):
        """Initialize with configuration."""
        self.config = config
        self._strategies = self._initialize_strategies()

    def _initialize_strategies(self) -> Dict[str, Any]:
        """Create strategy instances based on configuration."""
        return {
            '.pdf': PdfParseStrategy(
                enable_ocr=self.config.get('enable_ocr', True),
                enable_table_extraction=self.config.get('enable_table_extraction', True),
                enable_asr=self.config.get('enable_asr', False)
            ),
            '.docx': DocxParseStrategy(
                chunk_size=self.config.get('chunk_size', 1000),
                chunk_overlap=self.config.get('chunk_overlap', 200)
            ),
            '.pptx': PptxParseStrategy(
                enable_ocr=self.config.get('enable_ocr', True)
            )
        }

    def parse_document(self, file_path: str) -> DocumentParseResult:
        """Parse document using appropriate strategy."""
        ext = os.path.splitext(file_path)[1].lower()
        strategy = self._strategies.get(ext)

        if not strategy:
            raise UnsupportedFormatError(f"Unsupported file type: {ext}")

        return strategy.parse(file_path)
```

---

## Quality Requirements

### Complexity Targets
- **DoclingParser._parse_with_docling:** Eliminate (replaced by strategies)
- **DoclingParser.parse_document:** CC ≤5 (simple delegation)
- **Each strategy.parse():** CC ≤10

### Test Coverage
- **Overall processing module:** Maintain ≥80% coverage
- **New strategy classes:** Achieve ≥80% coverage each
- **Integration tests:** All existing tests must pass

### Performance
- **No regression:** Parsing speed must remain same or improve
- **Memory usage:** No increase in peak memory
- **Latency:** Document processing time ≤ current baseline

### Backward Compatibility
- **Public API:** Zero breaking changes to DoclingParser interface
- **Existing callers:** All code using DoclingParser continues to work without modification
- **Configuration:** All existing config options supported

---

## Validation Tests

### Contract Compliance Tests

```python
# tests/processing/test_parser_contract.py

def test_docling_parser_interface_unchanged():
    """Verify public interface unchanged."""
    parser = DoclingParser(chunk_size=1000)

    # Method exists with correct signature
    assert hasattr(parser, 'parse_document')
    assert callable(parser.parse_document)

    # Can be called with file path
    result = parser.parse_document("tests/fixtures/sample.pdf")

    # Returns expected type
    assert isinstance(result, DocumentParseResult)
    assert hasattr(result, 'file_path')
    assert hasattr(result, 'pages')
    assert hasattr(result, 'text_chunks')


def test_docling_parser_initialization_compatible():
    """Verify initialization accepts all legacy parameters."""
    # All these should work without errors
    parser1 = DoclingParser()
    parser2 = DoclingParser(chunk_size=500)
    parser3 = DoclingParser(chunk_size=1000, enable_ocr=False)
    parser4 = DoclingParser(
        chunk_size=1000,
        chunk_overlap=200,
        enable_ocr=True,
        enable_table_extraction=True,
        enable_asr=False
    )


def test_strategy_pattern_reduces_complexity():
    """Verify refactoring reduced complexity."""
    from radon.complexity import cc_visit

    # Parse docling_parser.py
    with open("src/processing/docling_parser.py") as f:
        code = f.read()

    results = cc_visit(code)

    # Verify no function exceeds CC 10
    for result in results:
        assert result.complexity <= 10, f"{result.name} has CC {result.complexity}"
```

### Integration Tests

```python
# tests/processing/test_parser_integration.py

def test_pdf_parsing_still_works():
    """Verify PDF parsing works after refactoring."""
    parser = DoclingParser(enable_ocr=True)
    result = parser.parse_document("tests/fixtures/sample.pdf")

    assert result.num_pages > 0
    assert len(result.pages) == result.num_pages
    assert len(result.text_chunks) > 0


def test_docx_parsing_still_works():
    """Verify DOCX parsing works after refactoring."""
    parser = DoclingParser()
    result = parser.parse_document("tests/fixtures/sample.docx")

    assert result.num_pages > 0
    assert len(result.text_chunks) > 0


def test_pptx_parsing_still_works():
    """Verify PPTX parsing works after refactoring."""
    parser = DoclingParser()
    result = parser.parse_document("tests/fixtures/sample.pptx")

    assert result.num_pages > 0
    assert len(result.pages) > 0


def test_all_existing_tests_pass():
    """Verify all existing parser tests pass."""
    import subprocess
    result = subprocess.run(
        ["pytest", "tests/processing/test_docling_parser.py", "-v"],
        capture_output=True
    )
    assert result.returncode == 0, "Existing tests failed after refactoring"
```

---

## Integration Points

### With test-infrastructure-agent
- **Dependency:** Requires working test suite from Wave 1
- **Handoff:** After refactoring, test-infrastructure-agent validates all tests pass
- **Coordination:** Test-infrastructure-agent adds coverage tests for new strategies

### With automation-agent
- **Timing:** Automated formatting runs after refactoring complete
- **Coordination:** Black/isort may reformat new strategy files

---

## Rollback Procedure

If refactoring causes issues:

1. **Identify failure:** Specific test failures or regressions
2. **Assess scope:** If >5 tests fail or performance degrades >10%, rollback
3. **Revert:** `git revert <commit-hash>` to restore pre-refactor state
4. **Analyze:** Determine root cause offline
5. **Re-implement:** Fix issues in isolation
6. **Re-validate:** Run full test suite before re-merging

---

## Notes

### Implementation Guidance

- Extract strategies one at a time (PDF → DOCX → PPTX)
- Run tests after each extraction
- Keep `_parse_with_docling` as fallback initially
- Remove `_parse_with_docling` only after all strategies validated

### Common Pitfalls

- **Don't change error handling:** Maintain same exceptions
- **Don't change logging:** Keep same log messages and levels
- **Don't change metadata:** DocumentParseResult fields must match exactly
- **Don't optimize yet:** Focus on refactoring, optimize in Wave 4

---

## Success Criteria

- ✅ All existing tests pass (100%)
- ✅ DoclingParser.parse_document complexity CC ≤5
- ✅ All strategy classes CC ≤10
- ✅ Original `_parse_with_docling` method removed
- ✅ No breaking changes to public API
- ✅ Test coverage maintained or improved
- ✅ Performance within 5% of baseline

---

## Version History

| Date | Change | Author |
|------|--------|--------|
| 2025-10-16 | Initial contract | orchestrator |

---

This contract ensures safe refactoring with clear validation criteria and backward compatibility guarantees.
