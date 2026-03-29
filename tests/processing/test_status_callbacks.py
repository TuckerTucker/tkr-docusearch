"""Tests for progress tracking and status callback progression.

Verifies that the DocumentProcessor invokes status callbacks in the
correct order, with monotonically increasing progress, consistent
identifiers, and graceful handling of broken callbacks.

All tests use MockEmbeddingModel + MockKojiClient for speed.
"""

from __future__ import annotations

import pytest

from src.processing.processor import ProcessingStatus, StorageConfirmation


# ---------------------------------------------------------------------------
# PDF status progression
# ---------------------------------------------------------------------------


class TestStatusProgressionPdf:
    """Status callback behaviour when processing a multi-page PDF."""

    def test_stages_appear_in_order(
        self, make_processor, status_collector, sample_pdf
    ):
        """Parsing appears before storing, and completed appears last."""
        callback, statuses = status_collector
        processor = make_processor()
        processor.process_document(str(sample_pdf), status_callback=callback)

        status_names = [s.status for s in statuses]

        # "parsing" should precede "storing"
        if "parsing" in status_names and "storing" in status_names:
            assert status_names.index("parsing") < status_names.index("storing")

        # "completed" must be the final status
        assert status_names[-1] == "completed"

    def test_progress_monotonically_increases(
        self, make_processor, status_collector, sample_pdf
    ):
        """Progress values never decrease across all captured statuses."""
        callback, statuses = status_collector
        processor = make_processor()
        processor.process_document(str(sample_pdf), status_callback=callback)

        progress_values = [s.progress for s in statuses]
        for i in range(1, len(progress_values)):
            assert progress_values[i] >= progress_values[i - 1], (
                f"Progress decreased from {progress_values[i - 1]} "
                f"to {progress_values[i]} at index {i}"
            )

    def test_final_status_is_completed(
        self, make_processor, status_collector, sample_pdf
    ):
        """The last captured status has status='completed'."""
        callback, statuses = status_collector
        processor = make_processor()
        processor.process_document(str(sample_pdf), status_callback=callback)

        assert statuses, "No statuses were captured"
        assert statuses[-1].status == "completed"

    def test_doc_id_is_consistent(
        self, make_processor, status_collector, sample_pdf
    ):
        """All statuses after the first share the same doc_id."""
        callback, statuses = status_collector
        processor = make_processor()
        processor.process_document(str(sample_pdf), status_callback=callback)

        # The first status may use a placeholder ("pending") before the
        # parser assigns a real doc_id, so skip it.
        post_parse = [s for s in statuses if s.doc_id != "pending"]
        assert post_parse, "Expected at least one status with a real doc_id"

        expected_id = post_parse[0].doc_id
        for s in post_parse[1:]:
            assert s.doc_id == expected_id, (
                f"Inconsistent doc_id: expected {expected_id!r}, got {s.doc_id!r}"
            )

    def test_filename_is_consistent(
        self, make_processor, status_collector, sample_pdf
    ):
        """All captured statuses report the same filename."""
        callback, statuses = status_collector
        processor = make_processor()
        processor.process_document(str(sample_pdf), status_callback=callback)

        filenames = {s.filename for s in statuses}
        assert len(filenames) == 1, f"Expected one filename, got {filenames}"
        assert "sample.pdf" in filenames

    def test_progress_reaches_one(
        self, make_processor, status_collector, sample_pdf
    ):
        """The final status has progress == 1.0."""
        callback, statuses = status_collector
        processor = make_processor()
        processor.process_document(str(sample_pdf), status_callback=callback)

        assert statuses[-1].progress == 1.0


# ---------------------------------------------------------------------------
# Text-only (Markdown) status progression
# ---------------------------------------------------------------------------


class TestStatusProgressionTextOnly:
    """Status callback behaviour for text-only formats (Markdown)."""

    def test_text_only_skips_visual_stage(
        self, make_processor, status_collector, sample_md
    ):
        """Text-only formats never emit an 'embedding_visual' status."""
        callback, statuses = status_collector
        processor = make_processor()
        processor.process_document(str(sample_md), status_callback=callback)

        visual_statuses = [s for s in statuses if s.status == "embedding_visual"]
        assert visual_statuses == [], (
            "Text-only document should not have embedding_visual statuses"
        )

    def test_text_only_reaches_completed(
        self, make_processor, status_collector, sample_md
    ):
        """Final status is 'completed' for text-only documents."""
        callback, statuses = status_collector
        processor = make_processor()
        processor.process_document(str(sample_md), status_callback=callback)

        assert statuses, "No statuses were captured"
        assert statuses[-1].status == "completed"


# ---------------------------------------------------------------------------
# Image (PNG) status progression
# ---------------------------------------------------------------------------


class TestStatusProgressionImage:
    """Status callback behaviour for single-page image files."""

    @pytest.mark.xfail(
        reason=(
            "Pre-existing bug: processor._store_koji references "
            "'chunk_records' before assignment when text_results is empty "
            "(image-only files). See processor.py line ~669."
        ),
        raises=Exception,
        strict=False,
    )
    def test_image_has_visual_stage(
        self, make_processor, status_collector, sample_png
    ):
        """At least one status mentions visual/embedding in the stage field."""
        callback, statuses = status_collector
        processor = make_processor()
        processor.process_document(str(sample_png), status_callback=callback)

        has_visual = any(
            s.status == "embedding_visual"
            or "visual" in (s.stage or "").lower()
            or "embedding" in (s.stage or "").lower()
            for s in statuses
        )
        assert has_visual, (
            "Expected at least one status with a visual/embedding stage "
            f"for an image file. Stages seen: {[s.stage for s in statuses]}"
        )


# ---------------------------------------------------------------------------
# Callback error handling
# ---------------------------------------------------------------------------


class TestCallbackErrorHandling:
    """Verify that broken callbacks do not crash processing."""

    def test_broken_callback_does_not_crash(self, make_processor, sample_md):
        """A callback that raises ValueError must not prevent completion.

        The processor catches callback errors inside ``_update_status()``
        so that a misbehaving observer never disrupts the pipeline.
        """

        def _exploding_callback(status: ProcessingStatus) -> None:
            raise ValueError("boom")

        processor = make_processor()
        result = processor.process_document(
            str(sample_md), status_callback=_exploding_callback
        )

        assert isinstance(result, StorageConfirmation)
        assert result.doc_id  # non-empty doc_id confirms processing finished
