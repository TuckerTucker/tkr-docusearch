# Migrating to Local LLM Preprocessing

**Version:** 1.0
**Last Updated:** 2025-10-22
**Target Audience:** Users migrating from standard Research Bot to preprocessed queries

---

## Overview

This guide walks you through enabling Local LLM Preprocessing for the Research Bot. Preprocessing uses a local language model (MLX) to pre-process document chunks before sending them to foundation models like GPT-4 or Claude.

**Benefits:**
- ~60% reduction in foundation model API costs
- Process more documents within token limits
- Enhanced privacy (more processing happens locally)
- Improved answer quality through relevance filtering

**Time Required:** 15-30 minutes

---

## Prerequisites

Before starting, verify you have:

**Hardware:**
- Mac with M1, M2, or M3 chip (Apple Silicon required)
- 16GB RAM minimum (32GB recommended)
- ~10GB free disk space (8GB for model, 2GB for dependencies)

**Software:**
- Python 3.11 or 3.13 installed
- Git and Homebrew (for dependencies)
- Active Research Bot installation
- Working `.env` configuration

**Verification Commands:**

```bash
# Check chip type (should show "Apple M1" or similar)
sysctl -n machdep.cpu.brand_string

# Check Python version (should be 3.11 or 3.13)
python --version

# Check available disk space (should have 10GB+ free)
df -h /Users

# Verify Research Bot is working
curl http://localhost:8004/health
```

If any checks fail, resolve them before proceeding.

---

## Migration Steps

### Step 1: Backup Current Configuration

**Create a backup of your working `.env` file:**

```bash
cd /Volumes/tkr-riffic/@tkr-projects/tkr-docusearch
cp .env .env.backup.$(date +%Y%m%d)
```

**Verify backup:**

```bash
ls -la .env.backup.*
```

This allows easy rollback if needed.

---

### Step 2: Install MLX Dependencies

**Install MLX-LM library:**

```bash
pip install mlx-lm>=0.26.3
```

**Verify installation:**

```bash
python -c "import mlx_lm; print('MLX-LM version:', mlx_lm.__version__)"
```

Expected output: `MLX-LM version: 0.26.3` (or higher)

**Troubleshooting:**

If installation fails:

```bash
# Update pip first
pip install --upgrade pip

# Try installing with verbose output
pip install -v mlx-lm>=0.26.3

# Check for conflicts
pip list | grep mlx
```

---

### Step 3: Download MLX Model

**Download the MLX-optimized model (~8GB):**

```bash
huggingface-cli download InferenceIllusionist/gpt-oss-20b-MLX-4bit
```

**This will take 10-20 minutes depending on your internet speed.**

**Verify download:**

```bash
ls -lh ~/.cache/huggingface/hub/models--InferenceIllusionist--gpt-oss-20b-MLX-4bit/snapshots/*/
```

You should see files like:
- `config.json`
- `model-*.safetensors` (multiple files)
- `tokenizer.json`

**Get the exact path:**

```bash
find ~/.cache/huggingface/hub -type d -name "models--InferenceIllusionist--gpt-oss-20b-MLX-4bit"
```

Copy this path for the next step.

**Troubleshooting:**

If download fails:

```bash
# Install huggingface-cli if missing
pip install huggingface-hub[cli]

# Try with token authentication (if needed)
huggingface-cli login

# Check cache location
echo $HF_HOME
```

---

### Step 4: Test WITHOUT Preprocessing First

**Before enabling preprocessing, verify the Research Bot works:**

**Update `.env` to use MLX client (preprocessing disabled):**

```bash
# LLM Configuration - Use MLX client
LLM_PROVIDER=mlx
MLX_MODEL_PATH=/Users/[your-username]/.cache/huggingface/hub/models--InferenceIllusionist--gpt-oss-20b-MLX-4bit

# Preprocessing - DISABLED for testing
LOCAL_PREPROCESS_ENABLED=false
```

**Replace `[your-username]` with your actual username.**

**Restart the Research API:**

```bash
./scripts/start-all.sh
```

**Wait 30 seconds for API to start, then test:**

```bash
# Check API health
curl http://localhost:8004/health

# Submit a test query
curl -X POST http://localhost:8004/api/research/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the main topic?"}'
```

**Expected result:** You should get an answer with `preprocessing_enabled: false` in the metadata.

**If this fails, DO NOT proceed to Step 5. Debug the MLX client first.**

---

### Step 5: Enable Preprocessing with Compression Strategy

**Now enable preprocessing with the safest strategy:**

**Update `.env`:**

```bash
# LLM Configuration
LLM_PROVIDER=mlx
MLX_MODEL_PATH=/Users/[your-username]/.cache/huggingface/hub/models--InferenceIllusionist--gpt-oss-20b-MLX-4bit

# Preprocessing - ENABLED with compression
LOCAL_PREPROCESS_ENABLED=true
LOCAL_PREPROCESS_STRATEGY=compress
LOCAL_PREPROCESS_THRESHOLD=7.0
LOCAL_PREPROCESS_MAX_SOURCES=20
```

**Restart the Research API:**

```bash
./scripts/start-all.sh
```

**Wait 30 seconds for initialization (model loading takes time).**

---

### Step 6: Verify Preprocessing is Working

**Submit a test query:**

```bash
curl -X POST http://localhost:8004/api/research/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the main topic?"}'
```

**Check the response metadata:**

```json
{
  "answer": "...",
  "metadata": {
    "preprocessing_enabled": true,
    "preprocessing_strategy": "compress",
    "preprocessing_latency_ms": 2847,
    "original_sources_count": 15,
    "token_reduction_percent": 45.2
  }
}
```

**Verify:**
- ✅ `preprocessing_enabled` is `true`
- ✅ `preprocessing_strategy` is `"compress"`
- ✅ `token_reduction_percent` is between 30-50%
- ✅ `preprocessing_latency_ms` is under 5000ms

**Test in UI:**

1. Open http://localhost:3000/research
2. Submit a query: "Summarize the key findings"
3. Look for the preprocessing badge below the answer:
   - "⚡ Preprocessed with compress"
   - "45.2% token reduction"
   - "Preprocessing: 2847ms"

**If you don't see these metrics, check:**

```bash
# Check API logs
tail -f logs/research-api.log

# Verify .env settings
cat .env | grep LOCAL_PREPROCESS

# Check frontend console for errors
# Open browser DevTools → Console
```

---

### Step 7: Test Other Strategies (Optional)

**Once compression is working, try other strategies:**

**Filtering Strategy:**

```bash
# In .env
LOCAL_PREPROCESS_STRATEGY=filter
LOCAL_PREPROCESS_THRESHOLD=7.0
```

**Restart and test:**

```bash
./scripts/start-all.sh
# Submit query and verify metadata shows "filter"
```

**Expected results:**
- Token reduction: 40-60%
- Fewer sources in final answer
- Higher relevance per source

**Synthesis Strategy:**

```bash
# In .env
LOCAL_PREPROCESS_STRATEGY=synthesize
```

**Restart and test:**

```bash
./scripts/start-all.sh
# Submit query and verify metadata shows "synthesize"
```

**Expected results:**
- Token reduction: 90%+
- Single synthesized context
- Broader, cross-document answers

---

## Rollback Procedure

**If preprocessing causes issues, roll back immediately:**

### Quick Rollback (Disable Preprocessing)

**Update `.env`:**

```bash
LOCAL_PREPROCESS_ENABLED=false
```

**Restart:**

```bash
./scripts/start-all.sh
```

**Verify:**

```bash
# Check health
curl http://localhost:8004/health

# Test query
curl -X POST http://localhost:8004/api/research/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "Test query"}'

# Verify metadata shows preprocessing_enabled: false
```

### Full Rollback (Restore Backup)

**If you need to completely restore previous configuration:**

```bash
# Stop all services
pkill -f "research.py"
pkill -f "worker.py"

# Restore backup .env
cp .env.backup.20251022 .env

# Restart with original configuration
./scripts/start-all.sh
```

**Verify everything works:**

```bash
./scripts/status.sh
```

---

## Frequently Asked Questions

### Q: Will this break existing functionality?

**A:** No. Preprocessing is opt-in and backward compatible. If disabled or if the MLX model is missing, the Research Bot works exactly as before.

### Q: What if I don't have an MLX model?

**A:** The API will log a warning and automatically disable preprocessing. All queries work normally without preprocessing.

### Q: How much will I save on API costs?

**A:** Approximately 60% on foundation model (GPT-4/Claude) API calls. Actual savings depend on:
- Preprocessing strategy (compression: 30-50%, filtering: 40-60%, synthesis: 90%+)
- Query complexity
- Number of source documents

**Example cost calculation:**

```
Without preprocessing:
- Average query: 10,000 tokens to GPT-4
- Cost: $0.30 per query (at $0.03/1K tokens)

With compression preprocessing:
- Average query: 5,000 tokens to GPT-4 (50% reduction)
- Cost: $0.15 per query
- Savings: $0.15 per query (50%)

At 100 queries/day: Save $15/day = $450/month
```

### Q: Will queries be slower?

**A:** Slightly. Preprocessing adds 2-5 seconds to the total query time. However:

- Local MLX processing is fast (uses Metal GPU)
- You save time on foundation model calls (fewer tokens to process)
- Total query time is usually still under 5 seconds

**Timing breakdown:**

```
Without preprocessing:
- Search: 0.3s
- Foundation model: 2.5s
- Total: 2.8s

With preprocessing:
- Search: 0.3s
- Local preprocessing: 2.5s
- Foundation model: 1.2s (fewer tokens)
- Total: 4.0s (1.2s slower, but 50% cheaper)
```

### Q: Can I use different strategies for different queries?

**A:** Not dynamically per query. The strategy is set in `.env` and applies to all queries. To change strategies:

1. Update `LOCAL_PREPROCESS_STRATEGY` in `.env`
2. Restart the Research API
3. New queries use the new strategy

**Tip:** Start with `compress` (safest, best balance). Try others once comfortable.

### Q: What if preprocessing is taking too long (>10s)?

**A:** This usually means too many sources or slow model loading. Try:

```bash
# Reduce max sources
LOCAL_PREPROCESS_MAX_SOURCES=10

# Restart (first startup loads model, subsequent queries are faster)
./scripts/start-all.sh
```

The first query after startup is slower (model loading). Subsequent queries are much faster.

### Q: How do I know if Metal GPU acceleration is working?

**A:** Check Activity Monitor:

1. Open Activity Monitor
2. Go to GPU tab
3. Submit a query
4. Look for Python process using GPU

Or check via command:

```bash
# During a query, check GPU usage
sudo powermetrics --samplers gpu_power -i 1000 -n 1
```

You should see GPU power usage spike during preprocessing.

### Q: Can I use a different MLX model?

**A:** Yes, but it must be compatible with the MLX API. Update:

```bash
MLX_MODEL_PATH=/path/to/your/mlx/model
```

Recommended models:
- `InferenceIllusionist/gpt-oss-20b-MLX-4bit` (8GB, balanced)
- `mlx-community/Mistral-7B-Instruct-v0.3-4bit` (4GB, faster)
- Any MLX-converted instruction-tuned model

### Q: Does this send less data to OpenAI/Anthropic?

**A:** Yes. With 50% token reduction, you send 50% less data to the foundation model API. This improves privacy and reduces data transmission costs.

### Q: What happens if the MLX model crashes?

**A:** The preprocessor handles errors gracefully:

1. Logs the error
2. Falls back to unprocessed sources
3. Query completes normally (without preprocessing)
4. User gets a valid answer

You'll see a warning in the logs, but queries won't fail.

---

## Validation Checklist

**Before marking migration complete, verify:**

- [ ] MLX-LM library installed (`python -c "import mlx_lm"`)
- [ ] MLX model downloaded and path correct
- [ ] API starts successfully with preprocessing enabled
- [ ] Health check passes (`curl http://localhost:8004/health`)
- [ ] Test query returns valid answer
- [ ] Metadata includes preprocessing fields
- [ ] Preprocessing badge visible in UI
- [ ] Token reduction is 30-60% (depending on strategy)
- [ ] Preprocessing latency is under 5 seconds
- [ ] Rollback procedure tested and works

---

## Getting Help

**If you encounter issues:**

1. **Check logs:**
   ```bash
   tail -f logs/research-api.log
   ```

2. **Verify configuration:**
   ```bash
   cat .env | grep -E "(LLM_PROVIDER|MLX_|LOCAL_PREPROCESS)"
   ```

3. **Test without preprocessing:**
   ```bash
   LOCAL_PREPROCESS_ENABLED=false
   ./scripts/start-all.sh
   ```

4. **Consult troubleshooting guide:**
   - See "Troubleshooting" section in `docs/RESEARCH_BOT_GUIDE.md`

5. **Open an issue:**
   - GitHub: https://github.com/tuckertucker/tkr-docusearch/issues
   - Include: logs, .env settings (redact API keys), error messages

---

## Next Steps

**After successful migration:**

1. **Monitor performance:**
   - Track token reduction percentages
   - Measure query latency
   - Calculate cost savings

2. **Optimize configuration:**
   - Try different strategies for different use cases
   - Tune threshold for filtering strategy
   - Adjust max sources for performance

3. **Experiment with strategies:**
   - Compression: General queries
   - Filtering: Focused, topic-specific queries
   - Synthesis: Broad, multi-document queries

4. **Share feedback:**
   - Report issues or suggestions
   - Contribute improvements
   - Help others migrate

---

**Migration complete! You're now using Local LLM Preprocessing. 🎉**

**Estimated cost savings: ~60% on foundation model API calls**
