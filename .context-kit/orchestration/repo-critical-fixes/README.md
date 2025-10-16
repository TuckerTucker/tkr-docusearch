# Repository Critical Fixes - Orchestration Plan

**Status:** Ready to Execute
**Created:** 2025-10-16
**Goal:** Increase repository health from 76/100 to 88+/100
**Strategy:** 4-wave parallel agent execution

---

## Quick Start

### For Orchestrator

1. **Review the plan:**
   ```bash
   cat orchestration-plan.md
   ```

2. **Launch Wave 1 agents:**
   ```bash
   # Trigger 4 agents in parallel
   # - security-fixer-agent
   # - test-infrastructure-agent
   # - automation-agent
   # - accessibility-agent
   ```

3. **Monitor progress:**
   ```bash
   # Check agent statuses
   ls status/*.json | xargs -I {} jq -r '"\(.agent): \(.status)"' {}

   # View overall progress
   cat progress.json | jq '.overall_progress_percentage'

   # Check for blockers
   cat blockers.md
   ```

4. **Validate wave gate:**
   ```bash
   # Run gate validation tests
   bash ../../../scripts/validate-wave-1-gate.sh

   # Review results and authorize next wave
   ```

### For Individual Agents

1. **Read your assignment:**
   ```bash
   # Find your section in agent-assignments.md
   grep -A 50 "Agent.*{your-agent-name}" agent-assignments.md
   ```

2. **Review integration contracts:**
   ```bash
   # Read contracts you provide or consume
   ls integration-contracts/*.md
   ```

3. **Start work and update status:**
   ```python
   # Update your status JSON regularly
   {
     "agent": "your-agent-name",
     "wave": 1,
     "status": "in_progress",
     ...
   }
   ```

4. **Run validation tests:**
   ```bash
   # Follow validation-strategy.md
   pytest tests/ -v
   ```

5. **Document handoff:**
   ```bash
   # When complete, update handoffs.md
   echo "## Handoff: your-agent → next-agent" >> handoffs.md
   ```

---

## File Structure

```
.context-kit/orchestration/repo-critical-fixes/
├── README.md                       # This file - Quick start guide
├── orchestration-plan.md           # Complete 4-wave execution plan
├── agent-assignments.md            # Territorial ownership & responsibilities
├── validation-strategy.md          # Testing & quality assurance approach
├── coordination-protocol.md        # Communication & status management
├── integration-contracts/          # Contract specifications
│   ├── README.md                   # Contract usage guide
│   ├── docling-parser-refactor-contract.md  # Example contract
│   └── ...                         # Additional contracts
├── status/                         # Agent status files (runtime)
├── gates/                          # Wave gate reports (runtime)
├── handoffs.md                     # Integration handoffs (runtime)
├── daily-status.md                 # Daily standup updates (runtime)
├── blockers.md                     # Active blockers (runtime)
├── coordination.md                 # Cross-agent communication (runtime)
└── progress.json                   # Overall progress tracking (runtime)
```

---

## Overview

### Problem Statement

Repository review identified critical issues:
- **Security:** 1 Critical, 3 High severity vulnerabilities
- **Dependencies:** 4 CVEs requiring immediate patches
- **Code Quality:** 3 functions with critical complexity (CC 57, 29, 28)
- **Test Coverage:** 61.5% (below 80% target)
- **Accessibility:** 45% WCAG 2.1 AA compliance
- **Architecture:** 8 DRY violations

**Current Health Score:** 76/100
**Target Health Score:** 88+/100

### Solution Approach

**4-Wave Parallel Execution:**
- Wave 1: Security & Infrastructure (3 days)
- Wave 2: Complexity & Quality (5 days)
- Wave 3: Architecture & Accessibility (6 days)
- Wave 4: Performance & Validation (4 days)

**6 Specialized Agents:**
1. security-fixer-agent
2. complexity-refactor-agent
3. test-infrastructure-agent
4. accessibility-agent
5. architecture-cleanup-agent
6. automation-agent

**Efficiency Gain:** 2.5x faster than sequential (18 days vs 45 days)

---

## Wave Summary

### Wave 1: Critical Security & Infrastructure (Days 1-3)
**Agents:** security-fixer, test-infrastructure, automation, accessibility
**Goal:** Eliminate critical vulnerabilities, establish test infrastructure
**Deliverables:**
- Zero critical/high security findings
- All tests passing
- CVEs patched
- Pre-commit hooks functional
- Basic accessibility improvements

### Wave 2: Complexity Reduction & Code Quality (Days 4-8)
**Agents:** complexity-refactor, test-infrastructure, automation
**Goal:** Reduce complexity hotspots, improve maintainability
**Deliverables:**
- All functions CC <15
- Storage coverage ≥80%
- Zero PEP 8 violations
- CHANGELOG.md and LICENSE created

### Wave 3: Architecture & Accessibility (Days 9-14)
**Agents:** architecture-cleanup, accessibility, test-infrastructure
**Goal:** Address DRY violations, complete accessibility
**Deliverables:**
- DRY violations ≤2
- WCAG 2.1 AA ≥75%
- API documentation complete
- Utilities centralized

### Wave 4: Performance Optimization & Final Validation (Days 15-18)
**Agents:** complexity-refactor, architecture-cleanup, test-infrastructure, automation
**Goal:** Optimize performance, final validation
**Deliverables:**
- Performance optimizations implemented
- Test coverage ≥80%
- Zero security findings
- Repository health ≥88/100

---

## Key Principles

### 1. Territorial Ownership
Each agent has exclusive write access to specific files. No overlapping modifications within a wave.

### 2. Contract-Driven Development
All integrations defined by contracts written before implementation. Agents validate against contracts, not implementations.

### 3. Progressive Validation
Quality gates after each wave ensure problems caught early. No wave starts until previous wave passes validation.

### 4. Async Communication
Agents coordinate through shared files (JSON status, handoffs.md, daily-status.md). No synchronous meetings required.

### 5. Failure Transparency
All blockers and failures immediately visible to all agents. Escalation protocol ensures quick resolution.

---

## Success Metrics

| Metric | Baseline | Target | Status |
|--------|----------|--------|--------|
| Repository Health | 76/100 | ≥88/100 | Pending |
| Security (Critical/High) | 1C + 3H | 0 | Pending |
| CVEs | 4 | 0 | Pending |
| Test Coverage | 61.5% | ≥80% | Pending |
| WCAG Compliance | 45% | ≥75% | Pending |
| Max Complexity | 57 | ≤15 | Pending |
| DRY Violations | 8 | ≤2 | Pending |

---

## Execution Commands

### Start Wave 1
```bash
# From project root
cd /Volumes/tkr-riffic/@tkr-projects/tkr-docusearch

# Launch agents (conceptual - use Task tool in Claude Code)
/orchestrate security-fixer-agent --wave 1
/orchestrate test-infrastructure-agent --wave 1
/orchestrate automation-agent --wave 1
/orchestrate accessibility-agent --wave 1
```

### Monitor Progress
```bash
# Check overall progress
cat .context-kit/orchestration/repo-critical-fixes/progress.json | jq

# Check agent statuses
ls .context-kit/orchestration/repo-critical-fixes/status/*.json | \
  xargs -I {} jq -r '"\(.agent): \(.status) - \(.completed_tasks | length)/\(.completed_tasks | length + .remaining_tasks | length) tasks"' {}

# View recent handoffs
tail -20 .context-kit/orchestration/repo-critical-fixes/handoffs.md

# Check for blockers
cat .context-kit/orchestration/repo-critical-fixes/blockers.md
```

### Validate Wave Gate
```bash
# Run gate validation (example for Wave 1)
# Security check
bandit -r src/ -ll | grep "Total issues"

# Test check
pytest -v --tb=short

# CVE check
pip-audit | grep "No known vulnerabilities"

# If all pass, authorize next wave
echo "Wave 1 PASSED" > .context-kit/orchestration/repo-critical-fixes/gates/wave-1-gate-report.md
```

---

## Resources

- **Full Plan:** [orchestration-plan.md](orchestration-plan.md)
- **Agent Assignments:** [agent-assignments.md](agent-assignments.md)
- **Validation Strategy:** [validation-strategy.md](validation-strategy.md)
- **Coordination Protocol:** [coordination-protocol.md](coordination-protocol.md)
- **Integration Contracts:** [integration-contracts/](integration-contracts/)

---

## Support

### Questions?
Post in `coordination.md` tagging relevant agents or orchestrator.

### Blockers?
Document in `blockers.md` with severity and impact. Escalate if not resolved within 4 hours.

### Status Updates?
Update your status JSON after each task and post daily updates in `daily-status.md`.

---

## License

This orchestration plan is part of the tkr-docusearch project and follows the same license (MIT).

---

**Ready to execute?** Review the orchestration-plan.md and launch Wave 1 agents!
