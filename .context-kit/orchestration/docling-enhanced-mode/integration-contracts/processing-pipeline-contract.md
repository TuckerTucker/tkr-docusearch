# Processing Pipeline Integration Contract

**Contract ID**: PIPELINE-001
**Version**: 1.0
**Status**: Specification
**Owner**: integration-agent
**Consumers**: All processing agents

## Purpose

Define the integration points for enhanced document processing pipeline, coordinating configuration, structure extraction, smart chunking, and storage operations.

## Pipeline Flow

### Enhanced Processing Flow

```python
"""
Complete enhanced processing pipeline:

1. Load Configuration
   └─> EnhancedModeConfig.from_env()

2. Parse Document (DoclingParser)
   ├─> Create PdfPipelineOptions from config
   ├─> DocumentConverter.convert()
   └─> Extract DoclingDocument

3. Structure Extraction (if enabled)
   └─> extract_document_structure(doc, config)
       ├─> Headings with hierarchy
       ├─> Tables with structure
       ├─> Pictures with classification
       ├─> Code blocks (optional)
       └─> Formulas (optional)

4. Convert to Pages
   └─> docling_to_pages(result)

5. Chunk Document
   ├─> If hybrid: SmartChunker.chunk_document(doc, doc_id, structure)
   └─> If legacy: LegacyChunker.chunk_pages(pages, doc_id)

6. Generate Visual Embeddings
   └─> ColPaliEngine.embed_images(page_images)

7. Generate Text Embeddings
   └─> ColPaliEngine.embed_texts(chunk_texts)

8. Store Enhanced Metadata
   ├─> add_visual_embedding(..., structure, page_context)
   └─> add_text_embedding(..., chunk_with_context)

9. Return ProcessingStatus
   └─> completed with doc_id, visual_ids, text_ids
"""
```

## Integration Points

### DocumentProcessor Initialization

```python
from src.config.processing_config import EnhancedModeConfig
from src.processing.structure_extractor import extract_document_structure
from src.processing.smart_chunker import create_chunker

class DocumentProcessor:
    """Enhanced document processor with structure awareness."""

    def __init__(
        self,
        embedding_engine,
        storage_client,
        config: Optional[EnhancedModeConfig] = None,
        visual_batch_size: int = 4,
        text_batch_size: int = 8
    ):
        """
        Initialize enhanced document processor.

        Args:
            embedding_engine: Embedding engine (ColPali)
            storage_client: Storage client (ChromaDB)
            config: Enhanced mode configuration (loads from env if None)
            visual_batch_size: Batch size for visual processing
            text_batch_size: Batch size for text processing
        """
        self.embedding_engine = embedding_engine
        self.storage_client = storage_client
        self.visual_batch_size = visual_batch_size
        self.text_batch_size = text_batch_size

        # Load configuration
        self.config = config or EnhancedModeConfig.from_env()

        # Initialize parser with config
        self.parser = DoclingParser(
            render_dpi=150,
            config=self.config
        )

        # Initialize chunker based on strategy
        self.chunker = create_chunker(self.config)

        # Log configuration
        logger.info(
            f"Initialized DocumentProcessor with enhanced mode: "
            f"table_structure={self.config.enable_table_structure}, "
            f"picture_classification={self.config.enable_picture_classification}, "
            f"chunking={self.config.chunking_strategy.value}"
        )
```

### Enhanced process_document Method

```python
async def process_document(
    self,
    file_path: str
) -> StorageConfirmation:
    """
    Process document with enhanced structure awareness.

    Args:
        file_path: Path to document file

    Returns:
        StorageConfirmation with IDs and metadata

    Raises:
        ProcessingError: If processing fails
    """
    doc_id = str(uuid.uuid4())
    filename = Path(file_path).name

    try:
        # Update status: parsing
        self._update_status(
            doc_id, filename, "parsing", 0.1, "Parsing document with Docling"
        )

        # Parse document with enhanced mode
        parsed_doc = self.parser.parse_document(
            file_path,
            config=self.config  # Pass config to parser
        )

        # parsed_doc now includes:
        # - pages: List[Page]
        # - text_chunks: List[TextChunk] (with context if hybrid)
        # - metadata: dict (with structure if enabled)

        # Extract structure from metadata
        structure = None
        if "structure" in parsed_doc.metadata:
            structure = DocumentStructure.from_dict(
                parsed_doc.metadata["structure"]
            )

        # Update status: embedding visual
        self._update_status(
            doc_id, filename, "embedding_visual", 0.3,
            f"Generating visual embeddings for {parsed_doc.num_pages} pages"
        )

        # Generate visual embeddings
        page_images = [page.image for page in parsed_doc.pages]
        visual_embeddings = await self._embed_visual_batch(page_images)

        # Update status: embedding text
        self._update_status(
            doc_id, filename, "embedding_text", 0.5,
            f"Generating text embeddings for {len(parsed_doc.text_chunks)} chunks"
        )

        # Generate text embeddings
        chunk_texts = [chunk.text for chunk in parsed_doc.text_chunks]
        text_embeddings = await self._embed_text_batch(chunk_texts)

        # Update status: storing
        self._update_status(
            doc_id, filename, "storing", 0.7, "Storing embeddings and metadata"
        )

        # Store visual embeddings with enhanced metadata
        visual_ids = []
        for idx, (page, embedding) in enumerate(zip(parsed_doc.pages, visual_embeddings)):
            # Build page context
            page_context = self._build_page_context(page, structure)

            # Store with enhanced metadata
            embedding_id = self.storage_client.add_visual_embedding(
                embedding=embedding,
                doc_id=doc_id,
                filename=filename,
                page_num=page.page_num,
                structure=structure,  # Full document structure
                page_context=page_context  # Page-specific context
            )
            visual_ids.append(embedding_id)

        # Store text embeddings with enhanced metadata
        text_ids = []
        for chunk, embedding in zip(parsed_doc.text_chunks, text_embeddings):
            # chunk.context already populated by smart chunker
            embedding_id = self.storage_client.add_text_embedding(
                embedding=embedding,
                chunk=chunk  # Includes context
            )
            text_ids.append(embedding_id)

        # Calculate total size
        total_size = self._calculate_storage_size(visual_embeddings, text_embeddings)

        # Update status: completed
        self._update_status(
            doc_id, filename, "completed", 1.0,
            f"Processing complete: {len(visual_ids)} pages, {len(text_ids)} chunks"
        )

        # Return confirmation
        return StorageConfirmation(
            doc_id=doc_id,
            visual_ids=visual_ids,
            text_ids=text_ids,
            total_size_bytes=total_size,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

    except Exception as e:
        # Update status: failed
        self._update_status(
            doc_id, filename, "failed", 0.0,
            f"Processing failed: {str(e)}",
            error_message=str(e)
        )
        raise ProcessingError(f"Failed to process {filename}: {e}") from e
```

### Page Context Builder

```python
def _build_page_context(
    self,
    page: Page,
    structure: Optional[DocumentStructure]
) -> dict:
    """
    Build page-specific context from document structure.

    Args:
        page: Page object
        structure: Document structure (if available)

    Returns:
        Page context dictionary
    """
    page_context = {
        "headings_on_page": [],
        "table_count": 0,
        "picture_count": 0,
        "element_types": []
    }

    if not structure:
        return page_context

    # Find headings on this page
    for heading in structure.headings:
        if heading.page_num == page.page_num:
            page_context["headings_on_page"].append(heading.text)

    # Count tables on this page
    page_context["table_count"] = sum(
        1 for table in structure.tables if table.page_num == page.page_num
    )

    # Count pictures on this page
    page_context["picture_count"] = sum(
        1 for picture in structure.pictures if picture.page_num == page.page_num
    )

    # Determine element types present
    element_types = set(["text"])  # Always has text
    if page_context["table_count"] > 0:
        element_types.add("table")
    if page_context["picture_count"] > 0:
        element_types.add("picture")
    if any(cb.page_num == page.page_num for cb in structure.code_blocks):
        element_types.add("code")
    if any(f.page_num == page.page_num for f in structure.formulas):
        element_types.add("formula")

    page_context["element_types"] = sorted(list(element_types))

    return page_context
```

## Updated DoclingParser Integration

### Modified parse_document Method

```python
# In DoclingParser class

def parse_document(
    self,
    file_path: str,
    config: EnhancedModeConfig,
    chunk_size_words: int = 250,  # Used only for legacy chunking
    chunk_overlap_words: int = 50  # Used only for legacy chunking
) -> ParsedDocument:
    """
    Parse document with enhanced structure extraction.

    Args:
        file_path: Path to document file
        config: Enhanced mode configuration
        chunk_size_words: Word count for legacy chunking
        chunk_overlap_words: Overlap for legacy chunking

    Returns:
        ParsedDocument with enhanced metadata
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    filename = path.name
    doc_id = str(uuid.uuid4())

    logger.info(f"Parsing document: {filename} (id={doc_id})")

    try:
        # Parse with Docling (enhanced mode)
        pages, metadata, docling_doc = self._parse_with_docling(file_path, config)

        # Extract structure (if enabled)
        structure = None
        if config.enable_table_structure or config.enable_picture_classification:
            structure = extract_document_structure(docling_doc, config)
            metadata["structure"] = structure.to_dict()

        # Chunk document using configured strategy
        text_chunks = self._chunk_document(
            doc=docling_doc,
            pages=pages,
            doc_id=doc_id,
            structure=structure,
            config=config
        )

        parsed_doc = ParsedDocument(
            filename=filename,
            doc_id=doc_id,
            num_pages=len(pages),
            pages=pages,
            text_chunks=text_chunks,
            metadata=metadata
        )

        logger.info(
            f"Parsed {filename}: {len(pages)} pages, "
            f"{len(text_chunks)} chunks, "
            f"structure={'enabled' if structure else 'disabled'}"
        )

        return parsed_doc

    except Exception as e:
        logger.error(f"Failed to parse {filename}: {e}")
        raise ParsingError(f"Parsing failed: {e}") from e


def _parse_with_docling(
    self,
    file_path: str,
    config: EnhancedModeConfig
) -> tuple:
    """
    Parse document using Docling with enhanced pipeline options.

    Returns:
        Tuple of (pages, metadata, docling_document)
    """
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat

    # Create pipeline options from config
    pipeline_options = create_pipeline_options(config)

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    logger.info(f"Converting document with Docling: {file_path}")
    result = converter.convert(file_path)

    # Convert to pages
    pages = docling_to_pages(result)

    # Build basic metadata
    doc = result.document
    metadata = {
        "title": doc.name if hasattr(doc, 'name') else "",
        "format": Path(file_path).suffix.lower()[1:],
        "num_pages": len(pages)
    }

    # Return docling_document for structure extraction
    return pages, metadata, doc
```

## Performance Monitoring

### Processing Metrics

```python
@dataclass
class ProcessingMetrics:
    """Metrics for monitoring enhanced processing."""
    doc_id: str
    filename: str
    num_pages: int
    num_chunks: int

    # Timing (seconds)
    parsing_time: float
    structure_extraction_time: float
    chunking_time: float
    visual_embedding_time: float
    text_embedding_time: float
    storage_time: float
    total_time: float

    # Metadata
    structure_size_kb: float
    total_metadata_kb: float
    chunking_strategy: str

    # Features enabled
    features_enabled: List[str]

    def overhead_percentage(self, baseline_time: float) -> float:
        """Calculate processing overhead vs baseline."""
        return ((self.total_time - baseline_time) / baseline_time) * 100
```

## Error Handling

### Graceful Degradation

```python
def process_document_with_fallback(
    self,
    file_path: str
) -> StorageConfirmation:
    """
    Process document with graceful degradation on feature failures.

    Features that fail individually don't block entire pipeline.
    """
    try:
        return self.process_document(file_path)
    except StructureExtractionError as e:
        # Structure extraction failed - fall back to no structure
        logger.warning(f"Structure extraction failed: {e}. Continuing without structure.")
        # Retry with structure disabled
        original_config = self.config
        self.config = EnhancedModeConfig(
            enable_table_structure=False,
            enable_picture_classification=False,
            chunking_strategy=original_config.chunking_strategy
        )
        result = self.process_document(file_path)
        self.config = original_config  # Restore
        return result

    except ChunkingError as e:
        # Smart chunking failed - fall back to legacy
        logger.warning(f"Smart chunking failed: {e}. Falling back to legacy chunking.")
        original_config = self.config
        self.config = EnhancedModeConfig(
            enable_table_structure=original_config.enable_table_structure,
            enable_picture_classification=original_config.enable_picture_classification,
            chunking_strategy=ChunkingStrategy.LEGACY
        )
        result = self.process_document(file_path)
        self.config = original_config  # Restore
        return result
```

## Testing Contract

### Integration Tests Required
- ✅ End-to-end processing with all features enabled
- ✅ Processing with selective features enabled
- ✅ Fallback behavior on feature failures
- ✅ Performance within targets (<20% overhead)
- ✅ Metadata stored and retrievable
- ✅ Backward compatibility maintained

### Performance Tests Required
- ✅ Baseline vs enhanced timing comparison
- ✅ Memory usage monitoring
- ✅ Storage size growth measurement
- ✅ Feature overhead breakdown

## File Locations

- `src/processing/processor.py` - Main integration point
- `src/processing/docling_parser.py` - Parser integration

## Version History

- **1.0** (2025-10-07): Initial specification
