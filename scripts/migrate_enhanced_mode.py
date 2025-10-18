#!/usr/bin/env python3
"""
Migrate existing documents to enhanced mode.

This script provides multiple migration strategies:
  1. Reprocess all: Fully reprocess all documents with structure extraction
  2. Lazy migration: Flag documents for lazy reprocessing on access
  3. Flag legacy: Mark documents as legacy (v0.0) without reprocessing
  4. Specific document: Migrate single document by ID

Usage:
    # Reprocess all documents (slow but thorough)
    python scripts/migrate_enhanced_mode.py --reprocess-all

    # Lazy migration (fast, on-demand)
    python scripts/migrate_enhanced_mode.py --lazy

    # Flag as legacy (instant, no reprocessing)
    python scripts/migrate_enhanced_mode.py --flag-legacy

    # Migrate specific document
    python scripts/migrate_enhanced_mode.py --doc-id doc_12345

    # Dry run (show what would be done)
    python scripts/migrate_enhanced_mode.py --reprocess-all --dry-run
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from processing.processor import DocumentProcessor
    from storage.chroma_client import ChromaClient
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure to run from project root and have all dependencies installed.")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/migration.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class MigrationStats:
    """Track migration statistics."""

    def __init__(self):
        self.total_documents = 0
        self.processed = 0
        self.failed = 0
        self.skipped = 0
        self.start_time = time.time()
        self.errors: List[Tuple[str, str]] = []  # (doc_id, error_message)

    def record_success(self):
        self.processed += 1

    def record_failure(self, doc_id: str, error: str):
        self.failed += 1
        self.errors.append((doc_id, error))

    def record_skip(self):
        self.skipped += 1

    def elapsed_time(self) -> float:
        return time.time() - self.start_time

    def report(self) -> str:
        """Generate migration report."""
        elapsed = self.elapsed_time()
        return f"""
Migration Statistics
{'=' * 60}
Total Documents:     {self.total_documents}
Processed:           {self.processed}
Failed:              {self.failed}
Skipped:             {self.skipped}
Elapsed Time:        {elapsed:.1f}s
Avg Time per Doc:    {elapsed / max(self.processed, 1):.1f}s

Errors:
{self._format_errors()}
"""

    def _format_errors(self) -> str:
        if not self.errors:
            return "  None"
        return "\n".join(f"  - {doc_id}: {error}" for doc_id, error in self.errors)


class EnhancedModeMigrator:
    """Migrate documents to enhanced mode."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.chroma_client = ChromaClient()
        self.stats = MigrationStats()

        # Check if enhanced mode is enabled
        self.enhanced_mode = os.getenv("ENHANCED_MODE", "false").lower() == "true"
        if not self.enhanced_mode and not dry_run:
            logger.warning("ENHANCED_MODE is not enabled. Set ENHANCED_MODE=true before migrating.")

    def get_all_documents(self) -> List[Dict]:
        """Retrieve all documents from ChromaDB."""
        logger.info("Fetching all documents from ChromaDB...")

        try:
            # Get all unique document IDs from visual collection
            visual_collection = self.chroma_client.get_collection("visual_embeddings")
            results = visual_collection.get()

            if not results or not results.get("metadatas"):
                logger.warning("No documents found in ChromaDB")
                return []

            # Extract unique document IDs
            doc_ids = set()
            doc_info = {}

            for metadata in results["metadatas"]:
                doc_id = metadata.get("doc_id")
                if doc_id and doc_id not in doc_ids:
                    doc_ids.add(doc_id)
                    doc_info[doc_id] = {
                        "doc_id": doc_id,
                        "filename": metadata.get("filename", "unknown"),
                        "metadata_version": metadata.get("metadata_version", "0.0"),
                        "has_structure": metadata.get("has_structure", False),
                    }

            documents = list(doc_info.values())
            logger.info(f"Found {len(documents)} unique documents")

            return documents

        except Exception as e:
            logger.error(f"Failed to fetch documents: {e}")
            return []

    def reprocess_all_documents(self) -> MigrationStats:
        """
        Reprocess all documents with enhanced mode enabled.

        This is the most thorough migration strategy:
        - Fully reprocesses each document
        - Extracts structure data
        - Updates all metadata
        """
        logger.info("Starting full reprocessing migration...")

        documents = self.get_all_documents()
        self.stats.total_documents = len(documents)

        if self.dry_run:
            logger.info(f"[DRY RUN] Would reprocess {len(documents)} documents")
            return self.stats

        for i, doc in enumerate(documents, 1):
            doc_id = doc["doc_id"]
            filename = doc["filename"]

            logger.info(f"[{i}/{len(documents)}] Reprocessing {filename} ({doc_id})")

            try:
                # Get original file path
                file_path = self._find_document_file(filename)

                if not file_path:
                    logger.warning(f"File not found: {filename}")
                    self.stats.record_skip()
                    continue

                # Reprocess document
                processor = DocumentProcessor()
                result = processor.process_document(str(file_path))

                if result.get("status") == "success":
                    logger.info(f"✓ Successfully reprocessed {filename}")
                    self.stats.record_success()
                else:
                    error_msg = result.get("error", "Unknown error")
                    logger.error(f"✗ Failed to reprocess {filename}: {error_msg}")
                    self.stats.record_failure(doc_id, error_msg)

            except Exception as e:
                logger.error(f"✗ Exception reprocessing {doc_id}: {e}")
                self.stats.record_failure(doc_id, str(e))

        logger.info(
            f"Migration complete. Processed {self.stats.processed}/{len(documents)} documents"
        )
        return self.stats

    def lazy_migration(self) -> MigrationStats:
        """
        Flag documents for lazy migration.

        Documents will be reprocessed when first accessed.
        This is fast but requires runtime reprocessing logic.
        """
        logger.info("Starting lazy migration (flagging for on-demand reprocessing)...")

        documents = self.get_all_documents()
        self.stats.total_documents = len(documents)

        if self.dry_run:
            logger.info(f"[DRY RUN] Would flag {len(documents)} documents for lazy migration")
            return self.stats

        for doc in documents:
            doc_id = doc["doc_id"]

            # Check if already has structure
            if doc.get("has_structure"):
                logger.info(f"Skipping {doc_id} (already enhanced)")
                self.stats.record_skip()
                continue

            try:
                # Update metadata to flag for lazy migration
                self._flag_for_lazy_migration(doc_id)
                logger.info(f"✓ Flagged {doc_id} for lazy migration")
                self.stats.record_success()

            except Exception as e:
                logger.error(f"✗ Failed to flag {doc_id}: {e}")
                self.stats.record_failure(doc_id, str(e))

        logger.info(f"Lazy migration complete. Flagged {self.stats.processed} documents")
        return self.stats

    def flag_legacy_documents(self) -> MigrationStats:
        """
        Flag existing documents as legacy (v0.0).

        This is the fastest option - just updates metadata version.
        Old documents keep working but lack enhanced features.
        """
        logger.info("Flagging documents as legacy (v0.0)...")

        documents = self.get_all_documents()
        self.stats.total_documents = len(documents)

        if self.dry_run:
            logger.info(f"[DRY RUN] Would flag {len(documents)} documents as legacy")
            return self.stats

        for doc in documents:
            doc_id = doc["doc_id"]

            # Skip if already versioned
            if doc.get("metadata_version") != "0.0":
                logger.info(f"Skipping {doc_id} (already versioned)")
                self.stats.record_skip()
                continue

            try:
                # Update metadata version to 0.0 (legacy)
                self._update_metadata_version(doc_id, "0.0")
                logger.info(f"✓ Flagged {doc_id} as legacy (v0.0)")
                self.stats.record_success()

            except Exception as e:
                logger.error(f"✗ Failed to flag {doc_id}: {e}")
                self.stats.record_failure(doc_id, str(e))

        logger.info(f"Legacy flagging complete. Updated {self.stats.processed} documents")
        return self.stats

    def migrate_document(self, doc_id: str) -> bool:
        """
        Migrate a specific document by ID.

        Args:
            doc_id: Document identifier

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Migrating document: {doc_id}")

        if self.dry_run:
            logger.info(f"[DRY RUN] Would migrate document {doc_id}")
            return True

        try:
            # Get document metadata
            doc_info = self._get_document_metadata(doc_id)

            if not doc_info:
                logger.error(f"Document not found: {doc_id}")
                return False

            # Check if already enhanced
            if doc_info.get("has_structure"):
                logger.info(f"Document {doc_id} already has structure data")
                return True

            # Get original file
            filename = doc_info.get("filename")
            file_path = self._find_document_file(filename)

            if not file_path:
                logger.error(f"File not found: {filename}")
                return False

            # Reprocess document
            processor = DocumentProcessor()
            result = processor.process_document(str(file_path))

            if result.get("status") == "success":
                logger.info(f"✓ Successfully migrated {doc_id}")
                return True
            else:
                error_msg = result.get("error", "Unknown error")
                logger.error(f"✗ Failed to migrate {doc_id}: {error_msg}")
                return False

        except Exception as e:
            logger.error(f"✗ Exception migrating {doc_id}: {e}")
            return False

    def _find_document_file(self, filename: str) -> Optional[Path]:
        """Find document file in uploads directory."""
        uploads_dir = Path(__file__).parent.parent / "data" / "uploads"

        # Search for file
        for file_path in uploads_dir.rglob(filename):
            if file_path.is_file():
                return file_path

        return None

    def _get_document_metadata(self, doc_id: str) -> Optional[Dict]:
        """Get metadata for a specific document."""
        try:
            visual_collection = self.chroma_client.get_collection("visual_embeddings")
            results = visual_collection.get(where={"doc_id": doc_id}, limit=1)

            if results and results.get("metadatas"):
                return results["metadatas"][0]

            return None

        except Exception as e:
            logger.error(f"Failed to get metadata for {doc_id}: {e}")
            return None

    def _update_metadata_version(self, doc_id: str, version: str):
        """Update metadata_version for all chunks of a document."""
        try:
            # Update visual collection
            visual_collection = self.chroma_client.get_collection("visual_embeddings")
            visual_collection.update(
                where={"doc_id": doc_id}, metadatas={"metadata_version": version}
            )

            # Update text collection
            text_collection = self.chroma_client.get_collection("text_embeddings")
            text_collection.update(
                where={"doc_id": doc_id}, metadatas={"metadata_version": version}
            )

        except Exception as e:
            logger.error(f"Failed to update metadata version for {doc_id}: {e}")
            raise

    def _flag_for_lazy_migration(self, doc_id: str):
        """Flag document for lazy migration."""
        try:
            # Add lazy_migration flag to metadata
            visual_collection = self.chroma_client.get_collection("visual_embeddings")
            visual_collection.update(
                where={"doc_id": doc_id},
                metadatas={
                    "lazy_migration": True,
                    "migration_flagged_at": datetime.now().isoformat(),
                },
            )

            text_collection = self.chroma_client.get_collection("text_embeddings")
            text_collection.update(
                where={"doc_id": doc_id},
                metadatas={
                    "lazy_migration": True,
                    "migration_flagged_at": datetime.now().isoformat(),
                },
            )

        except Exception as e:
            logger.error(f"Failed to flag for lazy migration: {e}")
            raise


def main():
    """Main migration entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate documents to enhanced mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Migration strategies
    strategy_group = parser.add_mutually_exclusive_group(required=True)
    strategy_group.add_argument(
        "--reprocess-all",
        action="store_true",
        help="Reprocess all documents with structure extraction (slow but thorough)",
    )
    strategy_group.add_argument(
        "--lazy",
        action="store_true",
        help="Flag documents for lazy migration (fast, on-demand reprocessing)",
    )
    strategy_group.add_argument(
        "--flag-legacy",
        action="store_true",
        help="Mark documents as legacy v0.0 (instant, no reprocessing)",
    )
    strategy_group.add_argument("--doc-id", type=str, help="Migrate specific document by ID")

    # Options
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done without making changes"
    )

    args = parser.parse_args()

    # Create migrator
    migrator = EnhancedModeMigrator(dry_run=args.dry_run)

    # Execute migration strategy
    try:
        if args.reprocess_all:
            stats = migrator.reprocess_all_documents()
            print(stats.report())

        elif args.lazy:
            stats = migrator.lazy_migration()
            print(stats.report())

        elif args.flag_legacy:
            stats = migrator.flag_legacy_documents()
            print(stats.report())

        elif args.doc_id:
            success = migrator.migrate_document(args.doc_id)
            sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logger.warning("\nMigration interrupted by user")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
