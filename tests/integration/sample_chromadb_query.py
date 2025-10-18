#!/usr/bin/env python
"""
Sample ChromaDB query demonstrating enhanced metadata retrieval.

This script shows how to query ChromaDB for documents with enhanced metadata
and parse the stored structure and context information.

NOTE: This is a demonstration script. Actual queries require a running ChromaDB instance.
"""




def sample_visual_collection_query():
    """
    Sample query for visual collection with enhanced metadata.

    This demonstrates the ChromaDB query pattern for retrieving documents
    with structure information.
    """
    print("\n" + "=" * 80)
    print("SAMPLE VISUAL COLLECTION QUERY")
    print("=" * 80)

    # Example ChromaDB query (pseudo-code)
    query_example = """
    # Query all pages with structure information
    results = visual_collection.get(
        where={"has_structure": {"$eq": True}},
        include=["metadatas", "embeddings", "documents"]
    )

    # Or query specific document
    results = visual_collection.get(
        where={
            "$and": [
                {"doc_id": {"$eq": "abc123def456789"}},
                {"has_structure": {"$eq": True}}
            ]
        }
    )

    # Or query pages with tables
    results = visual_collection.get(
        where={"num_tables": {"$gt": 0}}
    )
    """

    print("\nQuery patterns:")
    print(query_example)

    # Example result processing
    print("\nProcessing results:")
    print(
        """
    for metadata in results['metadatas']:
        if metadata['has_structure']:
            # Decompress structure
            structure_dict = decompress_structure_metadata(metadata['structure'])

            # Access structure information
            headings = structure_dict['headings']
            tables = structure_dict['tables']
            pictures = structure_dict['pictures']

            # Use for bidirectional highlighting
            for heading in headings:
                bbox = heading['bbox']  # [x1, y1, x2, y2]
                # Scale using image_width and image_height
                scale_x = display_width / metadata['image_width']
                scale_y = display_height / metadata['image_height']
                display_bbox = [
                    bbox[0] * scale_x,
                    bbox[1] * scale_y,
                    bbox[2] * scale_x,
                    bbox[3] * scale_y
                ]
    """
    )


def sample_text_collection_query():
    """
    Sample query for text collection with enhanced metadata.

    This demonstrates the ChromaDB query pattern for retrieving chunks
    with context information.
    """
    print("\n" + "=" * 80)
    print("SAMPLE TEXT COLLECTION QUERY")
    print("=" * 80)

    # Example ChromaDB query (pseudo-code)
    query_example = """
    # Query all chunks with context information
    results = text_collection.get(
        where={"has_context": {"$eq": True}},
        include=["metadatas", "embeddings"]
    )

    # Query chunks under specific heading
    results = text_collection.get(
        where={
            "$and": [
                {"doc_id": {"$eq": "abc123def456789"}},
                {"parent_heading": {"$eq": "Executive Summary"}}
            ]
        }
    )

    # Query chunks on specific page
    results = text_collection.get(
        where={
            "$and": [
                {"doc_id": {"$eq": "abc123def456789"}},
                {"page": {"$eq": 1}}
            ]
        }
    )

    # Query chunks that reference tables
    results = text_collection.get(
        where={
            "$and": [
                {"doc_id": {"$eq": "abc123def456789"}},
                {"related_tables": {"$ne": "[]"}}
            ]
        }
    )

    # Query chunks by element type
    results = text_collection.get(
        where={"element_type": {"$eq": "list_item"}}
    )
    """

    print("\nQuery patterns:")
    print(query_example)

    # Example result processing
    print("\nProcessing results:")
    print(
        """
    for metadata in results['metadatas']:
        if metadata['has_context']:
            # Access context information
            parent_heading = metadata['parent_heading']
            section_path = metadata['section_path']
            element_type = metadata['element_type']

            # Parse JSON array fields
            related_tables = json.loads(metadata['related_tables'])
            related_pictures = json.loads(metadata['related_pictures'])
            page_nums = json.loads(metadata['page_nums'])

            # Check if chunk crosses page boundary
            is_boundary = metadata['is_page_boundary']

            # Use for bidirectional highlighting
            if 'bbox' in metadata and metadata['bbox']:
                bbox = json.loads(metadata['bbox'])
                # Draw highlight at bbox coordinates
    """
    )


def sample_page_chunk_mapping_query():
    """
    Sample query for page-to-chunk mapping.

    This demonstrates how to efficiently find all chunks for a specific page.
    """
    print("\n" + "=" * 80)
    print("SAMPLE PAGE-TO-CHUNK MAPPING QUERY")
    print("=" * 80)

    # Example query for page-to-chunk mapping
    query_example = """
    # Find all chunks that start on page 2
    results = text_collection.get(
        where={
            "$and": [
                {"doc_id": {"$eq": "abc123def456789"}},
                {"page": {"$eq": 2}}
            ]
        }
    )

    # This will include:
    # - Chunks that start on page 2 (page=2)
    # - Multi-page chunks that start earlier but have page=2 won't be included
    #   (use page_nums field to find chunks that span page 2)

    # To find ALL chunks that include page 2 (anywhere):
    # 1. Query chunks with page=2 (chunks starting on page 2)
    # 2. Query chunks with page<2 and parse page_nums to check if 2 is included

    # Example: Find all chunks including page 2
    all_chunks = text_collection.get(
        where={"doc_id": {"$eq": "abc123def456789"}}
    )

    chunks_with_page_2 = []
    for i, metadata in enumerate(all_chunks['metadatas']):
        if metadata.get('has_context'):
            page_nums = json.loads(metadata['page_nums'])
            if 2 in page_nums:
                chunks_with_page_2.append({
                    'id': all_chunks['ids'][i],
                    'metadata': metadata
                })
    """

    print("\nQuery patterns:")
    print(query_example)

    # Example result processing
    print("\nUse cases:")
    print(
        """
    1. Document viewer: Show all chunks on current page
       - Query by page field for primary chunks
       - Check page_nums for multi-page chunks

    2. Heading click: Show all chunks under heading
       - Query by parent_heading field

    3. Structure navigation: Show document outline
       - Query visual collection for structure
       - Decompress and display heading hierarchy

    4. Cross-references: Find chunks mentioning tables/pictures
       - Query by related_tables or related_pictures fields
       - Parse JSON arrays to get IDs
    """
    )


def main():
    """Display all sample queries."""
    print("\n" + "=" * 80)
    print("CHROMADB ENHANCED METADATA QUERY SAMPLES")
    print("=" * 80)
    print("\nThese examples demonstrate how to query ChromaDB for enhanced metadata")
    print("and use it for bidirectional highlighting and document navigation.")

    sample_visual_collection_query()
    sample_text_collection_query()
    sample_page_chunk_mapping_query()

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(
        """
Enhanced metadata enables:

✓ Bidirectional highlighting between search results and document view
✓ Efficient page-to-chunk mapping for document viewer
✓ Structured navigation (headings, sections, tables)
✓ Cross-reference queries (find chunks mentioning specific elements)
✓ Element type filtering (text, list items, tables, code, formulas)

All metadata is stored in ChromaDB and queryable using standard where clauses.
JSON array fields (page_nums, related_tables, related_pictures) require
parsing after retrieval due to ChromaDB's flat metadata limitation.
    """
    )


if __name__ == "__main__":
    main()
