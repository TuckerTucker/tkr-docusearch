# Coordination Protocol

**Purpose**: Define communication and synchronization mechanisms for parallel agent execution

**Principle**: Clear, structured communication prevents misunderstandings and enables efficient collaboration.

---

## Communication Channels

### 1. Status Broadcasting

**Purpose**: Keep all agents informed of progress and blockers

**Location**: `.context-kit/orchestration/docusearch-mvp/status/`

**Format**:
```json
{
  "agent": "storage-agent",
  "wave": 2,
  "status": "completed" | "in_progress" | "blocked" | "failed",
  "task": "Implement ChromaClient with multi-vector storage",
  "timestamp": "2023-10-06T15:30:00Z",
  "deliverables": [
    "src/storage/chroma_client.py",
    "src/storage/test_storage.py"
  ],
  "tests": {
    "passed": 23,
    "failed": 0,
    "coverage": 92
  },
  "contract_compliance": "100%",
  "blockers": [],
  "next_task": "Code review with processing-agent",
  "eta": "2023-10-07T12:00:00Z"
}
```

**Publishing**:
```bash
# Each agent creates status file after completing task
cat > .context-kit/orchestration/docusearch-mvp/status/storage-agent-wave2.json <<EOF
{
  "agent": "storage-agent",
  "wave": 2,
  "status": "completed",
  ...
}
EOF
```

**Monitoring**:
```bash
# View all agent statuses
ls -lt .context-kit/orchestration/docusearch-mvp/status/

# Check specific agent
cat .context-kit/orchestration/docusearch-mvp/status/storage-agent-wave2.json | jq
```

---

### 2. Code Reviews

**Purpose**: Consumer agents validate provider implementations before integration

**Location**: `.context-kit/orchestration/docusearch-mvp/reviews/`

**Format**:
```markdown
## Code Review: embedding-agent → processing-agent

**Reviewer**: processing-agent
**Provider**: embedding-agent
**Contract**: integration-contracts/embedding-interface.md
**Implementation**: src/embeddings/colpali_wrapper.py
**Date**: 2023-10-06

### Compliance Check

- [x] All methods implemented
- [x] Correct input/output types (TypedDict compliance)
- [x] Error handling present (all exceptions caught)
- [x] Unit tests pass (coverage: 94%)
- [x] Performance targets met (6s per image FP16)

### API Testing

```python
# Test with mock data
from src.embeddings.colpali_wrapper import ColPaliEngine
import numpy as np
from PIL import Image

engine = ColPaliEngine()
test_image = Image.open("test-data/sample-page.png")

result = engine.embed_images([test_image])
assert result["embeddings"][0].shape == (100, 768)  # ✓ Correct shape
assert result["cls_tokens"].shape == (1, 768)        # ✓ Correct CLS token
```

### Issues Found

None

### Recommendations

1. Consider adding batch size auto-adjustment based on available memory
2. Add progress callback for long-running batches

### Approval

✅ **APPROVED** for integration

Ready to replace mocks in processing-agent.

**Signature**: processing-agent
**Timestamp**: 2023-10-06T16:00:00Z
```

**Process**:
1. Provider agent marks Wave 2 complete
2. Consumer agent reviews implementation
3. Consumer tests with mock data
4. Consumer approves or requests changes
5. If approved, integration proceeds

---

### 3. Blocker Reports

**Purpose**: Communicate blocking issues and coordinate resolution

**Location**: `.context-kit/orchestration/docusearch-mvp/blockers/`

**Format**:
```markdown
## BLOCKER: ChromaDB Metadata Size Limit

**ID**: BLOCK-001
**Reported By**: storage-agent
**Date**: 2023-10-06T10:00:00Z
**Wave**: 2
**Severity**: High
**Status**: 🟡 In Progress → 🟢 Resolved

### Problem

ChromaDB metadata field limited to 2MB per entry. Multi-vector embeddings
for 10-page document exceed this limit:

- Single page: 100 tokens × 768 dims × 4 bytes = 300KB
- 10 pages combined: 3MB > 2MB limit

### Impact

- **Blocked Agent**: processing-agent (cannot store embeddings)
- **Dependent Agents**: search-agent (waiting for storage integration)
- **Timeline Impact**: +1 day to implement solution

### Root Cause

Original design didn't account for ChromaDB's per-entry metadata limit.

### Proposed Solution

Add gzip compression before base64 encoding:
- Reduces size by 4x (300KB → 75KB per page)
- 10 pages: 750KB < 2MB ✓

### Implementation Plan

1. Update `integration-contracts/storage-interface.md` with compression API
2. Implement `src/storage/compression.py`
3. Update `src/storage/chroma_client.py` to use compression
4. Test compression/decompression round-trip
5. Notify processing-agent of changes

### Changes Required

**storage-agent**:
- [ ] Add compression.py module
- [ ] Update ChromaClient.add_visual_embedding()
- [ ] Update ChromaClient.add_text_embedding()
- [ ] Update ChromaClient.get_full_embeddings()
- [ ] Add compression tests

**processing-agent**:
- [ ] No changes needed (storage API unchanged from consumer perspective)

### Resolution

✅ **Resolved** on 2023-10-07T14:00:00Z

Compression implemented and tested. All agents unblocked.

### Lessons Learned

1. Validate assumptions about third-party service limits early
2. Add compression to initial design for large metadata
3. Test with realistic data sizes, not just toy examples
```

**Severity Levels**:
- **Critical**: Blocks multiple agents, prevents Wave progression
- **High**: Blocks one agent, delays timeline
- **Medium**: Workaround available, minor delay
- **Low**: Nice-to-have, doesn't block progress

**Status Indicators**:
- 🔴 **Blocked**: No progress possible
- 🟡 **In Progress**: Solution being implemented
- 🟢 **Resolved**: Blocker removed, agents unblocked
- ⚪ **Deferred**: Not critical, postponed to future wave

---

### 4. Integration Test Results

**Purpose**: Share test results to verify compatibility

**Location**: `.context-kit/orchestration/docusearch-mvp/test-results/`

**Format**:
```markdown
## Integration Test: processing-agent + storage-agent + embedding-agent

**Date**: 2023-10-08T14:00:00Z
**Wave**: 3
**Tester**: processing-agent

### Test Scenario

Upload 10-page PDF → Process visual + text → Store in ChromaDB

### Setup

```bash
docker compose up -d
cp test-data/sample-10pages.pdf data/copyparty/uploads/
```

### Results

**Status**: ✅ PASSED

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Processing time | <2 min | 1m 47s | ✅ Pass |
| Visual embeddings stored | 10 | 10 | ✅ Pass |
| Text embeddings stored | 30 | 30 | ✅ Pass |
| Embedding shapes valid | 100% | 100% | ✅ Pass |
| Storage size | <1MB | 780KB | ✅ Pass |

### Detailed Logs

```
[2023-10-08 14:00:00] Processing started: sample-10pages.pdf
[2023-10-08 14:00:05] Docling parsing complete: 10 pages, 30 chunks
[2023-10-08 14:00:10] Visual processing: page 1/10
...
[2023-10-08 14:01:30] Visual processing complete: 10 embeddings
[2023-10-08 14:01:35] Text processing: chunk 1/30
...
[2023-10-08 14:01:45] Text processing complete: 30 embeddings
[2023-10-08 14:01:47] Stored in ChromaDB: visual_collection (10), text_collection (30)
[2023-10-08 14:01:47] Processing complete
```

### Verification

```bash
# Check ChromaDB
curl -s http://localhost:8001/api/v1/collections | jq '.[] | select(.name=="visual_collection") | .count'
# Output: 10 ✓

curl -s http://localhost:8001/api/v1/collections | jq '.[] | select(.name=="text_collection") | .count'
# Output: 30 ✓
```

### Issues Found

None

### Sign-off

✅ Integration successful. Ready for Wave 3 merge.

**Tested By**: processing-agent
**Approved By**: storage-agent, embedding-agent
```

---

## Synchronization Mechanisms

### Wave Gates

**Purpose**: Ensure all agents complete a wave before any proceed to next

**Mechanism**: Manual gate with checklist

**Wave 1 → Wave 2 Gate**:

```markdown
## Wave 1 Completion Checklist

**Date**: 2023-10-04
**Status**: 🟡 In Progress

### Agent Completion Status

- [x] infrastructure-agent: Docker builds successful
- [x] storage-agent: Contract approved
- [x] embedding-agent: Contract approved
- [x] processing-agent: Contract approved
- [x] search-agent: Contract approved
- [x] ui-agent: Contract approved

### Gate Criteria

- [x] All integration contracts reviewed and approved
- [x] Docker Compose builds without errors
- [x] All containers start successfully
- [x] Health checks pass
- [x] PyTorch MPS available in processing-worker
- [x] ColNomic 7B model cached (14GB)

### Blockers

None

### Gate Decision

✅ **APPROVED** to proceed to Wave 2

All agents may begin independent implementation.

**Approved By**: Orchestration Lead
**Date**: 2023-10-04T18:00:00Z
```

**Wave 2 → Wave 3 Gate**:

```markdown
## Wave 2 Completion Checklist

**Date**: 2023-10-07
**Status**: 🟢 Complete

### Agent Completion Status

- [x] infrastructure-agent: All services running
- [x] storage-agent: Unit tests pass (92% coverage)
- [x] embedding-agent: Unit tests pass (94% coverage)
- [x] processing-agent: Unit tests pass (91% coverage)
- [x] search-agent: Unit tests pass (93% coverage)
- [x] ui-agent: Search page functional

### Code Review Status

- [x] processing-agent reviewed embedding-agent (✅ approved)
- [x] processing-agent reviewed storage-agent (✅ approved)
- [x] search-agent reviewed embedding-agent (✅ approved)
- [x] search-agent reviewed storage-agent (✅ approved)
- [x] ui-agent reviewed search-agent (✅ approved)

### Gate Criteria

- [x] All unit tests pass (>90% coverage)
- [x] Mocks match contracts
- [x] Code reviews approved
- [x] No critical blockers

### Blockers

- [x] BLOCK-001 (ChromaDB metadata limit) - ✅ Resolved

### Gate Decision

✅ **APPROVED** to proceed to Wave 3

Begin integration: replace mocks with real implementations.

**Approved By**: Orchestration Lead
**Date**: 2023-10-07T16:00:00Z
```

---

### Daily Standups (Async)

**Purpose**: Quick daily sync on progress and blockers

**Format**: Each agent posts update by end of day

**Location**: `.context-kit/orchestration/docusearch-mvp/daily-updates/YYYY-MM-DD.md`

**Template**:
```markdown
# Daily Update: 2023-10-06

## storage-agent

**Completed**:
- Implemented ChromaClient class
- Added compression module
- Unit tests for storage operations

**In Progress**:
- Testing with real ChromaDB

**Blockers**:
- Waiting for ChromaDB metadata limit clarification

**Tomorrow**:
- Complete integration tests
- Submit for code review

## embedding-agent

**Completed**:
- Implemented ColPaliEngine
- Late interaction scoring
- FP16/INT8 quantization

**In Progress**:
- Performance benchmarking

**Blockers**:
- None

**Tomorrow**:
- Submit for code review
- Document performance results

[... other agents ...]
```

---

## Conflict Resolution

### Merge Conflicts (Should Never Happen)

**If File Conflict Detected**:

1. **Identify**: Which agents touched the same file?
2. **Review**: Check agent-assignments.md for ownership
3. **Root Cause**: Why did territorial boundaries fail?
4. **Resolution**: Offending agent reverts changes, works in assigned directory
5. **Prevention**: Update assignments to clarify boundaries

**Example**:
```
CONFLICT: Both processing-agent and search-agent modified src/common/utils.py

Resolution:
1. Create src/processing/utils.py for processing-agent
2. Create src/search/utils.py for search-agent
3. No shared files allowed (except contracts)
```

### API Disagreements

**If Consumer Disagrees with Provider API**:

1. **Document**: What's wrong with current API?
2. **Propose**: Alternative design
3. **Discuss**: Provider and consumer negotiate
4. **Decide**: Update contract or consumer adapts
5. **Implement**: Agreed-upon solution

**Example**:
```markdown
## API Disagreement: Embedding Output Format

**Consumer**: processing-agent
**Provider**: embedding-agent
**Issue**: Processing-agent needs CLS token extracted, but current API
         only returns full multi-vector sequence.

**Current API**:
```python
def embed_images(images) -> np.ndarray:
    return embeddings  # Shape: (batch, seq_length, 768)
```

**Proposed API**:
```python
def embed_images(images) -> Dict[str, np.ndarray]:
    return {
        "embeddings": embeddings,     # (batch, seq_length, 768)
        "cls_tokens": cls_tokens      # (batch, 768)
    }
```

**Resolution**:
✅ Provider agrees to update API. Contract updated. ETA: 1 day.
```

### Priority Conflicts

**If Multiple Blockers Compete for Attention**:

1. **Assess Impact**: How many agents blocked?
2. **Prioritize**: Critical > High > Medium > Low
3. **Assign**: Who has expertise to resolve quickly?
4. **Communicate**: Update ETA for affected agents
5. **Resolve**: Focus on highest priority blocker first

---

## Meeting Protocols

### Wave Kickoff Meetings

**When**: Start of each wave
**Duration**: 30 minutes
**Attendees**: All agents

**Agenda**:
1. Review wave objectives (5 min)
2. Review integration contracts (10 min)
3. Clarify dependencies (5 min)
4. Discuss risks and mitigations (5 min)
5. Q&A (5 min)

**Deliverable**: Updated orchestration-plan.md with any clarifications

### Wave Retrospectives

**When**: After each wave gate
**Duration**: 30 minutes
**Attendees**: All agents

**Agenda**:
1. What went well? (10 min)
2. What didn't go well? (10 min)
3. What should we change? (10 min)

**Deliverable**: Lessons learned document

**Example**:
```markdown
## Wave 2 Retrospective

**Date**: 2023-10-07

### What Went Well ✅

- All agents delivered on time
- Mocks matched contracts perfectly
- Unit tests caught issues early
- Code reviews were constructive

### What Didn't Go Well ❌

- ChromaDB metadata limit caught us by surprise
- Some agents had unclear boundaries initially
- Test coverage metric caused confusion (what counts?)

### Action Items 🔧

1. Add early validation of third-party service limits
2. Clarify territorial boundaries in agent-assignments.md
3. Define test coverage expectations explicitly
4. Add integration test checklist to validation-strategy.md

### Carried Forward to Wave 3

- Focus on integration testing
- Monitor performance closely
- Document any API changes immediately
```

---

## Tools & Automation

### Status Dashboard

**Script**: `scripts/status-dashboard.sh`

```bash
#!/bin/bash
# Display all agent statuses

echo "=== DocuSearch MVP Status Dashboard ==="
echo "Generated: $(date)"
echo ""

for agent in infrastructure storage embedding processing search ui; do
    status_file=".context-kit/orchestration/docusearch-mvp/status/${agent}-agent-wave2.json"

    if [ -f "$status_file" ]; then
        status=$(jq -r '.status' "$status_file")
        task=$(jq -r '.task' "$status_file")
        timestamp=$(jq -r '.timestamp' "$status_file")

        echo "[$agent-agent] $status"
        echo "  Task: $task"
        echo "  Updated: $timestamp"
        echo ""
    else
        echo "[$agent-agent] ⚪ No status reported"
        echo ""
    fi
done

# Check for blockers
echo "=== Active Blockers ==="
blocker_count=$(find .context-kit/orchestration/docusearch-mvp/blockers/ -name "*.md" | wc -l)

if [ $blocker_count -eq 0 ]; then
    echo "✅ No active blockers"
else
    echo "🔴 $blocker_count blockers found:"
    for blocker in .context-kit/orchestration/docusearch-mvp/blockers/*.md; do
        echo "  - $(basename "$blocker")"
    done
fi
```

**Usage**:
```bash
./scripts/status-dashboard.sh
```

### Auto-notify on Status Changes

**Script**: `scripts/watch-status.sh`

```bash
#!/bin/bash
# Watch for status changes and notify

watch -n 60 'bash scripts/status-dashboard.sh'
```

### Blocker Alert

**Script**: `scripts/check-blockers.sh`

```bash
#!/bin/bash
# Check for new blockers and alert

NEW_BLOCKERS=$(find .context-kit/orchestration/docusearch-mvp/blockers/ \
  -name "*.md" -mtime -1)

if [ ! -z "$NEW_BLOCKERS" ]; then
    echo "🔴 NEW BLOCKERS DETECTED:"
    echo "$NEW_BLOCKERS"

    # Could send Slack/email notification here
    # slack-cli send "#docusearch-mvp" "New blocker: $NEW_BLOCKERS"
fi
```

---

## Communication Best Practices

### For All Agents

1. **Post status daily** (even if "no progress")
2. **Report blockers immediately** (don't wait)
3. **Update contracts promptly** if API changes
4. **Review consumer feedback** within 24 hours
5. **Ask questions early** (don't guess)

### For Provider Agents

1. **Document your API clearly** with examples
2. **Notify consumers** of any breaking changes
3. **Be responsive** to code review feedback
4. **Provide test fixtures** for integration testing
5. **Meet performance targets** specified in contracts

### For Consumer Agents

1. **Test provider APIs early** (don't wait for Wave 3)
2. **Give constructive feedback** in code reviews
3. **Report bugs clearly** with reproduction steps
4. **Adapt to minor API changes** (don't block on nitpicks)
5. **Validate contracts** match your needs

### For All

**Good Communication**:
```
"Embedding-agent: embed_images() returns shape (batch, seq_len, 768).
I need CLS token extracted (batch, 768). Can you add cls_token field
to output dict? This unblocks processing-agent."
```

**Bad Communication**:
```
"This API doesn't work for me. Please fix."
```

---

## Emergency Procedures

### Critical Blocker

**If Critical Blocker Blocks Multiple Agents**:

1. **All agents stop** current work
2. **Focus on blocker** resolution
3. **Assign experts** to solve quickly
4. **Update timeline** after resolution
5. **Resume normal work** once unblocked

### Agent Unavailable

**If Agent Becomes Unavailable**:

1. **Assess impact**: What's blocked?
2. **Find backup**: Who can take over?
3. **Transfer ownership**: Code review + handoff
4. **Update assignments**: New owner documented
5. **Continue work**: Minimize delay

### Timeline Slippage

**If Wave Taking Longer Than Expected**:

1. **Assess delay**: How far behind?
2. **Identify bottleneck**: What's slow?
3. **Re-prioritize**: Cut non-critical features?
4. **Add resources**: More agents on bottleneck?
5. **Update timeline**: Realistic new ETA

---

## Summary

This coordination protocol ensures:
1. **Visibility**: All agents know project status
2. **Rapid resolution**: Blockers addressed quickly
3. **Quality reviews**: Code validated before integration
4. **Smooth handoffs**: Clear expectations and deliverables
5. **Efficient collaboration**: Minimize meetings, maximize async

Follow this protocol to maintain momentum and deliver on schedule.
