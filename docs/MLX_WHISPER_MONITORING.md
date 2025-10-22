# MLX Whisper Support Monitoring

## Status: ✅ IMPLEMENTED - Docling 2.58.0

MLX Whisper integration successfully implemented with Docling 2.58.0 for 19x performance improvement on Apple Silicon.

## PR Information

**GitHub PR:** https://github.com/docling-project/docling/pull/2366
**Issue:** https://github.com/docling-project/docling/issues/2364
**Created:** October 14, 2025
**Merged:** October 21, 2025 by @dolfim-ibm
**Commit:** 657ce8b
**Status:** ✅ Merged into `main` branch

## Release Status

1. **PR Status:** ✅ Merged (October 21, 2025)
2. **PyPI Release:** ✅ 2.58.0 (October 22, 2025) - **INCLUDES MLX Whisper**
3. **GitHub Release:** ✅ v2.58.0 (October 22, 2025) - **INCLUDES MLX Whisper**
4. **Implementation:** ✅ Upgraded and configured (October 22, 2025)

## Implementation Summary

**Upgrade completed October 22, 2025:**
- ✅ Docling upgraded from 2.57.0 → 2.58.0
- ✅ MLX Whisper dependencies verified (mlx-whisper 0.4.3, lightning-whisper-mlx 0.0.10)
- ✅ Configuration updated to enable MPS device for Whisper ASR
- ✅ Automatic fallback to CPU for non-Apple systems implemented
- ⏳ Performance benchmarking pending (requires audio processing test)

**Configuration Changes:**
- File: `src/config/processing_config.py` (lines 470-481)
- Changed from: Force CPU for all Whisper operations
- Changed to: Use MPS (Metal) on Apple Silicon, CUDA on NVIDIA, CPU fallback otherwise

## Expected Performance Gains

- **19x faster** on Apple Silicon (M1/M2/M3)
- Comparison: Current CPU baseline ~250-300 frames/sec → MLX ~4,750-5,700 frames/sec
- Seamless fallback to native Whisper on non-Apple systems

## Implementation Details

### Actual Implementation (October 22, 2025)

**1. Docling Upgrade:**
```bash
source .venv-native/bin/activate
pip install --upgrade docling==2.58.0
# Result: Successfully installed docling-2.58.0
```

**2. Configuration Update:**

**File:** `src/config/processing_config.py` (lines 470-481)

**Before:**
```python
# IMPORTANT: Whisper uses sparse tensors which are NOT supported by MPS
# Force CPU for Whisper ASR even when MPS is available for other models
# See: https://github.com/pytorch/pytorch/issues/87886
accelerator_device = AcceleratorDevice.CPU
```

**After:**
```python
# MLX Whisper support added in Docling 2.58.0 (PR #2366)
# Provides 19x performance improvement on Apple Silicon
# Automatic fallback to CPU for non-Apple systems
if self.device.lower() == "mps":
    # Use MPS (Metal) for Apple Silicon - enables MLX Whisper backend
    accelerator_device = AcceleratorDevice.MPS
elif self.device.lower() == "cuda":
    # Use CUDA for NVIDIA GPUs
    accelerator_device = AcceleratorDevice.CUDA
else:
    # Fallback to CPU for other systems
    accelerator_device = AcceleratorDevice.CPU
```

**3. MLX Dependencies:**
Already installed in environment:
- `mlx-whisper==0.4.3`
- `lightning-whisper-mlx==0.0.10`

**4. Testing:**
Configuration validated with successful Python syntax check and module import.

## Next Steps

### Remaining Tasks

1. **Performance Benchmarking** (User action required)
   - Start worker: `./scripts/start-all.sh`
   - Upload test audio file via Copyparty
   - Monitor `logs/worker-native.log` for MLX initialization and performance metrics
   - Compare frames/sec against CPU baseline (~250-300 fps)
   - Expected improvement: 19x (target ~4,750-5,700 fps)

2. **Production Validation**
   - Process multiple audio file types (MP3, WAV, M4A)
   - Verify VTT generation quality
   - Confirm search functionality works correctly
   - Test with various audio lengths and qualities

3. **Documentation Updates**
   - Update performance metrics in README.md once benchmarked
   - Note MLX Whisper support in feature documentation

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

**Last Updated:** October 22, 2025
**Implementation Date:** October 22, 2025
**Status:** ✅ IMPLEMENTED - Ready for performance benchmarking
