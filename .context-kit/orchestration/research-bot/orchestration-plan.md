# Research Bot Parallel Orchestration Plan

**Created:** 2025-10-17
**Feature Goal:** AI Research Assistant with cited answers
**Max Agents:** 6
**Execution Model:** Wave-based with progressive validation
**Integration Strategy:** Interface-first, territorial boundaries

---

## Executive Summary

This orchestration plan coordinates 6 specialized agents working in parallel across 4 synchronous waves to deliver a complete research bot feature. The design emphasizes:

- **Zero file conflicts** through territorial ownership
- **Guaranteed integration** through interface contracts
- **Progressive validation** with quality gates
- **Maximum parallelism** (3-4 agents per wave)

**Estimated Timeline:** 4 waves (each agent works independently within waves)

---

## Component Decomposition

### Backend Components (Python)
1. **LiteLLM Client** - LLM inference wrapper
2. **Context Builder** - Search results → LLM prompt formatter
3. **Citation Parser** - LLM response → structured citations
4. **Research API** - FastAPI endpoint orchestrating the flow
5. **Configuration** - Settings, prompts, model selection

### Frontend Components (JavaScript)
6. **Research Page** - HTML structure and styling
7. **Answer Display** - Text rendering with citation badges
8. **Reference Cards** - Document reference UI component
9. **Highlighting Logic** - Bidirectional interaction handler
10. **API Client** - Frontend ↔ Backend communication

---

## Integration Points & Contracts

### Critical Interfaces

```
┌─────────────────┐
│  Frontend       │
│  (Wave 3)       │
└────────┬────────┘
         │ HTTP JSON
         ▼
┌─────────────────┐
│  Research API   │
│  (Wave 2)       │
└────────┬────────┘
         │ Python Function Calls
         ▼
┌─────────────────┐    ┌──────────────┐    ┌─────────────┐
│ Context Builder │───▶│ LiteLLM Client│───▶│Citation Parser│
│   (Wave 1)      │    │   (Wave 1)    │    │   (Wave 1)   │
└─────────────────┘    └───────────────┘    └──────────────┘
         │
         ▼
┌─────────────────┐
│ Existing Search │
│   (No changes)  │
└─────────────────┘
```

**Contract Files Created:**
- `integration-contracts/api-contract.md` - HTTP API specification
- `integration-contracts/context-builder-contract.md` - Python interface
- `integration-contracts/litellm-client-contract.md` - Python interface
- `integration-contracts/citation-parser-contract.md` - Python interface
- `integration-contracts/frontend-contract.md` - JS component interfaces

---

## Wave 1: Foundation Layer (3 Agents in Parallel)

**Goal:** Build independent backend services with no interdependencies

### Agent 1: LiteLLM Integration Agent
**Territory:** `src/research/litellm_client.py` (new file)

**Responsibilities:**
- Install and configure LiteLLM package
- Create `LiteLLMClient` class with model selection
- Implement `generate_answer(system_prompt, user_message)` method
- Add fallback routing (GPT-4 → Claude → GPT-3.5)
- Add error handling and retry logic
- Write unit tests with mocked LiteLLM responses

**Deliverables:**
- ✅ `src/research/litellm_client.py` - Standalone client
- ✅ `src/research/test_litellm_client.py` - Unit tests
- ✅ `.env.example` updates for API keys
- ✅ Documentation of model selection strategy

**Contract Compliance:**
- Implements `litellm-client-contract.md` interface
- No dependencies on other Wave 1 agents
- Testable in isolation with mocks

**Validation Criteria:**
- [ ] Can generate text from sample prompts
- [ ] Fallback routing works (mock primary failure)
- [ ] All tests pass
- [ ] No dependencies on context builder or citation parser

---

### Agent 2: Context Builder Agent
**Territory:** `src/research/context_builder.py` (new file)

**Responsibilities:**
- Create `build_llm_context(search_results: List[dict]) → str` function
- Decompress markdown from ChromaDB metadata
- Extract section/heading information
- Format as numbered document blocks
- Implement token counting and truncation
- Write unit tests with sample search results

**Deliverables:**
- ✅ `src/research/context_builder.py` - Context formatter
- ✅ `src/research/test_context_builder.py` - Unit tests
- ✅ Token management utilities
- ✅ Sample context templates

**Contract Compliance:**
- Implements `context-builder-contract.md` interface
- Uses existing `chroma_client.get_document_markdown()` (read-only)
- No dependencies on LiteLLM or citation parser

**Validation Criteria:**
- [ ] Converts search results to formatted context string
- [ ] Respects token limits (~10K tokens)
- [ ] Handles missing markdown gracefully
- [ ] All tests pass

---

### Agent 3: Citation Parser Agent
**Territory:** `src/research/citation_parser.py` (new file)

**Responsibilities:**
- Create `parse_citations(answer: str, sources: List[dict]) → dict` function
- Extract `[N]` markers with regex
- Map citations to source documents
- Validate citation numbers (no hallucinations)
- Extract character positions for highlighting
- Write unit tests with sample LLM responses

**Deliverables:**
- ✅ `src/research/citation_parser.py` - Parser module
- ✅ `src/research/test_citation_parser.py` - Unit tests
- ✅ Citation validation utilities
- ✅ Sample parsed outputs

**Contract Compliance:**
- Implements `citation-parser-contract.md` interface
- No dependencies on LiteLLM or context builder
- Pure function (deterministic output)

**Validation Criteria:**
- [ ] Correctly extracts `[1]`, `[2]`, `[N]` markers
- [ ] Maps to source documents accurately
- [ ] Detects invalid citation numbers
- [ ] All tests pass

---

**Wave 1 Synchronization Gate:**
```bash
# All agents must pass before Wave 2 begins
pytest src/research/test_litellm_client.py -v
pytest src/research/test_context_builder.py -v
pytest src/research/test_citation_parser.py -v

# Contract validation
python scripts/validate_contracts.py --wave 1
```

---

## Wave 2: Integration Layer (2 Agents in Parallel)

**Goal:** Integrate Wave 1 components and expose via API

**Prerequisites:** Wave 1 complete and validated

### Agent 4: Research API Agent
**Territory:** `src/api/research.py` (new file), `src/api/server.py` (append route)

**Responsibilities:**
- Create FastAPI router with `/api/research/ask` POST endpoint
- Integrate: Context Builder → LiteLLM Client → Citation Parser
- Define Pydantic models (ResearchQuery, ResearchResponse)
- Implement error handling (search fails, LLM timeout, invalid citations)
- Add request validation and rate limiting
- Write integration tests (end-to-end API flow)

**Deliverables:**
- ✅ `src/api/research.py` - New FastAPI router
- ✅ Updated `src/api/server.py` with research router
- ✅ `src/api/test_research_api.py` - Integration tests
- ✅ API documentation (OpenAPI spec)

**Dependencies:**
- Reads from: `litellm_client.py`, `context_builder.py`, `citation_parser.py`
- Uses existing: Search engine (read-only)

**Contract Compliance:**
- Implements `api-contract.md` HTTP specification
- Consumes Wave 1 agent interfaces
- No conflicts (new file + minimal append to server.py)

**Validation Criteria:**
- [ ] `/api/research/ask` endpoint responds with 200
- [ ] Returns structured JSON with answer and citations
- [ ] Handles errors gracefully (500, 400, 429)
- [ ] Integration tests pass (mock LiteLLM for speed)

---

### Agent 5: Prompt Engineering Agent
**Territory:** `src/research/prompts.py` (new file), `src/config/research_config.py` (new file)

**Responsibilities:**
- Design system prompt template for research assistant
- Create prompt variations (simple, detailed, comparison)
- Configure model selection logic (GPT-4, Claude, GPT-3.5)
- Define temperature and sampling parameters
- Document prompt design decisions
- Test prompts with real LLM (validation, not unit tests)

**Deliverables:**
- ✅ `src/research/prompts.py` - Prompt templates
- ✅ `src/config/research_config.py` - Model and parameter config
- ✅ Prompt design documentation
- ✅ Validation report (citation quality tests)

**Dependencies:**
- None (config only, consumed by Research API)

**Contract Compliance:**
- Provides configuration consumed by `research.py`
- No code dependencies, pure data/templates

**Validation Criteria:**
- [ ] Prompts generate answers with valid `[N]` citations
- [ ] Citation accuracy >90% on test queries
- [ ] No hallucinated sources
- [ ] Clear configuration API

---

**Wave 2 Synchronization Gate:**
```bash
# Integration tests
pytest src/api/test_research_api.py -v

# End-to-end validation
curl -X POST http://localhost:8002/api/research/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is X?", "max_sources": 5}'

# Contract validation
python scripts/validate_contracts.py --wave 2
```

---

## Wave 3: Frontend Layer (3 Agents in Parallel)

**Goal:** Build user interface components

**Prerequisites:** Wave 2 complete (API working)

### Agent 6: Research Page Structure Agent
**Territory:** `src/frontend/research.html` (new file), `src/frontend/css/research.css` (new file)

**Responsibilities:**
- Create HTML structure: header, answer panel, references panel
- Add search input field and "Ask" button
- Implement empty, loading, error states
- Apply Kraft Paper theme styling
- Make responsive (stack panels on mobile)
- Add Detailed/Simple toggle buttons

**Deliverables:**
- ✅ `src/frontend/research.html` - Page structure
- ✅ `src/frontend/css/research.css` - Page-specific styles
- ✅ Responsive breakpoints (mobile, tablet, desktop)
- ✅ Accessibility markup (ARIA labels, semantic HTML)

**Dependencies:**
- None (static HTML/CSS only)

**Contract Compliance:**
- Implements `frontend-contract.md` DOM structure
- Provides containers for answer-display.js and reference-card.js

**Validation Criteria:**
- [ ] Page loads with correct layout
- [ ] All UI states render correctly (empty, loading, error)
- [ ] Responsive on mobile/tablet/desktop
- [ ] Passes accessibility scan (axe, WAVE)

---

### Agent 7: Answer Display Agent
**Territory:** `src/frontend/answer-display.js` (new file)

**Responsibilities:**
- Create `createAnswerDisplay(answerData)` function
- Render answer text with markdown support
- Convert `[N]` markers to clickable citation badges
- Style citation badges (number, hover states)
- Add click handlers (scroll to reference)
- Implement highlight state management

**Deliverables:**
- ✅ `src/frontend/answer-display.js` - Component module
- ✅ Citation badge styling in CSS
- ✅ Event handlers for citation interactions
- ✅ Unit tests (JSDOM or browser-based)

**Dependencies:**
- Consumes API response format (from Wave 2)
- Mounts into DOM structure from Agent 6

**Contract Compliance:**
- Implements `frontend-contract.md` AnswerDisplay interface
- Emits events for highlighting logic (Agent 9)

**Validation Criteria:**
- [ ] Renders answer text correctly
- [ ] Citation badges are clickable
- [ ] Hover states work
- [ ] No conflicts with reference-card.js

---

### Agent 8: Reference Card Agent
**Territory:** `src/frontend/reference-card.js` (new file)

**Responsibilities:**
- Create `createReferenceCard(citationData, variant)` function
- Implement Detailed variant (thumbnail 64px, filename, Details button)
- Implement Simple variant (number, filename only)
- Link Details button to `/details.html?filename={filename}`
- Add highlight state class (`.reference-card--highlighted`)
- Reuse patterns from existing `document-card.js` (read-only)

**Deliverables:**
- ✅ `src/frontend/reference-card.js` - Component module
- ✅ Reference card styling in CSS
- ✅ Both Detailed and Simple variants
- ✅ Unit tests

**Dependencies:**
- Consumes API response format (from Wave 2)
- Mounts into DOM structure from Agent 6

**Contract Compliance:**
- Implements `frontend-contract.md` ReferenceCard interface
- Emits events for highlighting logic (Agent 9)

**Validation Criteria:**
- [ ] Both variants render correctly
- [ ] Thumbnails load with 64px max-height
- [ ] Details button links to correct URL
- [ ] No conflicts with answer-display.js

---

**Wave 3 Synchronization Gate:**
```bash
# Component tests
npm test -- answer-display.test.js
npm test -- reference-card.test.js

# Visual regression tests
npm run test:visual -- research.html

# Accessibility validation
npm run test:a11y -- research.html

# Contract validation
python scripts/validate_contracts.py --wave 3
```

---

## Wave 4: Integration & Polish (2 Agents in Parallel)

**Goal:** Connect frontend to backend, implement interactions

**Prerequisites:** Wave 3 complete (UI components built)

### Agent 9: API Integration & Highlighting Agent
**Territory:** `src/frontend/research-controller.js` (new file)

**Responsibilities:**
- Connect frontend to `/api/research/ask` endpoint
- Handle API calls (loading states, error handling)
- Orchestrate: Answer Display + Reference Cards rendering
- Implement bidirectional highlighting logic
- Add Detailed/Simple toggle functionality
- Manage application state

**Deliverables:**
- ✅ `src/frontend/research-controller.js` - Main controller
- ✅ Highlighting event handlers
- ✅ API client with error handling
- ✅ Integration tests (Cypress or Playwright)

**Dependencies:**
- Integrates: answer-display.js, reference-card.js (Wave 3)
- Calls: `/api/research/ask` (Wave 2)

**Contract Compliance:**
- Implements `frontend-contract.md` Controller interface
- Orchestrates all Wave 3 components

**Validation Criteria:**
- [ ] API calls work (query → answer display)
- [ ] Bidirectional highlighting works (hover citation ↔ card)
- [ ] Detailed/Simple toggle works
- [ ] Error states display correctly

---

### Agent 10: Documentation & Configuration Agent
**Territory:** `docs/research-bot-guide.md` (new file), `.env.example` updates

**Responsibilities:**
- Write user guide for research bot
- Document API usage and examples
- Create developer setup guide (API keys, model selection)
- Document prompt engineering decisions
- Create troubleshooting guide
- Update main README with research bot section

**Deliverables:**
- ✅ `docs/research-bot-guide.md` - User documentation
- ✅ `docs/research-bot-dev.md` - Developer guide
- ✅ Updated `.env.example` with LiteLLM keys
- ✅ API examples (curl, Python, JS)

**Dependencies:**
- Documents: All Wave 1-3 components

**Contract Compliance:**
- N/A (documentation only)

**Validation Criteria:**
- [ ] User guide is clear and complete
- [ ] Dev setup instructions work (tested by fresh developer)
- [ ] All examples run successfully

---

**Wave 4 Synchronization Gate:**
```bash
# End-to-end tests
npm run test:e2e -- research-flow.spec.js

# Full integration test
pytest tests/integration/test_research_e2e.py -v

# Performance validation
python scripts/benchmark_research.py --target-latency 6000ms

# Final contract validation
python scripts/validate_contracts.py --all
```

---

## Final Integration Testing

### Test Scenarios
1. **Happy Path:** User query → search → LLM → cited answer → display
2. **Empty Results:** Query with no matching documents
3. **LLM Failure:** Primary model down, fallback to secondary
4. **Invalid Citations:** LLM returns out-of-range citations
5. **Mobile Experience:** Full flow on small screen
6. **Accessibility:** Screen reader navigation through answer and citations
7. **Performance:** 100 concurrent queries (load test)

### Success Criteria
- [ ] All 7 test scenarios pass
- [ ] Total latency < 6 seconds (p95)
- [ ] Citation accuracy > 95%
- [ ] No file conflicts between agents
- [ ] All contracts validated
- [ ] WCAG 2.1 AA compliance
- [ ] Works in Chrome, Firefox, Safari, Edge

---

## Agent Coordination Protocol

### Status Broadcasting
Each agent must update status in shared file:
```bash
# .context-kit/orchestration/research-bot/status.json
{
  "agent_1_litellm": {"status": "complete", "timestamp": "2025-10-17T10:00:00Z"},
  "agent_2_context": {"status": "in_progress", "progress": 0.75},
  "agent_3_citation": {"status": "blocked", "reason": "waiting for sample data"},
  ...
}
```

### Conflict Resolution
- **File conflicts:** NEVER edit same file (prevented by territorial boundaries)
- **Contract disputes:** Update contract in `integration-contracts/`, notify all consumers
- **Dependency issues:** Consumer agent validates contract, producer agent fixes

### Rollback Procedures
If Wave N fails validation:
1. Identify failing agent(s)
2. Rollback only that agent's work (git revert specific commits)
3. Fix issue in isolation
4. Re-run validation
5. Proceed only when gate passes

---

## Territorial Boundaries (File Ownership)

| Agent | Owned Files | Read-Only Files | Shared Files (Coordinated) |
|-------|-------------|-----------------|----------------------------|
| 1 | `src/research/litellm_client.py` | - | `.env.example` (append) |
| 2 | `src/research/context_builder.py` | `chroma_client.py` | - |
| 3 | `src/research/citation_parser.py` | - | - |
| 4 | `src/api/research.py` | `litellm_client.py`, `context_builder.py`, `citation_parser.py` | `src/api/server.py` (append route) |
| 5 | `src/research/prompts.py`, `src/config/research_config.py` | - | - |
| 6 | `src/frontend/research.html`, `src/frontend/css/research.css` | - | - |
| 7 | `src/frontend/answer-display.js` | - | - |
| 8 | `src/frontend/reference-card.js` | `document-card.js` (patterns only) | - |
| 9 | `src/frontend/research-controller.js` | `answer-display.js`, `reference-card.js` | - |
| 10 | `docs/research-bot-*.md` | All files | `README.md` (append section) |

**Conflict Prevention:**
- ✅ 90% of files are new (no overlaps)
- ✅ 2 shared files (`server.py`, `README.md`) use append-only coordination
- ✅ All other files are read-only dependencies

---

## Quality Gates

### Wave 1 Gate
- [ ] All unit tests pass (100% coverage on new code)
- [ ] No dependencies between agents
- [ ] Contracts validated (interface compliance)
- [ ] Code review passed (peer review)

### Wave 2 Gate
- [ ] Integration tests pass (API → components)
- [ ] API contract validated (OpenAPI spec compliance)
- [ ] Prompt quality validated (>90% citation accuracy)
- [ ] Error handling tested (all failure modes)

### Wave 3 Gate
- [ ] Component tests pass (UI rendering)
- [ ] Visual regression tests pass (no layout breaks)
- [ ] Accessibility tests pass (WCAG 2.1 AA)
- [ ] Responsive tests pass (mobile, tablet, desktop)

### Wave 4 Gate
- [ ] End-to-end tests pass (full user flow)
- [ ] Performance benchmarks pass (<6s latency)
- [ ] Cross-browser tests pass (Chrome, Firefox, Safari, Edge)
- [ ] Documentation validated (tested by fresh developer)

---

## Risk Management

### High-Risk Items
1. **LiteLLM API changes** - Mitigation: Pin version, test with mocks
2. **Citation quality** - Mitigation: Extensive prompt testing in Wave 2
3. **Token limits** - Mitigation: Conservative limits in context builder
4. **Performance** - Mitigation: Benchmark in Wave 4, optimize if needed

### Contingency Plans
- **LiteLLM unavailable:** Use mocked responses for development
- **Prompt not working:** Fallback to simpler prompt template
- **Frontend conflicts:** Rollback to Wave 3, re-coordinate
- **Performance issues:** Reduce sources, optimize token usage

---

## Timeline Estimation

| Wave | Agents | Estimated Duration | Bottleneck |
|------|--------|-------------------|------------|
| 1 | 3 (parallel) | 1-2 days | LiteLLM setup |
| 2 | 2 (parallel) | 1 day | Prompt engineering |
| 3 | 3 (parallel) | 1-2 days | Component styling |
| 4 | 2 (parallel) | 1 day | E2E testing |
| **Total** | | **4-6 days** | |

*Note: Times assume experienced developers working full-time*

---

## Success Metrics

### Delivery Metrics
- [ ] 100% of agents complete without file conflicts
- [ ] All 4 wave gates pass on first attempt
- [ ] Zero integration bugs (contracts prevent issues)
- [ ] All tests pass (unit, integration, E2E)

### Quality Metrics
- [ ] Citation accuracy > 95%
- [ ] Latency < 6s (p95)
- [ ] Cost < $0.05 per query
- [ ] WCAG 2.1 AA compliance
- [ ] Zero critical security issues

### User Experience Metrics
- [ ] Research query completes successfully
- [ ] Citations are accurate and helpful
- [ ] Highlighting works smoothly
- [ ] Mobile experience is responsive
- [ ] Accessible to screen readers

---

**End of Orchestration Plan**

Next Steps:
1. Create integration contracts (detailed specs for each interface)
2. Assign agents to developers/teams
3. Kick off Wave 1 in parallel
4. Monitor progress via status.json
5. Validate gates before advancing waves
