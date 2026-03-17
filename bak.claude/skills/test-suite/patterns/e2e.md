# E2E Test Patterns

## What Makes It an E2E Test

E2E tests exercise the system from its **public boundary** — the same interface
a real user or client would use. For a web API, that means HTTP requests to a
running server. For a CLI, that means spawning the process with real arguments.

```
Integration: router.handle(fakeRequest) → response
E2E:         fetch("http://localhost:PORT/api/...") → response
```

The difference: E2E tests include real networking, real server startup, real
request parsing, and real response serialization.

## Core Pattern: Real Server, Real Requests

```typescript
let server: Server;
let baseUrl: string;
let tmpDir: string;

beforeEach(() => {
  tmpDir = mkdtempSync(join(tmpdir(), "e2e-"));
  const result = createServer({ port: 0, dataDir: tmpDir });
  server = result.server;
  baseUrl = `http://localhost:${server.port}`;
});

afterEach(() => {
  server.stop();
  rmSync(tmpDir, { recursive: true, force: true });
});

test("complete user journey: signup → configure → use", async () => {
  // Step 1: Create account
  const signupRes = await fetch(`${baseUrl}/api/signup`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ email: "user@test.com", password: "secure-pw" }),
  });
  expect(signupRes.status).toBe(200);

  // Step 2: Configure
  // ...

  // Step 3: Use the feature
  // ...
});
```

Key characteristics:
- **Port 0** — OS assigns a free port, no conflicts
- **Temp directory** — isolated data, no cross-test contamination
- **Real fetch** — actual HTTP through the network stack
- **Full cleanup** — server stopped, files removed

## Patterns

### User Journey Tests

Each E2E test should represent a **complete user journey**, not an isolated
endpoint test. Think in terms of user stories:

```typescript
test("new user onboarding: create account → add data → lock → unlock → verify", async () => {
  // This IS a user journey — sequential steps a real user would take
  const createRes = await api("POST", "/api/accounts", { password: "pw" });
  expect(createRes.status).toBe(200);

  await api("POST", "/api/data/KEY", { value: "important" });
  await api("POST", "/api/lock");
  await api("POST", "/api/unlock", { password: "pw" });

  const dataRes = await api("GET", "/api/data/KEY");
  const data = await dataRes.json();
  expect(data.value).toBe("important");
});
```

### Server Restart Simulation

Test that state persists across server restarts:

```typescript
test("data persists across server restart", async () => {
  // Create data
  await api("POST", "/api/data/KEY", { value: "persist-me" });
  await api("POST", "/api/lock");

  // Restart: stop old server, start new one with same data directory
  server.stop();
  const result2 = createServer({ port: 0, dataDir: tmpDir });
  server = result2.server;
  baseUrl = `http://localhost:${server.port}`;

  // Verify data survived
  await api("POST", "/api/unlock", { password: "pw" });
  const res = await api("GET", "/api/data/KEY");
  expect((await res.json()).value).toBe("persist-me");
});
```

### API Helper

Reduce boilerplate with a typed fetch wrapper:

```typescript
async function api(
  method: string,
  path: string,
  body?: unknown,
): Promise<Response> {
  const init: RequestInit = {
    method,
    headers: { "content-type": "application/json" },
  };
  if (body !== undefined) {
    init.body = JSON.stringify(body);
  }
  return fetch(`${baseUrl}${path}`, init);
}
```

### Concurrent Operation Tests

Verify the system handles concurrent requests correctly:

```typescript
test("concurrent requests don't interfere", async () => {
  // Create multiple resources concurrently
  await Promise.all([
    api("POST", "/api/items/a", { value: "aaa" }),
    api("POST", "/api/items/b", { value: "bbb" }),
    api("POST", "/api/items/c", { value: "ccc" }),
  ]);

  // Read all concurrently
  const [a, b, c] = await Promise.all([
    api("GET", "/api/items/a").then(r => r.json()),
    api("GET", "/api/items/b").then(r => r.json()),
    api("GET", "/api/items/c").then(r => r.json()),
  ]);

  expect(a.value).toBe("aaa");
  expect(b.value).toBe("bbb");
  expect(c.value).toBe("ccc");
});
```

### Error Response Tests

Verify the server returns correct HTTP status codes and error formats:

```typescript
test("returns 404 for nonexistent resource", async () => {
  const res = await api("GET", "/api/items/nonexistent");
  expect(res.status).toBe(404);
  const body = await res.json();
  expect(body.success).toBe(false);
  expect(body.error).toContain("not found");
});

test("returns 400 for invalid request body", async () => {
  const res = await fetch(`${baseUrl}/api/items`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: "not json",
  });
  expect(res.status).toBe(400);
});
```

### Static File Serving Tests

For servers that serve both API and static files:

```typescript
test("serves index.html for root path", async () => {
  const res = await fetch(`${baseUrl}/`);
  expect(res.status).toBe(200);
  expect(res.headers.get("content-type")).toContain("text/html");
});

test("serves SPA fallback for unknown paths", async () => {
  const res = await fetch(`${baseUrl}/some/client/route`);
  expect(res.status).toBe(200);
  expect(res.headers.get("content-type")).toContain("text/html");
});
```

### Large Payload Tests

Verify the server handles realistic payload sizes:

```typescript
test("handles large request bodies", async () => {
  const largeValue = "x".repeat(100_000);
  const res = await api("POST", "/api/items/large", { value: largeValue });
  expect(res.status).toBe(200);

  const getRes = await api("GET", "/api/items/large");
  const data = await getRes.json();
  expect(data.value).toHaveLength(100_000);
});
```

## Anti-Patterns

### Testing Every Endpoint in Isolation

```typescript
// BAD — these are endpoint tests, not E2E tests
test("POST /api/items returns 200", async () => { /* ... */ });
test("GET /api/items/:id returns 200", async () => { /* ... */ });
test("DELETE /api/items/:id returns 200", async () => { /* ... */ });

// GOOD — test the user journey
test("create → read → update → delete lifecycle", async () => { /* ... */ });
```

### Hardcoded Ports

```typescript
// BAD — fails when port is in use
const server = createServer({ port: 3000 });

// GOOD — OS assigns a free port
const server = createServer({ port: 0 });
```

### Missing Server Cleanup

```typescript
// BAD — server keeps running, port leaks
test("something", async () => {
  const server = createServer({ port: 0 });
  // test runs but server never stops
});

// GOOD — always stop in afterEach
afterEach(() => { server.stop(); });
```

### Sleep-Based Waiting

```typescript
// BAD — arbitrary sleep, flaky
await new Promise(r => setTimeout(r, 5000));
const res = await fetch(url);

// GOOD — poll with timeout, or test observable state
const res = await fetch(url);
expect(res.status).toBe(200); // If the server is ready, this works immediately
```

## CLI E2E Testing

For CLI tools, spawn the real process:

```typescript
import { spawn } from "child_process";

test("CLI prints help with --help flag", async () => {
  const proc = spawn("node", ["./cli.js", "--help"]);
  const output = await collectOutput(proc);
  expect(output.stdout).toContain("Usage:");
  expect(output.exitCode).toBe(0);
});

test("CLI exits with error for invalid input", async () => {
  const proc = spawn("node", ["./cli.js", "--invalid-flag"]);
  const output = await collectOutput(proc);
  expect(output.exitCode).not.toBe(0);
  expect(output.stderr).toContain("Unknown flag");
});
```
