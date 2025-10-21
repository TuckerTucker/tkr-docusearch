# Research Bot Vision Setup Guide

**Version:** 1.0
**Last Updated:** 2025-10-21
**Status:** Production Ready

---

## Overview

The Research Bot Vision feature enables multimodal AI responses by sending **both text and visual page thumbnails** to LLMs. This allows models like GPT-4 Vision, Claude with vision, and Gemini to analyze document layouts, diagrams, charts, and other visual content alongside extracted text.

### Why Vision Mode?

**Standard Text Mode:**
- Sends markdown text extracted from documents
- Works well for text-heavy documents
- Faster and cheaper (~10K tokens per query)

**Vision Mode (This Guide):**
- Sends text + page thumbnail images to LLM
- Analyzes visual layouts, charts, diagrams, tables
- Better understanding of document structure
- Higher token cost (~20K tokens + image tokens per query)

### Use Cases for Vision

- **Charts & Graphs** - Analyze data visualizations
- **Diagrams** - Understand flowcharts, architecture diagrams
- **Tables** - Better comprehension of complex tables
- **Document Layout** - Understand document structure visually
- **Mixed Content** - Documents with both text and visual elements

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Vision Research Flow                      │
└─────────────────────────────────────────────────────────────┘

1. User Query
   │
   ├─> Search Engine (ColPali)
   │   ├─> Visual Collection (image embeddings)
   │   └─> Text Collection (text embeddings)
   │
2. Context Builder
   │
   ├─> Extract Text Context (markdown)
   │
   └─> Extract Image URLs (page thumbnails)
       │
       ├─> Local Path: data/page_images/abc123/page001_thumb.jpg
       │
       └─> Convert to Absolute URL:
           │
           ├─> WITHOUT NGROK (Local Only):
           │   http://localhost:8002/images/abc123/page001_thumb.jpg
           │   ⚠️  NOT accessible by remote LLM APIs
           │
           └─> WITH NGROK (Remote Access):
               https://abc123.ngrok-free.app/images/abc123/page001_thumb.jpg
               ✅ Accessible by OpenAI, Anthropic, Google APIs

3. LiteLLM Client
   │
   └─> complete_with_context_and_images()
       │
       ├─> Sends: Query + Text Context + Image URLs
       │
       └─> LLM (GPT-4 Vision / Claude / Gemini)
           │
           └─> Analyzes text + images
               │
               └─> Returns answer with citations

4. Frontend
   │
   └─> Displays answer with bidirectional highlighting
```

### Why Ngrok is Required

**The Problem:**
- Document thumbnails are served by worker API at `http://localhost:8002`
- OpenAI, Anthropic, Google APIs run on **remote servers**
- Remote servers cannot access `localhost:8002` (local network only)

**The Solution:**
- **Ngrok** creates a public tunnel to your local worker API
- Converts `http://localhost:8002` → `https://abc123.ngrok-free.app`
- LLM APIs can fetch images via the public tunnel URL

**Architecture:**
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   LLM API    │────>│    Ngrok     │────>│ Worker API   │
│  (Remote)    │     │   (Tunnel)   │     │ (localhost)  │
└──────────────┘     └──────────────┘     └──────────────┘
  OpenAI/etc         Public Internet       Port 8002

  Fetches:              Routes:           Serves:
  https://...           Traffic to        /images/abc/
                        localhost:8002    page001.jpg
```

---

## Prerequisites

### Required Services

1. **DocuSearch Running**
   - ChromaDB (port 8001)
   - Copyparty (port 8000)
   - Worker API (port 8002)
   - Documents uploaded and indexed

2. **Ngrok Installed**
   ```bash
   # macOS (Homebrew)
   brew install ngrok

   # Linux (Snap)
   snap install ngrok

   # Manual (all platforms)
   # Download from: https://ngrok.com/download
   ```

3. **Ngrok Account** (Free Tier OK)
   - Sign up at: https://dashboard.ngrok.com/signup
   - Get auth token: https://dashboard.ngrok.com/get-started/your-authtoken

4. **LLM API Key**
   - OpenAI API key (for GPT-4 Vision) **recommended**
   - Anthropic API key (for Claude with vision)
   - Google API key (for Gemini with vision)

### Verify Prerequisites

```bash
# Check ngrok installed
ngrok version
# Expected: ngrok version 3.x.x

# Check DocuSearch running
./scripts/status.sh
# Expected: All services "Running"

# Check worker API serving images
curl http://localhost:8002/health
# Expected: {"status": "healthy"}
```

---

## Step-by-Step Setup

### Step 1: Configure Ngrok Authentication

**First Time Only:**

```bash
# Replace YOUR_AUTH_TOKEN with token from ngrok dashboard
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

**Verify:**
```bash
cat ~/.ngrok2/ngrok.yml
# Should show your authtoken
```

### Step 2: Start Ngrok Tunnel

**Option A: Using Automated Script (Recommended)**

```bash
# From project root
./scripts/start-vision-research.sh
```

**Expected Output:**
```
🔧 Starting Vision Research Setup...
✅ Ngrok already running (or starting)
✅ Ngrok URL: https://abc123-456-789.ngrok-free.app
✅ Updated .env with ngrok URL
🚀 Starting research API...
✅ Vision research ready!
   Ngrok URL: https://abc123-456-789.ngrok-free.app
   API: http://localhost:8004
   Logs: logs/research-api.log
```

**Option B: Manual Start**

```bash
# Terminal 1: Start ngrok tunnel
ngrok http 8000

# Expected Output:
# Forwarding  https://abc123-456-789.ngrok-free.app -> http://localhost:8000

# Copy the https:// URL (the ngrok URL)
# Terminal 2: Update .env
echo "NGROK_URL=https://abc123-456-789.ngrok-free.app" >> .env
echo "RESEARCH_VISION_ENABLED=true" >> .env
```

**Important Notes:**
- Ngrok URL changes **every restart** (free tier)
- Paid ngrok plans provide static URLs
- Keep ngrok terminal open while using vision

### Step 3: Configure Environment Variables

Edit `.env` file:

```bash
# ============================================================================
# Vision Configuration
# ============================================================================

# Enable vision mode (requires ngrok)
RESEARCH_VISION_ENABLED=true

# Ngrok public URL (auto-updated by start-vision-research.sh)
NGROK_URL=https://abc123-456-789.ngrok-free.app

# Maximum images to send to LLM (default: 10)
RESEARCH_MAX_IMAGES=10

# Base URL for image serving (auto-configured)
# - Local mode: http://localhost:8002
# - Vision mode: Uses NGROK_URL
RESEARCH_IMAGE_BASE_URL=${NGROK_URL}

# ============================================================================
# LLM Configuration (Existing)
# ============================================================================

# Choose vision-capable model
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-vision-preview  # or gpt-4-turbo (has vision)

# API Key
OPENAI_API_KEY=sk-your-key-here

# Alternative providers:
# LLM_PROVIDER=anthropic
# LLM_MODEL=claude-3-opus-20240229
# ANTHROPIC_API_KEY=sk-ant-your-key

# LLM_PROVIDER=google
# LLM_MODEL=gemini-1.5-pro
# GOOGLE_API_KEY=your-key
```

### Step 4: Start/Restart Research API

**If using start-vision-research.sh (already started):**
- Research API is already running with vision enabled

**If manual setup:**

```bash
# Restart research API to pick up new config
./scripts/stop-all.sh
./scripts/start-all.sh

# Or restart just research API
pkill -f "uvicorn.*research"
./scripts/start-research-api.sh
```

### Step 5: Verify Vision Mode Active

**Check Logs:**
```bash
tail -f logs/research-api.log

# Look for:
# "Vision support enabled=True"
# "NGROK_URL loaded: https://..."
```

**Test API Health:**
```bash
curl http://localhost:8004/api/research/health

# Expected:
# {"status": "healthy", "components": {...}}
```

**Check Environment:**
```bash
# In Python shell or script
python3 << EOF
import os
from dotenv import load_dotenv
load_dotenv()

print("Vision Enabled:", os.getenv("RESEARCH_VISION_ENABLED"))
print("Ngrok URL:", os.getenv("NGROK_URL"))
print("Max Images:", os.getenv("RESEARCH_MAX_IMAGES", "10"))
EOF
```

---

## Testing Vision Mode

### Test 1: Simple Text Query (Baseline)

**Query:**
```
What are the main topics covered in the documents?
```

**Expected:**
- Answer with text citations
- No mention of visual analysis
- ~2-3 second response time
- ~10K-15K tokens used

### Test 2: Visual Query (Diagrams/Charts)

**Query:**
```
Describe any charts, graphs, or diagrams you see in the documents.
What data do they show?
```

**Expected:**
- Answer references visual elements
- Describes chart types, axes, data points
- ~3-5 second response time
- ~20K-30K tokens used (includes image tokens)
- Metadata shows: `vision_enabled: true`, `images_sent: 5-10`

### Test 3: Table Analysis

**Query:**
```
What tables are in the documents? Summarize the data in the tables.
```

**Expected:**
- Better table comprehension than text-only mode
- Describes table structure and contents
- May interpret visual table layouts

### Verify Vision Active in Response

**Check API Response:**
```bash
# Submit query via API
curl -X POST http://localhost:8004/api/research/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What charts are in the documents?",
    "num_sources": 10,
    "search_mode": "hybrid"
  }' | jq .

# Look for in metadata:
# "vision_enabled": true
# "images_sent": 5  (or other number)
# "image_tokens": 5000  (estimated)
```

### Example Test Queries

**Good for Vision:**
- "What does the architecture diagram show?"
- "Summarize the data in the bar chart on page 3"
- "What is the structure of the flowchart?"
- "Describe the layout of the infographic"
- "What patterns do you see in the graphs?"

**Not Needed for Vision:**
- "What is the main topic?" (text is sufficient)
- "Summarize the introduction" (text is sufficient)
- "List the key findings" (text is sufficient)

---

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RESEARCH_VISION_ENABLED` | `false` | Enable/disable vision mode |
| `NGROK_URL` | (required) | Public ngrok URL for image access |
| `RESEARCH_MAX_IMAGES` | `10` | Max images to send per query |
| `RESEARCH_IMAGE_BASE_URL` | `http://localhost:8002` | Base URL for images (auto-set) |
| `LLM_MODEL` | `gpt-4-turbo` | Vision-capable model |

### Vision-Capable Models

**OpenAI:**
- `gpt-4-vision-preview` - Dedicated vision model
- `gpt-4-turbo` - Includes vision (recommended)
- `gpt-4o` - Latest with vision

**Anthropic:**
- `claude-3-opus-20240229` - Best vision
- `claude-3-sonnet-20240229` - Good vision, cheaper
- `claude-3-haiku-20240307` - Fast, basic vision

**Google:**
- `gemini-1.5-pro` - Excellent vision, 1M token context
- `gemini-1.5-flash` - Fast vision

### Image Processing Settings

**In `context_builder.py` (advanced):**

```python
# Default settings (good for most use cases)
max_images = int(os.getenv("RESEARCH_MAX_IMAGES", "10"))  # Top 10 visual sources
image_detail = "auto"  # Let LLM choose resolution

# To change:
# 1. Lower images for faster/cheaper queries:
#    RESEARCH_MAX_IMAGES=5
#
# 2. Higher images for better coverage:
#    RESEARCH_MAX_IMAGES=15  (increases cost!)
```

---

## Cost Implications

### Token Costs

**Text-Only Mode:**
- Prompt: ~10,000 text tokens
- Completion: ~500 tokens
- **Total: ~10,500 tokens**

**Vision Mode:**
- Prompt: ~10,000 text tokens + 10 images × 1,000 tokens = **~20,000 tokens**
- Completion: ~500 tokens
- **Total: ~20,500 tokens**

**Cost Multiplier: ~2x**

### Per-Query Cost Estimates

**GPT-4 Turbo (with vision):**
- Input: $10 per 1M tokens
- Output: $30 per 1M tokens
- **Text-only: $0.10-$0.15 per query**
- **Vision: $0.20-$0.30 per query**

**Claude 3 Opus:**
- Input: $15 per 1M tokens
- Output: $75 per 1M tokens
- **Text-only: $0.15-$0.20**
- **Vision: $0.30-$0.40**

**Gemini 1.5 Pro:**
- Input: $3.50 per 1M tokens
- Output: $10.50 per 1M tokens
- **Text-only: $0.03-$0.05**
- **Vision: $0.07-$0.10** ⭐ Most affordable

### Cost Optimization Tips

1. **Use vision selectively** - Enable only when needed
2. **Reduce max_images** - Set `RESEARCH_MAX_IMAGES=5` instead of 10
3. **Choose cheaper models** - Gemini 1.5 Pro or Claude Sonnet
4. **Filter queries** - Only use vision for visual-heavy documents

### Ngrok Free Tier Limits

**Free Plan:**
- ✅ 1 active tunnel at a time
- ✅ Unlimited bandwidth
- ✅ HTTPS encryption
- ⚠️ **Random URL** (changes every restart)
- ⚠️ **60 requests/minute limit**

**If hitting limits:**
- Upgrade to Ngrok Basic ($8/month) for:
  - Static domain (no URL changes)
  - 120 requests/minute
  - Better reliability

---

## Troubleshooting

### Issue: "Vision not working, only text responses"

**Symptoms:**
- API returns text-only answers
- No visual analysis in responses
- Metadata shows: `vision_enabled: false` or `images_sent: 0`

**Diagnosis:**
```bash
# Check .env config
grep RESEARCH_VISION_ENABLED .env
# Expected: RESEARCH_VISION_ENABLED=true

grep NGROK_URL .env
# Expected: NGROK_URL=https://...ngrok-free.app

# Check research API logs
tail -f logs/research-api.log | grep -i vision
# Expected: "Vision support enabled=True"
```

**Solutions:**
1. Verify `RESEARCH_VISION_ENABLED=true` in `.env`
2. Verify `NGROK_URL` is set and valid
3. Restart research API: `./scripts/stop-all.sh && ./scripts/start-all.sh`
4. Check model supports vision (must be GPT-4, Claude 3, or Gemini)

---

### Issue: "Image URLs return 404"

**Symptoms:**
- LLM complains "cannot load images"
- API logs show image fetch errors
- Ngrok dashboard shows 404s

**Diagnosis:**
```bash
# Test ngrok URL directly
curl https://YOUR-NGROK-URL.ngrok-free.app/health
# Expected: {"status": "healthy"}

# Test image path
curl https://YOUR-NGROK-URL.ngrok-free.app/images/abc123/page001_thumb.jpg
# Expected: Image binary data (or 200 OK)
```

**Solutions:**
1. **Check ngrok running:**
   ```bash
   pgrep -f ngrok
   # Should return PID number

   # If not running:
   ./scripts/start-vision-research.sh
   ```

2. **Verify worker API port:**
   ```bash
   # Ngrok must tunnel port 8000 (Copyparty) not 8002 (Worker)
   # Check ngrok config:
   curl http://localhost:4040/api/tunnels | jq

   # Should show: "config": { "addr": "http://localhost:8000" }
   ```

3. **Check image files exist:**
   ```bash
   ls -la data/page_images/
   # Should show document directories with thumbs
   ```

4. **Test image endpoint locally:**
   ```bash
   # Find a real image path from ChromaDB metadata
   curl http://localhost:8002/images/YOUR-DOC-ID/page001_thumb.jpg --output test.jpg
   # Should download image
   ```

---

### Issue: "Ngrok URL changes constantly"

**Symptoms:**
- Must re-run setup after every restart
- URLs in logs are outdated
- Vision breaks after ngrok restart

**Solutions:**

**Short-term:**
- Re-run setup script after each ngrok restart:
  ```bash
  ./scripts/start-vision-research.sh
  ```

**Long-term (Recommended):**
- Upgrade to Ngrok paid plan ($8/mo)
- Get static domain: `your-app.ngrok-free.app`
- Set once in `.env`, never changes:
  ```bash
  # Start ngrok with static domain
  ngrok http 8000 --domain=your-app.ngrok-free.app

  # Update .env once
  NGROK_URL=https://your-app.ngrok-free.app
  ```

---

### Issue: "Rate limit errors from ngrok"

**Symptoms:**
- "429 Too Many Requests" from ngrok
- Vision works for first few queries, then fails
- Ngrok dashboard shows rate limit warnings

**Diagnosis:**
```bash
# Check ngrok limits in dashboard
open https://dashboard.ngrok.com/usage

# Check request rate
curl http://localhost:4040/api/tunnels | jq '.tunnels[0].metrics'
```

**Solutions:**

1. **Reduce images sent:**
   ```bash
   # In .env
   RESEARCH_MAX_IMAGES=5  # Down from 10
   ```

2. **Space out queries:**
   - Wait 1-2 seconds between queries
   - Don't spam refresh on research page

3. **Upgrade ngrok plan:**
   - Free: 60 requests/minute
   - Basic ($8/mo): 120 requests/minute
   - Pro ($20/mo): 240 requests/minute

---

### Issue: "High API costs"

**Symptoms:**
- Unexpectedly high OpenAI/Anthropic bills
- Queries cost $0.50+ each

**Diagnosis:**
```bash
# Check metadata in API response
curl -X POST http://localhost:8004/api/research/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}' | jq '.metadata'

# Look at:
# - context_tokens: Should be <15,000
# - images_sent: Should be <10
# - image_tokens: Should be <10,000
```

**Solutions:**

1. **Reduce image count:**
   ```bash
   RESEARCH_MAX_IMAGES=3  # Minimum for useful vision
   ```

2. **Switch to cheaper model:**
   ```bash
   # In .env
   LLM_PROVIDER=google
   LLM_MODEL=gemini-1.5-pro  # 70% cheaper than GPT-4
   ```

3. **Use vision selectively:**
   ```bash
   # Disable by default
   RESEARCH_VISION_ENABLED=false

   # Enable manually when needed
   echo "RESEARCH_VISION_ENABLED=true" >> .env
   # Make query
   echo "RESEARCH_VISION_ENABLED=false" >> .env
   ```

4. **Monitor costs:**
   - OpenAI: https://platform.openai.com/usage
   - Anthropic: https://console.anthropic.com/usage
   - Google: https://console.cloud.google.com/billing

---

### Issue: "Worker API not accessible via ngrok"

**Symptoms:**
- Ngrok URL works for Copyparty (port 8000)
- But images served by Worker (port 8002) return 404
- Logs show "Image fetch failed"

**Root Cause:**
- Ngrok tunnels port 8000 (Copyparty)
- Worker API serves images on port 8002
- Need to tunnel 8000 and proxy images to 8002

**Solution:**
This is handled by the existing setup where:
1. Copyparty (8000) is publicly accessible via ngrok
2. Worker API (8002) remains local
3. Context builder uses Worker API paths that are served via Copyparty static file serving

**Verify:**
```bash
# Images should be accessible via Copyparty
curl http://localhost:8000/page_images/YOUR-DOC/page001_thumb.jpg
# If this works, ngrok will also work
```

---

### Issue: "Cannot install ngrok"

**Solutions by Platform:**

**macOS:**
```bash
# Via Homebrew
brew install ngrok

# Via downloaded binary
cd ~/Downloads
unzip ngrok-v3-stable-darwin-amd64.zip
sudo mv ngrok /usr/local/bin/
chmod +x /usr/local/bin/ngrok
```

**Linux:**
```bash
# Via Snap
sudo snap install ngrok

# Via downloaded binary
cd /tmp
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/
```

**Windows:**
```powershell
# Via Chocolatey
choco install ngrok

# Via Scoop
scoop install ngrok

# Manual: Download from https://ngrok.com/download
# Extract ngrok.exe to C:\Windows\System32\
```

---

## Advanced: Alternative to Ngrok

### Option 1: Localtunnel (Free alternative)

```bash
# Install
npm install -g localtunnel

# Start tunnel
lt --port 8000 --subdomain your-app

# Output: https://your-app.loca.lt

# Update .env
NGROK_URL=https://your-app.loca.lt
```

**Pros:** Free, no account needed
**Cons:** Less reliable, slower

---

### Option 2: Cloudflare Tunnel (Free, production-ready)

```bash
# Install cloudflared
brew install cloudflared

# Authenticate
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create docusearch

# Start tunnel
cloudflared tunnel --url http://localhost:8000 run docusearch

# Update .env with tunnel URL
```

**Pros:** Free forever, reliable, static URL
**Cons:** More complex setup

---

### Option 3: Self-hosted with Public IP

**If you have a VPS:**

```bash
# SSH tunnel from VPS to local
ssh -R 8000:localhost:8000 user@your-vps.com

# Update .env
NGROK_URL=https://your-vps.com
```

**Pros:** Full control, no third-party
**Cons:** Requires VPS, complex networking

---

## Best Practices

### When to Use Vision

**Use Vision For:**
- ✅ Documents with charts, graphs, diagrams
- ✅ Infographics and visual layouts
- ✅ Complex tables (better than text extraction)
- ✅ Architecture diagrams, flowcharts
- ✅ Annotated images or screenshots

**Skip Vision For:**
- ❌ Plain text documents (PDFs with no images)
- ❌ Simple queries ("What is the title?")
- ❌ When cost is a concern
- ❌ When speed matters (text-only is 2x faster)

---

### Security Considerations

**Risks:**
1. **Public tunnel exposes Worker API** - Anyone with ngrok URL can access your documents
2. **No authentication** - Ngrok free has no password protection
3. **Temporary exposure** - Images accessible during query processing

**Mitigations:**
1. **Stop ngrok when not needed:**
   ```bash
   pkill ngrok  # Stop tunnel
   ```

2. **Use ngrok auth (paid):**
   ```bash
   ngrok http 8000 --basic-auth="username:password"
   ```

3. **Monitor access:**
   ```bash
   # Watch ngrok dashboard
   open http://localhost:4040
   # Shows all requests to tunnel
   ```

4. **Time-box usage:**
   - Only start ngrok for vision queries
   - Stop immediately after
   - Don't leave running overnight

5. **Firewall worker API:**
   ```bash
   # Block external access to 8002 (redundant but safe)
   sudo ufw deny 8002
   ```

---

### Performance Optimization

**Reduce Latency:**
1. **Limit images:** `RESEARCH_MAX_IMAGES=5`
2. **Use faster model:** `gemini-1.5-flash` instead of `gpt-4`
3. **Optimize thumbnails:** Ensure Worker generates small thumbs (<100KB)

**Reduce Cost:**
1. **Lower image quality:** Thumbnails at 150x150px (default is good)
2. **Fewer sources:** `num_sources=5` instead of 10
3. **Choose Gemini:** 70% cheaper than GPT-4 with vision

**Monitor Performance:**
```bash
# Watch API response times
tail -f logs/research-api.log | grep "processing_time_ms"

# Watch ngrok latency
curl http://localhost:4040/api/tunnels | jq '.tunnels[0].metrics.http'
```

---

## Example Queries

### Query 1: Chart Analysis

**Query:**
```
What data is shown in the bar chart on page 5?
What are the key trends?
```

**Expected Output:**
```
The bar chart on page 5 shows quarterly revenue growth from 2020-2023 [1].
Key trends include a 15% year-over-year increase in Q4 2022 [1], followed by
a slight decline in Q1 2023 [1]. The chart uses blue bars for actual revenue
and orange bars for projected revenue [1].
```

**Metadata:**
```json
{
  "vision_enabled": true,
  "images_sent": 3,
  "image_tokens": 3000,
  "context_tokens": 12500,
  "total_tokens": 15500
}
```

---

### Query 2: Diagram Understanding

**Query:**
```
Describe the system architecture diagram.
What are the main components and how do they connect?
```

**Expected Output:**
```
The architecture diagram shows a three-tier system [1]. The frontend layer
consists of React components communicating via REST API [1]. The middle tier
contains the FastAPI server and business logic [2]. The backend layer includes
PostgreSQL for data storage and Redis for caching [2]. Arrows indicate data
flow from frontend → API → database, with bidirectional communication [1][2].
```

---

### Query 3: Table Comparison

**Query:**
```
Compare the financial tables in documents A and B.
What are the main differences?
```

**Expected Output:**
```
Document A shows revenue of $1.2M in 2022 [1], while Document B reports $1.5M
for the same period [2]. Document A's table includes a breakdown by product
category [1], whereas Document B aggregates all products [2]. Both use similar
table structures with quarters as rows and metrics as columns [1][2].
```

---

## FAQ

### Q: Do I always need ngrok for Research Bot?

**A:** No, only for **vision mode**. Text-only mode works fine without ngrok.

---

### Q: Can I use a static ngrok URL?

**A:** Yes, with ngrok paid plan ($8/month) you get a permanent subdomain.

---

### Q: Does vision mode work with all LLM providers?

**A:** No, only vision-capable models:
- ✅ OpenAI GPT-4 Vision, GPT-4 Turbo
- ✅ Anthropic Claude 3 (Opus, Sonnet, Haiku)
- ✅ Google Gemini 1.5 Pro/Flash
- ❌ GPT-3.5 (no vision)
- ❌ Older Claude 2 models

---

### Q: How much do vision queries cost vs text-only?

**A:** Approximately **2x more** due to image tokens (~1000 tokens per image).

---

### Q: Can I use vision for audio files (MP3/WAV)?

**A:** No, vision only applies to visual page images (PDF, DOCX, PPTX pages).
Audio files already include cover art thumbnails in text mode.

---

### Q: What if LLM fails to analyze images?

**A:** The system automatically falls back to text-only if:
1. Vision is disabled
2. No visual sources found
3. Image URLs are invalid

Check logs for: "Using text-only completion (no images)"

---

### Q: Can I self-host vision without ngrok?

**A:** Yes, if you deploy DocuSearch on a public VPS with a static IP/domain.
Then set `RESEARCH_IMAGE_BASE_URL=https://yourdomain.com` in `.env`.

---

## Additional Resources

### Documentation
- **Research Bot User Guide:** `/docs/RESEARCH_BOT_GUIDE.md`
- **API Reference:** `/docs/API_REFERENCE.md`
- **Architecture:** `/.context-kit/_specs/research-bot-architecture.md`

### External Resources
- **Ngrok Docs:** https://ngrok.com/docs
- **OpenAI Vision API:** https://platform.openai.com/docs/guides/vision
- **Claude Vision:** https://docs.anthropic.com/claude/docs/vision
- **Gemini Vision:** https://ai.google.dev/gemini-api/docs/vision

### Support
- **GitHub Issues:** https://github.com/yourusername/tkr-docusearch/issues
- **Ngrok Support:** https://ngrok.com/support

---

## Appendix: Start-Vision-Research.sh Explained

**What the script does:**

1. **Check ngrok installed** - Verifies `ngrok` command exists
2. **Start ngrok** - Launches `ngrok http 8000` in background
3. **Get ngrok URL** - Queries ngrok API at `localhost:4040` for public URL
4. **Update .env** - Writes `NGROK_URL` and enables vision
5. **Start research API** - Launches or restarts the research service

**Script breakdown:**

```bash
#!/bin/bash
set -e  # Exit on any error

# Check ngrok installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok not found. Install: brew install ngrok"
    exit 1
fi

# Start ngrok if not running
if pgrep -f "ngrok http 8000" > /dev/null; then
    echo "✅ Ngrok already running"
else
    echo "🚀 Starting ngrok tunnel..."
    nohup ngrok http 8000 > logs/ngrok.log 2>&1 &
    sleep 3  # Wait for ngrok to initialize
fi

# Get public URL from ngrok API
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url')

# Validate URL
if [ -z "$NGROK_URL" ] || [ "$NGROK_URL" = "null" ]; then
    echo "❌ Failed to get ngrok URL"
    exit 1
fi

echo "✅ Ngrok URL: $NGROK_URL"

# Update .env file
if grep -q "^NGROK_URL=" .env; then
    # Update existing line (macOS compatible sed)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|^NGROK_URL=.*|NGROK_URL=$NGROK_URL|" .env
    else
        sed -i "s|^NGROK_URL=.*|NGROK_URL=$NGROK_URL|" .env
    fi
else
    # Add new line
    echo "NGROK_URL=$NGROK_URL" >> .env
fi

# Enable vision
if grep -q "^RESEARCH_VISION_ENABLED=" .env; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|^RESEARCH_VISION_ENABLED=.*|RESEARCH_VISION_ENABLED=true|" .env
    else
        sed -i "s|^RESEARCH_VISION_ENABLED=.*|RESEARCH_VISION_ENABLED=true|" .env
    fi
else
    echo "RESEARCH_VISION_ENABLED=true" >> .env
fi

echo "✅ Updated .env with ngrok URL"

# Start research API
echo "🚀 Starting research API..."
./scripts/start-research-api.sh

echo ""
echo "✅ Vision research ready!"
echo "   Ngrok URL: $NGROK_URL"
echo "   API: http://localhost:8004"
echo "   Logs: logs/research-api.log"
```

---

**Happy Researching with Vision! 👁️🔍**
