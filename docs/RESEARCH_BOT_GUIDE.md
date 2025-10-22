# Research Bot User Guide

**Version:** 1.0
**Last Updated:** 2025-10-17

---

## Overview

The Research Bot is an AI-powered feature that allows you to ask questions about your document collection and receive comprehensive answers with inline citations. It combines semantic search with Large Language Models (LLMs) to provide factual, well-cited responses.

### Key Features

- **Natural Language Queries** - Ask questions in plain English
- **AI-Generated Answers** - Comprehensive responses from GPT-4, Claude, or other LLMs
- **Inline Citations** - Every fact cited with `[1]`, `[2]`, etc.
- **Source Documents** - View and navigate to original documents
- **Bidirectional Highlighting** - Hover citations to see sources, hover sources to see citations
- **Multiple View Modes** - Detailed view with thumbnails or simple list view

---

## Getting Started

### Prerequisites

1. **Documents Uploaded** - Upload PDF, DOCX, PPTX, or audio files to your collection
2. **LLM API Key** - OpenAI, Anthropic, or Google API key configured
3. **Research API Running** - Backend service must be active

### Accessing the Research Page

Navigate to: `http://localhost:8000/research.html`

---

## Using the Research Bot

### 1. Submit a Query

1. Type your question in the search box
2. Click "Ask" button or press Enter
3. Wait for the AI to generate an answer (typically 2-3 seconds)

**Example Queries:**
- "What caused the 2008 financial crisis?"
- "Summarize the key findings in the climate report"
- "What are the benefits of renewable energy?"
- "How does the approval process work?"

### 2. Read the Answer

The AI-generated answer appears in the left panel with:
- **Main Answer** - 2-3 paragraphs addressing your question
- **Inline Citations** - Numbered markers like `[1]`, `[2]` showing sources
- **Professional Tone** - Factual and objective language

### 3. Explore Sources

The right panel shows all source documents cited in the answer:

**Detailed View (Default):**
- Document thumbnail (64px height)
- File type badge (PDF, DOCX, etc.)
- Filename
- Page number and upload date
- "Details" button to view full document

**Simple View:**
- Compact list with just filename and details button
- Toggle using "Simple" button

### 4. Interactive Highlighting

**Hover on Citation Marker:**
- Citation changes to highlighted color
- Corresponding reference card highlights
- Reference scrolls into view if needed

**Hover on Reference Card:**
- All citations from that source highlight
- Sentences containing those citations highlight

**Keyboard Navigation:**
- Tab through citations and references
- Enter/Space on citation to jump to reference
- Escape to clear highlights

---

## Understanding Citations

### Citation Format

Citations use numbered brackets: `[1]`, `[2]`, `[3]`

**Example:**
```
The capital of France is Paris [1], located on the Seine River [1].
It has been the capital since 987 AD [2] and is known for the
Eiffel Tower [2].
```

### What Citations Mean

- `[1]` - Fact comes from Source #1
- `[1][2]` - Fact supported by multiple sources
- Multiple `[1]` - Same source cited multiple times

### Source Information

Each citation number corresponds to a source document:

```
[1] = report.pdf, Page 3
[2] = analysis.docx, Page 12
```

---

## Advanced Features

### Switching View Modes

**Detailed View:**
- Best for visual browsing
- Shows document thumbnails
- Easier to identify documents

**Simple View:**
- More compact, fits more sources
- Faster to scan
- Better for text-only documents

Toggle: Click "Detailed" or "Simple" buttons in references panel

### Viewing Full Documents

Click "Details" button on any reference card to:
- View full document details page
- See all pages and metadata
- Play audio (for MP3/WAV)
- Navigate document structure

### Understanding Metadata

At the bottom of the answer (in browser console):
- **Processing Time** - How long the query took
- **Model Used** - Which LLM generated the answer
- **Sources Found** - Number of relevant documents
- **Context Truncated** - Whether some sources were omitted

---

## Tips for Better Results

### Writing Effective Queries

**Do:**
- ✅ Be specific: "What are the main causes of climate change?"
- ✅ Ask direct questions: "How does photosynthesis work?"
- ✅ Request summaries: "Summarize the quarterly financial report"

**Don't:**
- ❌ Be too vague: "Tell me about stuff"
- ❌ Ask multiple questions: "What is X and Y and how do they relate to Z?"
- ❌ Request opinions: "What's the best approach?" (AI sticks to facts)

### Interpreting Answers

**If Answer Says "No documents found":**
- Your collection doesn't contain relevant documents
- Try rephrasing your query
- Upload documents related to your question

**If Answer is Incomplete:**
- The AI only uses information from your documents
- Missing information means it's not in your collection
- Answer will acknowledge gaps: "The documents don't contain information about..."

**If Sources Conflict:**
- AI will present both perspectives
- Example: "Document 1 states X [1], while Document 2 indicates Y [2]"

---

## Troubleshooting

### "No relevant documents found"

**Cause:** Search didn't find matching documents
**Solution:**
- Try different keywords
- Upload relevant documents
- Check if documents are properly indexed

### "Request timed out"

**Cause:** LLM took too long to respond
**Solution:**
- Try a simpler query
- Reduce `num_sources` (requires API modification)
- Check LLM service status

### "Rate limit exceeded"

**Cause:** Too many API requests
**Solution:**
- Wait 60 seconds before trying again
- Check your LLM provider's rate limits
- Consider upgrading API tier

### Citations Don't Highlight

**Cause:** JavaScript error or missing elements
**Solution:**
- Refresh the page
- Check browser console for errors
- Ensure all scripts loaded correctly

### Answer Doesn't Match Query

**Cause:** AI misunderstood or documents don't contain answer
**Solution:**
- Rephrase query more clearly
- Check if relevant documents are uploaded
- Try breaking complex questions into simpler ones

---

## Privacy & Security

### Data Handling

- **Queries** - Sent to LLM provider (OpenAI, Anthropic, etc.)
- **Documents** - Content sent to LLM for context (within your account)
- **Answers** - Not stored (generated fresh each time)
- **API Keys** - Stored securely in environment variables

### What's Sent to LLM

Each query sends:
1. Your question
2. Excerpts from top 10 matching documents (~10,000 tokens)
3. System prompt with citation instructions

**Not Sent:**
- Full document collection
- Other user data
- Previous queries

### API Costs

Estimated costs (per query):
- **GPT-4:** $0.10 - $0.30
- **GPT-3.5:** $0.01 - $0.03
- **Claude Sonnet:** $0.03 - $0.15
- **Gemini Pro:** $0.03 - $0.10

*Costs vary based on document length and answer complexity*

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **Tab** | Navigate between elements |
| **Enter** | Submit query / Activate citation |
| **Space** | Activate citation |
| **Escape** | Clear highlights |
| **Ctrl+/** | Focus query input |

---

## Accessibility

### Screen Reader Support

- All citations have ARIA labels: "Citation 1"
- Reference cards announced: "Reference 1: filename.pdf, Page 3"
- State changes announced (loading, success, error)
- Keyboard navigation fully supported

### Keyboard Navigation

- Tab through all interactive elements
- Focus indicators visible (2px outline)
- Skip links for main content
- No mouse required

### Visual Accessibility

- High contrast mode supported
- Focus indicators meet WCAG 2.1 AA
- Color not sole means of information
- Resizable text (up to 200%)

---

## Local LLM Preprocessing

### Overview

Local LLM Preprocessing is an optional feature that uses a local language model to pre-process your document chunks before sending them to the foundation model (GPT-4, Claude, etc.). This reduces token usage, lowers API costs, and can improve answer quality by focusing on the most relevant information.

**How It Works:**
1. Search finds top 10-20 relevant document chunks
2. Local MLX model processes chunks using selected strategy
3. Processed chunks sent to foundation model for final answer
4. You save ~60% on foundation model API costs

### Benefits

**Cost Savings:**
- Reduce foundation model API calls by ~60%
- Process more documents within token budget
- Pay-per-token savings on GPT-4/Claude

**Improved Quality:**
- Filter out low-relevance chunks
- Focus foundation model on key information
- Better citation accuracy

**Privacy:**
- Initial processing happens locally on your Mac
- Only filtered/compressed content sent to API
- Reduce data transmission to third parties

### Preprocessing Strategies

**Compression Strategy** (Default)
- Extracts key facts from each chunk
- Reduces token count by 30-50%
- Preserves all important information
- Best for: General queries with many sources

**Filtering Strategy**
- Scores each chunk 0-10 for relevance
- Keeps only high-scoring chunks (threshold: 7.0+)
- Retains 40-60% of original chunks
- Best for: Focused queries with specific topics

**Synthesis Strategy**
- Combines multiple chunks into organized summary
- Reduces token count by 90%+
- Creates cross-document knowledge graph
- Best for: Broad queries requiring synthesis across many documents

### Setup Instructions

**Prerequisites:**
- Mac with M1/M2/M3 chip (Metal GPU required)
- 16GB RAM minimum
- ~8GB free disk space for MLX model

**Step 1: Install MLX-LM**

```bash
pip install mlx-lm>=0.26.3
```

**Step 2: Download MLX Model**

```bash
huggingface-cli download InferenceIllusionist/gpt-oss-20b-MLX-4bit
```

This downloads the MLX-optimized 4-bit quantized model (~8GB).

**Step 3: Configure Environment Variables**

Edit your `.env` file:

```bash
# Enable MLX local LLM for preprocessing
LLM_PROVIDER=mlx
MLX_MODEL_PATH=/Users/[your-username]/.cache/huggingface/hub/models--InferenceIllusionist--gpt-oss-20b-MLX-4bit

# Enable preprocessing
LOCAL_PREPROCESS_ENABLED=true
LOCAL_PREPROCESS_STRATEGY=compress
LOCAL_PREPROCESS_THRESHOLD=7.0
LOCAL_PREPROCESS_MAX_SOURCES=20
```

**Step 4: Restart Research API**

```bash
./scripts/start-all.sh
```

Or restart just the API:

```bash
pkill -f "research.py"
./scripts/start-research-api.sh
```

**Step 5: Verify Setup**

Submit a test query and check for preprocessing badge:
- Look for "⚡ Preprocessed with compress" badge below answer
- Check token reduction percentage
- Verify preprocessing latency is reasonable (<3s)

### Configuration Options

**Strategy Selection**

```bash
# Compression (default) - 30-50% reduction
LOCAL_PREPROCESS_STRATEGY=compress

# Filtering - 40-60% retention
LOCAL_PREPROCESS_STRATEGY=filter

# Synthesis - 90%+ reduction
LOCAL_PREPROCESS_STRATEGY=synthesize
```

**Threshold Tuning** (Filtering strategy only)

```bash
# Higher = more aggressive filtering (fewer chunks kept)
LOCAL_PREPROCESS_THRESHOLD=8.0  # Very strict
LOCAL_PREPROCESS_THRESHOLD=7.0  # Default
LOCAL_PREPROCESS_THRESHOLD=6.0  # Lenient
```

**Max Sources**

```bash
# Maximum chunks to send to preprocessor
LOCAL_PREPROCESS_MAX_SOURCES=20  # Default
LOCAL_PREPROCESS_MAX_SOURCES=30  # More comprehensive
LOCAL_PREPROCESS_MAX_SOURCES=10  # Faster processing
```

**Performance Expectations:**
- Compression: <3s for 10 chunks
- Filtering: <3s for 20 chunks
- Synthesis: <5s for 15 chunks

### Viewing Preprocessing Metrics

When preprocessing is enabled, you'll see metrics below each answer:

**Preprocessing Badge:**
```
⚡ Preprocessed with compress
```

**Token Reduction:**
```
45.2% token reduction
```

**Processing Time:**
```
Preprocessing: 2847ms
```

These metrics help you understand:
- Which strategy was used
- How much you saved on API costs
- Processing overhead time

### Troubleshooting

**"MLX model not found"**

**Cause:** Model path incorrect or model not downloaded

**Solution:**
```bash
# Check model exists
ls -la ~/.cache/huggingface/hub/models--InferenceIllusionist--gpt-oss-20b-MLX-4bit

# Verify path in .env matches exactly
cat .env | grep MLX_MODEL_PATH

# Re-download if missing
huggingface-cli download InferenceIllusionist/gpt-oss-20b-MLX-4bit
```

**"Preprocessing taking too long" (>10s)**

**Cause:** Too many sources or slow model

**Solution:**
```bash
# Reduce max sources
LOCAL_PREPROCESS_MAX_SOURCES=10

# Or disable preprocessing temporarily
LOCAL_PREPROCESS_ENABLED=false

# Check CPU usage - MLX should use Metal GPU
```

**"Citation accuracy decreased"**

**Cause:** Synthesis strategy may lose chunk-level citations

**Solution:**
```bash
# Switch to compression or filtering
LOCAL_PREPROCESS_STRATEGY=compress

# Or disable preprocessing
LOCAL_PREPROCESS_ENABLED=false
```

**"API won't start with preprocessing enabled"**

**Cause:** Missing MLX dependencies or model

**Solution:**
1. Check API logs: `tail -f logs/research-api.log`
2. Disable preprocessing: `LOCAL_PREPROCESS_ENABLED=false`
3. Restart API: `./scripts/start-all.sh`
4. Install MLX: `pip install mlx-lm>=0.26.3`
5. Re-enable preprocessing

**"Preprocessing metrics not showing in UI"**

**Cause:** Frontend not updated or preprocessing disabled

**Solution:**
- Verify `LOCAL_PREPROCESS_ENABLED=true` in `.env`
- Restart API: `./scripts/start-all.sh`
- Hard refresh browser: Cmd+Shift+R
- Check browser console for errors

### Disabling Preprocessing

To temporarily disable preprocessing:

```bash
# In .env file
LOCAL_PREPROCESS_ENABLED=false
```

Then restart the API. All other functionality remains unchanged - this is a zero-breaking-change feature.

---

## Limitations

### Current Limitations

1. **One Query at a Time** - No history or multi-turn conversations
2. **No Streaming** - Full answer returned at once (2-3 second wait)
3. **10 Source Limit** - Maximum 10 documents cited per answer
4. **English Only** - Optimized for English documents and queries
5. **No Export** - Can't export answers as PDF (yet)

### Known Issues

- **Page Extraction** - May include content from adjacent pages if page markers missing
- **Long Documents** - Very long documents may be truncated to fit token budget
- **Complex Tables** - Tables may not format perfectly in answers

---

## FAQ

### Q: How does the Research Bot work?

A: It combines two AI systems:
1. **ColPali Search** - Finds relevant pages in your documents
2. **Large Language Model** - Reads those pages and writes an answer with citations

### Q: Can I use it offline?

A: No, requires internet connection to access LLM APIs (OpenAI, Anthropic, etc.)

### Q: Are my documents private?

A: Yes, documents are stored locally. Only relevant excerpts are sent to LLM for each query.

### Q: Can I choose which LLM to use?

A: Currently configured by administrator. Supports GPT-4, Claude, Gemini, and local models.

### Q: Why are some facts not cited?

A: The AI should cite all facts. If citations are missing, it may be an LLM error. Try regenerating.

### Q: Can it summarize a specific document?

A: Yes! Ask: "Summarize [filename]" (though general queries work better)

### Q: What if sources conflict?

A: The AI will present both perspectives with citations: "Doc 1 says X [1], but Doc 2 says Y [2]"

### Q: Can I save my research?

A: Not currently - answers are generated fresh each time. Copy/paste to save.

### Q: What is local LLM preprocessing?

A: It's an optional feature that uses a local model (running on your Mac) to pre-process document chunks before sending them to GPT-4/Claude. This reduces token usage by ~60%, saving API costs.

### Q: Do I need preprocessing enabled?

A: No, it's completely optional. The Research Bot works great without it. Enable preprocessing if you want to:
- Reduce API costs (~60% savings)
- Process more documents within token limits
- Keep more data local for privacy

### Q: Will preprocessing make queries slower?

A: Slightly. Preprocessing adds 2-5 seconds, but you save on foundation model API calls. Total query time is usually still under 5 seconds.

### Q: Which preprocessing strategy should I use?

A:
- **Compression** (default) - Best for most queries, 30-50% token reduction
- **Filtering** - Best for focused queries with clear topics
- **Synthesis** - Best for broad queries requiring cross-document analysis

### Q: Can I use preprocessing without an MLX model?

A: No, preprocessing requires an MLX-compatible model and Mac with M1+ chip. Without MLX, preprocessing is automatically disabled and the Research Bot works normally.

---

## Feedback & Support

### Reporting Issues

Found a bug? Open an issue at:
https://github.com/anthropics/claude-code/issues

Include:
- Your query
- Expected vs actual answer
- Browser and OS
- Console errors (if any)

### Feature Requests

Suggest improvements:
- Multi-turn conversations
- Answer history
- Export to PDF
- More citation formats
- Custom prompts

---

## Version History

**v1.0 (2025-10-17)**
- Initial release
- GPT-4, Claude, Gemini support
- Bidirectional highlighting
- Detailed/Simple view modes
- WCAG 2.1 AA accessibility

---

## Additional Resources

- **API Documentation:** `/docs/API_REFERENCE.md`
- **Developer Guide:** `/docs/CONTRIBUTING.md`
- **Architecture:** `/.context-kit/_specs/research-bot-architecture.md`

---

**Happy Researching! 🔍**
