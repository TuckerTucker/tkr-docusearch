"""
Citation Parser for extracting inline citation markers from LLM-generated text.

Parses citations in format [N], creates bidirectional mappings for highlighting,
and validates citation integrity.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)


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
    citations: List[Citation] = field(default_factory=list)

    def citation_ids(self) -> List[int]:
        """Get unique citation IDs in sentence"""
        return sorted(set(c.citation_id for c in self.citations))


@dataclass
class ParsedAnswer:
    """Parsed LLM answer with citation mappings"""

    original_text: str  # Full LLM-generated text
    clean_text: str  # Text with citations removed
    citations: List[Citation]  # All citations found
    sentences: List[Sentence]  # Sentences with their citations
    citation_to_sentences: Dict[int, List[Sentence]] = field(default_factory=dict)
    sentence_to_citations: Dict[int, List[Citation]] = field(default_factory=dict)

    def get_citations_in_range(self, start: int, end: int) -> List[Citation]:
        """Get all citations within character range"""
        return [c for c in self.citations if c.start_pos >= start and c.end_pos <= end]

    def get_sentence_for_citation(self, citation_id: int) -> Optional[Sentence]:
        """Get first sentence containing citation"""
        sentences = self.citation_to_sentences.get(citation_id, [])
        return sentences[0] if sentences else None

    def validate(self, num_sources: int) -> bool:
        """
        Validate citation integrity

        Args:
            num_sources: Number of source documents available

        Returns:
            True if all citations are valid
        """
        is_valid, errors = self._validate_citations(num_sources)

        if not is_valid:
            logger.warning("Citation validation failed", errors=errors)

        return is_valid

    def _validate_citations(self, num_sources: int) -> Tuple[bool, List[str]]:
        """Internal validation logic"""
        errors = []

        for citation in self.citations:
            # Check citation ID in range
            if citation.citation_id < 1 or citation.citation_id > num_sources:
                errors.append(
                    f"Citation [{citation.citation_id}] exceeds number of sources ({num_sources})"
                )

        return len(errors) == 0, errors


class CitationParser:
    """Parses citation markers from LLM-generated text"""

    # Regex patterns
    CITATION_PATTERN = r"\[(\d+)\]"  # Matches [1], [2], etc.
    SENTENCE_PATTERN = r"[^.!?]+[.!?]+"  # Simple sentence boundary

    # Common abbreviations that shouldn't split sentences
    ABBREVIATIONS = {"Dr", "Mr", "Mrs", "Ms", "Prof", "Sr", "Jr", "etc", "vs", "Inc", "Ltd"}

    def __init__(self):
        """Initialize citation parser"""
        self.citation_regex = re.compile(self.CITATION_PATTERN)
        self.sentence_regex = re.compile(self.SENTENCE_PATTERN)

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
        """
        logger.debug("Parsing citations from answer", text_length=len(text))

        # Extract citations
        citations = self.extract_citations(text)

        logger.debug("Extracted citations", num_citations=len(citations))

        # Validate citations
        is_valid, errors = self.validate_citations(citations, num_sources)
        if not is_valid:
            raise ValueError(f"Invalid citations: {', '.join(errors)}")

        # Split into sentences
        sentences = self.map_citations_to_sentences(text, citations)

        # Create bidirectional mappings
        citation_to_sentences, sentence_to_citations = self.create_bidirectional_map(sentences)

        # Remove citations for clean text
        clean_text = self.remove_citations(text)

        parsed = ParsedAnswer(
            original_text=text,
            clean_text=clean_text,
            citations=citations,
            sentences=sentences,
            citation_to_sentences=citation_to_sentences,
            sentence_to_citations=sentence_to_citations,
        )

        logger.info(
            "Citation parsing complete", num_citations=len(citations), num_sentences=len(sentences)
        )

        return parsed

    def extract_citations(self, text: str) -> List[Citation]:
        """
        Extract all citation markers from text

        Args:
            text: Text containing citations

        Returns:
            List of Citation objects in order of appearance
        """
        citations = []

        for match in self.citation_regex.finditer(text):
            citation_id = int(match.group(1))
            citation = Citation(
                citation_id=citation_id,
                start_pos=match.start(),
                end_pos=match.end(),
                marker=match.group(0),
            )
            citations.append(citation)

        return citations

    def extract_citation_clusters(self, text: str) -> List[CitationCluster]:
        """
        Extract citation clusters (multiple citations together)

        Args:
            text: Text containing citations

        Returns:
            List of CitationCluster objects
        """
        # Pattern for clusters: [1][2] or [1], [2]
        cluster_pattern = r"(\[\d+\](?:\s*,?\s*\[\d+\])*)"
        clusters = []

        for match in re.finditer(cluster_pattern, text):
            cluster_text = match.group(0)
            cluster_citations = self.extract_citations(cluster_text)

            if len(cluster_citations) > 1:
                cluster = CitationCluster(
                    citations=cluster_citations,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    cluster_marker=cluster_text,
                )
                clusters.append(cluster)

        return clusters

    def split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Simple regex-based splitting
        sentences = []
        current_pos = 0

        for match in self.sentence_regex.finditer(text):
            sentence = match.group(0).strip()

            # Check if this is a false split (abbreviation)
            words = sentence.split()
            if words and any(words[-1].rstrip(".") in self.ABBREVIATIONS for words in [words]):
                # Might be abbreviation, continue
                continue

            sentences.append(sentence)
            current_pos = match.end()

        # Add remaining text if any
        if current_pos < len(text):
            remaining = text[current_pos:].strip()
            if remaining:
                sentences.append(remaining)

        return sentences

    def map_citations_to_sentences(self, text: str, citations: List[Citation]) -> List[Sentence]:
        """
        Map citations to sentences they appear in

        Args:
            text: Original text
            citations: Extracted citations

        Returns:
            List of Sentence objects with their citations
        """
        # Split into sentences with positions
        sentence_matches = list(self.sentence_regex.finditer(text))

        if not sentence_matches:
            # No sentence boundaries found, treat whole text as one sentence
            sentence_matches = [
                type(
                    "Match",
                    (),
                    {
                        "group": lambda self, n=0: text,
                        "start": lambda self: 0,
                        "end": lambda self: len(text),
                    },
                )()
            ]

        sentences = []
        citation_index = 0

        for match in sentence_matches:
            sentence_text = match.group(0).strip()
            sentence_start = match.start()
            sentence_end = match.end()

            # Find citations in this sentence
            sentence_citations = []

            while citation_index < len(citations):
                citation = citations[citation_index]

                if citation.start_pos >= sentence_start and citation.end_pos <= sentence_end:
                    sentence_citations.append(citation)
                    citation_index += 1
                elif citation.start_pos >= sentence_end:
                    # Citation is in next sentence
                    break
                else:
                    # Skip citation (shouldn't happen)
                    citation_index += 1

            sentence = Sentence(
                text=sentence_text,
                start_pos=sentence_start,
                end_pos=sentence_end,
                citations=sentence_citations,
            )
            sentences.append(sentence)

        return sentences

    def create_bidirectional_map(
        self, sentences: List[Sentence]
    ) -> Tuple[Dict[int, List[Sentence]], Dict[int, List[Citation]]]:
        """
        Create bidirectional mappings for frontend highlighting

        Args:
            sentences: Sentences with citations

        Returns:
            Tuple of:
                - citation_to_sentences: Map citation ID → sentences containing it
                - sentence_to_citations: Map sentence index → citations in it
        """
        citation_to_sentences: Dict[int, List[Sentence]] = {}
        sentence_to_citations: Dict[int, List[Citation]] = {}

        for idx, sentence in enumerate(sentences):
            # Map sentence index to its citations
            sentence_to_citations[idx] = sentence.citations

            # Map each citation to sentences containing it
            for citation in sentence.citations:
                if citation.citation_id not in citation_to_sentences:
                    citation_to_sentences[citation.citation_id] = []
                citation_to_sentences[citation.citation_id].append(sentence)

        return citation_to_sentences, sentence_to_citations

    def remove_citations(self, text: str) -> str:
        """
        Remove all citation markers from text

        Args:
            text: Text with citations

        Returns:
            Clean text without citations
        """
        return self.citation_regex.sub("", text)

    def validate_citations(
        self, citations: List[Citation], num_sources: int
    ) -> Tuple[bool, List[str]]:
        """
        Validate citation integrity

        Args:
            citations: Extracted citations
            num_sources: Number of source documents

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        for citation in citations:
            # Check citation ID in range
            if citation.citation_id < 1:
                errors.append(f"Citation [{citation.citation_id}] is less than 1")
            elif citation.citation_id > num_sources:
                errors.append(
                    f"Citation [{citation.citation_id}] exceeds number of sources ({num_sources})"
                )

        # Check for well-formed markers (already validated by regex)

        return len(errors) == 0, errors

    def format_for_frontend(self, parsed: ParsedAnswer) -> Dict[str, Any]:
        """
        Format parsed answer for frontend consumption

        Args:
            parsed: ParsedAnswer object

        Returns:
            JSON-serializable dict for API response
        """
        # Format citations
        citations_data = [
            {"id": c.citation_id, "start": c.start_pos, "end": c.end_pos, "marker": c.marker}
            for c in parsed.citations
        ]

        # Format sentences
        sentences_data = [
            {
                "text": s.text,
                "start": s.start_pos,
                "end": s.end_pos,
                "citation_ids": s.citation_ids(),
            }
            for s in parsed.sentences
        ]

        # Format citation map (citation ID -> sentences)
        citation_map = {}
        for citation_id, sentences in parsed.citation_to_sentences.items():
            citation_map[str(citation_id)] = [
                {"sentence_index": parsed.sentences.index(s), "sentence_text": s.text}
                for s in sentences
            ]

        return {
            "text": parsed.original_text,
            "citations": citations_data,
            "sentences": sentences_data,
            "citation_map": citation_map,
        }
