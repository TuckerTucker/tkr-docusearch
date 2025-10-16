# MLX Whisper Support Monitoring

## Status: Pending Merge

Track progress on Docling MLX Whisper integration for 19x performance improvement on Apple Silicon.

## PR Information

**GitHub PR:** https://github.com/docling-project/docling/pull/2366
**Issue:** https://github.com/docling-project/docling/issues/2364
**Created:** October 14, 2025
**Status:** Open (Under Review)

## Current Blockers

1. **Review approval:** Needs 2 approvals (has 1 from PeterStaar-IBM)
2. **Architecture feedback:** dolfim-ibm suggests adding explicit model variants:
   - `WHISPER_X_MLX` - MLX-optimized for Apple Silicon
   - `WHISPER_X_NATIVE` - Standard PyTorch Whisper
   - Instead of automatic detection

## Expected Performance Gains

- **19x faster** on Apple Silicon (M1/M2/M3)
- Comparison: Current CPU baseline ~250-300 frames/sec → MLX ~4,750-5,700 frames/sec
- Seamless fallback to native Whisper on non-Apple systems

## Implementation Changes Required (Once Merged)

### 1. Update Docling

```bash
source .venv-native/bin/activate
pip install --upgrade docling
```

### 2. Update Configuration

**File:** `src/config/processing_config.py`

**Current (lines 433-436):**
```python
# IMPORTANT: Whisper uses sparse tensors which are NOT supported by MPS
# Force CPU for Whisper ASR even when MPS is available for other models
# See: https://github.com/pytorch/pytorch/issues/87886
accelerator_device = AcceleratorDevice.CPU
```

**After merge (expected):**
```python
# MLX Whisper is now supported on Apple Silicon (PR #2366)
# Use automatic device selection or explicit MLX variant
if self.device.lower() == "mps":
    # MLX variant for Apple Silicon
    accelerator_device = AcceleratorDevice.MPS
elif self.device.lower() == "cuda":
    accelerator_device = AcceleratorDevice.CUDA
else:
    accelerator_device = AcceleratorDevice.CPU
```

**Alternative (if explicit variants are required):**
```python
# Map to explicit MLX/Native variants
model_map = {
    "turbo": "turbo_mlx" if self.device.lower() == "mps" else "turbo",
    "base": "base_mlx" if self.device.lower() == "mps" else "base",
    # ... etc
}
```

### 3. Install MLX Dependencies (if needed)

```bash
# May be required after merge
pip install mlx-whisper
```

### 4. Test Audio Processing

```bash
# Test with sample audio file
./scripts/run-worker-native.sh run

# Upload test audio file via Copyparty
# Monitor logs/worker-native.log for performance improvement
```

## Monitoring Plan

### Weekly Checks

**GitHub PR:** https://github.com/docling-project/docling/pull/2366

Check for:
- Additional approvals
- Architecture changes implemented
- Merge status
- New comments/feedback

### Post-Merge Actions

1. Update docling to version containing MLX support
2. Test MLX Whisper with sample audio
3. Benchmark performance improvement
4. Update configuration as needed
5. Document actual implementation vs. expected changes
6. Update this tracking document with final status

## Links

- **PR #2366:** https://github.com/docling-project/docling/pull/2366
- **Issue #2364:** https://github.com/docling-project/docling/issues/2364
- **MLX Whisper Package:** https://github.com/ml-explore/mlx-examples/tree/main/whisper
- **PyTorch MPS Sparse Issue:** https://github.com/pytorch/pytorch/issues/87886

## Current Workaround

**Status:** CPU-only Whisper (forced in `src/config/processing_config.py:436`)
**Reason:** PyTorch MPS doesn't support sparse tensors
**Performance:** ~250-300 frames/sec (CPU baseline)
**Documented in:** Commit `bfe8e41` (Oct 14, 2025)

---

**Last Updated:** October 15, 2025
**Next Check:** October 22, 2025
