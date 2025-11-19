#!/usr/bin/env python3
"""
Query ChromaDB - Simple script to check stored documents and statistics.

Usage:
    python3 scripts/query-chromadb.py                 # Show stats
    python3 scripts/query-chromadb.py --list-docs     # List all documents
    python3 scripts/query-chromadb.py --search "text" # Search documents
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse

from tkr_docusearch.embeddings import ColPaliEngine
from tkr_docusearch.search import SearchEngine
from tkr_docusearch.storage import ChromaClient


def show_stats(client: ChromaClient):
    """Show ChromaDB collection statistics."""
    print("\n" + "=" * 70)
    print("ChromaDB Statistics")
    print("=" * 70)

    try:
        stats = client.get_collection_stats()

        print(f"\n📊 Collection Counts:")
        print(f"  Visual embeddings: {stats['visual_count']:,}")
        print(f"  Text embeddings:   {stats['text_count']:,}")
        print(f"  Total documents:   {stats['total_documents']:,}")
        print(f"  Storage size:      {stats['storage_size_mb']:.2f} MB")
        print(f"  Collections:       visual, text")

    except Exception as e:
        print(f"❌ Error getting stats: {e}")


def list_documents(client: ChromaClient):
    """List all documents in ChromaDB."""
    print("\n" + "=" * 70)
    print("Stored Documents")
    print("=" * 70)

    try:
        # Query visual collection for unique doc_ids
        visual_collection = client._visual_collection

        # Get all documents
        results = visual_collection.get(include=["metadatas"])

        # Extract unique documents
        docs = {}
        if results["metadatas"]:
            for metadata in results["metadatas"]:
                doc_id = metadata.get("doc_id", "unknown")
                if doc_id not in docs:
                    docs[doc_id] = {
                        "filename": metadata.get("filename", "N/A"),
                        "pages": set(),
                        "source": metadata.get("source_type", "N/A"),
                    }

                page_num = metadata.get("page_num")
                if page_num is not None:
                    docs[doc_id]["pages"].add(page_num)

        print(f"\n📄 Total documents: {len(docs)}\n")

        for idx, (doc_id, info) in enumerate(docs.items(), 1):
            pages_count = len(info["pages"]) if info["pages"] else "N/A"
            print(f"{idx}. {info['filename']}")
            print(f"   ID: {doc_id}")
            print(f"   Pages: {pages_count}")
            print(f"   Source: {info['source']}")
            print()

    except Exception as e:
        print(f"❌ Error listing documents: {e}")


def search_documents(client: ChromaClient, query: str, top_k: int = 5, mode: str = "hybrid"):
    """Search documents using semantic similarity search with ColPali."""
    print("\n" + "=" * 70)
    print(f"Semantic Search for: '{query}' (mode: {mode})")
    print("=" * 70)

    try:
        # Initialize ColPali engine and SearchEngine
        print("\n⏳ Loading ColPali model (this may take a moment on first run)...")
        embedding_engine = ColPaliEngine()
        search_engine = SearchEngine(storage_client=client, embedding_engine=embedding_engine)
        print("✅ Model loaded successfully")

        # Perform semantic search
        print(f"\n🔍 Searching with semantic similarity...")
        response = search_engine.search(
            query=query, n_results=top_k, search_mode=mode, enable_reranking=True
        )

        results = response["results"]

        print(f"\n📊 Search Statistics:")
        print(f"  Total candidates: {response['candidates_retrieved']}")
        print(f"  Reranked: {response['reranked_count']}")
        print(f"  Stage 1 time: {response['stage1_time_ms']:.1f}ms")
        print(f"  Stage 2 time: {response['stage2_time_ms']:.1f}ms")
        print(f"  Total time: {response['total_time_ms']:.1f}ms")

        print(f"\n🎯 Found {len(results)} results:\n")

        for idx, result in enumerate(results, 1):
            print(f"{idx}. {result['filename']}")
            print(f"   Doc ID: {result['doc_id']}")
            print(f"   Page: {result.get('page', 'N/A')}")
            print(f"   Score: {result['score']:.4f}")
            print(f"   Type: {result.get('type', 'N/A')}")
            if result.get("source_path"):
                print(f"   Path: {result['source_path']}")
            print()

        if not results:
            print("No matches found. Try a different query or search mode.")

    except Exception as e:
        print(f"❌ Error searching: {e}")
        import traceback

        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(
        description="Query ChromaDB for stored documents and statistics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/query-chromadb.py                           # Show statistics
  python3 scripts/query-chromadb.py --list-docs               # List all documents
  python3 scripts/query-chromadb.py --search "prompting"      # Semantic search (hybrid)
  python3 scripts/query-chromadb.py --search "revenue" --mode visual_only  # Visual search only
  python3 scripts/query-chromadb.py --search "quarterly" --top-k 10       # Show more results
        """,
    )

    parser.add_argument("--list-docs", action="store_true", help="List all stored documents")
    parser.add_argument("--search", type=str, help="Search documents using semantic similarity")
    parser.add_argument(
        "--mode",
        type=str,
        default="hybrid",
        choices=["hybrid", "visual_only", "text_only"],
        help="Search mode (default: hybrid)",
    )
    parser.add_argument(
        "--top-k", type=int, default=5, help="Number of results to show (default: 5)"
    )
    parser.add_argument("--host", default="localhost", help="ChromaDB host (default: localhost)")
    parser.add_argument("--port", type=int, default=8001, help="ChromaDB port (default: 8001)")

    args = parser.parse_args()

    # Initialize ChromaDB client
    print(f"\n🔗 Connecting to ChromaDB at {args.host}:{args.port}...")

    try:
        client = ChromaClient(host=args.host, port=args.port)
        print("✅ Connected successfully!")

        # Execute requested operation
        if args.list_docs:
            list_documents(client)
        elif args.search:
            search_documents(client, args.search, args.top_k, args.mode)
        else:
            show_stats(client)

        print("=" * 70 + "\n")

    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
