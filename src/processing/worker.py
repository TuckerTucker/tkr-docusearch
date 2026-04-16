"""Headless document processing worker.

Polls the ``processing_jobs`` table in Koji for queued work, processes
files sequentially through shikomi, and stores results in Koji.

No HTTP server, no event loop, no uvicorn.  Koji's Tokio runtime and
PyTorch MPS run uncontested in this process.

Usage:
    python3 -m tkr_docusearch.processing.worker
"""

from __future__ import annotations

import hashlib
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any, Optional

import structlog

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEVICE = os.getenv("DEVICE", "mps")
QUANTIZATION = os.getenv("MODEL_PRECISION", "fp16")
POLL_INTERVAL = float(os.getenv("WORKER_POLL_INTERVAL", "2.0"))
DB_PATH = os.getenv("KOJI_DB_PATH", "./data/koji.db")


# ---------------------------------------------------------------------------
# Job processing
# ---------------------------------------------------------------------------


def process_job(
    job: dict[str, Any],
    processor: Any,
    koji_client: Any,
) -> None:
    """Process a single job from the queue.

    Calls ``DocumentProcessor.process_document()`` with a status callback
    that writes progress to the ``processing_jobs`` table in Koji.

    Args:
        job: Job dict from ``koji_client.claim_next_job()``.
        processor: ``DocumentProcessor`` instance.
        koji_client: ``KojiClient`` instance for status updates.
    """
    doc_id = job["doc_id"]
    filename = job["filename"]
    file_path = job["file_path"]
    project_id = job.get("project_id", "default")

    logger.info(
        "worker.processing",
        doc_id=doc_id,
        filename=filename,
    )

    def _status_callback(status: Any) -> None:
        """Forward processing status to Koji."""
        try:
            koji_client.update_job_progress(
                doc_id,
                status.status,
                status.progress,
                status.stage,
            )
        except Exception:
            pass  # non-critical — don't interrupt processing

    try:
        result = processor.process_document(
            file_path=file_path,
            status_callback=_status_callback,
            project_id=project_id,
        )

        koji_client.complete_job(doc_id)

        logger.info(
            "worker.completed",
            doc_id=result.doc_id,
            filename=filename,
            chunks=len(result.text_ids),
            pages=len(result.visual_ids),
        )

    except Exception as exc:
        error_msg = str(exc)
        koji_client.fail_job(doc_id, error_msg)

        logger.error(
            "worker.failed",
            doc_id=doc_id,
            filename=filename,
            error=error_msg,
            exc_info=True,
        )


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the processing worker.

    Initializes all components (Koji, ShikomiIngester, DocumentProcessor),
    then enters a poll loop that claims and processes jobs sequentially.
    Exits cleanly on SIGTERM or SIGINT.
    """
    running = True

    def _shutdown(signum: int, frame: Any) -> None:
        nonlocal running
        sig_name = signal.Signals(signum).name
        logger.info("worker.shutdown_requested", signal=sig_name)
        running = False

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    # -- Initialize components -----------------------------------------------

    logger.info("worker.starting", device=DEVICE, quantization=QUANTIZATION)

    from ..config.koji_config import KojiConfig
    from ..storage.koji_client import KojiClient

    koji_config = KojiConfig(db_path=DB_PATH)
    koji_client = KojiClient(koji_config)
    koji_client.open()
    logger.info("worker.koji_opened", db_path=DB_PATH)

    from shikomi.config import EnrichmentConfig, RenderConfig
    from shikomi.parser.renderer import LibreOfficeRenderer

    from ..config.processing_config import ProcessingConfig
    from .processor import DocumentProcessor
    from .shikomi_ingester import ShikomiIngester

    processing_config = ProcessingConfig()
    renderer = LibreOfficeRenderer(RenderConfig(dpi=processing_config.page_render_dpi))

    enrichment_config = EnrichmentConfig(
        enabled=processing_config.enrichment_enabled,
        model_repo=processing_config.enrichment_model_repo,
    )
    logger.info(
        "worker.enrichment_config",
        enabled=enrichment_config.enabled,
        model_repo=enrichment_config.model_repo,
        index_captions=processing_config.enrichment_index_captions,
    )

    ingester = ShikomiIngester(
        device=DEVICE,
        quantization=QUANTIZATION,
        generate_vtt=True,
        generate_markdown=True,
        db=koji_client,
        renderer=renderer,
        enrichment_config=enrichment_config,
    )
    ingester.connect()
    logger.info("worker.ingester_connected")

    processor = DocumentProcessor(
        ingester=ingester,
        storage_client=koji_client,
        index_enrichment_captions=processing_config.enrichment_index_captions,
    )
    logger.info("worker.ready", poll_interval=POLL_INTERVAL)

    # -- Poll loop -----------------------------------------------------------

    jobs_processed = 0
    try:
        while running:
            job = koji_client.claim_next_job()

            if job is None:
                time.sleep(POLL_INTERVAL)
                continue

            process_job(job, processor, koji_client)
            jobs_processed += 1

    finally:
        logger.info(
            "worker.shutting_down",
            jobs_processed=jobs_processed,
        )
        ingester.close()
        koji_client.close()
        logger.info("worker.stopped")


if __name__ == "__main__":
    main()
