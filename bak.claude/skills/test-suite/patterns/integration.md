# Integration Test Patterns

## What Makes It an Integration Test

A test is an integration test when it exercises **multiple components collaborating
through real interfaces**. The components are real — not mocked — but the
environment is controlled.

```
Unit:        function(input) → output
Integration: handler → service → store → filesystem (all real, controlled env)
E2E:         HTTP client → running server → full stack
```

## Core Pattern: Real Components, Controlled Environment

```typescript
function createTestHarness(overrides?: Partial<Config>) {
  const tmpDir = mkdtempSync(join(tmpdir(), "test-"));
  const store = new Store({ dir: tmpDir, ...overrides });
  const service = new Service({ store });
  const router = createRouter({ service });

  return {
    store,
    service,
    router,
    tmpDir,
    cleanup() {
      rmSync(tmpDir, { recursive: true, force: true });
    },
  };
}
```

Key characteristics:
- **Real store**, but writing to a temp directory
- **Real service**, wired to the real store
- **Real router**, handling real Request objects
- **Cleanup** is explicit and reliable

## Patterns

### The Test Harness

Every integration test suite needs a harness that wires real components together
with controlled dependencies. The harness is the most important piece of test
infrastructure — invest time in making it ergonomic.

```typescript
// Good harness properties:
// 1. Sensible defaults — zero config for common cases
// 2. Override anything — full control when needed
// 3. Cleanup built in — no resource leaks
// 4. Type-safe — IDE autocompletion for everything returned

interface HarnessOptions {
  autoLockMs?: number;
  keychain?: KeychainProvider;
}

function createHarness(opts?: HarnessOptions) {
  const tmpDir = mkdtempSync(join(tmpdir(), "test-"));
  const keychain = opts?.keychain ?? new InMemoryKeychain();
  const store = new Store({
    dir: tmpDir,
    autoLockMs: opts?.autoLockMs ?? 300_000,
    keychain,
  });

  return { store, keychain, tmpDir, cleanup: () => rmSync(tmpDir, { recursive: true, force: true }) };
}
```

### Lifecycle Tests

Test state transitions end-to-end through the real component stack:

```typescript
test("data survives create → modify → lock → unlock cycle", async () => {
  const h = createHarness();
  try {
    await h.store.init(PASSWORD);
    await h.store.set("KEY", "original");
    await h.store.set("KEY", "modified");
    h.store.lock();
    await h.store.unlock(PASSWORD);
    expect(h.store.get("KEY")).toBe("modified");
  } finally {
    h.cleanup();
  }
});
```

### In-Memory Test Doubles (Not Mocks)

Replace external dependencies with **in-memory implementations** that honor the
same interface contract. These are NOT mocks — they have real behavior.

```typescript
// In-memory implementation — has real behavior
class InMemoryKeychain implements KeychainProvider {
  readonly entries = new Map<string, Buffer>();

  async store(service: string, account: string, data: Buffer): Promise<void> {
    this.entries.set(`${service}:${account}`, data);
  }

  async find(service: string, account: string): Promise<Buffer | null> {
    return this.entries.get(`${service}:${account}`) ?? null;
  }

  async remove(service: string, account: string): Promise<boolean> {
    return this.entries.delete(`${service}:${account}`);
  }
}

// Failing implementation — for testing error tolerance
class FailingKeychain implements KeychainProvider {
  async store(): Promise<void> { throw new Error("keychain unavailable"); }
  async find(): Promise<Buffer | null> { throw new Error("keychain unavailable"); }
  async remove(): Promise<boolean> { throw new Error("keychain unavailable"); }
}
```

Why in-memory doubles beat mocks:
- They have **real behavior** — you can inspect their state
- They **catch interface changes** — if the interface changes, they break
- They're **reusable** — every test uses the same doubles
- They **don't encode assumptions** — mocks encode what you think will happen

### HTTP Handler Testing

Test handlers with real Request/Response objects through the real router:

```typescript
// Helper to create real requests
function req(method: string, path: string, body?: unknown): Request {
  const init: RequestInit = { method, headers: { "content-type": "application/json" } };
  if (body) init.body = JSON.stringify(body);
  return new Request(`http://test${path}`, init);
}

test("POST /api/items creates item and returns 200", async () => {
  const h = createHarness();
  const res = await h.router.handle(req("POST", "/api/items", { name: "test" }));
  expect(res.status).toBe(200);
  const data = await res.json();
  expect(data.name).toBe("test");
});
```

### Testing Async Operations

For operations that involve timers, async callbacks, or delayed effects:

```typescript
test("auto-lock triggers after timeout", async () => {
  const h = createHarness({ autoLockMs: 50 });
  await h.store.init(PASSWORD);

  // Wait for auto-lock to trigger
  await new Promise(resolve => setTimeout(resolve, 100));

  expect(h.store.isLocked).toBe(true);
});
```

For operations that should complete before returning (not fire-and-forget):

```typescript
test("lock awaits async cleanup before returning", async () => {
  let cleanupDone = false;
  const slowCleanup = new SlowCleanupProvider({
    onCleanup: () => { cleanupDone = true; }
  });
  const h = createHarness({ cleanup: slowCleanup });

  await h.store.lock();
  expect(cleanupDone).toBe(true); // lock() must have awaited cleanup
});
```

### Cross-Component State Tests

Verify that state changes in one component are visible to another:

```typescript
test("changes made via service are visible via store", async () => {
  const h = createHarness();
  await h.service.createItem({ name: "test" });
  const items = h.store.list();
  expect(items).toContain("test");
});
```

## Anti-Patterns

### Over-Mocking

```typescript
// BAD — you're testing that mocks return what you told them to
const mockStore = { get: jest.fn().mockReturnValue("value") };
const service = new Service(mockStore);
const result = service.get("key");
expect(mockStore.get).toHaveBeenCalledWith("key"); // Tests wiring, not behavior

// GOOD — use real store, test real behavior
const store = new InMemoryStore();
await store.set("key", "value");
const service = new Service(store);
expect(service.get("key")).toBe("value"); // Tests actual retrieval
```

### Shared Mutable State Between Tests

```typescript
// BAD — tests depend on each other
let sharedStore: Store;
beforeAll(() => { sharedStore = new Store(); });

test("creates item", () => { sharedStore.set("key", "val"); });
test("reads item", () => { expect(sharedStore.get("key")).toBe("val"); }); // Depends on test 1

// GOOD — each test gets fresh state
let h: Harness;
afterEach(() => h.cleanup());

test("creates and reads item", () => {
  h = createHarness();
  h.store.set("key", "val");
  expect(h.store.get("key")).toBe("val");
});
```

### Missing Cleanup

```typescript
// BAD — temp files accumulate
test("writes to disk", () => {
  const dir = mkdtempSync("test-");
  writeFileSync(join(dir, "data.json"), "{}");
  // dir is never cleaned up
});

// GOOD — always clean up in afterEach or try/finally
afterEach(() => { if (tmpDir) rmSync(tmpDir, { recursive: true, force: true }); });
```

### Testing Internal State Instead of Behavior

```typescript
// BAD — reaches into internals
expect(service._cache.size).toBe(3);

// GOOD — tests observable behavior
expect(service.list()).toHaveLength(3);
```
