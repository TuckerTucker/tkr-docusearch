# Status Tracking

Conventions for tracking planning artifact status.

## Status Lifecycles

### Product Status
`draft` → `active` → `completed` → `archived`

### Capability Status
`draft` → `in_progress` → `implemented` → `verified`

### Feature Status
`draft` → `planning` → `in_progress` → `completed` → `archived`

### Story Status
`draft` → `ready` → `verified`

### Slice Status
`pending` → `in_progress` → `implemented` → `verified`

### Spec Status
`draft` → `review` → `approved` → `implemented`

## Two-Layer Status Model

### Layer 1: Slice Status (Dashboard View)

| Status | Meaning | Trigger |
|--------|---------|---------|
| `pending` | Not started | Created via expand slices |
| `in_progress` | Being implemented | Spec approved, work started |
| `implemented` | Code complete | Tests pass, diagnostics clean |
| `verified` | Fully validated | All verification checks pass |

### Layer 2: Spec Status (Detail View)

| Status | Meaning | Next Step |
|--------|---------|-----------|
| `draft` | Being written | Submit for review |
| `review` | Ready for feedback | Approve or revise |
| `approved` | Locked for implementation | Implement |
| `implemented` | Code complete | Close out |

## Status Transitions

```
expand stories        → all stories: draft        (TODO placeholders)
refine stories        → story: ready              (acceptance criteria complete)
expand slices         → all slices: pending       (no specs yet)
expand specs          → slice: pending            spec: draft
user review           → slice: in_progress        spec: approved
implementation done   → slice: implemented        spec: implemented
verification pass     → slice: verified           story: verified  (no spec change)
```

## Status Rollup

Status rolls up automatically through the hierarchy:

- **Feature status** derived from child slice statuses via `deriveFeatureStatus`
- **Capability status** derived from child feature statuses via `deriveCapabilityStatus`
- **Product status** derived from child capability statuses via `deriveProductStatus`

Use `buildRollupChain` from `core/planning/status-rollup.ts` for full chain.

## Dependency Validation

Before transitioning status, validate dependencies:

| Transition | Check |
|-----------|-------|
| spec: draft → review | `specReadyGate` — all required sections present |
| spec: review → approved | Manual review by user |
| slice: pending → in_progress | `dependencyCheckerGate` — all dep slices implemented |
| slice: in_progress → implemented | Diagnostics clean, tests pass |

Use `isValidSpecTransition` and `getAllowedTransitions` from `core/planning/spec-transitions.ts`.

## Progress Queries

| What | Function | Module |
|------|----------|--------|
| Feature progress | `getFeatureProgress` | `core/planning/artifact-store.ts` |
| Product progress | `getProductProgress` | `core/planning/artifact-store.ts` |
| Layer breakdown | `calculateLayerBreakdown` | `core/planning/progress-calculator.ts` |
| Health score | `getHealthScore` | `core/planning/progress-calculator.ts` |
| Recommended next | `getRecommendedNext` | `core/planning/progress-calculator.ts` |
| Available slices | `getAvailable` | `core/planning/dependency-graph.ts` |
| Blocked slices | `isBlocked` / `getBlockers` | `core/planning/dependency-graph.ts` / `topological-ordering.ts` |
| Critical path | `computeCriticalPath` | `core/planning/critical-path.ts` |
| Bottlenecks | `getBottlenecks` | `core/planning/critical-path.ts` |
