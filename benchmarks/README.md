# Preprocessing Strategy Benchmark Suite

Comprehensive benchmark for evaluating local LLM preprocessing strategies in the research bot.

## Overview

This benchmark suite tests three preprocessing strategies against a baseline (no preprocessing):

1. **Compression**: Extract key facts, reduce token count 30-50%
2. **Filtering**: Score and filter chunks by relevance, retain 40-60%
3. **Synthesis**: Cross-document knowledge synthesis with citations

## Quick Start

### Run with Mock LLM (Fast)

```bash
# From project root
PYTHONPATH=. python benchmarks/preprocessing_benchmark.py --mode mock --sources 10
```

**Execution time**: ~10-15 minutes (15 queries × 4 strategies × simulated latency)

### Run with Real MLX Model (Accurate)

```bash
# Requires MLX model loaded
export MLX_MODEL_PATH="./models/gpt-oss-20B-mlx"
PYTHONPATH=. python benchmarks/preprocessing_benchmark.py --mode real --sources 10
```

**Execution time**: ~30-45 minutes (depends on M1/M2 GPU performance)

## Test Corpus

The benchmark tests **15 diverse queries** across different categories:

| Category | Count | Example |
|----------|-------|---------|
| Factual | 2 | "What caused the 2008 financial crisis?" |
| Comparison | 2 | "How do solar and wind energy compare?" |
| Process | 2 | "What are the steps in the document review process?" |
| Multi-part | 2 | "What were the effects on housing and employment?" |
| Exploratory | 2 | "What are the key findings in the climate report?" |
| Technical | 2 | "How does OAuth2 authentication work?" |
| Timeline | 1 | "What events happened between 2010 and 2015?" |
| Contradictory | 1 | "What do different sources say about vaccine efficacy?" |
| Gap-testing | 1 | "What information is missing about the project timeline?" |

## Metrics Collected

For each query × strategy combination:

- **Token counts**: Before/after preprocessing
- **Reduction percentage**: How much context was reduced
- **Preprocessing latency**: Time spent in local LLM preprocessing
- **Cost savings**: Estimated GPT-4 API cost reduction (based on $10/1M input tokens)

## Output

The benchmark generates:

1. **Console logs**: Real-time progress during execution
2. **Markdown report**: `benchmark-report.md` with tables and analysis

### Sample Report Structure

```markdown
# Preprocessing Strategy Benchmark Report

## Executive Summary
- Baseline tokens: 8,240 avg per query
- Compression: 53% token reduction
- Filtering: 60% token reduction
- Synthesis: 98% token reduction

## Strategy Comparison
| Strategy | Avg Tokens Before | Avg Tokens After | Reduction % | Cost Savings % |
|----------|-------------------|------------------|-------------|----------------|
| Baseline | 8,240             | 8,240            | 0%          | 0%             |
| Compress | 8,240             | 3,870            | 53%         | 53%            |
| Filter   | 8,240             | 3,296            | 60%         | 60%            |
| Synthesize | 8,240           | 165              | 98%         | 98%            |

...
```

## Validation Targets

The benchmark validates these performance targets:

- ✅ **Token reduction ≥30%**: Compression strategy should reduce tokens by at least 30%
- ✅ **Cost savings ≥40%**: Preprocessing should save at least 40% on foundation model costs
- ⚠️  **Citation accuracy ≥95%**: Manual review required (see below)

### Manual Citation Accuracy Validation

The benchmark cannot automatically verify citation preservation. Manual review required:

1. Select 5 random synthesis results from the detailed output
2. Count citations in synthesized text (format: `[N]`)
3. Verify citations match original source order
4. Calculate accuracy: `(preserved_citations / total_citations) × 100`

**Target**: ≥95% citation preservation

## Customization

### Adjust Number of Sources

```bash
# Test with 5 sources per query (faster)
python benchmarks/preprocessing_benchmark.py --mode mock --sources 5

# Test with 20 sources (more realistic)
python benchmarks/preprocessing_benchmark.py --mode mock --sources 20
```

### Change Output Path

```bash
# Save report to custom location
python benchmarks/preprocessing_benchmark.py --mode mock --output ./reports/benchmark.md
```

## Implementation Details

### Mock Mode

- Uses `MockMLXClient` that simulates realistic token reduction
- Simulates latency based on token generation speed (~7.5 tokens/sec)
- No actual LLM calls, safe for CI/CD

### Real Mode

- Uses actual MLX model with Metal GPU acceleration
- Real token reduction and latency measurements
- Requires model loaded at `MLX_MODEL_PATH`

### Mock Source Generation

Each benchmark run creates 10 mock sources:

- **Visual sources**: 1 in 3 (no text compression)
- **Text sources**: 2 in 3 (~400 tokens each, ~1600 chars)
- **Relevance scores**: Decreasing from 0.85 to 0.30

## Prompt Optimization

If benchmark results show:

- **Compression <30%**: Strengthen "be concise" instructions in `CHUNK_COMPRESSION_PROMPT`
- **Relevance scores too generous**: Tighten scoring criteria in `RELEVANCE_SCORING_PROMPT`
- **Synthesis loses citations**: Add citation preservation examples in `KNOWLEDGE_SYNTHESIS_PROMPT`
- **Token budget exceeded**: Reduce instruction verbosity in prompts

See `src/research/prompts.py` for prompt definitions.

## Troubleshooting

### Import Errors

If you see "Warning: Research modules not available":

```bash
# Ensure PYTHONPATH is set
PYTHONPATH=/path/to/tkr-docusearch python benchmarks/preprocessing_benchmark.py --mode mock
```

### Benchmark Takes Too Long

- Use `--sources 5` for faster execution
- Use `--mode mock` (mock mode is 2-3x faster than real)
- Run subset of queries (edit `TEST_QUERIES` in script)

### Report Not Generated

Check script output for errors. Report generation requires all benchmarks to complete successfully.

## Contributing

To add new test queries:

1. Edit `TEST_QUERIES` in `preprocessing_benchmark.py`
2. Add diverse query types (factual, comparison, technical, etc.)
3. Run benchmark and verify metrics

## References

- **Preprocessing Implementation**: `src/research/local_preprocessor.py`
- **Prompts**: `src/research/prompts.py`
- **MLX Client**: `src/research/mlx_llm_client.py`
- **Integration Tests**: `tests/integration/test_research_e2e.py`

---

**Last Updated**: 2025-10-22
**Agent**: Agent 4 (Prompt Engineer / Benchmark Specialist)
**Wave**: Wave 4 (Production Validation)
