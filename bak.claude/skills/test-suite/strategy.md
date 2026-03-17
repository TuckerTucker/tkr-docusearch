# Test Strategy Framework

## The Test Trophy

Prioritize by bug-catching ROI, not by count:

```
        ╭───────────╮
        │   E2E     │  Few — critical user journeys only
        ├───────────┤
        │           │
        │Integration│  Most tests live here — real behavior
        │           │
        ├───────────┤
        │   Unit    │  Complex logic, transforms, edge cases
        ├───────────┤
        │  Static   │  Types, linting (free — already running)
        ╰───────────╯
```

### Unit Tests

**What they cover:** Pure functions, algorithms, data transforms, validators,
parsers, formatters, state machines.

**When to write them:**
- Function has >2 branches or non-trivial logic
- Function is a pure transform (input → output)
- Edge cases matter (boundary values, empty inputs, overflow)

**When NOT to write them:**
- Thin wrappers around framework calls
- Simple getters/setters
- Code that only wires dependencies together (test via integration instead)

### Integration Tests

**What they cover:** Multiple components collaborating. Real I/O with controlled
dependencies. Database queries against test databases. HTTP handlers with real
routing. File system operations against temp directories.

**When to write them:**
- Component boundaries where bugs actually hide
- Data flows through multiple layers (handler → service → store)
- State machines with persistence (create → modify → query → delete)
- Anything involving serialization/deserialization roundtrips

**Key principle:** Use real implementations with controlled inputs, not mocks.
Replace only external services (third-party APIs, email providers). Use
in-memory or temp-directory implementations for storage, not mock objects.

### E2E Tests

**What they cover:** Complete user journeys from the system boundary. HTTP
requests to a running server. CLI invocations with real arguments. Full
workflow sequences a user would actually perform.

**When to write them:**
- Critical business flows (signup, purchase, deploy)
- Flows that cross multiple service boundaries
- Regression tests for bugs that slipped through lower layers

**When NOT to write them:**
- Testing individual field validation (unit test)
- Testing database queries (integration test)
- Every permutation of a feature (combinatorial explosion)

## Identifying What to Test

### The Risk Matrix

For each module, assess:

| Factor | Low | High |
|--------|-----|------|
| Complexity | Linear flow, few branches | Nested conditionals, state machines |
| Criticality | Cosmetic, logging | Auth, payments, data integrity |
| Change frequency | Stable, rarely touched | Active development, frequent changes |
| Bug history | No past issues | Repeated bug reports |

High-risk modules (high complexity + high criticality) get the most thorough
testing. Low-risk modules get smoke tests at most.

### Boundary Analysis

Most bugs live at boundaries:

- **Input boundaries:** Empty strings, zero, negative, max int, unicode, null
- **State boundaries:** Uninitialized, locked/unlocked, expired, full/empty
- **Integration boundaries:** Network timeout, partial response, malformed data
- **Concurrency boundaries:** Race conditions, deadlocks, stale reads

### Error Path Coverage

For every operation, test:
1. The happy path (expected input → expected output)
2. Validation failures (bad input → clear error)
3. Dependency failures (downstream service unavailable → graceful degradation)
4. Partial failures (operation succeeds partially → rollback or clear state)

## Test Organization

### Directory Structure (by convention)

```
src/
├── auth/
│   ├── login.ts
│   └── __tests__/
│       ├── login.test.ts          # Unit tests
│       └── login.integration.ts   # Integration tests
├── __tests__/
│   └── integration/               # Cross-module integration
│       └── auth-flow.test.ts
└── __tests__/
    └── e2e/                       # Full system E2E
        └── signup-flow.test.ts
```

Or colocated (both are fine — match the project convention):

```
src/
├── auth/
│   ├── login.ts
│   ├── login.test.ts              # Unit
│   └── login.integration.test.ts  # Integration
tests/
├── integration/
└── e2e/
```

### Naming Conventions

Test names should read as specifications:

```
// Good — describes scenario and outcome
"returns empty array when no results match filter"
"throws AuthError when token is expired"
"preserves data through lock/unlock cycle"

// Bad — describes implementation
"calls database query"
"returns true"
"handles error"
```

### Test Helpers

Shared helpers belong in a dedicated file (`helpers.ts`, `conftest.py`,
`testutil_test.go`). They should provide:

- **Factories:** Create valid test objects with sensible defaults and overrides
- **Fixtures:** Set up and tear down shared state (temp dirs, test DBs, servers)
- **Assertions:** Domain-specific assertion helpers that improve error messages
- **Stubs:** In-memory implementations of external dependencies (not mocks)
