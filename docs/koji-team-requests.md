# Koji Team — Request List from DocuSearch

**From:** DocuSearch (tkr-docusearch)
**To:** Koji Team (tkr-koji)
**Updated:** 2026-03-28 (Koji 0.2.0 retest)
**Original:** 2026-03-10

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

## 3. ~~Koji DB: `db.delete()` silently fails on file-based databases~~ RESOLVED

**Status: Fixed** (koji-core storage/mod.rs rewrite fallback, 2026-03-28)

`db.delete(table, filter)` silently returns `rows_deleted=0` on file-based databases when any column in the table is non-nullable (which all primary keys are). The same call works correctly on in-memory databases.

**Reproduction:**

```python
import koji
import pyarrow as pa

# Works in memory:
db_mem = koji.open_memory()
db_mem.sync_schema({"t": {"columns": {"id": {"type": "text", "primary_key": True}, "v": {"type": "text"}}}})
schema = pa.schema([pa.field("id", pa.utf8(), nullable=False), pa.field("v", pa.utf8())])
db_mem.insert("t", pa.table({"id": ["a", "b"], "v": ["1", "2"]}, schema=schema))
r = db_mem.delete("t", "id = 'a'")
print(r.rows_deleted)  # 1  ← correct

# Fails on file-based:
db_file = koji.open("/tmp/koji-delete-test")
db_file.sync_schema({"t": {"columns": {"id": {"type": "text", "primary_key": True}, "v": {"type": "text"}}}})
db_file.insert("t", pa.table({"id": ["a", "b"], "v": ["1", "2"]}, schema=schema))
r = db_file.delete("t", "id = 'a'")
print(r.rows_deleted)  # 0  ← silent failure, both rows still present
print(db_file.count("t"))  # 2  ← should be 1
```

**Impact:** Document deletion, cascade deletes, and relation cleanup all fail silently on file-based DBs. This affects `db.delete()`, `db.delete_cascade()`, and any operation that depends on Lance row deletion.

**Current workaround:** `_delete_where()` in our `KojiClient` — queries rows NOT matching the condition, truncates the table, then reinserts the survivors. This works but:
- Is not atomic (interrupted truncate+reinsert loses data)
- Has O(n) cost for every delete regardless of selectivity
- Cannot be wrapped in a transaction

**What we need:**
- `db.delete(table, filter)` returning correct `rows_deleted` count and actually removing rows on file-based databases
- This would also unblock `delete_cascade` (issue #4) since it depends on `db.delete()` internally

---

## 4. Koji DB: `delete_cascade` fails on tables with no data (empty `.lance` directory)

**Priority: Low — fallback handles it**
**Status: Partially fixed** (delete works, but cascade throws on never-inserted tables)

`db.delete_cascade(table, filter)` works correctly on in-memory databases (returns `CascadeDeleteResult` with accurate `total` and `deleted` counts) but fails on file-based databases. The root cause is the same as issue #3 — the underlying `db.delete()` calls silently fail.

**Reproduction:**

```python
import koji
import pyarrow as pa
from koji._koji import ForeignKey

db = koji.open("/tmp/koji-cascade-test")
db.sync_schema({
    "parents": {"columns": {"id": {"type": "text", "primary_key": True}, "name": {"type": "text"}}},
    "children": {"columns": {"id": {"type": "text", "primary_key": True}, "pid": {"type": "text"}}},
})
db.register_foreign_key(ForeignKey(
    table="children", columns=["pid"],
    references_table="parents", references_columns=["id"],
    on_delete="cascade",
))

ps = pa.schema([pa.field("id", pa.utf8(), nullable=False), pa.field("name", pa.utf8())])
cs = pa.schema([pa.field("id", pa.utf8(), nullable=False), pa.field("pid", pa.utf8())])
db.insert("parents", pa.table({"id": ["p1"], "name": ["alice"]}, schema=ps))
db.insert("children", pa.table({"id": ["c1", "c2"], "pid": ["p1", "p1"]}, schema=cs))

r = db.delete_cascade("parents", "id = 'p1'")
# In-memory: CascadeDeleteResult(total=3, deleted={"children": 2, "parents": 1})
# File-based: silently fails — parent and children still present
print(db.count("parents"))   # 1  ← should be 0
print(db.count("children"))  # 2  ← should be 0
```

**What we need:**
- Fix issue #3 (which fixes this automatically), OR
- Documentation confirming file-based cascade delete is unsupported so we can keep our manual cascade and remove the FK `on_delete="cascade"` declarations

---

## 5. Koji DB: Recursive CTEs do not support arithmetic in the recursive term

**Priority: Low — iterative workaround is adequate**
**Status: Still unsupported in Koji 0.2.0** (retested 2026-03-28)

Recursive CTEs reject any arithmetic expression in the recursive SELECT clause. This prevents common graph traversal patterns like tracking hop depth.

**Reproduction:**

```sql
WITH RECURSIVE traversal AS (
    SELECT dst AS doc_id, 1 AS depth
    FROM edges WHERE src = 'a'
    UNION
    SELECT e.dst, t.depth + 1          -- ← fails here
    FROM edges e JOIN traversal t ON e.src = t.doc_id
    WHERE t.depth < 3
)
SELECT * FROM traversal ORDER BY depth
```

**Error:**
```
RuntimeError: Recursive CTE error: Unsupported SQL construct in CTE 'unknown'
(stage: translation): Unsupported select item in join: UnnamedExpr(BinaryOp {
left: CompoundIdentifier([...depth...]), op: Plus, right: Value(Number("1", false)) })
```

**Impact:** Graph traversal (`get_related_documents`) uses iterative BFS queries (one SQL query per hop) instead of a single recursive CTE. Works correctly but is O(depth) round-trips.

**What we need:**
- Support for arithmetic expressions (`+`, `-`, `*`) in the recursive term of `WITH RECURSIVE`
- At minimum: integer addition for depth/hop counting

---

## 6. ~~Koji DB: `db.update()` unavailable~~ RESOLVED in 0.2.0

`db.update(table, assignments, filter)` now works correctly on both in-memory and file-based databases. Assignment values are plain Python values (str, int), not SQL expressions. Returns `UpdateResult(rows_updated, new_version)`.

DocuSearch's `update_document()` has been migrated from delete+reinsert to `db.update()`, fixing a data integrity bug where updating any document field would cascade-delete all child data (pages, chunks, relations).

---

## 7. ~~Koji DB: `db.graph()` not on sync Database~~ RESOLVED in 0.2.0

`db.graph()` is now exposed on the sync `Database` object. DocuSearch's `hasattr` guard has been removed.

---

## Summary

| # | Component | Issue | Priority | Status |
|---|-----------|-------|----------|--------|
| 1 | Shikomi | `EncodeImages` unimplemented | High | Open — blocks PDFs/images |
| 2 | Shikomi | Build feature flags unclear | Medium | Open |
| 3 | Koji DB | `db.delete()` silent failure on file DBs | — | **Resolved** (rewrite fallback) |
| 4 | Koji DB | `delete_cascade` on empty tables | Low | Partial — throws on never-inserted tables |
| 5 | Koji DB | Recursive CTE arithmetic unsupported | Low | Open — workaround adequate |
| 6 | Koji DB | `db.update()` unavailable | — | **Resolved in 0.2.0** |
| 7 | Koji DB | `db.graph()` missing from sync API | — | **Resolved in 0.2.0** |
