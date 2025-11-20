#!/usr/bin/env python3
"""
DocuSearch - Copyparty Upload Event Hook
Triggers processing worker via HTTP webhook

Simplified version for --xau flag which only provides file path.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

# ============================================================================
# Configuration
# ============================================================================

# Supported document types for processing (must match file_validator.py defaults)
_formats_str = os.environ.get(
    "SUPPORTED_FORMATS",
    "pdf,docx,pptx,xlsx,html,xhtml,md,asciidoc,csv,mp3,wav,vtt,png,jpg,jpeg,tiff,bmp,webp",
)
SUPPORTED_EXTENSIONS = {f".{fmt.strip().lower()}" for fmt in _formats_str.split(",")}

# Worker endpoint
WORKER_HOST = os.environ.get("WORKER_HOST", "host.docker.internal")
WORKER_PORT = os.environ.get("WORKER_PORT", "8002")

# Path translation: container path -> host path
# For native worker (GPU mode): translate container /uploads to host path
# For Docker worker (CPU mode): no translation needed (both use /uploads)
CONTAINER_UPLOADS_PATH = "/uploads"
HOST_UPLOADS_PATH = os.environ.get(
    "HOST_UPLOADS_PATH", "/Volumes/tkr-riffic/@tkr-projects/tkr-docusearch/data/uploads"
)

# ============================================================================
# Main
# ============================================================================


def main():
    """Main entry point for --xau hook."""
    try:
        # --xau only provides file path as single argument
        if len(sys.argv) < 2:
            print(f"Error: No file path provided", file=sys.stderr)
            print(f"Received: {sys.argv}", file=sys.stderr)
            return 1

        container_path = sys.argv[1]
        filename = Path(container_path).name

        # Check if supported document
        if Path(container_path).suffix.lower() not in SUPPORTED_EXTENSIONS:
            print(f"ℹ Skipping unsupported file type: {filename}")
            return 0

        print(f"📄 New document uploaded: {filename}")
        print(f"   Container path: {container_path}")

        # Translate container path to host path for native worker
        # Native worker (GPU mode) needs full host path
        # Docker worker (CPU mode) uses container path
        if container_path.startswith(CONTAINER_UPLOADS_PATH):
            # Replace container path with host path
            relative_path = container_path[len(CONTAINER_UPLOADS_PATH) :].lstrip("/")
            host_path = os.path.join(HOST_UPLOADS_PATH, relative_path)
        else:
            # Already a host path
            host_path = container_path

        print(f"   Host path: {host_path}")

        # Trigger processing with host path
        url = f"http://{WORKER_HOST}:{WORKER_PORT}/process"
        data = {"file_path": host_path, "filename": filename}

        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode("utf-8"))
            print(f"✓ Processing queued: {filename}")
            print(f"  Response: {result.get('message', 'OK')}")
            return 0

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else "No error body"
        print(f"✗ HTTP Error {e.code}: {error_body}", file=sys.stderr)
        return 1

    except urllib.error.URLError as e:
        print(f"✗ Connection Error: {e.reason}", file=sys.stderr)
        print(f"  Worker URL: {url}", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"✗ Hook error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
