# Vitest

## Setup

```bash
npm install -D vitest
```

```json
// package.json
{ "scripts": { "test": "vitest", "test:run": "vitest run" } }
```

```typescript
// vitest.config.ts
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    globals: true,           // Optional: global describe/test/expect
    environment: "node",     // or "jsdom" for DOM tests
    include: ["src/**/*.test.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov"],
    },
  },
});
```

## API

```typescript
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
```

### Key Differences from Jest

- `vi.fn()` instead of `jest.fn()`
- `vi.spyOn()` instead of `jest.spyOn()`
- `vi.mock()` instead of `jest.mock()`
- `vi.useFakeTimers()` / `vi.useRealTimers()`
- Native ESM support — no transform issues
- HMR-powered watch mode

### Assertions

Same as Jest plus:

```typescript
expect(value).toSatisfy(predicate);    // Custom predicate
expect(promise).resolves.toBe(value);  // Resolved value
expect(promise).rejects.toThrow();     // Rejected value
```

### Concurrent Tests

```typescript
describe.concurrent("parallel tests", () => {
  it("test 1", async () => { /* runs in parallel */ });
  it("test 2", async () => { /* runs in parallel */ });
});
```

### In-Source Testing

Vitest supports tests inline with source code (opt-in):

```typescript
// src/utils.ts
export function add(a: number, b: number) { return a + b; }

if (import.meta.vitest) {
  const { test, expect } = import.meta.vitest;
  test("add", () => { expect(add(1, 2)).toBe(3); });
}
```

### Snapshot Testing

```typescript
expect(result).toMatchSnapshot();          // File snapshot
expect(result).toMatchInlineSnapshot(`"expected"`);  // Inline
```

Use sparingly. Prefer explicit assertions. Snapshots are appropriate for
serialized output (HTML, JSON structures) where the exact format matters.

## Conventions

### File Structure

```
src/
├── module.ts
├── module.test.ts        # Colocated unit tests
tests/
├── integration/          # Multi-module tests
└── e2e/                  # Full-system tests
```

### Mocking Modules

```typescript
vi.mock("./database", () => ({
  query: vi.fn().mockResolvedValue([]),
}));
```

Prefer dependency injection over module mocking. Module mocks are brittle
and hide coupling issues.

### Type-Safe Mocks

```typescript
const mockFn = vi.fn<[string, number], boolean>();
mockFn.mockReturnValue(true);
```
