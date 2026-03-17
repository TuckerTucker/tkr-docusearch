# Jest

## Setup

```bash
npm install -D jest @types/jest ts-jest
```

```javascript
// jest.config.js
module.exports = {
  preset: "ts-jest",
  testEnvironment: "node",
  roots: ["<rootDir>/src"],
  testMatch: ["**/__tests__/**/*.test.ts"],
  collectCoverageFrom: ["src/**/*.ts", "!src/**/*.test.ts"],
};
```

## API

```typescript
import { describe, expect, it, beforeEach, afterEach, jest } from "@jest/globals";
// Or with globals: true, no import needed
```

### Test Structure

```typescript
describe("ModuleName", () => {
  let dep: Dependency;

  beforeEach(() => {
    dep = createTestDep();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("does something specific", () => {
    expect(result).toBe(expected);
  });
});
```

### Mocking

```typescript
// Function mock
const mockFn = jest.fn().mockReturnValue(42);
const asyncMock = jest.fn().mockResolvedValue("data");

// Spy on existing method
const spy = jest.spyOn(object, "method");
spy.mockImplementation(() => "mocked");

// Module mock
jest.mock("./module", () => ({
  functionName: jest.fn(),
}));

// Restore
jest.restoreAllMocks();  // In afterEach
```

### Async Testing

```typescript
it("resolves with data", async () => {
  const result = await fetchData();
  expect(result).toEqual({ id: 1 });
});

it("rejects with error", async () => {
  await expect(failingFn()).rejects.toThrow("message");
});
```

### Timer Mocking

```typescript
beforeEach(() => { jest.useFakeTimers(); });
afterEach(() => { jest.useRealTimers(); });

it("calls callback after delay", () => {
  const cb = jest.fn();
  setTimeout(cb, 1000);
  jest.advanceTimersByTime(1000);
  expect(cb).toHaveBeenCalled();
});
```

## Conventions

### File Structure

```
src/
├── module.ts
└── __tests__/
    └── module.test.ts
```

### Common Gotchas

**ESM support:** Jest's ESM support requires `--experimental-vm-modules` and
careful configuration. For ESM-first projects, consider Vitest instead.

**Transform issues:** TypeScript files need `ts-jest` or `@swc/jest`. Raw
`.ts` imports will fail without a transform.

**Module mock hoisting:** `jest.mock()` calls are hoisted to the top of the
file. Variables referenced in mock factories must be prefixed with `mock`:

```typescript
const mockQuery = jest.fn();
jest.mock("./database", () => ({ query: mockQuery }));
```

**Clearing vs restoring mocks:**
- `jest.clearAllMocks()` — resets call counts, not implementations
- `jest.resetAllMocks()` — clears + removes implementations
- `jest.restoreAllMocks()` — resets spies to original implementations

Always use `restoreAllMocks()` in `afterEach` to prevent mock leakage.
