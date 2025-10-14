#!/usr/bin/env python3
"""
Cleanup orphaned documents.

Removes documents from ChromaDB and filesystem that no longer have
source files in the uploads directory.

Usage:
    python scripts/cleanup_orphaned_docs.py [--dry-run]
"""

import sys
import argparse
import requests
from pathlib import Path

WORKER_URL = "http://localhost:8002"
UPLOADS_DIR = Path("data/uploads")


def get_all_documents():
    """Get all documents from ChromaDB via API."""
    response = requests.get(f"{WORKER_URL}/documents")
    response.raise_for_status()
    data = response.json()
    return data["documents"]


def file_exists_in_uploads(filename):
    """Check if file exists in uploads directory."""
    file_path = UPLOADS_DIR / filename
    return file_path.exists()


def delete_document(filename, file_path):
    """Delete document via worker API."""
    payload = {
        "filename": filename,
        "file_path": file_path
    }
    response = requests.post(f"{WORKER_URL}/delete", json=payload)
    response.raise_for_status()
    return response.json()


def main():
    parser = argparse.ArgumentParser(description="Cleanup orphaned documents")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without deleting")
    args = parser.parse_args()

    print("=" * 70)
    print("Orphaned Document Cleanup")
    print("=" * 70)
    print()

    # Get all documents from ChromaDB
    print("Fetching documents from ChromaDB...")
    try:
        documents = get_all_documents()
        print(f"Found {len(documents)} documents in ChromaDB")
    except Exception as e:
        print(f"Error fetching documents: {e}")
        return 1

    print()

    # Check which ones are orphaned
    orphaned = []
    for doc in documents:
        filename = doc["filename"]
        doc_id = doc["doc_id"]

        if not file_exists_in_uploads(filename):
            orphaned.append(doc)
            print(f"❌ ORPHANED: {filename}")
            print(f"   doc_id: {doc_id[:16]}...")
        else:
            print(f"✓ OK: {filename}")

    print()
    print(f"Found {len(orphaned)} orphaned documents")
    print()

    if not orphaned:
        print("No cleanup needed!")
        return 0

    if args.dry_run:
        print("DRY RUN - Would delete:")
        for doc in orphaned:
            print(f"  - {doc['filename']} (doc_id: {doc['doc_id'][:16]}...)")
        print()
        print("Run without --dry-run to actually delete")
        return 0

    # Delete orphaned documents
    print("Deleting orphaned documents...")
    print()

    deleted_count = 0
    for doc in orphaned:
        filename = doc["filename"]
        doc_id = doc["doc_id"]
        file_path = f"/uploads/{filename}"  # Path doesn't need to exist for deletion

        print(f"Deleting: {filename} (doc_id: {doc_id[:16]}...)")
        try:
            result = delete_document(filename, file_path)
            print(f"  ✓ ChromaDB: {result['visual_deleted']} visual + {result['text_deleted']} text embeddings")
            print(f"  ✓ Filesystem: {result['page_images_deleted']} images, "
                  f"{result['cover_art_deleted']} cover art, "
                  f"{'1' if result.get('markdown_deleted') else '0'} markdown")
            deleted_count += 1
        except Exception as e:
            print(f"  ✗ Error: {e}")
        print()

    print("=" * 70)
    print(f"Cleanup complete: {deleted_count}/{len(orphaned)} documents deleted")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
