# Research Bot Integration Contracts

**Created:** 2025-10-17
**Status:** Complete
**Purpose:** Detailed interface specifications for all research bot components

---

## Overview

These integration contracts define the **exact interfaces** that each agent must implement during the research bot implementation. They serve as the single source of truth for:

- Function signatures and method contracts
- Data structures and schemas
- Error handling requirements
- Performance targets
- Validation gates

**Key Principle:** Interface-first development ensures all agents can work in parallel without conflicts.

---

## Contract Files

### Backend Contracts (Wave 1 - Foundation Layer)

1. **[LiteLLM Client Contract](./litellm-client-contract.md)**
   - Provider: Agent 1
   - File: `src/research/litellm_client.py`
   - Purpose: Unified LLM interface (OpenAI, Anthropic, Google, local)
   - Key Interfaces:
     - `LiteLLMClient.complete()` - Generate completion
     - `LiteLLMClient.stream_complete()` - Stream tokens
     - `ModelConfig` - Model configuration
     - `LLMResponse` - Standardized response

2. **[Context Builder Contract](./context-builder-contract.md)**
   - Provider: Agent 2
   - File: `src/research/context_builder.py`
   - Purpose: Build context from search results for LLM
   - Key Interfaces:
     - `ContextBuilder.build_context()` - Main context building
     - `ResearchContext` - Formatted context with sources
     - `SourceDocument` - Source metadata
     - Integration with SearchEngine and ChromaDB

3. **[Citation Parser Contract](./citation-parser-contract.md)**
   - Provider: Agent 3
   - File: `src/research/citation_parser.py`
   - Purpose: Parse citations from LLM output
   - Key Interfaces:
     - `CitationParser.parse()` - Parse full answer
     - `Citation` - Single citation marker
     - `ParsedAnswer` - Answer with citation mappings
     - Bidirectional sentence-citation maps

### API Contract (Wave 2 - Integration Layer)

4. **[Research API Contract](./research-api-contract.md)**
   - Provider: Agent 4
   - File: `src/api/research.py`
   - Purpose: HTTP API for research queries
   - Key Endpoints:
     - `POST /api/research/ask` - Submit query, get answer
     - `GET /api/research/health` - Health check
     - `GET /api/research/models` - List models
   - Request/Response schemas with Pydantic
   - Error handling (400, 404, 429, 500, 503)

### Frontend Contracts (Wave 3 & 4 - Frontend Layer)

5. **[Frontend Components Contract](./frontend-components-contract.md)**
   - Providers: Agents 6, 7, 8, 9
   - Files:
     - `src/frontend/research.html` - Page structure
     - `src/frontend/answer-display.js` - Answer panel
     - `src/frontend/reference-card.js` - Reference cards
     - `src/frontend/research-controller.js` - API integration
   - Key Features:
     - Two-panel layout (answer + references)
     - Bidirectional highlighting
     - View modes (detailed/simple)
     - State management (empty/loading/success/error)

---

## Contract Usage

### For Implementers

1. **Read your contract first**
   - Understand exact interfaces you must implement
   - Note all data structures and schemas
   - Review validation gates

2. **Implement to the contract**
   - Match function signatures exactly
   - Use specified data types
   - Handle all error cases
   - Meet performance targets

3. **Validate against gates**
   - Run all unit tests
   - Pass integration tests
   - Verify performance benchmarks

### For Integration

1. **Contracts define boundaries**
   - No need to coordinate across agents during implementation
   - Contracts guarantee compatibility

2. **Validation gates ensure quality**
   - Wave 1 gates validate before Wave 2 starts
   - Wave 2 gates validate before Wave 3 starts
   - Progressive validation prevents rework

---

## Dependency Map

```
Wave 1 (Foundation - Parallel)
├── Agent 1: LiteLLM Client
├── Agent 2: Context Builder → depends on SearchEngine, ChromaDB (existing)
└── Agent 3: Citation Parser

Wave 2 (Integration - Parallel)
├── Agent 4: Research API → depends on Agents 1, 2, 3
└── Agent 5: Prompt Engineering → depends on Agent 1

Wave 3 (Frontend - Parallel)
├── Agent 6: Research Page Structure
├── Agent 7: Answer Display
└── Agent 8: Reference Cards

Wave 4 (Integration & Polish - Sequential)
├── Agent 9: Frontend Integration → depends on Agents 6, 7, 8, 4
└── Agent 10: Documentation
```

---

## Key Data Structures

### LLM Response Flow

```python
# Agent 2: Context Builder
ResearchContext(
    formatted_text="[Document 1: file.pdf, Page 3]\nText...",
    sources=[SourceDocument(...), ...],
    total_tokens=8500,
    truncated=False
)

# Agent 1: LiteLLM Client
LLMResponse(
    content="Answer [1] with citation [2]...",
    model="gpt-4-turbo",
    usage={"total_tokens": 2000},
    latency_ms=1850
)

# Agent 3: Citation Parser
ParsedAnswer(
    original_text="Answer [1] with citation [2]...",
    citations=[Citation(id=1, ...), Citation(id=2, ...)],
    sentences=[Sentence(...), ...],
    citation_to_sentences={1: [Sentence(...)], ...}
)

# Agent 4: Research API Response
{
    "answer": "Answer [1] with citation [2]...",
    "citations": [{"id": 1, "start": 7, "end": 10}, ...],
    "citation_map": {"1": [{"sentence_index": 0, ...}], ...},
    "sources": [{"id": 1, "filename": "file.pdf", ...}, ...],
    "metadata": {...}
}
```

---

## Performance Targets

| Component | Target | Actual (Expected) |
|-----------|--------|-------------------|
| Context Building | <1s | ~500ms |
| LLM Completion | <30s | ~2s (GPT-4) |
| Citation Parsing | <10ms | ~5ms |
| Total API Latency | <3s | ~2.5s |
| Frontend Rendering | <100ms | ~50ms |
| Bidirectional Highlighting | <100ms | ~10ms |

---

## Validation Strategy

### Wave 1 Gates (Before Wave 2)

- [ ] LiteLLM client completes real API call
- [ ] Context builder retrieves from ChromaDB
- [ ] Citation parser handles all edge cases
- [ ] All unit tests pass
- [ ] Performance targets met

### Wave 2 Gates (Before Wave 3)

- [ ] Research API returns valid response
- [ ] End-to-end query → answer works
- [ ] Error handling covers all cases
- [ ] Integration tests pass

### Wave 3 Gates (Before Wave 4)

- [ ] All frontend components render
- [ ] State management works (empty/loading/success/error)
- [ ] View toggle switches modes
- [ ] Components pass accessibility checks

### Wave 4 Gates (Production Ready)

- [ ] Bidirectional highlighting works
- [ ] API integration successful
- [ ] Mobile responsive
- [ ] Cross-browser tested
- [ ] Documentation complete

---

## Contract Modifications

**Important:** These contracts are **living documents** during implementation.

### When to Modify

- Discovery of edge cases not covered
- Performance optimizations requiring interface changes
- User feedback requiring new features

### How to Modify

1. **Propose change** in orchestration plan discussion
2. **Validate impact** on dependent agents
3. **Update contract** with version bump
4. **Notify affected agents**
5. **Update tests** to match new contract

### Version History

- **v1.0** (2025-10-17) - Initial contracts created

---

## Related Documents

- **[Orchestration Plan](../orchestration-plan.md)** - Wave structure and agent coordination
- **[Research Bot Architecture](./../../../_specs/research-bot-architecture.md)** - System design
- **[Implementation Plan](./../../../_specs/research-page-implementation-plan.md)** - Frontend tasks

---

## Quick Reference

### For Agent 1 (LiteLLM)
- Contract: [litellm-client-contract.md](./litellm-client-contract.md)
- Key: Implement `LiteLLMClient` class with `complete()` and `stream_complete()`
- Test: Real API call to OpenAI succeeds

### For Agent 2 (Context Builder)
- Contract: [context-builder-contract.md](./context-builder-contract.md)
- Key: Implement `ContextBuilder.build_context()` using SearchEngine
- Test: Returns valid `ResearchContext` with sources

### For Agent 3 (Citation Parser)
- Contract: [citation-parser-contract.md](./citation-parser-contract.md)
- Key: Implement `CitationParser.parse()` with regex extraction
- Test: Correctly maps citations to sentences

### For Agent 4 (Research API)
- Contract: [research-api-contract.md](./research-api-contract.md)
- Key: FastAPI endpoint `POST /api/research/ask`
- Test: End-to-end query returns valid response

### For Agents 6-9 (Frontend)
- Contract: [frontend-components-contract.md](./frontend-components-contract.md)
- Key: Bidirectional highlighting between citations and references
- Test: Hover interactions work correctly

---

## Support

For questions about contracts:
1. Review the specific contract file for details
2. Check orchestration plan for wave dependencies
3. Consult architecture document for system design
4. Ask in implementation coordination channel

---

**Next Step:** Begin Wave 1 implementation following these contracts.
