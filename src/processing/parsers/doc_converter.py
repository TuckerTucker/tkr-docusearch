"""
Helper for .doc to .docx conversion.

This module provides a utility for converting legacy .doc files to modern .docx
format using the legacy-office-converter service.
"""

import logging
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)


class DocConverter:
    """Helper for converting .doc files to .docx."""

    def __init__(self):
        """Initialize converter."""
        pass

    def convert_if_needed(self, file_path: str) -> Tuple[str, bool]:
        """Convert .doc to .docx if needed.

        This method checks if the file is a .doc file and converts it to .docx
        if necessary. Files that are already .docx (or other formats) are
        returned unchanged.

        Args:
            file_path: Path to file (native or Docker path)

        Returns:
            Tuple of (path_to_use, was_converted)
            - path_to_use: Path to use for processing (original or converted)
            - was_converted: True if conversion happened, False otherwise

        Raises:
            LegacyOfficeError: If conversion fails

        Example:
            >>> converter = DocConverter()
            >>> # Native path
            >>> path, converted = converter.convert_if_needed('/Volumes/.../data/uploads/report.doc')
            >>> print(f"Use: {path}, Converted: {converted}")
            Use: /uploads/report.docx, Converted: True

            >>> # Already .docx
            >>> path, converted = converter.convert_if_needed('/uploads/modern.docx')
            >>> print(f"Use: {path}, Converted: {converted}")
            Use: /uploads/modern.docx, Converted: False
        """
        from src.processing.legacy_office_client import get_legacy_office_client

        file_path_obj = Path(file_path)
        extension = file_path_obj.suffix.lower()

        # Only convert .doc and .dot files
        if extension not in [".doc", ".dot"]:
            logger.debug(f"File is not .doc/.dot, no conversion needed: {file_path}")
            return file_path, False

        logger.info(f"Detected legacy .doc file, converting to .docx: {file_path_obj.name}")

        # Determine if this is a Docker path or native path
        # Docker paths start with /uploads or /page_images
        is_docker_path = file_path.startswith("/uploads") or file_path.startswith("/page_images")

        if is_docker_path:
            # Already a Docker path, use it directly
            docker_doc_path = file_path
        else:
            # Native path, convert to Docker path
            # Assume uploads directory: /Volumes/.../data/uploads/file.doc -> /uploads/file.doc
            docker_doc_path = f"/uploads/{file_path_obj.name}"

        logger.debug(f"Using Docker path for conversion: {docker_doc_path}")

        # Call conversion service
        client = get_legacy_office_client()
        docker_docx_path = client.convert_doc_to_docx(
            doc_path=docker_doc_path, output_dir="/uploads"
        )

        logger.info(f"Conversion successful: {docker_doc_path} -> {docker_docx_path}")

        return docker_docx_path, True
