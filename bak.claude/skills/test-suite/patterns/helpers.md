# Test Helper Patterns

## Purpose

Test helpers eliminate duplication across test files and provide a consistent
vocabulary for setting up test scenarios. Good helpers make tests **shorter,
clearer, and less fragile**.

## What Belongs in Helpers

### Factories

Create valid test objects with sensible defaults. Override only what matters
for the specific test:

```typescript
const DEFAULTS = {
  name: "test-user",
  email: "test@example.com",
  role: "member",
};

function createUser(overrides?: Partial<User>): User {
  return { ...DEFAULTS, id: randomId(), ...overrides };
}

// Usage — only specify what the test cares about
const admin = createUser({ role: "admin" });
const user = createUser({ email: "specific@test.com" });
```

### Test Doubles (In-Memory Implementations)

Implement interfaces with in-memory behavior. These are **real implementations**
with inspectable state, not mock frameworks:

```typescript
class InMemoryStore implements Store {
  readonly data = new Map<string, string>();

  async get(key: string): Promise<string | undefined> {
    return this.data.get(key);
  }

  async set(key: string, value: string): Promise<void> {
    this.data.set(key, value);
  }

  async delete(key: string): Promise<boolean> {
    return this.data.delete(key);
  }
}
```

Also provide **failure-mode doubles** for testing error tolerance:

```typescript
class FailingStore implements Store {
  async get(): Promise<string | undefined> { throw new Error("store unavailable"); }
  async set(): Promise<void> { throw new Error("store unavailable"); }
  async delete(): Promise<boolean> { throw new Error("store unavailable"); }
}
```

### Test Harnesses

Wire real components together with controlled dependencies:

```typescript
export interface TestHarness {
  readonly store: InMemoryStore;
  readonly service: UserService;
  readonly router: Router;
  readonly tmpDir: string;
  cleanup(): void;
}

export function createHarness(opts?: Partial<Config>): TestHarness {
  const tmpDir = mkdtempSync(join(tmpdir(), "test-"));
  const store = new InMemoryStore();
  const service = new UserService({ store, ...opts });
  const router = createRouter({ service });

  return {
    store,
    service,
    router,
    tmpDir,
    cleanup: () => rmSync(tmpDir, { recursive: true, force: true }),
  };
}
```

### HTTP Helpers

For integration/E2E tests against routers or servers:

```typescript
/** Build a Request object for router-level testing */
export function req(method: string, path: string, body?: unknown): Request {
  const init: RequestInit = {
    method,
    headers: { "content-type": "application/json" },
  };
  if (body !== undefined) init.body = JSON.stringify(body);
  return new Request(`http://test${path}`, init);
}

/** Extract JSON body from Response */
export async function json(res: Response): Promise<unknown> {
  return res.json();
}

/** Fetch wrapper for E2E tests against a real server */
export async function apiFetch(
  baseUrl: string,
  method: string,
  path: string,
  body?: unknown,
): Promise<Response> {
  const init: RequestInit = {
    method,
    headers: { "content-type": "application/json" },
  };
  if (body !== undefined) init.body = JSON.stringify(body);
  return fetch(`${baseUrl}${path}`, init);
}
```

### Constants

Shared test values with descriptive names:

```typescript
export const PASSWORD = "test-password-123";
export const ADMIN_EMAIL = "admin@test.com";
export const EXPIRED_TOKEN = "eyJ...expired";
```

### Null Loggers

Suppress log output during tests:

```typescript
export function createNullLogger(): Logger {
  const noop = () => {};
  return {
    info: noop, warn: noop, error: noop, debug: noop,
    child: () => createNullLogger(),
  };
}
```

## What Does NOT Belong in Helpers

- **Test logic** — assertions, expectations, test flow
- **One-off setup** — if only one test uses it, keep it inline
- **Complex orchestration** — if the helper needs its own tests, it's too complex
- **Mock configuration** — mocks encode assumptions about implementation

## Organization

### Single helpers file for small projects

```
src/__tests__/helpers.ts
```

### Split by concern for larger projects

```
src/__tests__/
├── helpers.ts          # Re-exports everything
├── factories.ts        # Object factories
├── doubles.ts          # In-memory implementations
├── harness.ts          # Test harness setup
└── http-helpers.ts     # Request/response utilities
```

### Language-Specific Conventions

| Language | Convention |
|----------|-----------|
| TypeScript/JS | `__tests__/helpers.ts` or `test/helpers.ts` |
| Python | `conftest.py` (pytest auto-discovers fixtures) |
| Go | `testutil_test.go` in the package, or `internal/testutil/` |
| Rust | `tests/common/mod.rs` |

## Design Principles

1. **Sensible defaults, full overrides.** Factories provide valid defaults.
   Tests override only what's relevant to their scenario.

2. **Return values, don't set globals.** Helpers return what they create.
   Tests destructure what they need. No global mutable state.

3. **Cleanup is the caller's job.** Harnesses provide a `cleanup()` method.
   Tests call it in `afterEach` or `try/finally`. The helper doesn't
   auto-register cleanup because that hides resource management.

4. **Type everything.** Helpers are shared code — type safety prevents
   subtle bugs across many test files.

5. **Keep helpers simple.** If a helper needs more than 20 lines, question
   whether it's doing too much. If a helper needs its own tests, it
   should be production code, not test code.
