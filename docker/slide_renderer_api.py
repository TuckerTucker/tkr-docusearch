"""
Slide Renderer API - HTTP service for converting PPTX slides to images.

This service provides an endpoint for rendering PowerPoint presentations
to PNG images using LibreOffice. It runs in a Docker container and is
called by the native processing worker.
"""

import os
import shutil
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Slide Renderer API", version="1.0.0")


class RenderRequest(BaseModel):
    """Request to render slides from a PPTX file.

    Attributes:
        file_path: Path to the PPTX file (must be accessible in shared volume)
        output_dir: Directory to save rendered slide images
        dpi: Resolution for rendered images (default: 150)
    """
    file_path: str
    output_dir: str
    dpi: int = 150


class RenderResponse(BaseModel):
    """Response from slide rendering.

    Attributes:
        success: Whether rendering succeeded
        slide_count: Number of slides rendered
        slide_paths: List of paths to rendered slide images
        error: Error message if rendering failed
    """
    success: bool
    slide_count: int
    slide_paths: List[str]
    error: Optional[str] = None


def render_slides_with_libreoffice(
    pptx_path: str,
    output_dir: str,
    dpi: int = 150
) -> Dict[str, Any]:
    """Render PPTX slides to PNG images using LibreOffice.

    Args:
        pptx_path: Path to PPTX file
        output_dir: Directory to save rendered images
        dpi: Resolution for rendering (default: 150)

    Returns:
        Dictionary with success status, slide paths, and error message

    Raises:
        FileNotFoundError: If PPTX file doesn't exist
        RuntimeError: If LibreOffice conversion fails
    """
    pptx_path = Path(pptx_path)
    output_dir = Path(output_dir)

    # Validate input file
    if not pptx_path.exists():
        raise FileNotFoundError(f"PPTX file not found: {pptx_path}")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create temporary directory for LibreOffice output
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        try:
            # Convert PPTX to PDF first (LibreOffice does this reliably)
            logger.info(f"Converting {pptx_path.name} to PDF...")
            pdf_path = temp_path / f"{pptx_path.stem}.pdf"

            result = subprocess.run(
                [
                    'libreoffice',
                    '--headless',
                    '--convert-to', 'pdf',
                    '--outdir', str(temp_path),
                    str(pptx_path)
                ],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                error_msg = f"LibreOffice conversion failed: {result.stderr}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)

            if not pdf_path.exists():
                raise RuntimeError("PDF conversion produced no output")

            # Convert PDF to PNG images (one per slide)
            logger.info(f"Rendering PDF to PNG images at {dpi} DPI...")

            # Use pdftoppm for high-quality rendering
            result = subprocess.run(
                [
                    'pdftoppm',
                    '-png',
                    '-r', str(dpi),
                    str(pdf_path),
                    str(temp_path / 'slide')
                ],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                # Fallback: try using ImageMagick convert
                logger.warning("pdftoppm failed, trying ImageMagick...")
                result = subprocess.run(
                    [
                        'convert',
                        '-density', str(dpi),
                        str(pdf_path),
                        str(temp_path / 'slide-%03d.png')
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode != 0:
                    error_msg = f"Image conversion failed: {result.stderr}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)

            # Find all generated PNG files
            slide_files = sorted(temp_path.glob('slide-*.png'))

            if not slide_files:
                raise RuntimeError("No slide images were generated")

            # Move slides to output directory with proper naming
            slide_paths = []
            for i, slide_file in enumerate(slide_files, start=1):
                output_path = output_dir / f"page{i:03d}.png"
                shutil.copy2(slide_file, output_path)
                slide_paths.append(str(output_path))
                logger.info(f"Saved slide {i} to {output_path}")

            logger.info(f"Successfully rendered {len(slide_paths)} slides")

            return {
                'success': True,
                'slide_count': len(slide_paths),
                'slide_paths': slide_paths,
                'error': None
            }

        except subprocess.TimeoutExpired:
            error_msg = "Rendering timeout (60s exceeded)"
            logger.error(error_msg)
            return {
                'success': False,
                'slide_count': 0,
                'slide_paths': [],
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Rendering error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'slide_count': 0,
                'slide_paths': [],
                'error': error_msg
            }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "slide-renderer"}


@app.post("/render", response_model=RenderResponse)
async def render_slides(request: RenderRequest):
    """Render PPTX slides to PNG images.

    Args:
        request: RenderRequest with file_path, output_dir, and optional dpi

    Returns:
        RenderResponse with success status and slide paths

    Raises:
        HTTPException: If rendering fails
    """
    logger.info(f"Rendering slides from {request.file_path}")

    try:
        result = render_slides_with_libreoffice(
            pptx_path=request.file_path,
            output_dir=request.output_dir,
            dpi=request.dpi
        )

        if not result['success']:
            raise HTTPException(status_code=500, detail=result['error'])

        return RenderResponse(**result)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Rendering error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "Slide Renderer API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "render": "POST /render"
        }
    }
