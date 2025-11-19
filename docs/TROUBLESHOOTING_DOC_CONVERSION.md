# Troubleshooting .doc Conversion

**Last Updated:** 2025-11-19

This guide provides detailed troubleshooting steps for common issues with legacy Office document (`.doc`) conversion in DocuSearch.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Common Issues](#common-issues)
  - [Service Unavailable](#service-unavailable)
  - [Conversion Timeout](#conversion-timeout)
  - [File Not Found](#file-not-found)
  - [Password-Protected Files](#password-protected-files)
  - [Corrupted Files](#corrupted-files)
  - [Empty Output Files](#empty-output-files)
  - [Path Access Denied](#path-access-denied)
  - [Large File Issues](#large-file-issues)
- [Advanced Debugging](#advanced-debugging)
- [Performance Issues](#performance-issues)
- [Known Limitations](#known-limitations)

---

## Quick Diagnostics

Before diving into specific issues, run these quick checks:

### 1. Check Service Status

```bash
# Check all services
./scripts/status.sh

# Specifically check legacy-office-converter
docker ps | grep legacy-office-converter
```

**Expected output:**
```
docusearch-legacy-office-converter   Up 5 minutes   0.0.0.0:8003->8003/tcp
```

### 2. Test Service Health

```bash
curl http://localhost:8003/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "legacy-office-converter",
  "capabilities": ["pptx-rendering", "doc-conversion"]
}
```

### 3. Check Worker Logs

```bash
# Native worker logs
tail -50 logs/worker-native.log | grep -i "doc\|conversion"

# Docker worker logs
docker logs docusearch-worker | grep -i "doc\|conversion"

# Converter service logs
docker logs docusearch-legacy-office-converter
```

### 4. Verify File Exists

```bash
# Check uploaded file
ls -lh data/uploads/*.doc

# Verify permissions
ls -l data/uploads/your-file.doc
```

---

## Common Issues

### Service Unavailable

#### Symptoms
- Error: `"Conversion failed: Service unavailable"`
- Error: `Connection refused`
- Documents stuck in "processing" status

#### Cause
The `legacy-office-converter` service is not running or not reachable.

#### Solution

**Step 1: Check if service is running**
```bash
docker ps | grep legacy-office-converter
```

**Step 2: If not running, start services**
```bash
./scripts/start-all.sh
```

**Step 3: If still not working, check logs**
```bash
docker logs docusearch-legacy-office-converter
```

**Step 4: Look for common startup errors**
```bash
# Port already in use
Error: bind: address already in use

# Solution: Find and kill process using port 8003
lsof -i :8003
kill -9 <PID>

# Then restart
./scripts/start-all.sh
```

**Step 5: Rebuild if necessary**
```bash
cd docker
docker-compose build legacy-office-converter
docker-compose up -d legacy-office-converter
```

**Step 6: Verify service is accessible**
```bash
curl http://localhost:8003/health
```

#### Prevention
- Always start services with `./scripts/start-all.sh`
- Monitor service health in production
- Set up restart policies in Docker Compose

---

### Conversion Timeout

#### Symptoms
- Error: `"Conversion timeout exceeded (30s)"`
- Large files fail to convert
- Processing hangs indefinitely

#### Cause
File is too large or complex, exceeding the configured timeout.

#### Solution

**Step 1: Identify file size**
```bash
ls -lh data/uploads/your-file.doc
# Example: 15M (15 megabytes)
```

**Step 2: Increase timeout in .env**
```bash
# Edit .env file
DOC_CONVERSION_TIMEOUT=120  # Increase to 120 seconds

# Or for very large files
DOC_CONVERSION_TIMEOUT=300  # 5 minutes
```

**Step 3: Restart services**
```bash
./scripts/stop-all.sh
./scripts/start-all.sh
```

**Step 4: Monitor conversion progress**
```bash
# Watch logs in real-time
docker logs -f docusearch-legacy-office-converter
```

**Alternative Solutions:**

**Option A: Split large document**
If file is very large (> 50 MB), consider splitting it:
1. Open in Microsoft Word
2. Split into smaller sections
3. Upload each section separately

**Option B: Pre-convert offline**
1. Convert to .docx using Microsoft Word or LibreOffice on desktop
2. Upload the .docx file directly (no conversion needed)

**Timeout Recommendations by File Size:**

| File Size | Recommended Timeout |
|-----------|-------------------|
| < 1 MB | 30s (default) |
| 1-5 MB | 60s |
| 5-20 MB | 120s |
| 20-50 MB | 300s |
| > 50 MB | Split file or pre-convert |

---

### File Not Found

#### Symptoms
- Error: `"File not found: document.doc"`
- 404 error from API
- File shows in UI but conversion fails

#### Cause
File path mismatch between upload location and conversion service.

#### Solution

**Step 1: Verify file exists in uploads directory**
```bash
ls -la data/uploads/ | grep ".doc"
```

**Step 2: Check file path in error logs**
```bash
docker logs docusearch-legacy-office-converter | tail -20
```

**Step 3: Verify volume mounts**
```bash
# Check docker-compose.yml
grep -A 5 "legacy-office-converter:" docker/docker-compose.yml | grep volumes
```

**Expected volume mount:**
```yaml
volumes:
  - ../data/uploads:/uploads
```

**Step 4: Test file access from container**
```bash
# List files visible to container
docker exec docusearch-legacy-office-converter ls -la /uploads/

# Try to read specific file
docker exec docusearch-legacy-office-converter cat /uploads/your-file.doc | head -c 100
```

**Step 5: Fix path issues**

If file is in wrong location:
```bash
# Move to correct location
mv /some/path/document.doc data/uploads/
```

If volume mount is wrong:
```bash
# Fix docker-compose.yml
# Then restart
docker-compose down
docker-compose up -d
```

---

### Password-Protected Files

#### Symptoms
- Error: `"LibreOffice conversion failed"`
- Error mentions encryption or password
- File opens fine in Word with password

#### Cause
LibreOffice cannot convert password-protected .doc files without authentication.

#### Solution

**Current Limitation:** DocuSearch does not support password-protected files.

**Workaround Options:**

**Option 1: Remove password in Microsoft Word**
1. Open file in Microsoft Word
2. Go to File → Info → Protect Document
3. Select "Encrypt with Password"
4. Delete password (leave blank)
5. Save file
6. Upload unprotected file to DocuSearch

**Option 2: Remove password in LibreOffice**
1. Open file in LibreOffice Writer
2. Enter password when prompted
3. Go to File → Properties → Security
4. Click "Remove" to remove password
5. Save file
6. Upload unprotected file to DocuSearch

**Option 3: Convert to .docx manually**
1. Open protected .doc in Word
2. Enter password
3. Save As → .docx format
4. Remove password from .docx (File → Info → Protect Document)
5. Upload .docx to DocuSearch (no conversion needed)

**Detection:**
Check if file is password-protected:
```bash
file data/uploads/document.doc | grep -i encrypt
```

---

### Corrupted Files

#### Symptoms
- Error: `"LibreOffice conversion failed: corrupted file structure"`
- Conversion produces empty output
- File won't open in Word or LibreOffice

#### Cause
File structure is damaged or invalid.

#### Solution

**Step 1: Verify file integrity**
```bash
# Check file type
file data/uploads/document.doc

# Expected output:
# document.doc: Microsoft Word Document

# If output shows something else:
# document.doc: data
# This indicates corruption
```

**Step 2: Try opening in LibreOffice manually**
```bash
docker exec -it docusearch-legacy-office-converter bash

# Inside container:
libreoffice --headless --convert-to docx --outdir /tmp /uploads/document.doc

# Check output
ls -la /tmp/*.docx
```

**Step 3: Attempt recovery**

**Option A: Open and re-save in Word**
1. Open file in Microsoft Word
2. If Word offers to repair, accept
3. Save As new file
4. Upload repaired file

**Option B: Use Word's built-in repair**
1. Open Word
2. File → Open
3. Browse to file
4. Click dropdown arrow on "Open" button
5. Select "Open and Repair"
6. Save repaired document

**Option C: Try LibreOffice recovery**
1. Open LibreOffice Writer
2. File → Open
3. Select corrupted file
4. LibreOffice may auto-repair
5. Save as new .docx

**Step 4: Validate repaired file**
```bash
# Upload repaired file
# Check conversion logs
docker logs docusearch-legacy-office-converter -f
```

**Prevention:**
- Ensure files are properly uploaded (not truncated)
- Verify file checksum after upload
- Keep backup of original files

---

### Empty Output Files

#### Symptoms
- Conversion succeeds but .docx file is 0 bytes
- Error: `"Conversion produced empty file"`
- UI shows document but no content

#### Cause
LibreOffice conversion succeeded but produced no output.

#### Solution

**Step 1: Check converted file**
```bash
ls -lh data/uploads/*.docx
# Look for 0-byte files
```

**Step 2: Verify source file has content**
```bash
# Check source file size
ls -lh data/uploads/document.doc

# If source is very small (< 5KB), may be mostly formatting
```

**Step 3: Try manual conversion with verbose output**
```bash
docker exec docusearch-legacy-office-converter \
  libreoffice --headless --convert-to docx \
  --outdir /uploads /uploads/document.doc 2>&1
```

**Step 4: Check for LibreOffice errors**
```bash
docker logs docusearch-legacy-office-converter | grep -i error
```

**Step 5: Verify LibreOffice installation**
```bash
docker exec docusearch-legacy-office-converter \
  libreoffice --version

# Expected: LibreOffice 7.x or higher
```

**Step 6: Rebuild container if needed**
```bash
cd docker
docker-compose build legacy-office-converter --no-cache
docker-compose up -d legacy-office-converter
```

**Alternative:**
If issue persists, convert file manually to .docx and upload directly.

---

### Path Access Denied

#### Symptoms
- Error: `"Access denied: Path outside allowed directories"`
- 403 Forbidden error
- File exists but conversion fails

#### Cause
Security validation blocks paths outside `/uploads` directory.

#### Solution

**Step 1: Verify file is in allowed directory**
```bash
# File must be in one of these locations:
# - /uploads/
# - /data/uploads/
# - data/uploads/ (from project root)

# Check file location
find data/uploads -name "*.doc"
```

**Step 2: Move file to uploads directory if needed**
```bash
mv /some/other/path/document.doc data/uploads/
```

**Step 3: Verify Docker volume mount**
```bash
docker inspect docusearch-legacy-office-converter | grep -A 5 Mounts
```

**Expected mount:**
```json
{
  "Type": "bind",
  "Source": "/Volumes/.../tkr-docusearch/data/uploads",
  "Destination": "/uploads"
}
```

**Step 4: Check environment variables**
```bash
docker exec docusearch-legacy-office-converter \
  printenv | grep ALLOWED_UPLOAD_DIRS

# Expected:
# ALLOWED_UPLOAD_DIRS=/uploads,/data/uploads
```

**Security Note:**
This validation prevents path traversal attacks. Do not disable it.

---

### Large File Issues

#### Symptoms
- Very slow conversion (> 5 minutes)
- Memory errors
- Container crashes during conversion
- System becomes unresponsive

#### Cause
File exceeds recommended size limits or resource allocation.

#### Solution

**Step 1: Check file size**
```bash
ls -lh data/uploads/large-file.doc
# Note: Files > 50 MB are not recommended
```

**Step 2: Increase Docker resource limits**

Edit `docker/docker-compose.yml`:
```yaml
services:
  legacy-office-converter:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G  # Increase from 512M
        reservations:
          cpus: '1.0'
          memory: 512M
```

Restart:
```bash
docker-compose restart legacy-office-converter
```

**Step 3: Increase timeout**
```bash
# In .env
DOC_CONVERSION_TIMEOUT=300  # 5 minutes
```

**Step 4: Monitor resource usage**
```bash
# Watch resource usage during conversion
docker stats docusearch-legacy-office-converter
```

**Step 5: Optimize file before upload**

**Option A: Reduce image quality**
1. Open in Word
2. File → Compress Pictures
3. Select "Email (96 ppi)" or "Web (150 ppi)"
4. Save

**Option B: Remove embedded objects**
1. Open in Word
2. Remove or externalize large embedded objects
3. Save

**Option C: Split document**
1. Split into smaller sections
2. Upload each section separately

**Recommended Limits:**

| Resource | Recommended | Maximum |
|----------|-------------|---------|
| File Size | < 20 MB | 50 MB |
| Memory | 512 MB | 1 GB |
| Timeout | 60s | 300s |
| CPU | 1 core | 2 cores |

---

## Advanced Debugging

### Enable Debug Logging

**Step 1: Set debug log level**
```yaml
# docker/docker-compose.yml
services:
  legacy-office-converter:
    environment:
      - LOG_LEVEL=DEBUG
```

**Step 2: Restart service**
```bash
docker-compose restart legacy-office-converter
```

**Step 3: Watch detailed logs**
```bash
docker logs -f docusearch-legacy-office-converter
```

### Manual Conversion Test

**Test conversion directly in container:**
```bash
# Enter container
docker exec -it docusearch-legacy-office-converter bash

# Run conversion manually
cd /uploads
libreoffice --headless --convert-to docx --outdir /uploads test.doc

# Check for errors
echo $?  # 0 = success, non-zero = failure

# Check output
ls -lh test.docx

# Exit container
exit
```

### Verify LibreOffice Installation

```bash
# Check LibreOffice version
docker exec docusearch-legacy-office-converter \
  libreoffice --version

# Check installed components
docker exec docusearch-legacy-office-converter \
  dpkg -l | grep libreoffice

# Expected packages:
# libreoffice
# libreoffice-writer
# libreoffice-calc
# libreoffice-impress
```

### Test with Known Good File

```bash
# Create simple test document
echo "Test document" | docker exec -i docusearch-legacy-office-converter \
  bash -c 'cat > /tmp/test.txt'

# Convert txt to doc (for testing)
docker exec docusearch-legacy-office-converter \
  libreoffice --headless --convert-to doc --outdir /uploads /tmp/test.txt

# Try converting back to docx
curl -X POST http://localhost:8003/convert-doc \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/uploads/test.doc",
    "output_dir": "/uploads"
  }'
```

### Network Connectivity Test

```bash
# From host, test service reachability
curl -v http://localhost:8003/health

# From worker container (if using Docker worker)
docker exec docusearch-worker \
  curl http://legacy-office-converter:8003/health

# Expected: Connection successful
```

---

## Performance Issues

### Slow Conversion Times

**Symptoms:**
- Conversions taking > 30s for small files
- Increasing conversion times over time
- CPU consistently high

**Diagnostics:**
```bash
# Check CPU usage
docker stats docusearch-legacy-office-converter

# Check for multiple LibreOffice processes
docker exec docusearch-legacy-office-converter \
  ps aux | grep libreoffice
```

**Solutions:**

**1. Restart service periodically**
```bash
# In production, set up scheduled restarts
docker restart docusearch-legacy-office-converter
```

**2. Clean up temp files**
```bash
docker exec docusearch-legacy-office-converter \
  find /tmp -name "lu*" -type d -delete
```

**3. Increase CPU allocation**
```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '2.0'  # Increase from 1.0
```

**4. Process files sequentially**
Ensure worker doesn't send concurrent conversion requests.

### Memory Leaks

**Symptoms:**
- Memory usage grows over time
- Container eventually crashes
- OOM (Out of Memory) errors

**Diagnostics:**
```bash
# Monitor memory over time
watch -n 5 'docker stats docusearch-legacy-office-converter --no-stream'
```

**Solutions:**

**1. Set memory limits**
```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      memory: 512M
```

**2. Restart on high memory**
```bash
# Add health check that monitors memory
# Restart if memory > threshold
```

**3. Use Docker restart policy**
```yaml
restart: unless-stopped
```

---

## Known Limitations

### Cannot Convert

The following scenarios **cannot** be handled by the conversion service:

| Issue | Why | Workaround |
|-------|-----|------------|
| Password-protected files | LibreOffice requires password | Decrypt before upload |
| Extremely corrupted files | Unrecoverable structure | Repair manually or skip |
| Files > 100 MB | Resource constraints | Split or compress file |
| Proprietary DRM | Locked content | Use unprotected version |
| Embedded macros | Stripped during conversion | Not needed for search |
| Digital signatures | Removed during conversion | Not needed for search |

### Partial Support

These features work but with caveats:

| Feature | Status | Note |
|---------|--------|------|
| Embedded objects | ⚠️ Partial | May lose formatting |
| Custom fonts | ⚠️ Substituted | Text preserved |
| Track changes | ✅ Preserved | Usually maintained |
| Comments | ✅ Preserved | Usually maintained |
| Complex tables | ⚠️ Partial | May shift layout |
| Page layout | ⚠️ Approximate | Good enough for search |

---

## Getting Help

### Collect Diagnostic Information

When reporting issues, include:

**1. Service status**
```bash
./scripts/status.sh --json > status.json
```

**2. Service logs**
```bash
docker logs docusearch-legacy-office-converter > converter-logs.txt
```

**3. File information**
```bash
file data/uploads/problem-file.doc
ls -lh data/uploads/problem-file.doc
```

**4. Environment**
```bash
cat .env | grep -i legacy
docker version
```

**5. Error details**
- Exact error message
- When error occurs (upload, processing, etc.)
- File characteristics (size, source, etc.)

### Support Resources

- [Legacy Office Conversion Guide](LEGACY_OFFICE_CONVERSION.md) - Feature overview
- [API Documentation](API_LEGACY_OFFICE.md) - API details
- [Quick Start](QUICK_START.md) - Basic setup
- [Multi-Format Support](MULTI_FORMAT_SUPPORT.md) - Format information

### Escalation Path

1. **Check this troubleshooting guide**
2. **Review service logs** for specific errors
3. **Test with simple file** to isolate issue
4. **Collect diagnostics** as described above
5. **Open issue** with diagnostic information

---

## Quick Reference

### Common Commands

```bash
# Check service health
curl http://localhost:8003/health

# View logs
docker logs -f docusearch-legacy-office-converter

# Restart service
docker restart docusearch-legacy-office-converter

# Rebuild service
docker-compose build legacy-office-converter
docker-compose up -d legacy-office-converter

# Test manual conversion
docker exec docusearch-legacy-office-converter \
  libreoffice --headless --convert-to docx \
  --outdir /uploads /uploads/test.doc

# Check resource usage
docker stats docusearch-legacy-office-converter
```

### Configuration Quick Check

```bash
# Verify environment
env | grep -i legacy

# Check Docker compose config
docker-compose config | grep -A 10 legacy-office-converter

# Verify volume mounts
docker inspect docusearch-legacy-office-converter | grep -A 5 Mounts
```
