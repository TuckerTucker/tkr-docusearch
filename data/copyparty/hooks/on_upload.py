#!/usr/bin/env python3
"""
DocuSearch - Copyparty Upload Event Hook
Wave 2: Basic event hook for upload notifications

This hook is triggered by copyparty when files are uploaded.
In Wave 3, this will trigger document processing pipeline.

Event Hook Documentation:
https://github.com/9001/copyparty/blob/hovudstraum/docs/hooks.md

Arguments provided by copyparty:
    sys.argv[1]: Event type (up, del, mv, etc.)
    sys.argv[2]: Virtual filesystem path
    sys.argv[3]: Physical filesystem path
    sys.argv[4]: Username
    sys.argv[5]: IP address

Environment variables:
    CPY_ROOT: Virtual filesystem root
    CPY_ABS: Absolute path to file
"""

import sys
import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ============================================================================
# Configuration
# ============================================================================

# Supported document types for processing
SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.pptx'}

# Log file location
LOG_DIR = Path(__file__).parent.parent / 'logs'
LOG_FILE = LOG_DIR / 'upload_events.log'

# Queue file for processing (Wave 3)
QUEUE_DIR = Path(__file__).parent.parent / 'queue'
QUEUE_FILE = QUEUE_DIR / 'processing_queue.json'

# ============================================================================
# Logging Setup
# ============================================================================

def setup_logging() -> logging.Logger:
    """Configure logging for upload events."""
    LOG_DIR.mkdir(exist_ok=True)

    logger = logging.getLogger('docusearch.upload_hook')
    logger.setLevel(logging.INFO)

    # File handler
    handler = logging.FileHandler(LOG_FILE)
    handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger

logger = setup_logging()

# ============================================================================
# Queue Management (Wave 3 preparation)
# ============================================================================

def load_queue() -> list:
    """Load processing queue from JSON file."""
    if not QUEUE_FILE.exists():
        return []

    try:
        with open(QUEUE_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load queue: {e}")
        return []

def save_queue(queue: list) -> None:
    """Save processing queue to JSON file."""
    QUEUE_DIR.mkdir(exist_ok=True)

    try:
        with open(QUEUE_FILE, 'w') as f:
            json.dump(queue, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save queue: {e}")

def add_to_queue(file_info: dict) -> None:
    """Add file to processing queue."""
    queue = load_queue()
    queue.append(file_info)
    save_queue(queue)
    logger.info(f"Added to queue: {file_info['filename']}")

# ============================================================================
# Event Handling
# ============================================================================

def is_supported_document(filepath: str) -> bool:
    """Check if file is a supported document type."""
    return Path(filepath).suffix.lower() in SUPPORTED_EXTENSIONS

def get_file_info(vfs_path: str, abs_path: str, username: str, ip_address: str) -> dict:
    """Extract file information for processing."""
    file_path = Path(abs_path)

    return {
        'doc_id': None,  # Will be assigned by processing-agent
        'filename': file_path.name,
        'vfs_path': vfs_path,
        'abs_path': abs_path,
        'file_size_bytes': file_path.stat().st_size if file_path.exists() else 0,
        'file_size_mb': round(file_path.stat().st_size / (1024 * 1024), 2) if file_path.exists() else 0,
        'extension': file_path.suffix.lower(),
        'upload_timestamp': datetime.now(timezone.utc).isoformat(),
        'uploaded_by': username,
        'upload_ip': ip_address,
        'status': 'queued',
        'processing_started': None,
        'processing_completed': None,
        'error': None
    }

def handle_upload(vfs_path: str, abs_path: str, username: str, ip_address: str) -> None:
    """Handle file upload event."""
    logger.info(f"Upload event: {vfs_path} by {username} from {ip_address}")

    # Check if supported document
    if not is_supported_document(abs_path):
        logger.info(f"Skipping unsupported file type: {abs_path}")
        return

    # Get file information
    file_info = get_file_info(vfs_path, abs_path, username, ip_address)

    logger.info(
        f"Processing document: {file_info['filename']} "
        f"({file_info['file_size_mb']} MB)"
    )

    # Wave 2: Just log the event
    logger.info(f"[Wave 2] Document logged for future processing: {file_info['filename']}")

    # Wave 3: Add to processing queue
    # Uncomment when processing-agent is implemented
    # add_to_queue(file_info)
    # trigger_processing()  # Trigger background processing

    print(f"✓ Logged upload: {file_info['filename']}")

def handle_delete(vfs_path: str, abs_path: str, username: str, ip_address: str) -> None:
    """Handle file deletion event."""
    logger.info(f"Delete event: {vfs_path} by {username} from {ip_address}")

    # Wave 3: Remove from index and embeddings
    # For now, just log
    logger.info(f"[Wave 2] Document deletion logged: {Path(abs_path).name}")

    print(f"✓ Logged deletion: {Path(abs_path).name}")

def handle_move(vfs_path: str, abs_path: str, username: str, ip_address: str) -> None:
    """Handle file move/rename event."""
    logger.info(f"Move event: {vfs_path} by {username} from {ip_address}")

    # Wave 3: Update index with new path
    logger.info(f"[Wave 2] Document move logged: {Path(abs_path).name}")

    print(f"✓ Logged move: {Path(abs_path).name}")

# ============================================================================
# Main Entry Point
# ============================================================================

def main() -> int:
    """Main event hook entry point."""
    try:
        # Parse arguments from copyparty
        if len(sys.argv) < 6:
            logger.error(f"Insufficient arguments: {sys.argv}")
            print("Error: Insufficient arguments", file=sys.stderr)
            return 1

        event_type = sys.argv[1]
        vfs_path = sys.argv[2]
        abs_path = sys.argv[3]
        username = sys.argv[4]
        ip_address = sys.argv[5]

        logger.info(f"Hook invoked: event={event_type}, vfs={vfs_path}")

        # Handle different event types
        if event_type == 'up':
            handle_upload(vfs_path, abs_path, username, ip_address)
        elif event_type == 'del':
            handle_delete(vfs_path, abs_path, username, ip_address)
        elif event_type == 'mv':
            handle_move(vfs_path, abs_path, username, ip_address)
        else:
            logger.info(f"Unhandled event type: {event_type}")

        return 0

    except Exception as e:
        logger.error(f"Hook error: {e}", exc_info=True)
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
