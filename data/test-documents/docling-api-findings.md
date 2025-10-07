# Docling API Investigation Results

**Date**: 2025-10-07
**Docling Version**: 2.55.1

---

## Key Findings

### ✅ PDF Processing

**Rendering with images**:
```python
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

pipeline_options = PdfPipelineOptions()
pipeline_options.generate_page_images = True
pipeline_options.generate_picture_images = True

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

result = converter.convert("document.pdf")
```

**Getting PIL images**:
```python
# Method 1: From result.pages (PREFERRED)
for page in result.pages:
    pil_image = page.get_image()  # Returns PIL.Image.Image (900x1125 RGB)

# Method 2: From doc.pages (has ImageRef)
for page_num, page in result.document.pages.items():
    if page.image:  # ImageRef with base64 data URI
        # page.image.uri contains data:image/png;base64,...
        pass
```

**Key attributes**:
- `result.pages` - List of Page objects (0-indexed)
- `result.pages[i].get_image()` - Returns PIL Image
- `result.document.pages` - Dict with integer keys {1, 2, 3...}
- `result.document.pages[n].image` - ImageRef with base64 data

### ⚠️ DOCX Processing

**Issues**:
- `result.document.pages` is empty dict `{}`
- No page concept for DOCX
- Docling treats DOCX as single document flow

**Text extraction works**:
```python
text = result.document.export_to_text()  # ✅ Works perfectly
markdown = result.document.export_to_markdown()  # ✅ Works perfectly
```

**Workaround needed**:
- For visual embeddings, need to render markdown → HTML → screenshot
- Or use python-docx to render to images (current approach)
- Or accept DOCX as text-only format

### ⚠️ PPTX Processing

**Behavior**:
- `result.document.pages` has 3 entries {1, 2, 3}
- But `page.image` is `None` even with `generate_page_images=True`
- Text extraction works perfectly

**Workaround needed**:
- Docling doesn't generate slide images automatically
- Need external rendering: python-pptx → images
- Or markdown → HTML → screenshots per slide

---

## Docling Output Structure

### ConversionResult

```python
result = converter.convert("doc.pdf")

# Top-level attributes
result.document       # DoclingDocument
result.pages          # List[Page] - physical pages with images
result.input          # InputDocument
result.status         # ConversionStatus
result.timings        # Dict[str, float]
```

### DoclingDocument

```python
doc = result.document

# Content structure
doc.pages             # Dict[int, PageItem] - {1: PageItem, 2: PageItem, ...}
doc.texts             # List[TextItem] - all text elements
doc.tables            # List[TableItem] - structured tables
doc.pictures          # List[PictureItem] - extracted images
doc.groups            # List[GroupItem] - document sections

# Export methods
doc.export_to_text()       # Plain text
doc.export_to_markdown()   # Markdown format
doc.export_to_html()       # HTML format
doc.export_to_dict()       # Dict format

# Metadata
doc.name              # Document name
doc.num_pages         # Number of pages (callable method!)
doc.origin            # DocumentOrigin with filename, mimetype
```

### Page (from result.pages)

```python
page = result.pages[0]  # 0-indexed list

# Image access (PRIMARY METHOD)
pil_image = page.get_image()  # Returns PIL.Image.Image or None

# Attributes
page.page_no          # Page number (1-indexed)
page.size             # Size(width, height) in units
page.image            # Optional image reference
page.cells            # Layout cells
page.predictions      # ML predictions
```

### PageItem (from doc.pages)

```python
page = doc.pages[1]  # 1-indexed dict

# Attributes
page.size             # Size(width, height)
page.image            # ImageRef or None
page.page_no          # Page number

# ImageRef (when present)
page.image.uri        # data:image/png;base64,iVBORw...
```

---

## Format-Specific Behavior

| Format | `doc.pages` | `result.pages` | Images | Text |
|--------|-------------|----------------|--------|------|
| PDF | ✅ Dict | ✅ List | ✅ Yes | ✅ Yes |
| DOCX | ❌ Empty | ❌ Empty | ❌ No | ✅ Yes |
| PPTX | ✅ Dict | ❌ Empty | ❌ No | ✅ Yes |

---

## Adapter Function Strategy

Based on these findings, the adapter function should:

### For PDF:
```python
def docling_to_pages(result: ConversionResult) -> List[Page]:
    pages = []
    for page in result.pages:
        img = page.get_image()  # PIL Image

        # Extract text for this page
        # (iterate doc.texts where prov[0].page_no == page.page_no)
        text = extract_page_text(result.document, page.page_no)

        pages.append(Page(
            page_num=page.page_no,
            image=img,
            text=text
        ))
    return pages
```

### For DOCX/PPTX:
**Option A**: Keep existing rendering (white background images)
**Option B**: Generate HTML from markdown → screenshot
**Option C**: Text-only mode (skip visual embeddings)

**Recommendation**: Start with Option A (existing code), add Option B as enhancement later

---

## Next Steps

✅ **Step 3 Complete**: Docling API and output structure fully understood

🔄 **Step 4**: Create adapter function:
- `docling_to_pages(result: ConversionResult) -> List[Page]`
- Handle PDF format first (has images)
- Use existing DOCX/PPTX rendering for now
- Add proper text extraction per page

⏳ **Step 5**: Rewrite `parse_document()` to use Docling
