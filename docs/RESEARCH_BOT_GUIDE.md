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
