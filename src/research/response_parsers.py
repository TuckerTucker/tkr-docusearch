"""
Response parsing utilities for Harmony-format LLM responses.

Handles JSON extraction, validation, and channel separation for GPT-OSS-20B
responses using the Harmony multi-channel format.

This module provides robust error handling and graceful fallbacks for
malformed LLM responses, ensuring preprocessing pipeline reliability.
"""

import json
import re
from typing import Any, Dict, Optional

import structlog

logger = structlog.get_logger(__name__)


class HarmonyResponseParser:
    """
    Parser for Harmony-format LLM responses with JSON schemas.

    Supports:
    - JSON extraction from Harmony responses
    - Schema validation (compression, relevance)
    - Multi-channel content separation
    - Graceful error handling with fallbacks
    """

    # Regex patterns for extraction
    JSON_PATTERN = re.compile(r'\{[^{}]*"[^"]+"\s*:\s*[^{}]*\}', re.DOTALL)
    CHANNEL_PATTERN = re.compile(
        r'<\|start\|>assistant<\|channel\|>(\w+)<\|message\|>(.*?)<\|end\|>',
        re.DOTALL
    )

    @staticmethod
    def parse_json_response(
        response: str,
        schema_type: str,
        doc_id: Optional[str] = None,
        chunk_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract and validate JSON from Harmony response.

        Implements graceful fallback strategy:
        1. Try to find JSON in response
        2. Validate against expected schema
        3. On failure, return appropriate fallback

        Args:
            response: Raw LLM response text
            schema_type: "compression" or "relevance"
            doc_id: Document ID for logging (optional)
            chunk_id: Chunk ID for logging (optional)

        Returns:
            Parsed JSON dict with schema-appropriate keys
            Fallback on errors:
            - compression: {"facts": original_text}
            - relevance: {"score": 5}

        Note:
            This method never raises exceptions. All errors are logged
            and handled via fallback values per contract spec.
        """
        context = {
            "schema_type": schema_type,
            "doc_id": doc_id or "unknown",
            "chunk_id": chunk_id or "unknown",
            "response_preview": response[:200] if response else "",
        }

        logger.debug("Parsing JSON response", **context)

        # Validate schema type
        if schema_type not in ["compression", "relevance"]:
            logger.error(
                "Invalid schema type",
                requested_schema_type=schema_type,
                valid_types=["compression", "relevance"],
                doc_id=doc_id or "unknown",
                chunk_id=chunk_id or "unknown",
            )
            return HarmonyResponseParser._get_fallback(schema_type, response)

        # Handle empty response
        if not response or not response.strip():
            logger.warning("Empty response received", **context)
            return HarmonyResponseParser._get_fallback(schema_type, response)

        # Extract JSON
        try:
            json_str = HarmonyResponseParser._extract_json(response)
            if not json_str:
                logger.warning(
                    "No JSON found in response",
                    response_length=len(response),
                    **context
                )
                return HarmonyResponseParser._get_fallback(schema_type, response)

            # Parse JSON
            parsed = json.loads(json_str)

            # Validate schema
            is_valid, error = HarmonyResponseParser._validate_schema(
                parsed, schema_type, response
            )

            if not is_valid:
                logger.warning(
                    "Schema validation failed",
                    error=error,
                    parsed_keys=list(parsed.keys()) if isinstance(parsed, dict) else None,
                    **context
                )
                return HarmonyResponseParser._get_fallback(schema_type, response)

            logger.debug(
                "JSON parsed successfully",
                parsed_keys=list(parsed.keys()),
                **context
            )

            return parsed

        except json.JSONDecodeError as e:
            logger.warning(
                "JSON decode error",
                error=str(e),
                error_pos=e.pos,
                **context
            )
            return HarmonyResponseParser._get_fallback(schema_type, response)

        except Exception as e:
            logger.error(
                "Unexpected error parsing JSON",
                error=str(e),
                error_type=type(e).__name__,
                **context
            )
            return HarmonyResponseParser._get_fallback(schema_type, response)

    @staticmethod
    def _extract_json(response: str) -> Optional[str]:
        """
        Extract JSON string from response text.

        Handles multiple formats:
        - Pure JSON response
        - JSON embedded in text
        - JSON within Harmony channel markers

        Args:
            response: Raw response text

        Returns:
            JSON string or None if not found
        """
        # Try to find JSON with regex
        matches = HarmonyResponseParser.JSON_PATTERN.findall(response)

        if matches:
            # Return the longest match (likely most complete)
            return max(matches, key=len)

        # Try to extract from brace-bounded text
        try:
            start = response.find('{')
            end = response.rfind('}')

            if start != -1 and end != -1 and end > start:
                json_candidate = response[start:end + 1]
                # Quick validation
                json.loads(json_candidate)
                return json_candidate
        except (json.JSONDecodeError, ValueError):
            pass

        return None

    @staticmethod
    def _validate_schema(
        parsed: Dict[str, Any],
        schema_type: str,
        original_text: str
    ) -> tuple[bool, Optional[str]]:
        """
        Validate parsed JSON against expected schema.

        Args:
            parsed: Parsed JSON object
            schema_type: Expected schema type
            original_text: Original response text (for compression validation)

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(parsed, dict):
            return False, f"Expected dict, got {type(parsed).__name__}"

        if schema_type == "compression":
            # Must have "facts" key
            if "facts" not in parsed:
                return False, "Missing required key 'facts'"

            # facts must be string
            if not isinstance(parsed["facts"], str):
                return False, f"'facts' must be string, got {type(parsed['facts']).__name__}"

            # facts must not be empty
            if not parsed["facts"].strip():
                return False, "'facts' value is empty"

            # Note: We don't validate compression ratio here as that's done separately
            # via validate_compression() method

        elif schema_type == "relevance":
            # Must have "score" key
            if "score" not in parsed:
                return False, "Missing required key 'score'"

            # score must be integer or float
            score = parsed["score"]
            if not isinstance(score, (int, float)):
                return False, f"'score' must be number, got {type(score).__name__}"

            # score must be in range 0-10
            if not (0 <= score <= 10):
                return False, f"'score' must be in range 0-10, got {score}"

        return True, None

    @staticmethod
    def _get_fallback(schema_type: str, original_text: str) -> Dict[str, Any]:
        """
        Get fallback value for failed parsing.

        Per contract specification:
        - compression: Return original text
        - relevance: Return neutral score (5)

        Args:
            schema_type: Schema type for fallback
            original_text: Original response text

        Returns:
            Fallback dict with appropriate schema
        """
        if schema_type == "compression":
            return {"facts": original_text}
        elif schema_type == "relevance":
            return {"score": 5}
        else:
            # Should never happen, but handle gracefully
            logger.error("Unknown schema type in fallback", schema_type=schema_type)
            return {"error": "unknown_schema"}

    @staticmethod
    def parse_channel_response(response: str, channel: str = "final") -> str:
        """
        Extract specific channel content from Harmony response.

        Harmony multi-channel format example:
        ```
        <|start|>assistant<|channel|>analysis<|message|>
        Reasoning here...
        <|end|><|start|>assistant<|channel|>final<|message|>
        {"facts": "..."}
        <|end|>
        ```

        Args:
            response: Raw Harmony response with channels
            channel: Channel name ("analysis" or "final")

        Returns:
            Content from specified channel, or full response if channel not found
        """
        logger.debug(
            "Extracting channel content",
            channel=channel,
            response_length=len(response)
        )

        # Find all channels
        matches = HarmonyResponseParser.CHANNEL_PATTERN.findall(response)

        if not matches:
            logger.debug(
                "No channels found in response, returning full text",
                response_preview=response[:200]
            )
            return response

        # Find requested channel
        for channel_name, content in matches:
            if channel_name.lower() == channel.lower():
                logger.debug(
                    "Channel found",
                    channel=channel,
                    content_length=len(content)
                )
                return content.strip()

        # Channel not found, return full response
        logger.warning(
            "Requested channel not found",
            requested_channel=channel,
            available_channels=[name for name, _ in matches]
        )
        return response

    @staticmethod
    def validate_compression(compressed: str, original: str) -> bool:
        """
        Validate that compression actually reduced size.

        Per contract: Compressed text must be shorter than original.
        This is a simple length check but ensures the LLM actually
        compressed rather than expanded the text.

        Args:
            compressed: Compressed text
            original: Original text

        Returns:
            True if compressed < original, False otherwise
        """
        compressed_len = len(compressed)
        original_len = len(original)

        is_valid = compressed_len < original_len

        if is_valid:
            reduction_pct = ((original_len - compressed_len) / original_len) * 100
            logger.debug(
                "Compression validation passed",
                original_length=original_len,
                compressed_length=compressed_len,
                reduction_percent=f"{reduction_pct:.1f}%"
            )
        else:
            logger.warning(
                "Compression validation failed",
                original_length=original_len,
                compressed_length=compressed_len,
                expansion=compressed_len - original_len
            )

        return is_valid
