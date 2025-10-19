# Environment Configuration Guide

This document explains how to configure environment variables for DocuSearch.

## Overview

DocuSearch uses **two separate `.env` files** for different purposes:

1. **Root `.env`** - Backend/server-side configuration (secrets, API keys)
2. **Frontend `.env`** - Client-side configuration (exposed to browser)

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Root .env (Backend)                                         │
│ ────────────────────────────────────────────────────────── │
│ • Used by: Python worker, Docker Compose, scripts          │
│ • Contains: API keys, database credentials, secrets        │
│ • Security: NEVER exposed to browser                       │
│ • Location: /Volumes/.../tkr-docusearch/.env              │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    Server-side processing
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Frontend .env (Client)                                      │
│ ────────────────────────────────────────────────────────── │
│ • Used by: React app, Vite build system                    │
│ • Contains: API URLs, public configuration                 │
│ • Security: Exposed to browser (only VITE_* vars)          │
│ • Location: /Volumes/.../tkr-docusearch/frontend/.env     │
└─────────────────────────────────────────────────────────────┘
```

## Setup Instructions

### 1. Backend Configuration (Root .env)

```bash
# Copy the example file
cp .env.example .env

# Edit with your secrets
nano .env  # or vim, code, etc.
```

**Required Variables:**

```env
# LLM API Keys (choose your provider)
OPENAI_API_KEY=sk-proj-your-key-here
# OR
ANTHROPIC_API_KEY=sk-ant-your-key-here
# OR
GOOGLE_API_KEY=your-google-key-here

# LLM Provider Selection
LLM_PROVIDER=openai  # or anthropic, google
LLM_MODEL=gpt-4      # or claude-3-opus-20240229, gemini-pro

# HuggingFace Model Cache
HF_HOME=/path/to/your/models  # Update this path!
```

**Optional Variables:**

```env
# ASR (Automatic Speech Recognition)
ASR_ENABLED=true
ASR_BACKEND=mlx
ASR_MODEL=turbo

# Logging
LOG_LEVEL=INFO  # DEBUG for development

# Processing
DEVICE=mps           # mps (Metal), cuda (NVIDIA), cpu
MODEL_PRECISION=fp16
```

### 2. Frontend Configuration (frontend/.env)

```bash
# Copy the example file
cd frontend
cp .env.example .env

# Edit if needed (defaults usually work)
nano .env
```

**Variables:**

```env
# API endpoint (backend worker)
VITE_API_URL=http://localhost:8002

# Copyparty upload credentials
# WARNING: These are exposed to the browser!
# Use a dedicated upload-only account
VITE_UPLOAD_USERNAME=uploader
VITE_UPLOAD_PASSWORD=docusearch2024  # Change in production!
```

## Getting API Keys

### OpenAI (GPT-4, GPT-3.5)
1. Visit https://platform.openai.com/api-keys
2. Sign in or create account
3. Click "Create new secret key"
4. Copy and paste into `.env` as `OPENAI_API_KEY`

### Anthropic (Claude)
1. Visit https://console.anthropic.com/
2. Sign in or create account
3. Navigate to API Keys section
4. Create a new key
5. Copy and paste into `.env` as `ANTHROPIC_API_KEY`

### Google (Gemini)
1. Visit https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Create API key
4. Copy and paste into `.env` as `GOOGLE_API_KEY`

## Environment Variable Reference

### Backend (.env)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OPENAI_API_KEY` | Secret | - | OpenAI API key for GPT models |
| `ANTHROPIC_API_KEY` | Secret | - | Anthropic API key for Claude |
| `GOOGLE_API_KEY` | Secret | - | Google API key for Gemini |
| `LLM_PROVIDER` | Config | `openai` | LLM provider: openai, anthropic, google |
| `LLM_MODEL` | Config | `gpt-4` | Model name (provider-specific) |
| `HF_HOME` | Path | `/path/to/models` | HuggingFace model cache directory |
| `LOG_LEVEL` | Config | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR |
| `ASR_ENABLED` | Boolean | `true` | Enable audio transcription |
| `ASR_BACKEND` | Config | `mlx` | ASR backend: mlx, whisper |
| `DEVICE` | Config | `mps` | Compute device: mps, cuda, cpu |
| `CHROMA_HOST` | Config | `localhost` | ChromaDB host |
| `CHROMA_PORT` | Number | `8001` | ChromaDB port |
| `WORKER_PORT` | Number | `8002` | Worker API port |
| `ALLOWED_ORIGINS` | List | See example | CORS allowed origins |

### Frontend (frontend/.env)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_API_URL` | URL | `http://localhost:8002` | Backend API endpoint |
| `VITE_UPLOAD_USERNAME` | String | `uploader` | Copyparty upload username |
| `VITE_UPLOAD_PASSWORD` | String | `docusearch2024` | Copyparty upload password |

## Security Best Practices

### ✅ DO:
- ✅ Keep `.env` files in `.gitignore` (already configured)
- ✅ Use different passwords in production
- ✅ Use dedicated upload-only account for frontend
- ✅ Rotate API keys periodically
- ✅ Use environment-specific `.env` files (`.env.production`, `.env.development`)
- ✅ Store production secrets in secure vault (AWS Secrets Manager, 1Password, etc.)

### ❌ DON'T:
- ❌ Commit `.env` files to git
- ❌ Share `.env` files via email/Slack
- ❌ Put backend secrets in `frontend/.env`
- ❌ Use production API keys in development
- ❌ Hardcode secrets in source code

## Troubleshooting

### Backend can't find API key
```bash
# Check if .env exists
ls -la .env

# Check if variable is set
grep OPENAI_API_KEY .env

# Check if services can read it
docker-compose config | grep OPENAI
```

### Frontend can't access backend API
```bash
# Check VITE_API_URL
cd frontend
grep VITE_API_URL .env

# Restart dev server to load new env vars
npm run dev
```

### CORS errors in browser
```bash
# Check allowed origins in backend .env
grep ALLOWED_ORIGINS .env

# Should include http://localhost:3000
# Restart worker after changes:
./scripts/stop-all.sh && ./scripts/start-all.sh
```

### Upload authentication fails
```bash
# Check credentials match in both places:
# 1. docker/Dockerfile.copyparty (line 74)
grep 'uploader:' docker/Dockerfile.copyparty

# 2. frontend/.env
cd frontend
grep VITE_UPLOAD frontend/.env

# Rebuild Copyparty if credentials changed:
docker-compose -f docker/docker-compose.yml up -d --build copyparty
```

## Production Deployment

For production deployments:

1. **Use environment-specific files:**
   ```bash
   .env.production      # Backend production
   frontend/.env.production  # Frontend production
   ```

2. **Change all default passwords:**
   - Copyparty upload password
   - Admin credentials
   - Database passwords

3. **Use secret management:**
   - AWS Secrets Manager
   - HashiCorp Vault
   - Docker Secrets
   - Kubernetes Secrets

4. **Set restrictive CORS:**
   ```env
   ALLOWED_ORIGINS=https://yourdomain.com
   ```

5. **Enable HTTPS:**
   ```env
   VITE_API_URL=https://api.yourdomain.com
   ```

## Environment File Locations

```
tkr-docusearch/
├── .env                    # Backend configuration (gitignored)
├── .env.example            # Backend template (committed)
├── frontend/
│   ├── .env               # Frontend configuration (gitignored)
│   └── .env.example       # Frontend template (committed)
└── docs/
    └── ENVIRONMENT_SETUP.md  # This file
```

## Support

For issues or questions:
- Check logs: `tail -f logs/worker-native.log`
- Review status: `./scripts/status.sh`
- GitHub Issues: [Create an issue](https://github.com/yourusername/tkr-docusearch/issues)
