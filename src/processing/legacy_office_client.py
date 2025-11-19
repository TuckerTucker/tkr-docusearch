"""
Legacy Office Client - HTTP client for legacy Office format conversion service.

This module provides a Python client for calling the legacy-office-converter Docker
service to:
1. Convert PPTX slides to PNG images (legacy functionality)
2. Convert .doc files to .docx format (new functionality)
"""

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class LegacyOfficeError(Exception):
    """Error from legacy office conversion service."""


class LegacyOfficeClient:
    """Client for legacy Office conversion HTTP service.

    Attributes:
        host: Legacy office service host
        port: Legacy office service port
        base_url: Base URL for service
        timeout: Request timeout in seconds
    """

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None, timeout: int = 60):
        """Initialize legacy office client.

        Args:
            host: Service host (default: from LEGACY_OFFICE_HOST or SLIDE_RENDERER_HOST env)
            port: Service port (default: from LEGACY_OFFICE_PORT or SLIDE_RENDERER_PORT env)
            timeout: Request timeout in seconds (default: 60)
        """
        # Support both new and old environment variable names (with fallback)
        self.host = host or os.getenv("LEGACY_OFFICE_HOST") or os.getenv("SLIDE_RENDERER_HOST", "localhost")
        self.port = port or int(os.getenv("LEGACY_OFFICE_PORT") or os.getenv("SLIDE_RENDERER_PORT", "8003"))
        self.base_url = f"http://{self.host}:{self.port}"
        self.timeout = timeout

        logger.info(f"Initialized LegacyOfficeClient: {self.base_url}")

    def check_health(self) -> bool:
        """Check if legacy office service is healthy.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Legacy office service health check failed: {e}")
            return False

    def render_slides(  # noqa: C901
        self, pptx_path: str, output_dir: str, dpi: int = 150, max_retries: int = 3
    ) -> List[str]:
        """Render PPTX slides to PNG images.

        Args:
            pptx_path: Path to PPTX file (Docker path format, e.g., /uploads/file.pptx)
            output_dir: Directory to save rendered slides
            dpi: Resolution for rendering (default: 150)
            max_retries: Maximum number of retry attempts (default: 3)

        Returns:
            List of paths to rendered slide images

        Raises:
            LegacyOfficeError: If rendering fails
            FileNotFoundError: If PPTX file doesn't exist
            ConnectionError: If service is unreachable
        """
        # Note: We don't validate pptx_path exists here because the native worker
        # passes Docker paths (e.g., /uploads/file.pptx) which don't exist on the
        # macOS host. The legacy-office-converter service will validate the path in Docker.

        # Note: We also don't create output_dir here because it's a Docker path
        # (e.g., /page_images/temp-slides-xxx) which doesn't exist on macOS.
        # The legacy-office-converter service will create the directory in Docker.

        # Prepare request payload
        payload = {"file_path": str(pptx_path), "output_dir": str(output_dir), "dpi": dpi}

        logger.info(f"Rendering slides: {Path(pptx_path).name} → {output_dir} @ {dpi} DPI")

        # Retry loop for transient errors
        last_error: Optional[Exception] = None
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.post(
                    f"{self.base_url}/render", json=payload, timeout=self.timeout
                )

                # Check response status
                if response.status_code == 200:
                    result = response.json()

                    if not result.get("success"):
                        error_msg = result.get("error", "Unknown error")
                        raise LegacyOfficeError(f"Rendering failed: {error_msg}")

                    slide_paths = result.get("slide_paths", [])
                    slide_count = result.get("slide_count", 0)

                    logger.info(
                        f"Successfully rendered {slide_count} slides from {Path(pptx_path).name}"
                    )

                    return slide_paths

                elif response.status_code == 404:
                    raise FileNotFoundError(f"PPTX file not found by service: {pptx_path}")
                else:
                    error_detail = response.json().get("detail", response.text)
                    raise LegacyOfficeError(
                        f"Rendering failed ({response.status_code}): {error_detail}"
                    )

            except requests.exceptions.Timeout as e:
                last_error = e
                logger.warning(f"Rendering timeout on attempt {attempt}/{max_retries}: {e}")
            except requests.exceptions.ConnectionError as e:
                last_error = e
                logger.warning(f"Connection error on attempt {attempt}/{max_retries}: {e}")
            except LegacyOfficeError:
                # Don't retry on rendering errors
                raise
            except FileNotFoundError:
                # Don't retry on file not found
                raise
            except Exception as e:
                last_error = e
                logger.warning(f"Unexpected error on attempt {attempt}/{max_retries}: {e}")

            # Wait before retrying (exponential backoff)
            if attempt < max_retries:
                wait_time = 2**attempt  # 2, 4, 8 seconds
                logger.info(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)

        # All retries failed
        raise ConnectionError(f"Failed to render slides after {max_retries} attempts: {last_error}")

    def convert_doc_to_docx(self, doc_path: str, output_dir: str = "/uploads") -> str:
        """Convert .doc file to .docx format.

        Args:
            doc_path: Path to .doc file (Docker path format, e.g., /uploads/file.doc)
            output_dir: Output directory for .docx file (default: /uploads)

        Returns:
            Path to converted .docx file (Docker path format)

        Raises:
            LegacyOfficeError: If conversion fails or service unavailable

        Example:
            >>> client = LegacyOfficeClient()
            >>> docx_path = client.convert_doc_to_docx('/uploads/report.doc')
            >>> print(docx_path)
            /uploads/report.docx
        """
        # Prepare request payload
        payload = {"file_path": str(doc_path), "output_dir": str(output_dir)}

        logger.info(f"Converting .doc to .docx: {Path(doc_path).name}")

        try:
            response = requests.post(
                f"{self.base_url}/convert-doc", json=payload, timeout=self.timeout
            )

            # Parse response
            result = response.json()

            # Check for success
            if response.status_code == 200 and result.get("success"):
                docx_path = result.get("docx_path")
                file_size = result.get("file_size_bytes", 0)
                conversion_time = result.get("conversion_time_ms", 0)

                logger.info(
                    f"Successfully converted {Path(doc_path).name} to .docx "
                    f"({file_size} bytes, {conversion_time}ms)"
                )

                return docx_path

            # Handle error responses
            error_msg = result.get("error", "Unknown error")

            if response.status_code == 400:
                raise LegacyOfficeError(f"Invalid request: {error_msg}")
            elif response.status_code == 403:
                raise LegacyOfficeError(f"Access denied: {error_msg}")
            elif response.status_code == 404:
                raise FileNotFoundError(f"File not found: {error_msg}")
            elif response.status_code == 500:
                raise LegacyOfficeError(f"Conversion failed: {error_msg}")
            else:
                raise LegacyOfficeError(
                    f"Conversion failed ({response.status_code}): {error_msg}"
                )

        except requests.exceptions.Timeout as e:
            raise LegacyOfficeError(f"Conversion timeout: {e}")
        except requests.exceptions.ConnectionError as e:
            raise LegacyOfficeError(f"Service unavailable: {e}")
        except LegacyOfficeError:
            # Re-raise our own exceptions
            raise
        except FileNotFoundError:
            # Re-raise file not found
            raise
        except Exception as e:
            raise LegacyOfficeError(f"Unexpected error during conversion: {e}")

    def get_info(self) -> Dict[str, Any]:
        """Get legacy office service information.

        Returns:
            Dictionary with service metadata including version and capabilities

        Raises:
            ConnectionError: If service is unreachable
        """
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise ConnectionError(f"Failed to get service info: {e}")


# Singleton instance for convenience
_client_instance: Optional[LegacyOfficeClient] = None


def get_legacy_office_client() -> LegacyOfficeClient:
    """Get singleton legacy office client instance.

    Returns:
        LegacyOfficeClient instance
    """
    global _client_instance

    if _client_instance is None:
        _client_instance = LegacyOfficeClient()

    return _client_instance


# Backward compatibility aliases (deprecated)
SlideRendererClient = LegacyOfficeClient
SlideRendererError = LegacyOfficeError
get_slide_renderer = get_legacy_office_client
