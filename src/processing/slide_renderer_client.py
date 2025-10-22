"""
Slide Renderer Client - HTTP client for slide renderer service.

This module provides a Python client for calling the slide-renderer Docker
service to convert PPTX slides to PNG images.
"""

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class SlideRendererError(Exception):
    """Error from slide renderer service."""


class SlideRendererClient:
    """Client for slide renderer HTTP service.

    Attributes:
        host: Slide renderer service host
        port: Slide renderer service port
        base_url: Base URL for service
        timeout: Request timeout in seconds
    """

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None, timeout: int = 60):
        """Initialize slide renderer client.

        Args:
            host: Service host (default: from SLIDE_RENDERER_HOST env)
            port: Service port (default: from SLIDE_RENDERER_PORT env)
            timeout: Request timeout in seconds (default: 60)
        """
        self.host = host or os.getenv("SLIDE_RENDERER_HOST", "localhost")
        self.port = port or int(os.getenv("SLIDE_RENDERER_PORT", "8003"))
        self.base_url = f"http://{self.host}:{self.port}"
        self.timeout = timeout

        logger.info(f"Initialized SlideRendererClient: {self.base_url}")

    def health_check(self) -> bool:
        """Check if slide renderer service is healthy.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Slide renderer health check failed: {e}")
            return False

    def render_slides(  # noqa: C901
        self, pptx_path: str, output_dir: str, dpi: int = 150, max_retries: int = 3
    ) -> List[str]:
        """Render PPTX slides to PNG images.

        Args:
            pptx_path: Path to PPTX file (must be accessible in Docker volume)
            output_dir: Directory to save rendered slides
            dpi: Resolution for rendering (default: 150)
            max_retries: Maximum number of retry attempts (default: 3)

        Returns:
            List of paths to rendered slide images

        Raises:
            SlideRendererError: If rendering fails
            FileNotFoundError: If PPTX file doesn't exist
            ConnectionError: If service is unreachable
        """
        # Note: We don't validate pptx_path exists here because the native worker
        # passes Docker paths (e.g., /uploads/file.pptx) which don't exist on the
        # macOS host. The slide-renderer service will validate the path in Docker.

        # Note: We also don't create output_dir here because it's a Docker path
        # (e.g., /page_images/temp-slides-xxx) which doesn't exist on macOS.
        # The slide-renderer service will create the directory in Docker.

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
                        raise SlideRendererError(f"Rendering failed: {error_msg}")

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
                    raise SlideRendererError(
                        f"Rendering failed ({response.status_code}): {error_detail}"
                    )

            except requests.exceptions.Timeout as e:
                last_error = e
                logger.warning(f"Rendering timeout on attempt {attempt}/{max_retries}: {e}")
            except requests.exceptions.ConnectionError as e:
                last_error = e
                logger.warning(f"Connection error on attempt {attempt}/{max_retries}: {e}")
            except SlideRendererError:
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

    def get_service_info(self) -> Dict[str, Any]:
        """Get slide renderer service information.

        Returns:
            Dictionary with service metadata

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
_client_instance: Optional[SlideRendererClient] = None


def get_slide_renderer() -> SlideRendererClient:
    """Get singleton slide renderer client instance.

    Returns:
        SlideRendererClient instance
    """
    global _client_instance

    if _client_instance is None:
        _client_instance = SlideRendererClient()

    return _client_instance
