"""
DocuSearch MCP Server

Main MCP server implementation exposing DocuSearch's multi-modal search
capabilities to Claude Desktop via the Model Context Protocol.
"""

import logging
import sys
from typing import Any, Sequence

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import ImageContent, TextContent, Tool

from .config import (
    CONTEXT_ENDPOINT,
    DEFAULT_NUM_SOURCES,
    DEFAULT_SEARCH_MODE,
    SERVER_DESCRIPTION,
    SERVER_NAME,
    SERVER_VERSION,
)
from .utils import fetch_image_as_base64, format_error_message, format_source_links, get_mime_type

# Configure logging to stderr (stdout is reserved for MCP protocol)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)

logger = logging.getLogger(__name__)

# Create MCP server instance
app = Server(SERVER_NAME)


@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    List available MCP tools.

    Returns single 'research' tool for DocuSearch multi-modal search.
    """
    return [
        Tool(
            name="research",
            description=(
                "Search your DocuSearch document collection and get AI-generated "
                "answers with citations. Searches both text (chunks) and visual "
                "(page images) using ColPali multi-modal embeddings. Returns cited "
                "answer with page images and links to source documents in your browser.\n\n"
                "Use this when you need to:\n"
                "- Answer questions about your documents\n"
                "- Find information across multiple sources\n"
                "- Analyze charts, diagrams, or visual content\n"
                "- Get cited answers with source links"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Research question to answer from your documents. "
                            "Can reference visual elements like charts, diagrams, tables. "
                            "Examples: 'What caused the 2008 crisis?', 'What does the revenue chart show?'"
                        ),
                    },
                    "num_sources": {
                        "type": "integer",
                        "description": "Number of source documents to retrieve (1-20)",
                        "default": DEFAULT_NUM_SOURCES,
                        "minimum": 1,
                        "maximum": 20,
                    },
                    "search_mode": {
                        "type": "string",
                        "enum": ["visual", "text", "hybrid"],
                        "description": (
                            "Search mode:\n"
                            "- 'visual': Search page images only (best for charts/diagrams)\n"
                            "- 'text': Search text chunks only (best for pure text)\n"
                            "- 'hybrid': Search both visual and text (recommended)"
                        ),
                        "default": DEFAULT_SEARCH_MODE,
                    },
                },
                "required": ["query"],
            },
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> Sequence[TextContent | ImageContent]:
    """
    Handle MCP tool calls.

    Args:
        name: Tool name (only 'research' is supported)
        arguments: Tool arguments (query, num_sources, search_mode)

    Returns:
        Sequence of TextContent and ImageContent for Claude Desktop

    Raises:
        ValueError: If tool name is unknown
    """
    if name != "research":
        raise ValueError(f"Unknown tool: {name}")

    logger.info(
        f"Research tool called: query='{arguments.get('query')}', "
        f"num_sources={arguments.get('num_sources', DEFAULT_NUM_SOURCES)}, "
        f"search_mode={arguments.get('search_mode', DEFAULT_SEARCH_MODE)}"
    )

    try:
        # Step 1: Call backend /api/research/context-only
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                CONTEXT_ENDPOINT,
                json={
                    "query": arguments["query"],
                    "num_sources": arguments.get("num_sources", DEFAULT_NUM_SOURCES),
                    "search_mode": arguments.get("search_mode", DEFAULT_SEARCH_MODE),
                },
            )
            response.raise_for_status()
            data = response.json()

        logger.info(
            f"Context retrieved from backend: {data['metadata']['total_sources']} sources "
            f"({data['metadata']['visual_sources_count']} visual, {data['metadata']['text_sources_count']} text), "
            f"{data['metadata']['images_sent']} images, {data['metadata']['search_latency_ms']}ms"
        )

        # Step 2: Build multi-part response
        content_parts: list[TextContent | ImageContent] = []

        # Part 1: System prompt + context + source links
        prompt_text = f"{data['system_prompt']}\n\n"
        prompt_text += f"CONTEXT:\n{data['formatted_context']}\n\n"

        # Add source links section (required for markdown link citations)
        links_text = format_source_links(data["sources"])
        prompt_text += f"{links_text}\n\n"

        prompt_text += f"QUERY: {arguments['query']}"

        content_parts.append(TextContent(type="text", text=prompt_text))

        # Part 3: Images (fetch and encode)
        image_count = 0
        for image_url in data.get("image_urls", []):
            image_data = await fetch_image_as_base64(image_url)

            if image_data:
                mime_type = get_mime_type(image_url)
                content_parts.append(
                    ImageContent(type="image", data=image_data, mimeType=mime_type)
                )
                image_count += 1
            else:
                logger.warning(f"Failed to fetch image: {image_url}")

        logger.info(f"Images fetched: {image_count}/{len(data.get('image_urls', []))} successful")

        logger.info(
            f"Research tool completed successfully: {len(content_parts)} content parts, "
            f"{image_count} images, {len(data['sources'])} sources"
        )

        return content_parts

    except httpx.ConnectError as e:
        logger.error(f"Failed to connect to DocuSearch API: {e}")
        error_msg = format_error_message("connection", str(e))
        return [TextContent(type="text", text=error_msg)]

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.warning(f"No sources found for query: {arguments.get('query')}")
            error_msg = format_error_message("not_found", e.response.text)
        else:
            logger.error(f"Backend HTTP error {e.response.status_code}: {e.response.text}")
            error_msg = format_error_message("server_error", e.response.text)

        return [TextContent(type="text", text=error_msg)]

    except Exception as e:
        logger.error(f"Unexpected error in research tool: {e}", exc_info=True)
        error_msg = format_error_message("server_error", str(e))
        return [TextContent(type="text", text=error_msg)]


async def main():
    """
    Main entry point for MCP server.

    Runs the server with stdio transport for Claude Desktop integration.
    """
    logger.info(
        f"Starting DocuSearch MCP Server: {SERVER_NAME} v{SERVER_VERSION} - {SERVER_DESCRIPTION}"
    )

    async with stdio_server() as (read_stream, write_stream):
        logger.info("MCP server running on stdio")
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
