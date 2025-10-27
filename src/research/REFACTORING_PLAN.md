# Refactoring Plan: `ask_research_question()` Function

**Status:** Planning Phase
**Target Complexity:** Reduce from 41 to <10 per function
**Current File:** `src/api/research.py`
**Function:** `ask_research_question()` (lines 289-651)

---

## Executive Summary

The `ask_research_question()` function has a cyclomatic complexity of 41 (Grade F), making it difficult to test, maintain, and extend. This plan proposes refactoring the function into 4 focused sub-functions, each with complexity <10, following the Single Responsibility Principle.

**Key Metrics:**
- Current lines: 363 (including comments/whitespace)
- Current complexity: 41 (F grade)
- Conditional branches: 15+ nested if/elif/else statements
- Try/except blocks: 10+ exception handlers
- Responsibilities: 7 distinct concerns mixed together

---

## Current Complexity Analysis

### Complexity Breakdown by Section

| Section | Lines | Complexity | Responsibilities |
|---------|-------|------------|------------------|
| Context Building | 20 | 3 | Search execution, result validation |
| Preprocessing Setup | 130 | 15 | Env config, strategy selection, compression/filter/synthesis logic |
| Vision Setup | 20 | 5 | Ngrok validation, image URL extraction |
| LLM Execution | 15 | 2 | LLM call with context/images |
| Citation Parsing | 10 | 2 | Parse and validate citations |
| Response Formatting | 60 | 4 | Build ResearchResponse with metadata |
| Error Handling | 40 | 10 | 6 different exception types |

**Total Complexity: 41**

### Root Causes of Complexity

1. **Mixed Concerns**: Single function handles search, preprocessing, vision, LLM, citations, and error handling
2. **Deep Nesting**: Preprocessing section has 4+ levels of indentation
3. **Conditional Logic**: 15+ if/elif/else branches for:
   - Preprocessing enabled/disabled
   - Strategy selection (compress/filter/synthesize)
   - Vision enabled/disabled
   - Error handling paths
4. **State Management**: 40+ local variables tracking different aspects
5. **Exception Handling**: 10+ try/except blocks scattered throughout
6. **Feature Flags**: Multiple environment variables controlling execution paths

### Current Execution Flow

```
ask_research_question()
├── 1. Build context (search + dedupe)
│   └── Check if sources found
├── 2. Preprocessing (if enabled)
│   ├── Check MLX client available
│   ├── Select strategy (compress/filter/synthesize)
│   ├── Execute strategy
│   │   ├── Compress: Per-chunk stats + compression
│   │   ├── Filter: Relevance scoring + thresholding
│   │   └── Synthesize: Knowledge synthesis
│   ├── Calculate token reduction
│   └── Update context
├── 3. Vision setup (if enabled)
│   ├── Validate NGROK_URL
│   ├── Extract image URLs
│   └── Estimate image tokens
├── 4. LLM execution
│   └── Call complete_with_context_and_images()
├── 5. Citation parsing
│   ├── Parse citations
│   └── Validate citations
├── 6. Format response
│   └── Build ResearchResponse with metadata
└── 7. Error handling (6 exception types)
```

---

## Proposed Refactoring Design

### Architecture Overview

Refactor into 4 focused sub-functions with clear interfaces:

```
ask_research_question() [Complexity: 8]
├── _prepare_research_context() [Complexity: 6]
├── _build_llm_messages() [Complexity: 5]
├── _execute_llm_request() [Complexity: 3]
└── _process_research_response() [Complexity: 4]
```

**Total Complexity: 26** (distributed across 5 functions)
**Per-Function Complexity: <10** ✓

---

## Sub-Function Specifications

### 1. `_prepare_research_context()`

**Responsibility:** Search execution, preprocessing, and context preparation

**Complexity Target:** 6

**Input Parameters:**
```python
async def _prepare_research_context(
    request: ResearchRequest,
    context_builder: ContextBuilder,
    local_preprocessor: Optional[LocalLLMPreprocessor],
) -> Tuple[ResearchContext, PreprocessingMetadata]
```

**Output:**
```python
@dataclass
class PreprocessingMetadata:
    """Metadata from preprocessing stage"""
    enabled: bool = False
    strategy: Optional[str] = None
    latency_ms: int = 0
    original_sources_count: int = 0
    token_reduction_percent: float = 0.0
    original_context: Optional[str] = None
    compressed_context: Optional[str] = None
    model: Optional[str] = None
    per_chunk_stats: Optional[List[Dict]] = None

ReturnType = Tuple[ResearchContext, PreprocessingMetadata]
```

**Responsibilities:**
1. Execute search via `context_builder.build_context()`
2. Validate sources found (raise HTTPException if none)
3. Apply preprocessing if enabled
4. Track preprocessing metrics
5. Return enriched context + metadata

**Implementation Strategy:**
- Extract lines 318-475 into dedicated function
- Create `PreprocessingMetadata` dataclass for clean return
- Delegate preprocessing logic to helper: `_apply_preprocessing()`
- Keep complexity <10 by extracting strategy selection to `_select_preprocessing_strategy()`

**Error Handling:**
- Raise HTTPException(404) if no sources found
- Log preprocessing failures, continue with original context
- Propagate search engine exceptions

**Testing:**
- Unit test: context building with/without sources
- Unit test: preprocessing enabled/disabled
- Unit test: each preprocessing strategy (compress/filter/synthesize)
- Integration test: end-to-end context preparation

---

### 2. `_build_llm_messages()`

**Responsibility:** Vision setup and LLM message construction

**Complexity Target:** 5

**Input Parameters:**
```python
def _build_llm_messages(
    request: ResearchRequest,
    context: ResearchContext,
    llm_client: LiteLLMClient,
) -> Tuple[str, List[str], int, VisionMetadata]
```

**Output:**
```python
@dataclass
class VisionMetadata:
    """Metadata from vision setup stage"""
    enabled: bool = False
    images_sent: int = 0
    image_tokens: int = 0
    image_urls: List[str] = field(default_factory=list)

ReturnType = Tuple[
    str,              # full_user_prompt
    List[str],        # image_urls
    int,              # image_tokens
    VisionMetadata    # vision metadata
]
```

**Responsibilities:**
1. Validate vision configuration (NGROK_URL, HTTPS)
2. Extract image URLs from visual sources
3. Limit images to max_images
4. Estimate image token cost
5. Build full user prompt

**Implementation Strategy:**
- Extract lines 476-514 into dedicated function
- Create `VisionMetadata` dataclass
- Delegate validation to `_validate_vision_config()`
- Keep complexity <10 by early returns for disabled vision

**Error Handling:**
- Log warnings for misconfiguration (NGROK_URL missing, not HTTPS)
- Gracefully disable vision if setup fails
- No exceptions raised (defensive)

**Testing:**
- Unit test: vision enabled with valid config
- Unit test: vision disabled
- Unit test: vision enabled but NGROK_URL missing
- Unit test: image URL extraction and limiting

---

### 3. `_execute_llm_request()`

**Responsibility:** LLM API call execution

**Complexity Target:** 3

**Input Parameters:**
```python
async def _execute_llm_request(
    request: ResearchRequest,
    context: ResearchContext,
    image_urls: List[str],
    llm_client: LiteLLMClient,
    system_prompt: str,
) -> Tuple[LLMResponse, int]
```

**Output:**
```python
ReturnType = Tuple[
    LLMResponse,  # LLM response object
    int           # latency_ms
]
```

**Responsibilities:**
1. Call `llm_client.complete_with_context_and_images()`
2. Track latency
3. Log completion metrics

**Implementation Strategy:**
- Extract lines 511-533 into dedicated function
- Minimal logic - just timing wrapper around LLM call
- Complexity naturally <10 (only 1 function call + timing)

**Error Handling:**
- Propagate all LLM exceptions to caller (no handling here)
- Let outer function handle specific exception types

**Testing:**
- Unit test: successful LLM call
- Unit test: LLM call with images
- Mock test: exception propagation

---

### 4. `_process_research_response()`

**Responsibility:** Citation parsing and response formatting

**Complexity Target:** 4

**Input Parameters:**
```python
def _process_research_response(
    llm_response: LLMResponse,
    context: ResearchContext,
    request: ResearchRequest,
    preprocessing_meta: PreprocessingMetadata,
    vision_meta: VisionMetadata,
    search_latency_ms: int,
    llm_latency_ms: int,
    total_time_ms: int,
    citation_parser: CitationParser,
    system_prompt: str,
    full_user_prompt: str,
) -> ResearchResponse
```

**Output:**
```python
ResearchResponse  # Pydantic model with answer, citations, sources, metadata
```

**Responsibilities:**
1. Parse citations from LLM response
2. Validate citations against source count
3. Format citations for frontend
4. Build ResearchResponse with all metadata

**Implementation Strategy:**
- Extract lines 535-612 into dedicated function
- Accept structured metadata objects (PreprocessingMetadata, VisionMetadata)
- Keep complexity <10 by using dataclasses for clean parameter passing

**Error Handling:**
- Log citation validation failures (non-fatal)
- Continue even if citations invalid

**Testing:**
- Unit test: valid citations
- Unit test: invalid citations (out of range)
- Unit test: metadata assembly
- Integration test: full response formatting

---

## Refactored `ask_research_question()` - Main Orchestrator

**New Complexity Target:** 8

**Structure:**
```python
@app.post("/api/research/ask", response_model=ResearchResponse)
async def ask_research_question(request: ResearchRequest):
    """
    Submit research question and receive AI-generated answer with citations

    This endpoint orchestrates the research pipeline:
    1. Search & preprocess context
    2. Build LLM messages with vision
    3. Execute LLM request
    4. Parse citations and format response
    """
    start_time = time.time()

    try:
        logger.info(
            "Processing research query",
            query=request.query,
            num_sources=request.num_sources,
            search_mode=request.search_mode,
        )

        # Step 1: Prepare context (search + preprocessing)
        search_start = time.time()
        context, preprocessing_meta = await _prepare_research_context(
            request=request,
            context_builder=app.state.context_builder,
            local_preprocessor=app.state.local_preprocessor,
        )
        search_latency_ms = int((time.time() - search_start) * 1000)

        # Step 2: Build LLM messages (vision + prompts)
        full_user_prompt, image_urls, image_tokens, vision_meta = _build_llm_messages(
            request=request,
            context=context,
            llm_client=app.state.llm_client,
        )

        # Step 3: Execute LLM request
        llm_response, llm_latency_ms = await _execute_llm_request(
            request=request,
            context=context,
            image_urls=image_urls,
            llm_client=app.state.llm_client,
            system_prompt=RESEARCH_SYSTEM_PROMPT,
        )

        # Step 4: Process response (citations + formatting)
        total_time_ms = int((time.time() - start_time) * 1000)
        response = _process_research_response(
            llm_response=llm_response,
            context=context,
            request=request,
            preprocessing_meta=preprocessing_meta,
            vision_meta=vision_meta,
            search_latency_ms=search_latency_ms,
            llm_latency_ms=llm_latency_ms,
            total_time_ms=total_time_ms,
            citation_parser=app.state.citation_parser,
            system_prompt=RESEARCH_SYSTEM_PROMPT,
            full_user_prompt=full_user_prompt,
        )

        logger.info(
            "Research query completed successfully",
            total_time_ms=total_time_ms,
            num_citations=len(response.citations),
        )

        return response

    except HTTPException:
        raise
    except AuthenticationError as e:
        logger.error("LLM authentication error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM authentication failed. Check API keys: {str(e)}",
        )
    except RateLimitError as e:
        logger.error("LLM rate limit hit", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Please try again in {e.retry_after} seconds.",
        )
    except TimeoutError as e:
        logger.error("LLM timeout", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request timed out. Try a simpler query or fewer sources.",
        )
    except ContextLengthError as e:
        logger.error("Context too long", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query context too long. Try reducing num_sources or simplifying query.",
        )
    except LLMError as e:
        logger.error("LLM error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM service error: {str(e)}",
        )
    except Exception as e:
        logger.error("Unexpected error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error. Please try again later.",
        )
```

**Complexity Breakdown:**
- Try/except block: +1
- 6 exception handlers: +6
- 4 function calls: +0 (no branching)
- Logging: +0

**Total: 7-8** ✓

---

## Interface Contracts

### Data Flow

```
Request → _prepare_research_context() → (ResearchContext, PreprocessingMetadata)
                                          ↓
                                    _build_llm_messages() → (prompt, images, tokens, VisionMetadata)
                                          ↓
                                    _execute_llm_request() → (LLMResponse, latency_ms)
                                          ↓
                                    _process_research_response() → ResearchResponse
```

### Contract Guarantees

1. **`_prepare_research_context()`**
   - Guarantees: Returns valid ResearchContext with >0 sources OR raises HTTPException
   - Side effects: Modifies context.sources if preprocessing enabled
   - Idempotent: No (calls search engine, uses external state)

2. **`_build_llm_messages()`**
   - Guarantees: Returns valid prompt string and image URLs (may be empty list)
   - Side effects: Logs warnings for misconfiguration
   - Idempotent: Yes (pure function given same inputs)

3. **`_execute_llm_request()`**
   - Guarantees: Returns LLMResponse OR propagates exception
   - Side effects: External API call, logs completion
   - Idempotent: No (external API call)

4. **`_process_research_response()`**
   - Guarantees: Returns valid ResearchResponse
   - Side effects: Logs citation validation warnings
   - Idempotent: Yes (pure function given same inputs)

### Error Handling Strategy

**Centralized in Main Function:**
- All LLM exceptions handled in main try/except
- Sub-functions propagate exceptions up
- HTTPException raised only in `_prepare_research_context()` for missing sources

**Defensive in Sub-Functions:**
- `_build_llm_messages()`: Logs warnings, disables vision on misconfiguration
- `_process_research_response()`: Logs citation errors, continues

---

## Supporting Data Structures

### New Dataclasses

```python
@dataclass
class PreprocessingMetadata:
    """Metadata from preprocessing stage"""
    enabled: bool = False
    strategy: Optional[str] = None
    latency_ms: int = 0
    original_sources_count: int = 0
    token_reduction_percent: float = 0.0
    original_context: Optional[str] = None
    compressed_context: Optional[str] = None
    model: Optional[str] = None
    per_chunk_stats: Optional[List[Dict]] = None


@dataclass
class VisionMetadata:
    """Metadata from vision setup stage"""
    enabled: bool = False
    images_sent: int = 0
    image_tokens: int = 0
    image_urls: List[str] = field(default_factory=list)
```

**Benefits:**
- Type-safe metadata passing
- Clear interfaces between functions
- Easy to extend with new fields
- Self-documenting code

---

## Helper Functions (Optional Extraction)

To keep sub-function complexity <10, consider extracting:

### `_apply_preprocessing()`
```python
async def _apply_preprocessing(
    context: ResearchContext,
    query: str,
    strategy: str,
    preprocessor: LocalLLMPreprocessor,
    context_builder: ContextBuilder,
) -> Tuple[ResearchContext, List[Dict]]:
    """
    Apply preprocessing strategy to context

    Complexity: 8 (strategy selection + error handling)
    """
    # Implementation of lines 366-474
```

### `_validate_vision_config()`
```python
def _validate_vision_config(ngrok_url: str) -> bool:
    """
    Validate vision configuration

    Complexity: 3 (2 validation checks)
    """
    if not ngrok_url:
        logger.warning("Vision enabled but NGROK_URL not set")
        return False
    if not ngrok_url.startswith("https://"):
        logger.warning("NGROK_URL should be HTTPS", ngrok_url=ngrok_url)
    return True
```

---

## Migration Strategy

### Phase 1: Create Data Structures (Non-Breaking)
1. Add `PreprocessingMetadata` dataclass
2. Add `VisionMetadata` dataclass
3. Update tests to use new structures
4. **Validation:** All tests pass, no functionality change

### Phase 2: Extract Sub-Functions (Non-Breaking)
1. Extract `_process_research_response()` (simplest, no async)
2. Extract `_execute_llm_request()` (simple async wrapper)
3. Extract `_build_llm_messages()` (moderate complexity)
4. Extract `_prepare_research_context()` (most complex)
5. **Validation:** All tests pass, no functionality change

### Phase 3: Refactor Main Function
1. Replace inline code with sub-function calls
2. Simplify error handling (already centralized)
3. Add integration tests for full pipeline
4. **Validation:** Coverage maintained, complexity <10

### Phase 4: Documentation & Cleanup
1. Add docstrings to all sub-functions
2. Update API documentation
3. Add complexity monitoring (radon CI check)
4. **Validation:** Documentation complete, CI passing

### Backwards Compatibility

- **API Contract:** No changes to `/api/research/ask` endpoint
- **Request/Response:** ResearchRequest and ResearchResponse unchanged
- **Behavior:** Identical functionality, just refactored internals
- **Performance:** No performance degradation expected

---

## Testing Strategy

### Unit Tests (Per Sub-Function)

**`_prepare_research_context()`:**
```python
async def test_prepare_context_with_sources():
    """Test successful context preparation"""

async def test_prepare_context_no_sources():
    """Test raises HTTPException when no sources"""

async def test_prepare_context_with_preprocessing():
    """Test preprocessing enabled"""

async def test_prepare_context_preprocessing_disabled():
    """Test preprocessing disabled"""

async def test_prepare_context_preprocessing_fails():
    """Test fallback to original context on preprocessing failure"""
```

**`_build_llm_messages()`:**
```python
def test_build_messages_vision_enabled():
    """Test vision setup with valid config"""

def test_build_messages_vision_disabled():
    """Test vision disabled"""

def test_build_messages_no_ngrok_url():
    """Test vision disabled when NGROK_URL missing"""

def test_build_messages_image_limiting():
    """Test max_images enforced"""
```

**`_execute_llm_request()`:**
```python
async def test_execute_llm_success():
    """Test successful LLM call"""

async def test_execute_llm_with_images():
    """Test LLM call with vision"""

async def test_execute_llm_exception_propagation():
    """Test exceptions propagate to caller"""
```

**`_process_research_response()`:**
```python
def test_process_response_valid_citations():
    """Test citation parsing and validation"""

def test_process_response_invalid_citations():
    """Test handles invalid citations gracefully"""

def test_process_response_metadata_assembly():
    """Test metadata correctly assembled"""
```

### Integration Tests

```python
async def test_research_pipeline_end_to_end():
    """Test full research pipeline"""

async def test_research_pipeline_with_preprocessing():
    """Test pipeline with preprocessing enabled"""

async def test_research_pipeline_with_vision():
    """Test pipeline with vision enabled"""

async def test_research_pipeline_all_features():
    """Test pipeline with all features enabled"""
```

### Complexity Monitoring

Add to CI pipeline:
```bash
# Fail CI if any function exceeds complexity 10
radon cc src/api/research.py -s -n C --min F

# Generate complexity report
radon cc src/api/research.py -s -a > complexity_report.txt
```

---

## Estimated Complexity Reduction

### Before Refactoring

| Function | Complexity | Grade |
|----------|-----------|-------|
| `ask_research_question()` | 41 | F |
| **Total** | **41** | **F** |

### After Refactoring

| Function | Complexity | Grade |
|----------|-----------|-------|
| `ask_research_question()` | 8 | A |
| `_prepare_research_context()` | 6 | A |
| `_build_llm_messages()` | 5 | A |
| `_execute_llm_request()` | 3 | A |
| `_process_research_response()` | 4 | A |
| **Total** | **26** | **A** |

**Complexity Reduction: 37% (41 → 26)**
**Per-Function Complexity: 100% compliance (<10)** ✓

---

## Key Design Decisions

### 1. **Function Granularity**
- **Decision:** 4 sub-functions instead of 7+ smaller functions
- **Rationale:** Balance between complexity reduction and function explosion
- **Trade-off:** Each sub-function has 3-6 complexity (could go lower with more functions)

### 2. **Dataclass vs Dict**
- **Decision:** Use `PreprocessingMetadata` and `VisionMetadata` dataclasses
- **Rationale:** Type safety, IDE autocomplete, self-documenting
- **Trade-off:** More boilerplate, but better maintainability

### 3. **Error Handling Location**
- **Decision:** Centralize LLM exception handling in main function
- **Rationale:** Single point of control for API error responses
- **Trade-off:** Sub-functions must propagate exceptions (no isolation)

### 4. **Async Boundaries**
- **Decision:** Keep async only where needed (context preparation, LLM execution)
- **Rationale:** Vision setup and response processing are CPU-bound, no I/O
- **Trade-off:** Mixed async/sync functions in call chain

### 5. **Helper Function Extraction**
- **Decision:** Optional extraction of `_apply_preprocessing()` and `_validate_vision_config()`
- **Rationale:** Keep sub-functions <10 complexity if needed
- **Trade-off:** More functions to maintain, but better testability

---

## Implementation Checklist

### Phase 1: Data Structures
- [ ] Create `PreprocessingMetadata` dataclass in `src/api/research.py`
- [ ] Create `VisionMetadata` dataclass in `src/api/research.py`
- [ ] Update imports to include `field` from `dataclasses`
- [ ] Run tests to verify no breaking changes

### Phase 2: Sub-Function Extraction
- [ ] Extract `_process_research_response()` with full docstring
- [ ] Write unit tests for `_process_research_response()`
- [ ] Extract `_execute_llm_request()` with full docstring
- [ ] Write unit tests for `_execute_llm_request()`
- [ ] Extract `_build_llm_messages()` with full docstring
- [ ] Write unit tests for `_build_llm_messages()`
- [ ] Extract `_prepare_research_context()` with full docstring
- [ ] Write unit tests for `_prepare_research_context()`

### Phase 3: Main Function Refactor
- [ ] Refactor `ask_research_question()` to call sub-functions
- [ ] Verify error handling still works (all exception paths)
- [ ] Run full integration test suite
- [ ] Verify API contract unchanged (request/response schemas)
- [ ] Check complexity with `radon cc`

### Phase 4: Documentation & CI
- [ ] Add docstrings to all new functions
- [ ] Update API documentation if needed
- [ ] Add complexity check to CI pipeline
- [ ] Run full test suite with coverage report
- [ ] Update CHANGELOG.md with refactoring notes

### Validation Criteria
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Code coverage maintained (>80%)
- [ ] Complexity <10 for all functions
- [ ] API endpoint behavior unchanged
- [ ] Performance metrics unchanged (±5%)
- [ ] No new linting errors

---

## Performance Impact

**Expected:** Negligible (function call overhead ~1-2ms total)

**Monitoring:**
- Track `total_time_ms` before/after refactoring
- Acceptable range: ±5% (current ~2500ms → 2375-2625ms)
- If degradation >5%, investigate function call overhead

**Optimization Opportunities:**
- Reduce metadata copying (use references where possible)
- Consider caching vision config validation
- Profile with `cProfile` if performance concerns arise

---

## Future Enhancements

Once refactored, the code will support:

1. **Strategy Pattern for Preprocessing:** Extract preprocessing strategies into separate classes
2. **Pipeline Composition:** Build flexible pipelines with different combinations of steps
3. **A/B Testing:** Easy to swap implementations for performance testing
4. **Metrics Collection:** Insert instrumentation points in sub-functions
5. **Retry Logic:** Add retry decorators to individual steps
6. **Circuit Breakers:** Isolate failures to specific pipeline stages

---

## Conclusion

This refactoring plan provides a clear path to reduce complexity from **41 to <10 per function** while maintaining:

- ✅ **100% backwards compatibility** (no API changes)
- ✅ **Same functionality** (no behavior changes)
- ✅ **Improved testability** (isolated sub-functions)
- ✅ **Better maintainability** (single responsibility per function)
- ✅ **Type safety** (dataclass-based interfaces)
- ✅ **Clear separation of concerns** (search → vision → LLM → citations)

**Next Steps:** Begin Phase 1 implementation after approval.

---

**Document Version:** 1.0
**Created:** 2025-10-26
**Author:** Claude Code Agent (Refactoring Plan Task #8)
**Complexity Tool:** `radon cc` (McCabe cyclomatic complexity)
