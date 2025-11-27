# RustFS Replacement Guide: Copyparty to RustFS

> **Date:** 2025-11-27
> **Type:** Wholesale Replacement (no migration, no backwards compatibility)
> **Branch:** `rustfs`

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Comparison](#architecture-comparison)
3. [RustFS Technical Specifications](#rustfs-technical-specifications)
4. [Component-by-Component Replacement](#component-by-component-replacement)
5. [Event Notification System](#event-notification-system)
6. [Asset Serving Strategy](#asset-serving-strategy)
7. [File Upload Flow](#file-upload-flow)
8. [File Deletion Flow](#file-deletion-flow)
9. [Docker Configuration](#docker-configuration)
10. [Environment Variables](#environment-variables)
11. [Frontend Changes](#frontend-changes)
12. [Backend Changes](#backend-changes)
13. [API Reference](#api-reference)
14. [Known Limitations](#known-limitations)
15. [References](#references)

---

## Executive Summary

This document provides complete technical specifications for replacing Copyparty with RustFS in DocuSearch. RustFS is an S3-compatible object storage system built in Rust, replacing Copyparty's file server approach with an S3 API paradigm.

### Key Paradigm Shifts

| Aspect | Copyparty (Current) | RustFS (Replacement) |
|--------|---------------------|----------------------|
| **Protocol** | Custom HTTP REST | S3-compatible API |
| **Upload** | HTTP POST multipart form | S3 PutObject / Presigned URL |
| **Download** | Direct HTTP GET | S3 GetObject / Presigned URL |
| **Events** | Script execution (`--xau`) | S3 bucket notifications to webhook |
| **Authentication** | Basic Auth | S3 Access Key / Secret Key |
| **URL Pattern** | `/uploads/{filename}` | `s3://bucket/key` or presigned URLs |

---

## Architecture Comparison

### Current Architecture (Copyparty)

```
┌─────────────┐     POST /uploads/      ┌────────────┐
│   Frontend  │ ──────────────────────> │  Copyparty │
└─────────────┘                         │  :8000     │
                                        └─────┬──────┘
                                              │
                                    executes --xau hook
                                              │
                                              v
                                        ┌────────────┐
                                        │ on_upload  │
                                        │   .py      │
                                        └─────┬──────┘
                                              │
                                    POST /process
                                              │
                                              v
                                        ┌────────────┐
                                        │   Worker   │
                                        │   :8002    │
                                        └────────────┘
```

### New Architecture (RustFS)

```
┌─────────────┐    S3 PutObject / Presigned   ┌────────────┐
│   Frontend  │ ────────────────────────────> │   RustFS   │
└─────────────┘                               │ :9000/9001 │
                                              └─────┬──────┘
                                                    │
                                        S3 bucket notification
                                            (webhook)
                                                    │
                                                    v
                                              ┌────────────┐
                                              │   Worker   │
                                              │   :8002    │
                                              │ /s3-event  │
                                              └────────────┘
```

---

## RustFS Technical Specifications

### Default Configuration

| Setting | Value |
|---------|-------|
| **S3 API Port** | 9000 |
| **Console Port** | 9001 |
| **Default User** | `rustfsadmin` |
| **Default Password** | `rustfsadmin` |
| **Container User** | `rustfs` (UID 1000) |
| **Data Directory** | `/data` |

### Key Environment Variables

```bash
# Authentication
RUSTFS_ROOT_USER=rustfsadmin
RUSTFS_ROOT_PASSWORD=rustfsadmin

# Network
RUSTFS_ADDRESS=:9000
RUSTFS_CONSOLE_ADDRESS=:9001
RUSTFS_CONSOLE_ENABLE=true

# CORS
RUSTFS_CORS_ALLOWED_ORIGINS=*
RUSTFS_CONSOLE_CORS_ALLOWED_ORIGINS=*

# Logging
RUSTFS_LOG_LEVEL=info
```

### S3 Compatibility

RustFS is 100% S3-compatible, supporting:
- CreateBucket, DeleteBucket, ListBuckets
- PutObject, GetObject, DeleteObject, ListObjects
- Presigned URLs (GET and PUT)
- Bucket notifications (webhooks, Kafka, etc.)
- Multipart uploads

---

## Component-by-Component Replacement

### 1. Docker Service

**Current:** `docker/Dockerfile.copyparty`

```dockerfile
FROM python:3.14-slim
RUN pip install copyparty==1.9.0
EXPOSE 8000
CMD ["copyparty", "--http-only", "-p", "8000", ...]
```

**Replacement:** `docker/Dockerfile.rustfs`

```dockerfile
FROM rustfs/rustfs:latest

ENV RUSTFS_ROOT_USER=docusearch
ENV RUSTFS_ROOT_PASSWORD=CHANGE_ME_IN_PRODUCTION
ENV RUSTFS_ADDRESS=:9000
ENV RUSTFS_CONSOLE_ADDRESS=:9001
ENV RUSTFS_CONSOLE_ENABLE=true
ENV RUSTFS_CORS_ALLOWED_ORIGINS=*

EXPOSE 9000 9001

# Data directory must be owned by UID 1000
VOLUME ["/data"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:9000/minio/health/live || exit 1
```

### 2. Docker Compose

**Current:** `docker/docker-compose.yml` (copyparty service)

```yaml
copyparty:
  build:
    context: .
    dockerfile: Dockerfile.copyparty
  ports:
    - "8000:8000"
  volumes:
    - ../data/uploads:/uploads
    - ../hooks:/hooks
  environment:
    - WORKER_HOST=host.docker.internal
    - WORKER_PORT=8002
```

**Replacement:**

```yaml
rustfs:
  image: rustfs/rustfs:latest
  container_name: docusearch-rustfs
  ports:
    - "${RUSTFS_API_PORT:-9000}:9000"
    - "${RUSTFS_CONSOLE_PORT:-9001}:9001"
  volumes:
    - ../data/rustfs:/data
  environment:
    - RUSTFS_ROOT_USER=${RUSTFS_USER:-docusearch}
    - RUSTFS_ROOT_PASSWORD=${RUSTFS_PASSWORD:-docusearch2024}
    - RUSTFS_ADDRESS=:9000
    - RUSTFS_CONSOLE_ADDRESS=:9001
    - RUSTFS_CONSOLE_ENABLE=true
    - RUSTFS_CORS_ALLOWED_ORIGINS=${ALLOWED_ORIGINS:-*}
    - RUSTFS_LOG_LEVEL=${LOG_LEVEL:-info}
  networks:
    - docusearch
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 10s
```

### 3. Upload Hook Replacement

**Current:** `hooks/on_upload.py`

The current hook receives a file path via command-line argument:

```python
# Called by copyparty with: on_upload.py /uploads/file.pdf
container_path = sys.argv[1]
filename = Path(container_path).name

# POST to worker
requests.post(f"http://{WORKER_HOST}:{WORKER_PORT}/process", json={
    "file_path": host_path,
    "filename": filename
})
```

**Replacement:** Worker endpoint `/s3-event`

RustFS sends S3 event notifications as JSON HTTP POST:

```json
{
  "EventName": "s3:ObjectCreated:Put",
  "Key": "uploads/document.pdf",
  "Records": [
    {
      "eventVersion": "2.0",
      "eventSource": "rustfs:s3",
      "eventTime": "2025-11-27T12:00:00.000Z",
      "eventName": "s3:ObjectCreated:Put",
      "userIdentity": {
        "principalId": "docusearch"
      },
      "requestParameters": {
        "sourceIPAddress": "172.20.0.1"
      },
      "responseElements": {},
      "s3": {
        "s3SchemaVersion": "1.0",
        "configurationId": "upload-notifications",
        "bucket": {
          "name": "uploads",
          "ownerIdentity": {
            "principalId": "docusearch"
          },
          "arn": "arn:aws:s3:::uploads"
        },
        "object": {
          "key": "document.pdf",
          "size": 1048576,
          "eTag": "d41d8cd98f00b204e9800998ecf8427e",
          "contentType": "application/pdf",
          "userMetadata": {}
        }
      }
    }
  ]
}
```

---

## Event Notification System

### Configuration via mc CLI

RustFS uses MinIO Client (mc) for configuration:

```bash
# 1. Configure mc alias
mc alias set docusearch http://localhost:9000 docusearch docusearch2024

# 2. Create the uploads bucket
mc mb docusearch/uploads

# 3. Configure webhook endpoint
mc admin config set docusearch/ notify_webhook:docusearch \
  endpoint="http://worker:8002/s3-event" \
  queue_dir="/data/events"

# 4. Restart to apply config
mc admin service restart docusearch

# 5. Subscribe bucket to upload events
mc event add docusearch/uploads arn:minio:sqs::docusearch:webhook \
  --event put \
  --suffix ".pdf,.docx,.pptx,.xlsx,.html,.md,.mp3,.wav,.png,.jpg,.jpeg"

# 6. Subscribe to delete events
mc event add docusearch/uploads arn:minio:sqs::docusearch:webhook \
  --event delete
```

### Supported Event Types

| Event | S3 Event Name | Use Case |
|-------|---------------|----------|
| Upload | `s3:ObjectCreated:Put` | Trigger document processing |
| Delete | `s3:ObjectRemoved:Delete` | Cleanup embeddings/assets |
| Copy | `s3:ObjectCreated:Copy` | (Optional) Handle copies |

### Worker Event Handler

New endpoint needed in `worker_webhook.py`:

```python
class S3EventRecord(BaseModel):
    """Single S3 event record."""
    eventName: str
    s3: dict

class S3EventRequest(BaseModel):
    """S3 event notification payload."""
    EventName: str
    Key: str
    Records: List[S3EventRecord]

@app.post("/s3-event")
async def handle_s3_event(request: S3EventRequest, background_tasks: BackgroundTasks):
    """Handle S3 bucket notification events from RustFS."""

    for record in request.Records:
        event_name = record.eventName
        bucket = record.s3["bucket"]["name"]
        key = record.s3["object"]["key"]

        if event_name.startswith("s3:ObjectCreated"):
            # Handle upload - queue for processing
            # Construct S3 URI for worker to download
            s3_uri = f"s3://{bucket}/{key}"
            background_tasks.add_task(process_s3_object, s3_uri, key)

        elif event_name.startswith("s3:ObjectRemoved"):
            # Handle deletion - cleanup embeddings
            background_tasks.add_task(cleanup_document, key)

    return {"status": "accepted", "events_processed": len(request.Records)}
```

---

## Asset Serving Strategy

### Current Approach (Copyparty)

Direct HTTP access to files:
```
http://localhost:8000/uploads/{doc_id}/images/page-001.png
```

### RustFS Approaches

#### Option A: Public Bucket Policy (Simplest)

```bash
# Set bucket to allow public read
mc anonymous set download docusearch/uploads
```

Access pattern:
```
http://localhost:9000/uploads/{doc_id}/images/page-001.png
```

**Pros:** Minimal code changes
**Cons:** All files publicly accessible, no directory listing prevention

#### Option B: Presigned URLs (Recommended)

Generate time-limited signed URLs for each asset:

```python
from minio import Minio
from datetime import timedelta

client = Minio(
    "localhost:9000",
    access_key="docusearch",
    secret_key="docusearch2024",
    secure=False
)

# Generate presigned URL (valid for 1 hour)
url = client.presigned_get_object(
    bucket_name="uploads",
    object_name=f"{doc_id}/images/page-001.png",
    expires=timedelta(hours=1)
)
```

**Pros:** Secure, time-limited access
**Cons:** Requires backend URL generation, URLs expire

#### Option C: API Proxy (Most Control)

Worker API proxies requests to RustFS:

```python
@app.get("/assets/{doc_id}/{path:path}")
async def proxy_asset(doc_id: str, path: str):
    """Proxy asset requests to RustFS."""

    # Validate doc_id
    if not validate_doc_id(doc_id):
        raise HTTPException(status_code=400)

    # Get object from RustFS
    response = s3_client.get_object(
        Bucket="uploads",
        Key=f"{doc_id}/{path}"
    )

    return StreamingResponse(
        response["Body"],
        media_type=response["ContentType"],
        headers={"Cache-Control": "max-age=86400"}
    )
```

**Pros:** Full control, caching, auth
**Cons:** Added latency, worker load

---

## File Upload Flow

### Current Flow (Copyparty)

```javascript
// Frontend: api.js
const formData = new FormData();
formData.append('act', 'bput');
formData.append('f', file);

xhr.open('POST', '/uploads/');
xhr.setRequestHeader('Authorization', `Basic ${btoa('uploader:docusearch2024')}`);
xhr.send(formData);
```

### New Flow (RustFS)

#### Option A: Direct S3 Upload (Recommended for large files)

```javascript
// 1. Request presigned URL from backend
const { uploadUrl, docId } = await api.upload.getPresignedUrl(file.name, file.size);

// 2. Upload directly to RustFS using presigned URL
await fetch(uploadUrl, {
  method: 'PUT',
  body: file,
  headers: {
    'Content-Type': file.type
  }
});
```

Backend presigned URL generation:

```python
@app.post("/upload/presign")
async def get_presigned_upload_url(filename: str, size: int):
    """Generate presigned URL for direct upload to RustFS."""

    # Generate doc_id
    doc_id = hashlib.sha256(f"{filename}{datetime.now().isoformat()}".encode()).hexdigest()

    # Create presigned PUT URL
    url = s3_client.presigned_put_object(
        bucket_name="uploads",
        object_name=f"{filename}",
        expires=timedelta(minutes=15)
    )

    return {
        "uploadUrl": url,
        "docId": doc_id,
        "expiresIn": 900
    }
```

#### Option B: Proxy Upload (Simpler frontend)

Keep similar frontend code, backend proxies to S3:

```python
@app.post("/upload")
async def upload_file(file: UploadFile):
    """Upload file via API proxy to RustFS."""

    # Upload to RustFS
    s3_client.put_object(
        Bucket="uploads",
        Key=file.filename,
        Body=file.file,
        ContentType=file.content_type
    )

    return {"filename": file.filename, "status": "uploaded"}
```

---

## File Deletion Flow

### Current Flow

```python
# documents_api.py
def delete_from_copyparty(filename: str) -> bool:
    url = f"http://{copyparty_host}:{copyparty_port}/uploads/{quote(filename)}"
    req = urllib.request.Request(url, method="DELETE", headers={...})
    urllib.request.urlopen(req, timeout=10)
```

### New Flow

```python
def delete_from_rustfs(key: str) -> bool:
    """Delete object from RustFS bucket."""
    try:
        s3_client.remove_object(
            bucket_name="uploads",
            object_name=key
        )
        return True
    except Exception as e:
        logger.error(f"Failed to delete from RustFS: {e}")
        return False
```

Note: S3 deletion triggers bucket notification, so webhook handler will also receive delete event for cleanup.

---

## Docker Configuration

### Complete docker-compose.yml Section

```yaml
services:
  # ============================================================================
  # RustFS - S3-Compatible Object Storage
  # ============================================================================
  rustfs:
    image: rustfs/rustfs:latest
    container_name: docusearch-rustfs
    ports:
      - "${RUSTFS_API_PORT:-9000}:9000"
      - "${RUSTFS_CONSOLE_PORT:-9001}:9001"
    volumes:
      # Data volume (must be owned by UID 1000)
      - rustfs-data:/data
    environment:
      - RUSTFS_ROOT_USER=${RUSTFS_USER:-docusearch}
      - RUSTFS_ROOT_PASSWORD=${RUSTFS_PASSWORD:-docusearch2024}
      - RUSTFS_ADDRESS=:9000
      - RUSTFS_CONSOLE_ADDRESS=:9001
      - RUSTFS_CONSOLE_ENABLE=true
      - RUSTFS_CORS_ALLOWED_ORIGINS=${ALLOWED_ORIGINS:-http://localhost:3000,http://localhost:8002}
      - RUSTFS_LOG_LEVEL=${LOG_LEVEL:-info}
    networks:
      - docusearch
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  # ============================================================================
  # RustFS Init - Configure buckets and notifications
  # ============================================================================
  rustfs-init:
    image: minio/mc:latest
    container_name: docusearch-rustfs-init
    depends_on:
      rustfs:
        condition: service_healthy
    environment:
      - RUSTFS_HOST=rustfs
      - RUSTFS_PORT=9000
      - RUSTFS_USER=${RUSTFS_USER:-docusearch}
      - RUSTFS_PASSWORD=${RUSTFS_PASSWORD:-docusearch2024}
      - WORKER_HOST=processing-worker
      - WORKER_PORT=8002
    entrypoint: ["/bin/sh", "-c"]
    command:
      - |
        # Wait for RustFS
        until mc alias set docusearch http://$$RUSTFS_HOST:$$RUSTFS_PORT $$RUSTFS_USER $$RUSTFS_PASSWORD; do
          echo "Waiting for RustFS..."
          sleep 2
        done

        # Create uploads bucket
        mc mb --ignore-existing docusearch/uploads

        # Configure webhook notification
        mc admin config set docusearch/ notify_webhook:worker \
          endpoint="http://$$WORKER_HOST:$$WORKER_PORT/s3-event" \
          queue_dir="/data/events"

        # Restart to apply webhook config
        mc admin service restart docusearch

        # Wait for restart
        sleep 5

        # Add event notifications for uploads
        mc event add docusearch/uploads arn:minio:sqs::worker:webhook \
          --event put,delete

        echo "RustFS initialization complete!"
    networks:
      - docusearch

volumes:
  rustfs-data:
    driver: local
```

### Data Directory Permissions

RustFS runs as UID 1000. Initialize data directory:

```bash
# Create data directory with correct ownership
mkdir -p data/rustfs
sudo chown -R 1000:1000 data/rustfs
```

---

## Environment Variables

### Complete .env.template Updates

```bash
# =============================================================================
# RustFS Configuration (replaces COPYPARTY_*)
# =============================================================================
RUSTFS_API_PORT=9000
RUSTFS_CONSOLE_PORT=9001
RUSTFS_USER=docusearch
RUSTFS_PASSWORD=CHANGE_ME_IN_PRODUCTION

# S3 endpoint for SDK clients
RUSTFS_ENDPOINT=http://localhost:9000
RUSTFS_BUCKET=uploads

# Legacy mapping (for gradual transition)
# COPYPARTY_URL -> RUSTFS_ENDPOINT
# COPYPARTY_PORT -> RUSTFS_API_PORT

# =============================================================================
# Asset Serving Strategy
# =============================================================================
# Options: public, presigned, proxy
ASSET_SERVING_STRATEGY=presigned
PRESIGNED_URL_EXPIRY_SECONDS=3600
```

---

## Frontend Changes

### URL Configuration Updates

**Current:** `frontend/src/config/urls.js`

```javascript
const BASE_URLS = {
  copyparty: import.meta.env.VITE_COPYPARTY_URL || 'http://localhost:8000',
};

const documentAssets = {
  imageUrl: (docId, imageFilename, absolute = true) => {
    const path = `/uploads/${docId}/images/${imageFilename}`;
    return absolute ? urlJoin(BASE_URLS.copyparty, path) : path;
  },
};
```

**Replacement:**

```javascript
const BASE_URLS = {
  rustfs: import.meta.env.VITE_RUSTFS_URL || 'http://localhost:9000',
  api: import.meta.env.VITE_API_URL || 'http://localhost:8002',
};

const ASSET_STRATEGY = import.meta.env.VITE_ASSET_STRATEGY || 'presigned';

const documentAssets = {
  /**
   * Get image URL based on configured strategy
   */
  imageUrl: async (docId, imageFilename) => {
    if (ASSET_STRATEGY === 'public') {
      // Direct S3 URL (public bucket)
      return `${BASE_URLS.rustfs}/uploads/${docId}/images/${imageFilename}`;
    } else if (ASSET_STRATEGY === 'presigned') {
      // Fetch presigned URL from API
      const response = await fetch(`${BASE_URLS.api}/assets/presign`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bucket: 'uploads',
          key: `${docId}/images/${imageFilename}`
        })
      });
      const { url } = await response.json();
      return url;
    } else {
      // Proxy through API
      return `${BASE_URLS.api}/assets/${docId}/images/${imageFilename}`;
    }
  },
};
```

### Upload API Changes

**Current:** `frontend/src/services/api.js`

```javascript
async uploadFile(file, onProgress = null) {
  const formData = new FormData();
  formData.append('act', 'bput');
  formData.append('f', file);

  xhr.open('POST', '/uploads/');
  xhr.setRequestHeader('Authorization', `Basic ${btoa('uploader:docusearch2024')}`);
  xhr.send(formData);
}
```

**Replacement:**

```javascript
async uploadFile(file, onProgress = null) {
  // 1. Get presigned upload URL from backend
  const presignResponse = await fetch(`${API_BASE_URL}/upload/presign`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      filename: file.name,
      contentType: file.type,
      size: file.size
    })
  });

  const { uploadUrl, docId } = await presignResponse.json();

  // 2. Upload directly to RustFS
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    if (onProgress) {
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          onProgress(Math.round((e.loaded / e.total) * 100));
        }
      });
    }

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve({ success: true, filename: file.name, docId });
      } else {
        reject(new APIError(`Upload failed: ${xhr.statusText}`, xhr.status));
      }
    });

    xhr.open('PUT', uploadUrl);
    xhr.setRequestHeader('Content-Type', file.type);
    xhr.send(file);
  });
}
```

---

## Backend Changes

### New S3 Client Module

**New file:** `src/storage/s3_client.py`

```python
"""
S3 client for RustFS integration.
"""

import os
from minio import Minio
from datetime import timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class S3StorageClient:
    """S3-compatible storage client for RustFS."""

    def __init__(
        self,
        endpoint: str = None,
        access_key: str = None,
        secret_key: str = None,
        secure: bool = False,
        bucket: str = "uploads"
    ):
        self.endpoint = endpoint or os.getenv("RUSTFS_ENDPOINT", "localhost:9000")
        self.access_key = access_key or os.getenv("RUSTFS_USER", "docusearch")
        self.secret_key = secret_key or os.getenv("RUSTFS_PASSWORD", "docusearch2024")
        self.bucket = bucket

        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=secure
        )

        logger.info(f"S3 client initialized: {self.endpoint}")

    def presigned_get_url(self, key: str, expires: int = 3600) -> str:
        """Generate presigned GET URL."""
        return self.client.presigned_get_object(
            bucket_name=self.bucket,
            object_name=key,
            expires=timedelta(seconds=expires)
        )

    def presigned_put_url(self, key: str, expires: int = 900) -> str:
        """Generate presigned PUT URL for uploads."""
        return self.client.presigned_put_object(
            bucket_name=self.bucket,
            object_name=key,
            expires=timedelta(seconds=expires)
        )

    def get_object(self, key: str):
        """Download object from bucket."""
        return self.client.get_object(self.bucket, key)

    def put_object(self, key: str, data, length: int, content_type: str = None):
        """Upload object to bucket."""
        self.client.put_object(
            bucket_name=self.bucket,
            object_name=key,
            data=data,
            length=length,
            content_type=content_type
        )

    def delete_object(self, key: str):
        """Delete object from bucket."""
        self.client.remove_object(self.bucket, key)

    def object_exists(self, key: str) -> bool:
        """Check if object exists."""
        try:
            self.client.stat_object(self.bucket, key)
            return True
        except Exception:
            return False


# Singleton instance
_s3_client: Optional[S3StorageClient] = None


def get_s3_client() -> S3StorageClient:
    """Get S3 client singleton."""
    global _s3_client
    if _s3_client is None:
        _s3_client = S3StorageClient()
    return _s3_client
```

### URL Configuration Updates

**Update:** `src/config/urls.py`

```python
class ServiceURLs:
    def __init__(self) -> None:
        # ... existing code ...

        # Replace copyparty with rustfs
        self.rustfs = os.getenv("RUSTFS_ENDPOINT", "http://localhost:9000")
        self.rustfs_bucket = os.getenv("RUSTFS_BUCKET", "uploads")

        # Asset serving strategy
        self.asset_strategy = os.getenv("ASSET_SERVING_STRATEGY", "presigned")

    def document_image_url(self, doc_id: str, image_filename: str) -> str:
        """Build URL for document image based on configured strategy."""

        if self.asset_strategy == "public":
            return f"{self.rustfs}/{self.rustfs_bucket}/{doc_id}/images/{image_filename}"
        elif self.asset_strategy == "presigned":
            # Return API endpoint that generates presigned URL
            return f"{self.worker}/assets/presign?key={doc_id}/images/{image_filename}"
        else:
            # Proxy through API
            return f"{self.worker}/assets/{doc_id}/images/{image_filename}"
```

---

## API Reference

### New Worker Endpoints

#### POST /s3-event

Handle S3 bucket notifications from RustFS.

**Request Body:**
```json
{
  "EventName": "s3:ObjectCreated:Put",
  "Key": "document.pdf",
  "Records": [...]
}
```

**Response:**
```json
{
  "status": "accepted",
  "events_processed": 1
}
```

#### POST /upload/presign

Generate presigned URL for direct upload.

**Request Body:**
```json
{
  "filename": "document.pdf",
  "contentType": "application/pdf",
  "size": 1048576
}
```

**Response:**
```json
{
  "uploadUrl": "http://localhost:9000/uploads/document.pdf?X-Amz-...",
  "docId": "abc123...",
  "expiresIn": 900
}
```

#### POST /assets/presign

Generate presigned URL for asset access.

**Request Body:**
```json
{
  "bucket": "uploads",
  "key": "abc123/images/page-001.png"
}
```

**Response:**
```json
{
  "url": "http://localhost:9000/uploads/abc123/images/page-001.png?X-Amz-...",
  "expiresIn": 3600
}
```

#### GET /assets/{doc_id}/{path}

Proxy asset requests (if strategy is "proxy").

**Response:** Binary file data with appropriate Content-Type.

---

## Known Limitations

### RustFS Beta Status

RustFS is currently in **beta/technical preview**. The official documentation states:
> "Not yet recommended for critical production workloads."

### S3 Event Delivery

- Events are delivered asynchronously by default
- No guaranteed delivery order
- Webhook must be available when RustFS starts
- Queue directory (`queue_dir`) provides persistence for offline webhook

### Presigned URL Considerations

- URLs have expiration times
- Clients need to handle URL refresh
- Not suitable for caching in browsers long-term
- Each URL generation requires backend round-trip

### CORS Configuration

RustFS CORS must be configured for frontend direct uploads:
- `RUSTFS_CORS_ALLOWED_ORIGINS` must include frontend origin
- Preflight requests must be handled

---

## References

### RustFS Documentation
- [RustFS GitHub](https://github.com/rustfs/rustfs)
- [RustFS Installation](https://docs.rustfs.com/installation/)
- [RustFS Docker Guide](https://docs.rustfs.com/installation/docker/)
- [RustFS mc CLI](https://docs.rustfs.com/developer/mc.html)

### S3/MinIO Documentation (Compatible)
- [MinIO Bucket Notifications](https://min.io/docs/minio/linux/administration/monitoring/bucket-notifications.html)
- [MinIO Webhook Events](https://min.io/docs/minio/linux/administration/monitoring/publish-events-to-webhook.html)
- [MinIO Python SDK](https://min.io/docs/minio/linux/developers/python/API.html)
- [S3 Event Message Structure](https://docs.aws.amazon.com/AmazonS3/latest/userguide/notification-content-structure.html)

### Frontend Upload Patterns
- [S3 Presigned URL Uploads](https://aws.amazon.com/blogs/developer/generate-presigned-url-modular-aws-sdk-javascript/)
- [Direct Browser Uploads to S3](https://softwareontheroad.com/aws-s3-secure-direct-upload)
