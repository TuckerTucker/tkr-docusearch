# Citation Parser Interface Contract

**Provider:** Agent 3 - Citation Parser
**Consumers:** Agent 4 - Research API, Agent 9 - Frontend Integration
**File:** `src/research/citation_parser.py`
**Status:** Wave 1 Foundation Layer
**Version:** 1.0
**Last Updated:** 2025-10-17

---

## Overview

The Citation Parser extracts inline citation markers `[N]` from LLM-generated text, validates citation integrity, and creates mappings between citations and source documents for bidirectional highlighting in the frontend.

---

## Interface Definition

### Data Classes

```python
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Citation:
    """Represents a single citation marker in text"""
    citation_id: int  # Citation number (1, 2, 3...)
    start_pos: int  # Character start position in text
    end_pos: int  # Character end position in text
    marker: str  # Original marker text (e.g., "[1]", "[2]")

    def __repr__(self) -> str:
        return f"Citation(id={self.citation_id}, pos={self.start_pos}-{self.end_pos}, marker='{self.marker}')"

@dataclass
class CitationCluster:
    """Represents multiple citations in same location"""
    citations: List[Citation]  # e.g., [Citation(1), Citation(2)]
    start_pos: int  # Start of cluster
    end_pos: int  # End of cluster
    cluster_marker: str  # e.g., "[1][2]" or "[1], [2]"

    def citation_ids(self) -> List[int]:
        """Get list of citation IDs in cluster"""
        return [c.citation_id for c in self.citations]

@dataclass
class Sentence:
    """Represents a sentence containing citations"""
    text: str  # Sentence text
    start_pos: int  # Character start position in full text
    end_pos: int  # Character end position in full text
    citations: List[Citation]  # Citations in this sentence

    def citation_ids(self) -> List[int]:
        """Get unique citation IDs in sentence"""
        return sorted(set(c.citation_id for c in self.citations))

@dataclass
class ParsedAnswer:
    """Parsed LLM answer with citation mappings"""
    original_text: str  # Full LLM-generated text
    clean_text: str  # Text with citations removed (optional use)
    citations: List[Citation]  # All citations found
    sentences: List[Sentence]  # Sentences with their citations
    citation_to_sentences: Dict[int, List[Sentence]]  # Map citation ID → sentences
    sentence_to_citations: Dict[int, List[Citation]]  # Map sentence index → citations

    def get_citations_in_range(self, start: int, end: int) -> List[Citation]:
        """Get all citations within character range"""
        pass

    def get_sentence_for_citation(self, citation_id: int) -> Optional[Sentence]:
        """Get first sentence containing citation"""
        pass

    def validate(self, num_sources: int) -> bool:
        """
        Validate citation integrity

        Args:
            num_sources: Number of source documents available

        Returns:
            True if all citations are valid

        Checks:
            - All citation IDs are in range [1, num_sources]
            - No duplicate markers at same position
            - Citations are well-formed [N]
        """
        pass
```

### Class: `CitationParser`

```python
import re
from typing import List, Dict, Optional

class CitationParser:
    """Parses citation markers from LLM-generated text"""

    # Regex patterns
    CITATION_PATTERN = r'\[(\d+)\]'  # Matches [1], [2], etc.
    CITATION_CLUSTER_PATTERN = r'(\[\d+\](?:\s*,?\s*\[\d+\])*)'  # [1][2] or [1], [2]
    SENTENCE_PATTERN = r'[^.!?]+[.!?]'  # Simple sentence boundary

    def __init__(self):
        """Initialize citation parser"""
        pass

    def parse(self, text: str, num_sources: int) -> ParsedAnswer:
        """
        Parse citations from LLM-generated answer

        Args:
            text: LLM-generated text with inline citations
            num_sources: Number of source documents (for validation)

        Returns:
            ParsedAnswer with citation mappings

        Raises:
            ValueError: If citations are malformed or invalid

        Example:
            >>> parser = CitationParser()
            >>> text = "Paris is the capital [1]. It is known for the Eiffel Tower [2]."
            >>> parsed = parser.parse(text, num_sources=2)
            >>> len(parsed.citations)  # 2
            >>> len(parsed.sentences)  # 2
        """
        pass

    def extract_citations(self, text: str) -> List[Citation]:
        """
        Extract all citation markers from text

        Args:
            text: Text containing citations

        Returns:
            List of Citation objects in order of appearance

        Example:
            >>> citations = parser.extract_citations("Fact [1]. Another fact [2][3].")
            >>> citations
            [Citation(id=1, pos=5-8), Citation(id=2, pos=24-27), Citation(id=3, pos=27-30)]
        """
        pass

    def extract_citation_clusters(self, text: str) -> List[CitationCluster]:
        """
        Extract citation clusters (multiple citations together)

        Args:
            text: Text containing citations

        Returns:
            List of CitationCluster objects

        Example:
            >>> clusters = parser.extract_citation_clusters("Fact [1][2].")
            >>> clusters[0].citation_ids()
            [1, 2]
        """
        pass

    def split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences

        Args:
            text: Text to split

        Returns:
            List of sentences

        Note:
            Uses simple regex, handles common abbreviations (Dr., Mr., etc.)

        Example:
            >>> sentences = parser.split_into_sentences("First. Second. Third.")
            >>> len(sentences)  # 3
        """
        pass

    def map_citations_to_sentences(
        self,
        text: str,
        citations: List[Citation]
    ) -> List[Sentence]:
        """
        Map citations to sentences they appear in

        Args:
            text: Original text
            citations: Extracted citations

        Returns:
            List of Sentence objects with their citations

        Example:
            >>> sentences = parser.map_citations_to_sentences(text, citations)
            >>> sentences[0].citation_ids()
            [1]
        """
        pass

    def create_bidirectional_map(
        self,
        sentences: List[Sentence]
    ) -> Tuple[Dict[int, List[Sentence]], Dict[int, List[Citation]]]:
        """
        Create bidirectional mappings for frontend highlighting

        Args:
            sentences: Sentences with citations

        Returns:
            Tuple of:
                - citation_to_sentences: Map citation ID → sentences containing it
                - sentence_to_citations: Map sentence index → citations in it

        Example:
            >>> citation_map, sentence_map = parser.create_bidirectional_map(sentences)
            >>> citation_map[1]  # All sentences with citation [1]
            [Sentence(text="Paris is the capital [1].", ...)]
            >>> sentence_map[0]  # All citations in first sentence
            [Citation(id=1, ...)]
        """
        pass

    def remove_citations(self, text: str) -> str:
        """
        Remove all citation markers from text

        Args:
            text: Text with citations

        Returns:
            Clean text without citations

        Example:
            >>> clean = parser.remove_citations("Paris [1] is nice [2].")
            >>> clean
            "Paris is nice ."
        """
        pass

    def validate_citations(
        self,
        citations: List[Citation],
        num_sources: int
    ) -> Tuple[bool, List[str]]:
        """
        Validate citation integrity

        Args:
            citations: Extracted citations
            num_sources: Number of source documents

        Returns:
            Tuple of (is_valid, error_messages)

        Validation checks:
            1. All citation IDs in range [1, num_sources]
            2. No duplicate markers at same position
            3. Citations are well-formed (regex match)

        Example:
            >>> valid, errors = parser.validate_citations(citations, num_sources=2)
            >>> if not valid:
            ...     print("Errors:", errors)
            ["Citation [3] exceeds number of sources (2)"]
        """
        pass

    def format_for_frontend(self, parsed: ParsedAnswer) -> Dict[str, Any]:
        """
        Format parsed answer for frontend consumption

        Args:
            parsed: ParsedAnswer object

        Returns:
            JSON-serializable dict for API response

        Structure:
            {
                "text": "original text",
                "citations": [
                    {"id": 1, "start": 10, "end": 13, "marker": "[1]"},
                    ...
                ],
                "sentences": [
                    {
                        "text": "First sentence [1].",
                        "start": 0,
                        "end": 19,
                        "citation_ids": [1]
                    },
                    ...
                ],
                "citation_map": {
                    "1": [{"sentence_index": 0, "sentence_text": "..."}],
                    ...
                }
            }

        Example:
            >>> frontend_data = parser.format_for_frontend(parsed)
            >>> print(frontend_data["citation_map"]["1"])
            [{"sentence_index": 0, "sentence_text": "Paris is the capital [1]."}]
        """
        pass
```

---

## Usage Examples

### Basic Parsing

```python
from src.research.citation_parser import CitationParser

parser = CitationParser()

# LLM-generated answer
answer_text = """
The capital of France is Paris [1], located on the Seine River [1]. It has
been the capital since 987 AD [2] and is known for landmarks like the Eiffel
Tower, Louvre Museum, and Notre-Dame Cathedral [2].
"""

# Parse with 2 sources available
parsed = parser.parse(answer_text, num_sources=2)

print(f"Found {len(parsed.citations)} citations")  # 4
print(f"In {len(parsed.sentences)} sentences")  # 2

# Access citations
for citation in parsed.citations:
    print(f"{citation.marker} at position {citation.start_pos}")
# [1] at position 32
# [1] at position 66
# [2] at position 105
# [2] at position 184
```

### Citation Validation

```python
# Parse with validation
try:
    parsed = parser.parse(answer_text, num_sources=2)
    is_valid = parsed.validate(num_sources=2)
    print(f"Citations valid: {is_valid}")  # True
except ValueError as e:
    print(f"Invalid citations: {e}")

# Example with invalid citation
bad_text = "Paris is great [5]."  # Only 2 sources
try:
    parsed = parser.parse(bad_text, num_sources=2)
except ValueError as e:
    print(e)  # "Citation [5] exceeds number of sources (2)"
```

### Sentence-Citation Mapping

```python
parsed = parser.parse(answer_text, num_sources=2)

# Get sentences containing citation [1]
sentences_with_1 = parsed.citation_to_sentences[1]
for sentence in sentences_with_1:
    print(sentence.text)
# "The capital of France is Paris [1], located on the Seine River [1]."

# Get citations in first sentence
first_sentence = parsed.sentences[0]
print(f"Sentence: {first_sentence.text}")
print(f"Citations: {first_sentence.citation_ids()}")
# Citations: [1]
```

### Citation Clusters

```python
# Text with multiple citations together
clustered_text = "This is supported by multiple sources [1][2][3]."

parsed = parser.parse(clustered_text, num_sources=3)

# Extract clusters
clusters = parser.extract_citation_clusters(clustered_text)
print(clusters[0].citation_ids())  # [1, 2, 3]
print(clusters[0].cluster_marker)  # "[1][2][3]"
```

### Frontend Formatting

```python
parsed = parser.parse(answer_text, num_sources=2)

# Format for API response
frontend_data = parser.format_for_frontend(parsed)

# Send to frontend
return {
    "answer": frontend_data["text"],
    "citations": frontend_data["citations"],
    "citation_map": frontend_data["citation_map"],
    "sources": [...]  # From context builder
}
```

---

## Integration Points

### Consumed By: Research API (Agent 4)

```python
# src/api/research.py
from src.research.citation_parser import CitationParser

@app.post("/api/research/ask")
async def ask_research_question(request: ResearchRequest):
    # Build context
    context = await context_builder.build_context(request.query)

    # Generate answer
    llm_response = await llm_client.complete_with_context(
        query=request.query,
        context=context.formatted_text,
        system_message=RESEARCH_SYSTEM_PROMPT
    )

    # Parse citations
    parser = CitationParser()
    parsed_answer = parser.parse(
        text=llm_response.content,
        num_sources=len(context.sources)
    )

    # Format for frontend
    return {
        "answer": parsed_answer.original_text,
        "citations": parser.format_for_frontend(parsed_answer)["citations"],
        "citation_map": parser.format_for_frontend(parsed_answer)["citation_map"],
        "sources": [source.to_dict() for source in context.sources]
    }
```

### Consumed By: Frontend Integration (Agent 9)

```javascript
// src/frontend/research-controller.js

// API response
const response = await fetch('/api/research/ask', {...});
const data = await response.json();

// data.citation_map structure:
// {
//   "1": [{"sentence_index": 0, "sentence_text": "..."}],
//   "2": [{"sentence_index": 1, "sentence_text": "..."}]
// }

// Use for bidirectional highlighting
function setupHighlighting(citationMap) {
    // Hover on citation → highlight reference
    document.querySelectorAll('.citation-marker').forEach(marker => {
        marker.addEventListener('mouseenter', (e) => {
            const citationId = e.target.dataset.citationId;
            highlightReference(citationId);
        });
    });

    // Hover on reference → highlight sentences
    document.querySelectorAll('.reference-card').forEach(card => {
        card.addEventListener('mouseenter', (e) => {
            const citationId = e.target.dataset.citationId;
            const sentences = citationMap[citationId];
            sentences.forEach(s => highlightSentence(s.sentence_index));
        });
    });
}
```

---

## Edge Cases & Handling

### Multiple Citations in Same Location

```python
# Input: "Fact [1][2][3]."
# Output: 3 separate Citation objects at consecutive positions

parsed = parser.parse("Fact [1][2][3].", num_sources=3)
print(len(parsed.citations))  # 3
print([c.citation_id for c in parsed.citations])  # [1, 2, 3]
```

### Citations at Sentence Boundaries

```python
# Input: "Sentence one [1]. Sentence two [2]."
# Ensure citation belongs to correct sentence

parsed = parser.parse("Sentence one [1]. Sentence two [2].", num_sources=2)
print(parsed.sentences[0].citation_ids())  # [1]
print(parsed.sentences[1].citation_ids())  # [2]
```

### No Citations

```python
# Input: "Text without any citations."
# Should return empty citations list, not error

parsed = parser.parse("Text without citations.", num_sources=0)
print(len(parsed.citations))  # 0
print(len(parsed.sentences))  # 1
```

### Invalid Citation Numbers

```python
# Input: "Fact [99]." with only 2 sources
# Should raise ValueError

try:
    parsed = parser.parse("Fact [99].", num_sources=2)
except ValueError as e:
    print(e)  # "Citation [99] exceeds number of sources (2)"
```

### Malformed Citations

```python
# Input: "Fact [abc]." (non-numeric)
# Should be ignored or raise error

text_with_bad_citation = "Fact [abc]."
parsed = parser.parse(text_with_bad_citation, num_sources=0)
print(len(parsed.citations))  # 0 (ignored as malformed)
```

---

## Testing Requirements

### Unit Tests

1. **Citation Extraction**
   - Extract single citation `[1]`
   - Extract multiple citations `[1][2][3]`
   - Extract citations with spaces `[1] [2]`
   - Ignore malformed citations `[abc]`, `[]`

2. **Sentence Splitting**
   - Split on periods, exclamation marks, question marks
   - Handle abbreviations (Dr., Mr., etc.)
   - Handle decimals (3.14 should not split)

3. **Citation Validation**
   - Valid citations pass (1 to num_sources)
   - Out-of-range citations fail
   - Duplicate positions detected

4. **Bidirectional Mapping**
   - Citation → sentences mapping correct
   - Sentence → citations mapping correct
   - Multiple citations per sentence handled

5. **Frontend Formatting**
   - JSON structure matches expected format
   - All fields present and correctly typed

### Integration Tests

1. **Full Parse Flow**
   - Real LLM output parsed successfully
   - All citations mapped to sentences
   - Frontend format valid

2. **Edge Cases**
   - Empty text
   - No citations
   - All citations in one sentence
   - One citation per sentence

---

## Performance Requirements

- **Parsing:** <10ms for 1000-word answer
- **Sentence Splitting:** <5ms for 1000 words
- **Citation Extraction:** <5ms for 50 citations
- **Validation:** <1ms for 50 citations

---

## Dependencies

```python
# requirements.txt
# No external dependencies - uses only Python stdlib (re module)
```

---

## Validation Gates (Wave 1)

- [ ] All unit tests pass
- [ ] Edge cases handled correctly
- [ ] Frontend format matches expected structure
- [ ] Validation catches all error conditions
- [ ] Performance requirements met
- [ ] Bidirectional mapping verified
- [ ] Citation clusters extracted properly

---

## Notes

- Uses simple regex for sentence splitting (may not handle all edge cases)
- Could be enhanced with spaCy/NLTK for better sentence boundary detection
- Citation format `[N]` is strict - other formats ignored
- Frontend highlighting depends on accurate sentence-citation mapping
- Validation is critical - invalid citations break frontend highlighting
