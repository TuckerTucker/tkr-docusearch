"""Tests for blob format compatibility between shikomi-ingest and koji_client.

Verifies that MultiVectorEmbedding.to_blob() and pack_multivec() produce
identical binary formats, and that round-tripping between the two works.
"""

import struct

import numpy as np
import pytest

from shikomi_ingest.types import MultiVectorEmbedding
from src.storage.koji_client import pack_multivec, unpack_multivec


@pytest.fixture
def sample_data():
    """Create deterministic sample embedding data."""
    rng = np.random.default_rng(42)
    return rng.standard_normal((10, 128)).astype(np.float32)


@pytest.fixture
def sample_embedding(sample_data):
    """Create a MultiVectorEmbedding from sample data."""
    return MultiVectorEmbedding(
        num_tokens=10,
        dim=128,
        data=sample_data,
    )


class TestBlobFormatEquivalence:
    """Verify to_blob() and pack_multivec() produce identical output."""

    def test_to_blob_matches_pack_multivec(self, sample_data, sample_embedding):
        """MultiVectorEmbedding.to_blob() produces the same bytes as pack_multivec()."""
        blob_from_shikomi = sample_embedding.to_blob()
        blob_from_koji = pack_multivec(sample_data.tolist())

        assert blob_from_shikomi == blob_from_koji

    def test_header_format_consistent(self, sample_embedding):
        """Both serializations use the same u32-LE header layout."""
        blob = sample_embedding.to_blob()
        num_tokens, dim = struct.unpack("<II", blob[:8])

        assert num_tokens == 10
        assert dim == 128

    def test_small_matrix(self):
        """Equivalence holds for a small known matrix."""
        data = np.array(
            [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float32
        )
        emb = MultiVectorEmbedding(num_tokens=2, dim=3, data=data)

        assert emb.to_blob() == pack_multivec(data.tolist())


class TestRoundTripToBlobUnpack:
    """Round-trip: shikomi to_blob() -> koji unpack_multivec()."""

    def test_data_survives_round_trip(self, sample_data, sample_embedding):
        """to_blob() followed by unpack_multivec() recovers the original data."""
        blob = sample_embedding.to_blob()
        recovered = unpack_multivec(blob)

        assert len(recovered) == 10
        assert len(recovered[0]) == 128

        recovered_np = np.array(recovered, dtype=np.float32)
        np.testing.assert_allclose(recovered_np, sample_data, atol=1e-7)

    def test_single_token(self):
        """Round-trip works for single-token embedding."""
        data = np.array([[0.5, -0.5, 1.0]], dtype=np.float32)
        emb = MultiVectorEmbedding(num_tokens=1, dim=3, data=data)

        blob = emb.to_blob()
        recovered = unpack_multivec(blob)

        assert len(recovered) == 1
        np.testing.assert_allclose(recovered[0], [0.5, -0.5, 1.0], atol=1e-7)


class TestRoundTripPackFromBlob:
    """Round-trip: koji pack_multivec() -> shikomi from_blob()."""

    def test_data_survives_round_trip(self, sample_data):
        """pack_multivec() followed by from_blob() recovers the original data."""
        blob = pack_multivec(sample_data.tolist())
        recovered = MultiVectorEmbedding.from_blob(blob)

        assert recovered.num_tokens == 10
        assert recovered.dim == 128
        np.testing.assert_allclose(recovered.data, sample_data, atol=1e-7)

    def test_single_token(self):
        """Round-trip works for single-token embedding."""
        data = [[0.5, -0.5, 1.0]]
        blob = pack_multivec(data)
        recovered = MultiVectorEmbedding.from_blob(blob)

        assert recovered.num_tokens == 1
        assert recovered.dim == 3
        np.testing.assert_allclose(
            recovered.data, np.array(data, dtype=np.float32), atol=1e-7
        )

    def test_large_embedding(self):
        """Round-trip works for a large embedding matrix."""
        rng = np.random.default_rng(99)
        data = rng.standard_normal((512, 128)).astype(np.float32)

        blob = pack_multivec(data.tolist())
        recovered = MultiVectorEmbedding.from_blob(blob)

        assert recovered.num_tokens == 512
        assert recovered.dim == 128
        np.testing.assert_allclose(recovered.data, data, atol=1e-7)
