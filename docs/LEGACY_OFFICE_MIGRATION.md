# Migration Guide: slide-renderer → legacy-office-converter

## Overview
The `slide-renderer` service has been renamed to `legacy-office-converter` to better reflect its expanded capabilities. The service now handles both PPTX slide rendering and legacy Office document conversion (.doc to .docx).

## What Changed

### Service Names
- **Service name**: `slide-renderer` → `legacy-office-converter`
- **Container name**: `docusearch-slide-renderer` → `docusearch-legacy-office-converter`
- **Image name**: `docusearch-slide-renderer` → `docusearch-legacy-office-converter`

### Environment Variables
- **Host**: `SLIDE_RENDERER_HOST` → `LEGACY_OFFICE_HOST`
- **Port**: `SLIDE_RENDERER_PORT` → `LEGACY_OFFICE_PORT`

### Files Updated
- `docker/docker-compose.yml` - Service definition
- `docker/Dockerfile.slide-renderer` → `docker/Dockerfile.legacy-office-converter`
- `scripts/run-worker-native.sh` - Environment variables
- `.env.example` - Documentation and variable names

## What Stayed the Same

### Port Number
- **Port**: 8003 (no change)
- All endpoints remain at `http://localhost:8003`

### Functionality
All existing PPTX rendering works exactly as before:
- `POST /render_slides` - Render PPTX slides to PNG images
- `GET /health` - Health check endpoint

### Volume Mounts
Same data directory structure:
- `/uploads` - Read/write access to uploads
- `/page_images` - Read/write access to rendered slides

### API Compatibility
All API endpoints remain unchanged. Existing client code will continue to work.

## Migration Steps

### 1. Update Environment Variables
Edit your `.env` file to use the new variable names:

```bash
# Old (deprecated but still works)
SLIDE_RENDERER_HOST=localhost
SLIDE_RENDERER_PORT=8003

# New (recommended)
LEGACY_OFFICE_HOST=localhost
LEGACY_OFFICE_PORT=8003
LEGACY_OFFICE_ENABLED=true
DOC_CONVERSION_TIMEOUT=30
```

### 2. Rebuild Container
Rebuild the service with the new name:

```bash
cd docker
docker-compose build legacy-office-converter
```

### 3. Restart Services
Use the unified scripts to restart:

```bash
# Stop all services
./scripts/stop-all.sh

# Start with new configuration
./scripts/start-all.sh
```

### 4. Verify Service
Check that the service is running correctly:

```bash
# Check status
./scripts/status.sh

# Test health endpoint
curl http://localhost:8003/health
```

## Backward Compatibility

### Old Variable Names Still Work
The system maintains backward compatibility with old environment variable names:

```bash
# If you set old variables, they still work
SLIDE_RENDERER_HOST=localhost  # Falls back to LEGACY_OFFICE_HOST
SLIDE_RENDERER_PORT=8003        # Falls back to LEGACY_OFFICE_PORT
```

This allows for gradual migration without breaking existing deployments.

### Transition Period
You can use either old or new variable names during the transition:

1. **Immediate**: Start using `LEGACY_OFFICE_*` for new configurations
2. **Gradual**: Keep `SLIDE_RENDERER_*` in existing `.env` files (still works)
3. **Eventually**: Update all `.env` files to use `LEGACY_OFFICE_*`

## New Features

### .doc to .docx Conversion
The renamed service adds support for legacy Office document conversion:

```bash
# Convert .doc to .docx
curl -X POST http://localhost:8003/convert_doc \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/uploads/document.doc"}'
```

### Automatic Legacy Format Detection
The processing worker now automatically:
1. Detects legacy `.doc` files
2. Converts them to `.docx` using the legacy-office-converter service
3. Processes the modern format for embedding
4. Preserves original filename in metadata

## Troubleshooting

### Container Not Found
If you see errors about `docusearch-slide-renderer` not found:

```bash
# Remove old container
docker rm -f docusearch-slide-renderer

# Rebuild with new name
docker-compose build legacy-office-converter

# Restart services
./scripts/start-all.sh
```

### Environment Variables Not Loading
Make sure your `.env` file is in the project root:

```bash
# Check .env location
ls -la .env

# Verify variables are exported
./scripts/status.sh
```

### Port 8003 Already in Use
Check for old service instances:

```bash
# Find process on port 8003
lsof -i :8003

# Kill if needed
kill -9 <PID>

# Restart
./scripts/start-all.sh
```

## Rollback Instructions

If you need to rollback to the old service name:

```bash
# 1. Stop all services
./scripts/stop-all.sh --force

# 2. Revert to previous git commit
git checkout HEAD~1 -- docker/docker-compose.yml
git checkout HEAD~1 -- scripts/run-worker-native.sh

# 3. Rebuild
docker-compose build slide-renderer

# 4. Restart
./scripts/start-all.sh
```

## Support

For issues or questions:
1. Check logs: `docker logs docusearch-legacy-office-converter`
2. Review status: `./scripts/status.sh`
3. See documentation: `docs/QUICK_START.md`

## Timeline

- **2025-11-19**: Migration completed
- **Deprecated**: `SLIDE_RENDERER_*` variables (still supported)
- **Recommended**: Use `LEGACY_OFFICE_*` variables going forward
