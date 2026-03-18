"""
Helper utilities for E2E tests.

Provides common functions for:
- Document upload simulation
- Processing status monitoring
- Test data generation
- Cleanup utilities
"""

import hashlib
import time
from pathlib import Path

import httpx


def generate_doc_id(filename: str) -> str:
    """
    Generate document ID from filename (matches production logic).

    Args:
        filename: Document filename

    Returns:
        Document ID (first 12 chars of SHA-256 hash)
    """
    hash_obj = hashlib.sha256(filename.encode("utf-8"))
    return hash_obj.hexdigest()[:12]


def wait_for_document_processing(
    client: httpx.Client,
    doc_id: str,
    timeout: int = 60,
    poll_interval: float = 1.0,
) -> dict:
    """
    Wait for document processing to complete and return final status.

    Args:
        client: HTTP client for Worker API
        doc_id: Document ID to monitor
        timeout: Maximum seconds to wait
        poll_interval: Seconds between status checks

    Returns:
        Final status dict with keys:
        - status: "completed" | "failed" | "timeout"
        - error: Error message if failed
        - duration: Processing time in seconds

    Raises:
        TimeoutError: If processing exceeds timeout
    """
    start_time = time.time()
    last_status = None

    while time.time() - start_time < timeout:
        try:
            response = client.get(f"/status/document/{doc_id}")

            if response.status_code == 200:
                status_data = response.json()
                last_status = status_data
                status = status_data.get("status")

                if status == "completed":
                    return {
                        "status": "completed",
                        "duration": time.time() - start_time,
                        "data": status_data,
                    }
                elif status == "failed":
                    return {
                        "status": "failed",
                        "error": status_data.get("error"),
                        "duration": time.time() - start_time,
                        "data": status_data,
                    }

            elif response.status_code == 404:
                # Document not found yet - processing may not have started
                pass

        except Exception as e:
            print(f"Error polling status: {e}")

        time.sleep(poll_interval)

    # Timeout
    return {
        "status": "timeout",
        "error": f"Processing exceeded {timeout}s timeout",
        "duration": timeout,
        "data": last_status,
    }


def create_test_pdf(output_path: Path, content: str = "Test PDF content") -> Path:
    """
    Create a simple test PDF file.

    Args:
        output_path: Path where PDF should be created
        content: Text content to include

    Returns:
        Path to created PDF

    Note: Requires reportlab package
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        c = canvas.Canvas(str(output_path), pagesize=letter)
        c.drawString(100, 750, content)
        c.showPage()
        c.save()

        return output_path
    except ImportError:
        raise ImportError(
            "reportlab required for PDF generation. Install with: pip install reportlab"
        )


def create_test_pdf_with_structure(
    output_path: Path,
    num_pages: int = 3,
    num_headings: int = 5,
    num_tables: int = 2,
) -> Path:
    """
    Create a test PDF with structure (headings, tables).

    Args:
        output_path: Path where PDF should be created
        num_pages: Number of pages
        num_headings: Number of headings
        num_tables: Number of tables

    Returns:
        Path to created PDF

    Note: Requires reportlab package
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table

        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Add headings
        for i in range(num_headings):
            story.append(Paragraph(f"Section {i+1}: Test Heading", styles["Heading1"]))
            story.append(Spacer(1, 12))
            story.append(
                Paragraph(
                    f"This is test content for section {i+1}. "
                    "It contains multiple sentences to create realistic chunks. "
                    "The content is designed to test structure extraction and "
                    "bidirectional highlighting features.",
                    styles["Normal"],
                )
            )
            story.append(Spacer(1, 12))

        # Add tables
        for i in range(num_tables):
            table_data = [
                ["Header 1", "Header 2", "Header 3"],
                [f"Row {j} Col 1" for j in range(1, 4)],
                [f"Row {j} Col 2" for j in range(1, 4)],
            ]
            t = Table(table_data)
            story.append(Paragraph(f"Table {i+1}: Test Data", styles["Heading2"]))
            story.append(Spacer(1, 6))
            story.append(t)
            story.append(Spacer(1, 12))

        doc.build(story)
        return output_path

    except ImportError:
        raise ImportError(
            "reportlab required for PDF generation. Install with: pip install reportlab"
        )


def verify_worker_api_connection(url: str = "http://localhost:8002") -> bool:
    """
    Verify Worker API is accessible.

    Args:
        url: Worker API base URL

    Returns:
        True if Worker API is accessible, False otherwise
    """
    try:
        response = httpx.get(f"{url}/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


