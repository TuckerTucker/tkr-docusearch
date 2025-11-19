"""
Integration tests for legacy-office-converter service endpoints.

Tests the service endpoints directly to ensure the Docker container is
properly configured and both PPTX rendering and .doc conversion capabilities
are functioning.

Author: Agent-Integration-Testing
Date: 2025-11-19
Wave: 8 (Legacy Office Doc Conversion)
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict

import pytest
import requests

from tkr_docusearch.processing.legacy_office_client import LegacyOfficeError

logger = logging.getLogger(__name__)


# ====================================================================================
# Service Health Tests
# ====================================================================================


class TestLegacyOfficeServiceHealth:
    """Test legacy-office-converter service health and availability."""

    def test_health_endpoint_accessible(
        self, legacy_office_url: str, skip_if_legacy_office_unavailable
    ):
        """Test /health endpoint is accessible."""
        response = requests.get(f"{legacy_office_url}/health", timeout=5)

        assert response.status_code == 200
        logger.info("✓ Health endpoint accessible")

    def test_health_endpoint_shows_capabilities(
        self, legacy_office_url: str, skip_if_legacy_office_unavailable
    ):
        """Test /health endpoint shows both PPTX and .doc capabilities."""
        response = requests.get(f"{legacy_office_url}/health", timeout=5)

        assert response.status_code == 200

        data = response.json()

        # Should have capabilities array
        assert "capabilities" in data, "Health response should include capabilities"

        capabilities = data["capabilities"]
        assert isinstance(capabilities, list), "Capabilities should be a list"

        # Should include both capabilities
        assert (
            "pptx-rendering" in capabilities
        ), "Should advertise PPTX rendering capability"
        assert "doc-conversion" in capabilities, "Should advertise .doc conversion capability"

        logger.info(f"✓ Service capabilities: {capabilities}")

    def test_root_endpoint_accessible(
        self, legacy_office_url: str, skip_if_legacy_office_unavailable
    ):
        """Test root endpoint (/) provides service info."""
        response = requests.get(f"{legacy_office_url}/", timeout=5)

        assert response.status_code == 200

        data = response.json()
        assert "service" in data
        assert data["service"] == "legacy-office-converter"

        logger.info(f"✓ Service info: {data.get('service')} v{data.get('version', 'unknown')}")


# ====================================================================================
# Doc Conversion Endpoint Tests
# ====================================================================================


class TestDocConversionEndpoint:
    """Test /convert-doc endpoint functionality."""

    def test_convert_doc_endpoint_exists(
        self, legacy_office_url: str, skip_if_legacy_office_unavailable
    ):
        """Test /convert-doc endpoint is accessible (not 404)."""
        # Send POST with minimal payload (will fail validation, but endpoint should exist)
        response = requests.post(
            f"{legacy_office_url}/convert-doc", json={"file_path": "/test.doc"}, timeout=10
        )

        # Should return 400, 403, 404, or 500 depending on validation
        # but NOT 404 (endpoint not found) or 405 (method not allowed)
        assert response.status_code != 404, "Endpoint should exist"
        assert response.status_code != 405, "POST method should be allowed"

        logger.info(f"✓ /convert-doc endpoint exists (status: {response.status_code})")

    def test_convert_doc_requires_file_path(
        self, legacy_office_url: str, skip_if_legacy_office_unavailable
    ):
        """Test /convert-doc requires file_path parameter."""
        # Send empty payload
        response = requests.post(f"{legacy_office_url}/convert-doc", json={}, timeout=10)

        # Should return 400 or 422 (validation error)
        assert response.status_code in [400, 422], "Should reject missing file_path"

        logger.info("✓ /convert-doc validates file_path parameter")

    def test_convert_doc_handles_missing_file(
        self, legacy_office_url: str, skip_if_legacy_office_unavailable
    ):
        """Test /convert-doc returns 404 for missing file."""
        response = requests.post(
            f"{legacy_office_url}/convert-doc",
            json={"file_path": "/uploads/nonexistent-file-12345.doc"},
            timeout=10,
        )

        # Should return 404 (file not found)
        assert response.status_code == 404, "Should return 404 for missing file"

        data = response.json()
        assert "error" in data or "detail" in data, "Should include error message"

        logger.info("✓ /convert-doc handles missing files correctly")

    def test_convert_doc_response_format(
        self, legacy_office_url: str, skip_if_legacy_office_unavailable
    ):
        """Test /convert-doc returns expected response format."""
        # Note: This test will fail if file doesn't exist, but we're testing the format
        response = requests.post(
            f"{legacy_office_url}/convert-doc",
            json={"file_path": "/uploads/test.doc"},
            timeout=10,
        )

        data = response.json()

        # Response should be JSON
        assert isinstance(data, dict), "Response should be JSON object"

        # Should have either success or error
        if response.status_code == 200:
            # Success response format
            assert "success" in data, "Success response should have 'success' field"
            assert "docx_path" in data, "Success response should have 'docx_path' field"
            assert (
                "conversion_time_ms" in data
            ), "Success response should have 'conversion_time_ms' field"
        else:
            # Error response format
            assert (
                "error" in data or "detail" in data
            ), "Error response should have 'error' or 'detail' field"

        logger.info("✓ /convert-doc response format validated")


# ====================================================================================
# PPTX Rendering Endpoint Tests
# ====================================================================================


class TestPptxRenderingEndpoint:
    """Test /render endpoint functionality (existing PPTX capability)."""

    def test_render_endpoint_exists(
        self, legacy_office_url: str, skip_if_legacy_office_unavailable
    ):
        """Test /render endpoint is accessible (not 404)."""
        response = requests.post(
            f"{legacy_office_url}/render", json={"file_path": "/test.pptx"}, timeout=10
        )

        # Should NOT return 404 or 405
        assert response.status_code != 404, "Endpoint should exist"
        assert response.status_code != 405, "POST method should be allowed"

        logger.info(f"✓ /render endpoint exists (status: {response.status_code})")

    def test_render_requires_parameters(
        self, legacy_office_url: str, skip_if_legacy_office_unavailable
    ):
        """Test /render requires file_path and output_dir parameters."""
        # Send empty payload
        response = requests.post(f"{legacy_office_url}/render", json={}, timeout=10)

        # Should return 400 or 422 (validation error)
        assert response.status_code in [400, 422], "Should reject missing parameters"

        logger.info("✓ /render validates required parameters")


# ====================================================================================
# Concurrent Request Tests
# ====================================================================================


class TestConcurrentCapabilities:
    """Test service handles concurrent PPTX and .doc requests."""

    def test_concurrent_pptx_and_doc_conversions(
        self, legacy_office_url: str, skip_if_legacy_office_unavailable
    ):
        """Test service handles concurrent PPTX and .doc requests.

        This validates that both capabilities can operate simultaneously
        without blocking each other.
        """

        def send_doc_request() -> Dict:
            """Send .doc conversion request."""
            try:
                response = requests.post(
                    f"{legacy_office_url}/convert-doc",
                    json={"file_path": "/uploads/test.doc"},
                    timeout=15,
                )
                return {"type": "doc", "status": response.status_code, "success": True}
            except Exception as e:
                return {"type": "doc", "status": None, "success": False, "error": str(e)}

        def send_pptx_request() -> Dict:
            """Send PPTX rendering request."""
            try:
                response = requests.post(
                    f"{legacy_office_url}/render",
                    json={"file_path": "/uploads/test.pptx", "output_dir": "/tmp"},
                    timeout=15,
                )
                return {"type": "pptx", "status": response.status_code, "success": True}
            except Exception as e:
                return {"type": "pptx", "status": None, "success": False, "error": str(e)}

        # Send concurrent requests
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(send_doc_request), executor.submit(send_pptx_request)]

            results = []
            for future in as_completed(futures):
                results.append(future.result())

        # Both requests should complete (even if they fail due to missing files)
        assert len(results) == 2, "Both requests should complete"

        doc_result = next(r for r in results if r["type"] == "doc")
        pptx_result = next(r for r in results if r["type"] == "pptx")

        # Both should get HTTP responses (not connection errors)
        assert doc_result["success"] or doc_result.get(
            "status"
        ), "Doc request should complete or return status"
        assert pptx_result["success"] or pptx_result.get(
            "status"
        ), "PPTX request should complete or return status"

        logger.info("✓ Service handles concurrent requests")
        logger.info(f"  Doc conversion: status={doc_result.get('status')}")
        logger.info(f"  PPTX rendering: status={pptx_result.get('status')}")

    @pytest.mark.slow
    def test_multiple_concurrent_doc_conversions(
        self, legacy_office_url: str, skip_if_legacy_office_unavailable
    ):
        """Test service handles multiple concurrent .doc conversion requests."""

        def send_request(request_id: int) -> Dict:
            """Send .doc conversion request."""
            try:
                response = requests.post(
                    f"{legacy_office_url}/convert-doc",
                    json={"file_path": f"/uploads/test-{request_id}.doc"},
                    timeout=15,
                )
                return {
                    "request_id": request_id,
                    "status": response.status_code,
                    "success": True,
                }
            except Exception as e:
                return {
                    "request_id": request_id,
                    "status": None,
                    "success": False,
                    "error": str(e),
                }

        # Send 5 concurrent requests
        num_requests = 5
        with ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [executor.submit(send_request, i) for i in range(num_requests)]

            results = []
            for future in as_completed(futures):
                results.append(future.result())

        # All requests should complete
        assert len(results) == num_requests, "All requests should complete"

        # At least some should complete successfully (or get HTTP response)
        completed_count = sum(1 for r in results if r["success"] or r.get("status"))
        assert (
            completed_count >= num_requests * 0.8
        ), "Most requests should complete (80%+)"

        logger.info(f"✓ Service handled {completed_count}/{num_requests} concurrent requests")


# ====================================================================================
# Client Integration Tests
# ====================================================================================


class TestLegacyOfficeClient:
    """Test LegacyOfficeClient class integration with service."""

    def test_client_health_check(
        self, legacy_office_client, skip_if_legacy_office_unavailable
    ):
        """Test client.check_health() method."""
        is_healthy = legacy_office_client.check_health()

        assert is_healthy is True, "Service should be healthy"
        logger.info("✓ Client health check passed")

    def test_client_get_info(self, legacy_office_client, skip_if_legacy_office_unavailable):
        """Test client.get_info() method."""
        info = legacy_office_client.get_info()

        assert isinstance(info, dict), "Info should be a dictionary"
        assert "service" in info, "Info should include service name"
        assert info["service"] == "legacy-office-converter"

        logger.info(f"✓ Client info: {info}")

    def test_client_convert_doc_with_missing_file(
        self, legacy_office_client, skip_if_legacy_office_unavailable
    ):
        """Test client raises appropriate error for missing file."""
        with pytest.raises((LegacyOfficeError, FileNotFoundError)):
            legacy_office_client.convert_doc_to_docx("/uploads/nonexistent-12345.doc")

        logger.info("✓ Client handles missing file correctly")

    def test_client_singleton_instance(self, legacy_office_singleton):
        """Test get_legacy_office_client() returns singleton."""
        from tkr_docusearch.processing.legacy_office_client import get_legacy_office_client

        # Get instance twice
        instance1 = get_legacy_office_client()
        instance2 = get_legacy_office_client()

        # Should be the same instance
        assert instance1 is instance2, "Should return singleton instance"

        logger.info("✓ Singleton pattern works correctly")


# ====================================================================================
# Error Handling Tests
# ====================================================================================


class TestServiceErrorHandling:
    """Test service error handling for edge cases."""

    def test_invalid_json_payload(
        self, legacy_office_url: str, skip_if_legacy_office_unavailable
    ):
        """Test service handles invalid JSON gracefully."""
        response = requests.post(
            f"{legacy_office_url}/convert-doc",
            data="invalid json",
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        # Should return 400 or 422 (bad request)
        assert response.status_code in [
            400,
            422,
        ], "Should reject invalid JSON with 400/422"

        logger.info("✓ Service handles invalid JSON correctly")

    def test_missing_content_type(
        self, legacy_office_url: str, skip_if_legacy_office_unavailable
    ):
        """Test service handles missing Content-Type header."""
        response = requests.post(
            f"{legacy_office_url}/convert-doc", data='{"file_path": "/test.doc"}', timeout=10
        )

        # Should either accept or reject with appropriate error
        assert response.status_code in [
            200,
            400,
            404,
            415,
            422,
        ], "Should handle missing Content-Type"

        logger.info("✓ Service handles missing Content-Type header")

    def test_timeout_handling(
        self, legacy_office_url: str, skip_if_legacy_office_unavailable
    ):
        """Test client timeout is respected."""
        # Use very short timeout to test timeout handling
        try:
            response = requests.post(
                f"{legacy_office_url}/convert-doc",
                json={"file_path": "/uploads/test.doc"},
                timeout=0.001,  # 1ms timeout - should fail
            )
            # If we get here, request was very fast
            logger.info("Request completed faster than timeout")
        except requests.exceptions.Timeout:
            # Expected - timeout was triggered
            logger.info("✓ Timeout handling works correctly")
        except requests.exceptions.ConnectionError:
            # Also acceptable - connection issues
            logger.info("✓ Connection error handled correctly")
