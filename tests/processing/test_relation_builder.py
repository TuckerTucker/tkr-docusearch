"""Tests for RelationBuilder — automatic relation detection at ingest time."""

import json

import pytest

from src.core.testing.mocks import MockKojiClient
from src.processing.relation_builder import RelationBuilder


@pytest.fixture
def client():
    """Create and open a MockKojiClient with pre-existing documents."""
    c = MockKojiClient()
    c.open()
    return c


@pytest.fixture
def builder(client):
    """Create a RelationBuilder backed by the mock client."""
    return RelationBuilder(storage_client=client)


class TestDetectVersionOf:
    """Tests for version_of relation detection."""

    def test_detect_version_of(self, client, builder):
        """Same base filename triggers version_of relation."""
        client.create_document(doc_id="doc-old", filename="report.pdf", format="pdf")
        client.create_document(doc_id="doc-new", filename="report.docx", format="docx")

        created = builder.build_relations(
            doc_id="doc-new", filename="report.docx", chunks=[],
        )

        assert len(created) == 1
        assert created[0]["relation_type"] == "version_of"
        assert created[0]["dst_doc_id"] == "doc-old"

    def test_detect_version_of_case_insensitive(self, client, builder):
        """Base filename comparison is case-insensitive."""
        client.create_document(doc_id="doc-old", filename="Report.PDF", format="pdf")
        client.create_document(doc_id="doc-new", filename="report.docx", format="docx")

        created = builder.build_relations(
            doc_id="doc-new", filename="report.docx", chunks=[],
        )

        assert len(created) == 1
        assert created[0]["relation_type"] == "version_of"

    def test_detect_version_of_no_match(self, client, builder):
        """Unique filename produces no version_of relations."""
        client.create_document(doc_id="doc-old", filename="budget.xlsx", format="xlsx")
        client.create_document(doc_id="doc-new", filename="report.pdf", format="pdf")

        created = builder.build_relations(
            doc_id="doc-new", filename="report.pdf", chunks=[],
        )

        version_rels = [r for r in created if r["relation_type"] == "version_of"]
        assert len(version_rels) == 0


class TestDetectReferences:
    """Tests for references relation detection."""

    def test_detect_references_found(self, client, builder):
        """Chunk text mentioning another document's filename triggers references."""
        client.create_document(doc_id="doc-budget", filename="budget.xlsx", format="xlsx")
        client.create_document(doc_id="doc-new", filename="report.pdf", format="pdf")

        chunks = [
            {"id": "doc-new-chunk0001", "text": "As detailed in budget.xlsx, costs rose 15%."},
        ]

        created = builder.build_relations(
            doc_id="doc-new", filename="report.pdf", chunks=chunks,
        )

        ref_rels = [r for r in created if r["relation_type"] == "references"]
        assert len(ref_rels) == 1
        assert ref_rels[0]["dst_doc_id"] == "doc-budget"

    def test_detect_references_no_match(self, client, builder):
        """Chunk text without known filenames produces no references."""
        client.create_document(doc_id="doc-other", filename="budget.xlsx", format="xlsx")
        client.create_document(doc_id="doc-new", filename="report.pdf", format="pdf")

        chunks = [
            {"id": "doc-new-chunk0001", "text": "Revenue increased significantly this quarter."},
        ]

        created = builder.build_relations(
            doc_id="doc-new", filename="report.pdf", chunks=chunks,
        )

        ref_rels = [r for r in created if r["relation_type"] == "references"]
        assert len(ref_rels) == 0

    def test_detect_references_deduplicates(self, client, builder):
        """Same filename in multiple chunks creates only one references relation."""
        client.create_document(doc_id="doc-budget", filename="budget.xlsx", format="xlsx")
        client.create_document(doc_id="doc-new", filename="report.pdf", format="pdf")

        chunks = [
            {"id": "doc-new-chunk0001", "text": "See budget.xlsx for details."},
            {"id": "doc-new-chunk0002", "text": "Refer to budget.xlsx again here."},
            {"id": "doc-new-chunk0003", "text": "As budget.xlsx shows clearly."},
        ]

        created = builder.build_relations(
            doc_id="doc-new", filename="report.pdf", chunks=chunks,
        )

        ref_rels = [r for r in created if r["relation_type"] == "references"]
        assert len(ref_rels) == 1


class TestBuildRelations:
    """Tests for the top-level build_relations method."""

    def test_failure_isolation(self, client):
        """create_relation failure does not propagate from build_relations."""
        client.create_document(doc_id="doc-new", filename="report.pdf", format="pdf")

        # Create a builder with a client whose create_relation always raises
        class BrokenClient:
            def list_documents(self, **kwargs):
                return [{"doc_id": "doc-old", "filename": "report.docx"}]

            def create_relation(self, **kwargs):
                raise RuntimeError("DB on fire")

        builder = RelationBuilder(storage_client=BrokenClient())
        # Should not raise
        created = builder.build_relations(
            doc_id="doc-new", filename="report.pdf", chunks=[],
        )
        assert len(created) == 0

    def test_returns_created_relations(self, client, builder):
        """Return value contains all successfully created relations."""
        client.create_document(doc_id="doc-old", filename="report.docx", format="docx")
        client.create_document(doc_id="doc-budget", filename="budget.xlsx", format="xlsx")
        client.create_document(doc_id="doc-new", filename="report.pdf", format="pdf")

        chunks = [
            {"id": "doc-new-chunk0001", "text": "Refer to budget.xlsx for numbers."},
        ]

        created = builder.build_relations(
            doc_id="doc-new", filename="report.pdf", chunks=chunks,
        )

        types = {r["relation_type"] for r in created}
        assert "version_of" in types
        assert "references" in types
        assert all("src_doc_id" in r for r in created)
        assert all("dst_doc_id" in r for r in created)


class TestDetectSeriesMember:
    """Tests for series_member relation detection (shared artist + album)."""

    def test_series_member_matching(self, client, builder):
        """Documents sharing artist and album get bidirectional series_member edges."""
        meta = json.dumps({"audio_artist": "Band Name", "audio_album": "Album One"})
        client.create_document("doc-1", "track1.mp3", "mp3", metadata=meta)
        client.create_document("doc-2", "track2.mp3", "mp3", metadata=meta)
        client.create_document("doc-3", "track3.mp3", "mp3", metadata=meta)

        created = builder.build_relations(
            doc_id="doc-3",
            filename="track3.mp3",
            chunks=[],
            doc_metadata={"audio_artist": "Band Name", "audio_album": "Album One"},
        )

        series_rels = [r for r in created if r["relation_type"] == "series_member"]
        # 2 existing docs x 2 directions = 4 series_member edges
        assert len(series_rels) == 4

        # Verify both directions exist for each pair
        pairs = {(r["src_doc_id"], r["dst_doc_id"]) for r in series_rels}
        assert ("doc-3", "doc-1") in pairs
        assert ("doc-1", "doc-3") in pairs
        assert ("doc-3", "doc-2") in pairs
        assert ("doc-2", "doc-3") in pairs

    def test_series_member_different_album(self, client, builder):
        """Same artist but different album produces no series_member edges."""
        meta1 = json.dumps({"audio_artist": "Band Name", "audio_album": "Album One"})
        meta2 = json.dumps({"audio_artist": "Band Name", "audio_album": "Album Two"})
        client.create_document("doc-1", "track1.mp3", "mp3", metadata=meta1)
        client.create_document("doc-2", "track2.mp3", "mp3", metadata=meta2)

        created = builder.build_relations(
            doc_id="doc-2",
            filename="track2.mp3",
            chunks=[],
            doc_metadata={"audio_artist": "Band Name", "audio_album": "Album Two"},
        )

        series_rels = [r for r in created if r["relation_type"] == "series_member"]
        assert len(series_rels) == 0

    def test_series_member_no_metadata(self, client, builder):
        """Passing doc_metadata=None does not crash, produces no series_member edges."""
        meta = json.dumps({"audio_artist": "Band Name", "audio_album": "Album One"})
        client.create_document("doc-1", "track1.mp3", "mp3", metadata=meta)
        client.create_document("doc-2", "track2.mp3", "mp3")

        created = builder.build_relations(
            doc_id="doc-2",
            filename="track2.mp3",
            chunks=[],
            doc_metadata=None,
        )

        series_rels = [r for r in created if r["relation_type"] == "series_member"]
        assert len(series_rels) == 0


class TestDetectSameAuthor:
    """Tests for same_author relation detection (shared audio_artist)."""

    def test_same_author_matching(self, client, builder):
        """Documents with same audio_artist get bidirectional same_author edges."""
        meta1 = json.dumps({"audio_artist": "John Smith"})
        meta2 = json.dumps({"audio_artist": "John Smith"})
        client.create_document("doc-1", "track1.mp3", "mp3", metadata=meta1)
        client.create_document("doc-2", "track2.mp3", "mp3", metadata=meta2)

        created = builder.build_relations(
            doc_id="doc-2",
            filename="track2.mp3",
            chunks=[],
            doc_metadata={"audio_artist": "John Smith"},
        )

        author_rels = [r for r in created if r["relation_type"] == "same_author"]
        assert len(author_rels) == 2

        pairs = {(r["src_doc_id"], r["dst_doc_id"]) for r in author_rels}
        assert ("doc-2", "doc-1") in pairs
        assert ("doc-1", "doc-2") in pairs

    def test_same_author_case_insensitive(self, client, builder):
        """Artist comparison is case-insensitive: 'John Smith' matches 'john smith'."""
        meta1 = json.dumps({"audio_artist": "John Smith"})
        client.create_document("doc-1", "track1.mp3", "mp3", metadata=meta1)
        client.create_document("doc-2", "track2.mp3", "mp3")

        created = builder.build_relations(
            doc_id="doc-2",
            filename="track2.mp3",
            chunks=[],
            doc_metadata={"audio_artist": "john smith"},
        )

        author_rels = [r for r in created if r["relation_type"] == "same_author"]
        assert len(author_rels) == 2

        pairs = {(r["src_doc_id"], r["dst_doc_id"]) for r in author_rels}
        assert ("doc-2", "doc-1") in pairs
        assert ("doc-1", "doc-2") in pairs


class TestDetectSameGenre:
    """Tests for same_genre relation detection (shared genre tokens)."""

    def test_same_genre_matching(self, client, builder):
        """Documents with same genre get bidirectional same_genre edges."""
        meta1 = json.dumps({"audio_genre": "Rock"})
        client.create_document("doc-1", "track1.mp3", "mp3", metadata=meta1)
        client.create_document("doc-2", "track2.mp3", "mp3")

        created = builder.build_relations(
            doc_id="doc-2",
            filename="track2.mp3",
            chunks=[],
            doc_metadata={"audio_genre": "Rock"},
        )

        genre_rels = [r for r in created if r["relation_type"] == "same_genre"]
        assert len(genre_rels) == 2

        pairs = {(r["src_doc_id"], r["dst_doc_id"]) for r in genre_rels}
        assert ("doc-2", "doc-1") in pairs
        assert ("doc-1", "doc-2") in pairs

    def test_same_genre_multi_value(self, client, builder):
        """Semi-colon separated genre 'Rock; Alternative' matches 'Rock'."""
        meta1 = json.dumps({"audio_genre": "Rock"})
        client.create_document("doc-1", "track1.mp3", "mp3", metadata=meta1)
        client.create_document("doc-2", "track2.mp3", "mp3")

        created = builder.build_relations(
            doc_id="doc-2",
            filename="track2.mp3",
            chunks=[],
            doc_metadata={"audio_genre": "Rock; Alternative"},
        )

        genre_rels = [r for r in created if r["relation_type"] == "same_genre"]
        assert len(genre_rels) == 2

        pairs = {(r["src_doc_id"], r["dst_doc_id"]) for r in genre_rels}
        assert ("doc-2", "doc-1") in pairs
        assert ("doc-1", "doc-2") in pairs

    def test_same_genre_no_match(self, client, builder):
        """Different genres produce no same_genre edges."""
        meta1 = json.dumps({"audio_genre": "Jazz"})
        client.create_document("doc-1", "track1.mp3", "mp3", metadata=meta1)
        client.create_document("doc-2", "track2.mp3", "mp3")

        created = builder.build_relations(
            doc_id="doc-2",
            filename="track2.mp3",
            chunks=[],
            doc_metadata={"audio_genre": "Rock"},
        )

        genre_rels = [r for r in created if r["relation_type"] == "same_genre"]
        assert len(genre_rels) == 0


class TestBuildRelationsBackwardCompat:
    """Tests for backward compatibility of build_relations."""

    def test_no_metadata_no_crash(self, client, builder):
        """Calling build_relations without doc_metadata skips metadata detectors safely."""
        client.create_document("doc-1", "report.pdf", "pdf")
        client.create_document("doc-2", "summary.pdf", "pdf")

        # Call without doc_metadata — default is None
        created = builder.build_relations(
            doc_id="doc-2",
            filename="summary.pdf",
            chunks=[],
        )

        # Should succeed; no metadata-based relations created
        assert isinstance(created, list)
        # No series_member, same_author, or same_genre edges
        metadata_types = {"series_member", "same_author", "same_genre"}
        for rel in created:
            assert rel["relation_type"] not in metadata_types
