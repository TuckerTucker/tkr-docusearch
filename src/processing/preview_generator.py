"""
Preview Generator for DocuSearch.

Generates page previews with images and text for document preview modal.
Uses DoclingParser to re-render pages from original files.

Wave 2, Agent 3 deliverable.
"""

import logging
import base64
from io import BytesIO
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image

from ..storage import ChromaClient
from .docling_parser import DoclingParser

logger = logging.getLogger(__name__)


class PreviewResponse:
    """Preview response with page image and text."""

    def __init__(
        self,
        doc_id: str,
        page_num: int,
        image: str,
        text: str,
        metadata: Dict[str, Any]
    ):
        self.doc_id = doc_id
        self.page_num = page_num
        self.image = image
        self.text = text
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "doc_id": self.doc_id,
            "page_num": self.page_num,
            "image": self.image,
            "text": self.text,
            "metadata": self.metadata
        }


class PreviewGenerator:
    """Generate page previews from original documents."""

    def __init__(
        self,
        storage_client: ChromaClient,
        parser: DoclingParser
    ):
        """
        Initialize preview generator.

        Args:
            storage_client: ChromaDB client for metadata lookup
            parser: DoclingParser for document rendering
        """
        self.storage_client = storage_client
        self.parser = parser

    def get_page_preview(
        self,
        doc_id: str,
        page_num: int
    ) -> Optional[PreviewResponse]:
        """
        Get preview for a specific document page.

        Args:
            doc_id: Document SHA-256 hash
            page_num: Page number (1-indexed)

        Returns:
            PreviewResponse with image, text, and metadata
            None if page not found

        Raises:
            FileNotFoundError: If original file not found
            ValueError: If page_num invalid
        """
        try:
            # Get file_path from ChromaDB metadata
            file_path, doc_metadata = self._get_file_path_from_metadata(doc_id, page_num)

            if not file_path:
                logger.error(f"No file_path found for doc_id={doc_id}, page={page_num}")
                return None

            # Verify file exists
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(
                    f"Original file not found: {file_path} (doc_id={doc_id})"
                )

            # Parse document to get page
            parsed_doc = self.parser.parse_document(
                file_path=path,
                chunk_size_words=100,  # Doesn't matter for preview
                chunk_overlap_words=20
            )

            # Validate page number
            if page_num < 1 or page_num > parsed_doc.num_pages:
                raise ValueError(
                    f"Invalid page_num={page_num}. Document has {parsed_doc.num_pages} pages"
                )

            # Get the specific page (page_num is 1-indexed, list is 0-indexed)
            page = parsed_doc.pages[page_num - 1]

            # Convert image to base64 PNG
            image_data_uri = self._image_to_base64_png(page.image)

            # Get page text
            page_text = page.text if page.text else ""

            # Build metadata
            metadata = {
                "filename": doc_metadata.get("original_filename") or doc_metadata.get("filename", "unknown"),
                "total_pages": parsed_doc.num_pages,
                "file_size": path.stat().st_size if path.exists() else 0,
                "format": path.suffix.lstrip('.').lower(),
                "upload_date": doc_metadata.get("upload_date", ""),
            }

            # Add page dimensions if available
            if page.image:
                metadata["page_dimensions"] = {
                    "width": page.image.width,
                    "height": page.image.height
                }

            logger.info(
                f"Generated preview for doc_id={doc_id}, page={page_num}, "
                f"text_len={len(page_text)}, has_image={page.image is not None}"
            )

            return PreviewResponse(
                doc_id=doc_id,
                page_num=page_num,
                image=image_data_uri,
                text=page_text,
                metadata=metadata
            )

        except Exception as e:
            logger.error(
                f"Failed to generate preview for doc_id={doc_id}, page={page_num}: {e}",
                exc_info=True
            )
            raise

    def _get_file_path_from_metadata(
        self,
        doc_id: str,
        page_num: int
    ) -> tuple[Optional[str], Dict[str, Any]]:
        """
        Get file_path from ChromaDB metadata.

        Args:
            doc_id: Document identifier
            page_num: Page number

        Returns:
            Tuple of (file_path, metadata_dict)
        """
        try:
            # Try visual collection first (pages have file_path)
            results = self.storage_client._visual_collection.get(
                where={
                    "$and": [
                        {"doc_id": doc_id},
                        {"page": page_num}
                    ]
                },
                limit=1,
                include=["metadatas"]
            )

            if results['ids'] and results['metadatas']:
                metadata = results['metadatas'][0]
                file_path = metadata.get('file_path')
                if file_path:
                    return file_path, metadata

            # Fallback to text collection
            results = self.storage_client._text_collection.get(
                where={
                    "$and": [
                        {"doc_id": doc_id},
                        {"page": page_num}
                    ]
                },
                limit=1,
                include=["metadatas"]
            )

            if results['ids'] and results['metadatas']:
                metadata = results['metadatas'][0]
                file_path = metadata.get('file_path')
                if file_path:
                    return file_path, metadata

            logger.warning(
                f"No metadata found for doc_id={doc_id}, page={page_num}"
            )
            return None, {}

        except Exception as e:
            logger.error(f"Error querying metadata: {e}", exc_info=True)
            return None, {}

    def _image_to_base64_png(self, image: Optional[Image.Image]) -> str:
        """
        Convert PIL Image to base64-encoded PNG data URI.

        Args:
            image: PIL Image object

        Returns:
            Base64 data URI string (data:image/png;base64,...)
        """
        if not image:
            # Return empty 1x1 transparent PNG if no image
            return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        try:
            # Convert image to PNG bytes
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            png_bytes = buffer.getvalue()

            # Encode to base64
            base64_str = base64.b64encode(png_bytes).decode('utf-8')

            # Return as data URI
            return f"data:image/png;base64,{base64_str}"

        except Exception as e:
            logger.error(f"Failed to convert image to base64: {e}", exc_info=True)
            # Return error placeholder (1x1 red pixel)
            return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
