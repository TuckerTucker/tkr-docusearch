"""
Format options builder for Docling document converter.

This module contains helpers to build format-specific options for
different document types, extracted from DoclingParser for reduced complexity.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class FormatOptionsBuilder:
    """Builder for Docling format options."""

    @staticmethod
    def build_pdf_options(pipeline_options):
        """
        Build PDF format options.

        Args:
            pipeline_options: Pipeline options for PDF processing

        Returns:
            Dict with PDF format options
        """
        from docling.datamodel.base_models import InputFormat
        from docling.document_converter import PdfFormatOption

        return {InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}

    @staticmethod
    def build_image_options(pipeline_options):
        """
        Build image format options.

        Args:
            pipeline_options: Pipeline options for image processing

        Returns:
            Dict with image format options
        """
        from docling.datamodel.base_models import InputFormat
        from docling.document_converter import ImageFormatOption

        return {InputFormat.IMAGE: ImageFormatOption(pipeline_options=pipeline_options)}

    @staticmethod
    def build_docx_options():
        """
        Build DOCX format options.

        Returns:
            Dict with DOCX format options
        """
        from docling.datamodel.base_models import InputFormat
        from docling.document_converter import WordFormatOption

        return {InputFormat.DOCX: WordFormatOption()}

    @staticmethod
    def build_audio_options(file_path: str) -> Dict:
        """
        Build audio format options with ASR configuration.

        Args:
            file_path: Path to audio file

        Returns:
            Dict with audio format options
        """
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import AsrPipelineOptions
        from docling.document_converter import AudioFormatOption
        from docling.pipeline.asr_pipeline import AsrPipeline

        from src.config.processing_config import AsrConfig

        try:
            # Load ASR configuration
            asr_config = AsrConfig.from_env()

            if asr_config.enabled:
                logger.info(f"Configuring ASR pipeline with model={asr_config.model}")

                # Create Docling ASR options
                asr_pipeline_options = AsrPipelineOptions()
                asr_pipeline_options.asr_options = asr_config.to_docling_model_spec()

                # Add to format options
                return {
                    InputFormat.AUDIO: AudioFormatOption(
                        pipeline_cls=AsrPipeline, pipeline_options=asr_pipeline_options
                    )
                }
            else:
                logger.warning(f"ASR disabled, audio file {file_path} will have minimal processing")
                return {}

        except Exception as e:
            logger.error(f"Failed to configure ASR: {e}")
            return {}

    @staticmethod
    def build_format_options(
        file_path: str, pipeline_options, config: Optional[Any] = None
    ) -> Dict:
        """
        Build format options based on file extension.

        Args:
            file_path: Path to document file
            pipeline_options: Base pipeline options
            config: Optional enhanced mode configuration

        Returns:
            Dict of format options for DocumentConverter
        """
        ext = Path(file_path).suffix.lower()

        # Import format sets
        from ..docling_parser import IMAGE_FORMATS

        format_options = {}

        if ext == ".pdf":
            format_options = FormatOptionsBuilder.build_pdf_options(pipeline_options)
        elif ext in IMAGE_FORMATS:
            format_options = FormatOptionsBuilder.build_image_options(pipeline_options)
        elif ext == ".docx":
            format_options = FormatOptionsBuilder.build_docx_options()
        elif ext in [".mp3", ".wav"]:
            format_options = FormatOptionsBuilder.build_audio_options(file_path)
        # PPTX, XLSX, and other formats use default handling

        return format_options if format_options else None
