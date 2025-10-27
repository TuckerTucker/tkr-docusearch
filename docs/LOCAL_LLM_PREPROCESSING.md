# Local LLM Preprocessing

## Overview

Local LLM preprocessing uses a local MLX model (gpt-oss-20b-4bit) to pre-process search results before sending them to the foundation model. This reduces foundation model costs by ~50% but adds 70-90 seconds of preprocessing latency.

## Status: **DISABLED BY DEFAULT** ✓

Preprocessing is disabled by default to prioritize fast, interactive responses. Users can opt-in globally via environment variable or per-request via API parameter.

## Performance Comparison

| Mode | Total Time | Foundation Cost | Use Case |
|------|-----------|----------------|----------|
| **Without Preprocessing** | ~25-30s | $0.12-0.18 | ✅ Interactive use, demos, development |
| **With Preprocessing** | ~95-120s | $0.05-0.09 | Cost optimization, batch processing |

### Breakdown

**Without Preprocessing (~25-30s total):**
- Search: ~5-10s
- Foundation LLM: ~20-25s
- **No local LLM overhead**

**With Preprocessing (~95-120s total):**
- Search: ~5-10s
- **Local LLM Synthesis: ~70-90s** ⚠️
- Foundation LLM: ~20-25s (reduced input tokens)

## How It Works

### Synthesis Strategy (Default)

The local LLM creates ONE comprehensive summary from ALL search results:

1. **Input**: 16 source chunks (~8,000 tokens) + images
2. **Process**: Local LLM synthesizes into single summary (~2,000 tokens)
3. **Output**: 1 synthesized source sent to foundation model
4. **Result**: 76-86% token reduction, 29-50% cost savings

### Benefits
- ✅ Eliminates redundancy across multiple chunks
- ✅ Foundation model gets coherent narrative vs fragmented chunks
- ✅ Preserves source citations [N] in synthesis
- ✅ Includes text from visual matches

### Tradeoffs
- ⚠️ Adds 70-90s preprocessing latency
- ⚠️ Requires MLX model (~20GB disk space)
- ⚠️ Requires Metal GPU (Mac) or compatible hardware

## Configuration

### Global Enable (Environment Variable)

Edit `.env`:
```bash
# Enable preprocessing globally
LOCAL_PREPROCESS_ENABLED=true

# Strategy: compress (synthesis), filter, or synthesize
LOCAL_PREPROCESS_STRATEGY=compress
```

Then restart the research API:
```bash
./scripts/stop-all.sh
./scripts/start-all.sh
```

### Per-Request Enable (API Parameter)

Enable for a single query without changing global settings:

```bash
curl -X POST 'http://localhost:8004/api/research/ask' \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "Who is Tucker?",
    "num_sources": 10,
    "preprocessing_enabled": true,
    "preprocessing_strategy": "compress"
  }'
```

**Python example:**
```python
import requests

response = requests.post(
    "http://localhost:8004/api/research/ask",
    json={
        "query": "Who is Tucker?",
        "num_sources": 10,
        "preprocessing_enabled": True,  # Override env var
        "preprocessing_strategy": "compress"
    }
)
```

### Check Current Status

```bash
./scripts/status.sh
```

Output will show:
```
Local LLM Preprocessing:
  ○ Disabled (default - fast responses)
    → Set LOCAL_PREPROCESS_ENABLED=true to enable
```

Or if enabled:
```
Local LLM Preprocessing:
  ✓ Enabled (strategy: compress)
    → Reduces costs ~50% but adds 70-90s latency
```

## When to Use

### ✅ Enable Preprocessing When:
- Processing large batches of queries
- Cost optimization is critical
- User can wait 90+ seconds per query
- Running scheduled/background research tasks

### ❌ Disable Preprocessing When:
- Interactive use (default)
- Demos and presentations
- Development and testing
- Fast response time is priority
- Real-time user queries

## Strategies

### `compress` (Synthesis) - **Recommended**
- Creates ONE summary from ALL sources
- 76-86% token reduction
- Best balance of quality and cost
- Preserves citations

### `filter`
- Scores chunks 0-10, keeps high-relevance only
- 40-60% source retention
- Less token reduction than compress
- Faster than synthesis

### `synthesize` (Legacy)
- Alias for `compress`
- Same behavior

## Installation

### 1. Install MLX Dependencies

```bash
pip install mlx-lm>=0.26.3
```

### 2. Download Model

```bash
./scripts/setup-mlx-model.sh
```

This downloads gpt-oss-20b-4bit (~20GB) to `data/models/`.

### 3. Configure Environment

Edit `.env`:
```bash
MLX_MODEL_PATH=/path/to/tkr-docusearch/data/models/gpt-oss-20b-MLX-4bit
MLX_MAX_TOKENS=4000
```

### 4. Enable (Optional)

```bash
# Global enable
echo "LOCAL_PREPROCESS_ENABLED=true" >> .env

# Or use per-request as shown above
```

## Monitoring

### Logs

The research API logs preprocessing status:

**At startup (disabled):**
```
[info] Local LLM preprocessing: DISABLED (default)
       note='Set LOCAL_PREPROCESS_ENABLED=true to enable cost optimization'
```

**At startup (enabled):**
```
[info] Local LLM preprocessing: ENABLED
       strategy=compress
       note='Reduces costs ~50% but adds 70-90s latency'
```

**Per-request override:**
```
[info] Using request-level preprocessing override
       enabled=True
       source=request_parameter
```

### Performance Metrics

Check logs for synthesis metrics:
```bash
tail -f logs/research-api.log | grep "Synthesis complete"
```

Output:
```
[info] Synthesis complete
       original_sources=16
       original_tokens=8269
       synthesized_tokens=1909
       reduction_pct=76.9
       latency_ms=92830
```

## Troubleshooting

### "MLX preprocessing disabled: model path not found"

**Solution**: Run `./scripts/setup-mlx-model.sh` to download the model.

### "MLX preprocessing disabled: mlx-lm not installed"

**Solution**: `pip install mlx-lm>=0.26.3`

### Preprocessing taking longer than expected

**Normal behavior**: 70-90s for 10-16 sources. The synthesis step requires processing all chunks through the local LLM.

**Check**: Monitor `latency_ms` in logs. Values >100000ms (100s) may indicate system load.

### Foundation model still showing high token counts

**Check**: Ensure `LOCAL_PREPROCESS_ENABLED=true` or `preprocessing_enabled: true` in request.

**Verify**: Look for "Synthesis complete" in logs with token reduction %.

## Migration from Previous Versions

### If preprocessing was enabled before

Your `.env` may have had:
```bash
LOCAL_PREPROCESS_ENABLED=true
```

**After update**: This is now `false` by default.

**To restore**: Set back to `true` in `.env` if you want global preprocessing.

**Or**: Use per-request parameters for selective optimization.

### Breaking changes

- **None**: All existing preprocessing functionality remains intact
- **Default changed**: `false` instead of `true`
- **New feature**: Request-level control

## API Documentation

### Request Model

```typescript
{
  query: string;              // Required: research question
  num_sources?: number;       // Optional: max sources (default: 10)
  search_mode?: "visual" | "text" | "hybrid";  // Optional (default: hybrid)
  preprocessing_enabled?: boolean;  // Optional: override env var
  preprocessing_strategy?: "compress" | "filter" | "synthesize";  // Optional
  model?: string;             // Optional: override LLM model
  temperature?: number;       // Optional: LLM temperature
}
```

### Response Metadata

When preprocessing is enabled, response includes:

```json
{
  "answer": "...",
  "preprocessing_metadata": {
    "strategy": "compress",
    "original_sources": 16,
    "final_sources": 1,
    "token_reduction_pct": 76.9,
    "latency_ms": 92830
  }
}
```

## Examples

### Example 1: Quick Query (No Preprocessing)

```bash
curl -X POST 'http://localhost:8004/api/research/ask' \
  -H 'Content-Type: application/json' \
  -d '{"query": "What is ColPali?"}'
```

**Time**: ~25s
**Cost**: ~$0.15
**Best for**: Interactive queries

### Example 2: Cost-Optimized Query

```bash
curl -X POST 'http://localhost:8004/api/research/ask' \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "What is ColPali?",
    "preprocessing_enabled": true
  }'
```

**Time**: ~100s
**Cost**: ~$0.08
**Best for**: Batch processing

### Example 3: Batch Script with Preprocessing

```python
import requests
import time

queries = [
    "What is ColPali?",
    "How does multimodal search work?",
    "What are the performance metrics?"
]

for query in queries:
    print(f"Processing: {query}")
    start = time.time()

    response = requests.post(
        "http://localhost:8004/api/research/ask",
        json={
            "query": query,
            "preprocessing_enabled": True  # Enable for cost savings
        }
    )

    elapsed = time.time() - start
    print(f"  Time: {elapsed:.1f}s")
    print(f"  Answer: {response.json()['answer'][:100]}...")
    print()
```

## Support

For issues or questions:
1. Check logs: `tail -f logs/research-api.log`
2. Verify status: `./scripts/status.sh`
3. Review this document
4. Open GitHub issue if problem persists
