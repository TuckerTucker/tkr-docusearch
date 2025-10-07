#!/usr/bin/env python3
"""
DocuSearch - Copyparty Upload Event Hook
Triggers processing worker via HTTP webhook

Event Hook Documentation:
https://github.com/9001/copyparty/blob/hovudstraum/docs/hooks.md

Arguments provided by copyparty:
    sys.argv[1]: Event type (up, del, mv, etc.)
    sys.argv[2]: Virtual filesystem path
    sys.argv[3]: Physical filesystem path
    sys.argv[4]: Username
    sys.argv[5]: IP address
"""

import sys
import os
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

# ============================================================================
# Configuration
# ============================================================================

# Supported document types for processing
SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.pptx'}

# Worker endpoint
WORKER_HOST = os.environ.get('WORKER_HOST', 'processing-worker')
WORKER_PORT = os.environ.get('WORKER_PORT', '8002')

# ============================================================================
# Worker Communication
# ============================================================================

def trigger_processing(file_path: str, filename: str) -> bool:
    """
    Trigger processing worker via HTTP POST.

    Args:
        file_path: Physical path to the file
        filename: Name of the file

    Returns:
        True if successfully queued, False otherwise
    """
    url = f"http://{WORKER_HOST}:{WORKER_PORT}/process"

    data = {
        "file_path": file_path,
        "filename": filename
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"✓ Processing queued: {filename}")
            print(f"  Response: {result.get('message', 'OK')}")
            return True

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else 'No error body'
        print(f"✗ HTTP Error {e.code}: {error_body}", file=sys.stderr)
        return False

    except urllib.error.URLError as e:
        print(f"✗ Connection Error: {e.reason}", file=sys.stderr)
        print(f"  Worker URL: {url}", file=sys.stderr)
        return False

    except Exception as e:
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        return False

# ============================================================================
# Event Handling
# ============================================================================

def is_supported_document(filepath: str) -> bool:
    """Check if file is a supported document type."""
    return Path(filepath).suffix.lower() in SUPPORTED_EXTENSIONS

def handle_upload(vfs_path: str, abs_path: str, username: str, ip_address: str) -> None:
    """Handle file upload event."""
    # Check if supported document
    if not is_supported_document(abs_path):
        print(f"ℹ Skipping unsupported file type: {Path(abs_path).name}")
        return

    filename = Path(abs_path).name
    print(f"📄 New document uploaded: {filename}")
    print(f"   Path: {abs_path}")
    print(f"   User: {username} from {ip_address}")

    # Trigger processing
    success = trigger_processing(abs_path, filename)

    if not success:
        print(f"⚠ Warning: Failed to queue {filename} for processing", file=sys.stderr)

def handle_delete(vfs_path: str, abs_path: str, username: str, ip_address: str) -> None:
    """Handle file deletion event."""
    print(f"🗑 Delete event: {Path(abs_path).name}")
    # Future: Remove from ChromaDB

def handle_move(vfs_path: str, abs_path: str, username: str, ip_address: str) -> None:
    """Handle file move/rename event."""
    print(f"📦 Move event: {Path(abs_path).name}")
    # Future: Update paths in ChromaDB

# ============================================================================
# Main Entry Point
# ============================================================================

def main() -> int:
    """Main event hook entry point."""
    try:
        # Parse arguments from copyparty
        if len(sys.argv) < 6:
            print(f"Error: Insufficient arguments", file=sys.stderr)
            print(f"Received: {sys.argv}", file=sys.stderr)
            print(f"Expected: <event> <vfs_path> <abs_path> <username> <ip>", file=sys.stderr)
            return 1

        event_type = sys.argv[1]
        vfs_path = sys.argv[2]
        abs_path = sys.argv[3]
        username = sys.argv[4]
        ip_address = sys.argv[5]

        # Handle different event types
        if event_type == 'up':
            handle_upload(vfs_path, abs_path, username, ip_address)
        elif event_type == 'del':
            handle_delete(vfs_path, abs_path, username, ip_address)
        elif event_type == 'mv':
            handle_move(vfs_path, abs_path, username, ip_address)
        else:
            print(f"ℹ Unhandled event type: {event_type}")

        return 0

    except Exception as e:
        print(f"✗ Hook error: {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
