# Koji Team — Request List from DocuSearch

**From:** DocuSearch (tkr-docusearch)
**To:** Koji Team (tkr-koji)
**Date:** 2026-03-10

DocuSearch has completed its migration from ChromaDB/ColPali to Koji + Shikomi. The text embedding pipeline works end-to-end, but we're blocked or working around issues in three areas.

---

## 1. Shikomi: `EncodeImages` is unimplemented

**Priority: High — blocks core functionality**

Our document pipeline processes PDFs and images by generating visual (page-level) embeddings via `ShikomiClient.embed_images()`. This calls the `EncodeImages` RPC, which currently returns `UNIMPLEMENTED`.

**Impact:** All PDF and image documents fail at the visual embedding stage. Only text-based formats (markdown, CSV, plain text, audio transcripts) can be processed end-to-end.

**What we need:**
- `EncodeImages` RPC implemented in `shikomi/src/server/service.rs`
- Input: raw image bytes (PNG/JPEG), per the existing `ImageEncodeRequest` proto
- Output: `MultiVectorEmbedding` in the same vector space as text embeddings (cross-modal retrieval)
- Our client (`src/embeddings/shikomi_client.py`) already sends PIL images as PNG bytes — the proto and client are ready

**Workaround (current):** None. Visual documents simply fail.

---

## 2. Shikomi: Python feature flag unclear in binary

**Priority: Medium — affects embedding quality**

The `shikomi-worker` binary we built (`cargo build --release --features server -p shikomi`) does not expose `--device` or any indication of whether the `python` feature was included. Without the `python` feature, `LocalEmbeddingWorker` generates deterministic mock embeddings even when `--mock` is **not** passed.

**What we need:**
- Clarity on whether `--features server` includes real model loading or requires `--features server,python`
- `shikomi-worker --version` or `--info` output that reports: compiled features, device backend (MPS/CUDA/CPU), and whether the model is actually loaded
- Documentation on the correct build command for production use on Apple Silicon

---

## 3. Koji DB: `db.delete()` silently fails on file-based databases

**Priority: Medium — workaround exists but is fragile**

`db.delete(table, condition)` returns `rows_deleted=0` without error when any column in the table is non-nullable (which all PKs are). This is a Lance storage bug.

**Impact:** Document deletion, cascade deletes, and relation cleanup all fail silently.

**Current workaround:** `_delete_where()` in our `KojiClient` — queries non-matching rows, truncates the table, then reinserts. This works but is not atomic and risks data loss on interruption.

**What we need:**
- `db.delete()` working correctly on file-based databases with non-nullable columns
- Or: an official `db.delete_where(table, condition)` API that handles this internally

---

## 4. Koji DB: `delete_cascade` does not work on file-based databases

**Priority: Low — manual cascade works**

Foreign keys are defined with `on_delete="cascade"` in our schema, but cascade deletes don't fire on file-based DBs. We manually delete children before parents in `delete_document()`.

**What we need:**
- `delete_cascade` support for file-based databases
- Or: documentation confirming this is not supported, so we can remove the FK cascade declarations and keep our manual approach

---

## Summary

| # | Component | Issue | Priority | Blocking? |
|---|-----------|-------|----------|-----------|
| 1 | Shikomi | `EncodeImages` unimplemented | High | Yes — PDFs and images |
| 2 | Shikomi | Build feature flags unclear | Medium | Possibly — may be running mock embeddings unknowingly |
| 3 | Koji DB | `db.delete()` silent failure | Medium | No — workaround in place |
| 4 | Koji DB | `delete_cascade` not working | Low | No — manual cascade works |
