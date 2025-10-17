#!/usr/bin/env python3
"""
Copyparty delete webhook for DocuSearch.

This script is called by copyparty when a file is deleted.
It triggers the document cleanup in ChromaDB and filesystem via HTTP.

Environment variables from copyparty:
- fn: filename
- ip: deleter IP
- ap: absolute path to file (may not exist anymore)
- vp: volume path
- src: original filename
"""

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Configuration
WORKER_HOST = os.getenv("WORKER_HOST", "processing-worker")
WORKER_PORT = os.getenv("WORKER_PORT", "8002")

# Load supported formats from environment
_formats_str = os.getenv("SUPPORTED_FORMATS", "pdf,docx,pptx")
SUPPORTED_EXTENSIONS = {f".{fmt.strip().lower()}" for fmt in _formats_str.split(",")}


def trigger_deletion(file_path: str, filename: str) -> bool:
    """
    Trigger document deletion via worker HTTP endpoint.

    Args:
        file_path: Absolute path to deleted file (may not exist anymore)
        filename: Original filename

    Returns:
        True if request succeeded, False otherwise
    """
    # Check if file type is supported
    file_ext = Path(filename).suffix.lower()
    if file_ext not in SUPPORTED_EXTENSIONS:
        print(f"Skipping unsupported file type: {filename}", file=sys.stderr)
        return True  # Not an error, just skip

    # Prepare request
    url = f"http://{WORKER_HOST}:{WORKER_PORT}/delete"
    data = {"file_path": file_path, "filename": filename}

    try:
        # Send POST request to worker
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
            doc_id = result.get("doc_id", "unknown")
            visual_deleted = result.get("visual_deleted", 0)
            text_deleted = result.get("text_deleted", 0)
            page_images_deleted = result.get("page_images_deleted", 0)
            cover_art_deleted = result.get("cover_art_deleted", 0)
            markdown_deleted = result.get("markdown_deleted", False)
            temp_dirs_cleaned = result.get("temp_dirs_cleaned", 0)

            print(f"Deletion completed for {filename} (doc_id: {doc_id[:8]}...)")
            print(f"  ChromaDB: {visual_deleted} visual + {text_deleted} text embeddings")
            print(
                f"  Filesystem: {page_images_deleted} images, {cover_art_deleted} cover art, "
                f"{'1' if markdown_deleted else '0'} markdown, {temp_dirs_cleaned} temp dirs"
            )
            return True

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        print(f"HTTP error triggering deletion: {e.code} {e.reason}", file=sys.stderr)
        print(f"Response: {error_body}", file=sys.stderr)
        return False
    except urllib.error.URLError as e:
        print(f"URL error triggering deletion: {e.reason}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error triggering deletion: {e}", file=sys.stderr)
        return False


def main():
    """Main webhook handler."""
    # Get file info from copyparty environment variables
    filename = os.getenv("fn", "")
    abs_path = os.getenv("ap", "")
    ip_address = os.getenv("ip", "unknown")

    if not filename or not abs_path:
        print("Error: Missing required environment variables (fn, ap)", file=sys.stderr)
        return 1

    print(f"Delete webhook triggered: {filename} from {ip_address}")
    print(f"File path: {abs_path}")

    # Note: File may not exist anymore (already deleted by copyparty)
    # but we still need the path/filename to identify the document in ChromaDB

    # Trigger deletion
    if trigger_deletion(abs_path, filename):
        print(f"Successfully cleaned up {filename} from DocuSearch")
        return 0
    else:
        print(f"Failed to clean up {filename} from DocuSearch", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
