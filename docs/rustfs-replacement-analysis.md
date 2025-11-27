# RustFS vs Copyparty: Replacement Analysis

> **Date:** 2025-11-27
> **Status:** Research / Understanding Only
> **Branch:** `rustfs`

## Current Copyparty Role in DocuSearch

Copyparty serves as the **file upload and asset serving layer**:

| Function | How Copyparty Does It |
|----------|----------------------|
| **File Upload** | Web UI + HTTP POST on port 8000 |
| **Upload Trigger** | `--xau /hooks/on_upload.py` (executes Python script) |
| **Delete Trigger** | `--xad /hooks/on_delete.py` (executes Python script) |
| **Asset Serving** | Direct HTTP GET from `/uploads/{doc_id}/...` |
| **Auth** | Basic auth (`admin:admin`, `uploader:docusearch2024`) |
| **File Delete API** | `DELETE /uploads/{filename}` |

### Key Integration Points

- **Docker:** `docker/Dockerfile.copyparty`, `docker/docker-compose.yml`
- **Hooks:** `/hooks/on_upload.py`, `/docker/data/copyparty/hooks/on_delete.py`
- **URL Config:** `src/config/urls.py`, `frontend/src/config/urls.js`
- **Worker Endpoints:** `POST /process`, `POST /delete`

---

## What is RustFS?

RustFS is a **high-performance, S3-compatible object storage system** built in Rust. It's architecturally similar to **MinIO**, not copyparty.

| Attribute | Value |
|-----------|-------|
| **Type** | Distributed object storage (S3-compatible) |
| **Ports** | 9000 (console), 9001 (API) |
| **Protocol** | S3 API |
| **Status** | **Beta / Technical Preview** (not production-ready) |
| **Performance** | Claims 2.3x faster than MinIO for 4KB objects |
| **License** | Apache 2.0 |

### RustFS Key Features

- **High Performance**: Built with Rust for speed and memory safety
- **Distributed Architecture**: Scalable, fault-tolerant design
- **S3 Compatibility**: Works with existing S3-compatible applications
- **Zero-Master Architecture**: Avoids centralized metadata server failures
- **WORM Support**: Write Once, Read Many for data protection
- **Cross-Platform**: Windows, macOS, Linux
- **Docker Support**: Pre-built containers available

### Installation Options

1. **One-Click Script**: Automated installation via shell script
2. **Docker**: Pre-built containers (ports 9000/9001)
3. **Source Build**: Multi-architecture compilation
4. **Kubernetes**: Helm chart deployment

---

## Key Architectural Differences

| Aspect | Copyparty | RustFS |
|--------|-----------|--------|
| **Paradigm** | File server with web UI | S3-compatible object storage |
| **API** | HTTP REST (custom) | S3 API standard |
| **Webhooks** | Direct script execution (`--xau`, `--xad`) | Bucket notifications to external targets |
| **URL Pattern** | `/uploads/file.pdf` | `s3://bucket/key` or presigned URLs |
| **Clients** | Browser, curl | AWS SDK, mc CLI, any S3 client |
| **Scale** | Single node | Distributed multi-node |

---

## RustFS Event Notification System

RustFS supports **bucket notifications** similar to AWS S3 and MinIO:

### Supported Targets

- Webhook endpoints (HTTP/HTTPS)
- Kafka
- Elasticsearch
- PostgreSQL

### Configuration Approach

```bash
# Set webhook endpoint
mc admin config set ALIAS/ notify_webhook:IDENTIFIER endpoint="http://worker:8002/process"

# Subscribe bucket to events
mc event add ALIAS/uploads arn:minio:sqs::primary:webhook --event put --suffix .pdf
```

This replaces copyparty's `--xau` hook mechanism but requires more configuration.

---

## Migration Complexity Assessment

### What Would Need to Change

| Component | Current (Copyparty) | Required for RustFS |
|-----------|---------------------|---------------------|
| **Upload flow** | POST to `/` with form | S3 PutObject or presigned URL |
| **Webhook handler** | Receives env vars from copyparty | Receives S3 event JSON payload |
| **Asset URLs** | `http://localhost:8000/uploads/doc/page.png` | Presigned S3 URLs or proxy |
| **File deletion** | HTTP DELETE | S3 DeleteObject |
| **Frontend changes** | Minimal | URL pattern changes throughout |
| **Docker setup** | Single container | RustFS container + config |

### Hook Migration

**Current copyparty hook** receives environment variables:

```python
# on_upload.py receives:
fn = os.environ.get("fn")  # filename
ap = os.environ.get("ap")  # absolute path
```

**RustFS webhook** receives S3 event JSON:

```json
{
  "EventName": "s3:ObjectCreated:Put",
  "Key": "uploads/document.pdf",
  "Records": [...]
}
```

---

## Concerns & Gaps

### 1. Beta Status

RustFS explicitly states: *"Not yet recommended for critical production workloads"*

### 2. S3 URL Patterns

The current frontend expects direct URLs like:

```
http://localhost:8000/uploads/{doc_id}/images/page-001.png
```

S3-style access requires either:
- Presigned URLs (temporary, expiring)
- A reverse proxy to translate paths
- Public bucket access (security concern)

### 3. Simplicity Trade-off

Copyparty is a **simple file server** that "just works" for this use case. RustFS is enterprise-grade distributed storage - potentially overkill for a document processing pipeline.

### 4. Direct Script Execution

Copyparty's `--xau` directly runs Python scripts in-container. RustFS only supports external webhook endpoints - requires the worker to be running and reachable.

---

## Summary: Should You Replace Copyparty with RustFS?

| Factor | Assessment |
|--------|------------|
| **Maturity** | Copyparty is stable; RustFS is beta |
| **Complexity** | RustFS adds significant complexity |
| **Features needed** | You're using ~10% of what RustFS offers |
| **Migration effort** | High - touches frontend, hooks, all URL generation |
| **Benefits** | S3 compatibility, potential for scale |

### Recommendation

RustFS solves a **different problem** (distributed object storage) than what you need (simple file upload server with webhooks). Unless you need:

- Multi-node distributed storage
- S3 API compatibility for external tools
- Migration path to cloud S3

...staying with copyparty is likely the simpler choice for this document processing use case.

### If Proceeding with Migration

The migration would require:

1. Rewriting hooks to handle S3 event JSON
2. Adding presigned URL generation or a proxy layer
3. Updating all asset URL references in frontend/backend
4. Testing the webhook delivery reliability (S3 notifications vs direct script execution)

---

## References

- [RustFS GitHub](https://github.com/rustfs/rustfs)
- [RustFS Documentation](https://docs.rustfs.com/installation/)
- [RustFS Logging & Auditing](https://docs.rustfs.com/features/logging/)
- [MinIO Webhook Notifications](https://min.io/docs/minio/linux/administration/monitoring/publish-events-to-webhook.html)
- [Managing RustFS with mc CLI](https://docs.rustfs.com/developer/mc.html)
