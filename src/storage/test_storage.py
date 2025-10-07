"""
Unit tests for ChromaDB storage module.

Tests cover:
- Collection initialization
- Embedding storage (visual and text)
- Search operations
- Full embedding retrieval
- Document deletion
- Collection statistics
- Compression/decompression
- Error handling
- Collection management
"""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime

from .chroma_client import (
    ChromaClient,
    StorageError,
    ChromaDBConnectionError,
    EmbeddingValidationError,
    MetadataCompressionError,
    DocumentNotFoundError,
)
from .collection_manager import CollectionManager
from .compression import (
    compress_embeddings,
    decompress_embeddings,
    estimate_compressed_size,
    compression_ratio,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_chroma_client():
    """Mock ChromaDB HttpClient."""
    with patch('chromadb.HttpClient') as mock:
        client = mock.return_value
        client.heartbeat.return_value = None
        yield mock


@pytest.fixture
def mock_collection():
    """Mock ChromaDB Collection."""
    collection = Mock()
    collection.count.return_value = 0
    collection.add.return_value = None
    collection.get.return_value = {'ids': [], 'metadatas': [], 'embeddings': []}
    collection.query.return_value = {
        'ids': [[]],
        'distances': [[]],
        'metadatas': [[]],
        'embeddings': [[]]
    }
    collection.delete.return_value = None
    return collection


@pytest.fixture
def chroma_client(mock_chroma_client, mock_collection):
    """Initialize ChromaClient with mocked dependencies."""
    with patch.object(ChromaClient, '_get_or_create_collection', return_value=mock_collection):
        client = ChromaClient(host="localhost", port=8000)
        return client


@pytest.fixture
def sample_visual_metadata():
    """Sample visual embedding metadata."""
    return {
        "filename": "test.pdf",
        "source_path": "/data/test.pdf",
        "file_size": 1024000
    }


@pytest.fixture
def sample_text_metadata():
    """Sample text embedding metadata."""
    return {
        "filename": "test.pdf",
        "page": 1,
        "source_path": "/data/test.pdf",
        "text_preview": "This is a test document preview...",
        "word_count": 150
    }


@pytest.fixture
def sample_embeddings():
    """Sample multi-vector embeddings."""
    return np.random.randn(100, 768).astype(np.float32)


# ============================================================================
# Compression Tests
# ============================================================================

class TestCompression:
    """Test compression utilities."""

    def test_compress_decompress_roundtrip(self):
        """Test compression and decompression restore original values."""
        original = np.random.randn(100, 768).astype(np.float32)

        # Compress
        compressed = compress_embeddings(original)
        assert isinstance(compressed, str)

        # Decompress
        restored = decompress_embeddings(compressed, original.shape)

        # Verify
        np.testing.assert_allclose(original, restored, rtol=1e-6)

    def test_compression_ratio(self):
        """Test compression achieves expected ratio."""
        embeddings = np.random.randn(100, 768).astype(np.float32)
        ratio = compression_ratio(embeddings)

        # Should achieve at least 2x compression
        assert ratio >= 2.0

    def test_estimate_compressed_size(self):
        """Test size estimation."""
        embeddings = np.random.randn(50, 768).astype(np.float32)
        size = estimate_compressed_size(embeddings)

        assert size > 0
        assert size < embeddings.nbytes  # Compressed should be smaller

    def test_compression_different_shapes(self):
        """Test compression with various embedding shapes."""
        shapes = [(10, 768), (50, 768), (200, 768)]

        for shape in shapes:
            embeddings = np.random.randn(*shape).astype(np.float32)
            compressed = compress_embeddings(embeddings)
            restored = decompress_embeddings(compressed, shape)

            assert restored.shape == shape
            np.testing.assert_allclose(embeddings, restored, rtol=1e-6)

    def test_compression_edge_cases(self):
        """Test compression with edge cases."""
        # Single vector
        single = np.random.randn(1, 768).astype(np.float32)
        compressed = compress_embeddings(single)
        restored = decompress_embeddings(compressed, single.shape)
        np.testing.assert_allclose(single, restored, rtol=1e-6)


# ============================================================================
# ChromaClient Initialization Tests
# ============================================================================

class TestChromaClientInit:
    """Test ChromaClient initialization."""

    def test_successful_connection(self, mock_chroma_client, mock_collection):
        """Test successful ChromaDB connection."""
        with patch.object(ChromaClient, '_get_or_create_collection', return_value=mock_collection):
            client = ChromaClient(host="localhost", port=8000)

            assert client.host == "localhost"
            assert client.port == 8000
            mock_chroma_client.return_value.heartbeat.assert_called_once()

    def test_connection_failure(self, mock_chroma_client):
        """Test connection failure handling."""
        mock_chroma_client.return_value.heartbeat.side_effect = Exception("Connection failed")

        with pytest.raises(ChromaDBConnectionError) as exc_info:
            ChromaClient(host="invalid", port=9999)

        assert "Connection failed" in str(exc_info.value)

    def test_collection_creation(self, mock_chroma_client):
        """Test collection creation on init."""
        mock_client = mock_chroma_client.return_value
        mock_client.get_collection.side_effect = Exception("Not found")
        mock_collection = Mock()
        mock_client.create_collection.return_value = mock_collection

        client = ChromaClient()

        # Should attempt to create both collections
        assert mock_client.create_collection.call_count == 2


# ============================================================================
# Embedding Storage Tests
# ============================================================================

class TestEmbeddingStorage:
    """Test embedding storage operations."""

    def test_add_visual_embedding_success(
        self,
        chroma_client,
        sample_embeddings,
        sample_visual_metadata
    ):
        """Test successful visual embedding storage."""
        doc_id = "test-doc-123"
        page = 1

        embedding_id = chroma_client.add_visual_embedding(
            doc_id=doc_id,
            page=page,
            full_embeddings=sample_embeddings,
            metadata=sample_visual_metadata
        )

        assert embedding_id == f"{doc_id}-page{page:03d}"
        assert chroma_client._visual_collection.add.called

    def test_add_text_embedding_success(
        self,
        chroma_client,
        sample_embeddings,
        sample_text_metadata
    ):
        """Test successful text embedding storage."""
        doc_id = "test-doc-123"
        chunk_id = 0

        embedding_id = chroma_client.add_text_embedding(
            doc_id=doc_id,
            chunk_id=chunk_id,
            full_embeddings=sample_embeddings,
            metadata=sample_text_metadata
        )

        assert embedding_id == f"{doc_id}-chunk{chunk_id:04d}"
        assert chroma_client._text_collection.add.called

    def test_invalid_embedding_shape(self, chroma_client, sample_visual_metadata):
        """Test rejection of invalid embedding shapes."""
        # 1D array (should be 2D)
        with pytest.raises(EmbeddingValidationError):
            chroma_client.add_visual_embedding(
                doc_id="test",
                page=1,
                full_embeddings=np.random.randn(768),
                metadata=sample_visual_metadata
            )

        # Wrong dimension
        with pytest.raises(EmbeddingValidationError):
            chroma_client.add_visual_embedding(
                doc_id="test",
                page=1,
                full_embeddings=np.random.randn(100, 512),
                metadata=sample_visual_metadata
            )

    def test_missing_required_metadata(self, chroma_client, sample_embeddings):
        """Test rejection of missing required metadata."""
        # Missing filename
        with pytest.raises(ValueError) as exc_info:
            chroma_client.add_visual_embedding(
                doc_id="test",
                page=1,
                full_embeddings=sample_embeddings,
                metadata={"source_path": "/data/test.pdf"}
            )
        assert "filename" in str(exc_info.value)

    def test_metadata_structure(
        self,
        chroma_client,
        sample_embeddings,
        sample_visual_metadata
    ):
        """Test metadata structure is correctly built."""
        chroma_client.add_visual_embedding(
            doc_id="test-doc",
            page=1,
            full_embeddings=sample_embeddings,
            metadata=sample_visual_metadata
        )

        # Get the metadata passed to ChromaDB
        call_args = chroma_client._visual_collection.add.call_args
        stored_metadata = call_args[1]['metadatas'][0]

        # Verify required fields
        assert stored_metadata['doc_id'] == "test-doc"
        assert stored_metadata['page'] == 1
        assert stored_metadata['type'] == "visual"
        assert 'full_embeddings' in stored_metadata
        assert 'timestamp' in stored_metadata
        assert stored_metadata['seq_length'] == 100

    def test_cls_token_extraction(self, chroma_client, sample_embeddings, sample_visual_metadata):
        """Test CLS token is correctly extracted."""
        chroma_client.add_visual_embedding(
            doc_id="test",
            page=1,
            full_embeddings=sample_embeddings,
            metadata=sample_visual_metadata
        )

        # Get the embedding passed to ChromaDB
        call_args = chroma_client._visual_collection.add.call_args
        stored_embedding = call_args[1]['embeddings'][0]

        # Should be the first token
        expected_cls = sample_embeddings[0].tolist()
        np.testing.assert_allclose(stored_embedding, expected_cls, rtol=1e-6)


# ============================================================================
# Search Tests
# ============================================================================

class TestSearch:
    """Test search operations."""

    def test_visual_search_success(self, chroma_client):
        """Test successful visual search."""
        query_embedding = np.random.randn(768).astype(np.float32)

        # Mock search results
        chroma_client._visual_collection.query.return_value = {
            'ids': [['doc1-page001', 'doc2-page001']],
            'distances': [[0.1, 0.2]],
            'metadatas': [[
                {'doc_id': 'doc1', 'page': 1},
                {'doc_id': 'doc2', 'page': 1}
            ]],
            'embeddings': [[
                [0.1] * 768,
                [0.2] * 768
            ]]
        }

        results = chroma_client.search_visual(query_embedding, n_results=10)

        assert len(results) == 2
        assert results[0]['id'] == 'doc1-page001'
        assert 0 <= results[0]['score'] <= 1  # Similarity score

    def test_text_search_success(self, chroma_client):
        """Test successful text search."""
        query_embedding = np.random.randn(768).astype(np.float32)

        # Mock search results
        chroma_client._text_collection.query.return_value = {
            'ids': [['doc1-chunk0000']],
            'distances': [[0.15]],
            'metadatas': [[{'doc_id': 'doc1', 'chunk_id': 0}]],
            'embeddings': [[[0.1] * 768]]
        }

        results = chroma_client.search_text(query_embedding, n_results=10)

        assert len(results) == 1
        assert results[0]['id'] == 'doc1-chunk0000'

    def test_search_with_filters(self, chroma_client):
        """Test search with metadata filters."""
        query_embedding = np.random.randn(768).astype(np.float32)
        filters = {"filename": "specific.pdf"}

        chroma_client.search_visual(query_embedding, filters=filters)

        # Verify filters were passed
        call_args = chroma_client._visual_collection.query.call_args
        assert call_args[1]['where'] == filters

    def test_search_empty_results(self, chroma_client):
        """Test search with no results."""
        query_embedding = np.random.randn(768).astype(np.float32)

        chroma_client._visual_collection.query.return_value = {
            'ids': [[]],
            'distances': [[]],
            'metadatas': [[]],
            'embeddings': [[]]
        }

        results = chroma_client.search_visual(query_embedding)
        assert len(results) == 0


# ============================================================================
# Full Embedding Retrieval Tests
# ============================================================================

class TestFullEmbeddingRetrieval:
    """Test full embedding retrieval for re-ranking."""

    def test_get_full_embeddings_success(self, chroma_client, sample_embeddings):
        """Test successful full embedding retrieval."""
        embedding_id = "doc1-page001"
        compressed = compress_embeddings(sample_embeddings)

        chroma_client._visual_collection.get.return_value = {
            'ids': [embedding_id],
            'metadatas': [{
                'full_embeddings': compressed,
                'embedding_shape': f"{sample_embeddings.shape}"
            }]
        }

        restored = chroma_client.get_full_embeddings(embedding_id, collection="visual")

        np.testing.assert_allclose(restored, sample_embeddings, rtol=1e-6)

    def test_get_full_embeddings_not_found(self, chroma_client):
        """Test retrieval of non-existent embedding."""
        chroma_client._visual_collection.get.return_value = {
            'ids': [],
            'metadatas': []
        }

        with pytest.raises(DocumentNotFoundError):
            chroma_client.get_full_embeddings("nonexistent", collection="visual")

    def test_get_full_embeddings_corrupted_metadata(self, chroma_client):
        """Test handling of corrupted metadata."""
        chroma_client._visual_collection.get.return_value = {
            'ids': ['doc1'],
            'metadatas': [{'full_embeddings': None}]  # Missing data
        }

        with pytest.raises(MetadataCompressionError):
            chroma_client.get_full_embeddings("doc1", collection="visual")


# ============================================================================
# Document Deletion Tests
# ============================================================================

class TestDocumentDeletion:
    """Test document deletion operations."""

    def test_delete_document_success(self, chroma_client):
        """Test successful document deletion."""
        doc_id = "test-doc"

        # Mock visual embeddings for this doc
        chroma_client._visual_collection.get.return_value = {
            'ids': [f"{doc_id}-page001", f"{doc_id}-page002"]
        }

        # Mock text embeddings for this doc
        chroma_client._text_collection.get.return_value = {
            'ids': [f"{doc_id}-chunk0000", f"{doc_id}-chunk0001", f"{doc_id}-chunk0002"]
        }

        visual_count, text_count = chroma_client.delete_document(doc_id)

        assert visual_count == 2
        assert text_count == 3
        assert chroma_client._visual_collection.delete.called
        assert chroma_client._text_collection.delete.called

    def test_delete_nonexistent_document(self, chroma_client):
        """Test deletion of non-existent document."""
        chroma_client._visual_collection.get.return_value = {'ids': []}
        chroma_client._text_collection.get.return_value = {'ids': []}

        visual_count, text_count = chroma_client.delete_document("nonexistent")

        assert visual_count == 0
        assert text_count == 0


# ============================================================================
# Collection Statistics Tests
# ============================================================================

class TestCollectionStats:
    """Test collection statistics."""

    def test_get_collection_stats(self, chroma_client):
        """Test retrieval of collection statistics."""
        chroma_client._visual_collection.count.return_value = 10
        chroma_client._text_collection.count.return_value = 30

        chroma_client._visual_collection.get.return_value = {
            'metadatas': [
                {'doc_id': 'doc1'},
                {'doc_id': 'doc2'},
                {'doc_id': 'doc1'},  # Duplicate doc_id
            ]
        }

        stats = chroma_client.get_collection_stats()

        assert stats['visual_count'] == 10
        assert stats['text_count'] == 30
        assert stats['total_documents'] == 2  # Unique doc_ids
        assert 'storage_size_mb' in stats


# ============================================================================
# Collection Manager Tests
# ============================================================================

class TestCollectionManager:
    """Test collection management operations."""

    def test_validate_collections(self, chroma_client):
        """Test collection validation."""
        manager = CollectionManager(chroma_client)

        chroma_client._visual_collection.count.return_value = 5
        chroma_client._text_collection.count.return_value = 15

        chroma_client._visual_collection.get.return_value = {
            'metadatas': [{
                'doc_id': 'test',
                'page': 1,
                'type': 'visual',
                'full_embeddings': 'test',
                'seq_length': 100,
                'embedding_shape': '(100, 768)',
                'timestamp': '2024-01-01T00:00:00',
                'filename': 'test.pdf',
                'source_path': '/data/test.pdf'
            }]
        }

        chroma_client._text_collection.get.return_value = {
            'metadatas': [{
                'doc_id': 'test',
                'chunk_id': 0,
                'page': 1,
                'type': 'text',
                'full_embeddings': 'test',
                'seq_length': 64,
                'embedding_shape': '(64, 768)',
                'timestamp': '2024-01-01T00:00:00',
                'filename': 'test.pdf',
                'source_path': '/data/test.pdf'
            }]
        }

        report = manager.validate_collections()

        assert report['status'] == 'healthy'
        assert report['visual_collection']['exists'] is True
        assert report['text_collection']['exists'] is True

    def test_reset_collection(self, chroma_client):
        """Test collection reset."""
        manager = CollectionManager(chroma_client)

        chroma_client._visual_collection.count.return_value = 5
        chroma_client._visual_collection.get.return_value = {
            'ids': ['id1', 'id2', 'id3', 'id4', 'id5']
        }

        report = manager.reset_collection("visual", confirm=True)

        assert report['status'] == 'success'
        assert 'visual' in report['collections_reset']
        assert chroma_client._visual_collection.delete.called

    def test_reset_requires_confirmation(self, chroma_client):
        """Test reset requires explicit confirmation."""
        manager = CollectionManager(chroma_client)

        with pytest.raises(ValueError) as exc_info:
            manager.reset_collection("visual", confirm=False)

        assert "confirmation" in str(exc_info.value).lower()

    def test_get_document_list(self, chroma_client):
        """Test document list retrieval."""
        manager = CollectionManager(chroma_client)

        chroma_client._visual_collection.get.return_value = {
            'metadatas': [
                {
                    'doc_id': 'doc1',
                    'filename': 'test1.pdf',
                    'timestamp': '2024-01-01T00:00:00',
                    'source_path': '/data/test1.pdf'
                },
                {
                    'doc_id': 'doc2',
                    'filename': 'test2.pdf',
                    'timestamp': '2024-01-02T00:00:00',
                    'source_path': '/data/test2.pdf'
                }
            ]
        }

        chroma_client._text_collection.get.return_value = {
            'metadatas': [
                {'doc_id': 'doc1'},
                {'doc_id': 'doc1'},
                {'doc_id': 'doc2'}
            ]
        }

        docs = manager.get_document_list()

        assert len(docs) == 2
        assert docs[0]['doc_id'] == 'doc2'  # Sorted by timestamp, newest first
        assert docs[0]['text_chunks'] == 1
        assert docs[1]['text_chunks'] == 2

    def test_get_orphaned_embeddings(self, chroma_client):
        """Test orphaned embedding detection."""
        manager = CollectionManager(chroma_client)

        # Valid metadata
        valid_metadata = {
            'doc_id': 'doc1',
            'page': 1,
            'type': 'visual',
            'full_embeddings': 'test',
            'seq_length': 100,
            'embedding_shape': '(100, 768)',
            'timestamp': '2024-01-01',
            'filename': 'test.pdf',
            'source_path': '/data/test.pdf'
        }

        # Invalid metadata (missing fields)
        invalid_metadata = {
            'doc_id': 'doc2',
            'type': 'visual'
            # Missing required fields
        }

        chroma_client._visual_collection.get.return_value = {
            'ids': ['valid-id', 'invalid-id'],
            'metadatas': [valid_metadata, invalid_metadata]
        }

        chroma_client._text_collection.get.return_value = {
            'ids': [],
            'metadatas': []
        }

        orphans = manager.get_orphaned_embeddings()

        assert orphans['count'] == 1
        assert 'invalid-id' in orphans['visual_orphans']

    def test_cleanup_orphaned_embeddings(self, chroma_client):
        """Test orphaned embedding cleanup."""
        manager = CollectionManager(chroma_client)

        # Mock orphaned embeddings
        with patch.object(manager, 'get_orphaned_embeddings') as mock_orphans:
            mock_orphans.return_value = {
                'visual_orphans': ['orphan1', 'orphan2'],
                'text_orphans': ['orphan3'],
                'count': 3
            }

            report = manager.cleanup_orphaned_embeddings(confirm=True)

            assert report['status'] == 'success'
            assert report['visual_deleted'] == 2
            assert report['text_deleted'] == 1
            assert report['total_deleted'] == 3

    def test_export_collection_metadata(self, chroma_client):
        """Test metadata export."""
        manager = CollectionManager(chroma_client)

        visual_metadata = [{'doc_id': 'doc1', 'page': 1}]
        text_metadata = [{'doc_id': 'doc1', 'chunk_id': 0}]

        chroma_client._visual_collection.get.return_value = {
            'metadatas': visual_metadata
        }
        chroma_client._text_collection.get.return_value = {
            'metadatas': text_metadata
        }

        export = manager.export_collection_metadata(collection="all")

        assert export['visual'] == visual_metadata
        assert export['text'] == text_metadata
        assert 'export_timestamp' in export


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple operations."""

    def test_end_to_end_visual_workflow(
        self,
        chroma_client,
        sample_embeddings,
        sample_visual_metadata
    ):
        """Test complete visual embedding workflow."""
        # Store embedding
        embedding_id = chroma_client.add_visual_embedding(
            doc_id="test-doc",
            page=1,
            full_embeddings=sample_embeddings,
            metadata=sample_visual_metadata
        )

        assert embedding_id == "test-doc-page001"

        # Mock search to return this embedding
        compressed = compress_embeddings(sample_embeddings)
        chroma_client._visual_collection.query.return_value = {
            'ids': [[embedding_id]],
            'distances': [[0.1]],
            'metadatas': [[{
                'doc_id': 'test-doc',
                'full_embeddings': compressed,
                'embedding_shape': f"{sample_embeddings.shape}"
            }]],
            'embeddings': [[sample_embeddings[0].tolist()]]
        }

        # Search
        query = np.random.randn(768).astype(np.float32)
        results = chroma_client.search_visual(query, n_results=10)

        assert len(results) == 1
        assert results[0]['id'] == embedding_id

        # Retrieve full embeddings
        chroma_client._visual_collection.get.return_value = {
            'ids': [embedding_id],
            'metadatas': [{
                'full_embeddings': compressed,
                'embedding_shape': f"{sample_embeddings.shape}"
            }]
        }

        full_emb = chroma_client.get_full_embeddings(embedding_id, collection="visual")
        np.testing.assert_allclose(full_emb, sample_embeddings, rtol=1e-6)

    def test_multi_document_storage_and_deletion(
        self,
        chroma_client,
        sample_embeddings,
        sample_visual_metadata,
        sample_text_metadata
    ):
        """Test storing multiple documents and deleting one."""
        # Store multiple documents
        for doc_num in range(3):
            doc_id = f"doc{doc_num}"

            # Visual embeddings
            chroma_client.add_visual_embedding(
                doc_id=doc_id,
                page=1,
                full_embeddings=sample_embeddings,
                metadata=sample_visual_metadata
            )

            # Text embeddings
            chroma_client.add_text_embedding(
                doc_id=doc_id,
                chunk_id=0,
                full_embeddings=sample_embeddings,
                metadata=sample_text_metadata
            )

        # Delete one document
        chroma_client._visual_collection.get.return_value = {
            'ids': ['doc1-page001']
        }
        chroma_client._text_collection.get.return_value = {
            'ids': ['doc1-chunk0000']
        }

        visual_count, text_count = chroma_client.delete_document("doc1")

        assert visual_count == 1
        assert text_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
