---
name: review-team
description: Spawn an Agent Team to verify completed implementation work
allowed-tools:
  - Read
  - Grep
  - Glob
  - Task
  - mcp__context-kit__planning
  - mcp__context-kit__module
  - mcp__context-kit__context
  - mcp__context-kit__analyze
  - mcp__context-kit__insight
  - mcp__ide__getDiagnostics
---

# Review Team Command

Spawn an Agent Team to verify completed implementation work.

## Arguments

- `$ARGUMENTS` - Feature ID, capability ID, or file paths to review

## Prerequisites Check

First, verify Agent Teams are enabled:

```bash
# Check if CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS is set
```

If not enabled, inform the user:

> Agent Teams are experimental and disabled by default. To use review-team, enable via settings:
>
> ```json
> // .claude/settings.local.json
> {
>   "env": {
>     "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
>   }
> }
> ```

## Execution

### Step 1: Identify Review Scope

Parse `$ARGUMENTS` to determine what to review:

**If feature ID provided:**
```
mcp__context-kit__planning command:get_feature id:<feature_id>
mcp__context-kit__planning command:list_slices feature_id:<feature_id>
```

**If capability ID provided:**
```
mcp__context-kit__planning command:get_capability id:<capability_id>
```

**If file paths provided:**
- Use the files directly as review scope

### Step 2: Gather Implementation Details

For the identified scope:

1. **List files** - Get all files in the implementation
2. **Get specs** - Load spec documents for conformance checking
3. **Identify contracts** - Types, APIs, schemas that need verification

### Step 3: Create Review Team

Create the agent team with appropriate size based on scope:

**For small scope (< 5 files):**
Create minimal 2-reviewer team:
- Wiring-Quality Reviewer
- Spec Reviewer

**For medium scope (5-15 files):**
Create standard 3-reviewer team:
- Wiring Reviewer
- Quality Reviewer
- Spec Reviewer

**For large scope (> 15 files):**
Create extended 5-reviewer team:
- Wiring Reviewer
- Quality Reviewer
- Spec Reviewer
- Security Reviewer
- Performance Reviewer

### Step 4: Spawn Teammates

Create team with natural language:

```
Create an agent team called "review-<scope-name>" to verify the implementation.

Team members:
1. wiring-reviewer: Verify all imports, exports, barrel files, and route registrations
2. quality-reviewer: Run diagnostics, check type errors, verify test coverage
3. spec-reviewer: Compare implementation against spec deliverables

Context:
- Feature/Capability: <name>
- Files to review: <file list>
- Specs to check: <spec locations>

Each reviewer should:
1. Thoroughly investigate their focus area
2. Document findings with file:line references
3. Classify issues as ERROR/WARN/INFO
4. Message the team lead when complete

I will synthesize findings into a consolidated report.
```

### Step 5: Monitor Progress

As teammates report findings:
1. Acknowledge receipt
2. Ask clarifying questions if needed
3. Track progress toward completion

### Step 6: Synthesize Report

When all reviewers complete, produce consolidated report:

```markdown
## Review Team Report: <scope-name>

### Summary
| Category | Errors | Warnings | Verified |
|----------|--------|----------|----------|
| Wiring   | N      | N        | N        |
| Quality  | N      | N        | N        |
| Spec     | N      | N        | N        |

### Verdict: [PASS | CONDITIONAL PASS | FAIL]

### Critical Issues (Must Fix)
<numbered list with file:line>

### Warnings (Should Fix)
<numbered list with file:line>

### Verified Items
<checklist of what passed>

### Recommendations
<next steps>
```

### Step 7: Cleanup

After report is delivered:

```
Clean up the review-<scope-name> team
```

## Output

Deliver the consolidated review report to the user.

If errors were found, offer to:
1. Create backlog items for fixes
2. Record findings as insights
3. Update slice/capability status

## Examples

### Review a feature
```
/review-team feat_user_auth
```

### Review specific files
```
/review-team src/services/auth.ts src/routes/auth.ts src/types/auth.ts
```

### Review a capability
```
/review-team cap_oauth_integration
```

### Review current orchestration
```
/review-team --current-orchestration
```
