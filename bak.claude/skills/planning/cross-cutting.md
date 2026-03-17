# Cross-Cutting Concern Detection

How to identify and document patterns that span multiple slices.

## What Are Cross-Cutting Concerns?

Patterns, utilities, or contracts that:
- Appear in 3+ slices
- Would cause duplication if implemented separately
- Benefit from consistent implementation
- Form foundation that other slices depend on

## Detection

### During expand slices

Scan the feature inventory for repeated signals:

| Signal | Cross-Cutting Candidate |
|--------|------------------------|
| "validation" in 3+ places | Validation patterns |
| "error handling" repeated | Error handling spec |
| "auth" or "permissions" | Authorization layer |
| "logging" or "audit" | Observability patterns |
| Same data transformation | Utility patterns |
| "config" or "settings" shared | Configuration patterns |

### During expand patterns

Scan existing specs for repeated structures:

| Signal | Cross-Cutting Candidate |
|--------|------------------------|
| Same interface in 3+ specs | Shared interface spec |
| Same error type defined | Error types consolidation |
| Same utility imported | Utility extraction |
| Same validation logic | Validation consolidation |

## Storage

Cross-cutting patterns are regular slices and specs with special characteristics:
- **Early slice numbers** (1-5) — they're foundations
- **Layer: core or domain** — shared across layers above
- **Spec frontmatter:** `{ type: 'cross-cutting', used_by: [3, 5, 7] }`

## Process

### Creating Cross-Cutting Slices

1. Identify the pattern (3+ occurrences)
2. Create slice with early number, `layer: core`, no dependencies
3. Create spec with `frontmatter.type: 'cross-cutting'`
4. Update all affected slices to add dependency on the new slice
5. Update spec `frontmatter.used_by` with consumer slice numbers

### Cross-Cutting Spec Format

Abbreviated format focused on the shared interface:

- **Interface** — The shared types/functions
- **Usage** — When to use / when NOT to use
- **Examples** — Before/after showing the pattern
- **Consumers** — Table of slices using this pattern
- **Tests** — Test scenarios for the shared interface

## Common Patterns

| Pattern | Typical Contents |
|---------|-----------------|
| Error Handling | Error types, formatters, recovery strategies |
| Validation | Schema validation, type guards, error messages |
| Authorization | Permission checks, role definitions, guards |
| Logging | Structured log helpers, context propagation |
| Configuration | Config loading, validation, defaults |
| Serialization | JSON/YAML parsing, type coercion |
| Async Patterns | Retry logic, timeouts, cancellation |
| Testing Utilities | Factories, mocks, assertions |
