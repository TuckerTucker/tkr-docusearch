"""
PPTX slide rendering helper.

This module handles rendering PowerPoint slides to images via the
slide-renderer service, extracted from DoclingParser for reduced complexity.
"""

import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class SlideRenderer:
    """Helper for rendering PPTX slides to images."""

    def __init__(self, render_dpi: int = 150):
        """
        Initialize slide renderer.

        Args:
            render_dpi: DPI for slide rendering
        """
        self.render_dpi = render_dpi

    def render_pptx_slides(self, file_path: str) -> Optional[List]:
        """
        Render PPTX slides to images via slide-renderer service.

        Args:
            file_path: Path to PPTX file

        Returns:
            List of PIL Images (one per slide), or None if rendering fails
        """
        try:
            import shutil

            from PIL import Image as PILImage

            from src.processing.legacy_office_client import get_legacy_office_client

            logger.info(f"Rendering PPTX slides to images via slide-renderer service")

            # Convert file path from native worker's perspective to Docker container's mount
            # Native: /Volumes/.../data/uploads/file.pptx -> Docker: /uploads/file.pptx
            pptx_filename = Path(file_path).name
            docker_pptx_path = f"/uploads/{pptx_filename}"

            logger.debug(f"Path translation: {file_path} -> {docker_pptx_path}")

            # Create temporary output directory in shared volume
            # Both Docker and native worker can access /page_images mount
            temp_subdir = f"temp-slides-{Path(file_path).stem}"
            native_temp_dir = Path("data/page_images").resolve() / temp_subdir
            docker_temp_dir = f"/page_images/{temp_subdir}"

            logger.debug(f"Creating temp directory: {native_temp_dir}")
            native_temp_dir.mkdir(parents=True, exist_ok=True)

            try:
                slide_client = get_legacy_office_client()

                # Render slides to shared volume
                slide_paths = slide_client.render_slides(
                    pptx_path=docker_pptx_path, output_dir=docker_temp_dir, dpi=self.render_dpi
                )

                logger.info(f"Slides rendered to shared volume: {native_temp_dir}")

                # Load rendered images from native path
                rendered_slide_images = []
                for docker_path in slide_paths:
                    # Convert Docker path back to native path
                    filename = Path(docker_path).name
                    native_path = native_temp_dir / filename

                    img = PILImage.open(native_path)
                    # Convert to RGB if needed (remove alpha channel)
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    rendered_slide_images.append(img.copy())
                    img.close()

                logger.info(f"Loaded {len(rendered_slide_images)} rendered slide images")
                return rendered_slide_images

            finally:
                # Clean up temporary directory
                if native_temp_dir.exists():
                    shutil.rmtree(native_temp_dir)
                    logger.debug(f"Cleaned up temp slides directory: {native_temp_dir}")

        except Exception as e:
            logger.error(f"Failed to render PPTX slides: {e}")
            logger.warning("PPTX will be processed as text-only without slide images")
            return None
