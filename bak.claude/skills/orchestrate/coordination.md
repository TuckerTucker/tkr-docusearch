# Agent Coordination Guide

Contract patterns and coordination strategies for multi-agent orchestration.

## Core Principle: Contracts Over Communication

Agents in an orchestrated workflow **do not communicate directly**. Instead, they:
1. **Consume contracts** from prior waves (types, schemas, APIs)
2. **Produce artifacts** that fulfill contracts for future waves
3. **Validate via gates** that contracts are met

This eliminates coordination overhead and ensures parallel execution safety.

---

## Data Storage

Contracts, gate definitions, and agent constraints are stored in the Koji database and managed via REST API. The planner auto-generates these from slice data:

- **Contracts** → `orchestration_contracts` table, managed via `GET/PATCH /api/orchestration/runs/:id/contracts`
- **Gate definitions** → `wave_gate_definitions` table, managed via `GET /api/orchestration/runs/:id/gate-definitions`
- **Agent constraints** → stored on `agent_executions` (`path_constraints`, `pattern_requirements`, `completion_checklist` JSON columns)
- **Briefing context** → auto-assembled by `assembleBriefing()` (`core/planning/orchestration/briefing.ts`), includes slice details, territory, constraints, prior wave outputs, and insights

The planner (`core/planning/orchestration/planner.ts`) auto-derives:
- `file_location` contracts from slice `delivers` arrays
- L1-L5 gate definitions based on slice layers
- Path constraints, pattern requirements, and completion checklists per layer
- Wiring wave with orphan detection contracts

The contract types and coordination patterns below describe the *conceptual model*. The planner generates the DB records; agents and the executor consume them.

---

## Contract Types

### 1. Type Contracts (Shared Data Shapes)

**Definition:** TypeScript interfaces, Python dataclasses, Go structs that define data shapes.

**When to use:** When multiple agents need to work with the same data structure.

**Example:**
```typescript
// Wave 1: Foundation Agent produces
// src/types/user.ts
export interface UserProfile {
  id: string;
  email: string;
  displayName: string;
  avatarUrl?: string;
}

export interface ProfileUpdateRequest {
  displayName?: string;
  avatarUrl?: string;
}
```

**Wave 1 Gate:**
```bash
# Verify contract exists
test -f src/types/user.ts
grep "export interface UserProfile" src/types/user.ts
grep "export interface ProfileUpdateRequest" src/types/user.ts
```

**Wave 2 Agents consume:**
```typescript
// Backend agent
import { UserProfile, ProfileUpdateRequest } from '../types/user';

// Frontend agent
import type { UserProfile, ProfileUpdateRequest } from '@/types/user';
```

**Why this works:**
- Both agents work against same contract
- Type checker enforces compliance
- Changes to contract break both agents equally (fail-fast)

---

### 2. API Contracts (Endpoint Specifications)

**Definition:** HTTP endpoints with request/response shapes, status codes, error formats.

**When to use:** When frontend and backend agents need to integrate.

**Example:**
```typescript
// Wave 1: API Spec Agent produces
// docs/api-contracts.md

## PUT /api/users/:id/profile

**Request:**
```json
{
  "displayName": "string?",
  "avatarUrl": "string?"
}
```

**Response 200:**
```json
{
  "id": "string",
  "email": "string",
  "displayName": "string",
  "avatarUrl": "string?"
}
```

**Response 400:**
```json
{
  "error": "string",
  "details": { "field": "string", "message": "string" }[]
}
```
```

**Wave 1 Gate:**
```bash
# Verify API contract documented
test -f docs/api-contracts.md
grep "PUT /api/users/:id/profile" docs/api-contracts.md
```

**Wave 2 Agents implement:**
```typescript
// Backend agent implements server
app.put('/api/users/:id/profile', async (req, res) => {
  // Implementation follows contract
});

// Frontend agent implements client
async function updateProfile(userId: string, updates: ProfileUpdateRequest) {
  const response = await fetch(`/api/users/${userId}/profile`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  });
  // Handles responses per contract
}
```

**Why this works:**
- Both sides implement against same spec
- Integration tests in Wave 3 verify compliance
- Contract serves as integration test oracle

---

### 3. Schema Contracts (Database Definitions)

**Definition:** Database tables, columns, indexes, constraints.

**When to use:** When multiple agents build services on top of the same data store.

**Example:**
```sql
-- Wave 1: Schema Agent produces
-- migrations/001_user_profiles.sql

CREATE TABLE user_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  display_name VARCHAR(100) NOT NULL,
  avatar_url TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_profiles_email ON user_profiles(email);
```

**Wave 1 Gate:**
```bash
# Run migration
npm run db:migrate

# Verify table exists
psql -c "\d user_profiles"
```

**Wave 2 Agents consume:**
```typescript
// Repository agent
const profile = await db.query(
  'SELECT id, email, display_name, avatar_url FROM user_profiles WHERE id = $1',
  [userId]
);

// Analytics agent
const stats = await db.query(
  'SELECT COUNT(*) FROM user_profiles WHERE created_at > $1',
  [startDate]
);
```

**Why this works:**
- Schema established before services built
- Database enforces constraints for both agents
- Migration reversibility allows rollback

---

### 4. File Location Contracts (Module Paths)

**Definition:** Agreed-upon paths for files, modules, components.

**When to use:** When agents create files that others will import.

**Example:**
```
// Wave 1: Architecture Agent produces
// docs/file-structure.md

## User Profile Module

- `src/types/user.ts` - Type definitions
- `src/services/user-profile.service.ts` - Business logic
- `src/api/user-profile.routes.ts` - API endpoints
- `src/components/UserProfile.tsx` - UI component
```

**Wave 1 Gate:**
```bash
# Verify structure documented
test -f docs/file-structure.md
grep "src/types/user.ts" docs/file-structure.md
```

**Wave 2 Agents follow:**
```typescript
// Service agent creates
// src/services/user-profile.service.ts
export class UserProfileService { }

// API agent imports
import { UserProfileService } from '../services/user-profile.service';

// UI agent imports
import { UserProfileService } from '@/services/user-profile.service';
```

**Why this works:**
- No guessing where to put files
- No import path conflicts
- Easier to navigate codebase post-orchestration

---

### 5. Behavior Contracts (Test Specifications)

**Definition:** Expected behaviors described as test cases, before implementation.

**When to use:** Test-driven orchestration, especially for complex logic.

**Example:**
```typescript
// Wave 1: Test Spec Agent produces
// tests/user-profile.spec.ts

describe('UserProfileService', () => {
  it('updates display name when valid', async () => {
    const result = await service.updateProfile(userId, { displayName: 'New Name' });
    expect(result.displayName).toBe('New Name');
  });

  it('rejects empty display name', async () => {
    await expect(
      service.updateProfile(userId, { displayName: '' })
    ).rejects.toThrow('Display name cannot be empty');
  });

  it('sanitizes HTML in display name', async () => {
    const result = await service.updateProfile(userId, { displayName: '<script>alert()</script>' });
    expect(result.displayName).not.toContain('<script>');
  });
});
```

**Wave 1 Gate:**
```bash
# Tests exist and fail (not implemented yet)
npm test -- user-profile.spec.ts
# Expected: tests run but fail
```

**Wave 2 Agents implement to pass tests:**
```typescript
// Service agent implements
export class UserProfileService {
  async updateProfile(userId: string, updates: ProfileUpdateRequest) {
    if (updates.displayName !== undefined) {
      if (updates.displayName.trim() === '') {
        throw new Error('Display name cannot be empty');
      }
      updates.displayName = sanitizeHtml(updates.displayName);
    }
    // ... rest of implementation
  }
}
```

**Wave 2 Gate:**
```bash
# Tests pass
npm test -- user-profile.spec.ts
# Expected: all tests pass
```

**Why this works:**
- Tests define expected behavior unambiguously
- Implementation agent has clear success criteria
- Refactoring later is safe (tests catch regressions)

---

## Coordination Patterns

### Pattern 1: Handoff via Artifacts

**Scenario:** Wave 1 creates files, Wave 2 uses them.

**Wave 1 Output:**
- Creates `src/types/user.ts`
- Creates `src/schemas/user.schema.sql`

**Wave 1 Gates:**
```bash
test -f src/types/user.ts
test -f src/schemas/user.schema.sql
npm run build  # Ensures types compile
```

**Wave 2 Input:**
- Agents instructed: "Import types from src/types/user.ts"
- Agents instructed: "Assume user_profiles table exists per src/schemas/user.schema.sql"

**Coordination mechanism:** File system + gates ensure artifacts exist and are valid.

---

### Pattern 2: Handoff via Documentation

**Scenario:** Wave 1 designs architecture, Wave 2 implements it.

**Wave 1 Output:**
- Creates `docs/api-contracts.md` (API spec)
- Creates `docs/architecture.md` (component diagram)

**Wave 1 Gates:**
```bash
test -f docs/api-contracts.md
grep "PUT /api/users" docs/api-contracts.md  # Spot check
test -f docs/architecture.md
```

**Wave 2 Input:**
- Agents instructed: "Implement endpoints per docs/api-contracts.md"
- Agents instructed: "Follow architecture in docs/architecture.md"

**Coordination mechanism:** Documentation serves as contract; gates verify completeness.

---

### Pattern 3: Handoff via Running Services

**Scenario:** Wave 1 deploys infrastructure, Wave 2 deploys applications.

**Wave 1 Output:**
- Provisions database (outputs connection string to `.env`)
- Provisions S3 bucket (outputs bucket name to `config/storage.json`)

**Wave 1 Gates:**
```bash
# Verify database reachable
psql $DATABASE_URL -c "SELECT 1"

# Verify S3 bucket exists
aws s3 ls s3://$(jq -r .bucketName config/storage.json)
```

**Wave 2 Input:**
- Agents instructed: "Use DATABASE_URL from .env"
- Agents instructed: "Use bucket name from config/storage.json"

**Coordination mechanism:** Environment variables + config files + health checks.

---

### Pattern 4: Handoff via Shared State

**Scenario:** Wave 1 seeds database, Wave 2 runs tests against seed data.

**Wave 1 Output:**
- Runs `db:seed` script
- Exports seed IDs to `tests/fixtures/seed-ids.json`

**Wave 1 Gates:**
```bash
npm run db:seed
test -f tests/fixtures/seed-ids.json

# Verify seed data exists
psql $DATABASE_URL -c "SELECT COUNT(*) FROM users" | grep -q "10"
```

**Wave 2 Input:**
- Agents instructed: "Use seed IDs from tests/fixtures/seed-ids.json in tests"

**Coordination mechanism:** Database + fixture files.

---

## Anti-Patterns to Avoid

### ❌ Anti-Pattern 1: Agents Messaging Each Other

**Problem:**
```
Wave 2:
├─ Agent A: Build backend, notify Agent B when done
└─ Agent B: Wait for Agent A, then build frontend
```

This defeats parallelism and adds fragile communication.

**Fix:** Make them sequential waves, or eliminate dependency via contracts.

---

### ❌ Anti-Pattern 2: Implicit Contracts

**Problem:**
```
Wave 1: Agent A creates types (but doesn't document where)
Wave 2: Agent B guesses where types are
```

**Fix:** Explicit file location contracts in Wave 1 instructions.

---

### ❌ Anti-Pattern 3: Weak Gates

**Problem:**
```
Wave 1 Gate: "Types seem okay"
```

**Fix:** Concrete, verifiable gates:
```bash
test -f src/types/user.ts
npm run build  # Type check
```

---

### ❌ Anti-Pattern 4: Over-Coordination

**Problem:**
```
Wave 1:
├─ Agent A: Create type
├─ Agent B: Review Agent A's type
└─ Agent C: Approve Agent B's review
```

Excessive coordination overhead for simple task.

**Fix:** Single agent creates type, gate validates via type checker.

---

### ❌ Anti-Pattern 5: Hidden Dependencies

**Problem:**
```
Wave 2:
├─ Agent A: Build service (secretly depends on config file)
└─ Agent B: Build UI (also secretly depends on same config file)
```

Both agents fail because config not created in Wave 1.

**Fix:** Identify shared dependencies, create in foundation wave.

---

## Debugging Failed Coordination

### Symptom: Wave 2 agent fails immediately

**Likely cause:** Wave 1 gate passed but didn't verify the right thing.

**Debug:**
1. Check Wave 1 gates—are they specific enough?
2. Manually verify Wave 1 outputs exist and are correct
3. Check Wave 2 agent's instructions—do they match Wave 1 outputs?

**Fix:** Strengthen Wave 1 gates to catch the issue.

---

### Symptom: Wave 2 agents produce incompatible outputs

**Likely cause:** Missing shared contract in Wave 1.

**Debug:**
1. Identify what agents assumed differently (e.g., data shape)
2. Check if Wave 1 established this contract
3. If not, that's the gap

**Fix:** Add contract to Wave 1, re-run from Wave 1.

---

### Symptom: Wave 3 integration fails

**Likely cause:** Wave 1/2 contracts were incomplete or incorrect.

**Debug:**
1. Check integration point (API call, import, database query)
2. Compare actual vs. expected contract
3. Find which wave produced incorrect contract

**Fix:**
- If contract wrong: Fix in foundation wave, re-run
- If contract incomplete: Extend contract, re-run dependent waves

---

### Symptom: Gate passes but downstream fails

**Likely cause:** Gate checks wrong thing or too shallow.

**Debug:**
1. Manually verify what gate checked
2. Identify what downstream agent actually needed
3. Compare—what's the gap?

**Fix:** Add deeper gate check (e.g., not just file exists, but file exports expected symbol).

---

## Gate Design Best Practices

> These levels map to the `wave_gate_definitions.level` column (1-5) and are auto-generated by `generateGateDefinitions()` in the planner based on slice layers. The definitions below describe what each level verifies.

### Level 1: Existence Gates
```bash
test -f src/types/user.ts
test -d src/components
```

**Use for:** Verifying files/directories created.

---

### Level 2: Content Gates
```bash
grep "export interface UserProfile" src/types/user.ts
jq -e '.bucketName' config/storage.json
```

**Use for:** Verifying specific content exists.

---

### Level 3: Validation Gates
```bash
npm run build          # TypeScript compiles
npm run lint           # Code passes linter
npm run test:unit      # Unit tests pass
```

**Use for:** Verifying code quality and correctness.

---

### Level 4: Integration Gates
```bash
npm run test:integration    # Services integrate correctly
curl http://localhost:3000/health | grep -q "ok"
```

**Use for:** Verifying systems work together.

---

### Level 5: End-to-End Gates
```bash
npm run test:e2e       # Full user flows work
```

**Use for:** Final validation before completion.

**Recommendation:** Use Level 1-3 for early waves, Level 4-5 for final waves.

---

## Contract Evolution

### Adding to Contracts (Safe)

**Scenario:** Wave 3 needs additional field in type from Wave 1.

**Safe approach:**
1. Pause orchestration
2. Update Wave 1 contract (add optional field)
3. Re-run Wave 1 gates to verify
4. Continue from Wave 3 (downstream agents see new field)

**Why safe:** Optional field doesn't break existing usage.

---

### Changing Contracts (Risky)

**Scenario:** Wave 1 contract has wrong type (string should be number).

**Risky approach:**
1. Update Wave 1 contract
2. Re-run all waves that depend on it (Wave 2, 3, ...)

**Why risky:** Breaks all downstream agents; might be faster to restart.

---

### Versioning Contracts (Advanced)

**Scenario:** Multiple orchestrations share same contracts.

**Approach:**
- Version contract files: `types/user.v1.ts`, `types/user.v2.ts`
- Orchestration A uses v1, Orchestration B uses v2
- Migrate when both complete

**When to use:** Large-scale orchestrations with shared foundations.

---

## Agent Completion Verification

Before an agent marks work as complete, verification checks must pass.

### Required Verification Tools

| Tool | Purpose | When Required |
|------|---------|---------------|
| `mcp__ide__getDiagnostics()` | Type errors, lint issues | Always |
| `mcp__context-kit__browser_errors()` | Console errors | UI/frontend work |
| `mcp__context-kit__browser_network()` | API failures | API/backend work |

### Agent Completion Protocol

Each agent should:

1. **Before final report:**
```
# Run diagnostic check
diagnostics = mcp__ide__getDiagnostics()

if diagnostics.errors > 0:
  # DO NOT mark complete
  # Report errors in findings
  status = "blocked"
```

2. **For UI agents, also check:**
```
browser_errors = mcp__context-kit__browser_errors(limit: 20)
if browser_errors.length > 0:
  # Review and address or document
```

3. **For API agents, also check:**
```
network = mcp__context-kit__browser_network(url_filter: "/api/")
failed_requests = [r for r in network if r.status >= 400]
if failed_requests.length > 0:
  # Address failures before completion
```

### Verification in Agent Prompts

Include in agent task prompts:

```markdown
## Completion Requirements

Before reporting completion:
1. Run `mcp__ide__getDiagnostics()` - must have zero errors
2. [If UI work] Run `mcp__context-kit__browser_errors()` - address any errors
3. [If API work] Run `mcp__context-kit__browser_network()` - verify no 4xx/5xx

Include verification results in your completion report.
```

### Handling Verification Failures

When verification fails:

1. **Diagnose** - Identify root cause from tool output
2. **Fix** - Address if within agent's scope
3. **Document** - If cannot fix, document as known issue
4. **Escalate** - If blocking, report to orchestrator

---

## Agent Prompt Constraints (Lessons Learned)

> These constraints are now stored on the `agent_executions` record (`path_constraints`, `pattern_requirements`, `completion_checklist` JSON columns) and injected into agent briefing context automatically via `assembleBriefing()` → `formatBriefingForAgent()`. The planner's `deriveAgentConstraints()` generates them per-layer.

Based on production orchestration experience (P0/P1/P2 phases, 54 slices):

### Path Restrictions

Agents MUST have explicit path constraints to prevent files in wrong locations.

```yaml
constraints:
  paths:
    allowed:
      - "src/**/*.py"
      - "src/**/*.ts"
      - "tests/**/*.py"
      - "tests/**/*.ts"
    forbidden:
      - "/*.md"       # No markdown in project root
      - "/*.py"       # No python in project root
      - "/*.ts"       # No typescript in project root
      - "/*.txt"      # No text files in project root
```

**Why:** In P0, agents created 9 misplaced files in project root (WAVE5_CHECKLIST.md, validate_*.py, etc.) requiring manual cleanup.

### Pattern Requirements

Include explicit coding pattern requirements:

```yaml
patterns:
  required:
    - "NO files in project root"
    - "NO emojis unless explicitly requested"
    - "Timezone-aware datetime only: datetime.now(UTC) not utcnow()"
    - "Run pytest on your code before completing"
    - "Run linter before completing"

  framework_specific:
    pydantic_v2:
      - "Avoid use_enum_values=True unless serialization-only model"
      - "Compare enums directly, not via .value on serialized objects"

    structlog:
      - "Use structlog for JSON logging"
      - "CLI tests: parse JSON output carefully, logs mix with output"

    timing_tests:
      - "Add 25-50% tolerance for OS scheduling"
      - "elapsed < 2.0 becomes elapsed < 2.5"
```

### Context Requirements

Provide agents with existing code patterns to follow:

```yaml
context:
  required:
    - "2-3 similar existing files as examples"
    - "Existing test patterns for the project"
    - "Framework-specific patterns (Pydantic, Click, etc.)"

  territory:
    defined: true          # Each agent knows which files they own
    conflicts: prevented   # No two agents modify same files
```

### Completion Checklist

Every agent completion report must include:

```markdown
## Completion Checklist

- [ ] All files in allowed paths (not project root)
- [ ] Tests passing: `pytest` exits 0
- [ ] Linter clean: `ruff`/`eslint` exits 0
- [ ] `mcp__ide__getDiagnostics()` returns zero errors
- [ ] Imports valid: no unresolved references
- [ ] Patterns matched existing code style
- [ ] No emojis added (unless requested)
- [ ] Timezone-aware datetime used
```

### Common Issues Prevented

| Issue | Prevention | P0→P1 Result |
|-------|-----------|--------------|
| Files in project root | Explicit path constraints | 9→0 misplaced |
| Pydantic enum issues | Framework guidance in context | Fixed pattern |
| Timing test failures | 25% tolerance rule | No flaky tests |
| CLI JSON parsing | Test pattern examples | Helper created |
| Manual intervention | All constraints combined | 5→0 fixes |

---

## Summary Checklist

Before starting orchestration, ensure:

- [ ] **Wave 1 establishes all contracts** (types, schemas, APIs, file paths)
- [ ] **Contracts are explicit** (documented, not implicit)
- [ ] **Gates verify contracts** (existence, content, validation)
- [ ] **Wave N agents consume Wave N-1 contracts** (no hidden deps)
- [ ] **No inter-agent communication** (agents are independent)
- [ ] **Integration wave validates contracts** (end-to-end tests)
- [ ] **Agent prompts include verification requirements**
- [ ] **Agent prompts include path constraints** (allowed/forbidden)
- [ ] **Agent prompts include pattern requirements** (no emojis, datetime, etc.)
- [ ] **Agent prompts include context files** (existing patterns to follow)

If any checkbox unchecked, coordination will likely fail.
