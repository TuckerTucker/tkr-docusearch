# DocuSearch MVP Orchestration

**Comprehensive parallel agent orchestration plan for implementing a local document processing and semantic search system**

---

## Quick Start

### For Project Leads

```bash
# Review the orchestration plan
cat orchestration-plan.md

# Assign agents to team members
vim agent-assignments.md  # Update "Team Member" column

# Kickoff Wave 1 (Contract Definition)
# All agents review integration contracts
cd integration-contracts/
ls -la  # Review all interface contracts
```

### For Individual Agents

```bash
# 1. Find your assignments
grep -A 20 "YOUR-AGENT-NAME" agent-assignments.md

# 2. Review your integration contracts
cat integration-contracts/YOUR-CONTRACT.md

# 3. Set up your workspace
mkdir -p YOUR-OWNED-DIRECTORY
cd YOUR-OWNED-DIRECTORY

# 4. Start Wave 1 tasks (see orchestration-plan.md)
```

---

## Document Overview

| Document | Purpose | Who Reads |
|----------|---------|-----------|
| **orchestration-plan.md** | Master execution plan with 4 waves | Everyone (overview) |
| **agent-assignments.md** | Territorial ownership and responsibilities | Everyone (find your role) |
| **validation-strategy.md** | Quality gates and testing requirements | Everyone (know exit criteria) |
| **coordination-protocol.md** | Communication and status updates | Everyone (daily reference) |
| **integration-contracts/** | API interfaces and data contracts | Agents implementing those interfaces |

---

## Architecture Summary

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        User Browser                          │
│                    (Copyparty Web UI)                        │
└───────────────┬─────────────────────────────────────────────┘
                │ HTTP (port 8000)
┌───────────────▼─────────────────────────────────────────────┐
│                   Copyparty Container                        │
│  - File upload/browsing (ui-agent)                          │
│  - Event hooks (ui-agent)                                   │
│  - Search page (ui-agent)                                   │
└───────────────┬─────────────────────────────────────────────┘
                │ Event Hook
┌───────────────▼─────────────────────────────────────────────┐
│              Processing Worker Container                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Docling Parser (processing-agent)                      │ │
│  │ ↓                                                       │ │
│  │ Visual + Text Processing (processing-agent)            │ │
│  │ ↓                                                       │ │
│  │ ColPali Embeddings (embedding-agent)                   │ │
│  │ ↓                                                       │ │
│  │ ChromaDB Storage (storage-agent)                       │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────┬─────────────────────────────────────────────┘
                │ HTTP API (port 8001)
┌───────────────▼─────────────────────────────────────────────┐
│                  ChromaDB Container                          │
│  - Vector storage (storage-agent)                           │
│  - Two-stage search (search-agent)                          │
└─────────────────────────────────────────────────────────────┘
```

### Agent Roster

| Agent | Responsibility | Output |
|-------|---------------|--------|
| **infrastructure-agent** | Docker orchestration | Runnable containers |
| **storage-agent** | ChromaDB integration | Storage client library |
| **embedding-agent** | ColPali engine | Embedding generation |
| **processing-agent** | Document processing | Processing pipeline |
| **search-agent** | Semantic search | Search engine |
| **ui-agent** | Web UI & hooks | User interface |

---

## Execution Timeline

### Wave 1: Foundation (Days 1-2)
**All agents define integration contracts**

- infrastructure-agent: Docker environment setup
- All agents: Review and approve contracts
- Gate: Contract compliance validation

### Wave 2: Components (Days 3-7)
**All agents implement independently with mocks**

- infrastructure-agent: Complete Docker Compose
- storage-agent: ChromaDB client + multi-vector storage
- embedding-agent: ColPali wrapper + late interaction
- processing-agent: Document processing + mocks
- search-agent: Two-stage search + mocks
- ui-agent: Search page + event hooks
- Gate: Unit tests pass, code review approved

### Wave 3: Integration (Days 8-12)
**Replace mocks with real integrations**

- processing-agent: Integrate real embedding + storage
- search-agent: Integrate real embedding + storage
- ui-agent: Integrate real search + processing
- Gate: End-to-end workflows functional

### Wave 4: Production (Days 13-15)
**Add production features and scale testing**

- search-agent: Add filters and optimizations
- ui-agent: Add dashboard and previews
- processing-agent: Add queue and INT8 support
- Gate: 100 document batch test passes

---

## Key Integration Points

### 1. Multi-Vector Embeddings

**Format**: ColNomic produces sequences, not single vectors

```python
# Shape: (seq_length, 768) not (768,)
embeddings = model.embed_images([page_image])
# embeddings.shape = (100, 768)  # 100 tokens × 768 dims
```

**Storage Strategy**: CLS token + compressed full sequence

```python
# Store representative vector for fast search
representative = embeddings[0]  # CLS token

# Store full sequence in metadata (compressed)
compressed = gzip.compress(embeddings.tobytes())
metadata["full_embeddings"] = base64.b64encode(compressed)
```

### 2. Two-Stage Search

**Stage 1**: Fast retrieval with representative vectors (200ms)
```python
candidates = chromadb.search(query_cls, n=100)
```

**Stage 2**: Precise re-ranking with late interaction (100ms)
```python
scores = colpali.score_multi_vector(query_full, candidate_embeddings)
```

### 3. Event-Driven Processing

**Trigger**: Copyparty calls hook on upload
```python
# hooks/on_upload.py
def on_upload(file_path):
    worker.process_document(file_path)
```

---

## Critical Success Factors

### Technical Risks

1. **M1 Compatibility** (High Risk)
   - Mitigation: Test MPS early in Wave 2
   - Fallback: CPU inference (3x slower)

2. **Model Memory** (Medium Risk)
   - Mitigation: INT8 quantization (7GB vs 14GB)
   - Fallback: Process smaller batches

3. **Search Performance** (Medium Risk)
   - Mitigation: Two-stage pipeline
   - Target: <500ms p95 latency

### Process Risks

1. **Integration Conflicts** (Low Risk with Territorial Ownership)
   - Prevention: Zero overlapping file writes
   - Resolution: Clear ownership in agent-assignments.md

2. **API Mismatches** (Low Risk with Contracts)
   - Prevention: Detailed integration contracts
   - Resolution: Code reviews before integration

3. **Timeline Slippage** (Medium Risk)
   - Prevention: Progressive validation gates
   - Resolution: Re-prioritize features

---

## Communication

### Daily Updates

**Each agent posts by end of day**:
```bash
# Create/update status file
cat > .context-kit/orchestration/docusearch-mvp/status/YOUR-AGENT-wave2.json <<EOF
{
  "agent": "YOUR-AGENT",
  "wave": 2,
  "status": "in_progress",
  "task": "Implementing core functionality",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "blockers": []
}
EOF
```

**View all statuses**:
```bash
bash scripts/status-dashboard.sh
```

### Code Reviews

**Before Wave 3 integration**:

1. Provider marks Wave 2 complete
2. Consumer reviews implementation
3. Consumer tests with mock data
4. Consumer approves or requests changes

**Template**: See `coordination-protocol.md` section 2

### Blockers

**Report immediately**:
```bash
# Create blocker report
cat > .context-kit/orchestration/docusearch-mvp/blockers/BLOCK-001.md <<EOF
## BLOCKER: Short description

**Reported By**: your-agent
**Severity**: High
**Impact**: Who is blocked?
**Proposed Solution**: What should we do?
EOF
```

---

## Validation Gates

### Wave 1 → Wave 2

- [ ] All contracts reviewed
- [ ] Docker builds successfully
- [ ] MPS available in container
- [ ] Model cached (14GB)

### Wave 2 → Wave 3

- [ ] Unit tests pass (>90% coverage)
- [ ] Mocks match contracts
- [ ] Code reviews approved
- [ ] No critical blockers

### Wave 3 → Wave 4

- [ ] End-to-end workflow works
- [ ] 10-page PDF processes in <2 min
- [ ] Search latency <500ms p95
- [ ] Integration tests pass

### Wave 4 → Production

- [ ] 100 document batch test passes
- [ ] All production features working
- [ ] Documentation complete
- [ ] User acceptance test passed

---

## Getting Help

### Quick Reference

```bash
# View your tasks
grep -A 50 "YOUR-AGENT" orchestration-plan.md

# Check gate criteria
grep -A 20 "Wave X → Wave Y" validation-strategy.md

# Review contract
cat integration-contracts/YOUR-CONTRACT.md

# Post status update
bash scripts/update-status.sh YOUR-AGENT "task description"

# Check for blockers
bash scripts/check-blockers.sh
```

### Escalation

1. **Blocker?** → Post in `blockers/` directory
2. **API question?** → Review integration contract, then ask provider agent
3. **Timeline concern?** → Post in daily update, notify orchestration lead
4. **Emergency?** → See coordination-protocol.md emergency procedures

---

## Directory Structure

```
.context-kit/orchestration/docusearch-mvp/
├── README.md                           # This file
├── orchestration-plan.md               # Master execution plan (4 waves)
├── agent-assignments.md                # Territorial ownership
├── validation-strategy.md              # Quality gates
├── coordination-protocol.md            # Communication protocol
│
├── integration-contracts/              # API interface specifications
│   ├── storage-interface.md           # ChromaDB client API
│   ├── embedding-interface.md         # ColPali engine API
│   ├── processing-interface.md        # Document processing workflow
│   ├── search-interface.md            # Two-stage search API
│   ├── config-interface.md            # Environment variables
│   └── ui-interface.md                # Search page API
│
├── status/                            # Agent status updates (daily)
│   ├── infrastructure-agent-wave2.json
│   ├── storage-agent-wave2.json
│   ├── embedding-agent-wave2.json
│   ├── processing-agent-wave2.json
│   ├── search-agent-wave2.json
│   └── ui-agent-wave2.json
│
├── reviews/                           # Code reviews (Wave 2 → Wave 3)
│   ├── embedding-to-processing.md
│   ├── storage-to-processing.md
│   └── search-to-ui.md
│
├── blockers/                          # Active blockers
│   └── BLOCK-XXX.md
│
└── test-results/                      # Integration test reports
    └── wave3-integration-tests.md
```

---

## Success Metrics

### MVP Targets (Wave 4 Complete)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Processing Speed** | <2min for 10-page PDF | Time from upload to searchable |
| **Search Latency** | <500ms p95 | p95 latency for hybrid queries |
| **Storage Efficiency** | <3x original size | Embeddings + metadata overhead |
| **Batch Processing** | 100 docs in <2 hours | Queue throughput (FP16) |
| **Test Coverage** | >90% per component | pytest --cov reports |
| **Uptime** | 99% | Docker health checks |

### Quality Targets

- All unit tests pass
- All integration tests pass
- All code reviews approved
- Zero critical bugs
- Documentation complete
- User acceptance test passed

---

## Next Steps

1. **Project Lead**: Assign agents to team members
2. **All Agents**: Review orchestration-plan.md and your agent-assignments.md section
3. **All Agents**: Study your integration contracts
4. **Kickoff Meeting**: Discuss contracts, dependencies, and timeline
5. **Begin Wave 1**: Define contracts and set up environment
6. **Daily Updates**: Post status to `status/` directory
7. **Wave Gates**: Complete validation checklist before proceeding

---

## Resources

### Documentation

- Architecture: `_ref/mvp-architecture.md`
- Docker Deployment: `_ref/docker-deployment-m1.md`
- Embedding Models: `_ref/embedding-models-comparison.md`

### External Links

- ColPali Engine: https://github.com/illuin-tech/colpali
- ChromaDB Docs: https://docs.trychroma.com/
- Docling Docs: https://ds4sd.github.io/docling/
- PyTorch MPS: https://pytorch.org/docs/stable/notes/mps.html

---

## Contact

**Orchestration Lead**: TBD
**Wave Status**: Pre-Wave 1 (Planning)
**Last Updated**: 2023-10-06

---

**Ready to begin? Start with Wave 1 in orchestration-plan.md!**
