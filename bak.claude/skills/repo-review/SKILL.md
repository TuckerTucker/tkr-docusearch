---
name: repo-review
description: Analyze a single review dimension (security, quality, performance, accessibility, testing, documentation, architecture, dependencies, git-practices) against the codebase. Returns structured findings with severity, file locations, and a scored assessment. Use when user asks for code review, audit, or quality analysis.
allowed-tools: [Read, Glob, Grep, Bash]
source: tkr-kit
version: 2.0.0
---

# Repo Review

> **Layer 1 — Capability.** This is a skill. It performs code analysis for a single review dimension. It does NOT fan out across multiple dimensions — that belongs to Layer 3 (`full-review` command). It produces structured findings that the `review-agent` (L2) enforces and the command aggregates.

## Composition

| Layer | Component | Relationship |
|-------|-----------|-------------|
| L3 Command | `full-review` | discovers dimensions, fans out one review-agent per dimension, aggregates scores |
| L2 Agent | `review-agent` | wraps this skill with isolation + structured reporting for parallel execution |
| **L1 Skill** | **`repo-review` (this file)** | **analyzes one dimension, returns scored findings** |

## When to Use

- User asks for code review, audit, or quality analysis
- User mentions a specific dimension (security, testing, performance, etc.)
- User asks for "full review" or "comprehensive audit" → suggest `/full-review` command (L3)
- Agent invokes this skill with a specific DIMENSION parameter

## Dimensions

| Dimension | What It Checks |
|-----------|----------------|
| `security` | Secrets in code, injection vectors, auth gaps, CORS config, env handling |
| `quality` | Dead code, duplication, complexity, naming, error handling patterns |
| `performance` | N+1 queries, unbounded loops, missing indexes, large payloads, memory leaks |
| `accessibility` | ARIA attributes, keyboard navigation, color contrast, semantic HTML |
| `testing` | Coverage gaps, test quality, missing edge cases, assertion quality |
| `documentation` | Missing docs, stale docs, API docs, README completeness |
| `architecture` | Boundary violations, circular deps, coupling, cohesion, pattern consistency |
| `dependencies` | Outdated deps, unused deps, license issues, duplicate deps, security advisories |
| `git-practices` | Commit quality, branch hygiene, conventional commits, changelog |

## Instructions

### Step 1: Identify Dimension

Parse the DIMENSION from the prompt. If none specified, ask for clarification or default to `quality`.

### Step 2: Scope the Analysis

Determine which files to analyze based on dimension:

| Dimension | Primary Files | Secondary Files |
|-----------|--------------|-----------------|
| security | `core/**/*.ts`, `.env*`, `config/**` | `package.json` (deps with known CVEs) |
| quality | `core/**/*.ts`, `services/**/*.ts` | `mcp/tools/**/*.ts` |
| performance | `core/**/*.ts`, `services/**/*.ts` | DB queries, API handlers |
| accessibility | `dashboard/**/*.vue`, `dashboard/**/*.css` | component props, ARIA usage |
| testing | `**/*.test.ts`, `**/*.spec.ts` | source files without test counterparts |
| documentation | `**/*.md`, `**/adapter.ts` (JSDoc) | README, CLAUDE.md, inline comments |
| architecture | `core/**/adapter.ts`, `services/**/*.ts` | import graphs, boundary crossings |
| dependencies | `package.json`, `**/package.json` | lock files, vendor/ |
| git-practices | git log, git diff | commit messages, branch names |

### Step 3: Analyze

For each file in scope:
1. Read the file
2. Apply dimension-specific checks from the Dimension Checklist
3. Classify each finding by severity: `critical`, `high`, `medium`, `low`, `info`
4. Record file path and line number

### Step 4: Score

Calculate a dimension score (0-100):

| Severity | Weight | Deduction per finding |
|----------|--------|-----------------------|
| critical | 25 | -25 points |
| high | 10 | -10 points |
| medium | 5 | -5 points |
| low | 2 | -2 points |
| info | 0 | no deduction |

Score = max(0, 100 - total deductions). Cap at 0.

### Step 5: Format Output

Structure results per the Output Contract below.

## Dimension Checklists

### security
- [ ] No hardcoded secrets, API keys, or tokens in source
- [ ] Environment variables used for sensitive config
- [ ] Input validation on all external boundaries (API routes, form handlers)
- [ ] SQL/NoSQL injection prevention (parameterized queries)
- [ ] XSS prevention (output encoding, CSP headers)
- [ ] CORS configured restrictively (not `*` in production)
- [ ] Auth checks on protected routes
- [ ] No sensitive data in logs or error messages

### quality
- [ ] No dead code (unused exports, unreachable branches)
- [ ] No copy-paste duplication (>10 lines identical)
- [ ] Functions under 50 lines, files under 300 lines
- [ ] Consistent naming conventions (camelCase functions, PascalCase types)
- [ ] Error handling on all async operations
- [ ] No `any` types in TypeScript (strict mode violations)
- [ ] Named exports over default exports
- [ ] No console.log in production code

### performance
- [ ] No N+1 query patterns (loop with DB call inside)
- [ ] Bounded iteration (no unbounded while loops on external data)
- [ ] Pagination on list endpoints
- [ ] No synchronous file I/O in request handlers
- [ ] Response payloads under reasonable size limits
- [ ] No memory leaks (event listeners cleaned up, intervals cleared)

### accessibility
- [ ] Interactive elements have ARIA labels
- [ ] Keyboard navigation works (tab order, Enter/Space activation)
- [ ] Color is not the sole indicator of state
- [ ] Semantic HTML elements used (button, nav, main, not div-for-everything)
- [ ] Form inputs have associated labels
- [ ] Focus management on modals and dynamic content

### testing
- [ ] Every module has at least one test file
- [ ] Tests cover happy path and at least one error case
- [ ] No flaky patterns (timing-dependent, order-dependent)
- [ ] Assertions are specific (not just "doesn't throw")
- [ ] Test data is deterministic (no random values without seeds)
- [ ] Edge cases covered (empty input, boundary values, null/undefined)

### documentation
- [ ] README exists with setup instructions
- [ ] Exported functions have JSDoc/TSDoc
- [ ] API endpoints documented (parameters, responses, errors)
- [ ] Architecture decisions recorded (ADRs or inline)
- [ ] No stale docs (references to removed features or old APIs)

### architecture
- [ ] `core/` has no imports from `services/` or `mcp/` (boundary integrity)
- [ ] No circular dependencies between modules
- [ ] Adapter interfaces used at module boundaries (IoC)
- [ ] Consistent patterns across similar modules
- [ ] Single responsibility per module/file
- [ ] Dependencies flow inward (infrastructure → domain, not reverse)

### dependencies
- [ ] No outdated major versions (>1 major behind)
- [ ] No unused dependencies (installed but not imported)
- [ ] No duplicate dependencies (same package at multiple versions)
- [ ] License compatibility (no GPL in MIT projects, etc.)
- [ ] No known security advisories (`npm audit` / `bun audit` equivalent)

### git-practices
- [ ] Commits follow conventional format (`type(scope): description`)
- [ ] Commits are atomic (one logical change per commit)
- [ ] No large commits (>500 lines without justification)
- [ ] Branch names are descriptive
- [ ] No secrets in git history

## Output Contract

> This contract is the interface between layers. The `review-agent` (L2) passes this output through to its report. The `full-review` command (L3) parses the STATUS line and Score to build aggregated dashboards. Do not change this structure without updating the agent and command.

### Success
```
STATUS: SUCCESS

**Dimension:** <dimension name>
**Score:** <0-100>/100
**Scope:** <files analyzed count> files in <directories>
**Findings:** <N total> (<critical> critical, <high> high, <medium> medium, <low> low, <info> info)

| # | Finding | Severity | File | Line |
|---|---------|----------|------|------|
| 1 | Description of finding | high | path/to/file.ts | 42 |
| 2 | Description of finding | medium | path/to/other.ts | 18 |

### Top Recommendations
1. Most impactful fix
2. Second priority
3. Third priority
```

### No Findings
```
STATUS: SUCCESS

**Dimension:** <dimension name>
**Score:** 100/100
**Scope:** <files analyzed count> files in <directories>
**Findings:** 0

No issues found.
```

### Failure
```
STATUS: FAILURE

**Dimension:** <dimension name>
**Error:** <what went wrong — no files in scope, parse error, etc.>
**Diagnostic:** <details>
```

## Examples

### Example 1: Single dimension
```
/repo-review security
```
Analyzes security dimension, returns scored findings with file locations.

### Example 2: Default dimension
```
/repo-review
```
Defaults to `quality` dimension.

### Example 3: Scoped review
```
/repo-review testing core/planning/
```
Analyzes testing dimension scoped to the planning module only.
