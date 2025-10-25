# Preprocessing Optimization Benchmarks

This directory contains benchmark tools for measuring the performance impact of the GPT-OSS-20B Harmony prompt optimization.

## Overview

The `benchmark_preprocessing_optimization.py` script compares legacy preprocessing prompts against Harmony-optimized prompts to validate:

- **Token Reduction:** 30-50% target reduction in preprocessed chunk size
- **Latency Improvement:** <3s per chunk processing time
- **Quality Preservation:** No loss of factual accuracy or citation capability

## Quick Start

### Run Mock Benchmark (Fast)

```bash
# From project root
python tests/benchmarks/benchmark_preprocessing_optimization.py --mode mock

# Output saved to .context-kit/benchmarks/preprocessing-results.md
```

### Run Real MLX Benchmark (Accurate)

```bash
# Ensure MLX model is available
export MLX_MODEL_PATH=./models/gpt-oss-20B-mlx

# Run benchmark
python tests/benchmarks/benchmark_preprocessing_optimization.py --mode real

# Monitor progress (will take 5-10 minutes for 5 chunks)
```

## Command Options

```bash
python tests/benchmarks/benchmark_preprocessing_optimization.py [OPTIONS]

Options:
  --mode {mock,real}     Use mock LLM (fast, simulated) or real MLX model (accurate, slow)
                         Default: mock

  --output PATH          Output report path
                         Default: .context-kit/benchmarks/preprocessing-results.md

Examples:
  # Mock benchmark with custom output
  python tests/benchmarks/benchmark_preprocessing_optimization.py --mode mock --output results.md

  # Real MLX benchmark
  python tests/benchmarks/benchmark_preprocessing_optimization.py --mode real
```

## Test Corpus

The benchmark uses 5 real resume text samples that demonstrated expansion issues with legacy prompts:

1. **Professional summary** (~400 chars, 86 tokens)
2. **Work experience** (~500 chars, 109 tokens)
3. **Technical skills** (~450 chars, 107 tokens)
4. **Education and certifications** (~400 chars, 95 tokens)
5. **Projects and achievements** (~550 chars, 148 tokens)

These samples were selected because they:
- Represent realistic preprocessing workloads
- Showed -5% to -107% expansion with legacy prompts (problematic)
- Cover diverse content types (professional, technical, educational)

## Success Criteria

| Metric | Target | Description |
|--------|--------|-------------|
| Token Reduction | 30-50% | Average token reduction across all chunks |
| Latency per Chunk | <3000ms | Max processing time per chunk |
| Success Rate | 80%+ | Percentage of chunks meeting 30-50% target |
| Quality | No degradation | Manual review: factual accuracy preserved |

## Output Report

The benchmark generates a markdown report with:

### Executive Summary
- Validation status (PASS/FAIL for each criterion)
- Key findings (legacy vs Harmony comparison)
- Overall recommendations

### Detailed Results
- Per-chunk token metrics
- Latency measurements
- Target compliance indicators

### Performance Comparison
- Token usage tables
- Latency comparison
- Cost savings projections

### Methodology
- Test setup description
- Metrics definitions
- Validation criteria

## Interpreting Results

### Mock Mode Results

Mock mode **simulates** expected behavior based on contract specifications:

- **Legacy:** 7% expansion (realistic based on observed issues)
- **Harmony:** 40% reduction +/- 5% variance (target range)
- **Latency:** Simulated based on token throughput estimates

**Note:** Mock results demonstrate *expected* improvements but require real MLX validation for production deployment.

### Real Mode Results

Real mode uses the actual MLX model:

- Measures true token reduction achieved
- Captures real latency performance
- Exposes any prompt engineering issues
- Validates production readiness

## Common Issues

### Issue: Success Rate < 80%

**Cause:** Some chunks fall outside 30-50% target range

**Solutions:**
1. Review chunks that failed target
2. Adjust prompt engineering (tune compression instructions)
3. Consider adjusting `max_tokens` or `reasoning_effort` parameters
4. Re-run benchmark after changes

### Issue: Harmony Reduction > 50%

**Cause:** Compression too aggressive, potential information loss

**Solutions:**
1. Review compressed output for factual accuracy
2. Adjust compression prompt to preserve more context
3. Increase few-shot example detail
4. Consider raising `max_tokens` for compression output

### Issue: Harmony Reduction < 30%

**Cause:** Compression too conservative, not achieving token savings

**Solutions:**
1. Review compression prompt for clarity
2. Add more explicit compression instructions
3. Verify `reasoning_effort="low"` is set (faster, more focused)
4. Check few-shot example demonstrates sufficient compression

### Issue: Latency > 3000ms per chunk

**Cause:** Model inference too slow

**Solutions:**
1. Verify `reasoning_effort="low"` is configured
2. Reduce `max_tokens` if overly generous
3. Check system resources (Metal GPU availability)
4. Consider model quantization (4-bit vs 8-bit)

## Extending the Benchmark

### Adding New Test Chunks

Edit `RESUME_CHUNKS` in `benchmark_preprocessing_optimization.py`:

```python
RESUME_CHUNKS = [
    # Existing chunks...

    # New chunk
    "Your new test content here (400-600 chars recommended)",
]
```

Then update `chunk_descriptions` in `run_all_benchmarks()`:

```python
chunk_descriptions = [
    # Existing descriptions...
    "Your new chunk description",
]
```

### Customizing Target Ranges

Edit the validation logic in `generate_report()`:

```python
# Current: 30-50% target
harmony_meets_target = 30.0 <= harmony_reduction_pct <= 50.0

# Example: Looser range (25-55%)
harmony_meets_target = 25.0 <= harmony_reduction_pct <= 55.0
```

### Adding New Metrics

1. Add fields to `BenchmarkResult` dataclass
2. Calculate metrics in `run_single_benchmark()`
3. Update report generation in `generate_report()`

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Preprocessing Optimization Benchmark

on:
  pull_request:
    paths:
      - 'src/research/prompts.py'
      - 'src/research/local_preprocessor.py'

jobs:
  benchmark:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run mock benchmark
        run: |
          python tests/benchmarks/benchmark_preprocessing_optimization.py --mode mock

      - name: Check success criteria
        run: |
          # Parse results and fail if criteria not met
          python -c "
          import re
          with open('.context-kit/benchmarks/preprocessing-results.md') as f:
              report = f.read()
              if '❌ FAIL' in report.split('## Executive Summary')[1].split('##')[0]:
                  print('Benchmark failed success criteria')
                  exit(1)
          "

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: benchmark-results
          path: .context-kit/benchmarks/preprocessing-results.md
```

## Related Documentation

- **Integration Contract:** `.context-kit/orchestration/gpt-oss-prompt-optimization/integration-contracts/preprocessing-pipeline-integration.md`
- **Prompt Specifications:** `.context-kit/orchestration/gpt-oss-prompt-optimization/integration-contracts/prompt-response-schema.md`
- **MLX Client Guide:** `.context-kit/research/gpt-oss-20B-comprehensive-guide.md`

## Troubleshooting

### ImportError: No module named 'src.research'

**Solution:** Run from project root:
```bash
cd /Volumes/tkr-riffic/@tkr-projects/tkr-docusearch
python tests/benchmarks/benchmark_preprocessing_optimization.py --mode mock
```

### MLX Model Not Found

**Solution:** Download and configure MLX model:
```bash
# Run setup script
python scripts/setup_mlx_model.py

# Or set path manually
export MLX_MODEL_PATH=/path/to/gpt-oss-20B-mlx
```

### Benchmark Takes Too Long

**Solution:** Use mock mode for quick validation:
```bash
python tests/benchmarks/benchmark_preprocessing_optimization.py --mode mock
```

Mock mode completes in ~1 minute vs 5-10 minutes for real MLX.

## Version History

- **v1.0** (2025-10-25): Initial benchmark implementation
  - Mock and real MLX modes
  - 5 resume test chunks
  - Success criteria validation
  - Comprehensive markdown reporting
