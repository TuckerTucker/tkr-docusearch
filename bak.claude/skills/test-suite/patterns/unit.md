# Unit Test Patterns

## Core Pattern: Arrange-Act-Assert

```
test("descriptive name of scenario and expectation", () => {
  // Arrange — set up inputs and expected outputs
  const input = createInput({ overrides });
  const expected = "result";

  // Act — call the function under test (one call)
  const result = functionUnderTest(input);

  // Assert — verify the outcome
  expect(result).toBe(expected);
});
```

One act per test. If you need multiple acts, you need multiple tests.

## When to Unit Test

Unit test when the function has:
- **Branching logic** — if/else, switch, ternary with >2 paths
- **Data transformation** — parsing, formatting, mapping, reducing
- **Validation rules** — input validation, business rules
- **Algorithms** — sorting, searching, scoring, calculating
- **State machines** — transitions, guards, terminal states

## Patterns

### Parameterized Tests

When testing the same logic with different inputs, use table-driven tests:

```typescript
// TypeScript/JS
const cases = [
  { input: "",        expected: false, desc: "empty string" },
  { input: "abc",     expected: false, desc: "no digits" },
  { input: "abc123",  expected: true,  desc: "mixed alphanumeric" },
  { input: "123",     expected: true,  desc: "digits only" },
];

for (const { input, expected, desc } of cases) {
  test(`isValid returns ${expected} for ${desc}`, () => {
    expect(isValid(input)).toBe(expected);
  });
}
```

```python
# Python
@pytest.mark.parametrize("input,expected,desc", [
    ("", False, "empty string"),
    ("abc", False, "no digits"),
    ("abc123", True, "mixed alphanumeric"),
])
def test_is_valid(input, expected, desc):
    assert is_valid(input) == expected
```

```go
// Go
func TestIsValid(t *testing.T) {
    cases := []struct {
        name     string
        input    string
        expected bool
    }{
        {"empty string", "", false},
        {"no digits", "abc", false},
        {"mixed", "abc123", true},
    }
    for _, tc := range cases {
        t.Run(tc.name, func(t *testing.T) {
            got := IsValid(tc.input)
            if got != tc.expected {
                t.Errorf("IsValid(%q) = %v, want %v", tc.input, got, tc.expected)
            }
        })
    }
}
```

### Boundary Value Testing

Test at the edges, not just the middle:

```
// For a function that accepts 1-100:
test("rejects 0 (below minimum)")
test("accepts 1 (minimum boundary)")
test("accepts 50 (typical value)")
test("accepts 100 (maximum boundary)")
test("rejects 101 (above maximum)")
```

### Error Path Testing

Every throwable function needs error path tests:

```typescript
test("throws TypeError for null input", () => {
  expect(() => process(null)).toThrow(TypeError);
});

test("throws ValidationError with field name for invalid email", () => {
  expect(() => validate({ email: "not-an-email" }))
    .toThrow(/email.*invalid/i);
});
```

### Pure Function Testing

Pure functions are the easiest to test. If your function isn't pure, consider
refactoring to separate the pure logic from the side effects:

```typescript
// Hard to test — mixed logic and I/O
function processOrder(orderId: string) {
  const order = db.findOrder(orderId);      // I/O
  const total = calculateTotal(order.items); // Pure logic
  const tax = calculateTax(total, order.region); // Pure logic
  db.updateOrder(orderId, { total, tax });   // I/O
}

// Easy to test — pure logic extracted
function calculateOrderTotals(items: Item[], region: string) {
  const total = calculateTotal(items);
  const tax = calculateTax(total, region);
  return { total, tax };
}
```

## Anti-Patterns

### Testing Implementation Details

```typescript
// BAD — breaks when you refactor internals
test("calls sortItems before calculateTotal", () => {
  const spy = jest.spyOn(utils, "sortItems");
  processOrder(order);
  expect(spy).toHaveBeenCalledBefore(calculateSpy);
});

// GOOD — tests observable behavior
test("total is correct regardless of item order", () => {
  const shuffled = shuffle(items);
  expect(calculateTotal(shuffled)).toBe(expectedTotal);
});
```

### Tautological Tests

```typescript
// BAD — tests that the mock returns what you told it to return
const mock = jest.fn().mockReturnValue(42);
expect(mock()).toBe(42); // This always passes. You tested jest, not your code.
```

### Over-Specific Assertions

```typescript
// BAD — breaks on any formatting change
expect(errorMessage).toBe("Error: Invalid email 'foo' at field 'user.email' on line 3");

// GOOD — tests the important parts
expect(errorMessage).toContain("Invalid email");
expect(errorMessage).toContain("foo");
```

### Duplicated Setup

```typescript
// BAD — every test repeats setup
test("test 1", () => {
  const db = new TestDB();
  const service = new UserService(db);
  // ...
});
test("test 2", () => {
  const db = new TestDB();
  const service = new UserService(db);
  // ...
});

// GOOD — shared setup via helper or beforeEach
function setup() {
  const db = new TestDB();
  return { db, service: new UserService(db) };
}
```
