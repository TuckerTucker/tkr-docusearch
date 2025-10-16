# Coordination Protocol - Audio Album Art

**Purpose**: Define communication and synchronization mechanisms between parallel agents

**Model**: Asynchronous status broadcasting with contract-based coordination

---

## Protocol Overview

### Communication Channels

1. **Status Files**: JSON files for async progress updates
2. **Integration Contracts**: Shared specifications for coordination
3. **Quality Gates**: Synchronization points between waves

### Coordination Philosophy

- **Loose Coupling**: Agents communicate through contracts, not direct dependencies
- **Autonomous Execution**: Each agent works independently within its territory
- **Progressive Integration**: Validate continuously, not just at the end

---

## Status Broadcasting

### Status File Format

**Location**: `.context-kit/orchestration/audio-album-art/status/{agent-name}.json`

**Schema**:
```json
{
  "agent": "backend-api-agent",
  "wave": 1,
  "status": "in_progress",
  "progress": 0.75,
  "started_at": "2025-10-15T10:00:00Z",
  "updated_at": "2025-10-15T10:45:00Z",
  "estimated_completion": "2025-10-15T11:30:00Z",

  "deliverables": {
    "cover_endpoint": {
      "status": "complete",
      "verification": "curl http://localhost:8002/documents/test-doc/cover → 200 OK"
    },
    "metadata_extension": {
      "status": "in_progress",
      "blocker": null
    },
    "unit_tests": {
      "status": "pending",
      "blocker": null
    }
  },

  "integration_points": {
    "IC-001": {
      "status": "complete",
      "endpoint": "/documents/{doc_id}/cover",
      "example": "http://localhost:8002/documents/abc123/cover"
    },
    "IC-002": {
      "status": "in_progress",
      "fields_added": ["has_album_art"],
      "fields_pending": ["album_art_url"]
    }
  },

  "blockers": [],
  "issues": [
    {
      "severity": "low",
      "description": "MIME type detection could be more robust",
      "resolution": "Will use file extension as primary, magic bytes as fallback"
    }
  ],

  "tests": {
    "total": 7,
    "passing": 5,
    "failing": 0,
    "pending": 2
  }
}
```

### Status Values

| Status | Meaning | Next Action |
|--------|---------|-------------|
| `pending` | Not started | Wait for dependencies |
| `in_progress` | Actively working | Continue development |
| `blocked` | Cannot proceed | Resolve blocker |
| `complete` | Finished and validated | Hand off to consumers |
| `failed` | Unrecoverable error | Escalate to orchestrator |

---

## Update Frequency

### During Active Development

**Frequency**: Every 15-30 minutes OR on significant milestone

**Triggers**:
- Deliverable completed
- Integration contract ready
- Blocker encountered
- Test status changes
- Wave gate reached

### Status Update Script

```bash
#!/bin/bash
# update-status.sh

AGENT_NAME=$1
STATUS_FILE=".context-kit/orchestration/audio-album-art/status/${AGENT_NAME}.json"

# Update timestamp
jq '.updated_at = now | todate' "$STATUS_FILE" > tmp.$$.json && mv tmp.$$.json "$STATUS_FILE"

# Commit to git (optional - for tracking)
git add "$STATUS_FILE"
git commit -m "Update ${AGENT_NAME} status" --no-verify
```

---

## Integration Contract Handoff

### Contract Completion Notification

When an agent completes an integration contract, they must:

1. **Update Status File**:
```json
{
  "integration_points": {
    "IC-001": {
      "status": "complete",
      "endpoint": "/documents/{doc_id}/cover",
      "verified": true,
      "verification_commands": [
        "curl -I http://localhost:8002/documents/test-doc/cover",
        "pytest src/processing/test_audio_album_art.py::test_cover_endpoint_with_art"
      ]
    }
  }
}
```

2. **Create Handoff Document** (optional for complex contracts):
```markdown
# Integration Contract IC-001 Handoff

**From**: backend-api-agent
**To**: frontend-ui-agent, integration-test-agent
**Date**: 2025-10-15T11:00:00Z

## Contract Delivered

✅ IC-001: Album Art API Endpoint

## Verification

Endpoint: `GET /documents/{doc_id}/cover`

Test:
```bash
curl -I http://localhost:8002/documents/test-doc-001/cover
# HTTP/1.1 200 OK
# Content-Type: image/jpeg
```

## Implementation Notes

- Supports JPEG and PNG
- Returns 404 if no cover art
- Cache headers set to 1 year
- Security validation implemented

## Known Issues

None

## Consumer Actions

**frontend-ui-agent**: Can now use `/documents/{doc_id}/cover` in image src

**integration-test-agent**: Can test endpoint in integration suite
```

---

## Dependency Management

### Contract Dependency Graph

```
Wave 1 Agents:

backend-api-agent (IC-001, IC-002)
    │
    ├─────> frontend-ui-agent (IC-003)
    │         │
    │         └─────> integration-test-agent
    │
    └─────> integration-test-agent
```

### Waiting for Dependencies

If agent is blocked waiting for contract:

**Status Update**:
```json
{
  "status": "blocked",
  "blockers": [
    {
      "waiting_for": "IC-001",
      "provider": "backend-api-agent",
      "required_by": "frontend-ui-agent",
      "eta": "2025-10-15T11:30:00Z"
    }
  ]
}
```

**Action**: Agent can work on non-blocked tasks OR assist other agents

---

## Quality Gate Coordination

### Wave 1 → Wave 2 Transition

**Gate Criteria**: All Wave 1 agents must report `status: complete`

**Validation Process**:
1. Orchestrator polls all Wave 1 status files
2. Checks all agents are `complete`
3. Runs gate validation tests
4. If all pass → proceed to Wave 2
5. If any fail → notify responsible agent, return to Wave 1

**Status Check Script**:
```bash
#!/bin/bash
# check-wave1-complete.sh

AGENTS=("backend-api-agent" "frontend-ui-agent" "integration-test-agent")
ALL_COMPLETE=true

for agent in "${AGENTS[@]}"; do
  STATUS=$(jq -r '.status' ".context-kit/orchestration/audio-album-art/status/${agent}.json")

  if [ "$STATUS" != "complete" ]; then
    echo "❌ ${agent}: ${STATUS}"
    ALL_COMPLETE=false
  else
    echo "✅ ${agent}: complete"
  fi
done

if [ "$ALL_COMPLETE" = true ]; then
  echo "🎉 Wave 1 Complete - Proceeding to Wave 2"
  exit 0
else
  echo "⏳ Wave 1 Incomplete - Agents still working"
  exit 1
fi
```

---

## Issue Escalation

### Severity Levels

| Level | Response Time | Escalation |
|-------|---------------|------------|
| `low` | Best effort | Agent resolves independently |
| `medium` | Within 1 hour | Notify orchestrator if unresolved |
| `high` | Immediate | Notify all agents (may block others) |
| `critical` | Stop work | Escalate to orchestrator, all agents pause |

### Issue Format

```json
{
  "issues": [
    {
      "id": "issue-001",
      "severity": "medium",
      "title": "MIME type detection inconsistent",
      "description": "File extension says PNG but magic bytes say JPEG",
      "impact": "May serve incorrect Content-Type header",
      "reported_at": "2025-10-15T10:30:00Z",
      "reported_by": "backend-api-agent",
      "affects": ["frontend-ui-agent"],
      "resolution": "Use file extension as source of truth, validate on save",
      "resolved_at": "2025-10-15T10:45:00Z",
      "status": "resolved"
    }
  ]
}
```

---

## Cross-Agent Communication

### Direct Communication (Rare)

If an agent needs clarification from another agent:

**Method 1: Status File Question**:
```json
{
  "questions": [
    {
      "for": "backend-api-agent",
      "from": "frontend-ui-agent",
      "question": "Does album_art_url include host? (http://...) or just path (/documents/...)?",
      "asked_at": "2025-10-15T11:00:00Z",
      "answered": false
    }
  ]
}
```

**Method 2: Integration Contract Update**:
- Update contract markdown file with clarification
- Commit change
- Update status file to indicate change

**Method 3: Orchestrator Mediation** (for conflicts):
- Both agents report issue in status
- Orchestrator makes decision
- Orchestrator updates contract
- Agents proceed with clarified contract

---

## Progress Monitoring

### Orchestrator Dashboard

**Check Status**:
```bash
# Quick status check
for agent in backend-api frontend-ui integration-test; do
  echo "${agent}:"
  jq '{status, progress, blockers}' ".context-kit/orchestration/audio-album-art/status/${agent}-agent.json"
done
```

**Expected Output**:
```
backend-api-agent:
{
  "status": "in_progress",
  "progress": 0.75,
  "blockers": []
}

frontend-ui-agent:
{
  "status": "blocked",
  "progress": 0.0,
  "blockers": [
    {
      "waiting_for": "IC-001",
      "provider": "backend-api-agent"
    }
  ]
}

integration-test-agent:
{
  "status": "pending",
  "progress": 0.0,
  "blockers": []
}
```

---

## Automated Coordination

### CI/CD Integration

**Trigger**: On status file update

```yaml
# .github/workflows/orchestration-monitor.yml
name: Orchestration Monitor

on:
  push:
    paths:
      - '.context-kit/orchestration/audio-album-art/status/*.json'

jobs:
  check-status:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Check Wave 1 Status
        run: |
          bash scripts/check-wave1-complete.sh

      - name: Run Quality Gates
        if: success()
        run: |
          pytest src/processing/test_audio_album_art.py -v
```

---

## Success Criteria

### Coordination Effectiveness

**Metrics**:
- ✅ Zero merge conflicts (territorial boundaries working)
- ✅ < 15 minutes average dependency wait time
- ✅ All blockers resolved within 1 hour
- ✅ < 2 integration bugs (contract-driven development working)

**Monitoring**:
```bash
# Check for merge conflicts
git status | grep "both modified"
# Expected: none

# Check dependency wait times
jq '.blockers[].waiting_time' status/*.json | sort -n
# Expected: all < 1 hour

# Check integration bugs
grep -r "severity: high" status/*.json
# Expected: zero
```

---

## Emergency Procedures

### Wave Rollback

If Wave 1 fails quality gate:

1. **Identify** failing agent(s)
2. **Notify** all agents via status files
3. **Pause** Wave 2 work
4. **Fix** issues in Wave 1
5. **Re-validate** quality gates
6. **Resume** Wave 2 when gates pass

**Rollback Status**:
```json
{
  "wave": 1,
  "status": "rollback",
  "reason": "Quality gate 1.1 failed - backend API tests failing",
  "action_required": "Fix test_cover_endpoint_mime_types",
  "resumed_at": null
}
```

---

*Generated: 2025-10-15 | Orchestrator*
