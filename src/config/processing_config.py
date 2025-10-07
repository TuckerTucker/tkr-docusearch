"""
Processing configuration for document processing.

This module defines configuration for file handling, text chunking,
and visual processing parameters.
"""

from dataclasses import dataclass
from typing import List, Tuple
import os


@dataclass
class ProcessingConfig:
    """Document processing configuration.

    Attributes:
        max_file_size_mb: Maximum file size in MB
        supported_formats: List of supported file extensions
        upload_dir: Directory for uploaded files
        chunk_size_words: Average words per text chunk
        chunk_overlap_words: Word overlap between chunks
        page_render_dpi: DPI for page rendering
        worker_threads: Number of parallel workers
        enable_queue: Enable processing queue
        log_level: Logging level
        log_format: Logging format
        log_file: Log file path
    """

    # File handling
    max_file_size_mb: int = int(os.getenv('MAX_FILE_SIZE_MB', '100'))
    supported_formats: List[str] = None  # type: ignore
    upload_dir: str = os.getenv('UPLOAD_DIR', '/uploads')

    # Text processing
    chunk_size_words: int = int(os.getenv('TEXT_CHUNK_SIZE', '250'))
    chunk_overlap_words: int = int(os.getenv('TEXT_CHUNK_OVERLAP', '50'))

    # Visual processing
    page_render_dpi: int = int(os.getenv('PAGE_RENDER_DPI', '150'))

    # Worker configuration
    worker_threads: int = int(os.getenv('WORKER_THREADS', '1'))
    enable_queue: bool = os.getenv('ENABLE_QUEUE', 'false').lower() == 'true'

    # Logging
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    log_format: str = os.getenv('LOG_FORMAT', 'json')
    log_file: str = os.getenv('LOG_FILE', '/data/logs/worker.log')

    def __post_init__(self):
        """Initialize supported formats from environment."""
        if self.supported_formats is None:
            formats_str = os.getenv('SUPPORTED_FORMATS', 'pdf,docx,pptx')
            self.supported_formats = [fmt.strip().lower() for fmt in formats_str.split(',')]

    def validate_file(self, filename: str, size_bytes: int) -> Tuple[bool, str]:
        """Validate uploaded file.

        Args:
            filename: Name of the uploaded file
            size_bytes: File size in bytes

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check extension
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if ext not in self.supported_formats:
            return False, f"Unsupported format: {ext}. Supported: {', '.join(self.supported_formats)}"

        # Check size
        size_mb = size_bytes / (1024 * 1024)
        if size_mb > self.max_file_size_mb:
            return False, f"File too large: {size_mb:.1f}MB > {self.max_file_size_mb}MB"

        return True, ""

    @property
    def max_file_size_bytes(self) -> int:
        """Get maximum file size in bytes.

        Returns:
            Maximum file size in bytes
        """
        return self.max_file_size_mb * 1024 * 1024

    @property
    def chunk_overlap_ratio(self) -> float:
        """Get chunk overlap as ratio of chunk size.

        Returns:
            Overlap ratio (0.0 to 1.0)
        """
        if self.chunk_size_words == 0:
            return 0.0
        return self.chunk_overlap_words / self.chunk_size_words

    def to_dict(self) -> dict:
        """Convert configuration to dictionary.

        Returns:
            Configuration as dictionary
        """
        return {
            'max_file_size_mb': self.max_file_size_mb,
            'max_file_size_bytes': self.max_file_size_bytes,
            'supported_formats': self.supported_formats,
            'upload_dir': self.upload_dir,
            'chunk_size_words': self.chunk_size_words,
            'chunk_overlap_words': self.chunk_overlap_words,
            'chunk_overlap_ratio': self.chunk_overlap_ratio,
            'page_render_dpi': self.page_render_dpi,
            'worker_threads': self.worker_threads,
            'enable_queue': self.enable_queue,
            'log_level': self.log_level,
            'log_format': self.log_format,
        }

    def __repr__(self) -> str:
        """String representation of configuration."""
        return (
            f"ProcessingConfig("
            f"max_size={self.max_file_size_mb}MB, "
            f"formats={self.supported_formats}, "
            f"chunk_size={self.chunk_size_words}w, "
            f"dpi={self.page_render_dpi})"
        )
