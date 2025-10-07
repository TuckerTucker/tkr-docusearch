"""
Document Processing Worker for DocuSearch MVP.

Watches the uploads directory and processes documents automatically.
Extracts text, generates embeddings, and stores in ChromaDB.
"""

import logging
import time
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import hashlib

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

# Import core components
from ..embeddings import ColPaliEngine
from ..storage import ChromaClient
from ..processing import DocumentProcessor
from ..processing.docling_parser import DoclingParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/data/logs/worker.log')
    ]
)

logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

UPLOADS_DIR = Path(os.getenv("UPLOAD_DIR", "/uploads"))
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8001"))
DEVICE = os.getenv("DEVICE", "mps")
PRECISION = os.getenv("MODEL_PRECISION", "fp16")
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx"}

# Processing status tracking
processing_status = {}


# ============================================================================
# File System Event Handler
# ============================================================================

class DocumentUploadHandler(FileSystemEventHandler):
    """Handles new document uploads."""

    def __init__(self, processor: DocumentProcessor, parser: DoclingParser):
        """
        Initialize upload handler.

        Args:
            processor: Document processor instance
            parser: Document parser instance
        """
        self.processor = processor
        self.parser = parser
        self.processing_queue = []

    def on_created(self, event: FileCreatedEvent):
        """Handle file creation events."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Check if supported file type
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            logger.debug(f"Ignoring unsupported file type: {file_path}")
            return

        # Skip temp files
        if file_path.name.startswith('.') or file_path.name.startswith('~'):
            return

        logger.info(f"New upload detected: {file_path}")

        # Wait a moment for file write to complete
        time.sleep(2)

        # Add to processing queue
        self.processing_queue.append(file_path)
        self.process_file(file_path)

    def process_file(self, file_path: Path):
        """
        Process a document file.

        Args:
            file_path: Path to document file
        """
        doc_id = None
        try:
            # Generate doc ID from file hash
            with open(file_path, 'rb') as f:
                content = f.read()
                doc_id = hashlib.md5(content).hexdigest()[:12]

            # Update status
            processing_status[doc_id] = {
                "filename": file_path.name,
                "status": "parsing",
                "progress": 0.0,
                "started_at": datetime.now().isoformat(),
                "error": None
            }

            logger.info(f"Processing document: {file_path.name} (ID: {doc_id})")

            # Process document (parsing, embedding, and storage)
            processing_status[doc_id]["status"] = "processing"
            processing_status[doc_id]["progress"] = 0.1

            # DocumentProcessor handles parsing, embedding, and storage
            result = self.processor.process_document(
                file_path=str(file_path),
                status_callback=lambda status: self._update_processing_status(doc_id, status)
            )

            if not result or result.status.lower() != "completed":
                error_msg = result.error if result else "Unknown error"
                raise ValueError(f"Document processing failed: {error_msg}")

            logger.info(f"Processed {file_path.name}: {result.pages_processed} pages, {result.text_chunks_processed} text chunks")

            # Update status to completed
            processing_status[doc_id]["status"] = "completed"
            processing_status[doc_id]["progress"] = 1.0
            processing_status[doc_id]["completed_at"] = datetime.now().isoformat()

            logger.info(f"✓ Successfully processed {file_path.name} (ID: {doc_id})")

        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}", exc_info=True)

            if doc_id:
                processing_status[doc_id]["status"] = "failed"
                processing_status[doc_id]["error"] = str(e)
                processing_status[doc_id]["completed_at"] = datetime.now().isoformat()

        finally:
            # Remove from queue
            if file_path in self.processing_queue:
                self.processing_queue.remove(file_path)

    def _update_processing_status(self, doc_id: str, status):
        """Update processing status from DocumentProcessor callback.

        Args:
            doc_id: Document ID
            status: ProcessingStatus object from DocumentProcessor
        """
        if doc_id in processing_status:
            processing_status[doc_id]["status"] = status.status
            processing_status[doc_id]["progress"] = status.progress


# ============================================================================
# Worker Main Function
# ============================================================================

def process_existing_files(handler: DocumentUploadHandler, uploads_dir: Path):
    """
    Process any existing files in uploads directory.

    Args:
        handler: Upload handler instance
        uploads_dir: Path to uploads directory
    """
    logger.info(f"Scanning {uploads_dir} for existing files...")

    existing_files = []
    for ext in SUPPORTED_EXTENSIONS:
        existing_files.extend(uploads_dir.glob(f"*{ext}"))

    if existing_files:
        logger.info(f"Found {len(existing_files)} existing files to process")
        for file_path in existing_files:
            logger.info(f"Processing existing file: {file_path.name}")
            handler.process_file(file_path)
    else:
        logger.info("No existing files to process")


def main():
    """Main worker entry point."""
    logger.info("=" * 70)
    logger.info("DocuSearch Processing Worker Starting...")
    logger.info("=" * 70)

    # Log configuration
    logger.info(f"Configuration:")
    logger.info(f"  Uploads Directory: {UPLOADS_DIR}")
    logger.info(f"  ChromaDB: {CHROMA_HOST}:{CHROMA_PORT}")
    logger.info(f"  Device: {DEVICE}")
    logger.info(f"  Precision: {PRECISION}")
    logger.info(f"  Supported Extensions: {SUPPORTED_EXTENSIONS}")

    # Create uploads directory if it doesn't exist
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize components
    logger.info("Initializing components...")

    try:
        # Initialize embedding engine
        logger.info(f"Loading ColPali model (device={DEVICE}, precision={PRECISION})...")
        embedding_engine = ColPaliEngine(
            device=DEVICE,
            precision=PRECISION
        )
        logger.info("✓ ColPali model loaded")

        # Initialize storage client
        logger.info(f"Connecting to ChromaDB ({CHROMA_HOST}:{CHROMA_PORT})...")
        storage_client = ChromaClient(
            host=CHROMA_HOST,
            port=CHROMA_PORT
        )
        logger.info("✓ ChromaDB connected")

        # Initialize document processor
        document_processor = DocumentProcessor(
            embedding_engine=embedding_engine,
            storage_client=storage_client
        )
        logger.info("✓ Document processor initialized")

        # Initialize document parser
        parser = DoclingParser()
        logger.info("✓ Document parser initialized")

    except Exception as e:
        logger.error(f"Failed to initialize components: {e}", exc_info=True)
        return 1

    # Create event handler
    event_handler = DocumentUploadHandler(
        processor=document_processor,
        parser=parser
    )

    # Process existing files
    process_existing_files(event_handler, UPLOADS_DIR)

    # Start file system observer
    observer = Observer()
    observer.schedule(event_handler, str(UPLOADS_DIR), recursive=False)
    observer.start()

    logger.info("=" * 70)
    logger.info("✓ Worker started successfully")
    logger.info(f"  Watching: {UPLOADS_DIR}")
    logger.info("  Press Ctrl+C to stop")
    logger.info("=" * 70)

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutdown signal received, stopping worker...")
        observer.stop()

    observer.join()
    logger.info("Worker stopped")
    return 0


# ============================================================================
# Status API (Optional)
# ============================================================================

def get_processing_status(doc_id: Optional[str] = None):
    """
    Get processing status.

    Args:
        doc_id: Optional document ID. If None, returns all statuses.

    Returns:
        Processing status dict
    """
    if doc_id:
        return processing_status.get(doc_id, {
            "status": "not_found",
            "error": f"No processing record for document {doc_id}"
        })

    return {
        "total": len(processing_status),
        "documents": processing_status
    }


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    exit(main())
