# Audio Album Art - Orchestration

**Feature**: Audio player album art display with default SVG fallback

**Status**: Wave 0 COMPLETE - Ready for Wave 1 execution

**Duration**: 0.5 days (4 hours with parallel execution)

---

## Quick Start

### For Orchestrator

```bash
# 1. Review plan
cat orchestration-plan.md

# 2. Review contracts
ls integration-contracts/

# 3. Launch Wave 1 agents (parallel)
# See agent-assignments.md for detailed commands

# 4. Monitor progress
watch -n 30 'bash scripts/check-wave1-complete.sh'

# 5. Validate quality gates
pytest src/processing/test_audio_album_art.py -v

# 6. Proceed to Wave 2 (orchestrator tasks)
```

---

## For Individual Agents

### backend-api-agent

```bash
# 1. Read your assignment
cat agent-assignments.md  # Find "Agent 1: backend-api-agent"

# 2. Review contracts to implement
cat integration-contracts/01-album-art-api.md
cat integration-contracts/02-album-art-metadata.md

# 3. Start development
# - Implement GET /documents/{doc_id}/cover
# - Extend DocumentMetadata schema
# - Write unit tests

# 4. Update status
vim status/backend-api-agent.json
# Set progress, deliverables status

# 5. Mark complete when done
jq '.status = "complete"' status/backend-api-agent.json
```

### frontend-ui-agent

```bash
# 1. Wait for backend-api-agent (check IC-001, IC-002)
cat status/backend-api-agent.json | jq '.integration_points'

# 2. Read your assignment
cat agent-assignments.md  # Find "Agent 2: frontend-ui-agent"

# 3. Review contracts
cat integration-contracts/03-default-svg-fallback.md

# 4. Start development
# - Add HTML album art structure
# - Add CSS styles (responsive)
# - Implement JavaScript loading logic
# - Convert default SVG to data URI

# 5. Manual testing
open src/frontend/details.html?doc={test_doc}

# 6. Update status and mark complete
```

### integration-test-agent

```bash
# 1. Wait for both backend and frontend
cat status/backend-api-agent.json | jq '.status'
cat status/frontend-ui-agent.json | jq '.status'

# 2. Review all contracts
ls integration-contracts/

# 3. Write integration tests
# - Full pipeline tests
# - Performance tests
# - Browser compatibility tests

# 4. Create manual testing page
cat > src/frontend/test_audio_player_album_art.html

# 5. Run tests and mark complete
pytest src/processing/test_audio_album_art.py::TestIntegration -v
```

---

## Key Files

| File | Purpose | Owner |
|------|---------|-------|
| `orchestration-plan.md` | Complete execution plan | orchestrator |
| `agent-assignments.md` | Agent territories & responsibilities | orchestrator |
| `validation-strategy.md` | Quality gates & testing approach | orchestrator |
| `coordination-protocol.md` | Communication & status management | orchestrator |
| `integration-contracts/01-album-art-api.md` | API endpoint specification | backend-api-agent |
| `integration-contracts/02-album-art-metadata.md` | Metadata extension spec | backend-api-agent |
| `integration-contracts/03-default-svg-fallback.md` | UI fallback spec | frontend-ui-agent |
| `status/{agent}-agent.json` | Real-time agent status | each agent |

---

## Integration Contracts Summary

### IC-001: Album Art API Endpoint
- **Provider**: backend-api-agent
- **Consumers**: frontend-ui-agent, integration-test-agent
- **Deliverable**: `GET /documents/{doc_id}/cover`

### IC-002: Album Art Metadata Extension
- **Provider**: backend-api-agent
- **Consumers**: frontend-ui-agent
- **Deliverable**: `has_album_art` and `album_art_url` fields in DocumentMetadata

### IC-003: Default SVG Fallback
- **Provider**: frontend-ui-agent (self-contained)
- **Deliverable**: Data URI constant for gray microphone SVG

---

## Wave Structure

### Wave 1: Parallel Implementation (3 agents, 2-3 hours)

| Agent | Tasks | Duration |
|-------|-------|----------|
| backend-api | API endpoint + metadata | 1.5 hours |
| frontend-ui | HTML + CSS + JS + SVG | 2 hours |
| integration-test | Tests + validation | 1 hour |

**Synchronization**: All agents work simultaneously
**Gate**: All unit tests pass, manual testing complete

### Wave 2: Integration & QA (orchestrator, 30 minutes)

| Task | Owner | Duration |
|------|-------|----------|
| Cross-agent integration verification | orchestrator | 10 min |
| Accessibility audit | orchestrator | 10 min |
| Performance validation | orchestrator | 5 min |
| Documentation updates | orchestrator | 5 min |

**Gate**: All quality gates pass, production ready

---

## Quality Gates

### Wave 1 Gates

1. **Backend API** (Gate 1.1)
   - All unit tests pass
   - Endpoint serves images correctly
   - Metadata fields present
   - Security validation passes

2. **Frontend UI** (Gate 1.2)
   - Visual regression tests pass
   - Browser compatibility verified
   - Accessibility score ≥ 90

3. **Integration Testing** (Gate 1.3)
   - End-to-end pipeline tests pass
   - Performance within budget

### Wave 2 Gates

1. **Cross-browser validation**
2. **Mobile responsiveness (5 viewports)**
3. **No regressions in existing features**
4. **Documentation complete**

---

## Success Metrics

**Technical**:
- ✅ Zero merge conflicts (territorial boundaries)
- ✅ 100% contract compliance
- ✅ < 2 integration bugs

**Delivery**:
- ✅ Wave 1: 2-3 hours (parallel)
- ✅ Wave 2: 30 minutes
- ✅ **Total: 0.5 days**

**Quality**:
- ✅ Accessibility score > 90
- ✅ Image load time < 500ms
- ✅ All browsers supported

---

## Status Monitoring

### Check Overall Progress

```bash
# Quick status check
bash scripts/check-wave1-complete.sh

# Detailed status
for agent in backend-api frontend-ui integration-test; do
  echo "=== ${agent}-agent ==="
  cat status/${agent}-agent.json | jq '{status, progress, blockers, tests}'
done
```

### Watch for Completion

```bash
# Auto-refresh every 30 seconds
watch -n 30 'bash scripts/check-wave1-complete.sh'
```

---

## Troubleshooting

### Agent Blocked?

```bash
# Check blocker details
cat status/{agent}-agent.json | jq '.blockers'

# Check dependency status
cat status/{provider}-agent.json | jq '.integration_points'
```

### Tests Failing?

```bash
# Run specific failing test
pytest src/processing/test_audio_album_art.py::test_name -v

# Check test output
cat test-results.xml
```

### Merge Conflict?

**Should not happen** due to territorial boundaries. If it does:

1. Check agent-assignments.md for file ownership
2. Identify which agent violated territory
3. Rollback offending changes
4. Clarify boundaries
5. Resume work

---

## References

- **Wireframes**: `.context-kit/_ref/details_page/audio.svg`
- **Default SVG**: `.context-kit/_ref/details_page/default_audio_cover_art.svg`
- **Current Code**: `src/frontend/audio-player.js`, `src/processing/documents_api.py`
- **Audio Metadata**: `src/processing/audio_metadata.py`

---

## Contact

**Orchestrator**: Review orchestration-plan.md for complete details

**Agents**: Update status files frequently, communicate via status/*.json

---

*Generated: 2025-10-15 | Wave 0 Orchestrator*
