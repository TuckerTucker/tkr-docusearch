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


def verify_chromadb_connection(host: str = "localhost", port: int = 8001) -> bool:
    """
    Verify ChromaDB is accessible.

    Args:
        host: ChromaDB host
        port: ChromaDB port

    Returns:
        True if ChromaDB is accessible, False otherwise
    """
    try:
        response = httpx.get(f"http://{host}:{port}/api/v1/heartbeat", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


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


def cleanup_test_documents(chromadb_client, doc_ids: list[str], verbose: bool = False) -> dict:
    """
    Clean up test documents from ChromaDB.

    Args:
        chromadb_client: ChromaDB client instance
        doc_ids: List of document IDs to remove
        verbose: Print cleanup progress

    Returns:
        Dict with cleanup statistics:
        - visual_deleted: Number of visual embeddings deleted
        - text_deleted: Number of text embeddings deleted
        - errors: List of errors encountered
    """
    stats = {"visual_deleted": 0, "text_deleted": 0, "errors": []}

    for doc_id in doc_ids:
        try:
            # Delete from visual collection
            visual_results = chromadb_client._visual_collection.get(where={"doc_id": doc_id})
            if visual_results["ids"]:
                chromadb_client._visual_collection.delete(where={"doc_id": doc_id})
                stats["visual_deleted"] += len(visual_results["ids"])
                if verbose:
                    print(f"Deleted {len(visual_results['ids'])} visual embeddings for {doc_id}")

            # Delete from text collection
            text_results = chromadb_client._text_collection.get(where={"doc_id": doc_id})
            if text_results["ids"]:
                chromadb_client._text_collection.delete(where={"doc_id": doc_id})
                stats["text_deleted"] += len(text_results["ids"])
                if verbose:
                    print(f"Deleted {len(text_results['ids'])} text embeddings for {doc_id}")

        except Exception as e:
            error_msg = f"Error cleaning up {doc_id}: {str(e)}"
            stats["errors"].append(error_msg)
            if verbose:
                print(error_msg)

    return stats


def get_document_stats(chromadb_client, doc_id: str) -> dict:
    """
    Get statistics for a document in ChromaDB.

    Args:
        chromadb_client: ChromaDB client instance
        doc_id: Document ID

    Returns:
        Dict with stats:
        - visual_embeddings: Number of visual embeddings
        - text_embeddings: Number of text embeddings
        - has_structure: Whether document has structure metadata
        - pages: List of page numbers
    """
    # Query visual collection
    visual_results = chromadb_client._visual_collection.get(
        where={"doc_id": doc_id}, include=["metadatas"]
    )

    # Query text collection
    text_results = chromadb_client._text_collection.get(
        where={"doc_id": doc_id}, include=["metadatas"]
    )

    # Check for structure
    has_structure = False
    if visual_results["metadatas"]:
        has_structure = any(m.get("has_structure", False) for m in visual_results["metadatas"])

    # Get pages
    pages = set()
    for metadata in visual_results["metadatas"]:
        if "page" in metadata:
            pages.add(metadata["page"])
    for metadata in text_results["metadatas"]:
        if "page" in metadata:
            pages.add(metadata["page"])

    return {
        "visual_embeddings": len(visual_results["ids"]),
        "text_embeddings": len(text_results["ids"]),
        "has_structure": has_structure,
        "pages": sorted(list(pages)),
    }
