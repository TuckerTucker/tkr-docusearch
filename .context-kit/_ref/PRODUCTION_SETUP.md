# DocuSearch Production Setup - Real ColNomic Model

This guide ensures you're using the **real ColNomic embedding model** with **zero mock data**.

---

## Current Status

**Problem**: The system is using mock embeddings because:
1. ColPali library is not installed in Docker container
2. Fallback to mock is automatic when library missing

**Solution**: Install real ColPali and configure correctly.

---

## Step 1: Install ColPali Library

### Option A: Update Dockerfile (Recommended for Docker)

Edit `docker/Dockerfile.processing-worker` and uncomment the ColPali installation:

```dockerfile
# Install ColPali from GitHub
RUN pip install --no-cache-dir git+https://github.com/illuin-tech/colpali.git
```

**Current line 104-106**: Commented out - needs to be uncommented.

### Option B: Install Locally (for non-Docker use)

```bash
# Activate environment
source start_env

# Install ColPali
pip install git+https://github.com/illuin-tech/colpali.git

# Or install colpali-engine from PyPI
pip install colpali-engine>=0.3.0
```

---

## Step 2: Configure Correct Model Name

The official ColNomic model on HuggingFace is:

```
vidore/colpali-v1.2
```

**Update these files:**

### 1. `docker/.env`
```bash
# Change this line:
MODEL_NAME=vidore/colqwen2-v0.1  # OLD - ColQwen2

# To this:
MODEL_NAME=vidore/colpali-v1.2   # CORRECT - ColPali v1.2
```

### 2. `src/config/model_config.py`
```python
# Line 28 - change default:
name: str = os.getenv('MODEL_NAME', 'vidore/colpali-v1.2')  # Updated
```

### 3. `docker/docker-compose.yml`
```yaml
# Line 82 - change default:
- MODEL_NAME=${MODEL_NAME:-vidore/colpali-v1.2}
```

---

## Step 3: Remove Mock Fallback (Optional - for strict production)

If you want the system to **fail loudly** instead of falling back to mocks:

Edit `src/embeddings/model_loader.py`:

```python
# Around line 24-32, change from:
try:
    from colpali_engine.models import ColPali, ColPaliProcessor
    import torch
    COLPALI_AVAILABLE = True
    logger.info("ColPali engine available - using real implementation")
except ImportError as e:
    COLPALI_AVAILABLE = False
    logger.warning(f"ColPali engine not available ({e}) - using mock implementation")

# To:
try:
    from colpali_engine.models import ColPali, ColPaliProcessor
    import torch
    COLPALI_AVAILABLE = True
    logger.info("ColPali engine available - using real implementation")
except ImportError as e:
    logger.error(f"ColPali engine not available: {e}")
    raise ImportError(
        "ColPali engine required for production. "
        "Install with: pip install git+https://github.com/illuin-tech/colpali.git"
    ) from e
```

---

## Step 4: Verify Real Model is Used

After installation, check logs for these indicators:

### ✅ Real Model (Good)
```
INFO - Loading model: vidore/colpali-v1.2
INFO - Model loaded successfully from HuggingFace
INFO - Device: mps (or cuda)
INFO - Memory allocated: 5500.0MB
```

### ❌ Mock Model (Bad)
```
WARNING - Using mock ColPali model. Install ColPali for production.
INFO - MockColPaliModel initialized
```

---

## Step 5: Complete Production Deployment

### 1. Build with Real Model

```bash
cd docker

# Remove old container
docker-compose down processing-worker

# Rebuild with ColPali installed
docker-compose build processing-worker

# Start with real model
docker-compose up -d processing-worker

# Check logs
docker logs -f docusearch-worker
```

### 2. Verify Model Loading

```bash
# Should see:
# ✓ Loading model: vidore/colpali-v1.2
# ✓ Model loaded successfully
# ✓ Device: mps/cuda/cpu
# ✓ Memory: ~5.5GB

# Should NOT see:
# ⚠️ "Using mock ColPali model"
# ⚠️ "MockColPaliModel initialized"
```

### 3. Test with Real Embeddings

```python
from src.embeddings import ColPaliEngine

# Initialize
engine = ColPaliEngine(device='mps', precision='fp16')

# Check model info
info = engine.get_model_info()
print(f"Model: {info['model_name']}")
print(f"Mock: {info.get('mock', False)}")  # Should be False or missing
print(f"Memory: {info['memory_allocated_mb']} MB")

# Verify it's real by checking memory usage
# Real model: ~5500 MB
# Mock model: ~0.1 MB
assert info['memory_allocated_mb'] > 1000, "Still using mock model!"
```

---

## Model Specifications

### vidore/colpali-v1.2 (Recommended)
- **Size**: 14GB FP16, 7GB INT8
- **Embeddings**: 128 dimensions (late interaction optimized)
- **Performance**: 2.3s/image, 0.24s/text
- **Device**: MPS (M1/M2/M3), CUDA, CPU
- **Quality**: Production-grade multimodal embeddings

### Alternative Models

If you want ColNomic 7B instead:
```bash
MODEL_NAME=vidore/colqwen2-v1.0  # ColNomic's ColQwen2
```

---

## Troubleshooting

### "No module named 'colpali_engine'"

**Solution**: ColPali not installed
```bash
pip install git+https://github.com/illuin-tech/colpali.git
```

### "Using mock ColPali model"

**Solutions**:
1. Check ColPali is installed: `pip list | grep colpali`
2. Rebuild Docker container if using Docker
3. Check import error in logs

### "Device 'mps' not available"

**Solution**: MPS requires M1/M2/M3 Mac
```bash
# Fallback to CPU
export DEVICE=cpu

# Or use CUDA on Linux/Windows
export DEVICE=cuda
```

### Model Download Fails

**Solution**: Model is large (~14GB), ensure:
1. Stable internet connection
2. Sufficient disk space (20GB free)
3. HuggingFace access (no auth needed for public models)

```bash
# Pre-download model
python -c "
from transformers import AutoModel, AutoProcessor
AutoModel.from_pretrained('vidore/colpali-v1.2')
AutoProcessor.from_pretrained('vidore/colpali-v1.2')
print('✓ Model downloaded')
"
```

---

## Quick Checklist

Before production deployment, verify:

- [ ] ColPali library installed (`pip list | grep colpali`)
- [ ] Model name set to `vidore/colpali-v1.2` in `.env`
- [ ] Docker container rebuilt with ColPali
- [ ] Logs show "Model loaded successfully" (not mock)
- [ ] Memory usage ~5.5GB (not <1MB)
- [ ] `info.get('mock')` returns `False`
- [ ] Real embeddings generated (check dimensions: 128)

---

## Performance Expectations

With **real ColPali v1.2**:

| Operation | Expected Time | Memory |
|-----------|---------------|--------|
| Model Load | 10-15 seconds | 5.5 GB |
| Image Embedding | 2-3 seconds | +500 MB |
| Text Embedding | 0.2-0.3 seconds | +100 MB |
| Query Embedding | 0.15-0.2 seconds | +50 MB |

With **mock model** (incorrect):

| Operation | Expected Time | Memory |
|-----------|---------------|--------|
| Model Load | <1 second | <1 MB |
| Image Embedding | 0.01 seconds | <1 MB |
| Text Embedding | 0.01 seconds | <1 MB |

**If your times are <1 second, you're using mocks!**

---

## Summary

To ensure **100% real embeddings, zero mocks**:

1. **Install ColPali**: `pip install git+https://github.com/illuin-tech/colpali.git`
2. **Set model name**: `MODEL_NAME=vidore/colpali-v1.2` in `.env`
3. **Rebuild containers**: `docker-compose build processing-worker`
4. **Verify logs**: Look for "Model loaded successfully", NOT "Using mock"
5. **Check memory**: Should be ~5.5GB, not <1MB

The system will then use **real ColPali v1.2 embeddings** for production-quality semantic search.
