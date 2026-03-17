# Wave Planning Guide

How to structure waves for parallel agent execution in orchestrated workflows.

## Core Principles

### Wave = Dependency Layer

Each wave represents a layer of work where all agents can execute in parallel because they share the same dependency prerequisites and produce outputs for the next wave.

**Wave Dependency Rule:** Wave N can only start after all gates in Wave N-1 pass.

**Intra-Wave Parallelism:** All agents within Wave N execute concurrently.

## Automated Plan Generation

The planner (`core/planning/orchestration/planner.ts`) automates wave plan generation from slice dependency graphs:

- **Wave grouping**: Topological sort of slice dependencies → wave layers
- **Contracts**: Auto-extracted from slice `delivers` arrays (`extractContractsFromSlices`)
- **Gate definitions**: Auto-generated per layer L1-L5 (`generateGateDefinitions`)
- **Agent constraints**: Auto-derived from territory and layer (`deriveAgentConstraints`)
- **Wiring wave**: Auto-appended by `buildWiringWave()` (opt-out: `includeWiringWave: false`)

Create a run via API:
```bash
POST /api/orchestration/runs
{ "feature_id": "...", "agents_per_wave": 3, "agent_prefix": "auth" }
```

The manual wave design patterns below remain valuable for understanding the planner's output and for custom/override scenarios.

---

### Four-Wave Pattern (Foundation → Implementation → Integration → Wiring)

Most features naturally decompose into four waves:

1. **Wave 1: Foundation** - Shared contracts, types, schemas, core utilities
2. **Wave 2: Implementation** - Business logic, components, endpoints that depend on Wave 1
3. **Wave 3: Integration** - Glue code, tests, documentation that validate Wave 1+2
4. **Wave N (Final): Wiring** - Connect new components to existing application (routes, navigation, imports)

> **MANDATORY:** Every orchestration MUST end with a Wiring Wave to prevent orphaned components.

---

## Wave Structure Patterns

### Pattern 1: Simple Feature (3 waves, 3-6 agents)

**Example:** Add user profile editing feature

```
Wave 1: Foundation (2 agents, parallel)
├─ Agent A: Define user profile schema + validation types
└─ Agent B: Create API endpoint contracts (request/response shapes)

Gates: Schema exists, types compile, contracts documented

Wave 2: Implementation (2 agents, parallel)
├─ Agent C: Implement backend profile update logic
└─ Agent D: Build frontend profile edit form component

Gates: Backend logic passes unit tests, frontend component renders

Wave 3: Integration (2 agents, parallel)
├─ Agent E: Wire frontend to backend API + error handling
└─ Agent F: Write integration tests + update documentation

Gates: E2E tests pass, feature works end-to-end
```

**Why this works:**
- Wave 1 establishes contracts both Wave 2 agents depend on
- Wave 2 agents work independently (backend vs frontend)
- Wave 3 validates integration and adds safety net

---

### Wiring Wave Pattern (MANDATORY — Auto-Generated)

> `buildWiringWave()` in `core/planning/orchestration/wiring-wave.ts` auto-generates wiring agents based on detected layers (UI → route coverage agent, API → endpoint registration agent, Core → barrel exports agent). Each gets pre-defined contracts, constraints, and L5 gate definitions. The planner appends this wave automatically unless `includeWiringWave: false`.

**Every orchestration ends with a Wiring Wave** that handles integration slices:

```
Final Wave: Wiring (1-3 agents, parallel)
├─ Agent X: Wire UI components (routes, navigation, parent imports)
├─ Agent Y: Wire API routes (server mounts, barrel exports)
└─ Agent Z: Wire core modules (index.ts barrels, re-exports)

Gates (ALL MUST PASS):
- orphan_detection: No Vue components without imports
- route_coverage: All views have routes
- api_mount_check: All route files mounted in server
- barrel_check: New directories have index.ts
```

**Wiring Agent Responsibilities:**

| Territory | Tasks |
|-----------|-------|
| UI Wiring | Add routes to router.ts, nav links to AppNav.vue, import components in parent views |
| API Wiring | Mount routers in server.ts, create barrel exports |
| Core Wiring | Create index.ts barrel files, wire module exports |

**Wiring Wave Gates (Automated):**

```bash
# These run as part of wave gate validation
orphan_detection:
  command: |
    for f in $(find dashboard/src/components -name "*.vue"); do
      basename=$(basename "$f" .vue)
      if ! grep -r "import.*$basename" dashboard/src --include="*.vue" --include="*.ts" | grep -v "$f" > /dev/null; then
        echo "ORPHAN: $f"
      fi
    done
  expected_output: ""
  blocker: true

route_coverage:
  command: |
    for view in $(find dashboard/src/views -name "*.vue"); do
      name=$(basename "$view" .vue)
      if ! grep -q "$name" dashboard/src/router.ts; then
        echo "MISSING ROUTE: $view"
      fi
    done
  expected_output: ""
  blocker: true
```

**Why Wiring Wave is Mandatory:**

Problem observed: Components created in implementation waves are "orphaned" - they exist but aren't:
- Imported in parent components
- Registered in routes
- Mounted in servers
- Exported from barrel files

Result: Features technically exist but are unreachable.

Solution: Dedicated wiring wave with automated orphan detection gates.

---

### Documentation Wave Pattern (Optional)

For features with significant public API or documentation requirements, include a **Docs Wave** before or alongside the final Integration wave:

```
Wave N: Documentation (1-2 agents, parallel)
├─ Agent D1: TSDoc/JSDoc coverage for new exports
└─ Agent D2: mdBook chapter + CHANGELOG entry

Gates (automated):
- tsdoc_coverage: ck docs:check --gate tsdoc --format json
- mdbook_builds: ck docs:check --gate mdbook --format json
- changelog_updated: ck docs:check --gate changelog --format json
```

**When to include a Docs Wave:**
- New public API being exposed
- Major feature affecting user documentation
- Slice spec has `layer: integration`
- Feature has 5+ new exports

**When to skip Docs Wave:**
- Internal refactoring
- Bug fixes
- Changes to existing tested code
- Private/internal modules

---

### Documentation Gate Selection by Layer

| Slice Layer | Required Doc Gates | Command |
|-------------|-------------------|---------|
| core | tsdoc | `ck docs:check --gate tsdoc` |
| infrastructure | tsdoc | `ck docs:check --gate tsdoc` |
| api | tsdoc | `ck docs:check --gate tsdoc` |
| ui | tsdoc | `ck docs:check --gate tsdoc` |
| integration | mdbook, changelog | `ck docs:check --layer integration` |
| mixed | tsdoc | `ck docs:check --gate tsdoc` |

---

### Good Documentation Gates (Automated)

Documentation gates are now first-class automated checks:

✅ `ck docs:check --gate tsdoc` - TSDoc/JSDoc coverage (exits 0 if >= 80%)
✅ `ck docs:check --gate mdbook` - mdBook builds successfully (exits 0)
✅ `ck docs:check --gate changelog` - CHANGELOG has entry (exits 0)
✅ `ck docs:check --layer {layer}` - All gates for layer pass (exits 0)

**Example wave gate integration:**

```yaml
waves:
  3:
    name: "Integration"
    gate:
      automated_checks:
        - name: "tsdoc_coverage"
          command: "ck docs:check --gate tsdoc --format json"
          expected_output: "passed"
          timeout: "30s"
          description: "All exports have TSDoc comments"

        - name: "mdbook_build"
          command: "ck docs:check --gate mdbook --format json"
          expected_output: "passed"
          timeout: "60s"
          description: "Documentation builds successfully"
```

**MCP tool integration:**

```typescript
// Verify docs in agent completion
const report = await mcp__context-kit__analyze({
  type: "docs",
  layer: "core"
});

if (report.overall_status !== "passed") {
  throw new Error("Documentation gates failed");
}
```

---

### Pattern 2: Complex Feature (4+ waves, 6-12 agents)

**Example:** Multi-tenant authorization system

```
Wave 1: Data Foundation (2 agents, parallel)
├─ Agent A: Design tenant + role database schemas
└─ Agent B: Create authorization policy type definitions

Gates: Schemas migrated, types compile

Wave 2: Core Services (3 agents, parallel)
├─ Agent C: Implement tenant repository (CRUD)
├─ Agent D: Build authorization policy engine
└─ Agent E: Create role assignment service

Gates: Unit tests pass for all services, services integrate with schemas

Wave 3: API Layer (2 agents, parallel)
├─ Agent F: Expose tenant management REST endpoints
└─ Agent G: Add authorization middleware for route protection

Gates: API endpoints functional, middleware applied correctly

Wave 4: Integration & Validation (3 agents, parallel)
├─ Agent H: Frontend tenant admin UI
├─ Agent I: End-to-end authorization flow tests
└─ Agent J: Documentation + migration guide

Gates: UI works, E2E tests pass, docs complete
```

**Why this works:**
- Wave 1: Data layer must exist before services
- Wave 2: Services depend on data layer, but independent of each other
- Wave 3: API layer depends on services but not on UI
- Wave 4: Everything comes together for validation

---

### Pattern 3: Refactoring (2 waves, 4-6 agents)

**Example:** Extract shared utilities from monolithic codebase

```
Wave 1: Extract & Test (3 agents, parallel)
├─ Agent A: Extract string utilities to shared module
├─ Agent B: Extract date utilities to shared module
└─ Agent C: Extract validation utilities to shared module

Gates: All utilities have unit tests, modules export correctly

Wave 2: Replace & Verify (3 agents, parallel)
├─ Agent D: Replace string utility calls in subsystem X
├─ Agent E: Replace date utility calls in subsystem Y
└─ Agent F: Replace validation calls in subsystem Z

Gates: All subsystems pass integration tests, no regressions
```

**Why this works:**
- Wave 1 creates stable, tested utilities
- Wave 2 safely replaces scattered implementations
- If Wave 1 has issues, Wave 2 doesn't make things worse

---

## Dependency Management

### Vertical Dependencies (Between Waves)

**Rule:** Output of Wave N becomes input to Wave N+1

**Examples:**
- Wave 1 creates types → Wave 2 imports those types
- Wave 2 creates API → Wave 3 calls that API
- Wave 3 creates tests → Wave 4 refactors with safety net

**How to encode:**
```
Wave 1 Gate: "types.ts exports UserProfile, ProfileUpdateRequest"
Wave 2 Input: "Import UserProfile from types.ts"
```

### Horizontal Dependencies (Within a Wave)

**Rule:** Agents in the same wave should NOT depend on each other's outputs

**Anti-pattern:**
```
Wave 2: Implementation
├─ Agent A: Create database repository
└─ Agent B: Create service that uses Agent A's repository ❌
```

**Fix:** Move Agent B to Wave 3, or combine A+B into single agent

**Correct pattern:**
```
Wave 2: Implementation
├─ Agent A: Backend repository (uses Wave 1 schema)
└─ Agent B: Frontend component (uses Wave 1 types)
```

Both agents depend only on Wave 1, not each other.

---

## Wave Sizing Guidelines

### Agents Per Wave

- **Min:** 2 agents (otherwise, why parallelize?)
- **Sweet spot:** 3-4 agents (enough parallelism, manageable coordination)
- **Max:** 4 agents (beyond this, context fragmentation occurs)

**If you need > 4 agents in a wave:**
- Split into sub-waves if dependencies allow
- Combine related work into single agents
- Question if feature is too complex for orchestration

---

## Execution Constraints (Lessons Learned)

Based on production orchestration experience (P0/P1/P2 phases, 54 slices):

### Concurrency Limits

| Setting | Value | Rationale |
|---------|-------|-----------|
| `max_concurrent_agents` | 4 | >4 causes context fragmentation and tracking difficulty |
| `agent_batch_size` | 2-3 | Within a wave, launch agents in batches of 2-3 |
| `wave_strategy` | sequential | Complete Wave N before starting Wave N+1 |

These are enforced by `PlanOptions.agentsPerWave` passed to the planner, and the executor's `startWave` controls batch launch. Configure via API:

```bash
POST /api/orchestration/runs
{
  "feature_id": "...",
  "agents_per_wave": 3,
  "run_pre_build_gates": true,
  "agent_prefix": "auth"
}
```

### Wave Execution Protocol

1. **Before wave starts:** Verify all dependencies from prior waves
2. **Launch batch:** Start 2-3 agents (not all at once)
3. **Monitor:** Track agent progress, catch issues early
4. **Batch complete:** Wait for batch to finish before next batch
5. **Wave complete:** Run validation gate (pytest, lint, build)
6. **Gate pass:** Proceed to next wave
7. **Gate fail:** Fix issues before continuing

### Why These Limits Matter

**Problem observed (P0):** Launched 14 agents simultaneously instead of 6-8 target
- Context fragmentation across too many parallel contexts
- Difficult to track progress and catch issues early
- Manual intervention required to coordinate

**Solution applied (P1/P2):** Sequential waves with batch limits
- Zero manual fixes required
- No misplaced files
- 100% first-pass success rate

### Waves Per Feature

- **Simple:** 3 waves (foundation → implementation → integration)
- **Moderate:** 4 waves (data → services → API → UI)
- **Complex:** 5-6 waves (architecture with deep layering)

**If you need > 6 waves:**
- Break into multiple orchestrations (e.g., Phase 1 + Phase 2)
- Simplify architecture (fewer layers)
- Reconsider if feature should be tackled monolithically first

---

## Wave Gates (Success Criteria)

Each wave must define **pass/fail gates** that determine if the next wave can proceed.

### Good Gates (Automated, Verifiable)

✅ **Build succeeds:** `npm run build` exits 0
✅ **Tests pass:** `npm test` exits 0
✅ **Type check passes:** `tsc --noEmit` exits 0
✅ **Linter passes:** `eslint . --max-warnings 0` exits 0
✅ **File exists:** `test -f src/types/user.ts`
✅ **Contract met:** `grep "export interface UserProfile" src/types/user.ts`

### MCP Tool Gates (Enhanced Verification)

Use MCP/IDE tools for verification beyond standard build scripts:

✅ **IDE diagnostics clean:** `mcp__ide__getDiagnostics()` returns zero errors
✅ **Browser console clean:** `mcp__context-kit__browser_errors()` is empty (UI waves)
✅ **API requests succeed:** `mcp__context-kit__browser_network()` has no 4xx/5xx (API waves)

**Example MCP Gate Integration:**
```markdown
## Wave 2 Gates

### Standard Gates
- [ ] `npm run build` exits 0
- [ ] `npm run test:unit` exits 0

### MCP Verification Gates
- [ ] `mcp__ide__getDiagnostics()` → 0 errors
- [ ] [UI agents] `mcp__context-kit__browser_errors(limit: 20)` → empty
- [ ] [API agents] `mcp__context-kit__browser_network(url_filter: "/api/")` → no failures
```

**Gate Selection by Slice Layer:**

| Slice Layer | Standard Gates | MCP Gates |
|-------------|---------------|-----------|
| core | build, lint | diagnostics |
| infrastructure | build, lint, test | diagnostics |
| ui | build, lint, test | diagnostics + browser_errors |
| api | build, lint, test | diagnostics + browser_network |
| integration | build, test, e2e | diagnostics + browser_errors + browser_network |

### Bad Gates (Subjective, Manual)

❌ "Code looks good"
❌ "Seems to work"
❌ "Ready for next wave"
❌ "No obvious issues"

**Why bad gates fail:**
- Require human judgment → can't automate progression
- Ambiguous → different agents might interpret differently
- Not verifiable → can't programmatically check

---

## Common Wave Planning Mistakes

### Mistake 1: Waves with Dependencies

**Problem:**
```
Wave 2:
├─ Agent A: Create database migration
└─ Agent B: Run database migration and seed data ❌
```

Agent B depends on Agent A completing first → they're not parallel!

**Fix:** Make them sequential waves or combine into one agent.

### Mistake 2: Waves Too Granular

**Problem:**
```
Wave 1: Create file
Wave 2: Add imports to file
Wave 3: Add function to file
Wave 4: Export function from file
```

Excessive waves add coordination overhead with no parallelism benefit.

**Fix:** Combine into single wave with one agent.

### Mistake 3: Waves Too Coarse

**Problem:**
```
Wave 1: Implement entire feature
Wave 2: Test entire feature
```

No parallelization happening.

**Fix:** Decompose Wave 1 into parallel territories (backend, frontend, etc.)

### Mistake 4: Missing Foundation Wave

**Problem:**
```
Wave 1:
├─ Agent A: Build API endpoint (where's the schema?)
└─ Agent B: Build UI component (what's the data shape?)
```

Agents making independent assumptions about contracts → integration fails.

**Fix:** Add Wave 0 for shared types/schemas.

### Mistake 5: Unclear Gates

**Problem:**
```
Wave 1 Gate: "Foundation is ready"
```

Too vague to verify.

**Fix:**
```
Wave 1 Gates:
- types.ts exports UserProfile interface
- schema.sql creates users table
- npm run build succeeds
```

---

## Wave Planning Checklist

Before finalizing your wave plan, verify:

- [ ] Each wave has ≥ 2 agents (parallelism exists)
- [ ] Agents within a wave don't depend on each other
- [ ] Each wave has clear, verifiable gates
- [ ] Wave N agents only depend on Wave 0..N-1 outputs
- [ ] Total waves ≤ 6 (or feature broken into phases)
- [ ] Agents per wave ≤ 6 (or work combined)
- [ ] Foundation wave establishes shared contracts
- [ ] Integration wave validates end-to-end behavior
- [ ] **Documentation gates defined** (if integration or public API layer)
- [ ] **MANDATORY: Final wave is Wiring Wave** (routes, navigation, imports, barrels)
- [ ] **MANDATORY: Wiring Wave has orphan detection gates**

---

## Examples by Domain

### Backend Feature
```
Wave 1: Data (schema, migrations)
Wave 2: Services (repositories, business logic)
Wave 3: API (endpoints, middleware)
Wave 4: Tests (unit, integration, E2E)
Wave 5: Wiring (mount routes, barrel exports, server integration)
```

### Frontend Feature
```
Wave 1: Types & Contracts (API types, component props)
Wave 2: Components (UI building blocks)
Wave 3: Integration (state management, API calls)
Wave 4: Tests & Docs (component tests, storybook, docs)
Wave 5: Wiring (routes, navigation, parent view imports)
```

### Full-Stack Feature
```
Wave 1: Contracts (shared types, API spec)
Wave 2: Parallel Implementation (backend services, frontend components)
Wave 3: Integration (API wiring, error handling)
Wave 4: Validation (E2E tests, documentation)
Wave 5: Wiring (routes, navigation, server mounts, barrels)
```

### Infrastructure
```
Wave 1: Configuration (IaC definitions, secrets setup)
Wave 2: Deployment (provision resources in parallel)
Wave 3: Validation (health checks, monitoring)
Wave 4: Wiring (service registration, DNS, load balancer config)
```

---

## Advanced: Dynamic Wave Replanning

Sometimes mid-execution you discover:
- Wave gates fail → need remediation agent
- New dependencies discovered → need to insert wave
- Work completes faster → can collapse waves

**Replanning triggers:**
1. Wave gate fails 2+ times → add remediation wave
2. Agent discovers missing dependency → insert foundation work
3. Wave completes with < 50% planned work → collapse next wave into this one

**How to replan:**
- Pause execution after current wave
- Analyze failures or new information
- Regenerate plan from current state forward
- Resume with updated wave structure

This is advanced usage—most orchestrations should stick to initial plan.
