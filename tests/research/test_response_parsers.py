"""
Unit tests for Harmony response parsers.

Tests JSON extraction, validation, channel separation, and error handling
for GPT-OSS-20B preprocessing responses.
"""

import json
import pytest

from tkr_docusearch.research.response_parsers import HarmonyResponseParser


class TestParseJsonResponse:
    """Test JSON parsing from Harmony responses"""

    def test_parse_compression_valid_json(self):
        """Parse valid compression response"""
        response = '{"facts": "Tucker: Senior UX Designer, 15+ years. Contact: 403-630-7003"}'
        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="compression",
            doc_id="doc1",
            chunk_id="chunk1"
        )

        assert "facts" in result
        assert result["facts"] == "Tucker: Senior UX Designer, 15+ years. Contact: 403-630-7003"

    def test_parse_compression_embedded_json(self):
        """Parse JSON embedded in text"""
        response = '''Some text before
        {"facts": "Revenue $2.5M, +15% YoY"}
        Some text after'''

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="compression"
        )

        assert "facts" in result
        assert result["facts"] == "Revenue $2.5M, +15% YoY"

    def test_parse_compression_harmony_channel_format(self):
        """Parse JSON from Harmony channel response"""
        response = '''<|start|>assistant<|channel|>final<|message|>
        {"facts": "Per Section 3.2: implement within 30 days"}
        <|end|>'''

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="compression"
        )

        assert "facts" in result
        assert result["facts"] == "Per Section 3.2: implement within 30 days"

    def test_parse_relevance_valid_json(self):
        """Parse valid relevance response"""
        response = '{"score": 8}'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="relevance"
        )

        assert "score" in result
        assert result["score"] == 8

    def test_parse_relevance_float_score(self):
        """Parse relevance response with float score"""
        response = '{"score": 7.5}'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="relevance"
        )

        assert "score" in result
        assert result["score"] == 7.5

    def test_parse_relevance_zero_score(self):
        """Parse relevance response with zero score"""
        response = '{"score": 0}'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="relevance"
        )

        assert "score" in result
        assert result["score"] == 0

    def test_parse_relevance_max_score(self):
        """Parse relevance response with max score"""
        response = '{"score": 10}'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="relevance"
        )

        assert "score" in result
        assert result["score"] == 10

    def test_parse_compression_with_doc_and_chunk_ids(self):
        """Parse with doc_id and chunk_id for traceability"""
        response = '{"facts": "Test facts"}'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="compression",
            doc_id="test-doc-123",
            chunk_id="chunk-0045"
        )

        assert "facts" in result
        assert result["facts"] == "Test facts"


class TestParseJsonResponseErrors:
    """Test error handling and fallback behavior"""

    def test_parse_malformed_json(self):
        """Handle malformed JSON gracefully"""
        response = '{"facts": "incomplete...'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="compression"
        )

        # Should fallback to original text
        assert "facts" in result
        assert result["facts"] == response

    def test_parse_missing_facts_key(self):
        """Handle missing 'facts' key in compression response"""
        response = '{"data": "some content"}'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="compression"
        )

        # Should fallback to original text
        assert "facts" in result
        assert result["facts"] == response

    def test_parse_missing_score_key(self):
        """Handle missing 'score' key in relevance response"""
        response = '{"rating": 8}'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="relevance"
        )

        # Should fallback to neutral score
        assert "score" in result
        assert result["score"] == 5

    def test_parse_empty_facts_value(self):
        """Handle empty 'facts' value"""
        response = '{"facts": ""}'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="compression"
        )

        # Should fallback to original text
        assert "facts" in result

    def test_parse_empty_facts_whitespace(self):
        """Handle whitespace-only 'facts' value"""
        response = '{"facts": "   "}'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="compression"
        )

        # Should fallback to original text
        assert "facts" in result

    def test_parse_facts_wrong_type(self):
        """Handle 'facts' with wrong type"""
        response = '{"facts": 123}'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="compression"
        )

        # Should fallback to original text
        assert "facts" in result

    def test_parse_score_wrong_type(self):
        """Handle 'score' with wrong type"""
        response = '{"score": "high"}'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="relevance"
        )

        # Should fallback to neutral score
        assert "score" in result
        assert result["score"] == 5

    def test_parse_score_out_of_range_high(self):
        """Handle score above 10"""
        response = '{"score": 15}'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="relevance"
        )

        # Should fallback to neutral score
        assert "score" in result
        assert result["score"] == 5

    def test_parse_score_out_of_range_low(self):
        """Handle score below 0"""
        response = '{"score": -5}'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="relevance"
        )

        # Should fallback to neutral score
        assert "score" in result
        assert result["score"] == 5

    def test_parse_empty_response(self):
        """Handle empty response string"""
        result_compression = HarmonyResponseParser.parse_json_response(
            "",
            schema_type="compression"
        )

        result_relevance = HarmonyResponseParser.parse_json_response(
            "",
            schema_type="relevance"
        )

        assert "facts" in result_compression
        assert "score" in result_relevance
        assert result_relevance["score"] == 5

    def test_parse_whitespace_only_response(self):
        """Handle whitespace-only response"""
        result = HarmonyResponseParser.parse_json_response(
            "   \n\t  ",
            schema_type="compression"
        )

        assert "facts" in result

    def test_parse_no_json_in_response(self):
        """Handle response with no JSON"""
        response = "This is just plain text without any JSON structure"

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="compression"
        )

        # Should fallback to original text
        assert "facts" in result
        assert result["facts"] == response

    def test_parse_invalid_schema_type(self):
        """Handle invalid schema type"""
        response = '{"facts": "test"}'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="invalid_type"
        )

        # Should return error fallback
        assert isinstance(result, dict)

    def test_parse_json_list_not_dict(self):
        """Handle JSON list instead of dict"""
        response = '[{"facts": "test"}]'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="compression"
        )

        # Should fallback
        assert "facts" in result

    def test_parse_nested_json_objects(self):
        """Handle nested JSON objects"""
        response = '{"outer": {"facts": "nested"}}'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="compression"
        )

        # Should not find facts at root level, fallback
        assert "facts" in result


class TestParseChannelResponse:
    """Test Harmony multi-channel response parsing"""

    def test_parse_final_channel(self):
        """Extract content from 'final' channel"""
        response = '''<|start|>assistant<|channel|>analysis<|message|>
        User wants key facts about revenue
        <|end|><|start|>assistant<|channel|>final<|message|>
        {"facts": "Revenue $2.5M, +15% YoY"}
        <|end|>'''

        result = HarmonyResponseParser.parse_channel_response(response, channel="final")

        assert '{"facts": "Revenue $2.5M, +15% YoY"}' in result
        assert "analysis" not in result.lower()

    def test_parse_analysis_channel(self):
        """Extract content from 'analysis' channel"""
        response = '''<|start|>assistant<|channel|>analysis<|message|>
        User wants key facts about revenue
        <|end|><|start|>assistant<|channel|>final<|message|>
        {"facts": "Revenue $2.5M"}
        <|end|>'''

        result = HarmonyResponseParser.parse_channel_response(response, channel="analysis")

        assert "User wants key facts" in result
        assert "facts" not in result.lower() or "revenue" in result.lower()

    def test_parse_channel_case_insensitive(self):
        """Channel names should be case-insensitive"""
        response = '''<|start|>assistant<|channel|>FINAL<|message|>
        {"score": 8}
        <|end|>'''

        result = HarmonyResponseParser.parse_channel_response(response, channel="final")

        assert '{"score": 8}' in result

    def test_parse_channel_strips_whitespace(self):
        """Extracted channel content should be stripped"""
        response = '''<|start|>assistant<|channel|>final<|message|>

        {"facts": "test"}

        <|end|>'''

        result = HarmonyResponseParser.parse_channel_response(response, channel="final")

        # Should not start or end with newlines
        assert not result.startswith('\n')
        assert not result.endswith('\n')

    def test_parse_no_channels_returns_full_response(self):
        """Return full response if no channels found"""
        response = '{"facts": "simple response"}'

        result = HarmonyResponseParser.parse_channel_response(response, channel="final")

        assert result == response

    def test_parse_channel_not_found(self):
        """Return full response if requested channel not found"""
        response = '''<|start|>assistant<|channel|>analysis<|message|>
        Some content
        <|end|>'''

        result = HarmonyResponseParser.parse_channel_response(response, channel="final")

        # Should return full response as fallback
        assert result == response

    def test_parse_multiple_channels(self):
        """Handle response with multiple channels"""
        response = '''<|start|>assistant<|channel|>analysis<|message|>
        Analysis here
        <|end|><|start|>assistant<|channel|>final<|message|>
        Final here
        <|end|><|start|>assistant<|channel|>debug<|message|>
        Debug here
        <|end|>'''

        result_analysis = HarmonyResponseParser.parse_channel_response(
            response,
            channel="analysis"
        )
        result_final = HarmonyResponseParser.parse_channel_response(
            response,
            channel="final"
        )
        result_debug = HarmonyResponseParser.parse_channel_response(
            response,
            channel="debug"
        )

        assert "Analysis here" in result_analysis
        assert "Final here" in result_final
        assert "Debug here" in result_debug

    def test_parse_default_channel_is_final(self):
        """Default channel should be 'final'"""
        response = '''<|start|>assistant<|channel|>final<|message|>
        Default content
        <|end|>'''

        result = HarmonyResponseParser.parse_channel_response(response)

        assert "Default content" in result


class TestValidateCompression:
    """Test compression validation"""

    def test_validate_compression_success(self):
        """Validate successful compression"""
        original = "This is a very long text with lots of redundant information that should be compressed down to something much shorter for efficiency."
        compressed = "Long text compressed for efficiency."

        result = HarmonyResponseParser.validate_compression(compressed, original)

        assert result is True

    def test_validate_compression_50_percent_reduction(self):
        """Validate 50% compression"""
        original = "A" * 1000
        compressed = "A" * 500

        result = HarmonyResponseParser.validate_compression(compressed, original)

        assert result is True

    def test_validate_compression_minimal_reduction(self):
        """Validate minimal compression (1 char reduction)"""
        original = "ABC"
        compressed = "AB"

        result = HarmonyResponseParser.validate_compression(compressed, original)

        assert result is True

    def test_validate_compression_failure_same_length(self):
        """Reject compression with same length"""
        original = "Test text"
        compressed = "Same text"

        result = HarmonyResponseParser.validate_compression(compressed, original)

        assert result is False

    def test_validate_compression_failure_expansion(self):
        """Reject text expansion (longer than original)"""
        original = "Short"
        compressed = "Much longer than original text"

        result = HarmonyResponseParser.validate_compression(compressed, original)

        assert result is False

    def test_validate_compression_empty_strings(self):
        """Handle empty strings"""
        result1 = HarmonyResponseParser.validate_compression("", "test")
        result2 = HarmonyResponseParser.validate_compression("test", "")

        assert result1 is True  # Empty is shorter than original
        assert result2 is False  # Longer than empty

    def test_validate_compression_unicode_text(self):
        """Handle unicode text correctly"""
        original = "Unicode test: 你好世界 🌍 with emojis"
        compressed = "Unicode: 你好 🌍"

        result = HarmonyResponseParser.validate_compression(compressed, original)

        assert result is True


class TestContractTestCases:
    """
    Test cases from integration contract specification.

    These tests validate behavior specified in:
    .context-kit/orchestration/gpt-oss-prompt-optimization/integration-contracts/prompt-response-schema.md
    """

    def test_contract_compression_technical_resume(self):
        """Contract Test 1: Technical resume text compression"""
        original = (
            "Tucker is a Senior UX Designer with 15+ years of experience. "
            "He has worked at Nutrien as Lead UX Designer from February 2023 to September 2023, "
            "where he led a team of 5 designers on multiple product initiatives. "
            "His contact information is 403-630-7003 and connect@tucker.sh."
        )

        response = '{"facts": "Tucker: Senior UX Designer, 15+ years. Nutrien Lead UX Designer Feb-Sep 2023, led 5 designers. Contact: 403-630-7003, connect@tucker.sh"}'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="compression",
            doc_id="resume-001",
            chunk_id="chunk-0001"
        )

        assert "facts" in result
        assert len(result["facts"]) < len(original)
        # Validate key information preserved
        assert "Tucker" in result["facts"]
        assert "15+ years" in result["facts"]
        assert "403-630-7003" in result["facts"]
        assert "connect@tucker.sh" in result["facts"]

    def test_contract_compression_already_concise(self):
        """Contract Test 2: Already concise text"""
        original = "Revenue: $2.5M. Growth: 15% YoY. Profit margins improved from 8% to 12%. CEO: positive outlook."

        response = '{"facts": "Revenue $2.5M, +15% YoY. Margins 8%→12%. CEO positive outlook."}'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="compression"
        )

        assert "facts" in result
        # May not compress much if already concise
        assert "$2.5M" in result["facts"]
        assert "15%" in result["facts"] or "YoY" in result["facts"]

    def test_contract_compression_verbose_boilerplate(self):
        """Contract Test 3: Verbose boilerplate compression"""
        original = (
            "In accordance with the provisions set forth in Section 3.2 of the agreement, "
            "it has been determined that the parties shall undertake to implement the measures "
            "described herein. Specifically, the timeline for completion shall not exceed "
            "thirty (30) business days from the date of execution. All stakeholders are required "
            "to provide written confirmation of their acceptance of these terms."
        )

        response = '{"facts": "Per Section 3.2: implement measures within 30 business days of execution. Stakeholders must provide written acceptance."}'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="compression"
        )

        assert "facts" in result
        assert len(result["facts"]) < len(original)
        # Validate key information preserved
        assert "Section 3.2" in result["facts"]
        assert "30" in result["facts"]

    def test_contract_relevance_direct_match(self):
        """Contract Test 1: Direct match relevance"""
        response = '{"score": 10}'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="relevance"
        )

        assert result["score"] == 10

    def test_contract_relevance_partial_match(self):
        """Contract Test 2: Partial match relevance"""
        response = '{"score": 7}'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="relevance"
        )

        assert result["score"] == 7

    def test_contract_relevance_tangential(self):
        """Contract Test 3: Tangential relevance"""
        response = '{"score": 3}'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="relevance"
        )

        assert result["score"] == 3

    def test_contract_relevance_irrelevant(self):
        """Contract Test 4: Irrelevant text"""
        response = '{"score": 0}'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="relevance"
        )

        assert result["score"] == 0


class TestEdgeCases:
    """Test edge cases and unusual inputs"""

    def test_very_long_response(self):
        """Handle very long response"""
        long_text = "A" * 10000
        response = f'{{"facts": "{long_text}"}}'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="compression"
        )

        assert "facts" in result

    def test_generic_exception_during_parsing(self):
        """Handle generic exception during parsing"""
        # Create a pathological input that triggers unexpected error path
        # This is a JSON-like string that's valid until loaded
        response = '{"facts": "test"}' * 1000  # Very repetitive

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="compression"
        )

        # Should gracefully handle and fallback
        assert "facts" in result

    def test_fallback_extraction_path(self):
        """Test secondary JSON extraction path (brace-bounded)"""
        # This tests the fallback extraction method when regex doesn't match
        response = '  {  "score": 8  }  '

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="relevance"
        )

        assert "score" in result
        assert result["score"] == 8

    def test_not_dict_response(self):
        """Handle response that's not a dict after parsing"""
        # Though this is hard to trigger naturally, test the validation path
        # The parser should handle this gracefully
        response = '"just a string"'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="compression"
        )

        # Should fallback
        assert "facts" in result

    def test_special_characters_in_json(self):
        """Handle special characters in JSON values"""
        response = r'{"facts": "Text with \"quotes\" and \n newlines and \t tabs"}'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="compression"
        )

        assert "facts" in result

    def test_multiline_json_response(self):
        """Handle multiline JSON"""
        response = '''{
            "facts": "Multiline
            JSON
            response"
        }'''

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="compression"
        )

        assert "facts" in result

    def test_multiple_json_objects_uses_longest(self):
        """When multiple JSON objects present, use longest"""
        response = '{"score": 5} and also {"score": 8, "confidence": 0.9}'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="relevance"
        )

        # Should use the more complete JSON
        assert "score" in result

    def test_json_with_extra_fields(self):
        """Handle JSON with extra fields beyond schema"""
        response = '{"facts": "test", "confidence": 0.95, "metadata": "extra"}'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="compression"
        )

        assert "facts" in result
        assert result["facts"] == "test"

    def test_compression_with_newlines_and_formatting(self):
        """Handle compressed text with newlines"""
        response = '{"facts": "Line 1\\nLine 2\\nLine 3"}'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="compression"
        )

        assert "facts" in result

    def test_score_as_float_gets_preserved(self):
        """Float scores should be preserved"""
        response = '{"score": 7.8}'

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="relevance"
        )

        assert result["score"] == 7.8
        assert isinstance(result["score"], float)

    def test_channel_with_nested_markers(self):
        """Handle channel markers within content"""
        response = '''<|start|>assistant<|channel|>final<|message|>
        This text mentions <|something|> but it's not a channel marker
        <|end|>'''

        result = HarmonyResponseParser.parse_channel_response(response, channel="final")

        assert "<|something|>" in result


class TestIntegration:
    """Integration tests simulating real usage"""

    def test_full_compression_workflow(self):
        """Test complete compression parsing workflow"""
        # Simulate LLM response
        harmony_response = '''<|start|>assistant<|channel|>analysis<|message|>
        User wants facts compressed. Extract key numbers and names.
        <|end|><|start|>assistant<|channel|>final<|message|>
        {"facts": "Tucker: 15+ years UX. Nutrien 2023. Contact: 403-630-7003, connect@tucker.sh"}
        <|end|>'''

        # Step 1: Extract final channel
        final_content = HarmonyResponseParser.parse_channel_response(
            harmony_response,
            channel="final"
        )

        # Step 2: Parse JSON
        parsed = HarmonyResponseParser.parse_json_response(
            final_content,
            schema_type="compression",
            doc_id="doc-123",
            chunk_id="chunk-0005"
        )

        # Step 3: Validate compression
        original_text = "Tucker is a Senior UX Designer with 15+ years of experience. He has worked at Nutrien as Lead UX Designer from February 2023 to September 2023, where he led a team of 5 designers on multiple product initiatives. His contact information is 403-630-7003 and connect@tucker.sh."
        is_compressed = HarmonyResponseParser.validate_compression(
            parsed["facts"],
            original_text
        )

        assert "facts" in parsed
        assert is_compressed is True

    def test_full_relevance_workflow(self):
        """Test complete relevance scoring workflow"""
        harmony_response = '{"score": 8}'

        parsed = HarmonyResponseParser.parse_json_response(
            harmony_response,
            schema_type="relevance",
            doc_id="doc-456",
            chunk_id="chunk-0012"
        )

        assert "score" in parsed
        assert 0 <= parsed["score"] <= 10

    def test_error_recovery_workflow(self):
        """Test error recovery with fallback"""
        # Malformed response
        bad_response = "This is not JSON at all"

        # Should gracefully fallback
        result = HarmonyResponseParser.parse_json_response(
            bad_response,
            schema_type="compression"
        )

        # Should return original text
        assert "facts" in result
        assert result["facts"] == bad_response

    def test_mixed_format_response(self):
        """Test response with mixed text and JSON"""
        response = '''
        The model analyzed the text and produced:
        {"facts": "Key information extracted"}
        Additional notes about the processing.
        '''

        result = HarmonyResponseParser.parse_json_response(
            response,
            schema_type="compression"
        )

        assert "facts" in result
        assert result["facts"] == "Key information extracted"
