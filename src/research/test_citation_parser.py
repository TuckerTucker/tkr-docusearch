"""
Unit tests for Citation Parser.
"""

import pytest

from src.research.citation_parser import Citation, CitationParser


class TestCitationParser:
    """Tests for CitationParser"""

    def setup_method(self):
        """Setup test fixtures"""
        self.parser = CitationParser()

    def test_extract_single_citation(self):
        """Test extracting a single citation"""
        text = "Paris is the capital [1]."
        citations = self.parser.extract_citations(text)

        assert len(citations) == 1
        assert citations[0].citation_id == 1
        assert citations[0].marker == "[1]"
        assert citations[0].start_pos == 21
        assert citations[0].end_pos == 24

    def test_extract_multiple_citations(self):
        """Test extracting multiple citations"""
        text = "Paris [1] is the capital of France [2]."
        citations = self.parser.extract_citations(text)

        assert len(citations) == 2
        assert citations[0].citation_id == 1
        assert citations[1].citation_id == 2

    def test_extract_citation_cluster(self):
        """Test extracting citation clusters"""
        text = "This is supported [1][2][3]."
        citations = self.parser.extract_citations(text)

        assert len(citations) == 3
        assert [c.citation_id for c in citations] == [1, 2, 3]

    def test_parse_full_answer(self):
        """Test parsing complete answer"""
        text = """
        Paris is the capital of France [1]. It is known for the Eiffel Tower [2].
        The city has a population of over 2 million [1][2].
        """
        parsed = self.parser.parse(text, num_sources=2)

        assert len(parsed.citations) == 4
        assert len(parsed.sentences) > 0
        assert parsed.validate(num_sources=2)

    def test_citation_validation_valid(self):
        """Test citation validation with valid citations"""
        citations = [Citation(1, 0, 3, "[1]"), Citation(2, 10, 13, "[2]")]

        is_valid, errors = self.parser.validate_citations(citations, num_sources=2)
        assert is_valid
        assert len(errors) == 0

    def test_citation_validation_out_of_range(self):
        """Test citation validation with out-of-range citations"""
        citations = [Citation(1, 0, 3, "[1]"), Citation(5, 10, 13, "[5]")]  # Exceeds num_sources

        is_valid, errors = self.parser.validate_citations(citations, num_sources=2)
        assert not is_valid
        assert len(errors) > 0

    def test_remove_citations(self):
        """Test removing citations from text"""
        text = "Paris [1] is nice [2]."
        clean = self.parser.remove_citations(text)

        assert "[1]" not in clean
        assert "[2]" not in clean
        assert "Paris" in clean
        assert "is nice" in clean

    def test_bidirectional_mapping(self):
        """Test creating bidirectional citation-sentence map"""
        text = "First sentence [1]. Second sentence [2]. Third sentence [1][2]."
        parsed = self.parser.parse(text, num_sources=2)

        # Citation 1 appears in sentence 0 and 2
        assert 1 in parsed.citation_to_sentences
        assert len(parsed.citation_to_sentences[1]) >= 1

        # Citation 2 appears in sentence 1 and 2
        assert 2 in parsed.citation_to_sentences
        assert len(parsed.citation_to_sentences[2]) >= 1

    def test_format_for_frontend(self):
        """Test formatting for frontend consumption"""
        text = "Paris is the capital [1]."
        parsed = self.parser.parse(text, num_sources=1)

        frontend_data = self.parser.format_for_frontend(parsed)

        assert "text" in frontend_data
        assert "citations" in frontend_data
        assert "citation_map" in frontend_data
        assert len(frontend_data["citations"]) == 1
        assert frontend_data["citations"][0]["id"] == 1

    def test_no_citations(self):
        """Test handling text with no citations"""
        text = "This text has no citations."
        parsed = self.parser.parse(text, num_sources=0)

        assert len(parsed.citations) == 0
        assert len(parsed.sentences) > 0

    def test_malformed_citations_ignored(self):
        """Test that malformed citations are ignored"""
        text = "Text with [abc] and [] and [1]."
        citations = self.parser.extract_citations(text)

        # Only [1] should be extracted
        assert len(citations) == 1
        assert citations[0].citation_id == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
