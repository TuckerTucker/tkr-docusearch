# Go Testing

## Setup

No installation needed. Go has a built-in test framework.

```bash
go test ./...                    # Run all tests
go test ./pkg/auth/              # Run tests in package
go test -v ./...                 # Verbose output
go test -run TestSpecific ./...  # Run matching tests
go test -race ./...              # Enable race detector
go test -count=1 ./...           # Disable test caching
go test -cover ./...             # Show coverage
go test -coverprofile=cover.out ./... && go tool cover -html=cover.out  # HTML coverage
```

## Test Structure

```go
// user_test.go
package auth

import (
    "testing"
)

func TestCreateUser(t *testing.T) {
    store := NewInMemoryStore()
    service := NewUserService(store)

    user, err := service.Create("test@example.com")
    if err != nil {
        t.Fatalf("Create() error = %v", err)
    }
    if user.Email != "test@example.com" {
        t.Errorf("Email = %q, want %q", user.Email, "test@example.com")
    }
}
```

## Table-Driven Tests

The standard Go pattern for parameterized tests:

```go
func TestValidateEmail(t *testing.T) {
    tests := []struct {
        name    string
        input   string
        wantErr bool
    }{
        {"valid email", "user@example.com", false},
        {"empty string", "", true},
        {"no domain", "user@", true},
        {"no at sign", "userexample.com", true},
        {"valid with plus", "user+tag@example.com", false},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := ValidateEmail(tt.input)
            if (err != nil) != tt.wantErr {
                t.Errorf("ValidateEmail(%q) error = %v, wantErr %v",
                    tt.input, err, tt.wantErr)
            }
        })
    }
}
```

## Test Helpers

```go
// testutil_test.go (or internal/testutil/testutil.go)
package auth

import "testing"

func newTestService(t *testing.T) *UserService {
    t.Helper() // Marks this as a helper — errors report caller's line
    store := NewInMemoryStore()
    service := NewUserService(store)
    t.Cleanup(func() {
        store.Close()
    })
    return service
}
```

Key patterns:
- `t.Helper()` — error messages reference the test, not the helper
- `t.Cleanup()` — register cleanup that runs after test completes
- `t.TempDir()` — returns a temp directory, auto-cleaned

## Subtests

```go
func TestUserService(t *testing.T) {
    t.Run("Create", func(t *testing.T) {
        t.Run("with valid email", func(t *testing.T) { /* ... */ })
        t.Run("with duplicate email", func(t *testing.T) { /* ... */ })
    })

    t.Run("Delete", func(t *testing.T) {
        t.Run("existing user", func(t *testing.T) { /* ... */ })
        t.Run("nonexistent user", func(t *testing.T) { /* ... */ })
    })
}
```

## Interfaces for Testing

Go's implicit interfaces make testing natural:

```go
// Production interface
type Store interface {
    Get(key string) (string, error)
    Set(key, value string) error
    Delete(key string) error
}

// In-memory test implementation
type inMemoryStore struct {
    data map[string]string
}

func newInMemoryStore() *inMemoryStore {
    return &inMemoryStore{data: make(map[string]string)}
}

func (s *inMemoryStore) Get(key string) (string, error) {
    v, ok := s.data[key]
    if !ok {
        return "", ErrNotFound
    }
    return v, nil
}

func (s *inMemoryStore) Set(key, value string) error {
    s.data[key] = value
    return nil
}

func (s *inMemoryStore) Delete(key string) error {
    delete(s.data, key)
    return nil
}
```

## HTTP Handler Testing

```go
import (
    "net/http"
    "net/http/httptest"
    "strings"
    "testing"
)

func TestCreateHandler(t *testing.T) {
    store := newInMemoryStore()
    handler := NewHandler(store)

    body := strings.NewReader(`{"name":"test"}`)
    req := httptest.NewRequest("POST", "/api/items", body)
    req.Header.Set("Content-Type", "application/json")
    rec := httptest.NewRecorder()

    handler.ServeHTTP(rec, req)

    if rec.Code != http.StatusCreated {
        t.Errorf("status = %d, want %d", rec.Code, http.StatusCreated)
    }
}
```

## Integration Testing with httptest.Server

```go
func TestAPIFlow(t *testing.T) {
    store := newInMemoryStore()
    handler := NewHandler(store)
    srv := httptest.NewServer(handler)
    defer srv.Close()

    // Real HTTP requests
    resp, err := http.Post(srv.URL+"/api/items", "application/json",
        strings.NewReader(`{"name":"test"}`))
    if err != nil {
        t.Fatalf("POST error: %v", err)
    }
    defer resp.Body.Close()

    if resp.StatusCode != http.StatusCreated {
        t.Errorf("status = %d, want %d", resp.StatusCode, http.StatusCreated)
    }
}
```

## Conventions

### File Naming

- `foo_test.go` — tests for `foo.go` (same package)
- `foo_integration_test.go` — integration tests
- Build tags for slow/integration tests:

```go
//go:build integration
package auth
```

```bash
go test -tags=integration ./...
```

### Error Assertions

```go
// Check error type
var authErr *AuthError
if !errors.As(err, &authErr) {
    t.Fatalf("expected AuthError, got %T: %v", err, err)
}

// Check error wrapping
if !errors.Is(err, ErrNotFound) {
    t.Errorf("expected ErrNotFound, got: %v", err)
}
```

### Parallel Tests

```go
func TestParallel(t *testing.T) {
    t.Parallel() // Mark test as safe to run in parallel

    tests := []struct{ name string }{{"a"}, {"b"}, {"c"}}
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            t.Parallel() // Each subtest also runs in parallel
            // ...
        })
    }
}
```

### TestMain for Setup/Teardown

```go
func TestMain(m *testing.M) {
    // Setup (e.g., start test database)
    pool := setupTestDB()
    defer pool.Close()

    // Run tests
    code := m.Run()

    // Teardown
    os.Exit(code)
}
```

### Assertion Libraries (Optional)

Go's standard library has no assertion helpers. Options:
- **No library** — use `if` + `t.Errorf` (standard Go style)
- **testify** — `assert.Equal(t, expected, actual)` (popular, adds dependency)
- **is** — minimal assertion helper

Standard `if` + `t.Errorf` is preferred in most Go projects. Use `t.Fatalf`
for errors that should stop the test immediately.
