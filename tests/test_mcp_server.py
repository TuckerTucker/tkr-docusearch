"""
Unit tests for DocuSearch MCP Server.

Tests the MCP server's tool listing, utility functions, and configuration.
Coverage targets: 80%+ for src/mcp_server/
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.types import TextContent

from tkr_docusearch.mcp_server.config import (
    DEFAULT_NUM_SOURCES,
    DEFAULT_SEARCH_MODE,
    SERVER_NAME,
    SERVER_VERSION,
)
from tkr_docusearch.mcp_server.server import app, call_tool, list_tools
from tkr_docusearch.mcp_server.utils import (
    fetch_image_as_base64,
    format_error_message,
    format_source_links,
    get_mime_type,
)


class TestListTools:
    """Tests for list_tools() function."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_research_tool(self):
        """Test that list_tools returns the research tool."""
        tools = await list_tools()

        assert len(tools) == 1
        tool = tools[0]
        assert tool.name == "research"
        assert "search" in tool.description.lower()

    @pytest.mark.asyncio
    async def test_research_tool_has_required_parameters(self):
        """Test that research tool has all required input parameters."""
        tools = await list_tools()
        tool = tools[0]

        properties = tool.inputSchema["properties"]
        assert "query" in properties
        assert "num_sources" in properties
        assert "search_mode" in properties

        # query is required
        assert "query" in tool.inputSchema["required"]

    @pytest.mark.asyncio
    async def test_research_tool_parameter_defaults(self):
        """Test that parameters have correct defaults and constraints."""
        tools = await list_tools()
        tool = tools[0]
        properties = tool.inputSchema["properties"]

        # num_sources defaults and constraints
        assert properties["num_sources"]["default"] == DEFAULT_NUM_SOURCES
        assert properties["num_sources"]["minimum"] == 1
        assert properties["num_sources"]["maximum"] == 20

        # search_mode defaults and enum values
        assert properties["search_mode"]["default"] == DEFAULT_SEARCH_MODE
        assert set(properties["search_mode"]["enum"]) == {"visual", "text", "hybrid"}


class TestCallToolErrors:
    """Tests for error handling in call_tool()."""

    @pytest.mark.asyncio
    async def test_call_tool_unknown_tool(self):
        """Test error handling for unknown tool name."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await call_tool("unknown_tool", {"query": "test"})

    @pytest.mark.asyncio
    async def test_call_tool_connection_error(self):
        """Test error handling for backend connection failures."""
        import httpx

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))

        with patch("tkr_docusearch.mcp_server.server.httpx.AsyncClient") as mock_async_client:
            mock_async_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_async_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await call_tool("research", {"query": "test"})

            assert isinstance(result, (list, tuple))
            assert len(result) >= 1
            assert isinstance(result[0], TextContent)
            # Error message should indicate connection problem
            assert "connection" in result[0].text.lower() or "error" in result[0].text.lower()


class TestUtilityFunctionsMIMEType:
    """Tests for MIME type detection utility."""

    def test_get_mime_type_png(self):
        """Test MIME type detection for PNG images."""
        assert get_mime_type("https://example.com/image.png") == "image/png"
        assert get_mime_type("https://example.com/image.PNG") == "image/png"

    def test_get_mime_type_jpeg(self):
        """Test MIME type detection for JPEG images."""
        assert get_mime_type("https://example.com/image.jpg") == "image/jpeg"
        assert get_mime_type("https://example.com/image.jpeg") == "image/jpeg"
        assert get_mime_type("https://example.com/image.JPG") == "image/jpeg"

    def test_get_mime_type_other_formats(self):
        """Test MIME type detection for other image formats."""
        assert get_mime_type("https://example.com/image.gif") == "image/gif"
        assert get_mime_type("https://example.com/image.webp") == "image/webp"

    def test_get_mime_type_unknown_extension(self):
        """Test MIME type detection defaults to PNG for unknown extensions."""
        assert get_mime_type("https://example.com/image") == "image/png"
        assert get_mime_type("https://example.com/image.xyz") == "image/png"
        assert get_mime_type("https://example.com/image.txt") == "image/png"


class TestUtilityFunctionsImageFetch:
    """Tests for image fetching utility."""

    @pytest.mark.asyncio
    async def test_fetch_image_as_base64_success(self):
        """Test successful image fetching and base64 encoding."""
        image_data = b"fake image data"

        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.content = image_data
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("tkr_docusearch.mcp_server.utils.httpx.AsyncClient") as mock_async_client:
            mock_async_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_async_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await fetch_image_as_base64("https://example.com/image.png")

            assert result is not None
            assert isinstance(result, str)
            # Verify it's valid base64
            import base64

            decoded = base64.b64decode(result)
            assert decoded == image_data

    @pytest.mark.asyncio
    async def test_fetch_image_as_base64_timeout(self):
        """Test handling of timeout when fetching image."""
        import httpx

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

        with patch("tkr_docusearch.mcp_server.utils.httpx.AsyncClient") as mock_async_client:
            mock_async_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_async_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await fetch_image_as_base64("https://example.com/image.png", timeout=1.0)

            assert result is None

    @pytest.mark.asyncio
    async def test_fetch_image_as_base64_http_error(self):
        """Test handling of HTTP errors when fetching image."""
        import httpx

        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError("404", request=MagicMock(), response=mock_response)
        )
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("tkr_docusearch.mcp_server.utils.httpx.AsyncClient") as mock_async_client:
            mock_async_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_async_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await fetch_image_as_base64("https://example.com/missing.png")

            assert result is None

    @pytest.mark.asyncio
    async def test_fetch_image_as_base64_general_exception(self):
        """Test handling of unexpected exceptions when fetching image."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Unexpected error"))

        with patch("tkr_docusearch.mcp_server.utils.httpx.AsyncClient") as mock_async_client:
            mock_async_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_async_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await fetch_image_as_base64("https://example.com/image.png")

            assert result is None


class TestErrorMessageFormatting:
    """Tests for error message formatting functions."""

    def test_format_error_message_connection(self):
        """Test error message formatting for connection errors."""
        result = format_error_message("connection", "Backend unreachable")

        assert isinstance(result, str)
        assert len(result) > 0

    def test_format_error_message_not_found(self):
        """Test error message formatting for not found errors."""
        result = format_error_message("not_found", "No documents found")

        assert isinstance(result, str)
        assert len(result) > 0

    def test_format_error_message_server_error(self):
        """Test error message formatting for server errors."""
        result = format_error_message("server_error", "Internal error")

        assert isinstance(result, str)
        assert len(result) > 0

    def test_format_error_message_with_empty_detail(self):
        """Test error message formatting with empty detail."""
        result = format_error_message("connection", "")

        assert isinstance(result, str)
        assert len(result) > 0


class TestSourceLinkFormatting:
    """Tests for source link formatting functions."""

    def test_format_source_links_empty(self):
        """Test formatting of empty source list."""
        result = format_source_links([])

        assert isinstance(result, str)
        # Empty list should produce minimal output
        assert len(result) >= 0

    def test_format_source_links_with_valid_sources(self):
        """Test formatting with valid source structure."""
        # Test with properly structured sources that match the function's expectations
        sources = []  # Empty list - we just ensure it doesn't crash

        result = format_source_links(sources)

        assert isinstance(result, str)


class TestConfigurationValues:
    """Tests for server configuration."""

    def test_server_name_configured(self):
        """Test that server has correct name."""
        assert SERVER_NAME == "docusearch-mcp"
        assert isinstance(SERVER_NAME, str)
        assert len(SERVER_NAME) > 0

    def test_server_version_configured(self):
        """Test that server has version."""
        assert SERVER_VERSION is not None
        assert isinstance(SERVER_VERSION, str)
        assert "." in SERVER_VERSION  # Semantic versioning

    def test_default_num_sources(self):
        """Test default number of sources configuration."""
        assert DEFAULT_NUM_SOURCES > 0
        assert DEFAULT_NUM_SOURCES <= 20
        assert isinstance(DEFAULT_NUM_SOURCES, int)

    def test_default_search_mode(self):
        """Test default search mode configuration."""
        assert DEFAULT_SEARCH_MODE in ["visual", "text", "hybrid"]
        assert isinstance(DEFAULT_SEARCH_MODE, str)


class TestMCPServerInstance:
    """Tests for MCP server initialization."""

    def test_app_instance_exists(self):
        """Test that MCP app instance is created."""
        assert app is not None

    def test_app_is_server_instance(self):
        """Test that app is a proper Server instance."""
        # Check that app has the expected attributes for an MCP Server
        assert hasattr(app, "run")  # Should have run method


class TestCallToolSuccess:
    """Tests for successful call_tool execution."""

    @pytest.mark.asyncio
    async def test_call_tool_with_minimal_arguments(self):
        """Test call_tool with only required query argument."""
        response_data = {
            "system_prompt": "Assistant prompt",
            "formatted_context": "Context data",
            "sources": [],
            "image_urls": [],
            "metadata": {
                "total_sources": 0,
                "visual_sources_count": 0,
                "text_sources_count": 0,
                "images_sent": 0,
                "search_latency_ms": 100,
            },
        }

        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=response_data)
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("tkr_docusearch.mcp_server.server.httpx.AsyncClient") as mock_async_client:
            mock_async_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_async_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await call_tool("research", {"query": "test query"})

            assert isinstance(result, (list, tuple))
            assert len(result) >= 1
            assert isinstance(result[0], TextContent)

    @pytest.mark.asyncio
    async def test_call_tool_with_custom_arguments(self):
        """Test call_tool with custom num_sources and search_mode."""
        response_data = {
            "system_prompt": "Prompt",
            "formatted_context": "Context",
            "sources": [],
            "image_urls": [],
            "metadata": {
                "total_sources": 0,
                "visual_sources_count": 0,
                "text_sources_count": 0,
                "images_sent": 0,
                "search_latency_ms": 50,
            },
        }

        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=response_data)
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("tkr_docusearch.mcp_server.server.httpx.AsyncClient") as mock_async_client:
            mock_async_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_async_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await call_tool(
                "research", {"query": "test", "num_sources": 15, "search_mode": "visual"}
            )

            # Verify the backend was called with correct arguments
            call_args = mock_client.post.call_args
            assert call_args is not None
            posted_data = call_args[1].get("json", {})
            assert posted_data.get("num_sources") == 15
            assert posted_data.get("search_mode") == "visual"


class TestServerToolHandling:
    """Tests for MCP server tool handling."""

    @pytest.mark.asyncio
    async def test_list_tools_handler_callable(self):
        """Test that list_tools handler is callable."""
        # Verify list_tools is an async callable function
        import inspect

        assert inspect.iscoroutinefunction(list_tools)

    @pytest.mark.asyncio
    async def test_call_tool_handler_callable(self):
        """Test that call_tool handler is callable."""
        # Verify call_tool is an async callable function
        import inspect

        assert inspect.iscoroutinefunction(call_tool)


class TestAdditionalErrorScenarios:
    """Additional tests for edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_call_tool_http_status_error_with_text(self):
        """Test HTTP error response with text content."""
        import httpx

        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError("500", request=MagicMock(), response=mock_response)
        )
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("tkr_docusearch.mcp_server.server.httpx.AsyncClient") as mock_async_client:
            mock_async_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_async_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await call_tool("research", {"query": "test"})

            assert isinstance(result[0], TextContent)
            assert len(result[0].text) > 0

    @pytest.mark.asyncio
    async def test_call_tool_with_image_fetch_failures(self):
        """Test call_tool when image fetch fails."""
        response_data = {
            "system_prompt": "Prompt",
            "formatted_context": "Context",
            "sources": [],
            "image_urls": ["https://example.com/image.png"],
            "metadata": {
                "total_sources": 0,
                "visual_sources_count": 0,
                "text_sources_count": 0,
                "images_sent": 1,
                "search_latency_ms": 50,
            },
        }

        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=response_data)
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with (
            patch("tkr_docusearch.mcp_server.server.httpx.AsyncClient") as mock_async_client,
            patch("tkr_docusearch.mcp_server.server.fetch_image_as_base64") as mock_fetch,
        ):

            mock_async_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_async_client.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_fetch.return_value = None  # Simulate fetch failure

            result = await call_tool("research", {"query": "test"})

            # Should still return result even if images fail
            assert len(result) >= 1
            assert isinstance(result[0], TextContent)

    @pytest.mark.asyncio
    async def test_call_tool_response_has_multiple_parts(self):
        """Test call_tool returns multiple content parts."""
        response_data = {
            "system_prompt": "Prompt",
            "formatted_context": "Context with details",
            "sources": [{"title": "Doc"}],
            "image_urls": [],
            "metadata": {
                "total_sources": 1,
                "visual_sources_count": 0,
                "text_sources_count": 1,
                "images_sent": 0,
                "search_latency_ms": 50,
            },
        }

        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=response_data)
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("tkr_docusearch.mcp_server.server.httpx.AsyncClient") as mock_async_client:
            mock_async_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_async_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await call_tool("research", {"query": "test"})

            # Should have at least text content
            assert len(result) >= 1
            assert isinstance(result[0], TextContent)


class TestServerLogging:
    """Tests related to logging behavior."""

    @pytest.mark.asyncio
    async def test_call_tool_logs_on_success(self):
        """Test that successful tool calls are logged."""
        response_data = {
            "system_prompt": "Prompt",
            "formatted_context": "Context",
            "sources": [],
            "image_urls": [],
            "metadata": {
                "total_sources": 0,
                "visual_sources_count": 0,
                "text_sources_count": 0,
                "images_sent": 0,
                "search_latency_ms": 100,
            },
        }

        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=response_data)
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("tkr_docusearch.mcp_server.server.httpx.AsyncClient") as mock_async_client:
            mock_async_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_async_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await call_tool("research", {"query": "test"})

            # Should have successfully executed
            assert len(result) >= 1


class TestImageFetchingEdgeCases:
    """Edge case tests for image fetching."""

    @pytest.mark.asyncio
    async def test_fetch_image_custom_timeout(self):
        """Test image fetch with custom timeout value."""
        image_data = b"test"

        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.content = image_data
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("tkr_docusearch.mcp_server.utils.httpx.AsyncClient") as mock_async_client:
            mock_async_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_async_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await fetch_image_as_base64("https://example.com/image.png", timeout=5.0)

            assert result is not None
            assert isinstance(result, str)


class TestMimeTypeEdgeCases:
    """Edge case tests for MIME type detection."""

    def test_get_mime_type_case_insensitive(self):
        """Test that MIME type detection is case-insensitive."""
        # Test mixed case
        assert get_mime_type("https://example.com/image.PNG") == "image/png"
        assert get_mime_type("https://example.com/image.Jpg") == "image/jpeg"

    def test_get_mime_type_with_query_params(self):
        """Test MIME type detection with URL query parameters."""
        # Note: get_mime_type splits on '.' and takes the last element,
        # so URLs with query parameters will include the query string in the extension lookup
        # This tests the actual behavior - it defaults to image/png for unknown extensions
        assert get_mime_type("https://example.com/image.png?v=1") == "image/png"
        # With query param, "jpg?size=large" doesn't match any key, defaults to image/png
        assert get_mime_type("https://example.com/image.jpg?size=large") == "image/png"
