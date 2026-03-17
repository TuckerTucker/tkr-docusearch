---
name: planning
description: Unified planning system for decomposing products into capabilities, features, slices, stories, and specs. Use when user discusses planning, specs, slices, stories, features, products, capabilities, dependencies, progress, or implementation order.
allowed-tools: [Read, Write, Glob, Grep, Bash, Task]
source: tkr-kit
version: 2.0.0
---

# Planning Skill

> **Layer 1 — Capability.** This is a skill. It manages the full planning hierarchy from product vision to implementation-ready specs. It does NOT orchestrate multi-feature execution — that belongs to a future L3 command when the orchestration engine is validated end-to-end.

## Composition

| Layer | Component | Relationship |
|-------|-----------|-------------|
| L3 Command | `planning` (command) | thin dispatcher — parses `/planning <domain> <action>` and invokes this skill |
| L2 Agent | _deferred_ | orchestration engine not yet e2e tested; L2 adds value when parallel expand across features is needed |
| **L1 Skill** | **`planning` (this file)** | **manages hierarchy, expands artifacts, tracks status** |

This skill stays L1-only because:
- Planning operations are conversational and sequential (create → expand → review → approve)
- Bulk expansion (`expand specs`) iterates internally but results must be reviewed as a coherent set
- L2/L3 become valuable when orchestrating execution across multiple features in parallel — that requires the orchestration engine to be validated first

## Data Access — MANDATORY

**NEVER use raw SQL queries or direct `curl` to Koji endpoints.** All planning data MUST be accessed through one of these layers, in order of preference:

### 1. REST API (preferred for CRUD operations)
The observability service exposes planning endpoints. Use these via the Bash tool with `curl`:

```bash
# Base URL (port may vary — check TKR_OBS_PORT)
API="http://127.0.0.1:${TKR_OBS_PORT}/api/planning"

# Products
curl -s -X POST "$API/products" -H 'Content-Type: application/json' -d '{"name": "...", "status": "draft"}'
curl -s "$API/products"                          # list
curl -s "$API/products/{id}"                     # get
curl -s -X PATCH "$API/products/{id}" -d '{...}' # update
curl -s -X DELETE "$API/products/{id}"           # delete
curl -s "$API/products/{id}/summary"             # summary with capabilities

# Capabilities
curl -s -X POST "$API/capabilities" -d '{"product_id": "...", "name": "...", "layer": "domain"}'
curl -s "$API/capabilities?product_id={id}"      # list by product
curl -s "$API/capabilities/{id}"                 # get
curl -s "$API/capabilities/{id}/dependencies"    # dependency graph
curl -s "$API/capabilities/{id}/slices"          # linked slices

# Features
curl -s -X POST "$API/features" -d '{"name": "...", "capability_id": "..."}'
curl -s "$API/features?capability_id={id}"       # list by capability

# Stories (Interaction Stories)
curl -s -X POST "$API/stories" -H 'Content-Type: application/json' -d '{"feature_id": "...", "number": 1, "title": "..."}'
curl -s "$API/stories?feature_id={id}"                # list by feature
curl -s "$API/stories/{id}"                           # get
curl -s -X PATCH "$API/stories/{id}" -d '{...}'       # update
curl -s -X DELETE "$API/stories/{id}"                 # delete
curl -s "$API/stories/by-slice/{sliceId}"             # list by linked slice
curl -s -X POST "$API/expand/stories" -d '{"feature_id": "..."}'  # generate from feature

# Slices
curl -s -X POST "$API/slices" -d '{"feature_id": "...", "name": "...", "number": 1, "layer": "data"}'
curl -s "$API/slices?feature_id={id}"            # list by feature
curl -s -X PATCH "$API/slices/{id}" -d '{"status": "in_progress"}'

# Specs
curl -s -X POST "$API/specs" -d '{"feature_id": "...", "slice_number": 1, "content": "..."}'
curl -s "$API/specs?feature_id={id}"             # list by feature
```

### 2. Query functions (for scripts or when building new features)
Import from `core/koji/queries/planning-queries.ts`:

```typescript
import { createProduct, listProducts, getProduct, createCapability, createFeature, createSlice } from "core/koji/queries/planning-queries.js";
```

These functions use the `KojiHttpClient` internally — they do NOT bypass the single-writer architecture.

### 3. MCP planning tool (for agent-to-agent communication)
The `planning` MCP tool (`mcp/tools/unified/planning.ts`) wraps the REST API with command-based dispatch. Commands: `create_product`, `list_products`, `create_capability`, `create_feature`, `create_slice`, `create_spec`, `create_story`, `get_story`, `list_stories`, `update_story`, `delete_story`, `list_stories_by_slice`, `expand_stories`, etc.

### What NOT to do
- **NO** direct SQL via `curl -X POST http://localhost:42002/query -d '{"sql": "..."}'`
- **NO** raw inserts via `curl -X POST http://localhost:42002/insert`
- These bypass validation, schema enforcement, and cascade logic

## When to Use

Activate this skill when the user:
- Mentions planning, specs, slices, stories, features, products, or capabilities
- Wants to organize work into buildable units
- Needs to define user interactions, acceptance criteria, or test scenarios
- Needs to understand implementation order or dependencies
- Asks about progress, status, or what to build next
- Wants to decompose a large initiative into smaller pieces
- Mentions "expand", "generate specs", or "suggest slices"

## Planning Hierarchy

```
Product          — high-level initiative (problem, target state, success criteria)
  Capability     — functional domain within product (13-section spec, layer, scope)
    Feature      — deliverable unit (6-section model: user story, acceptance criteria, scope)
      ├── Interaction Stories — behavioral intent (actor, steps, acceptance criteria)
      │     ├── wireframe_refs → concrete screen/element references
      │     ├── acceptance_criteria → given/when/then → test plans
      │     └── slice_ids → which slices implement this story
      └── Slices — structural decomposition (layer, delivers, depends_on)
            ├── story_ids → which stories this slice serves
            └── Spec — implementation contract (interfaces, behavior, tests)
```

Products and capabilities are for large initiatives that need structured decomposition. Features can exist standalone or within a capability. Both paths converge to slices and specs.

**Interaction Stories** are a parallel artifact on Features. They describe *what the user experiences* while slices describe *how to build it*. Stories and slices cross-reference via many-to-many links (`slice_ids` on stories, `story_ids` on slices).

### Recommended Entity Sequence

Follow this order when planning. Each level provides the context needed by the next:

```
1. Product       — define the initiative (problem, target state, success criteria)
2. Capabilities  — decompose into functional domains
3. Inventory     — scope each capability (problem, scope_in/out, dependencies, acceptance criteria)
4. Features      — identify deliverable units per capability
5. Stories       — describe user interactions (expand from inventory via expand_stories)
6. Slices        — decompose into buildable units (expand from inventory via expand_slices)
7. Specs         — generate implementation contracts (expand from slices via expand_specs)
```

**Inventory is the bridge between "what" and "how."** Without it, stories and slices are written against implicit scope, causing boundary questions to surface mid-implementation. For small capabilities this is acceptable; for products with many capabilities, always create inventories first.

## Domains

The planning system operates across seven domains:

### product — Initiative Management

Top-level container for large initiatives.

| Action | What it does |
|--------|-------------|
| `create` | Create product with problem statement, target state, success criteria |
| `list` | List products with status and capability counts |
| `get` | Show product details with progress rollup |
| `update` | Update product fields |
| `delete` | Delete product (cascades — confirm with user) |
| `summary` | Full dashboard: progress, health score, bottlenecks, critical path |

**REST API:** `POST/GET/PATCH/DELETE /api/planning/products`, `GET /api/planning/products/{id}/summary`
**Query functions:** `createProduct`, `listProducts`, `getProduct`, `updateProduct`, `deleteProduct` from `core/koji/queries/planning-queries.ts`
**Schemas:** `ProductSchema`, `CreateProductSchema` from `core/koji/schemas/planning.ts`
**Algorithms:** `getProductProgress`, `calculateProductProgress`, `deriveProductStatus` from `core/planning/`

### capability — Functional Domain Decomposition

Capabilities are the primary unit of decomposition within a product. Each contains a 13-section spec designed for AI agent consumption.

| Action | What it does |
|--------|-------------|
| `create` | Create capability with layer, scope, dependencies |
| `list` | List capabilities for a product |
| `get` | Show capability with spec content and linked features |
| `update` | Update capability fields or spec content |
| `delete` | Delete capability |
| `spec` | Generate or regenerate the 13-section spec |
| `validate` | Check spec completeness (all 13 sections present) |
| `deps` | Show dependency graph (depends_on + provides_to) |

**13-Section Spec Format:**
1. Context, 2. Problem Statement, 3. Scope, 4. Dependencies, 5. Data Contracts,
6. File Locations, 7. Implementation Steps, 8. Error Handling, 9. Edge Cases,
10. Integration Points, 11. Verification Criteria, 12. Performance, 13. Security

**REST API:** `POST/GET/PATCH/DELETE /api/planning/capabilities`, `GET .../dependencies`, `GET .../slices`
**Query functions:** `createCapability`, `listCapabilities`, `getCapability`, `updateCapability`, `deleteCapability` from `core/koji/queries/planning-queries.ts`
**Schemas:** `CapabilitySchema`, `CreateCapabilitySchema` from `core/koji/schemas/planning.ts`
**Algorithms:** `deriveCapabilityStatus` from `core/planning/`

### feature — Deliverable Unit Management

Features are the working level of planning — standalone or linked to a capability.

| Action | What it does |
|--------|-------------|
| `create` | Create feature with 6-section model (user story, acceptance criteria, scope) |
| `list` | List features with status and slice counts |
| `get` | Show feature with inventory, slices, progress |
| `update` | Update feature fields or extension sections |
| `delete` | Delete feature |
| `summary` | Progress dashboard with slice/spec status breakdown |

**6-Section Feature Model** (stored in `feature_extensions`):
1. User Story, 2. Acceptance Criteria, 3. Scope In, 4. Scope Out,
5. Dependencies, 6. Slice Decomposition Guide

**REST API:** `POST/GET/PATCH/DELETE /api/planning/features`
**Query functions:** `createFeature`, `listFeatures`, `getFeature`, `updateFeature`, `deleteFeature` from `core/koji/queries/planning-queries.ts`
**Schemas:** `FeatureSchema` from `core/koji/schemas/planning.ts`
**Types:** `ParsedFeature`, `FeatureExtensionInput` from `core/planning/types.ts`

### story — Interaction Stories (Behavioral Intent)

Interaction stories describe what the user experiences. They are parallel artifacts on features — not a hierarchy level between features and slices. Stories are the primary input for AI coding agents to understand behavioral expectations and generate meaningful tests.

| Action | What it does |
|--------|-------------|
| `create` | Create story — requires `feature_id` and `title` (or `name`). `number` auto-assigns if omitted. Optional: `actor`, `intent`, `steps`, `acceptance_criteria`, `wireframe_refs` |
| `list` | List stories for a feature (ordered by number) |
| `get` | Show story with all fields |
| `update` | Update story fields or status |
| `delete` | Delete story |
| `list_by_slice` | List stories linked to a specific slice |

**Status lifecycle:** `draft` → `ready` → `verified`

**Required fields:** `feature_id`, `title` (or `name` alias). `number` auto-increments per feature if omitted.

**Key fields:**
| Field | Type | Purpose |
|-------|------|---------|
| `title` | string | **Required.** Story title (also accepts `name` as alias) |
| `number` | number | Sequence within feature — auto-assigned if omitted |
| `actor` | string | Who performs the interaction (e.g., "Developer", "Product Manager") |
| `intent` | string | What the actor wants to achieve |
| `preconditions` | string[] | What must be true before the interaction |
| `trigger_action` | string | What initiates the interaction |
| `steps` | `{actor, action, system_response}[]` | Step-by-step interaction flow |
| `acceptance_criteria` | `{given, when, then}[]` | Testable criteria mapping 1:1 to test cases |
| `wireframe_refs` | `{screen, element, notes?}[]` | Concrete screen/element references for AI agents |
| `slice_ids` | string[] | Which slices implement this story (many-to-many) |

**REST API:** `POST/GET/PATCH/DELETE /api/planning/stories`, `GET /api/planning/stories?feature_id=X`, `GET /api/planning/stories/by-slice/:sliceId`
**Query functions:** `createStory`, `getStory`, `listStories`, `listStoriesBySlice`, `updateStory`, `deleteStory` from `core/koji/queries/planning-queries.ts`
**Schemas:** `InteractionStorySchema`, `CreateInteractionStoryInput`, `UpdateInteractionStoryInput` from `core/koji/schemas/planning.ts`
**Types:** `ParsedInteractionStory`, `InteractionStep`, `AcceptanceCriterion`, `WireframeRef` from `core/planning/types.ts`
**Generator:** `generateStories`, `extractActor`, `storiesToCreateInput` from `core/planning/story-generator.ts`

### slice — Implementable Work Units

Slices are ordered, dependency-aware units within a feature.

| Action | What it does |
|--------|-------------|
| `create` | Create slice with number, layer, delivers, depends_on |
| `list` | List slices for a feature (ordered, with status) |
| `get` | Show slice with context (parent feature, capability) |
| `update` | Update slice fields or status |
| `suggest` | Analyze a capability or feature and suggest slice boundaries |

**Status lifecycle:** `pending` → `in_progress` → `implemented` → `verified`

**REST API:** `POST/GET/PATCH/DELETE /api/planning/slices`, `GET /api/planning/slices/by-number`
**Query functions:** `createSlice`, `listSlices`, `getSlice`, `updateSlice`, `deleteSlice` from `core/koji/queries/planning-queries.ts`
**Schemas:** `PlanningSliceSchema` from `core/koji/schemas/planning.ts`
**Algorithms:** `buildDependencyGraph`, `computeExecutionWaves`, `getAvailable`, `isBlocked` from `core/planning/`

### spec — Implementation Contracts

Specs are detailed implementation documents for individual slices. **All specs MUST be persisted to the planning database** via the REST API or query functions — never written as files to disk.

| Action | What it does |
|--------|-------------|
| `create` | Create spec for a slice number |
| `list` | List specs for a feature |
| `get` | Show spec content and status |
| `update` | Update spec content or status |
| `generate` | Generate spec from slice context (full or abbreviated) |

**Storage:** Specs are stored in the `specs` table with fields: `feature_id`, `slice_number`, `title`, `purpose`, `content` (markdown), `layer`, `status`, `frontmatter` (JSON metadata).

**Persistence — MANDATORY:**
- Use `POST /api/planning/specs` with `{ feature_id, slice_number, title, purpose, content, layer, status }`
- Or use `createSpec()` from `core/koji/queries/planning-queries.ts`
- **NEVER** write spec content as markdown files to disk
- The `content` field holds the full spec as markdown (interfaces, behaviors, errors, tests)
- The `frontmatter` field holds structured metadata as JSON (e.g., `{ "templateType": "full", "sections": [...] }`)

**Status lifecycle:** `draft` → `review` → `approved` → `implemented`
**Transition enforcement:** `isValidSpecTransition`, `getAllowedTransitions` from `core/planning/spec-transitions.ts`

**Spec hierarchy — two levels:**

| Level | Stored via | Purpose |
|-------|-----------|---------|
| **Capability spec** | `update_capability` with `spec_content` field | High-level design: 13-section format covering architecture, interfaces, data models, cross-cutting concerns. Defines *what* a capability provides. |
| **Slice spec** | `create_spec` with `feature_id` + `slice_number` | Implementation contract: per-slice detail covering interfaces, behavior, errors, tests. Defines *how* to build one slice. |

Capability specs are authored first during planning. Slice specs are generated later (manually or via `expand_specs`) and reference the capability spec for context. They are stored in different tables — `spec_content` is a text field on the capabilities table, while slice specs live in the `specs` table.

**Slice spec templates:**

**Full spec sections:** Purpose, Layer Assignment, Interfaces, Data Models, Behavior (Given/When/Then), Error Handling, Dependencies, Integration Points, Configuration, Test Scenarios

**Abbreviated spec** (for CRUD/adapters): Purpose, Interface, Behavior, Errors, Tests

**Wiring spec sections:** Purpose, Registration Order (what registers and in what sequence), Startup/Shutdown Lifecycle, Configuration Loading, Dependency Injection, Health Checks, Error Recovery (what happens when a dependency fails to initialize)

**Test spec sections:** Purpose, Test Matrix (which slices get unit tests, which flows get integration tests), Fixtures and Helpers, Coverage Targets, Test Data Strategy

### expand — Bulk Expansion Operations

The core intelligence of the planning system. Expand takes artifacts at one level and generates the next level down.

| Action | What it does |
|--------|-------------|
| `expand_stories` | Feature extension → interaction stories with actor, steps, acceptance criteria |
| `expand_slices` | Inventory/feature → ordered slices with dependencies and cross-cutting detection |
| `expand_specs` | Generate specs for all ready slices (pending slices with deps met) |

### batch — Bulk Creation

Create multiple entities in a single tool call. Each item in the `items` array uses the same fields as the single-create command. Returns per-item success/failure.

| Action | What it does |
|--------|-------------|
| `batch_create_stories` | Create multiple stories. Set `feature_id` at top level or per item. |
| `batch_create_slices` | Create multiple slices. Set `feature_id` at top level or per item. |

**Expand stories process:**
1. Read feature and its extension (user_story, scope_in, acceptance_criteria)
2. Extract actor from user_story text ("As a [Actor]..." pattern)
3. Map each scope_in item to a story title
4. Distribute acceptance criteria across stories round-robin
5. Map wireframe refs by index when available
6. Generate TODO placeholders for agent refinement (intent, preconditions, steps)
7. Persist stories via `POST /api/planning/stories`
8. Return generated stories for review

**REST API:** `POST /api/planning/expand/stories` with `{ feature_id }`
**Generator:** `generateStories`, `storiesToCreateInput` from `core/planning/story-generator.ts`

**Required cross-cutting slices:** Every feature MUST include these two slices in addition to domain slices:

1. **Wiring slice** (last domain slice number, `integration` layer) — App bootstrap, registration, route mounting, dependency injection, lifespan hooks. Depends on all other slices. Ensures "it works in isolation but not together" issues are caught. Title convention: `"Wire {feature name}"`.
2. **Test slice** (final slice number, `integration` layer) — Unit tests for each domain slice, integration tests for cross-slice flows, test fixtures and helpers. Depends on the wiring slice. Title convention: `"Test {feature name}"`.

These slices prevent the common failure mode where individual slices pass in isolation but the feature doesn't work end-to-end. The wiring slice is where fetcher registration, route mounting, config loading, and startup sequencing live. The test slice is where the test suite lives — not scattered across domain slices.

**Expand slices process:**
1. Read feature inventory (problem, scope, dependencies)
2. Detect cross-cutting patterns (signals appearing 3+ times)
3. Create foundation slices for cross-cutting concerns (early numbers, core layer)
4. Create remaining slices ordered by: hard deps → risk reduction → value → efficiency
5. Assign layers: data → domain → service → api → ui
6. Map dependencies between slices
7. Append wiring slice (depends on all domain slices) and test slice (depends on wiring slice)
8. Compute execution waves via `computeExecutionWaves`

**Expand specs process:**
1. Find ready slices via `getAvailable` (pending + all deps implemented)
2. For each ready slice, read dependent specs for context
3. Generate full or abbreviated spec based on complexity
4. **Persist each spec to DB** via `POST /api/planning/specs` with filled-in content (not TODO templates)
5. Set spec status to `draft`
6. Report what was generated and what's still blocked

**Expand patterns process:**
1. Query all specs for a feature
2. Scan for repeated interfaces, error types, validation patterns
3. If pattern appears in 3+ specs → create cross-cutting slice + spec
4. Update affected slices to depend on the new cross-cutting slice

**Algorithms:** `computeExecutionWaves`, `getAvailable`, `getBlockers`, `buildDependencyGraph` from `core/planning/`

### status — Planning Dashboard

Show progress across the entire planning hierarchy.

| Action | What it does |
|--------|-------------|
| _(default)_ | Show overview: products, features, progress, blockers, recommended next |
| `<id>` | Show detailed status for a specific entity |

**Output includes:**
- Progress rollup (percent complete at each level)
- Health score via `getHealthScore`
- Blocked items with reasons via `getBlockers`
- Critical path via `computeCriticalPath`
- Recommended next action via `getRecommendedNext`
- Layer breakdown via `calculateLayerBreakdown`

**Algorithms:** `calculateProgress`, `calculateAggregateProgress`, `getHealthScore`, `getRecommendedNext`, `computeCriticalPath`, `getBottlenecks`, `buildRollupChain` from `core/planning/`

## Context Inference

The skill resolves ambiguity automatically to reduce the number of IDs users need to provide:

### Resolution Rules

1. **Single product** → use it without asking
2. **Single feature in scope** → use it without asking
3. **Name match** → if user says "auth", resolve to the feature/capability named "auth" (if unique)
4. **Recent context** → if a product/feature/capability was discussed earlier in conversation, use it
5. **Parent inference** → `slice suggest` on a capability implies the capability's product
6. **Ambiguous** → present options and ask (max 5, with IDs)

### Examples

```
User: "show me the slices"
→ If 1 feature: list slices for that feature
→ If multiple: "Which feature? [1] auth [2] dashboard [3] settings"

User: "expand slices for auth"
→ Resolve "auth" to feature named "auth" or containing "auth"
→ If unique match: proceed
→ If ambiguous: "Did you mean [1] user-auth (feature) or [2] auth-middleware (capability)?"

User: "what should I build next"
→ Run getRecommendedNext across all features
→ Show the available slice with highest priority
```

## Quality Gates Integration

Before status transitions, the skill checks quality gates from `core/planning/gates/`:

| Transition | Gate | What it checks |
|-----------|------|---------------|
| spec: draft → review | `specReadyGate` | All required sections present |
| spec: review → approved | (manual review) | User confirms spec quality |
| slice: pending → in_progress | `dependencyCheckerGate` | All dependency slices implemented |
| slice: in_progress → implemented | (verification) | Tests pass, diagnostics clean |

**Gate infrastructure:** `GateRegistry`, `runGates`, `runSequence` from `core/planning/gates/`

## Supporting Documentation

- `expansion-levels.md` — Detailed patterns for each expansion level
- `cross-cutting.md` — How to detect and document cross-cutting patterns
- `status-tracking.md` — Status conventions, transitions, and verification

## Output Contract

> This contract is the interface between layers. If this skill is wrapped by an agent (L2), callers will parse these formats to build their reports. Do not change this structure without updating any corresponding agent or command.

### CRUD Operations (create, get, update, delete, list)

```
STATUS: SUCCESS

**Domain:** <domain name>
**Action:** <action name>
**Entity:** <entity type> <id or name>

<formatted entity details or list>
```

### Expand Operations

```
STATUS: SUCCESS

**Domain:** expand
**Action:** <slices|specs|patterns>
**Scope:** <feature or capability name>
**Generated:** <N> items
**Blocked:** <M> items (awaiting dependencies)

| # | Item | Layer | Status | Dependencies |
|---|------|-------|--------|-------------|
| 1 | slice/spec name | data | draft | — |
| 2 | slice/spec name | domain | blocked | slice-1 |

### Blocked Items
<list of items that could not be generated and why>
```

### Status Dashboard

```
STATUS: SUCCESS

**Domain:** status
**Scope:** <product/feature/all>

### Progress
<progress bars and counts>

### Health: <score>/100
<health breakdown>

### Blockers
<blocked items with reasons>

### Recommended Next
<highest priority available action>
```

### Failure

```
STATUS: FAILURE

**Domain:** <domain>
**Action:** <action>
**Error:** <what went wrong>
**Diagnostic:** <API unreachable, entity not found, validation error, etc.>
```
