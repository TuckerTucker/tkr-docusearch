"""
Processing configuration for document processing.

This module defines configuration for file handling, text chunking,
and visual processing parameters, including enhanced Docling features.
"""

from dataclasses import dataclass
from typing import List, Tuple, Set
from enum import Enum
import os
import logging

logger = logging.getLogger(__name__)


class ChunkingStrategy(Enum):
    """Chunking strategy selection.

    Attributes:
        LEGACY: Word-based sliding window (backward compatible)
        HYBRID: Document-aware hybrid chunker (recommended)
    """
    LEGACY = "legacy"
    HYBRID = "hybrid"


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
            formats_str = os.getenv('SUPPORTED_FORMATS', 'pdf,docx,pptx,xlsx,html,xhtml,md,asciidoc,csv,mp3,wav,vtt,png,jpg,jpeg,tiff,bmp,webp')
            self.supported_formats = [fmt.strip().lower() for fmt in formats_str.split(',')]

    def validate_file(self, filename: str, size_bytes: int) -> Tuple[bool, str]:
        """Validate uploaded file.

        Args:
            filename: Name of the uploaded file
            size_bytes: File size in bytes

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Delegate to file_validator module for consistency
        from ..processing.file_validator import validate_file as validator
        return validator(filename, size_bytes, self.max_file_size_mb)

    @property
    def supported_extensions_set(self) -> Set[str]:
        """Get supported file extensions as set with dot prefix.

        Returns:
            Set of extensions like {'.pdf', '.docx', ...}
        """
        from ..processing.file_validator import get_supported_extensions
        return get_supported_extensions()

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


@dataclass
class EnhancedModeConfig:
    """Configuration for Docling enhanced mode features.

    This configuration controls which advanced Docling features are enabled
    and how document processing behaves. All features have sensible defaults
    that can be overridden via environment variables.

    Attributes:
        enable_table_structure: Enable table structure recognition with TableFormer
        enable_picture_classification: Enable image type classification
        enable_code_enrichment: Enable code block language detection (slower)
        enable_formula_enrichment: Enable formula LaTeX extraction (slower)
        chunking_strategy: Text chunking strategy (legacy or hybrid)
        max_chunk_tokens: Maximum tokens per chunk
        min_chunk_tokens: Minimum tokens per chunk
        merge_peer_chunks: Merge adjacent small chunks with same headings
        table_structure_mode: TableFormer mode (fast or accurate)
        images_scale: Image generation scale factor
        generate_page_images: Generate full page images
        generate_picture_images: Generate individual picture images
        max_structure_size_kb: Maximum size of structure metadata
    """

    # Feature flags (all default to True for enhanced mode)
    enable_table_structure: bool = True
    enable_picture_classification: bool = True
    enable_code_enrichment: bool = False  # Optional, adds overhead
    enable_formula_enrichment: bool = False  # Optional, adds overhead

    # Chunking configuration
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.HYBRID
    max_chunk_tokens: int = 512
    min_chunk_tokens: int = 100
    merge_peer_chunks: bool = True

    # Pipeline options
    table_structure_mode: str = "accurate"  # "fast" or "accurate"
    images_scale: float = 2.0
    generate_page_images: bool = True
    generate_picture_images: bool = True

    # Performance limits
    max_structure_size_kb: int = 100  # Max size of structure metadata

    @classmethod
    def from_env(cls) -> "EnhancedModeConfig":
        """Load configuration from environment variables.

        Environment variables:
            ENABLE_TABLE_STRUCTURE: Enable table structure (default: true)
            ENABLE_PICTURE_CLASSIFICATION: Enable picture classification (default: true)
            ENABLE_CODE_ENRICHMENT: Enable code enrichment (default: false)
            ENABLE_FORMULA_ENRICHMENT: Enable formula enrichment (default: false)
            CHUNKING_STRATEGY: Chunking strategy (default: hybrid)
            MAX_CHUNK_TOKENS: Max tokens per chunk (default: 512)
            MIN_CHUNK_TOKENS: Min tokens per chunk (default: 100)
            MERGE_PEER_CHUNKS: Merge peer chunks (default: true)
            TABLE_STRUCTURE_MODE: Table mode (default: accurate)
            IMAGES_SCALE: Image scale (default: 2.0)

        Returns:
            EnhancedModeConfig instance with values from environment
        """
        try:
            # Parse feature flags
            enable_table = os.getenv("ENABLE_TABLE_STRUCTURE", "true").lower() == "true"
            enable_pictures = os.getenv("ENABLE_PICTURE_CLASSIFICATION", "true").lower() == "true"
            enable_code = os.getenv("ENABLE_CODE_ENRICHMENT", "false").lower() == "true"
            enable_formula = os.getenv("ENABLE_FORMULA_ENRICHMENT", "false").lower() == "true"

            # Parse chunking config
            chunking_str = os.getenv("CHUNKING_STRATEGY", "hybrid").lower()
            try:
                chunking_strategy = ChunkingStrategy(chunking_str)
            except ValueError:
                logger.warning(
                    f"Invalid CHUNKING_STRATEGY '{chunking_str}', using default 'hybrid'"
                )
                chunking_strategy = ChunkingStrategy.HYBRID

            max_tokens = int(os.getenv("MAX_CHUNK_TOKENS", "512"))
            min_tokens = int(os.getenv("MIN_CHUNK_TOKENS", "100"))
            merge_peers = os.getenv("MERGE_PEER_CHUNKS", "true").lower() == "true"

            # Parse pipeline options
            table_mode = os.getenv("TABLE_STRUCTURE_MODE", "accurate").lower()
            if table_mode not in ["fast", "accurate"]:
                logger.warning(
                    f"Invalid TABLE_STRUCTURE_MODE '{table_mode}', using 'accurate'"
                )
                table_mode = "accurate"

            images_scale = float(os.getenv("IMAGES_SCALE", "2.0"))

            config = cls(
                enable_table_structure=enable_table,
                enable_picture_classification=enable_pictures,
                enable_code_enrichment=enable_code,
                enable_formula_enrichment=enable_formula,
                chunking_strategy=chunking_strategy,
                max_chunk_tokens=max_tokens,
                min_chunk_tokens=min_tokens,
                merge_peer_chunks=merge_peers,
                table_structure_mode=table_mode,
                images_scale=images_scale
            )

            # Validate configuration
            validate_config(config)

            logger.info(
                f"Loaded enhanced mode config: "
                f"table_structure={enable_table}, "
                f"picture_classification={enable_pictures}, "
                f"chunking={chunking_strategy.value}, "
                f"tokens={min_tokens}-{max_tokens}"
            )

            return config

        except Exception as e:
            logger.error(f"Error loading config from environment: {e}")
            logger.info("Using default configuration")
            return cls()


def validate_config(config: EnhancedModeConfig) -> None:
    """Validate configuration values.

    Args:
        config: Configuration to validate

    Raises:
        AssertionError: If configuration values are invalid
    """
    # Token limits
    assert 10 <= config.min_chunk_tokens <= 1000, \
        f"min_chunk_tokens {config.min_chunk_tokens} out of range [10, 1000]"

    assert 100 <= config.max_chunk_tokens <= 4096, \
        f"max_chunk_tokens {config.max_chunk_tokens} out of range [100, 4096]"

    assert config.min_chunk_tokens < config.max_chunk_tokens, \
        f"min_chunk_tokens {config.min_chunk_tokens} must be < max_chunk_tokens {config.max_chunk_tokens}"

    # Image scale
    assert 0.5 <= config.images_scale <= 4.0, \
        f"images_scale {config.images_scale} out of range [0.5, 4.0]"

    # Table mode
    assert config.table_structure_mode in ["fast", "accurate"], \
        f"Invalid table_structure_mode: {config.table_structure_mode}"


def create_pipeline_options(config: EnhancedModeConfig):
    """Create Docling pipeline options from configuration.

    Args:
        config: Enhanced mode configuration

    Returns:
        PdfPipelineOptions configured according to settings
    """
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode

    options = PdfPipelineOptions()

    # Structure features
    options.do_table_structure = config.enable_table_structure
    options.do_picture_classification = config.enable_picture_classification
    options.do_code_enrichment = config.enable_code_enrichment
    options.do_formula_enrichment = config.enable_formula_enrichment

    # Table structure mode
    if config.enable_table_structure:
        options.table_structure_options.mode = (
            TableFormerMode.ACCURATE if config.table_structure_mode == "accurate"
            else TableFormerMode.FAST
        )

    # Image options
    options.generate_page_images = config.generate_page_images
    options.generate_picture_images = config.generate_picture_images
    options.images_scale = config.images_scale

    logger.debug(
        f"Created pipeline options: "
        f"table_structure={options.do_table_structure}, "
        f"picture_classification={options.do_picture_classification}"
    )

    return options


# ============================================================================
# ASR (Automatic Speech Recognition) Configuration
# ============================================================================

@dataclass
class AsrConfig:
    """Configuration for Automatic Speech Recognition (Whisper).

    Controls Whisper ASR settings for MP3/WAV audio file transcription.
    All settings have sensible defaults and can be overridden via environment
    variables.

    Attributes:
        enabled: Whether ASR processing is enabled
        model: Whisper model to use (turbo, base, small, medium, large)
        language: Language code or "auto" for detection
        device: Compute device (mps, cpu, cuda)
        word_timestamps: Enable word-level timestamps
        temperature: Sampling temperature for generation (0.0 = deterministic)
        max_time_chunk: Maximum audio chunk duration (seconds)
    """

    enabled: bool = True
    model: str = "turbo"  # turbo, base, small, medium, large
    language: str = "en"  # ISO 639-1 code or "auto"
    device: str = "mps"  # mps, cpu, cuda
    word_timestamps: bool = True
    temperature: float = 0.0  # 0.0-1.0, lower = more deterministic
    max_time_chunk: float = 30.0  # seconds

    def __post_init__(self):
        """Validate configuration values."""
        # Validate model
        valid_models = ["turbo", "base", "small", "medium", "large"]
        if self.model not in valid_models:
            raise ValueError(
                f"Invalid model: {self.model}. Must be one of {valid_models}"
            )

        # Validate device
        valid_devices = ["mps", "cpu", "cuda"]
        if self.device not in valid_devices:
            raise ValueError(
                f"Invalid device: {self.device}. Must be one of {valid_devices}"
            )

        # Validate temperature
        if not (0.0 <= self.temperature <= 1.0):
            raise ValueError(
                f"Temperature must be 0.0-1.0, got {self.temperature}"
            )

        # Validate max_time_chunk
        if self.max_time_chunk <= 0:
            raise ValueError(
                f"max_time_chunk must be positive, got {self.max_time_chunk}"
            )

    def to_docling_model_spec(self):
        """Convert to Docling ASR model specification.

        Returns:
            InlineAsrNativeWhisperOptions instance configured for Whisper ASR

        Raises:
            ImportError: If Docling ASR modules not available
        """
        try:
            from docling.datamodel.pipeline_options_asr_model import (
                InlineAsrNativeWhisperOptions
            )
        except ImportError as e:
            raise ImportError(
                "Docling ASR not installed. Install with: pip install docling[asr]"
            ) from e

        # Map our model names to Docling repo_ids
        # Note: For native Whisper, use simple model names, not HuggingFace repo IDs
        model_map = {
            "turbo": "turbo",
            "base": "base",
            "small": "small",
            "medium": "medium",
            "large": "large"
        }

        repo_id = model_map[self.model]

        # Build kwargs dynamically - omit language if "auto"
        kwargs = {
            "repo_id": repo_id,
            "word_timestamps": self.word_timestamps,
            "temperature": self.temperature,
            "max_time_chunk": self.max_time_chunk,
            "device": self.device  # ADD DEVICE FOR MPS/CUDA/CPU ACCELERATION
        }

        # Only include language if not "auto" (for auto-detection, omit the parameter)
        if self.language != "auto":
            kwargs["language"] = self.language

        # Create Docling ASR options
        return InlineAsrNativeWhisperOptions(**kwargs)

    @classmethod
    def from_env(cls) -> "AsrConfig":
        """Load configuration from environment variables.

        Environment Variables:
            ASR_ENABLED: Enable ASR (default: true)
            ASR_MODEL: Model name (default: turbo)
            ASR_LANGUAGE: Language code (default: en)
            ASR_DEVICE: Compute device (default: mps)
            ASR_WORD_TIMESTAMPS: Enable word timestamps (default: true)
            ASR_TEMPERATURE: Sampling temperature (default: 0.0)
            ASR_MAX_TIME_CHUNK: Max chunk duration (default: 30.0)

        Returns:
            AsrConfig instance loaded from environment

        Example:
            >>> import os
            >>> os.environ["ASR_MODEL"] = "base"
            >>> config = AsrConfig.from_env()
            >>> config.model
            'base'
        """
        try:
            enabled = os.getenv("ASR_ENABLED", "true").lower() == "true"
            model = os.getenv("ASR_MODEL", "turbo")
            language = os.getenv("ASR_LANGUAGE", "en")
            device = os.getenv("ASR_DEVICE", "mps")
            word_timestamps = os.getenv("ASR_WORD_TIMESTAMPS", "true").lower() == "true"

            # Parse numeric values with error handling
            try:
                temperature = float(os.getenv("ASR_TEMPERATURE", "0.0"))
            except ValueError:
                logger.warning("Invalid ASR_TEMPERATURE, using default 0.0")
                temperature = 0.0

            try:
                max_time_chunk = float(os.getenv("ASR_MAX_TIME_CHUNK", "30.0"))
            except ValueError:
                logger.warning("Invalid ASR_MAX_TIME_CHUNK, using default 30.0")
                max_time_chunk = 30.0

            config = cls(
                enabled=enabled,
                model=model,
                language=language,
                device=device,
                word_timestamps=word_timestamps,
                temperature=temperature,
                max_time_chunk=max_time_chunk
            )

            logger.info(
                f"Loaded ASR config: model={model}, language={language}, "
                f"device={device}, enabled={enabled}"
            )

            return config

        except ValueError as e:
            # Validation error from __post_init__
            logger.error(f"Invalid ASR configuration: {e}")
            logger.info("Using default ASR configuration")
            return cls()
        except Exception as e:
            logger.error(f"Error loading ASR config from environment: {e}")
            logger.info("Using default ASR configuration")
            return cls()

    def to_dict(self) -> dict:
        """Convert configuration to dictionary.

        Returns:
            Configuration as dictionary
        """
        return {
            "enabled": self.enabled,
            "model": self.model,
            "language": self.language,
            "device": self.device,
            "word_timestamps": self.word_timestamps,
            "temperature": self.temperature,
            "max_time_chunk": self.max_time_chunk
        }

    def __repr__(self) -> str:
        """String representation of configuration."""
        return (
            f"AsrConfig(model={self.model}, language={self.language}, "
            f"device={self.device}, enabled={self.enabled})"
        )
