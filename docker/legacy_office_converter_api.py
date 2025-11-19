"""
Legacy Office Converter API - HTTP service for converting legacy Office documents.

This service provides endpoints for:
1. Rendering PowerPoint presentations to PNG images using LibreOffice
2. Converting legacy .doc files to .docx format using LibreOffice

It runs in a Docker container and is called by the native processing worker.
"""

import logging
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================================
# Security Configuration
# ============================================================================
# Allowed base directories for file access (configurable via environment)
ALLOWED_UPLOAD_DIRS = os.getenv("ALLOWED_UPLOAD_DIRS", "/uploads,/data/uploads").split(",")
ALLOWED_EXTENSIONS = {".pptx", ".ppt", ".doc"}


def validate_and_sanitize_path(file_path: str) -> Path:
    """Validate and sanitize file path to prevent path traversal attacks.

    Args:
        file_path: Requested file path

    Returns:
        Validated and resolved Path object

    Raises:
        HTTPException: If path is invalid or outside allowed directories
    """
    try:
        # Convert to Path and resolve (eliminates .. and symlinks)
        requested_path = Path(file_path).resolve()

        # Check if path is within allowed directories
        allowed = False
        for allowed_dir in ALLOWED_UPLOAD_DIRS:
            allowed_base = Path(allowed_dir).resolve()
            try:
                # Check if requested_path is relative to allowed_base
                requested_path.relative_to(allowed_base)
                allowed = True
                break
            except ValueError:
                continue

        if not allowed:
            raise HTTPException(
                status_code=403, detail=f"Access denied: Path outside allowed directories"
            )

        # Validate file extension
        if requested_path.suffix.lower() not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, detail=f"Invalid file type: {requested_path.suffix}"
            )

        # Check file exists
        if not requested_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {requested_path.name}")

        return requested_path

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Path validation error: {e}")
        raise HTTPException(status_code=400, detail="Invalid file path")


app = FastAPI(title="Legacy Office Converter API", version="2.0.0")


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


class ConvertDocRequest(BaseModel):
    """Request to convert .doc file to .docx format.

    Attributes:
        file_path: Path to the .doc file (must be accessible in shared volume)
        output_dir: Directory to save converted .docx file
    """

    file_path: str
    output_dir: str


class ConvertDocResponse(BaseModel):
    """Response from doc to docx conversion.

    Attributes:
        success: Whether conversion succeeded
        docx_path: Path to converted .docx file (null on error)
        file_size_bytes: Size of converted file in bytes (null on error)
        conversion_time_ms: Time taken for conversion in milliseconds
        error: Error message if conversion failed
    """

    success: bool
    docx_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    conversion_time_ms: Optional[int] = None
    error: Optional[str] = None


def render_slides_with_libreoffice(
    pptx_path: str, output_dir: str, dpi: int = 150
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
    # Validate and sanitize paths
    pptx_path = validate_and_sanitize_path(pptx_path)
    output_dir = Path(output_dir)

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
                    "libreoffice",
                    "--headless",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    str(temp_path),
                    str(pptx_path),
                ],
                capture_output=True,
                text=True,
                timeout=60,
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
                ["pdftoppm", "-png", "-r", str(dpi), str(pdf_path), str(temp_path / "slide")],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                # Fallback: try using ImageMagick convert
                logger.warning("pdftoppm failed, trying ImageMagick...")
                result = subprocess.run(
                    [
                        "convert",
                        "-density",
                        str(dpi),
                        str(pdf_path),
                        str(temp_path / "slide-%03d.png"),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                if result.returncode != 0:
                    error_msg = f"Image conversion failed: {result.stderr}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)

            # Find all generated PNG files
            slide_files = sorted(temp_path.glob("slide-*.png"))

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
                "success": True,
                "slide_count": len(slide_paths),
                "slide_paths": slide_paths,
                "error": None,
            }

        except subprocess.TimeoutExpired:
            error_msg = "Rendering timeout (60s exceeded)"
            logger.error(error_msg)
            return {"success": False, "slide_count": 0, "slide_paths": [], "error": error_msg}
        except Exception as e:
            error_msg = f"Rendering error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"success": False, "slide_count": 0, "slide_paths": [], "error": error_msg}


def convert_doc_to_docx(doc_path: str, output_dir: str) -> Dict[str, Any]:
    """Convert .doc to .docx using LibreOffice.

    Args:
        doc_path: Path to .doc file
        output_dir: Directory for output

    Returns:
        Dictionary with success status, docx path, file size, and conversion time
        {
            "success": bool,
            "docx_path": str or None,
            "file_size_bytes": int or None,
            "conversion_time_ms": int or None,
            "error": str or None
        }

    Raises:
        HTTPException: If path validation fails
    """
    start_time = time.time()

    try:
        # Validate and sanitize path
        doc_path = validate_and_sanitize_path(doc_path)
        output_dir = Path(output_dir)

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Determine expected output path
        docx_filename = doc_path.stem + ".docx"
        expected_docx_path = output_dir / docx_filename

        logger.info(f"Converting {doc_path} to {expected_docx_path}...")

        # Run LibreOffice conversion
        # Command: libreoffice --headless --convert-to docx --outdir {output_dir} {doc_path}
        result = subprocess.run(
            [
                "libreoffice",
                "--headless",
                "--convert-to",
                "docx",
                "--outdir",
                str(output_dir),
                str(doc_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,  # 30s timeout as per contract
        )

        conversion_time_ms = int((time.time() - start_time) * 1000)

        # Check if conversion succeeded
        if result.returncode != 0:
            error_msg = f"LibreOffice conversion failed: {result.stderr or result.stdout}"
            logger.error(error_msg)
            logger.error(f"Exit code: {result.returncode}")
            return {
                "success": False,
                "docx_path": None,
                "file_size_bytes": None,
                "conversion_time_ms": conversion_time_ms,
                "error": error_msg,
            }

        # Verify output file exists
        if not expected_docx_path.exists():
            error_msg = f"Conversion appeared to succeed but output file not found: {expected_docx_path}"
            logger.error(error_msg)
            return {
                "success": False,
                "docx_path": None,
                "file_size_bytes": None,
                "conversion_time_ms": conversion_time_ms,
                "error": error_msg,
            }

        # Get file size
        file_size = expected_docx_path.stat().st_size

        # Verify file is not empty
        if file_size == 0:
            error_msg = "Conversion produced empty file"
            logger.error(error_msg)
            return {
                "success": False,
                "docx_path": None,
                "file_size_bytes": None,
                "conversion_time_ms": conversion_time_ms,
                "error": error_msg,
            }

        logger.info(
            f"Successfully converted {doc_path.name} to {docx_filename} ({file_size} bytes) in {conversion_time_ms}ms"
        )

        return {
            "success": True,
            "docx_path": str(expected_docx_path),
            "file_size_bytes": file_size,
            "conversion_time_ms": conversion_time_ms,
            "error": None,
        }

    except subprocess.TimeoutExpired:
        conversion_time_ms = int((time.time() - start_time) * 1000)
        error_msg = "Conversion timeout exceeded (30s)"
        logger.error(error_msg)
        return {
            "success": False,
            "docx_path": None,
            "file_size_bytes": None,
            "conversion_time_ms": conversion_time_ms,
            "error": error_msg,
        }
    except HTTPException:
        # Re-raise validation errors
        raise
    except Exception as e:
        conversion_time_ms = int((time.time() - start_time) * 1000)
        error_msg = f"Conversion error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "docx_path": None,
            "file_size_bytes": None,
            "conversion_time_ms": conversion_time_ms,
            "error": error_msg,
        }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "legacy-office-converter",
        "capabilities": ["pptx-rendering", "doc-conversion"],
    }


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
            pptx_path=request.file_path, output_dir=request.output_dir, dpi=request.dpi
        )

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])

        return RenderResponse(**result)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Rendering error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/convert-doc", response_model=ConvertDocResponse)
async def convert_doc(request: ConvertDocRequest):
    """Convert .doc file to .docx format.

    Args:
        request: ConvertDocRequest with file_path and output_dir

    Returns:
        ConvertDocResponse with success status, docx path, file size, and conversion time

    Raises:
        HTTPException: If conversion fails or validation errors occur
    """
    logger.info(f"Converting .doc file: {request.file_path}")

    try:
        result = convert_doc_to_docx(doc_path=request.file_path, output_dir=request.output_dir)

        # If conversion failed, return appropriate HTTP error
        if not result["success"]:
            # Determine appropriate status code based on error
            error = result.get("error", "Unknown error")
            if "not found" in error.lower():
                status_code = 404
            elif "timeout" in error.lower():
                status_code = 500
            elif "corrupted" in error.lower() or "invalid" in error.lower():
                status_code = 400
            else:
                status_code = 500

            raise HTTPException(status_code=status_code, detail=error)

        return ConvertDocResponse(**result)

    except HTTPException:
        # Re-raise HTTP exceptions (from validation or our own error handling)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in convert_doc endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "Legacy Office Converter API",
        "version": "2.0.0",
        "capabilities": ["pptx-rendering", "doc-conversion"],
        "endpoints": {
            "health": "GET /health",
            "render_pptx": "POST /render",
            "convert_doc": "POST /convert-doc",
        },
    }
