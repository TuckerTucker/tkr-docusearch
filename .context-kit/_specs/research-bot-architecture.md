# Research Bot Architecture

**Created:** 2025-10-17
**Status:** Planning
**Phase:** Architecture Design
**Dependencies:** LiteLLM, ChromaDB metadata, ColPali search

---

## Overview

The Research Bot provides AI-generated answers to user questions with inline citations linking back to source documents. It combines semantic search (ColPali + ChromaDB) with LLM inference (via LiteLLM) to generate grounded, cited responses.

---

## System Architecture

```
User Query: "What caused the revenue drop?"
    ↓
┌─────────────────────────────────────────────────────┐
│ 1. Query Processing                                 │
│    - Embed query with ColPali (22 tokens × 128 dim) │
│    - Optional: Query expansion for better recall    │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ 2. Semantic Search (Existing System)                │
│    - Stage 1: ChromaDB HNSW (top 100 candidates)   │
│    - Stage 2: MaxSim late interaction (top 10)      │
│    - Average latency: 239ms                         │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ 3. Context Building                                 │
│    - Retrieve metadata for top results              │
│    - Decompress markdown text                       │
│    - Format for LLM prompt                          │
│    - Add document structure (headings, sections)    │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ 4. LLM Inference (via LiteLLM)                      │
│    - System prompt: Research assistant role         │
│    - Context: Top 5-10 documents with metadata      │
│    - User query                                      │
│    - Generate answer with [N] citations             │
│    - Latency: 2-5s depending on model               │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ 5. Response Processing                              │
│    - Parse citation markers: [1], [2], [3]          │
│    - Map citations to source documents              │
│    - Extract character positions for highlighting   │
│    - Build reference card metadata                  │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ 6. Frontend Display                                 │
│    - Answer text with inline citations              │
│    - Reference cards (thumbnails, filenames)        │
│    - Bidirectional highlighting                     │
│    - Links to details page                          │
└─────────────────────────────────────────────────────┘
```

**Total User-Facing Latency:** ~3-5 seconds (search 239ms + LLM 2-5s)

---

## Component 1: LiteLLM Integration

### What is LiteLLM?

**Purpose:** Unified interface for 100+ LLM providers
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude Sonnet, Haiku, Opus)
- Google (Gemini Pro)
- Local (Ollama, vLLM)
- Many more...

**Key Features:**
- Single API format (OpenAI-compatible)
- Automatic provider translation
- Fallback routing (primary fails → backup)
- Load balancing across models
- Rate limiting and retry logic
- Cost tracking and logging
- Streaming support

### Why LiteLLM for DocuSearch?

1. **Flexibility**: Easy to switch between GPT-4, Claude, or local models
2. **Cost optimization**: Route simple queries to cheaper models
3. **Reliability**: Automatic fallback if primary provider down
4. **Privacy options**: Can route to local Ollama for sensitive documents
5. **Observability**: Built-in logging and monitoring

### LiteLLM Configuration

```python
# litellm_config.py
from litellm import completion

# Example: Route to different models based on complexity
MODELS = {
    "primary": "gpt-4-turbo-preview",      # High quality, expensive
    "fallback": "claude-sonnet-3.5",       # Backup
    "simple": "gpt-3.5-turbo",            # Fast, cheap for simple queries
    "local": "ollama/llama3",             # Offline mode
}

# Example usage
response = completion(
    model="gpt-4-turbo-preview",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query}
    ],
    temperature=0.1,  # Low temp for factual answers
    max_tokens=1000,
    stream=False,
)
```

### Model Selection Strategy

| Query Type | Model | Latency | Cost/1K tokens | Use Case |
|------------|-------|---------|----------------|----------|
| Complex analysis | GPT-4 | 3-5s | $0.03 | Deep research, multiple sources |
| Simple lookup | GPT-3.5 | 1-2s | $0.002 | Single fact, quick answer |
| Offline/Private | Ollama Llama3 | 5-10s | $0 | Sensitive documents |
| Fallback | Claude Sonnet | 2-4s | $0.015 | If GPT-4 unavailable |

---

## Component 2: Semantic Search (Existing)

### Current System Capabilities

Already implemented and validated (Wave 3+4):
- ✅ ColPali 128-dim multi-vector embeddings
- ✅ ChromaDB vector database
- ✅ 2-stage search: HNSW → MaxSim
- ✅ 239ms average latency (target <300ms)
- ✅ 100% accuracy on test queries
- ✅ MPS GPU acceleration (10-20x faster)

### Search Flow for Research Bot

```python
def search_for_research(query: str, top_k: int = 10):
    """
    Search documents to build LLM context.

    Returns:
        List of dicts with metadata:
        [
            {
                "doc_id": "doc-123",
                "filename": "report.pdf",
                "page": 5,
                "score": 0.92,
                "metadata": {...}  # Full ChromaDB metadata
            }
        ]
    """
    # 1. Embed query
    query_embedding = colpali_model.embed_query(query)  # 22 tokens × 128 dim

    # 2. Search ChromaDB (Stage 1: HNSW)
    candidates = chromadb.search(
        collection="visual_collection",
        query_embedding=query_embedding,
        n_results=100
    )

    # 3. Re-rank (Stage 2: MaxSim late interaction)
    top_results = maxsim_rerank(
        query_embedding=query_embedding,
        candidates=candidates,
        top_k=top_k
    )

    return top_results
```

### What We Get from Search

For each result:
```python
{
    "doc_id": "quarterly-report-2024-q4",
    "filename": "Q4_2024_Financial_Report.pdf",
    "page": 5,
    "score": 0.92,  # MaxSim relevance score
    "metadata": {
        # Core fields
        "source_path": "/data/uploads/Q4_2024_Financial_Report.pdf",
        "timestamp": "2025-10-15T10:30:00",
        "type": "visual",

        # Image paths
        "image_path": "/data/images/Q4_2024_page_005.jpg",
        "thumb_path": "/data/images/Q4_2024_page_005_thumb.jpg",

        # Document structure (if available)
        "num_headings": 15,
        "num_tables": 3,
        "num_pictures": 5,
        "has_structure": true,
        "structure": "<compressed-json>",  # Decompress for details

        # Markdown text (compressed)
        "full_markdown_compressed": "<gzipped-base64>",
        "markdown_compression": "gzip+base64"
    }
}
```

---

## Component 3: Context Building

### Goal
Transform search results into formatted context for LLM prompt.

### Process

1. **Retrieve metadata**: Get top 5-10 results from search
2. **Decompress text**: Extract markdown from compressed metadata
3. **Extract structure**: Get headings, sections from structure metadata
4. **Format for LLM**: Build readable context blocks

### ChromaDB Metadata Available

#### Visual Collection (Page-level):
- ✅ `filename` - Document name
- ✅ `page` - Page number
- ✅ `source_path` - Full file path
- ✅ `full_markdown_compressed` - Compressed text content
- ✅ `structure` - Document structure (headings, tables, pictures)
- ✅ `num_headings`, `num_tables`, `num_pictures` - Summary stats
- ✅ `thumb_path` - Thumbnail for reference cards
- ✅ `timestamp` - Upload date

#### Text Collection (Chunk-level):
- ✅ `filename` - Document name
- ✅ `page` - Page where chunk starts
- ✅ `chunk_id` - Chunk number
- ✅ `text_preview` - First 100 chars of chunk
- ✅ `word_count` - Chunk length
- ✅ `parent_heading` - Immediate parent heading
- ✅ `section_path` - Breadcrumb trail (e.g., "Intro > Methods > Data")
- ✅ `element_type` - text, list_item, table_cell, caption, code, formula
- ✅ `related_tables`, `related_pictures` - IDs of referenced content

### Text Extraction Method

**Already exists:** `chroma_client.get_document_markdown(doc_id)`

```python
def get_document_markdown(doc_id: str) -> Optional[str]:
    """
    Retrieve full markdown for a document.

    - Queries visual collection for doc_id
    - Decompresses gzipped+base64 markdown
    - Returns full text content
    """
```

### Context Formatting

```python
def build_llm_context(search_results: List[dict]) -> str:
    """
    Format search results into LLM context.
    """
    context_blocks = []

    for i, result in enumerate(search_results, 1):
        doc_id = result["doc_id"]
        metadata = result["metadata"]

        # Decompress markdown text
        full_text = chroma_client.get_document_markdown(doc_id)

        # Extract structure if available
        section = ""
        if metadata.get("has_structure"):
            structure = decompress_structure(metadata["structure"])
            # Get heading for this page
            page_headings = [
                h for h in structure.headings
                if h["page"] == metadata["page"]
            ]
            if page_headings:
                section = page_headings[0]["text"]

        # Build context block
        context_block = f"""
[Document {i}: {metadata['filename']}, Page {metadata['page']}]
Section: {section or 'N/A'}
Relevance: {result['score']:.2f}

{full_text[:2000]}  # Limit to first 2000 chars
"""
        context_blocks.append(context_block)

    return "\n\n".join(context_blocks)
```

### Token Management

**LLM Context Limits:**
- GPT-4: 128K tokens
- Claude: 200K tokens
- GPT-3.5: 16K tokens

**Strategy:**
- System prompt: ~500 tokens
- Context (5-10 docs × 2000 chars each): ~10K tokens
- Query: ~50 tokens
- Answer space: ~1K tokens
- **Total:** ~12K tokens (well within limits)

**Optimization:**
- If over limit: Reduce docs or chars per doc
- Truncate to most relevant passages
- Prioritize recent documents

---

## Component 4: Prompt Engineering

### Research Bot System Prompt

```
ROLE:
You are a research assistant that answers questions based ONLY on the provided documents.
You must cite sources using the format [N] where N is the document number.

CONTEXT:
[Document 1: quarterly_report.pdf, Page 5]
Section: Financial Performance
Relevance: 0.92

Revenue increased by 23% in Q4 2024, driven by strong product sales...
[Full text content]

[Document 2: market_analysis.pdf, Page 12]
Section: Industry Trends
Relevance: 0.88

Market conditions improved in late 2024 with...
[Full text content]

[Additional documents...]

USER QUERY:
What caused the revenue increase?

INSTRUCTIONS:
1. Answer the question using ONLY the provided context above
2. Cite sources inline using [1], [2], etc. where [N] refers to [Document N]
3. Place citations immediately after the fact: "Revenue grew 23% [1]"
4. Use multiple citations for a single claim if supported by multiple sources: [1][2]
5. If information is NOT in the context, respond: "I don't have information about that in the provided documents."
6. Do NOT make up information or cite external knowledge
7. Be concise but complete
8. Use professional, clear language

ANSWER:
```

### Prompt Variations

#### For Simple Queries (Short Answer):
```
INSTRUCTIONS:
- Provide a direct, concise answer (2-3 sentences max)
- Focus on the specific fact requested
- Always cite sources [N]
```

#### For Complex Analysis (Detailed Answer):
```
INSTRUCTIONS:
- Provide a comprehensive analysis
- Synthesize information from multiple sources
- Structure with clear paragraphs
- Cite each claim [N]
- Identify any contradictions between sources
```

#### For Comparison/Contrast:
```
INSTRUCTIONS:
- Compare information across documents
- Highlight agreements and disagreements
- Cite each source appropriately [N]
```

### Citation Format Enforcement

**Key prompt elements:**
1. **Explicit format**: "Use [N] format where N is document number"
2. **Placement**: "Place immediately after the fact"
3. **Multiple sources**: "Use [1][2] for claims from multiple docs"
4. **Grounding**: "Answer ONLY from provided context"
5. **Honesty**: "Say 'I don't have information' if not in context"

### Temperature & Sampling

```python
# For factual research (recommended)
temperature = 0.1  # Low = deterministic, factual
top_p = 0.95
frequency_penalty = 0.0
presence_penalty = 0.0

# For creative synthesis (alternative)
temperature = 0.3  # Slightly higher for varied phrasing
```

---

## Component 5: Response Processing

### Citation Parsing

**Goal:** Extract `[N]` markers and map to source documents

```python
import re

def parse_citations(answer_text: str, source_docs: List[dict]) -> dict:
    """
    Parse LLM response and map citations to sources.

    Returns:
        {
            "answer": "Revenue grew 23% [1] due to...",
            "citations": [
                {
                    "id": 1,
                    "filename": "report.pdf",
                    "page": 5,
                    "thumbnail": "/path/to/thumb.jpg",
                    "positions": [(20, 23)]  # Character positions of [1]
                }
            ]
        }
    """
    # Find all citation markers
    citation_pattern = r'\[(\d+)\]'
    matches = list(re.finditer(citation_pattern, answer_text))

    # Build citation map
    citations = {}
    for match in matches:
        citation_num = int(match.group(1))
        if citation_num not in citations:
            if citation_num <= len(source_docs):
                source = source_docs[citation_num - 1]
                citations[citation_num] = {
                    "id": citation_num,
                    "filename": source["filename"],
                    "page": source["metadata"]["page"],
                    "thumbnail": source["metadata"].get("thumb_path"),
                    "doc_id": source["doc_id"],
                    "relevance_score": source["score"],
                    "positions": []
                }
            citations[citation_num]["positions"].append(
                (match.start(), match.end())
            )

    return {
        "answer": answer_text,
        "citations": list(citations.values())
    }
```

### Validation

**Check for hallucinations:**
1. All citation numbers are valid (≤ number of source docs)
2. No uncited claims (optional: flag sentences without citations)
3. Citations map to provided documents

```python
def validate_citations(parsed: dict, source_docs: List[dict]) -> bool:
    """
    Validate that all citations are valid.
    """
    max_citation = len(source_docs)

    for citation in parsed["citations"]:
        if citation["id"] > max_citation or citation["id"] < 1:
            logger.warning(f"Invalid citation number: {citation['id']}")
            return False

    return True
```

### Response Format

**API Response Structure:**

```json
{
  "query": "What caused the revenue increase?",
  "answer": "Revenue increased by 23% in Q4 2024 [1], driven primarily by strong product sales and improved market conditions [2]. The growth was consistent across all regions [1] and exceeded analyst expectations [3].",
  "citations": [
    {
      "id": 1,
      "filename": "Q4_2024_Financial_Report.pdf",
      "page": 5,
      "section": "Financial Performance",
      "thumbnail_url": "/data/images/Q4_2024_page_005_thumb.jpg",
      "doc_id": "quarterly-report-2024-q4",
      "relevance_score": 0.92,
      "positions": [
        {"start": 35, "end": 38},
        {"start": 145, "end": 148}
      ],
      "excerpt": "Revenue increased by 23% in Q4 2024..."
    },
    {
      "id": 2,
      "filename": "market_analysis.pdf",
      "page": 12,
      "section": "Industry Trends",
      "thumbnail_url": "/data/images/market_analysis_page_012_thumb.jpg",
      "doc_id": "market-analysis-2024",
      "relevance_score": 0.88,
      "positions": [{"start": 78, "end": 81}],
      "excerpt": "Strong product sales and improved market conditions..."
    }
  ],
  "metadata": {
    "model_used": "gpt-4-turbo-preview",
    "tokens_used": 1250,
    "latency_ms": 3200,
    "search_latency_ms": 239,
    "num_sources": 5,
    "timestamp": "2025-10-17T15:30:00Z"
  }
}
```

---

## Component 6: API Endpoint

### Endpoint Design

```
POST /api/research/ask
```

**Request:**
```json
{
  "query": "What caused the revenue drop?",
  "max_sources": 10,
  "model": "gpt-4-turbo-preview",
  "temperature": 0.1
}
```

**Response:** See "Response Format" above

### Implementation Outline

```python
# src/api/research.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from litellm import completion

router = APIRouter()

class ResearchQuery(BaseModel):
    query: str
    max_sources: int = 10
    model: str = "gpt-4-turbo-preview"
    temperature: float = 0.1

@router.post("/research/ask")
async def ask_research_question(request: ResearchQuery):
    """
    Generate AI answer with citations.
    """
    try:
        # 1. Semantic search
        search_results = search_engine.search(
            query=request.query,
            top_k=request.max_sources
        )

        # 2. Build LLM context
        context = build_llm_context(search_results)

        # 3. Generate answer via LiteLLM
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"{context}\n\nQUERY: {request.query}"}
        ]

        response = completion(
            model=request.model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=1000
        )

        answer_text = response.choices[0].message.content

        # 4. Parse citations
        parsed = parse_citations(answer_text, search_results)

        # 5. Validate
        if not validate_citations(parsed, search_results):
            raise HTTPException(400, "Invalid citations in answer")

        # 6. Build response
        return {
            "query": request.query,
            "answer": parsed["answer"],
            "citations": parsed["citations"],
            "metadata": {
                "model_used": request.model,
                "tokens_used": response.usage.total_tokens,
                "num_sources": len(search_results)
            }
        }

    except Exception as e:
        logger.error(f"Research query failed: {e}")
        raise HTTPException(500, str(e))
```

---

## Implementation Roadmap

### Phase 1: Core Infrastructure
1. **Install LiteLLM**: `pip install litellm`
2. **Configure API keys**: OpenAI, Anthropic, etc.
3. **Create context builder**: Function to format search results
4. **Build system prompt template**: Research assistant instructions

### Phase 2: API Integration
5. **Create `/api/research/ask` endpoint**: FastAPI route
6. **Connect to existing search**: Use ColPali + ChromaDB
7. **Integrate LiteLLM**: Call completion API
8. **Implement citation parser**: Regex for `[N]` markers

### Phase 3: Testing & Refinement
9. **Test with real documents**: Validate accuracy
10. **Tune prompts**: Improve citation quality
11. **Optimize token usage**: Balance context size vs quality
12. **Add error handling**: Fallback models, retry logic

### Phase 4: Frontend Integration
13. **Connect frontend to API**: research.html → `/api/research/ask`
14. **Display answer with citations**: Inline markers
15. **Render reference cards**: Thumbnails, filenames, Details button
16. **Implement highlighting**: Bidirectional hover states

---

## Key Design Decisions

### Decision 1: Use Page-Level or Chunk-Level Search?

**Options:**
- **A) Page-level** (visual collection): Entire page as context
- **B) Chunk-level** (text collection): Specific paragraphs

**Recommendation:** **Hybrid approach**
- Use page-level for initial search (faster, visual context)
- Extract chunk-level for precise citations (section_path, parent_heading)

### Decision 2: How Many Sources to Include?

**Analysis:**
- Too few (1-3): May miss important context
- Too many (20+): Token limit, noise

**Recommendation:** **5-10 sources**
- Balances coverage and token budget
- Allows comparison across sources
- Fits well within GPT-4 128K limit

### Decision 3: Citation Granularity

**Options:**
- **A) Document-level**: [1] = "report.pdf"
- **B) Page-level**: [1] = "report.pdf, page 5"
- **C) Passage-level**: [1] = "report.pdf, page 5, section 'Methods'"

**Recommendation:** **Page-level (B)**
- Provides useful specificity without complexity
- Maps cleanly to visual embeddings
- Easy to display in reference cards
- User can click Details button for full context

### Decision 4: Streaming vs Complete Response?

**Options:**
- **A) Streaming**: Answer appears word-by-word (better UX)
- **B) Complete**: Wait for full answer (simpler implementation)

**Recommendation:** **Start with Complete (B), add Streaming later**
- Simpler MVP implementation
- Citation parsing easier with complete text
- Can add streaming in Phase 2

---

## Performance Targets

| Metric | Target | Actual (Expected) |
|--------|--------|-------------------|
| Search latency | <300ms | 239ms (✓) |
| LLM latency | <5s | 2-5s (depends on model) |
| Total latency | <6s | 3-5s (acceptable) |
| Citation accuracy | >95% | TBD (test with prompts) |
| Cost per query | <$0.05 | $0.01-0.03 (GPT-4) |

---

## Cost Estimation

### Per Query Cost (GPT-4):
- Input tokens (~12K): $0.36 (at $0.03/1K)
- Output tokens (~1K): $0.06 (at $0.06/1K)
- **Total:** ~$0.42 per query

### Cost Optimization:
1. Use GPT-3.5 for simple queries: ~$0.03 per query
2. Cache common queries
3. Reduce context size for known simple questions
4. Use local Ollama for dev/testing (free)

---

## Security & Privacy Considerations

### Data Privacy:
- User queries and document content sent to LLM provider
- **Mitigation:** Offer local model option (Ollama) for sensitive docs
- **Disclosure:** Inform users about data being sent to OpenAI/Anthropic

### Citation Validation:
- Prevent LLM from citing non-existent sources
- **Mitigation:** Validate citation numbers, flag invalid citations
- **Logging:** Track hallucination rates

### Rate Limiting:
- Prevent abuse of expensive LLM API
- **Mitigation:** Rate limit per user/IP
- **Cost caps:** Set monthly budget alerts

---

## Success Metrics

### Functional:
- [ ] LLM generates answers with valid citations
- [ ] Citation format is consistent: `[1]`, `[2]`, etc.
- [ ] All citations map to provided documents (no hallucinations)
- [ ] Frontend displays answer and reference cards correctly
- [ ] Highlighting works bidirectionally

### Non-Functional:
- [ ] Total latency < 6 seconds
- [ ] Cost per query < $0.05
- [ ] 95%+ citation accuracy
- [ ] LLM response rate > 95% (fallback works)

---

## Next Steps

1. **Review this architecture** with stakeholders
2. **Choose primary LLM model** (GPT-4 vs Claude vs local)
3. **Set up LiteLLM** with API keys
4. **Prototype context builder** with real ChromaDB data
5. **Test prompt engineering** with sample queries
6. **Implement API endpoint** (`/api/research/ask`)
7. **Integrate with frontend** (research.html)

---

## Appendix: Example End-to-End Flow

### User Query:
```
"What were the key factors driving revenue growth in Q4 2024?"
```

### Search Results (Top 3):
```python
[
    {
        "doc_id": "q4-report",
        "filename": "Q4_2024_Financial_Report.pdf",
        "page": 5,
        "score": 0.94,
        "metadata": {...}
    },
    {
        "doc_id": "sales-analysis",
        "filename": "Sales_Performance_Analysis.pdf",
        "page": 12,
        "score": 0.89,
        "metadata": {...}
    },
    {
        "doc_id": "market-trends",
        "filename": "Market_Trends_Q4.pdf",
        "page": 3,
        "score": 0.85,
        "metadata": {...}
    }
]
```

### LLM Context:
```
[Document 1: Q4_2024_Financial_Report.pdf, Page 5]
Section: Executive Summary
Relevance: 0.94

Revenue increased 23% year-over-year to $45.2M in Q4 2024.
Growth was driven by three primary factors: strong product sales (+18%),
expanded market presence (+12 new regions), and improved operational
efficiency (margins up 3.5%). All business units exceeded targets...

[Document 2: Sales_Performance_Analysis.pdf, Page 12]
Section: Product Performance
Relevance: 0.89

Product line performance exceeded expectations in Q4. Flagship products
contributed 65% of revenue growth, with new product launches adding
another 20%. Customer retention improved to 94%, up from 89% in Q3...

[Document 3: Market_Trends_Q4.pdf, Page 3]
Section: Industry Analysis
Relevance: 0.85

Market conditions in Q4 2024 were favorable for growth. Industry-wide
demand increased 15% compared to Q3, driven by seasonal purchasing and
pent-up demand from earlier supply chain constraints...
```

### LLM Response:
```
Revenue growth in Q4 2024 was driven by three key factors [1]. First,
strong product sales increased 18% year-over-year [1], with flagship
products contributing 65% of total growth [2]. Second, the company expanded
into 12 new regions [1], broadening market presence. Third, operational
improvements resulted in 3.5% higher margins [1]. These internal factors
were supported by favorable market conditions, including 15% industry-wide
demand growth [3] and improved supply chain stability [3]. Customer
retention also improved significantly to 94% [2], indicating strong
product-market fit.
```

### Parsed Response:
```json
{
  "answer": "Revenue growth in Q4 2024 was driven by three key factors [1]...",
  "citations": [
    {
      "id": 1,
      "filename": "Q4_2024_Financial_Report.pdf",
      "page": 5,
      "positions": [[62, 65], [142, 145], [238, 241], [311, 314]]
    },
    {
      "id": 2,
      "filename": "Sales_Performance_Analysis.pdf",
      "page": 12,
      "positions": [[175, 178], [428, 431]]
    },
    {
      "id": 3,
      "filename": "Market_Trends_Q4.pdf",
      "page": 3,
      "positions": [[360, 363], [410, 413]]
    }
  ]
}
```

### Frontend Display:
- Left panel: Answer text with clickable `[1]`, `[2]`, `[3]` badges
- Right panel: 3 reference cards with thumbnails, filenames, Details buttons
- Hover `[1]` → Highlights Q4 report card
- Hover Q4 report card → Highlights all `[1]` citations in answer

---

**End of Architecture Document**
