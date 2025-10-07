#!/usr/bin/env python3
"""
Query ChromaDB - Simple script to check stored documents and statistics.

Usage:
    python3 scripts/query-chromadb.py                 # Show stats
    python3 scripts/query-chromadb.py --list-docs     # List all documents
    python3 scripts/query-chromadb.py --search "text" # Search documents
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage import ChromaClient
from src.embeddings import ColPaliEngine
import argparse
from typing import List, Dict, Any


def show_stats(client: ChromaClient):
    """Show ChromaDB collection statistics."""
    print("\n" + "="*70)
    print("ChromaDB Statistics")
    print("="*70)
    
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
    print("\n" + "="*70)
    print("Stored Documents")
    print("="*70)
    
    try:
        # Query visual collection for unique doc_ids
        visual_collection = client._visual_collection
        
        # Get all documents
        results = visual_collection.get(
            include=["metadatas"]
        )
        
        # Extract unique documents
        docs = {}
        if results['metadatas']:
            for metadata in results['metadatas']:
                doc_id = metadata.get('doc_id', 'unknown')
                if doc_id not in docs:
                    docs[doc_id] = {
                        'filename': metadata.get('filename', 'N/A'),
                        'pages': set(),
                        'source': metadata.get('source_type', 'N/A')
                    }
                
                page_num = metadata.get('page_num')
                if page_num is not None:
                    docs[doc_id]['pages'].add(page_num)
        
        print(f"\n📄 Total documents: {len(docs)}\n")
        
        for idx, (doc_id, info) in enumerate(docs.items(), 1):
            pages_count = len(info['pages']) if info['pages'] else 'N/A'
            print(f"{idx}. {info['filename']}")
            print(f"   ID: {doc_id}")
            print(f"   Pages: {pages_count}")
            print(f"   Source: {info['source']}")
            print()
        
    except Exception as e:
        print(f"❌ Error listing documents: {e}")


def search_documents(client: ChromaClient, query: str, top_k: int = 5):
    """Search documents with a text query."""
    print("\n" + "="*70)
    print(f"Search Results for: '{query}'")
    print("="*70)
    
    try:
        # For now, we'll do a simple metadata search
        # Full semantic search would require loading the ColPali model
        
        text_collection = client._text_collection
        
        # Get all documents and filter by text
        results = text_collection.get(
            include=["metadatas", "documents"]
        )
        
        matches = []
        if results['metadatas']:
            for idx, metadata in enumerate(results['metadatas']):
                doc_text = results['documents'][idx] if results['documents'] and idx < len(results['documents']) else ""
                # Handle None values
                if doc_text is None:
                    doc_text = ""

                # Simple text matching
                if query.lower() in doc_text.lower():
                    matches.append({
                        'filename': metadata.get('filename', 'N/A'),
                        'doc_id': metadata.get('doc_id', 'unknown'),
                        'page': metadata.get('page_num', 'N/A'),
                        'chunk': metadata.get('chunk_id', 'N/A'),
                        'preview': doc_text[:200] + '...' if len(doc_text) > 200 else doc_text
                    })
        
        print(f"\n🔍 Found {len(matches)} matches (showing first {min(len(matches), top_k)}):\n")
        
        for idx, match in enumerate(matches[:top_k], 1):
            print(f"{idx}. {match['filename']}")
            print(f"   Doc ID: {match['doc_id']} | Page: {match['page']} | Chunk: {match['chunk']}")
            print(f"   Preview: {match['preview']}")
            print()
        
        if not matches:
            print("No matches found. Try a different query or use semantic search.")
        
    except Exception as e:
        print(f"❌ Error searching: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Query ChromaDB for stored documents and statistics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/query-chromadb.py                    # Show statistics
  python3 scripts/query-chromadb.py --list-docs        # List all documents
  python3 scripts/query-chromadb.py --search "revenue" # Search for text
  python3 scripts/query-chromadb.py --top-k 10         # Show more results
        """
    )
    
    parser.add_argument('--list-docs', action='store_true',
                       help='List all stored documents')
    parser.add_argument('--search', type=str,
                       help='Search documents for text')
    parser.add_argument('--top-k', type=int, default=5,
                       help='Number of results to show (default: 5)')
    parser.add_argument('--host', default='localhost',
                       help='ChromaDB host (default: localhost)')
    parser.add_argument('--port', type=int, default=8001,
                       help='ChromaDB port (default: 8001)')
    
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
            search_documents(client, args.search, args.top_k)
        else:
            show_stats(client)
        
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
