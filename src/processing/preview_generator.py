"""Preview Generator for DocuSearch.

Generates page previews with images and text for document preview modal.
Uses pypdfium2 for PDF rendering and PIL for image files.
"""

import base64
import logging
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Optional

from PIL import Image

try:
    from ..storage import KojiClient
except ImportError:
    from src.storage import KojiClient

logger = logging.getLogger(__name__)


class PreviewResponse:
    """Preview response with page image and text."""

    def __init__(self, doc_id: str, page_num: int, image: str, text: str, metadata: Dict[str, Any]):
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
            "metadata": self.metadata,
        }


class PreviewGenerator:
    """Generate page previews from stored page data or original files.

    Args:
        storage_client: Koji client for metadata and page lookup.
    """

    def __init__(self, storage_client: KojiClient, parser: Any = None):
        """Initialize preview generator.

        Args:
            storage_client: Koji client for metadata lookup.
            parser: Unused — kept for backward compatibility.
        """
        self.storage_client = storage_client

    def get_page_preview(self, doc_id: str, page_num: int) -> Optional[PreviewResponse]:
        """Get preview for a specific document page.

        Attempts to load the page image from Koji first. Falls back to
        re-rendering from the original file if no stored image exists.

        Args:
            doc_id: Document SHA-256 hash.
            page_num: Page number (1-indexed).

        Returns:
            PreviewResponse with image, text, and metadata.
            None if page not found.

        Raises:
            FileNotFoundError: If original file not found.
            ValueError: If page_num invalid.
        """
        try:
            page_id = f"{doc_id}-page{page_num:03d}"
            page_data = self.storage_client.get_page(page_id)

            # Try to use stored page image
            if page_data and page_data.get("image"):
                img = Image.open(BytesIO(page_data["image"]))
                image_data_uri = self._image_to_base64_png(img)
                doc_data = self.storage_client.get_document(doc_id) or {}
                return PreviewResponse(
                    doc_id=doc_id,
                    page_num=page_num,
                    image=image_data_uri,
                    text="",
                    metadata={
                        "filename": doc_data.get("filename", "unknown"),
                        "format": doc_data.get("format", ""),
                    },
                )

            # Fallback: re-render from original file
            file_path, doc_metadata = self._get_file_path_from_metadata(doc_id, page_num)
            if not file_path:
                logger.error(f"No file_path found for doc_id={doc_id}, page={page_num}")
                return None

            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"Original file not found: {file_path}")

            ext = path.suffix.lower()
            pages = self._render_page(str(path), ext, page_num)
            if not pages:
                return None

            page_image = pages[0]
            image_data_uri = self._image_to_base64_png(page_image)

            metadata = {
                "filename": doc_metadata.get("filename", "unknown"),
                "format": ext.lstrip("."),
                "file_size": path.stat().st_size,
            }
            if page_image:
                metadata["page_dimensions"] = {
                    "width": page_image.width,
                    "height": page_image.height,
                }

            return PreviewResponse(
                doc_id=doc_id,
                page_num=page_num,
                image=image_data_uri,
                text="",
                metadata=metadata,
            )

        except Exception as e:
            logger.error(
                f"Failed to generate preview for doc_id={doc_id}, page={page_num}: {e}",
                exc_info=True,
            )
            raise

    @staticmethod
    def _render_page(file_path: str, ext: str, page_num: int) -> list:
        """Render a single page from a file.

        Args:
            file_path: Path to source file.
            ext: File extension.
            page_num: 1-indexed page number.

        Returns:
            List containing the rendered PIL Image, or empty list.
        """
        if ext in {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}:
            try:
                return [Image.open(file_path).convert("RGB")]
            except Exception:
                return []

        # Office formats: convert to PDF first, then render the requested page
        if ext in {".pptx", ".docx"}:
            from .processor import DocumentProcessor

            pdf_path = DocumentProcessor._convert_office_to_pdf(file_path)
            if pdf_path is None:
                return []
            try:
                return PreviewGenerator._render_pdf_page(pdf_path, page_num)
            finally:
                Path(pdf_path).unlink(missing_ok=True)

        if ext == ".pdf":
            return PreviewGenerator._render_pdf_page(file_path, page_num)

        return []

    @staticmethod
    def _render_pdf_page(pdf_path: str, page_num: int) -> list:
        """Render a single page from a PDF.

        Args:
            pdf_path: Path to the PDF file.
            page_num: 1-indexed page number.

        Returns:
            List containing the rendered PIL Image, or empty list.
        """
        try:
            import pypdfium2 as pdfium

            pdf = pdfium.PdfDocument(pdf_path)
            idx = page_num - 1
            if idx < 0 or idx >= len(pdf):
                pdf.close()
                return []
            page = pdf[idx]
            bitmap = page.render(scale=150 / 72)
            img = bitmap.to_pil().convert("RGB")
            pdf.close()
            return [img]
        except Exception:
            return []

    def _get_file_path_from_metadata(
        self, doc_id: str, page_num: int
    ) -> tuple[Optional[str], Dict[str, Any]]:
        """Get file_path from Koji metadata.

        Args:
            doc_id: Document identifier.
            page_num: Page number.

        Returns:
            Tuple of (file_path, metadata_dict).
        """
        try:
            page_id = f"{doc_id}-page{page_num:03d}"
            page_data = self.storage_client.get_page(page_id)

            if page_data:
                structure = page_data.get("structure") or {}
                file_path = structure.get("file_path") if isinstance(structure, dict) else None
                if file_path:
                    return file_path, page_data

            doc_data = self.storage_client.get_document(doc_id)
            if doc_data:
                metadata = doc_data.get("metadata") or {}
                file_path = metadata.get("file_path") if isinstance(metadata, dict) else None
                if file_path:
                    return file_path, doc_data

            return None, {}

        except Exception as e:
            logger.error(f"Error querying metadata: {e}", exc_info=True)
            return None, {}

    @staticmethod
    def _image_to_base64_png(image: Optional[Image.Image]) -> str:
        """Convert PIL Image to base64-encoded PNG data URI.

        Args:
            image: PIL Image object.

        Returns:
            Base64 data URI string.
        """
        if not image:
            return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        try:
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            png_bytes = buffer.getvalue()
            base64_str = base64.b64encode(png_bytes).decode("utf-8")
            return f"data:image/png;base64,{base64_str}"
        except Exception as e:
            logger.error(f"Failed to convert image to base64: {e}", exc_info=True)
            return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
