# Expansion Levels

Patterns for expanding planning artifacts at each level of abstraction.

## Overview

```
Product + Capabilities     Vision level — what we're solving
        |
        v  capability spec / feature create
Feature + Inventory        Scope level — what we're building
        |
        v  expand stories
Interaction Stories        Behavioral level — what the user experiences
        |
        v  expand slices (enriched by stories)
Slices                     Work level — ordered implementable units
        |
        v  expand specs
Specs                      Contract level — implementation details
        |
        v  (orchestration / direct implementation)
Code                       Execution level
```

## Level 1: Feature Inventory

**Input:** Product description, capability spec, or raw requirements
**Output:** Feature with 6-section model

### 6-Section Feature Model

| Section | Purpose | Source |
|---------|---------|--------|
| User Story | Who benefits and how | Product problem_statement |
| Acceptance Criteria | Measurable outcomes | Product success_criteria |
| Scope In | What's included | Capability scope_in |
| Scope Out | What's excluded | Capability scope_out |
| Dependencies | What must exist first | Capability depends_on |
| Slice Decomposition Guide | Hints for slicing | Capability implementation_steps |

### When to Create Features

- **From capability:** Each capability typically produces 1-3 features
- **Standalone:** User describes a deliverable unit of work
- **From exploration:** Discovery reveals a needed feature

## Level 1.5: Interaction Stories

**Input:** Feature with 6-section model (user_story, scope_in, acceptance_criteria)
**Output:** Interaction stories with actor, steps, acceptance criteria, wireframe refs

Stories are a parallel artifact on features — they describe *what the user experiences* while slices describe *how to build it*. Stories and slices cross-reference via many-to-many links.

### Story Fields

| Field | Type | Description |
|-------|------|-------------|
| `number` | number | Sequential order within feature |
| `title` | string | Derived from scope_in items |
| `actor` | string | Extracted from user_story ("As a [Actor]...") |
| `intent` | string | What the actor wants to achieve |
| `preconditions` | string[] | What must be true before interaction |
| `trigger_action` | string | What initiates the interaction |
| `steps` | `{actor, action, system_response}[]` | Step-by-step interaction flow |
| `acceptance_criteria` | `{given, when, then}[]` | Testable criteria (maps 1:1 to test cases) |
| `wireframe_refs` | `{screen, element, notes?}[]` | Concrete screen/element references |
| `slice_ids` | string[] | Which slices implement this story |
| `status` | string | draft/ready/verified |

### Expansion Process

1. Extract actor from feature's `user_story` text
2. Map each `scope_in` item to a story title
3. Distribute `acceptance_criteria` across stories round-robin
4. Map wireframe refs by index when available
5. Generate TODO placeholders for steps, preconditions, intent
6. Persist stories via REST API or query functions

### Consumer: AI Coding Agents

Stories are designed primarily for AI agent consumption:
- `acceptance_criteria` with `{given, when, then}` maps directly to test case generation
- `wireframe_refs` with `{screen, element}` provides concrete UI anchors
- `steps` with `{actor, action, system_response}` defines behavioral contracts
- `slice_ids` links tell agents which structural work implements each behavior

### Feeding Into Slice Generation

When stories exist, they enrich slice generation:
- Story steps and acceptance criteria add behavioral text for cross-cutting pattern detection
- More behavioral context may surface additional foundation slices
- Generated slices can be linked back to stories via `story_ids`

## Level 2: Slices

**Input:** Feature with inventory/6-section model (optionally enriched by stories)
**Output:** Ordered slices with dependencies

### Ordering Methodology

| Priority | Criterion | Question |
|----------|-----------|----------|
| 1 | Hard dependencies | What must exist before this can work? |
| 2 | Cross-cutting | Does this pattern appear in 3+ places? |
| 3 | Risk reduction | Does this tackle an unknown early? |
| 4 | Value delivery | Does this produce something runnable? |
| 5 | Efficiency | Does this minimize context switching? |

### Layer Assignment

| Layer | Contains | Typical Dependencies |
|-------|----------|---------------------|
| data | Schemas, migrations, models | Nothing |
| domain | Business logic, validation | data |
| service | Orchestration, workflows | domain |
| api | HTTP routes, MCP tools | service, domain |
| ui | Components, views, interactions | api, domain |
| infra | Config, deployment, monitoring | Nothing |
| integration | E2E tests, glue code | All above |

### Cross-Cutting Detection

During slice generation, scan for signals appearing 3+ times:

| Signal | Pattern to Extract |
|--------|-------------------|
| "validation" repeated | Validation utilities slice |
| "error handling" repeated | Error types/formatting slice |
| "auth" or "permissions" | Authorization layer slice |
| "logging" or "audit" | Observability patterns slice |
| Same data transformation | Utility patterns slice |
| "config" or "settings" shared | Configuration slice |

Cross-cutting slices get early numbers (1-5) and `layer: core` or `layer: domain`.

### Slice Fields

| Field | Type | Description |
|-------|------|-------------|
| `number` | number | Unique order within feature |
| `name` | string | Short descriptive name (2-4 words) |
| `layer` | Layer | data/domain/service/api/ui/infra/integration |
| `status` | SliceStatus | pending/in_progress/implemented/verified |
| `delivers` | string[] | What's usable after this slice |
| `depends_on` | string[] | Slice numbers this depends on |
| `files` | string[] | Files this slice will create/modify |

## Level 3: Specs

**Input:** Slice with context (parent feature, dependent specs)
**Output:** Implementation contract

### Full Spec (10 sections)

Use for slices with complex logic, multiple components, or multiple integration points.

1. **Purpose** — One sentence: what and why
2. **Layer Assignment** — Component-to-layer mapping table
3. **Interfaces** — TypeScript interfaces
4. **Data Models** — Types and schemas
5. **Behavior** — Given/When/Then scenarios
6. **Error Handling** — Condition/Error/Recovery table
7. **Dependencies** — Required slices + cross-cutting patterns
8. **Integration Points** — Consumes/Provides tables
9. **Configuration** — Settings with defaults
10. **Test Scenarios** — Unit + integration test tables

### Abbreviated Spec (5 sections)

Use for CRUD, wrappers, adapters, or single-interface slices.

1. **Purpose** — One sentence
2. **Interface** — Primary interface only
3. **Behavior** — 2-3 Given/When/Then
4. **Errors** — Error conditions table
5. **Tests** — Test scenarios table

### Choosing Full vs. Abbreviated

| Criterion | Full Spec | Abbreviated |
|-----------|-----------|-------------|
| Components | Multiple | Single |
| Business logic | Complex | CRUD/passthrough |
| Integration points | Multiple | 0-1 |
| Configuration | Has settings | None |
| Performance concerns | Yes | No |

## Expansion Rules

### Inventory → Stories

1. Extract actor from user_story ("As a [Actor], I want...")
2. One story per scope_in item
3. Distribute acceptance criteria round-robin across stories
4. Map wireframe refs by index
5. Generate TODO placeholders for agent refinement
6. Every story has at least one acceptance criterion

### Stories → Slices (enriched)

1. Extract cross-cutting first (patterns in 3+ places)
2. Order by layer: data → domain → service → api → ui
3. Minimize dependencies: each slice depends on minimum required
4. One concern per slice: split multi-concern items
5. Every slice delivers something testable

### Slice → Spec

1. Read dependency specs first for context
2. Check cross-cutting specs for shared patterns to consume
3. Match interfaces to layer conventions
4. Every behavior has a test scenario
5. Every error has a recovery strategy
