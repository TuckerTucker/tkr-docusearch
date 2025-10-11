# Coordination Protocol: Page Images & Document View

**Orchestration Plan:** page-images-document-view
**Created:** 2025-10-11

---

## Overview

This document defines the communication and coordination protocol for the 6 agents implementing page image persistence and the document view feature. It ensures zero-conflict execution through clear handoff procedures, status management, and synchronization gates.

---

## Communication Channels

### Status Updates

**Location:** `.context-kit/orchestration/page-images-document-view/status/`

Each agent maintains a status file:
```
status/
  infra-agent.status
  image-agent.status
  storage-agent.status
  parser-agent.status
  visual-processor-agent.status
  api-agent.status
  ui-agent.status
```

**Status File Format:**
```yaml
agent: infra-agent
wave: 1
status: in_progress  # or: pending, completed, blocked, failed
current_task: "Creating image_config.py"
progress: 75  # percentage
updated: 2025-10-11T15:30:00Z
blockers: []  # or: [{blocking_agent, reason, estimated_unblock}]
deliverables_completed:
  - docker-compose.yml updated
  - .gitignore updated
deliverables_pending:
  - image_config.py
  - docs/IMAGE_STORAGE.md
```

### Update Frequency

- **Task start:** Update status to `in_progress`
- **Deliverable complete:** Add to `deliverables_completed`
- **Blocked:** Update status to `blocked`, add blocker details
- **Wave complete:** Update status to `completed`

---

## Wave Synchronization Protocol

### Wave Gate Process

```
┌─────────────────────────────────────────────────────────┐
│ Wave N agents complete their work                        │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ Each agent updates status to "completed"                 │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ Gate Keeper runs validation tests                        │
│ (Automated test suite for wave N)                        │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
         ┌───────┴────────┐
         │ Tests pass?     │
         └───────┬────────┘
                 │
      ┌──────────┴──────────┐
      │ Yes               No │
      ▼                     ▼
┌──────────────┐   ┌───────────────────┐
│ Gate opens    │   │ Report failures   │
│ Wave N+1 starts│   │ Block next wave   │
└──────────────┘   └───────────────────┘
```

**Gate Keeper Role:** Can be automated script or human reviewer

### Wave 1 Gate (Foundation)

**Participants:** infra-agent, image-agent, storage-agent

**Gate Check Commands:**
```bash
# Run by gate keeper after all agents report "completed"
./scripts/validate-wave1.sh
```

**Wave 1 Validation Script:**
```bash
#!/bin/bash
# scripts/validate-wave1.sh

echo "Validating Wave 1: Foundation..."

# 1. Check agent status
for agent in infra-agent image-agent storage-agent; do
  status=$(cat .context-kit/orchestration/page-images-document-view/status/${agent}.status | grep "status:" | awk '{print $2}')
  if [ "$status" != "completed" ]; then
    echo "❌ $agent not complete: $status"
    exit 1
  fi
done

# 2. Run test suite
pytest tests/test_image_utils.py -v || exit 1
pytest src/storage/test_storage.py -v || exit 1

# 3. Validate imports
python -c "from src.config.image_config import PAGE_IMAGE_DIR" || exit 1
python -c "from src.processing.image_utils import save_page_image" || exit 1

# 4. Check directory
test -d data/page_images || exit 1

# 5. Validate Docker Compose
docker-compose -f docker/docker-compose.yml config > /dev/null || exit 1

echo "✅ Wave 1 validation passed"
echo "status: passed" > .context-kit/orchestration/page-images-document-view/gates/wave1.gate
```

**Gate Pass Condition:** Script exits 0

### Wave 2 Gate (Integration)

**Participants:** parser-agent, visual-processor-agent

**Gate Check:**
```bash
./scripts/validate-wave2.sh
```

**Includes:**
- Integration test (upload PDF, verify images saved)
- ChromaDB query (verify metadata has paths)
- Performance test (processing time increase <10%)

### Wave 3 Gate (Backend API)

**Participant:** api-agent

**Gate Check:**
```bash
./scripts/validate-wave3.sh
```

**Includes:**
- API endpoint tests (curl or pytest)
- Performance tests (latency < targets)
- Security audit (path traversal prevention)

### Wave 4 Gate (Frontend)

**Participant:** ui-agent

**Gate Check:**
```bash
./scripts/validate-wave4.sh  # Automated tests
# Plus manual browser testing checklist
```

---

## Blocker Management

### Blocker Report Format

When an agent is blocked:

```yaml
agent: parser-agent
status: blocked
blockers:
  - blocking_agent: image-agent
    reason: "Waiting for save_page_image() implementation"
    required_deliverable: "image_utils.py with save_page_image()"
    estimated_unblock: "2025-10-11T18:00:00Z"
    severity: critical  # or: high, medium, low
```

### Blocker Resolution Protocol

1. **Blocked agent** updates status file
2. **Blocking agent** sees blocker (notified via status poll)
3. **Blocking agent** prioritizes unblocking work
4. **Blocking agent** updates status when deliverable complete
5. **Blocked agent** polls for updates, resumes when unblocked

### Blocker Escalation

If blocked for >2 hours:
1. Blocked agent posts escalation message
2. Gate keeper / orchestration manager investigates
3. May reassign work or adjust plan

---

## Code Review Protocol

### Cross-Agent Review Requirements

**Provider → Consumer Reviews:**

| Provider | Consumer | Review Item |
|----------|----------|-------------|
| infra-agent → all | `image_config.py` API surface |
| image-agent → parser-agent | `image_utils.py` function signatures |
| storage-agent → visual-processor-agent | `add_visual_embedding()` parameters |
| parser-agent → visual-processor-agent | `Page` dataclass fields |
| api-agent → ui-agent | API response schemas |

### Review Checklist

Each consumer must verify:
- [ ] Contract compliance (signatures match)
- [ ] Error handling adequate
- [ ] Performance acceptable
- [ ] Documentation clear
- [ ] Tests comprehensive

### Review Process

1. **Provider** completes implementation, updates status
2. **Consumer** reads provider's code
3. **Consumer** runs provider's tests
4. **Consumer** validates contract compliance
5. **Consumer** posts review result:

```yaml
review:
  reviewer: parser-agent
  reviewed: image-agent/image_utils.py
  result: approved  # or: changes_requested
  timestamp: 2025-10-11T16:00:00Z
  comments:
    - "Contract compliance: ✅"
    - "Error handling: ✅"
    - "Performance: ✅"
    - "Documentation: ✅"
```

---

## Dependency Handoff Protocol

### Interface-First Development

**Principle:** Define interfaces before implementation

**Example: image-agent → parser-agent**

1. **Contract phase** (Wave 0):
   - Contract defines `save_page_image(image, doc_id, page_num) -> (str, str)`
   - Contract approved by both agents

2. **Implementation phase** (Wave 1):
   - image-agent implements function
   - parser-agent can write import statement (won't crash if function exists)

3. **Integration phase** (Wave 2):
   - parser-agent uses function
   - Already knows signature from contract

### Progressive Integration Testing

**Level 1: Unit Tests** (by provider)
- Test each function in isolation
- Mock dependencies

**Level 2: Integration Tests** (by consumer)
- Test provider's code from consumer's perspective
- Real calls, real data

**Level 3: End-to-End Tests** (by gate keeper)
- Test complete workflow
- All agents' code together

---

## Failure Recovery

### Failure Types

**Type 1: Unit Test Failure**
- **Handler:** Provider agent
- **Action:** Fix code, re-run tests, update status
- **Escalation:** If not fixed in 1 hour, report to gate keeper

**Type 2: Integration Test Failure**
- **Handler:** Provider + Consumer agents
- **Action:** Debug together, identify root cause
- **Resolution:** Provider fixes if API mismatch, consumer fixes if usage error

**Type 3: Wave Gate Failure**
- **Handler:** Gate keeper
- **Action:** Identify failing agent, block next wave
- **Resolution:** Agent fixes issue, gate re-runs validation

**Type 4: Performance Regression**
- **Handler:** Agent that introduced regression
- **Action:** Optimize code or adjust target
- **Resolution:** Gate keeper approves updated target

### Rollback Procedure

If wave fails catastrophically:

```bash
# Example: Wave 2 fails, rollback to Wave 1
git checkout wave1-complete-branch

# Or selective rollback
git checkout HEAD -- src/processing/docling_parser.py
git checkout HEAD -- src/processing/visual_processor.py
```

Each wave should create a git tag:
- `wave1-complete`
- `wave2-complete`
- `wave3-complete`
- `wave4-complete`

---

## Status Monitoring

### Automated Status Dashboard

```bash
# scripts/check-status.sh

#!/bin/bash

echo "=== Agent Status Dashboard ==="
echo ""

for agent_file in .context-kit/orchestration/page-images-document-view/status/*.status; do
  agent=$(basename $agent_file .status)
  wave=$(grep "wave:" $agent_file | awk '{print $2}')
  status=$(grep "status:" $agent_file | awk '{print $2}')
  progress=$(grep "progress:" $agent_file | awk '{print $2}')
  task=$(grep "current_task:" $agent_file | cut -d: -f2-)

  printf "%-25s Wave %s  [%-10s] %3s%% - %s\n" "$agent" "$wave" "$status" "$progress" "$task"
done

echo ""
echo "=== Wave Gates ==="
for gate_file in .context-kit/orchestration/page-images-document-view/gates/*.gate; do
  if [ -f "$gate_file" ]; then
    wave=$(basename $gate_file .gate)
    gate_status=$(grep "status:" $gate_file | awk '{print $2}')
    printf "%-10s: %s\n" "$wave" "$gate_status"
  fi
done
```

**Output:**
```
=== Agent Status Dashboard ===

infra-agent               Wave 1  [completed ] 100% - All tasks done
image-agent               Wave 1  [completed ] 100% - All tasks done
storage-agent             Wave 1  [completed ] 100% - All tasks done
parser-agent              Wave 2  [in_progress]  60% - Integrating image_utils
visual-processor-agent    Wave 2  [pending   ]   0% - Waiting for parser-agent
api-agent                 Wave 3  [pending   ]   0% - Waiting for Wave 2
ui-agent                  Wave 4  [pending   ]   0% - Waiting for Wave 3

=== Wave Gates ===
wave1     : passed
wave2     : pending
wave3     : pending
wave4     : pending
```

---

## Conflict Prevention Strategies

### Strategy 1: Territorial Boundaries

**Rule:** Each agent owns specific files. No overlap.

**Enforcement:**
- Pre-commit hook validates file ownership
- Any modification outside territory triggers warning

### Strategy 2: Interface Contracts

**Rule:** All integration points have documented contracts

**Enforcement:**
- Contracts reviewed in Wave 0
- All agents acknowledge before coding starts

### Strategy 3: Progressive Validation

**Rule:** Test early, test often

**Enforcement:**
- Unit tests required before marking task complete
- Integration tests run at wave gates
- Performance tests in final validation

### Strategy 4: Dependency Injection

**Rule:** Components receive dependencies, not import directly

**Example:**
```python
# ❌ Bad: Direct import creates tight coupling
from src.processing.image_utils import save_page_image

# ✅ Good: Dependency injection (easier to test, mock)
class Parser:
    def __init__(self, image_saver=None):
        self.image_saver = image_saver or save_page_image
```

---

## Meeting Schedule (Optional)

For complex orchestrations, consider sync meetings:

**Wave 0 Kickoff Meeting**
- Review contracts
- Clarify ambiguities
- Assign agents

**Wave Gate Reviews**
- After each wave completes
- Review test results
- Plan next wave

**Daily Standup** (if team-based)
- Each agent reports: done yesterday, doing today, blockers
- 15 minutes max

---

## Appendix: Status File Examples

### Example 1: Agent In Progress

```yaml
agent: image-agent
wave: 1
status: in_progress
current_task: "Implementing generate_thumbnail()"
progress: 75
updated: 2025-10-11T15:45:00Z
blockers: []
deliverables_completed:
  - save_page_image() implemented
  - get_image_path() implemented
  - delete_document_images() implemented
deliverables_pending:
  - generate_thumbnail()
  - image_exists()
  - Unit tests
estimated_completion: 2025-10-11T17:00:00Z
```

### Example 2: Agent Blocked

```yaml
agent: parser-agent
wave: 2
status: blocked
current_task: "Waiting for image_utils.save_page_image()"
progress: 10
updated: 2025-10-11T16:00:00Z
blockers:
  - blocking_agent: image-agent
    reason: "save_page_image() not yet available"
    required_deliverable: "src/processing/image_utils.py"
    severity: critical
    reported: 2025-10-11T14:00:00Z
    estimated_unblock: 2025-10-11T17:00:00Z
deliverables_completed:
  - Page dataclass updated (fields added)
deliverables_pending:
  - Call save_page_image() in _extract_pages_from_result()
  - Update tests
```

### Example 3: Agent Completed

```yaml
agent: infra-agent
wave: 1
status: completed
current_task: "Wave 1 complete"
progress: 100
updated: 2025-10-11T14:30:00Z
blockers: []
deliverables_completed:
  - data/page_images/ directory created
  - docker-compose.yml updated
  - .gitignore updated
  - src/config/image_config.py created
  - docs/IMAGE_STORAGE.md written
tests_passed:
  - test_config_validation
  - test_directory_exists
  - test_docker_compose_valid
review_status: approved_by_image-agent
```

---

**Document Version:** 1.0
**Last Updated:** 2025-10-11
