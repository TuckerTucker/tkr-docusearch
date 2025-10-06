# Validation Strategy & Quality Gates

**Purpose**: Define progressive validation gates to ensure successful integration and production readiness

**Principle**: Test early, test often, fail fast. Each wave has clear validation criteria that must pass before proceeding.

---

## Validation Philosophy

### Quality Gates (Wave Boundaries)

```
Wave 1 → Wave 2: Contract Compliance
  ✓ All contracts reviewed and approved
  ✓ Docker builds successfully
  ✓ Directory structure matches assignments
  ✓ No file ownership conflicts

Wave 2 → Wave 3: Component Quality
  ✓ Unit tests pass (>90% coverage per component)
  ✓ Mocks match contract specifications exactly
  ✓ Code review approved by consumer agents
  ✓ Performance meets preliminary targets

Wave 3 → Wave 4: Integration Success
  ✓ End-to-end workflows functional
  ✓ Integration tests pass
  ✓ Performance targets met
  ✓ Error handling validated

Wave 4 → Production: System Ready
  ✓ Scale testing complete (100 document batch)
  ✓ All production features working
  ✓ Documentation complete
  ✓ User acceptance test passed
```

---

## Wave 1 Validation: Contract Compliance

### Goals
- Verify all agents understand their responsibilities
- Ensure contracts are complete and unambiguous
- Validate Docker setup works on M1

### Checklist

**Contract Review** (All Agents):
- [ ] All integration contracts reviewed by relevant agents
- [ ] No missing API methods or data structures
- [ ] Error handling strategies documented
- [ ] Performance targets realistic and measurable
- [ ] Consensus reached on any disputed specifications

**Directory Structure** (infrastructure-agent):
- [ ] All directories created as specified in agent-assignments.md
- [ ] No overlapping write permissions
- [ ] Volume mounts configured correctly
- [ ] Permissions set appropriately (755 for scripts, etc.)

**Docker Build** (infrastructure-agent):
- [ ] `docker compose build` succeeds without errors
- [ ] ARM64 platform specified for all services
- [ ] Base images pull successfully
- [ ] Python dependencies install correctly
- [ ] Build time <15 minutes

**Model Pre-caching** (infrastructure-agent):
- [ ] ColNomic 7B model downloads successfully (14GB)
- [ ] Model stored in correct cache directory (`/models`)
- [ ] Model loads in container without errors
- [ ] PyTorch MPS available in processing-worker container

### Validation Commands

```bash
# Build all containers
cd docker
docker compose build

# Verify builds
docker images | grep -E "tkr-docusearch|copyparty|chromadb"

# Test container startup
docker compose up -d
docker compose ps  # All should be "Up" or "healthy"

# Verify MPS in processing-worker
docker compose exec processing-worker python -c "
import torch
print('MPS available:', torch.backends.mps.is_available())
assert torch.backends.mps.is_available(), 'MPS not available'
"

# Pre-cache model
docker compose run processing-worker python -c "
from colpali_engine.models import ColQwen2_5
model = ColQwen2_5.from_pretrained('nomic-ai/colnomic-embed-multimodal-7b')
print('Model cached successfully')
"

# Cleanup
docker compose down
```

### Exit Criteria

**All Must Pass**:
1. Docker Compose builds without errors
2. All containers start successfully
3. Health checks pass for all services
4. MPS device available in processing-worker
5. ColNomic 7B model cached (14GB in `/models`)
6. All agents confirm contract understanding

**If Any Fail**: Address blockers before proceeding to Wave 2

---

## Wave 2 Validation: Component Quality

### Goals
- Verify each component works independently
- Ensure mocks match contracts exactly
- Validate unit test coverage
- Confirm code quality standards

### Checklist (Per Agent)

**storage-agent**:
- [ ] Unit tests pass: `pytest src/storage/test_storage.py -v`
- [ ] Test coverage >90%: `pytest --cov=src/storage --cov-report=html`
- [ ] Mock ChromaDB client behaves correctly
- [ ] Compression reduces size by 4x
- [ ] All methods in `storage-interface.md` implemented

**embedding-agent**:
- [ ] Unit tests pass: `pytest src/embeddings/test_embeddings.py -v`
- [ ] Test coverage >90%
- [ ] Mock embeddings have correct shapes
- [ ] Late interaction scoring produces expected results
- [ ] FP16 and INT8 modes both work

**processing-agent**:
- [ ] Unit tests pass: `pytest src/processing/test_processing.py -v`
- [ ] Test coverage >90%
- [ ] Mocks for embedding-agent match `embedding-interface.md`
- [ ] Mocks for storage-agent match `storage-interface.md`
- [ ] Docling parser handles PDF/DOCX/PPTX

**search-agent**:
- [ ] Unit tests pass: `pytest src/search/test_search.py -v`
- [ ] Test coverage >90%
- [ ] Mocks for embedding-agent and storage-agent match contracts
- [ ] Two-stage search logic correct
- [ ] Result merging produces expected rankings

**ui-agent**:
- [ ] Search page renders in browser
- [ ] Query form validation works
- [ ] Mock search API returns formatted results
- [ ] Event hook script has correct structure

**infrastructure-agent**:
- [ ] All services start in <30 seconds
- [ ] Health checks pass consistently
- [ ] Resource limits enforced (memory, CPU)
- [ ] Logs accessible via `docker compose logs`

### Code Quality Standards

**Python Style**:
```bash
# Run linters (all agents)
flake8 src/
black --check src/
mypy src/

# Expected: No errors
```

**Documentation**:
- [ ] All classes have docstrings
- [ ] All public methods documented
- [ ] Type hints for all function signatures
- [ ] README with usage examples

### Mock Validation

**Critical**: Mocks must match contracts exactly to prevent integration failures.

**Example Validation Script**:
```python
# processing-agent validates embedding-agent mock
from src.processing.mocks import MockEmbeddingEngine
from integration_contracts.embedding_interface import EmbeddingOutput

# Test mock returns correct structure
mock_engine = MockEmbeddingEngine()
result = mock_engine.embed_images([mock_image])

assert isinstance(result, dict)
assert "embeddings" in result
assert "cls_tokens" in result
assert result["embeddings"][0].shape == (100, 768)  # Expected shape
assert result["cls_tokens"].shape == (1, 768)

print("✓ Mock matches contract")
```

### Exit Criteria

**All Agents Must**:
1. Unit tests pass with >90% coverage
2. Mocks validated against contracts
3. Code passes linters (flake8, black, mypy)
4. Documentation complete
5. No known bugs or issues

**Code Review Gate**:
- Consumer agents review provider implementations
- Approve or request changes
- All reviews approved before Wave 3

**If Any Fail**: Fix issues before integration

---

## Wave 3 Validation: Integration Success

### Goals
- Verify components work together
- Test end-to-end workflows
- Validate performance targets
- Ensure error handling works

### Integration Test Suites

**Test Suite 1: Visual Search Workflow**

```bash
# Start all services
docker compose up -d

# Upload sample PDF
cp test-data/sample-10pages.pdf data/copyparty/uploads/

# Wait for processing (max 2 minutes)
timeout 120 bash -c 'until [ -f data/logs/sample-10pages.processed ]; do sleep 5; done'

# Verify embeddings in ChromaDB
docker compose exec chromadb curl -s http://localhost:8000/api/v1/collections | jq '.[] | select(.name=="visual_collection") | .count'
# Expected: 10 (one per page)

# Test search via UI
curl -X POST http://localhost:8000/search/query \
  -H "Content-Type: application/json" \
  -d '{"query": "charts and graphs", "n_results": 5}'
# Expected: Results with pages containing visuals

# Measure latency
time curl -X POST http://localhost:8000/search/query \
  -H "Content-Type: application/json" \
  -d '{"query": "revenue", "n_results": 10}'
# Expected: <500ms total
```

**Test Suite 2: Hybrid Search**

```bash
# Upload text-heavy document
cp test-data/contract-50pages.pdf data/copyparty/uploads/

# Wait for processing
timeout 300 bash -c 'until [ -f data/logs/contract-50pages.processed ]; do sleep 10; done'

# Verify both collections populated
docker compose exec chromadb curl -s http://localhost:8000/api/v1/collections

# Test hybrid search
curl -X POST http://localhost:8000/search/query \
  -H "Content-Type: application/json" \
  -d '{"query": "termination clause", "search_mode": "hybrid", "n_results": 10}'

# Expected: Top results from text collection (precise match)
```

**Test Suite 3: Error Handling**

```bash
# Upload corrupted PDF
cp test-data/corrupted.pdf data/copyparty/uploads/

# Check error logged (not crash)
docker compose logs processing-worker | grep -i "error processing corrupted.pdf"

# Upload unsupported format
cp test-data/sample.mp4 data/copyparty/uploads/

# Check graceful skip
docker compose logs processing-worker | grep -i "unsupported format"

# Test empty query
curl -X POST http://localhost:8000/search/query \
  -H "Content-Type: application/json" \
  -d '{"query": "", "n_results": 10}'

# Expected: 400 Bad Request with error message
```

### Performance Validation

**Processing Speed** (processing-agent + embedding-agent + storage-agent):

| Test | Target | Command |
|------|--------|---------|
| 10-page PDF | <2 min | `time docker compose exec processing-worker python -m src.processing.processor test-data/sample-10pages.pdf` |
| 50-page PDF | <10 min | Same as above with 50-page doc |
| Batch 10 PDFs | <20 min | Upload all 10, measure total time |

**Search Latency** (search-agent + embedding-agent + storage-agent):

| Test | Target | Measurement |
|------|--------|-------------|
| Simple query | <300ms | Median of 10 queries |
| Hybrid query | <500ms | Median of 10 queries |
| With filters | <500ms | Median of 10 queries |
| p95 latency | <800ms | 95th percentile of 100 queries |

**Storage Efficiency** (storage-agent):

```bash
# Measure storage overhead
original_size=$(du -sm data/copyparty/uploads | cut -f1)
chroma_size=$(du -sm data/chroma_db | cut -f1)
overhead_percent=$((100 * chroma_size / original_size))

echo "Storage overhead: ${overhead_percent}%"
# Expected: <300% (embeddings + metadata < 3x original)
```

### Integration Checklist

**End-to-End Workflows**:
- [ ] Upload PDF → Processing starts automatically
- [ ] Processing completes → Embeddings stored in ChromaDB
- [ ] Search query → Results returned in <500ms
- [ ] Click result → Preview modal shows correct page
- [ ] Filter by filename → Only matching documents returned

**Error Scenarios**:
- [ ] Corrupted PDF → Error logged, processing continues with next file
- [ ] Empty query → 400 Bad Request returned
- [ ] ChromaDB down → Graceful error message, no crash
- [ ] Model loading fails → Falls back to CPU, logs warning

**Performance Targets**:
- [ ] 10-page PDF processes in <2 minutes
- [ ] Search latency p95 <500ms
- [ ] Storage overhead <300%
- [ ] Memory usage stable (<8GB for processing-worker)

### Exit Criteria

**All Must Pass**:
1. End-to-end visual search works (upload → embed → search → results)
2. Hybrid search returns relevant results
3. Performance targets met
4. Error handling validated
5. No crashes or unhandled exceptions

**If Any Fail**: Debug and fix before Wave 4

---

## Wave 4 Validation: Production Readiness

### Goals
- Verify system handles production workloads
- Test all production features
- Validate documentation completeness
- Conduct user acceptance testing

### Scale Testing

**Batch Processing Test** (100 documents):

```bash
# Prepare 100 test PDFs (mix of sizes)
for i in {1..100}; do
  cp test-data/sample-$((i % 10)).pdf data/copyparty/uploads/doc-$i.pdf
done

# Start timer
start_time=$(date +%s)

# Monitor processing
watch 'docker compose logs processing-worker | tail -n 20'

# Wait for completion
timeout 7200 bash -c 'while [ $(ls data/logs/*.processed 2>/dev/null | wc -l) -lt 100 ]; do sleep 30; done'

# Calculate total time
end_time=$(date +%s)
elapsed=$((end_time - start_time))

echo "Processed 100 documents in ${elapsed} seconds"
echo "Average: $((elapsed / 100)) seconds per document"

# Expected:
# FP16: <2 hours (120s avg per doc)
# INT8: <1 hour (60s avg per doc)
```

**Search Load Test** (10 queries/min for 10 minutes):

```bash
# Install load testing tool
pip install locust

# Create locustfile.py
cat > locustfile.py <<'EOF'
from locust import HttpUser, task, between

class SearchUser(HttpUser):
    wait_time = between(5, 10)

    @task
    def search(self):
        queries = ["revenue", "quarterly earnings", "product growth", "expenses"]
        query = random.choice(queries)
        self.client.post("/search/query", json={"query": query, "n_results": 10})
EOF

# Run load test
locust --host=http://localhost:8000 --users=10 --spawn-rate=1 --run-time=10m --headless

# Check results
# Expected:
# - No failures
# - p95 latency <800ms
# - No memory leaks
```

**Storage Test** (1000 documents):

```bash
# Estimate storage for 1000 docs
docs_count=1000
avg_pages=20
avg_chunks=60

visual_storage=$((docs_count * avg_pages * 78))  # KB per page
text_storage=$((docs_count * avg_chunks * 51))    # KB per chunk
total_storage_mb=$(( (visual_storage + text_storage) / 1024))

echo "Estimated storage for 1000 docs: ${total_storage_mb} MB"

# Expected: ~6.5 GB (matches architecture estimates)
```

### Production Feature Testing

**Search Filters** (search-agent + ui-agent):

```bash
# Test date range filter
curl -X POST http://localhost:8000/search/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "revenue",
    "filters": {
      "date_range": {"start": "2023-01-01", "end": "2023-12-31"}
    }
  }'

# Test filename filter
curl -X POST http://localhost:8000/search/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "revenue",
    "filters": {"filename": "Q3-2023-Earnings.pdf"}
  }'

# Test page range filter
curl -X POST http://localhost:8000/search/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "revenue",
    "filters": {"page_range": {"min": 1, "max": 10}}
  }'
```

**Processing Queue** (processing-agent):

```bash
# Upload 20 documents rapidly
for i in {1..20}; do
  cp test-data/sample.pdf data/copyparty/uploads/doc-$i.pdf &
done
wait

# Check queue status
curl http://localhost:8000/api/processing/status

# Expected:
# {
#   "queue_size": 20,
#   "processing": 1,
#   "completed": 0,
#   "failed": 0
# }

# Wait for completion
watch 'curl -s http://localhost:8000/api/processing/status'

# Verify all processed
curl http://localhost:8000/api/processing/status | jq '.completed'
# Expected: 20
```

**Status Dashboard** (ui-agent):

```bash
# Open dashboard
open http://localhost:8000/status

# Verify displays:
# - Queue size
# - Processing rate (docs/min)
# - Completed count
# - Failed count
# - Current processing document
# - Estimated time remaining
```

**INT8 Quantization** (embedding-agent):

```bash
# Switch to INT8 mode
docker compose down
echo "MODEL_PRECISION=int8" >> docker/.env
docker compose up -d

# Verify model loads
docker compose logs processing-worker | grep -i "int8"

# Process test document
cp test-data/sample-10pages.pdf data/copyparty/uploads/

# Measure processing time
# Expected: ~30 seconds (2x faster than FP16)

# Verify search still works
curl -X POST http://localhost:8000/search/query \
  -H "Content-Type: application/json" \
  -d '{"query": "revenue", "n_results": 10}'

# Switch back to FP16
docker compose down
sed -i '' '/MODEL_PRECISION/d' docker/.env
docker compose up -d
```

### Documentation Validation

**User Documentation**:
- [ ] README with getting started guide
- [ ] Setup instructions (prerequisites, installation, configuration)
- [ ] Upload workflow (how to add documents)
- [ ] Search usage (query syntax, filters, interpreting results)
- [ ] Troubleshooting guide (common issues, solutions)
- [ ] Performance tuning (FP16 vs INT8, resource allocation)

**Developer Documentation**:
- [ ] Architecture overview with diagrams
- [ ] API documentation for all components
- [ ] Integration contracts (already complete)
- [ ] Deployment guide (Docker, environment variables)
- [ ] Monitoring and logging (where to find logs, metrics)

**Documentation Tests**:
```bash
# Verify all referenced commands work
# Extract commands from README
grep '```bash' README.md | grep -v '```' > test_commands.sh

# Run each command (in test mode)
bash -x test_commands.sh
```

### User Acceptance Testing

**Test Scenario 1: New User Onboarding**

User: Non-technical person wanting to search their documents

1. Follow setup instructions in README
2. Start services
3. Upload 5 sample PDFs via browser
4. Wait for processing
5. Search for "revenue growth"
6. Verify results make sense

**Pass Criteria**:
- Setup completed without asking for help
- All 5 PDFs processed successfully
- Search returned relevant pages in top 5
- User able to view results and understand scores

**Test Scenario 2: Power User Workflow**

User: Technical user with 500 documents

1. Batch upload 500 PDFs
2. Monitor processing via status dashboard
3. Perform complex searches with filters
4. Verify accuracy of results
5. Test edge cases (large PDFs, scanned documents)

**Pass Criteria**:
- Batch processing completes without intervention
- Status dashboard shows accurate progress
- Filters work correctly
- Search finds target documents in top 10
- No crashes or errors during processing

### Exit Criteria

**All Must Pass**:
1. Scale test: 100 documents processed successfully
2. Load test: 10 queries/min with p95 <800ms
3. Production features working (filters, queue, dashboard, INT8)
4. Documentation complete and tested
5. User acceptance tests passed (2/2 scenarios)

**System Health**:
- [ ] No memory leaks (monitor over 1 hour)
- [ ] No crashes or restarts
- [ ] Logs clean (no errors or warnings)
- [ ] Health checks passing continuously

**Performance Metrics**:
- [ ] Processing: FP16 <2min/10pages, INT8 <1min/10pages
- [ ] Search: p95 <500ms, p99 <800ms
- [ ] Storage: <3x original file size
- [ ] Uptime: 99% (health checks pass)

**If Any Fail**: Fix critical issues, consider deferring nice-to-have features

---

## Continuous Validation (Post-MVP)

### Automated Testing

```bash
# Daily smoke tests
cron: 0 2 * * * /path/to/scripts/smoke-test.sh

# smoke-test.sh
docker compose up -d
sleep 30  # Wait for services to start

# Test upload
cp test-data/sample.pdf data/copyparty/uploads/smoke-test-$(date +%Y%m%d).pdf

# Test search
curl -X POST http://localhost:8000/search/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "n_results": 5}' \
  | jq '.total_time_ms'

# Cleanup
docker compose down
```

### Monitoring Alerts

```yaml
# alerts.yml (future enhancement)
alerts:
  - name: search_latency_high
    condition: p95_latency > 800ms
    action: notify_team

  - name: processing_failed
    condition: failed_count > 5
    action: restart_worker

  - name: memory_high
    condition: memory_usage > 90%
    action: alert_ops
```

---

## Validation Tools & Scripts

### Automated Test Runner

```bash
#!/bin/bash
# scripts/run-validations.sh

set -e

echo "Running Wave 3 validations..."

# Integration tests
pytest tests/integration/ -v --tb=short

# Performance tests
python tests/performance/benchmark.py

# End-to-end tests
bash tests/e2e/test-upload-search.sh

# Generate report
python tests/generate-report.py

echo "✓ All validations passed"
```

### Performance Benchmark Script

```python
# tests/performance/benchmark.py

import time
import requests
from statistics import mean, median

def benchmark_search(queries, n_iterations=10):
    """Measure search latency."""
    latencies = []

    for query in queries:
        for _ in range(n_iterations):
            start = time.time()
            response = requests.post(
                "http://localhost:8000/search/query",
                json={"query": query, "n_results": 10}
            )
            elapsed = (time.time() - start) * 1000  # ms
            latencies.append(elapsed)

    return {
        "mean": mean(latencies),
        "median": median(latencies),
        "p95": sorted(latencies)[int(len(latencies) * 0.95)],
        "p99": sorted(latencies)[int(len(latencies) * 0.99)],
    }

if __name__ == "__main__":
    queries = ["revenue", "quarterly earnings", "product growth"]
    results = benchmark_search(queries)

    print("Search Latency Benchmarks:")
    print(f"  Mean:   {results['mean']:.1f} ms")
    print(f"  Median: {results['median']:.1f} ms")
    print(f"  p95:    {results['p95']:.1f} ms")
    print(f"  p99:    {results['p99']:.1f} ms")

    assert results['p95'] < 500, f"p95 latency too high: {results['p95']:.1f} ms"
    print("\n✓ Performance targets met")
```

---

## Summary

This validation strategy ensures:
1. **Early detection**: Issues caught at wave boundaries
2. **Progressive validation**: Each wave builds on previous quality
3. **Automated testing**: Repeatable validation processes
4. **Performance tracking**: Metrics measured and compared to targets
5. **Production confidence**: Comprehensive testing before release

Each wave has clear exit criteria. If validation fails, address issues before proceeding.
