# Coordination Protocol

**Orchestration**: markdown-audio-features
**Created**: 2025-10-11
**Purpose**: Define communication, status tracking, and coordination mechanisms for parallel agent execution

## Overview

This protocol ensures smooth coordination between 6 parallel agents working on markdown storage and audio processing features. Key principles:

1. **Transparent Communication**: All agents broadcast status and blockers
2. **Asynchronous Coordination**: Agents work independently, synchronize at wave gates
3. **Failure Isolation**: One agent's failure doesn't crash others
4. **Progressive Integration**: Continuous validation, not big-bang integration

---

## Communication Channels

### 1. Status Broadcasting

**Purpose**: Agents report progress, completion, and failures

**Location**: `.context-kit/orchestration/markdown-audio-features/status/`

**File Format**: `{agent-name}-status.json`

```json
{
  "agent": "compression-agent",
  "wave": 1,
  "status": "completed",  // pending | in_progress | completed | failed | blocked
  "timestamp": "2025-10-11T10:30:00Z",
  "progress_percent": 100,
  "deliverables": [
    {
      "file": "src/storage/compression.py",
      "status": "completed",
      "tests_passing": true,
      "coverage_percent": 95
    }
  ],
  "blockers": [],
  "dependencies_met": true,
  "ready_for_next_wave": true,
  "notes": "All compression tests passing, performance exceeds targets"
}
```

**Status Values**:
- `pending`: Not yet started
- `in_progress`: Actively working
- `completed`: All deliverables done, tests passing
- `failed`: Critical failure, cannot complete
- `blocked`: Waiting on dependencies or external factors

**Update Frequency**:
- On start: Set to `in_progress`
- Every major milestone: Update progress
- On completion: Set to `completed`
- On failure: Set to `failed` with details
- On blocker: Set to `blocked` with blocker details

---

### 2. Blocker Reporting

**Purpose**: Document issues blocking progress

**Location**: `.context-kit/orchestration/markdown-audio-features/blockers/`

**File Format**: `{agent-name}-{blocker-id}.md`

**Template**:
```markdown
# Blocker: {Short Description}

**Agent**: compression-agent
**Blocker ID**: B001
**Severity**: critical | high | medium | low
**Created**: 2025-10-11T10:30:00Z
**Status**: open | resolved

## Problem Description

Clear description of what is blocking progress.

## Impact

- Which deliverables are blocked
- Which dependent agents are affected
- Estimated delay if not resolved

## Attempted Solutions

1. What was tried
2. Why it didn't work

## Requested Help

What is needed to unblock (resources, clarification, dependency completion)

## Resolution (when resolved)

How the blocker was resolved and when.
```

**Severity Levels**:
- **critical**: Blocks entire agent, cannot proceed
- **high**: Blocks major deliverable, workaround possible
- **medium**: Delays progress, but can work on other tasks
- **low**: Minor issue, doesn't block progress

---

### 3. Question & Answer

**Purpose**: Ask questions about contracts, requirements, or coordination

**Location**: `.context-kit/orchestration/markdown-audio-features/questions/`

**File Format**: `{agent-name}-{question-id}.md`

**Template**:
```markdown
# Question: {Short Summary}

**Agent**: parser-markdown-agent
**Question ID**: Q001
**Priority**: urgent | normal | low
**Created**: 2025-10-11T10:30:00Z
**Status**: open | answered

## Question

Clear question text here.

## Context

Why this question matters, what depends on the answer.

## Possible Answers

If you have ideas, list them here.

## Answer (when answered)

**Answered by**: storage-markdown-agent
**Date**: 2025-10-11T11:00:00Z

Answer text here with rationale.
```

---

### 4. Code Review Requests

**Purpose**: Request review of integration points

**Location**: `.context-kit/orchestration/markdown-audio-features/reviews/`

**File Format**: `{reviewer-agent}-reviews-{provider-agent}.md`

**Template**:
```markdown
# Code Review: {provider-agent} → {reviewer-agent}

**Provider**: compression-agent
**Reviewer**: storage-markdown-agent
**Wave**: 1
**Date**: 2025-10-11T12:00:00Z
**Status**: requested | in_progress | approved | changes_requested

## Files Under Review

- `src/storage/compression.py`

## Interface Contract

Reference to integration contract being validated:
`integration-contracts/01-compression-interface.md`

## Review Checklist

- [ ] Interface contract followed exactly
- [ ] All required methods implemented
- [ ] Error handling matches specification
- [ ] Performance targets met
- [ ] Tests are comprehensive
- [ ] Documentation complete

## Comments

### Positive Feedback

What was done well.

### Requested Changes

1. Issue description
   - File/line reference
   - Why it matters
   - Suggested fix

### Questions

Any clarifications needed.

## Approval (when approved)

**Status**: approved | changes_requested
**Date**: 2025-10-11T13:00:00Z
**Notes**: Changes implemented, ready for integration
```

---

## Wave Synchronization Protocol

### Wave Gate Process

At the end of each wave, before proceeding to the next:

1. **Status Check** (automated):
   ```bash
   # Check all agents in current wave
   python scripts/check-wave-status.py --wave 1

   # Output:
   # compression-agent: ✓ completed
   # config-asr-agent: ✓ completed
   # All agents ready: YES
   ```

2. **Validation Gate Check**:
   - Review validation checklist (see `validation-strategy.md`)
   - Run integration tests for completed wave
   - Verify all deliverables present

3. **Dependency Propagation**:
   - Notify dependent agents that their dependencies are ready
   - Update status files with `dependencies_met: true`

4. **Wave Transition**:
   - Update orchestration status: `wave_1_complete: true`
   - Green-light Wave 2 agents to start
   - Archive Wave 1 status as `status/archive/wave-1/`

---

### Coordination Scripts

#### check-wave-status.py

```python
#!/usr/bin/env python
"""Check if all agents in a wave are ready to proceed."""

import json
import sys
from pathlib import Path

def check_wave_status(wave_num):
    """Check status of all agents in specified wave."""
    status_dir = Path(".context-kit/orchestration/markdown-audio-features/status")

    # Define agents per wave
    wave_agents = {
        1: ["compression-agent", "config-asr-agent"],
        2: ["parser-markdown-agent", "parser-asr-agent"],
        3: ["storage-markdown-agent", "testing-integration-agent"],
    }

    agents = wave_agents.get(wave_num, [])
    if not agents:
        print(f"ERROR: Invalid wave number {wave_num}")
        return False

    all_ready = True
    for agent in agents:
        status_file = status_dir / f"{agent}-status.json"

        if not status_file.exists():
            print(f"✗ {agent}: status file not found")
            all_ready = False
            continue

        with open(status_file) as f:
            status = json.load(f)

        if status["status"] == "completed":
            print(f"✓ {agent}: completed ({status.get('notes', '')})")
        elif status["status"] == "failed":
            print(f"✗ {agent}: FAILED - {status.get('notes', '')}")
            all_ready = False
        elif status["status"] == "blocked":
            print(f"⚠ {agent}: BLOCKED - {status.get('notes', '')}")
            all_ready = False
        else:
            print(f"⏳ {agent}: {status['status']} ({status.get('progress_percent', 0)}%)")
            all_ready = False

    print()
    if all_ready:
        print(f"✓ Wave {wave_num} COMPLETE - Ready to proceed")
        return True
    else:
        print(f"✗ Wave {wave_num} NOT COMPLETE - Waiting for agents")
        return False

if __name__ == "__main__":
    wave = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    success = check_wave_status(wave)
    sys.exit(0 if success else 1)
```

#### update-agent-status.py

```python
#!/usr/bin/env python
"""Helper to update agent status."""

import json
import sys
from datetime import datetime
from pathlib import Path

def update_status(agent_name, status, notes="", progress=0):
    """Update agent status file."""
    status_dir = Path(".context-kit/orchestration/markdown-audio-features/status")
    status_dir.mkdir(parents=True, exist_ok=True)

    status_file = status_dir / f"{agent_name}-status.json"

    # Load existing status if present
    if status_file.exists():
        with open(status_file) as f:
            data = json.load(f)
    else:
        data = {
            "agent": agent_name,
            "wave": 1,
            "deliverables": [],
            "blockers": []
        }

    # Update fields
    data["status"] = status
    data["timestamp"] = datetime.utcnow().isoformat() + "Z"
    data["progress_percent"] = progress
    if notes:
        data["notes"] = notes

    # Write back
    with open(status_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Updated {agent_name} status: {status}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: update-agent-status.py <agent-name> <status> [notes] [progress]")
        sys.exit(1)

    agent = sys.argv[1]
    status = sys.argv[2]
    notes = sys.argv[3] if len(sys.argv) > 3 else ""
    progress = int(sys.argv[4]) if len(sys.argv) > 4 else 0

    update_status(agent, status, notes, progress)
```

---

## Dependency Management

### Dependency Graph

```
Wave 1 (Foundation):
  compression-agent ─────┐
                         ├──> Wave 2 (Parser)
  config-asr-agent ──────┘

Wave 2 (Parser):
  parser-markdown-agent ──> Wave 3 (Storage)
  parser-asr-agent ────────> Wave 3 (existing pipeline, no changes)

Wave 3 (Storage & Testing):
  storage-markdown-agent ──> Wave 4 (Integration)
  testing-integration-agent ─> Wave 4 (Integration)
```

### Dependency Checking

Before starting work, agents must verify dependencies:

```python
# Example for storage-markdown-agent (Wave 3)
def check_dependencies():
    """Verify dependencies are met before starting."""
    required_agents = ["compression-agent", "parser-markdown-agent"]
    status_dir = Path(".context-kit/orchestration/markdown-audio-features/status")

    for agent in required_agents:
        status_file = status_dir / f"{agent}-status.json"
        if not status_file.exists():
            raise DependencyError(f"{agent} status not found")

        with open(status_file) as f:
            status = json.load(f)

        if status["status"] != "completed":
            raise DependencyError(f"{agent} not completed (status: {status['status']})")

    print("✓ All dependencies met, ready to proceed")
```

---

## Conflict Resolution

### Territorial Conflicts

If two agents accidentally edit the same file region:

1. **Detect conflict**:
   - Git merge conflict
   - Manual code review
   - Automated tooling

2. **Identify owner**:
   - Check `agent-assignments.md` for territory
   - Agent with earlier wave has priority
   - Agent on critical path has priority (if same wave)

3. **Resolve**:
   - Non-owner reverts their changes
   - Non-owner coordinates with owner for alternative approach
   - Update territory definitions if needed

4. **Prevent recurrence**:
   - Clarify boundaries in agent-assignments.md
   - Add automated territorial checks
   - Better coordination protocol

### Interface Contract Disputes

If there's disagreement about interface contract:

1. **Document dispute**:
   - Create issue in `questions/contract-dispute-{id}.md`
   - Both agents provide their interpretation
   - Reference original contract

2. **Orchestrator decision**:
   - Review both interpretations
   - Consult original requirements
   - Make binding decision
   - Update contract if needed

3. **Propagate decision**:
   - Notify all affected agents
   - Update integration contract
   - Agents adjust implementation

---

## Handoff Protocol

When one agent's work becomes input to another:

### 1. Completion Notification

**Provider agent**:
```bash
# Update status
python scripts/update-agent-status.py compression-agent completed \
  "compress_markdown() and decompress_markdown() ready" 100

# Notify consumers (via shared status file)
```

### 2. Validation by Consumer

**Consumer agent** (storage-markdown-agent):
```python
# Validate provider's deliverables
from src.storage.compression import compress_markdown, decompress_markdown

# Quick smoke test
test_data = "# Test\n\nContent"
compressed = compress_markdown(test_data)
decompressed = decompress_markdown(compressed)
assert decompressed == test_data

print("✓ compression-agent deliverables validated")
```

### 3. Integration

**Consumer agent**:
- Import provider's interface
- Use according to contract
- Report any contract violations as questions or blockers

### 4. Feedback

**Consumer agent** → **Provider agent**:
- Code review feedback (via reviews/)
- Bug reports (via blockers/)
- Questions (via questions/)

---

## Progress Monitoring

### Dashboard (Conceptual)

```
┌─────────────────────────────────────────────────────────────┐
│ Markdown-Audio Features Orchestration Dashboard            │
│ Wave 1 (Foundation Layer) - COMPLETE ✓                     │
├─────────────────────────────────────────────────────────────┤
│ Agent                 Status      Progress  Tests  Coverage│
│ compression-agent     ✓ completed   100%    15/15   95%   │
│ config-asr-agent      ✓ completed   100%    10/10   92%   │
├─────────────────────────────────────────────────────────────┤
│ Wave 2 (Parser Layer) - IN PROGRESS                        │
├─────────────────────────────────────────────────────────────┤
│ Agent                 Status      Progress  Tests  Coverage│
│ parser-markdown-agent ⏳ in_progress 70%     5/8     80%   │
│ parser-asr-agent      ⏳ in_progress 60%     4/9     75%   │
├─────────────────────────────────────────────────────────────┤
│ Blockers: 0 | Questions: 1 | Reviews: 2 pending           │
└─────────────────────────────────────────────────────────────┘
```

### Metrics Tracked

Per agent:
- Status (pending, in_progress, completed, failed, blocked)
- Progress percentage
- Test pass rate
- Code coverage
- Deliverables status

Per wave:
- Overall completion percentage
- Estimated time remaining
- Blocker count
- Critical path status

Overall:
- Total progress (all waves)
- Time elapsed
- Time remaining estimate
- Risk level (green, yellow, red)

---

## Risk Communication

### Risk Levels

**Green** (Low Risk):
- All agents on track
- No blockers
- Tests passing
- Performance meeting targets

**Yellow** (Medium Risk):
- 1-2 agents slightly behind
- Non-critical blockers
- Some tests failing (non-critical)
- Performance 10-20% below target

**Red** (High Risk):
- Multiple agents blocked
- Critical blockers unresolved
- Critical tests failing
- Performance >50% below target
- Risk of missing wave deadline

### Risk Escalation

When risk level increases:

1. **Yellow Alert**:
   - Update status files with warnings
   - Assess if help needed
   - Consider simplifying requirements
   - Increase communication frequency

2. **Red Alert**:
   - Halt dependent work
   - Convene coordination meeting
   - Reassess priorities
   - Consider fallback options:
     - Defer non-critical features
     - Simplify implementation
     - Extend timeline
     - Rollback wave

---

## Daily Standup (Async)

Each agent posts daily update in status file:

**Template**:
```json
{
  "agent": "parser-asr-agent",
  "date": "2025-10-11",
  "yesterday": [
    "Implemented ASR pipeline configuration",
    "Added audio metadata extraction",
    "Fixed import issues"
  ],
  "today": [
    "Write unit tests for MP3 processing",
    "Write unit tests for WAV processing",
    "Performance testing"
  ],
  "blockers": [
    "Waiting for sample_10s.mp3 test file"
  ],
  "help_needed": false
}
```

---

## Communication Best Practices

### For All Agents

1. **Update status frequently**: At least daily, more if significant changes
2. **Be specific in notes**: "Implemented compress_markdown()" not "Made progress"
3. **Report blockers immediately**: Don't wait, others may be able to help
4. **Ask questions early**: Better to clarify than implement wrong
5. **Review dependencies' code**: Validate interfaces before integrating

### For Provider Agents

1. **Document breaking changes**: If interface changes, notify consumers
2. **Provide examples**: Show how to use your interface
3. **Test thoroughly**: Don't make consumers debug your code
4. **Version interfaces**: If significant change, consider new version

### For Consumer Agents

1. **Validate dependencies first**: Don't assume, test the interface
2. **Report issues clearly**: Reproducible examples, error messages
3. **Suggest fixes**: If you see a problem, propose a solution
4. **Give feedback**: Let providers know what works well

---

## Emergency Procedures

### Agent Failure

If an agent fails critically:

1. **Assess impact**:
   - Which features are affected?
   - Which agents are blocked?
   - Can we proceed without this agent?

2. **Options**:
   - **Fix immediately**: If quick fix (<1 hour)
   - **Reassign work**: To another agent or orchestrator
   - **Simplify requirement**: Minimal viable version
   - **Defer feature**: Move to future iteration
   - **Rollback wave**: Revert and reassess

3. **Communicate decision**:
   - Update all affected agents
   - Document in coordination-protocol.md
   - Update orchestration-plan.md if needed

### Integration Failure

If integration between agents fails:

1. **Isolate issue**:
   - Which interface is broken?
   - Provider or consumer problem?
   - Contract ambiguity?

2. **Debug collaboratively**:
   - Provider and consumer work together
   - Review integration contract
   - Create reproducible test case

3. **Fix and validate**:
   - Implement fix
   - Add integration test
   - Validate fix with both agents
   - Document lesson learned

---

## Success Metrics

Track these metrics throughout orchestration:

### Efficiency Metrics
- **Parallel efficiency**: Actual time / Sequential time
- **Wave completion rate**: Waves completed on schedule
- **Blocker resolution time**: Average time to resolve blockers

### Quality Metrics
- **Test pass rate**: % of tests passing
- **Code coverage**: % of new code covered
- **Integration success rate**: % of interfaces that work on first integration

### Coordination Metrics
- **Status update frequency**: Updates per agent per day
- **Question response time**: Average time to answer questions
- **Code review turnaround**: Time from request to approval

---

## Tools & Automation

### Recommended Tools

1. **Status tracking**: JSON files + Python scripts (provided above)
2. **Code review**: Git/GitHub pull request workflow
3. **Testing**: pytest with coverage reporting
4. **Monitoring**: Watch scripts for status changes
5. **Notifications**: Optional Slack/Discord integration for status updates

### Automation Opportunities

- Auto-update status from test results
- Auto-check wave completion criteria
- Auto-generate progress dashboard
- Auto-notify dependent agents when dependencies complete
- Auto-archive completed waves

---

## Conclusion

Effective coordination is key to successful parallel agent orchestration. This protocol provides:

- **Clear communication channels** (status, blockers, questions, reviews)
- **Synchronization points** (wave gates)
- **Dependency management** (graph, checking, handoffs)
- **Conflict resolution** (territorial, interface disputes)
- **Risk management** (levels, escalation, emergency procedures)

By following this protocol, the 6 agents can work independently while maintaining alignment and achieving successful integration.

---

*Generated as part of markdown-audio-features orchestration plan on 2025-10-11*
