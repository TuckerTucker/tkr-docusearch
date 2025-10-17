 Implementation Plan: Real Docling Integration
  (Wholesale Replacement)

  Goal: Replace current format-specific parsers with
  unified Docling implementation, improving DOCX/PPTX
  visual quality while maintaining system functionality.

  Constraints:
  - Clean slate approach (no backward compatibility
  needed)
  - Must maintain existing API interface for
  DocumentProcessor
  - M1 Mac with MPS acceleration available
  - No existing data to preserve

  Priority: Quality (better visual embeddings) with
  reasonable performance

  ---
  Ordered Task List

  1. Install and verify Docling locally

  - Install in virtual environment: pip install docling
  - Run simple test conversion on sample PDF/DOCX/PPTX
  - Verify model downloads work (DocLayNet, TableFormer)
  - Check MPS/GPU detection and acceleration
  - Understand DoclingDocument structure output

  Why first: De-risk the unknown - ensure Docling works
  on our hardware before code changes

  ---
  2. Create test document suite

  - Collect 3-5 representative documents:
    - Multi-page PDF with images/tables
    - DOCX with formatting, images, tables
    - PPTX with slides, charts, text
  - Document current parsing behavior (screenshots,
  output)
  - Establish baseline for quality comparison

  Why now: Need reference points to validate improvement

  ---
  3. Study Docling API and output structure

  - Read Docling documentation for DocumentConverter
  - Understand DoclingDocument fields and structure
  - Map Docling's page/layout elements to our Page
  dataclass
  - Identify how to extract images from Docling output
  - Note any format-specific quirks or limitations

  Why now: Design the adapter layer before writing code

  ---
  4. Create Docling-to-Page adapter function

  - Write _docling_to_pages(docling_doc) → List[Page]
  - Extract page images from Docling output
  - Extract text content with layout awareness
  - Handle multi-page documents
  - Test with sample documents from step 2

  Why now: Core conversion logic that all formats will
  use

  ---
  5. Rewrite parse_document() with Docling

  - Replace all format-specific _parse_* methods
  - Initialize DocumentConverter with MPS device
  - Call converter.convert(file_path)
  - Use adapter from step 4 to convert output
  - Keep ParsedDocument return structure identical

  Why now: Main implementation - all previous work feeds
   into this

  ---
  6. Remove old parsing code

  - Delete _parse_pdf(), _parse_docx(), _parse_pptx()
  - Delete _create_text_image() helper
  - Delete _mock_parse() fallback
  - Clean up unused imports (fitz, python-docx,
  python-pptx)
  - Simplify class structure

  Why now: Clean code immediately after replacement,
  avoid confusion

  ---
  7. Test with local worker

  - Process test documents through full pipeline
  - Verify ChromaDB embeddings are created
  - Compare output quality to baseline (step 2)
  - Check memory usage during processing
  - Validate visual elements properly captured

  Why now: Catch issues in dev environment before Docker
   changes

  ---
  8. Update requirements and dependencies

  - Remove from requirements.txt: PyMuPDF, python-docx,
  python-pptx
  - Add to requirements.txt: docling with version pin
  - Update native worker setup script if needed
  - Document any system dependencies Docling needs

  Why now: Docker build depends on correct requirements

  ---
  9. Update Dockerfile for processing worker

  - Modify pip install commands
  - Add Docling model cache directory
  - Pre-download models during build (optional but
  recommended)
  - Adjust memory limits if needed
  - Add comments explaining Docling setup

  Why now: Container needs correct dependencies and
  resources

  ---
  10. Update docker-compose.yml

  - Add Docling model cache volume mount
  - Add environment variables: DOCLING_DEVICE,
  DOCLING_MODEL_CACHE
  - Increase memory limits if needed (test shows
  requirement)
  - Document new volume in comments

  Why now: Full Docker setup needed before deployment
  testing

  ---
  11. Clear and rebuild Docker environment

  - Stop all services: ./scripts/stop-all.sh
  - Remove old containers and images
  - Delete ChromaDB data: rm -rf data/chroma_db/*
  - Rebuild worker: docker-compose build --no-cache
  processing-worker
  - Start services: ./scripts/start-all.sh

  Why now: Clean environment ensures no contamination
  from old code

  ---
  12. End-to-end validation with Docker

  - Upload test documents via Copyparty UI
  - Verify webhook triggers processing
  - Check worker logs for Docling activity
  - Confirm embeddings stored in ChromaDB
  - Run semantic search queries

  Why now: Full system integration test

  ---
  13. Quality comparison testing

  - Search for visual elements in DOCX/PPTX (e.g.,
  "chart", "diagram")
  - Compare to baseline expectations
  - Verify visual embeddings improved over text-only
  - Test edge cases: large documents, complex layouts
  - Document quality improvements

  Why now: Validate the core goal was achieved

  ---
  14. Performance benchmarking

  - Measure processing time per document type
  - Monitor memory usage during processing
  - Test with 10-page, 50-page, 100-page documents
  - Verify GPU/MPS acceleration is working
  - Document if performance acceptable or needs tuning

  Why now: Ensure system is production-ready

  ---
  15. Update configuration documentation

  - Update docker/.env.template with Docling variables
  - Add comments explaining model cache location
  - Document GPU vs CPU trade-offs
  - Note memory requirements increased

  Why now: Future deployments need this info

  ---
  16. Update README.md and user documentation

  - Update "Supported Formats" section
  - Note improved DOCX/PPTX visual processing
  - Update processing time estimates (slower but better)
  - Add troubleshooting for model downloads
  - Update memory requirements

  Why now: Users need to understand what changed

  ---
  17. Update technical documentation

  - Update src/processing/README.md with Docling
  architecture
  - Document DoclingDocument → ParsedDocument flow
  - Explain model caching and GPU usage
  - Add troubleshooting guide for Docling issues

  Why now: Developers need implementation details

  ---
  18. Create migration guide (for users)

  - Document that all documents need reprocessing
  - Explain visual quality improvements
  - Provide reprocessing workflow
  - Note any behavioral changes in search

  Why now: Help users understand the transition

  ---
  19. Git commit and documentation

  - Commit with descriptive message
  - Document breaking changes in commit body
  - Tag as major version if using semver
  - Update CHANGELOG if exists

  Why now: Preserve history and communicate changes

  ---
  20. Monitor first production use

  - Watch logs for Docling errors
  - Monitor memory usage trends
  - Track processing times vs expectations
  - Collect user feedback on search quality
  - Be ready to tune or rollback if needed

  Why now: Real-world validation and readiness to
  respond

  ---
  Implementation Status: ✅ COMPLETE (Steps 1-12)

  Date Completed: 2025-10-07

  Completed Steps:
  ✅ 1-6: Core implementation (Docling 2.55.1 integrated)
  ✅ 7: Native worker validation (30 visual + 17 text chunks)
  ✅ 8-9: Dependencies updated (removed 5 obsolete libs)
  ✅ 10-11: Docker image built (2.7GB with Docling)
  ✅ 12: End-to-end validation complete

  Git Commits:
  - f9b3942: feat: integrate Docling document parser
  - 85e8195: chore: update dependencies for Docling

  Performance Results:
  - Model loading: 8s native (MPS) vs 14s Docker (CPU)
  - PDF rendering: 900x1125px (vs old 1024x1024)
  - Code reduction: 240 lines removed (663→423)

  Remaining Tasks (13-20): Documentation and validation

  ---
  🚀 DEPLOYMENT RECOMMENDATION: Native Worker on M1/M2/M3

  For production deployment on Apple Silicon Macs:

  ✅ USE NATIVE WORKER (Recommended):
    - 40% faster model loading (8s vs 14s)
    - MPS GPU acceleration for ColPali
    - Docling leverages Metal for processing
    - Direct file system access
    - Lower memory overhead

    Setup:
    - Create .venv-native: python3 -m venv .venv-native
    - Install deps: pip install -r requirements.txt
    - Run worker: CHROMA_HOST=localhost CHROMA_PORT=8001 \
                  python -m src.processing.worker_webhook

  ⚠️ DOCKER (Alternative):
    Use Docker only for:
    - CI/CD testing environments
    - CPU-only cloud deployments
    - Cross-platform compatibility testing

    Limitation: No MPS support in Docker
    - Falls back to CPU-only mode
    - ~40% slower model loading
    - No Metal acceleration benefits

  See: docs/deployment/native-worker-setup.md for details

  ---
  Success Criteria

  ✅ All three formats (PDF, DOCX, PPTX) process without errors
  ✅ DOCX/PPTX produce actual visual embeddings
