# Coding Philosophy

> "We don't simply 'Make it work'—we 'Make it correctly'"

We aren't building MVPs or Prototypes. 
We are creating useful software applications that solve real problems.
We don't look for workarounds or quickfixes. 



## When Writing code
Ensure modularity, extensibility and testability by following Inversion of Control (IoC) design principles.

## Python:

Use:
- PEP 8 coding conventions
- `structlog` for structured JSON logging, capturing important events such as function entry/exit, errors, and state changes
- PEP 484 Type Hints conventions
- Docstrings follow Google Styleguide

## Go:

Use:
- Effective Go conventions (https://go.dev/doc/effective_go)
- `zerolog` for structured JSON logging, capturing important events such as function entry/exit, errors, and state changes
- Explicit error handling with wrapped context via `fmt.Errorf("context: %w", err)`
- GoDoc comment conventions (https://go.dev/doc/comment)
- Context propagation via `context.Context` as first parameter where applicable
- Table-driven tests with `t.Run()` subtests

## JavaScript/TypeScript:

Use:
- ES Modules (`"type": "module"` in package.json, `import/export` syntax)
- ESLint with recommended rules for consistent code style
- `pino` for structured JSON logging, capturing important events such as function entry/exit, errors, and state changes
- TypeScript strict mode (`"strict": true`) for maximum type safety
- JSDoc comments for JavaScript; TSDoc conventions for TypeScript
- Explicit return types on exported functions
- `async/await` over raw Promises; always handle rejections
- Named exports over default exports for better refactoring support

## Bash:

Use:
- Bash 3.2 compliance

# Policies
The following policies are designed to ensure clarity, consistency, and code safety for all work.

## 'No Assumptions' Policy
Never assume:
- File structure, imports, or dependencies without reading the files
- Coding patterns or conventions - verify against existing code
- Configuration values, paths, or environment variables
- API contracts, function signatures, or data structures

Before planning or implementing any task:
1. **Read the actual code** - don't infer from file names or assume common patterns
2. **Verify dependencies** - check imports, configuration files, and environment setup
3. **Validate paths and config** - ensure files, directories, and values actually exist
4. **Match existing patterns** - align with the project's actual coding style and architecture

## The No-Time-Estimates Policy
Time estimates from AI are unreliable and can create false expectations. 
Scope and complexity descriptions are more actionable.

Avoid false precision in effort predictions:
- Do not offer LOE, time estimates, or duration predictions
- Ignore any estimates in existing plans
- Avoid phrases like: "5 minutes", "a few hours", "quick", "should be fast"

Acceptable alternatives:
- Describe scope: "This involves 3 files and 2 API changes"
- Describe complexity: "This requires understanding the auth flow first"
- Describe dependencies: "This is blocked by X"

Only mention "quick-fix" or "quick-win" when the person explicitly asks.


# UX Philosophy

> "We do the work so the user doesn't have to."

The burden of effort shifts from user to system. 
Every interaction should feel effortless—not because the problem is simple, but because the complexity has been absorbed by the design.

The user experiences simplicity. We've hidden the machinery.

---

## What This Philosophy Means

### Absorbing Complexity
You take on the hard thinking, edge cases, and technical burden so the interface feels effortless. The work you do is invisible; the user only sees the result.

### Anticipating, Not Asking
Instead of presenting options and asking "what do you want?", we predict intent. 
Smart defaults, contextual actions, auto-saving.
The system just *does* the right thing.

### Eliminating Decisions
Every choice you force on a user is work. 
Your job is to reduce those decisions to only the ones that truly matter to them.

### Front-Loading Effort
The value comes from us spendin time solving a problem once so 10,000 users never encounter it. 
The ROI is in the invisibility of the work.

### Graceful Handling
Errors, edge cases, loading states, permissions
You handle these so users never have to troubleshoot or wonder what went wrong.

### In Practice:

#### State & Memory
- Remember where they left off
- Persist preferences without asking
- Never lose user work
- Auto-save continuously
- Undo instead of "Are you sure?"

#### Feedback & Errors
- Status and errors appear contextual to the action
- Constrain inputs so invalid states are impossible
- Disable instead of error after the fact
- Inline validation as they type, not on submit
- Show what went wrong and how to fix it, in place

#### Progressive Disclosure
- Show basics first, reveal advanced when needed
- Hide what's not relevant to current context
- Expand complexity on demand, not by default

#### Sensible Defaults
- Pre-fill with likely values
- Suggest based on recent actions or patterns
- Name things automatically (e.g., "Untitled Document 3")
- Select the most common option by default

#### Performance as UX
- Optimistic UI—assume success, rollback on failure
- Load content progressively, not all-or-nothing
- Background sync, not blocking saves
- Perceived speed matters as much as actual speed

#### Reduce Mode-Switching
- Edit in place, not in modals
- Inline actions over navigation
- Keep context visible during operations
- Avoid full-page transitions for single actions

#### Accessibility
- Input-agnostic: mouse, keyboard, touch parity
- System adapts to user preferences (motion, contrast, size)
- Screen reader compatible by default

#### Error Prevention
- Make the right thing easy and the wrong thing hard
- Gray out unavailable actions, don't hide them
- Validate as they go, not at the end
- Confirm destructive actions with undo, not dialogs

### That means:
**NO Toast notifications** 
- forces context-switching to read status
**NO "Are you sure?" dialogs** 
- shifts responsibility instead of providing undo
**NO Auto-correct** 
- assumes system knows better than user
**NO Pagination for small datasets < 100 items**
- makes user work to see their data
**NO Required fields without indication**
- errors discovered after the fact
**NO Silent logout on inactivity**
- loses work and context without warning
**NO Console-only errors**
- user has no idea what went wrong


# Agentic Architecture

> "Skills provide capability. Agents provide isolation. Commands provide orchestration."

All agentic work in this project follows a three-layer composable architecture. Each layer has one job and delegates down. Every layer is independently testable, and they compose upward.

```
┌──────────────────────────────────────────────────────────────┐
│  L3 — COMMAND (Orchestrate)          .claude/commands/       │
│  Discover work, fan out agents, aggregate results            │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │  Agent 1 │  │  Agent 2 │  │  Agent 3 │  ...              │
│  │  Task A  │  │  Task B  │  │  Task C  │                   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                   │
│       │              │              │                        │
│  ┌────▼──────────────▼──────────────▼─────────────────────┐  │
│  │  L2 — AGENT (Scale)             .claude/agents/        │  │
│  │  Receive scoped task → invoke skill → enforce output   │  │
│  │  contract → report structured results                  │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │  L1 — SKILL (Capability)     .claude/skills/     │  │  │
│  │  │  Domain logic, tool invocation, raw capability   │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## Layer 1 — Skills (Capability)

Skills are the foundational layer. They encapsulate domain logic and tool invocation.

**Location:** `.claude/skills/<name>/SKILL.md`

**Rules:**
- A skill does one thing well — context analysis, planning CRUD, browser automation, wireframe generation
- Skills are invoked directly (by users or agents) via `/skill-name`
- Skills MUST define an **Output Contract** section specifying the structured format callers can expect
- Skills contain no orchestration logic — they don't spawn agents or fan out work
- Skills are stateless between invocations unless they explicitly persist to a store (Koji, filesystem)

**Output Contract Example:**
```markdown
## Output Contract

Returns structured markdown:
- **Status line:** `✅ SUCCESS` or `❌ FAILURE`
- **Summary:** 2-3 sentence description of what was done
- **Findings table:** `| # | Finding | Severity | File |`
- **Metrics:** key-value pairs relevant to the analysis
```

## Layer 2 — Agents (Scale)

Agents are thin wrappers around skills that provide isolation, structured reporting, and parallel execution.

**Location:** `.claude/agents/<name>.md`

**Rules:**
- An agent's only job: receive a scoped task, invoke the skill, enforce the output contract, report results
- Agents are thin — typically under 50 lines of markdown config. No business logic.
- Agents MUST return the output format defined in their Report section — this is what makes aggregation possible at L3
- Agents handle their own setup and teardown (create directories, open sessions, close sessions)
- On failure, agents capture diagnostic context (console errors, stack traces) and report structured failure — they do not retry or escalate
- Multiple agent instances can run in parallel when the skill supports it

**Agent Frontmatter:**
```yaml
---
name: <agent-name>
description: <when to use, keywords>
model: <sonnet|opus|haiku>
skills:
  - <skill-name>
---
```

**Agent Structure:**
```markdown
# <Agent Name>
## Purpose        — one sentence role definition
## Variables      — configurable inputs with defaults
## Workflow       — numbered steps: setup → execute → teardown → report
## Report         — exact output format (success and failure variants)
```

## Layer 3 — Commands (Orchestration)

Commands discover work, fan out agents in parallel, collect results, and aggregate reports.

**Location:** `.claude/commands/<name>.md`

**Rules:**
- Commands orchestrate — they do NOT execute domain logic directly
- Commands use TeamCreate/Task to spawn agents in parallel when work is parallelizable
- Commands discover work dynamically (glob for YAML, query the planning hierarchy, scan directories)
- Commands aggregate agent reports into summary tables with overall pass/fail status
- Commands handle agent timeouts and partial failures gracefully — one agent failing does not abort the run
- Commands clean up after themselves (TeamDelete, shutdown requests)

**Command Phases:**
1. **Discover** — find the work items (files, stories, entities, dimensions)
2. **Spawn** — create team, create tasks, launch agents in parallel
3. **Collect** — receive agent reports (auto-delivered via messages), parse results
4. **Report** — aggregate into summary markdown with status, table, and failure details

## When to Use Each Layer

| Scenario | Layer | Example |
|----------|-------|---------|
| Run a single analysis or action | L1 Skill | `/repo-review` for one dimension |
| Execute a scoped task with structured output | L2 Agent | `review-agent` runs security analysis, returns findings table |
| Fan out parallel work and aggregate | L3 Command | `/full-review` spawns 9 review agents, collects all findings |
| Direct user interaction, ad-hoc | L1 Skill | `/planning product create "X"` |
| CI or repeatable workflow | L3 Command | `/ui-review` discovers YAML stories, validates all in parallel |

## Composability Principle

Each layer is independently testable:
- Test a skill directly: `/context-kit-yaml`
- Spawn a single agent: `Task tool → subagent_type: review-agent`
- Run full orchestration: `/full-review`

Layers delegate down, never sideways or up. A command never calls another command. An agent never spawns another agent. A skill never orchestrates agents.

# Project Manifest

```yaml
meta:
  kit: tkr-docusearch
  fmt: 14
  type: fullstack-app
  desc: "Local document search with Shikomi multimodal embeddings, Koji hybrid database, two-stage semantic search, and native Metal GPU architecture"
  ver: "0.9.0"
  ts: "2026-03-17T02:00:00Z"
  status: development
  entry: src/api/server.py
  stack: "Python 3.10+ (FastAPI) + React 19 (Vite) + Koji + Shikomi"
  cmds: [scripts/start-all.sh, scripts/stop-all.sh, scripts/status.sh, scripts/setup.sh]
  langs: {py: 0.51, js: 0.13, jsx: 0.12, ts: 0.10, tsx: 0.05, css: 0.07, sh: 0.02}

struct:
  _: {n: 470, t: {py: 173, js: 43, jsx: 53, ts: 30, tsx: 11, css: 28, sh: 11}}
  src:
    _: {n: 103, t: {py: 103}, d: "Python backend — FastAPI + ML pipeline"}
    api: {n: 10, t: {py: 10}, d: "FastAPI routes and models"}
    config: {n: 9, t: {py: 9}, d: "App configuration (Koji, Shikomi, LLM, URLs)"}
    core: {n: 8, t: {py: 8}, d: "Core types, exceptions, utils, testing mocks"}
    embeddings: {n: 5, t: {py: 5}, d: "Shikomi gRPC client, embedding generation"}
    mcp_server: {n: 5, t: {py: 5}, d: "MCP tool server"}
    processing: {n: 48, t: {py: 48}, d: "Document parsing (Docling), ASR (Whisper), embedding pipeline"}
    research: {n: 10, t: {py: 10}, d: "LLM-powered research with LiteLLM + MLX"}
    search: {n: 2, t: {py: 2}, d: "Two-stage semantic search (KojiSearch)"}
    storage: {n: 5, t: {py: 5}, d: "Koji hybrid database client"}
    utils: {n: 4, t: {py: 4}, d: "Shared utilities"}
  frontend:
    _: {n: 176, t: {jsx: 53, tsx: 11, js: 41, ts: 30, css: 26}, d: "React 19 SPA"}
    src:
      components: {n: 53, d: "UI components"}
      features: {n: 18, d: "Feature modules (library, details)"}
      views: {n: 5, t: {jsx: 5}, d: "Page-level views"}
      hooks: {n: 22, d: "Custom React hooks"}
      services: {n: 7, d: "API client services"}
      stores: {n: 4, d: "Zustand state stores"}
      utils: {n: 16, d: "Utility functions"}
      contexts: {n: 1, d: "React contexts (TitleContext)"}
      types: {n: 2, d: "TypeScript type definitions"}
      constants: {n: 3, d: "App constants"}
      config: {n: 1, d: "Frontend configuration"}
    e2e: {n: 5, t: {js: 5}, d: "Playwright E2E tests"}
  tests: {n: 70, t: {py: 70}, d: "Backend pytest suite"}
  scripts: {n: 11, t: {sh: 11}, d: "Dev/ops shell scripts"}

deps:
  py:
    prod:
      fastapi: {v: ">=0.104.0", d: "REST API framework"}
      uvicorn: {v: ">=0.24.0", d: "ASGI server"}
      torch: {v: ">=2.8.0", d: "PyTorch ML runtime"}
      transformers: {v: ">=4.30.0", d: "Hugging Face transformers"}
      pyarrow: {v: ">=14.0.0", d: "Koji hybrid database interface"}
      grpcio: {v: ">=1.60.0", d: "gRPC client (Shikomi)"}
      protobuf: {v: ">=4.25.0", d: "Protocol buffers"}
      docling: {v: ">=2.55.0", d: "Document parsing (PDF, Office, etc.)"}
      litellm: {v: ">=1.0.0", d: "LLM provider abstraction"}
      mlx-lm: {v: ">=0.26.3", d: "Apple Silicon local inference"}
      structlog: {v: ">=23.1.0", d: "Structured logging"}
      pydantic: {v: ">=2.0.0", d: "Data validation"}
      watchdog: {v: ">=3.0.0", d: "File system watcher"}
      python-multipart: {v: ">=0.0.6", d: "File upload support"}
      mutagen: {v: ">=1.47.0", d: "Audio metadata"}
    dev:
      pytest: {v: ">=7.4.0"}
      pytest-asyncio: {v: ">=0.21.0"}
      pytest-cov: {v: ">=4.1.0"}
      ruff: {v: ">=0.1.0"}
      mypy: {v: ">=1.0.0"}
  js:
    prod:
      react: {v: "^19.1.1", d: "UI framework"}
      react-dom: {v: "^19.1.1", d: "React DOM"}
      react-router-dom: {v: "^7.9.4", d: "Client-side routing"}
      "@tanstack/react-query": {v: "^5.90.5", d: "Server state management"}
      zustand: {v: "^5.0.8", d: "Client state management"}
      react-markdown: {v: "^10.1.0", d: "Markdown rendering"}
      clsx: {v: "^2.1.1", d: "Classname utility"}
    dev:
      vite: {v: "^7.1.7", d: "Build tool"}
      vitest: {v: "^4.0.3", d: "Test runner"}
      "@playwright/test": {v: "^1.56.1", d: "E2E testing"}
      typescript: {v: "^5.8.3"}
      eslint: {v: "^9.36.0", d: "Linting"}

nav:
  start:
    backend: src/api/server.py
    frontend: frontend/src/main.jsx
    config: .env.example
  views:
    library: {route: "/", file: frontend/src/views/LibraryView.jsx, d: "Document library grid"}
    details: {route: "/details/:id", file: frontend/src/views/DetailsView.jsx, d: "Document detail with bounding boxes"}
    research: {route: "/research", file: frontend/src/views/ResearchView.jsx, d: "AI research Q&A interface"}
    research-explore: {route: "/research-explore", file: frontend/src/views/ResearchExploreView.jsx, d: "Experimental research UI"}
    local-inference: {route: "/local-inference", file: frontend/src/views/LocalInferenceView.jsx, d: "Local MLX inference test"}
  reading_order:
    - {p: src/api/server.py, d: "FastAPI app factory, middleware, core routes"}
    - {p: src/api/research.py, d: "Research API — LLM-powered document Q&A"}
    - {p: src/embeddings/shikomi_client.py, d: "Shikomi gRPC embedding client"}
    - {p: src/storage/, d: "Koji hybrid database client"}
    - {p: src/search/, d: "Two-stage semantic search (KojiSearch)"}
    - {p: src/processing/, d: "Document ingestion — Docling + Whisper ASR"}
    - {p: frontend/src/App.jsx, d: "React router and layout"}

api:
  endpoints:
    - {m: GET, p: /health, d: "Health check"}
    - {m: GET, p: /status, d: "System status"}
    - {m: POST, p: /search, d: "Semantic document search"}
    - {m: GET, p: /search, d: "Search (GET variant)"}
    - {m: POST, p: /upload, d: "Document upload + processing"}
    - {m: GET, p: /processing/{doc_id}, d: "Processing status"}
    - {m: GET, p: /stats/search, d: "Search performance stats"}
    - {m: GET, p: /api/documents, d: "List documents"}
    - {m: GET, p: /api/document/{doc_id}, d: "Get document"}
    - {m: DELETE, p: /api/document/{doc_id}, d: "Delete document"}
    - {m: POST, p: /api/document/{doc_id}/reprocess, d: "Reprocess document"}
    - {m: GET, p: /api/document/{doc_id}/download, d: "Download document"}
    - {m: GET, p: /api/document/{doc_id}/markdown, d: "Get markdown content"}
    - {m: POST, p: /api/research/ask, d: "Research Q&A with LLM"}
    - {m: POST, p: /api/research/context-only, d: "Retrieve context without LLM"}
    - {m: POST, p: /api/research/local-inference, d: "Local MLX inference"}
    - {m: GET, p: /api/research/health, d: "Research API health"}
    - {m: GET, p: /api/research/models, d: "Available LLM models"}
  schemas:
    BoundingBox: {t: [left, bottom, right, top]}
    PageStructure: {t: [doc_id, page, headings, tables, pictures, code_blocks, formulas]}
    HeadingInfo: {t: [text, level, page, section_path, bbox]}

config:
  env:
    required: [KOJI_DB_PATH, SHIKOMI_GRPC_TARGET]
    optional: [SHIKOMI_USE_MOCK, OPENAI_API_KEY, LLM_PROVIDER, LLM_MODEL, ASR_ENABLED, ASR_BACKEND, ASR_MODEL, LOG_LEVEL, DEVICE, UPLOADS_DIR, MAX_FILE_SIZE_MB, SUPPORTED_FORMATS, ALLOWED_ORIGINS]
  ports: &ports
    backend: 8000
    worker: 8002
    shikomi: 50051
    research-api: 8004
    frontend: 3333
  db: {type: Koji, d: "Hybrid SQL + vector + graph database via PyArrow"}
  embeddings: {type: Shikomi, d: "gRPC embedding service (multi-vector colnomic)"}

relations:
  frontend_backend:
    proto: HTTP/REST
    base: "http://localhost:8000"
    fmt: JSON
    services:
      - {svc: api, file: frontend/src/services/, calls: ["/search", "/upload", "/api/documents", "/api/research/ask"]}
  backend_internal:
    pattern: "Routes → Services → Shikomi (embeddings) → KojiSearch → Koji DB"
  service_mesh:
    pattern: "All services run natively (no Docker). Startup: Shikomi → Worker → Research API → Frontend"

testing:
  backend:
    framework: pytest
    files: 70
    config: pyproject.toml
    cmd: "pytest"
    coverage: ">=70%"
    by_module:
      api: {files: 4, tested: true}
      embeddings: {tested: true}
      processing: {files: 17, tested: true}
      search: {tested: true}
      storage: {files: 5, tested: true}
      research: {files: 7, tested: true}
      mcp_server: {tested: true}
      config: {files: 1, tested: true}
      integration: {files: 4, tested: true}
      e2e: {files: 4, tested: true}
  frontend:
    framework: vitest
    config: frontend/vitest.config.ts
    cmd: "cd frontend && npm test"
    by_module:
      components: {tested: true}
      hooks: {tested: true}
      utils: {tested: true}
      services: {tested: true}
      features: {tested: true}
    e2e:
      framework: playwright
      files: 5
      cmd: "cd frontend && npm run test:e2e"

issues:
  total: 4
  byTag: {TODO: 4}

design:
  tokens:
    color: {count: 106, file: frontend/src/styles/global.css, d: "OKLCH design tokens via CSS custom properties"}
    spacing: {count: 10}
    typography: {count: 13}
    shadows: {count: 7}
    transitions: {count: 3}
    z-index: {count: 6}
  system: "OKLCH color space with 5 themes (kraft-paper, blue-on-black, notebook, graphite, gold-on-blue)"

arch:
  stack: "Python 3.10+ (FastAPI/Uvicorn) + React 19 (Vite) + Koji + Shikomi"
  patterns: ["IoC/DI", "Feature-based frontend modules", "Two-stage semantic search", "Native Metal GPU", "gRPC embedding service"]
  services:
    backend: {type: "FastAPI HTTP", port: 8000, features: ["REST API", "Document processing", "Search", "Upload"]}
    worker: {type: "Processing worker", port: 8002, features: ["Docling parsing", "Whisper ASR", "File uploads"]}
    shikomi: {type: "gRPC embedding service", port: 50051, features: ["Multi-vector embeddings", "Mock mode"]}
    research-api: {type: "FastAPI HTTP", port: 8004, features: ["LLM Q&A", "Context retrieval", "Local MLX inference"]}
    frontend: {type: "Vite dev server", port: 3333, features: ["React SPA", "HMR"]}
  frontend: {framework: "React 19", lang: "JSX/TSX", router: "react-router-dom v7", state: "Zustand + TanStack Query"}
  backend: {framework: FastAPI, lang: Python, db: Koji}
  ml:
    embeddings: {model: "Shikomi (colnomic)", d: "Multimodal document embeddings via gRPC service"}
    asr: {model: "Whisper (MLX)", d: "Audio transcription with Metal GPU acceleration"}
    llm: {providers: ["OpenAI via LiteLLM", "Local MLX"], d: "Research Q&A generation"}

ops:
  paths:
    "src/": "Python backend source"
    "frontend/": "React frontend"
    "tests/": "Backend test suite"
    "scripts/": "Dev/ops scripts"
    "data/": "Runtime data (uploads, Koji DB)"
    "bin/": "Native binaries (shikomi-worker)"
  ports: *ports
  scripts:
    setup: "scripts/setup.sh"
    start: "scripts/start-all.sh"
    stop: "scripts/stop-all.sh"
    status: "scripts/status.sh"
    test-backend: "pytest"
    test-frontend: "cd frontend && npm test"
    test-e2e: "cd frontend && npm run test:e2e"
    dev-frontend: "cd frontend && npm run dev"
    build-frontend: "cd frontend && npm run build"

semantic:
  ~patterns: "IoC with dependency injection, feature-based frontend modules, two-stage semantic search via Koji"
  ~conventions: "Python PEP 8 + structlog + type hints; React JSX with Zustand stores; ES Modules"
  ~learning_path: "server.py → storage/ (Koji) → embeddings/ (Shikomi) → search/ → processing/ → frontend App.jsx → views/"
  ~focus: "Local-first document intelligence — upload, parse, embed, search, research with AI"
  ~key_feature: "Shikomi gRPC embeddings + Koji hybrid DB enable visual+text document understanding with bounding box overlays"
```
