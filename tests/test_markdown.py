"""Test markdown integration in document processing."""

from pathlib import Path

from src.embeddings.colpali_wrapper import ColPaliEngine
from src.processing.processor import DocumentProcessor
from src.storage.chroma_client import ChromaClient


def test_markdown_integration():
    """Test that markdown is generated and metadata is populated."""
    print("\n" + "=" * 80)
    print("Testing Markdown Integration")
    print("=" * 80)

    # Initialize components
    print("\n[1] Initializing components...")
    embedding_engine = ColPaliEngine()
    storage_client = ChromaClient(host="localhost", port=8001)

    # Create processor (without enhanced mode to avoid structure dict issues)
    processor = DocumentProcessor(embedding_engine=embedding_engine, storage_client=storage_client)

    # Test document path
    test_doc = Path("data/test-documents/test-financial-report.docx")

    if not test_doc.exists():
        print(f"❌ Test document not found: {test_doc}")
        return False

    print(f"✓ Using test document: {test_doc.name}")

    # Process document
    print("\n[2] Processing document...")
    result = processor.process_document(test_doc)

    # Check markdown directory was created
    markdown_dir = Path("data/markdown")
    print(f"\n[3] Checking markdown directory: {markdown_dir}")

    if markdown_dir.exists():
        print(f"✓ Markdown directory exists")
        markdown_files = list(markdown_dir.glob("*.md"))
        print(f"✓ Found {len(markdown_files)} markdown file(s)")
    else:
        print(f"❌ Markdown directory not created")
        return False

    # Query metadata from ChromaDB to verify markdown fields
    print("\n[4] Querying metadata from ChromaDB...")

    # Get visual metadata
    query_output = embedding_engine.embed_query("test")
    visual_results = storage_client.search_visual(
        query_embedding=query_output["cls_token"], n_results=1, filters={"doc_id": result.doc_id}
    )

    if visual_results:
        metadata = visual_results[0]["metadata"]
        print(f"\n✓ Retrieved visual metadata for doc_id: {result.doc_id}")

        # Check markdown fields
        has_markdown = metadata.get("has_markdown", False)
        markdown_path = metadata.get("markdown_path")
        markdown_size_kb = metadata.get("markdown_size_kb")

        print(f"\n[5] Markdown Metadata Validation:")
        print(f"  has_markdown: {has_markdown}")
        print(f"  markdown_path: {markdown_path}")
        print(f"  markdown_size_kb: {markdown_size_kb}")

        # Validate
        if has_markdown:
            print(f"\n✓ has_markdown = True")
        else:
            print(f"❌ has_markdown = False (expected True)")
            return False

        if markdown_path:
            print(f"✓ markdown_path present: {markdown_path}")
            # Verify absolute path
            if Path(markdown_path).is_absolute():
                print(f"✓ markdown_path is absolute")
            else:
                print(f"❌ markdown_path is not absolute")
                return False
            # Verify file exists
            if Path(markdown_path).exists():
                print(f"✓ Markdown file exists on disk")
                # Read and display first few lines
                with open(markdown_path, "r") as f:
                    content = f.read()
                    lines = content.split("\n")[:5]
                    print(f"\n  Preview (first 5 lines):")
                    for line in lines:
                        print(f"    {line}")
            else:
                print(f"❌ Markdown file not found at: {markdown_path}")
                return False
        else:
            print(f"❌ markdown_path missing")
            return False

        if markdown_size_kb is not None and markdown_size_kb > 0:
            print(f"✓ markdown_size_kb = {markdown_size_kb} KB")
            # Check precision (1 decimal place)
            if markdown_size_kb == round(markdown_size_kb, 1):
                print(f"✓ markdown_size_kb has correct precision (1 decimal)")
            else:
                print(f"❌ markdown_size_kb precision incorrect")
                return False
        else:
            print(f"❌ markdown_size_kb invalid: {markdown_size_kb}")
            return False

        # Check text metadata too
        text_query_output = embedding_engine.embed_query("test")
        text_results = storage_client.search_text(
            query_embedding=text_query_output["cls_token"],
            n_results=1,
            filters={"doc_id": result.doc_id},
        )

        if text_results:
            text_metadata = text_results[0]["metadata"]
            text_has_markdown = text_metadata.get("has_markdown", False)
            text_markdown_path = text_metadata.get("markdown_path")

            print(f"\n[6] Text Metadata Validation:")
            print(f"  has_markdown: {text_has_markdown}")
            print(f"  markdown_path: {text_markdown_path}")

            if text_has_markdown and text_markdown_path == markdown_path:
                print(f"✓ Text metadata matches visual metadata")
            else:
                print(f"❌ Text metadata mismatch")
                return False

        print("\n" + "=" * 80)
        print("✅ MARKDOWN INTEGRATION TEST PASSED!")
        print("=" * 80)
        print("\nContract Validation:")
        print("  ✓ Markdown Storage Contract: PASS")
        print("  ✓ Metadata Schema Contract: PASS")
        return True
    else:
        print(f"❌ No visual results found for doc_id: {result.doc_id}")
        return False


if __name__ == "__main__":
    import sys

    success = test_markdown_integration()
    sys.exit(0 if success else 1)
