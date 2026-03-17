---
name: context-kit-yaml
description: Generate context-kit YAML manifest and embed it in CLAUDE.local.md. Use when the project structure, dependencies, or architecture have changed and the manifest needs updating.
allowed-tools: [Bash, Read, Write, Edit, Grep, Glob]
source: tkr-kit
version: 4.0.0
---

# Context-Kit YAML Generator

> **Layer 1 — Capability.** This is a skill. It generates a comprehensive project manifest by combining deterministic CLI analysis with LLM semantic enrichment. The CLI script already orchestrates 9 analysis tools internally — agent-level parallelism would add overhead without benefit since all results must converge into a single LLM enrichment pass and a single output file.

## Composition

| Layer | Component | Relationship |
|-------|-----------|-------------|
| L3 Command | _not needed_ | single output file — no work to discover, no fan-out, no aggregation |
| L2 Agent | _not needed_ | CLI script handles tool orchestration internally |
| **L1 Skill** | **`context-kit-yaml` (this file)** | **runs CLI analysis + LLM enrichment → manifest** |

This skill stays L1-only because:
- The 9 analysis tools converge into one manifest — there are no independent work items to fan out
- The CLI script (`context-yaml.ts`) already runs tools in sequence with error handling
- The LLM enrichment step requires all tool results simultaneously — it cannot be parallelized

## When to Use

- Project structure, dependencies, or architecture have changed
- New modules, services, or views have been added
- User asks to update or regenerate the project manifest
- After significant refactoring or new feature additions
- User mentions context-kit, project manifest, or YAML generation

## Instructions

### Step 1: Run CLI Analysis

```bash
bun run .claude/skills/context-kit-yaml/scripts/context-yaml.ts --dir . --json --verbose
```

Executes 9 analysis tools and outputs structured JSON:
- `structure` — file tree with counts by type
- `dependencies` — package dependencies
- `testing` — test files, frameworks, coverage gaps
- `imports` — module relationships
- `config` — environment, ports, database
- `issues` — TODOs, FIXMEs, stubs
- `nav` — entry points, exports
- `api` — HTTP endpoints, MCP tools
- `design` — design tokens, components

Options:
- `--dir <path>` — target directory (default: cwd)
- `--output <path>` — output file (default: `_context-kit.yml`)
- `--json` — output JSON to stdout instead of YAML file
- `--tools <list>` — comma-separated subset of tools to run
- `--koji` — ingest results into Koji (requires running service)
- `--verbose` — show progress per tool

### Step 2: Review Raw Output

Read the JSON output. Note any tools that failed — their sections need manual attention.

### Step 3: Read Key Source Files

Read 3-5 key source files to understand architecture patterns, framework usage, and module organization. Use entry points from `nav` results as starting points.

#### 3a: Detect Stub vs. Wired Status

For adapter-pattern projects, scan adapter files:

```bash
grep -rn "not implemented\|throw.*stub\|no-op\|TODO.*wire\|TODO.*implement" core/*/adapter.ts
```

Classify each module:
- `wired: true` — real implementation connected
- `stub: true` — adapter exists but handlers are no-op/throw
- `partial: true` — some methods wired, some still stubbed

#### 3b: Enumerate Frontend Views and Routes

If the project has a frontend, read the router config to map views to routes. Add to `nav.views`:
```yaml
nav:
  views:
    plan: {route: "/execution/plan", file: dashboard/src/views/PlanView.vue, d: "Planning hierarchy"}
```

### Step 4: Enrich with LLM Sections

Add sections that require judgment:

- **`semantic`** — AI hints with `~` prefix keys: `~patterns`, `~conventions`, `~learning_path`, `~focus`, `~key_feature`
- **`arch`** — stack, patterns array, services (type/port/features), frontend/backend details
- **`nav` enrichment** — annotate entry points with why they matter, add reading order
- **`ops`** — paths, ports, scripts (read actual `package.json` values), dev commands

### Step 5: Write Final YAML

Two output targets:

1. **`CLAUDE.local.md`** — embedded under `# Project Manifest` heading in a fenced YAML block. This loads into the system prompt automatically.
2. **`_context-kit.yml`** — standalone file for programmatic consumption

Process for `CLAUDE.local.md`:
1. Read current file
2. Find `# Project Manifest` section
3. Replace from that heading through the end of the fenced code block
4. If no section exists, append it

---

## Format v14 Specification

### Required Sections

| # | Question | Section | Source |
|---|----------|---------|--------|
| 1 | Where do I start? | `nav` | CLI nav tool |
| 2 | What does it do? | `api` | CLI api tool |
| 3 | How do I configure it? | `config` | CLI config tool |
| 4 | How does it work? | `relations` | CLI imports tool |
| 5 | How do I test it? | `testing` | CLI testing tool |
| 6 | What's incomplete? | `issues` | CLI issues tool |
| 7 | What does it look like? | `design` | CLI design tool |
| 8 | How is it organized? | `struct` | CLI structure tool |
| 9 | What are the patterns? | `arch` | LLM enrichment |
| 10 | How do I run it? | `ops` | LLM enrichment |

Plus: `meta` (required), `deps`, `semantic` (optional).

### Section Schemas

#### `meta` (required)
```yaml
meta:
  kit: string          # Project identifier
  fmt: 14              # Format version (≥14)
  type: string         # development-toolkit | library | application | monorepo | fullstack-app
  desc: string         # Brief description
  ver: "1.0.0"         # Semantic version, quoted
  ts: "2025-01-01T00:00:00Z"  # ISO 8601 UTC, quoted
  status: string       # development | production-ready | archived | experimental
  entry: string        # Main entry point
  stack: string        # Tech stack summary
  cmds: [cmd1, cmd2]   # Key commands
  langs: {ts: 0.60, js: 0.25}  # Language distribution
```

#### `struct` — uses `_:` aggregate pattern
```yaml
struct:
  _: {n: 100, t: {ts: 50, js: 30, md: 10}}  # Root aggregate
  src:
    _: {n: 80, t: {ts: 50, js: 30}}
    components: {n: 20, t: {tsx: 20}, d: "UI components"}
```

Source vs. test separation — `n:` excludes test files, `tests:` reports them separately:
```yaml
planning: {n: 12, tests: 8, t: {ts: 20}, d: "Planning hierarchy", wired: true}
```

#### `deps`
```yaml
deps: &deps
  js: &js-deps
    prod:
      package: {v: "^1.0.0", d: "description"}
    dev:
      package: {v: "^1.0.0"}
```

#### `nav`
```yaml
nav:
  start:
    backend: path/to/main.ts
    frontend: path/to/app.tsx
  flows:
    auth: [routes/auth.ts, services/auth.ts, middleware/jwt.ts]
  views:
    dashboard: {route: "/", file: src/views/Dashboard.vue, d: "Main dashboard"}
  reading_order:
    - {p: path/to/file.ts, d: "Why this file matters"}
```

#### `api` — abbreviated fields
```yaml
api:
  endpoints:
    - {m: GET, p: /api/users, r: "User[]", q: "limit, offset"}
    - {m: POST, p: /api/users, b: UserCreate, r: User}
    # m=method, p=path, r=response, b=body, q=query, c=code, proc=processing notes
  models:
    User: {t: [id, name, email, created_at]}  # t=fields
```

#### `config`
```yaml
config:
  env:
    required: [VAR1]
    optional: [VAR2]
  ports: &ports {backend: 3000, frontend: 3001}
  db: {type: SQLite, path: data/app.db}
```

#### `relations`
```yaml
relations:
  frontend_backend:
    proto: HTTP/REST
    base: "http://localhost:3000"
    fmt: JSON
    services:
      - {svc: api, file: src/api/client.ts, calls: ["/api/users"]}
  backend_internal:
    pattern: "Routes → Services → DB"
```

#### `testing`
```yaml
testing:
  framework: vitest
  files: 8
  by_module:
    api: {files: 3, tested: true}
    services: {files: 2, tested: partial}
  gaps: ["E2E missing", "Frontend: 0 tests"]
```

#### `issues`
```yaml
issues:
  total: 21
  byTag: {TODO: 15, FIXME: 4, REVIEW: 2}
  high_priority:
    - {sev: HIGH, file: src/api.ts, line: 26, d: "Add JWT validation"}
  test_gaps: ["Frontend: 0 tests"]
```

#### `design`
```yaml
design:
  tokens:
    color: {count: 12, file: src/styles/tokens.css}
    spacing: {count: 5}
    typography: {count: 5}
  comp:
    Button: {p: [variant, size], file: src/components/Button.vue}
```

#### `arch` (LLM-generated)
```yaml
arch:
  stack: "TypeScript + React 18 + SQLite"
  patterns: ["IoC/DI", "Adapter pattern"]
  services:
    api: {type: "Express HTTP", port: 3000, features: ["REST", "MCP tools"]}
  frontend: {framework: "React 18", lang: TypeScript}
  backend: {framework: Express, lang: TypeScript, db: SQLite}
```

#### `ops` (LLM-generated)
```yaml
ops:
  paths:
    "src/": "Source code"
  ports: *ports
  scripts:
    test: "bun test"
    dev: "bun run src/server.ts"
```

#### `semantic` (LLM-generated)
```yaml
semantic:
  ~patterns: "IoC with adapter interfaces"
  ~conventions: "ES Modules, named exports, strict TypeScript"
  ~learning_path: "types.ts → adapter.ts → core module → CLI entry"
  ~focus: "AI-powered project analysis toolkit"
```

---

## Compression Rules

**Target: 40-60% token reduction.**

### Standard Abbreviations

| Full | Abbrev | Context |
|------|--------|---------|
| dependencies | `deps` | section |
| structure | `struct` | section |
| components | `comp` | design |
| description | `d` | struct, metadata |
| method | `m` | API |
| path | `p` | API |
| response | `r` | API |
| body | `b` | API |
| query | `q` | API |
| code | `c` | API status |
| service | `svc` | relations |
| protocol | `proto` | relations |
| format | `fmt` | relations |
| severity | `sev` | issues |

Never abbreviate domain-specific terms.

### Compact Notation

- Inline arrays for < 5 simple items: `cmds: ["bun test", "bun run dev"]`
- Inline objects for 2-4 properties: `{cov: "70%", tested: true}`
- `_:` aggregate for directory metadata
- `d:` for descriptions within aggregates

### Anchors & Aliases

Define before use. Reference with `*alias`:
```yaml
ports: &ports {api: 3000, dashboard: 5173}
ops:
  ports: *ports
```

### Strategic Omissions

- Omit `null`, empty arrays, empty objects
- Omit default values (e.g., status code 200)
- Omit zero counts

### Quoting

Always quote: ISO timestamps, version constraints with special chars, strings starting with YAML special characters.

---

## Output Contract

> This contract is the interface between layers. Currently L1-only, but if this skill is ever wrapped by an agent, callers will parse this format.

### Success
```
STATUS: SUCCESS

**Manifest:** _context-kit.yml
**Embedded:** CLAUDE.local.md (# Project Manifest)
**Tools:** 9/9 completed
**Sections:** <N> sections generated
**Size:** <lines> lines (<tokens> estimated tokens)

### Tool Results
| Tool | Status | Items |
|------|--------|-------|
| structure | PASS | <N> files |
| dependencies | PASS | <N> deps |
| testing | PASS | <N> test files |
| imports | PASS | <N> modules |
| config | PASS | <N> env vars |
| issues | PASS | <N> issues |
| nav | PASS | <N> entry points |
| api | PASS | <N> endpoints |
| design | PASS | <N> tokens |
```

### Partial Success
```
STATUS: PARTIAL

**Manifest:** _context-kit.yml
**Embedded:** CLAUDE.local.md (# Project Manifest)
**Tools:** <N>/9 completed (<M> failed)

### Tool Results
| Tool | Status | Items |
|------|--------|-------|
| structure | PASS | <N> files |
| dependencies | FAIL | error description |
| ... | ... | ... |

### Manual Attention Required
- <section>: <what needs manual review due to tool failure>
```

### Failure
```
STATUS: FAILURE

**Error:** <what went wrong>
**Diagnostic:** <CLI script error, missing dependencies, etc.>
```

## Quality Checklist

- [ ] `meta.fmt: 14` is set
- [ ] All timestamps and versions are quoted
- [ ] `struct` uses `_:` aggregate pattern with `n:` excluding tests
- [ ] Stub/wired status annotated on adapter-pattern modules
- [ ] Frontend views enumerated in `nav.views` with route mappings
- [ ] `ops.scripts` values match actual `package.json` commands
- [ ] API endpoints use abbreviated fields (m, p, r, b, q, c)
- [ ] Anchors defined before aliases
- [ ] No null/empty values
- [ ] `~` prefix on all semantic keys
- [ ] Target under 2000 lines
- [ ] Valid YAML 1.2 syntax
- [ ] CLAUDE.local.md `# Project Manifest` section updated
- [ ] `_context-kit.yml` standalone file also updated
