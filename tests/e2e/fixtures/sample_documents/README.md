# Sample Test Documents

This directory contains sample documents for E2E integration testing.

## Overview

Sample documents are **optional**. Tests will automatically skip if documents are not available.

## Creating Sample Documents

You can create sample documents using the helper functions or add real documents.

### Option 1: Generate with Helper Functions

```python
from pathlib import Path
from tests.e2e.fixtures.helpers import (
    create_test_pdf,
    create_test_pdf_with_structure
)

# Simple text PDF
create_test_pdf(
    Path("tests/e2e/fixtures/sample_documents/simple_text.pdf"),
    content="This is a simple test PDF with plain text content."
)

# Complex PDF with structure
create_test_pdf_with_structure(
    Path("tests/e2e/fixtures/sample_documents/complex_pdf.pdf"),
    num_pages=5,
    num_headings=10,
    num_tables=3
)
```

**Note**: Requires `reportlab` package:
```bash
pip install reportlab
```

### Option 2: Add Real Documents

For more comprehensive testing, add real PDF documents with known structure:

- **complex_pdf.pdf** - Multi-column layout, tables, figures, hierarchical headings
- **simple_text.pdf** - Plain text without complex structure
- **presentation.pptx** - PowerPoint with slide structure (optional)
- **document.docx** - Word document with headings (optional)

## Document Requirements

### complex_pdf.pdf

Ideal characteristics:
- Multiple pages (3-5)
- Hierarchical headings (Title, Section, Subsection)
- At least 2 tables with captions
- At least 1 figure/chart with caption
- Multi-column layout (if possible)
- Mixed content (text, lists, tables, images)

### simple_text.pdf

Ideal characteristics:
- 1-2 pages
- Plain text paragraphs
- No tables or figures
- Minimal or no headings
- Used to test graceful degradation when structure extraction fails

## Test Usage

Tests check for document availability:

```python
def test_with_sample_document(sample_pdf_with_structure: Optional[Path]):
    """Test using sample document."""
    if sample_pdf_with_structure is None:
        pytest.skip("Sample PDF with structure not available")

    # Test code using sample_pdf_with_structure
    ...
```

## Security Note

**Do not commit sensitive or proprietary documents to the repository.**

Sample documents should be:
- Generic test content only
- No personal information
- No confidential data
- No copyrighted material

For CI/CD, documents can be generated on-the-fly using helper functions.

## File Size Guidelines

Keep sample documents small for repository efficiency:
- Simple PDF: < 100 KB
- Complex PDF: < 500 KB
- Total directory: < 1 MB

## Gitignore

Sample documents are gitignored by default. To track specific test documents:

```bash
# In .gitignore
tests/e2e/fixtures/sample_documents/*.pdf
tests/e2e/fixtures/sample_documents/*.docx
tests/e2e/fixtures/sample_documents/*.pptx

# To track a specific file, use:
git add -f tests/e2e/fixtures/sample_documents/specific_test.pdf
```

## Current Status

This directory is currently empty. Tests will skip if sample documents are not available.

To run full E2E tests with document processing:
1. Generate sample documents using helper functions
2. Or add real documents following guidelines above
3. Run tests with `pytest tests/e2e/ -v`
