"""
DocuSearch MCP Server - Entry point

Allows running the MCP server as a module:
    python -m src.mcp_server
"""

import asyncio

from .server import main

if __name__ == "__main__":
    asyncio.run(main())
