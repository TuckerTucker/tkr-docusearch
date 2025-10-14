# Coordination Protocol

**Purpose**: Define communication, synchronization, and failure handling procedures for parallel agent execution

---

## Overview

This protocol ensures **zero-conflict parallel execution** through:
1. Clear status broadcasting
2. Dependency verification
3. Synchronization gates
4. Failure isolation and recovery

---

## Status Management

### Status File Format

Each agent publishes status to:
```
.context-kit/orchestration/tech-debt-resolution/status/{agent-name}.yml
```

**Schema**:
```yaml
agent: validation-core-agent      # Agent identifier
wave: 1                           # Wave number
status: complete                  # queued | in_progress | complete | failed
started: 2025-10-13T22:00:00Z    # ISO 8601 timestamp
completed: 2025-10-13T23:30:00Z  # ISO 8601 timestamp (null if not complete)
duration_minutes: 90              # Actual duration

deliverables:
  - path: src/processing/file_validator.py
    status: complete              # complete | failed | skipped
    lines_added: 120
    tests_added: 15
    coverage: 98%

  - path: integration-contracts/file-validator-api.md
    status: complete
    validation: passed

contracts_published:
  - file-validator-api.md

tests_passing: true               # Boolean
integration_validated: true       # Boolean

notes: |
  All tests pass with 98% coverage.
  API contract published and validated.
  Ready for Wave 2 integration.

blockers: []                      # List of blocking issues
dependencies_met: true            # All prerequisites satisfied

# Agent-specific metrics
metrics:
  test_count: 15
  coverage_percent: 98
  lint_warnings: 0
  type_check_errors: 0
```

---

### Status Lifecycle

```
┌─────────┐
│ queued  │  ← Agent assigned, waiting for wave
└────┬────┘
     │
     ▼
┌────────────┐
│ in_progress│  ← Agent actively working
└────┬───────┘
     │
     ├──────────┐
     ▼          ▼
┌─────────┐ ┌─────────┐
│complete │ │ failed  │
└─────────┘ └─────────┘
```

---

## Pre-Flight Checks

Before starting, each agent MUST verify:

### 1. Wave Dependencies
```bash
#!/bin/bash
# check_wave_dependencies.sh

WAVE=$1
REQUIRED_AGENTS=$2  # Comma-separated list

echo "Checking Wave $WAVE dependencies..."

for agent in $(echo $REQUIRED_AGENTS | tr ',' ' '); do
  STATUS_FILE=".context-kit/orchestration/tech-debt-resolution/status/${agent}.yml"

  if [ ! -f "$STATUS_FILE" ]; then
    echo "❌ BLOCKED: $agent has not started"
    exit 1
  fi

  STATUS=$(yq '.status' "$STATUS_FILE")

  if [ "$STATUS" != "complete" ]; then
    echo "❌ BLOCKED: $agent status is $STATUS (expected: complete)"
    exit 1
  fi

  echo "✅ $agent complete"
done

echo "✅ All Wave $WAVE dependencies satisfied"
```

**Usage**:
```bash
# Wave 2 agents check Wave 1 completion
./check_wave_dependencies.sh 1 "validation-core-agent,worker-analysis-agent,config-analysis-agent"
```

---

### 2. Contract Availability
```bash
#!/bin/bash
# check_contracts.sh

REQUIRED_CONTRACTS=$1  # Space-separated list

echo "Checking required contracts..."

for contract in $REQUIRED_CONTRACTS; do
  CONTRACT_PATH=".context-kit/orchestration/tech-debt-resolution/integration-contracts/${contract}"

  if [ ! -f "$CONTRACT_PATH" ]; then
    echo "❌ BLOCKED: Contract $contract missing"
    exit 1
  fi

  echo "✅ Contract $contract available"
done

echo "✅ All required contracts available"
```

**Usage**:
```bash
# Wave 2 webhook-refactor agent checks contracts
./check_contracts.sh "file-validator-api.md worker-integration-spec.md"
```

---

### 3. Test Prerequisites
```bash
#!/bin/bash
# check_test_prerequisites.sh

MODULE=$1

echo "Checking test prerequisites for $MODULE..."

# Check if module exists
if [ ! -f "$MODULE" ]; then
  echo "❌ BLOCKED: Module $MODULE not found"
  exit 1
fi

# Run module tests
pytest "$MODULE" -v --tb=short

if [ $? -ne 0 ]; then
  echo "❌ BLOCKED: Tests failing for $MODULE"
  exit 1
fi

echo "✅ Test prerequisites satisfied for $MODULE"
```

**Usage**:
```bash
# Wave 2 agents check Wave 1 module works
./check_test_prerequisites.sh "src/processing/file_validator.py"
```

---

## Wave Synchronization Gates

### Gate Structure

Each wave has a synchronization gate that must pass before next wave starts:

```yaml
wave_gate:
  wave_number: 1
  required_agents:
    - validation-core-agent
    - worker-analysis-agent
    - config-analysis-agent

  pass_criteria:
    - all_agents_complete: true
    - all_tests_passing: true
    - all_contracts_published: true
    - no_blockers: true

  validation_tests:
    - pytest src/processing/test_file_validator.py -v
    - test -f integration-contracts/file-validator-api.md
    - test -f integration-contracts/worker-integration-spec.md
    - test -f integration-contracts/config-integration-spec.md

  on_pass:
    action: proceed_to_wave_2
    notify: all_wave_2_agents

  on_fail:
    action: block_wave_2
    notify: failed_agents
    require: fix_and_revalidate
```

---

### Gate Validation Script

```bash
#!/bin/bash
# validate_wave_gate.sh

WAVE=$1

echo "==================================="
echo "Validating Wave $WAVE Gate"
echo "==================================="

# Load gate configuration
GATE_CONFIG=".context-kit/orchestration/tech-debt-resolution/gates/wave${WAVE}.yml"

if [ ! -f "$GATE_CONFIG" ]; then
  echo "❌ FAIL: Gate configuration missing for Wave $WAVE"
  exit 1
fi

# Check all agents complete
echo ""
echo "1. Checking agent completion..."
REQUIRED_AGENTS=$(yq '.required_agents[]' "$GATE_CONFIG")

for agent in $REQUIRED_AGENTS; do
  STATUS_FILE=".context-kit/orchestration/tech-debt-resolution/status/${agent}.yml"
  STATUS=$(yq '.status' "$STATUS_FILE")

  if [ "$STATUS" != "complete" ]; then
    echo "❌ FAIL: $agent not complete (status: $STATUS)"
    exit 1
  fi

  echo "  ✅ $agent complete"
done

# Check tests passing
echo ""
echo "2. Checking tests..."
TESTS=$(yq '.validation_tests[]' "$GATE_CONFIG")

for test_cmd in $TESTS; do
  echo "  Running: $test_cmd"
  eval $test_cmd

  if [ $? -ne 0 ]; then
    echo "❌ FAIL: Test failed: $test_cmd"
    exit 1
  fi

  echo "  ✅ Test passed"
done

# Check contracts published
echo ""
echo "3. Checking contracts..."
# (similar logic)

# Check no blockers
echo ""
echo "4. Checking for blockers..."
for agent in $REQUIRED_AGENTS; do
  STATUS_FILE=".context-kit/orchestration/tech-debt-resolution/status/${agent}.yml"
  BLOCKERS=$(yq '.blockers | length' "$STATUS_FILE")

  if [ "$BLOCKERS" -gt 0 ]; then
    echo "❌ FAIL: $agent has blockers"
    yq '.blockers' "$STATUS_FILE"
    exit 1
  fi
done

echo ""
echo "==================================="
echo "✅ Wave $WAVE Gate PASSED"
echo "==================================="
echo ""
echo "Ready to proceed to Wave $((WAVE + 1))"
```

**Usage**:
```bash
# Validate Wave 1 gate before starting Wave 2
./validate_wave_gate.sh 1

# If passes, proceed with Wave 2
# If fails, agents must fix issues and revalidate
```

---

## Agent Communication

### Status Broadcasting

Agents broadcast status changes:

```python
# agent_communication.py

import yaml
from datetime import datetime
from pathlib import Path

class AgentCommunicator:
    def __init__(self, agent_name: str, wave: int):
        self.agent_name = agent_name
        self.wave = wave
        self.status_file = Path(
            f".context-kit/orchestration/tech-debt-resolution/status/{agent_name}.yml"
        )

    def update_status(self, status: str, **kwargs):
        """Update agent status file"""
        data = {
            "agent": self.agent_name,
            "wave": self.wave,
            "status": status,
            "updated": datetime.utcnow().isoformat() + "Z",
            **kwargs
        }

        with open(self.status_file, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)

        print(f"📢 [{self.agent_name}] Status updated: {status}")

    def publish_contract(self, contract_name: str, content: str):
        """Publish integration contract"""
        contract_path = Path(
            f".context-kit/orchestration/tech-debt-resolution/integration-contracts/{contract_name}"
        )

        with open(contract_path, 'w') as f:
            f.write(content)

        print(f"📝 [{self.agent_name}] Contract published: {contract_name}")

    def check_dependencies(self, required_agents: list) -> bool:
        """Check if all required agents are complete"""
        for agent in required_agents:
            status_file = Path(
                f".context-kit/orchestration/tech-debt-resolution/status/{agent}.yml"
            )

            if not status_file.exists():
                print(f"❌ BLOCKED: {agent} has not started")
                return False

            with open(status_file) as f:
                status_data = yaml.safe_load(f)

            if status_data.get('status') != 'complete':
                print(f"❌ BLOCKED: {agent} status is {status_data.get('status')}")
                return False

        print("✅ All dependencies satisfied")
        return True

# Usage example
comm = AgentCommunicator("validation-core-agent", wave=1)

comm.update_status("in_progress", started=datetime.utcnow().isoformat())

# ... do work ...

comm.publish_contract("file-validator-api.md", api_docs)

comm.update_status(
    "complete",
    completed=datetime.utcnow().isoformat(),
    deliverables=[
        {"path": "src/processing/file_validator.py", "status": "complete"},
        {"path": "integration-contracts/file-validator-api.md", "status": "complete"}
    ],
    tests_passing=True
)
```

---

### Contract Publishing

Contracts must be published in standardized format:

**Template**: `integration-contracts/{contract-name}.md`

```markdown
# {Contract Name}

**Provider**: {agent-name}
**Consumers**: {list-of-consumer-agents}
**Wave**: {wave-number}
**Status**: {draft | published | validated}

## Overview
Brief description of what this contract defines

## API Specification

### Functions
```python
def function_name(param: Type) -> ReturnType:
    """Function description"""
```

### Constants
```python
CONSTANT_NAME: Type = value
```

## Usage Examples

```python
# Example 1: Basic usage
from module import function_name
result = function_name(value)
```

## Error Handling

| Error Type | Condition | Response |
|------------|-----------|----------|
| ValueError | Invalid input | (False, "error message") |

## Integration Points

### Call Sites
| Location | Current Code | Replacement |
|----------|-------------|-------------|
| file.py:123 | old code | new code |

## Validation

- [ ] API signatures match specification
- [ ] Error formats preserved
- [ ] All integration points documented
- [ ] Usage examples tested

## Change Log
- 2025-10-13: Initial specification
```

---

## Failure Handling

### Failure Detection

Agents report failures in status:

```yaml
agent: webhook-worker-refactor-agent
wave: 2
status: failed
started: 2025-10-13T23:00:00Z
failed: 2025-10-13T23:45:00Z

deliverables:
  - path: src/processing/worker_webhook.py
    status: failed
    error: "Import error: cannot import get_supported_extensions"

blockers:
  - type: import_error
    description: "file_validator module not found"
    resolution: "Ensure Wave 1 validation-core-agent completed successfully"

error_log: |
  Traceback (most recent call last):
    File "src/processing/worker_webhook.py", line 73
      from .file_validator import get_supported_extensions
  ImportError: cannot import name 'get_supported_extensions'
```

---

### Failure Response Protocol

```
Failure Detected
     ↓
┌────────────────────────────┐
│ 1. Agent updates status    │
│    to "failed" with details│
└────────────┬───────────────┘
             ↓
┌────────────────────────────┐
│ 2. Block dependent agents  │
│    (via gate validation)   │
└────────────┬───────────────┘
             ↓
┌────────────────────────────┐
│ 3. Notify team/orchestrator│
└────────────┬───────────────┘
             ↓
┌────────────────────────────┐
│ 4. Analyze failure cause   │
│    - Dependency issue?     │
│    - Code error?           │
│    - Integration mismatch? │
└────────────┬───────────────┘
             ↓
┌────────────────────────────┐
│ 5. Fix root cause          │
└────────────┬───────────────┘
             ↓
┌────────────────────────────┐
│ 6. Reset status to queued  │
└────────────┬───────────────┘
             ↓
┌────────────────────────────┐
│ 7. Retry execution         │
└────────────────────────────┘
```

---

### Rollback Procedures

If agent fails and can't be fixed quickly:

```bash
#!/bin/bash
# rollback_wave.sh

WAVE=$1

echo "Rolling back Wave $WAVE..."

# Get list of agents in wave
AGENTS=$(yq ".waves[] | select(.wave==$WAVE) | .agents[]" orchestration-plan.yml)

for agent in $AGENTS; do
  echo "Rolling back $agent..."

  # Get deliverables from status
  DELIVERABLES=$(yq ".deliverables[].path" status/${agent}.yml)

  for file in $DELIVERABLES; do
    if [ -f "$file" ]; then
      # Check if file is new or modified
      if git ls-files --error-unmatch "$file" 2>/dev/null; then
        # File exists in git, revert changes
        git checkout HEAD -- "$file"
        echo "  Reverted: $file"
      else
        # File is new, remove it
        rm "$file"
        echo "  Removed: $file"
      fi
    fi
  done

  # Update status to rolled back
  yq -i '.status = "rolled_back"' status/${agent}.yml
done

echo "Wave $WAVE rolled back successfully"
echo "System returned to pre-Wave-$WAVE state"
```

---

## Progress Monitoring

### Real-Time Dashboard

```bash
#!/bin/bash
# monitor_progress.sh

while true; do
  clear
  echo "====================================="
  echo "Technical Debt Resolution Progress"
  echo "====================================="
  echo ""

  for wave in 1 2 3 4; do
    echo "Wave $wave:"

    STATUS_FILES=(.context-kit/orchestration/tech-debt-resolution/status/*)

    for status_file in "${STATUS_FILES[@]}"; do
      AGENT_WAVE=$(yq '.wave' "$status_file")

      if [ "$AGENT_WAVE" -eq "$wave" ]; then
        AGENT=$(yq '.agent' "$status_file")
        STATUS=$(yq '.status' "$status_file")

        case $STATUS in
          complete)
            echo "  ✅ $AGENT"
            ;;
          in_progress)
            echo "  🔄 $AGENT"
            ;;
          failed)
            echo "  ❌ $AGENT"
            ;;
          queued)
            echo "  ⏳ $AGENT"
            ;;
        esac
      fi
    done

    echo ""
  done

  echo "====================================="
  sleep 5
done
```

---

### Progress Metrics

Track overall progress:

```python
# progress_tracker.py

from pathlib import Path
import yaml

def calculate_progress():
    status_dir = Path(".context-kit/orchestration/tech-debt-resolution/status")

    total_agents = 0
    completed_agents = 0
    failed_agents = 0
    in_progress_agents = 0

    for status_file in status_dir.glob("*.yml"):
        total_agents += 1

        with open(status_file) as f:
            data = yaml.safe_load(f)

        status = data.get('status')

        if status == 'complete':
            completed_agents += 1
        elif status == 'failed':
            failed_agents += 1
        elif status == 'in_progress':
            in_progress_agents += 1

    progress_percent = (completed_agents / total_agents * 100) if total_agents > 0 else 0

    return {
        "total": total_agents,
        "completed": completed_agents,
        "failed": failed_agents,
        "in_progress": in_progress_agents,
        "progress_percent": progress_percent
    }

if __name__ == "__main__":
    metrics = calculate_progress()
    print(f"Progress: {metrics['progress_percent']:.1f}%")
    print(f"Completed: {metrics['completed']}/{metrics['total']}")
    print(f"In Progress: {metrics['in_progress']}")
    print(f"Failed: {metrics['failed']}")
```

---

## Conflict Resolution

Despite territorial boundaries, if conflicts occur:

### Detection
```bash
# detect_conflicts.sh

git status --porcelain | grep "^UU" && echo "❌ Merge conflicts detected!"
```

### Resolution Protocol

1. **Identify Conflicting Agents**
   ```bash
   # Find which agents modified conflicting files
   git log --all --oneline -- path/to/conflicting/file
   ```

2. **Priority Rules**
   - Earlier wave has priority
   - Within same wave, lower agent ID has priority

3. **Resolution Steps**
   - Higher priority agent continues
   - Lower priority agent rolls back
   - Lower priority agent waits for higher to complete
   - Lower priority agent rebases and retries

4. **Prevention**
   - Review territorial boundaries
   - Update orchestration plan to prevent recurrence

---

## Summary

### Key Protocols

1. **Status Management**: All agents publish YAML status files
2. **Pre-Flight Checks**: Verify dependencies before starting
3. **Wave Gates**: Synchronization points between waves
4. **Contract Publishing**: Standardized integration specs
5. **Failure Handling**: Detect, report, fix, retry
6. **Progress Monitoring**: Real-time dashboard and metrics
7. **Conflict Resolution**: Priority-based resolution protocol

### Success Criteria

- ✅ All agents publish status
- ✅ All contracts published on time
- ✅ All wave gates pass
- ✅ Zero unresolved conflicts
- ✅ Clear failure recovery
- ✅ Complete audit trail

This protocol ensures **guaranteed integration** through specification-driven coordination!
