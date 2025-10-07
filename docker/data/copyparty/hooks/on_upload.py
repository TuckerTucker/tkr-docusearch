#!/usr/bin/env python3
"""
Copyparty upload webhook for DocuSearch.

This script is called by copyparty when a file is uploaded.
It triggers the document processing worker via HTTP.

Environment variables from copyparty:
- fn: filename
- ip: uploader IP
- ap: absolute path to file
- vp: volume path
- src: original filename
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

# Configuration
WORKER_HOST = os.getenv("WORKER_HOST", "processing-worker")
WORKER_PORT = os.getenv("WORKER_PORT", "8002")
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx"}


def trigger_processing(file_path: str, filename: str) -> bool:
    """
    Trigger document processing via worker HTTP endpoint.

    Args:
        file_path: Absolute path to uploaded file
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
    url = f"http://{WORKER_HOST}:{WORKER_PORT}/process"
    data = {
        "file_path": file_path,
        "filename": filename
    }

    try:
        # Send POST request to worker
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"Processing triggered: {result.get('message', 'OK')}")
            return True

    except urllib.error.HTTPError as e:
        print(f"HTTP error triggering processing: {e.code} {e.reason}", file=sys.stderr)
        return False
    except urllib.error.URLError as e:
        print(f"URL error triggering processing: {e.reason}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error triggering processing: {e}", file=sys.stderr)
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

    print(f"Upload webhook triggered: {filename} from {ip_address}")
    print(f"File path: {abs_path}")

    # Verify file exists
    if not os.path.exists(abs_path):
        print(f"Error: File not found: {abs_path}", file=sys.stderr)
        return 1

    # Trigger processing
    if trigger_processing(abs_path, filename):
        print(f"Successfully queued {filename} for processing")
        return 0
    else:
        print(f"Failed to queue {filename} for processing", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
