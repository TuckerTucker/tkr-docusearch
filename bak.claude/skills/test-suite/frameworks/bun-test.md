# Bun Test Runner

## Setup

Bun has a built-in test runner. No installation needed.

```bash
bun test                    # Run all tests
bun test src/__tests__/     # Run tests in directory
bun test --watch            # Watch mode
bun test --timeout 10000    # Custom timeout
```

## API

```typescript
import { describe, expect, test, beforeEach, afterEach, beforeAll, afterAll } from "bun:test";
```

### Test Structure

```typescript
describe("module name", () => {
  let state: SomeState;

  beforeEach(() => {
    state = createFreshState();
  });

  afterEach(() => {
    state.cleanup();
  });

  test("describes scenario and expected outcome", () => {
    const result = doThing(state);
    expect(result).toBe(expected);
  });
});
```

### Assertions

```typescript
expect(value).toBe(exact);                    // Strict equality (===)
expect(value).toEqual(deep);                  // Deep equality
expect(value).toBeTrue();                     // === true
expect(value).toBeFalse();                    // === false
expect(value).toBeNull();                     // === null
expect(value).toBeUndefined();                // === undefined
expect(value).toBeDefined();                  // !== undefined
expect(value).toContain(item);               // Array/string contains
expect(value).toHaveLength(n);               // .length === n
expect(value).toBeGreaterThan(n);            // > n
expect(value).toMatch(/regex/);              // Regex match
expect(fn).toThrow();                        // Throws any error
expect(fn).toThrow(ErrorType);              // Throws specific type
expect(fn).toThrow(/message/);              // Throws with message match
```

### Async Tests

```typescript
test("async operation", async () => {
  const result = await asyncFunction();
  expect(result).toBe(expected);
});
```

## Conventions

### File Naming

```
src/__tests__/unit/module.test.ts
src/__tests__/integration/feature.test.ts
src/__tests__/e2e/flow.test.ts
```

### package.json Scripts

```json
{
  "scripts": {
    "test": "bun test",
    "test:unit": "bun test src/__tests__/unit/",
    "test:integration": "bun test src/__tests__/integration/",
    "test:e2e": "bun test src/__tests__/e2e/",
    "typecheck": "bunx tsc --noEmit"
  }
}
```

### Bun-Specific Features

**Bun.serve for E2E tests:**

```typescript
const server = Bun.serve({
  port: 0,  // OS-assigned port
  fetch(req) { return router.handle(req); },
});
const baseUrl = `http://localhost:${server.port}`;
// ... tests ...
server.stop();
```

**Bun.file for file assertions:**

```typescript
const file = Bun.file(path);
expect(await file.exists()).toBe(true);
expect(await file.text()).toContain("expected content");
```

**Bun.build for transpilation tests:**

```typescript
const result = await Bun.build({
  entrypoints: [filePath],
  target: "browser",
});
expect(result.success).toBe(true);
```

### Type Checking

Bun test does not type-check. Always run `tsc --noEmit` separately:

```bash
bun test && bunx tsc --noEmit
```

### No jest.fn() — Use Bun Equivalents

```typescript
import { mock, spyOn } from "bun:test";

const fn = mock(() => 42);
fn();
expect(fn).toHaveBeenCalled();

const spy = spyOn(object, "method");
object.method();
expect(spy).toHaveBeenCalled();
```

Prefer in-memory test doubles over mocks. Use mocks only for verifying
side-effect calls (e.g., "was the email sent?").
