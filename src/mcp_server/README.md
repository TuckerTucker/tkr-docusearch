# DocuSearch MCP Server

Model Context Protocol server for integrating DocuSearch with Claude Desktop.

## Overview

The DocuSearch MCP Server exposes DocuSearch's multi-modal document search capabilities to Claude Desktop via a single `research` tool. This enables Claude to search your local documents using ColPali embeddings (visual + text) and provide cited answers with source links.

## Features

- **Multi-modal Search**: Searches both page images (visual) and text chunks using ColPali embeddings
- **Vision Support**: Sends page images to Claude for analyzing charts, diagrams, and tables
- **Inline Citations**: Returns system prompt that guides Claude to use `[1][2]` citation format
- **Source Links**: Provides clickable links to document detail views in your browser
- **Hybrid Search**: Combines visual and text search by default for best results

## Prerequisites

1. **DocuSearch Running**: All services must be running
   ```bash
   ./scripts/start-all.sh
   ```

2. **Ngrok Tunnel**: Required for vision support (Claude Desktop needs HTTPS image URLs)
   ```bash
   ngrok http 8002
   # Copy the https://xxx.ngrok.io URL
   ```

3. **Environment Variables**: Set in `.env`
   ```bash
   NGROK_URL=https://your-ngrok-url.ngrok.io
   ```

4. **MCP Dependencies**: Install MCP SDK and httpx
   ```bash
   source .venv-native/bin/activate
   pip install mcp httpx
   ```

## Installation

### 1. Install Dependencies

```bash
source .venv-native/bin/activate
pip install -r src/mcp_server/requirements.txt
```

### 2. Configure Claude Desktop

Edit Claude Desktop configuration file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add the DocuSearch MCP server:

```json
{
  "mcpServers": {
    "docusearch": {
      "command": "python",
      "args": [
        "-m",
        "src.mcp_server"
      ],
      "cwd": "/Volumes/tkr-riffic/@tkr-projects/tkr-docusearch",
      "env": {
        "PYTHONPATH": "/Volumes/tkr-riffic/@tkr-projects/tkr-docusearch",
        "NGROK_URL": "https://your-ngrok-url.ngrok.io"
      }
    }
  }
}
```

**Important**: Replace `/Volumes/tkr-riffic/@tkr-projects/tkr-docusearch` with your actual project path.

### 3. Restart Claude Desktop

Close and reopen Claude Desktop to load the MCP server.

## Usage

### In Claude Desktop

Once configured, Claude Desktop will have access to the `research` tool. You can ask questions like:

**Text Queries**:
```
What caused the 2008 financial crisis?
```

**Visual Queries**:
```
What trends does the revenue chart show?
```

**Hybrid Queries**:
```
Explain the architecture diagram and its components
```

### Tool Parameters

The `research` tool accepts:

- **query** (required): Research question to answer
- **num_sources** (optional): Number of sources to retrieve (1-20, default: 10)
- **search_mode** (optional): `"visual"`, `"text"`, or `"hybrid"` (default: `"hybrid"`)

### Response Format

Claude receives:

1. **System Prompt**: Instructions for citation format and visual analysis
2. **Formatted Context**: Numbered sources `[1]`, `[2]`, etc.
3. **Images**: Page images for visual sources (via ngrok)
4. **Source Links**: Clickable links to `http://localhost:3000/details/:id`

### Example Interaction

```
User: What does the sales chart show?

Claude receives:
- System prompt with citation instructions
- Context: "[1] [Visual Match] Q3-Report.pdf, Page 8\nSales increased 25%..."
- Image: [Bar chart from page 8]
- Links: [1] http://localhost:3000/details/abc123

Claude responds:
"The sales chart in [1] shows a 25% increase in Q3. The bar chart visualizes
regional breakdown: North America (+30%), Europe (+22%), and Asia-Pacific (+20%) [1]."
```

## Testing

### Manual Test (Standalone)

Test the MCP server without Claude Desktop:

```bash
source .venv-native/bin/activate
PYTHONPATH=/Volumes/tkr-riffic/@tkr-projects/tkr-docusearch python -m src.mcp_server
```

The server will wait for stdin input (MCP protocol). Press Ctrl+C to exit.

### With MCP Inspector

Use the official MCP inspector for interactive testing:

```bash
npx @modelcontextprotocol/inspector python -m src.mcp_server
```

This opens a web UI where you can:
- See available tools
- Call the `research` tool with test queries
- Inspect request/response

## Configuration

### Environment Variables

The MCP server respects these environment variables (set in Claude Desktop config or `.env`):

- `DOCUSEARCH_API_URL`: Research API endpoint (default: `http://localhost:8004`)
- `WORKER_API_URL`: Worker API for images (default: `http://localhost:8002`)
- `FRONTEND_URL`: React frontend URL (default: `http://localhost:3000`)
- `NGROK_URL`: Ngrok tunnel URL (required for vision)

### Customizing Defaults

Edit `src/mcp_server/config.py`:

```python
DEFAULT_NUM_SOURCES = 10  # Number of sources to retrieve
DEFAULT_SEARCH_MODE = "hybrid"  # visual | text | hybrid
VISION_ENABLED = True  # Enable vision support
```

## Troubleshooting

### "DocuSearch API is unavailable"

**Cause**: Research API not running or not accessible

**Fix**:
```bash
./scripts/status.sh  # Check service status
./scripts/start-all.sh  # Start all services
curl http://localhost:8004/api/research/health  # Test API
```

### "No relevant documents found"

**Cause**: No documents match the query or no documents uploaded

**Fix**:
- Rephrase your question
- Upload more documents via the web UI (`http://localhost:3000`)
- Try different search keywords

### Images Not Displaying

**Cause**: Ngrok tunnel not running or `NGROK_URL` not set

**Fix**:
```bash
# Terminal 1: Start ngrok
ngrok http 8002

# Terminal 2: Update .env
echo "NGROK_URL=https://abc123.ngrok.io" >> .env

# Restart Claude Desktop
```

### "ModuleNotFoundError: No module named 'mcp'"

**Cause**: MCP SDK not installed in virtual environment

**Fix**:
```bash
source .venv-native/bin/activate
pip install mcp httpx
```

### Check MCP Server Logs

Claude Desktop logs MCP server stderr output. Check for errors:

- **macOS**: `~/Library/Logs/Claude/mcp-server-docusearch.log`
- **Windows**: `%LOCALAPPDATA%\Claude\logs\mcp-server-docusearch.log`

## Architecture

```
┌─────────────────┐
│ Claude Desktop  │
│   (MCP Client)  │
└────────┬────────┘
         │ MCP stdio
         ▼
┌─────────────────────────────┐
│   DocuSearch MCP Server     │
│   - Single 'research' tool  │
│   - Fetch images via ngrok  │
│   - Format citations        │
└────────┬────────────────────┘
         │ HTTP
         ▼
┌─────────────────────────────┐
│  Research API (port 8004)   │
│  /api/research/context-only │
│  - Search (visual + text)   │
│  - Build context            │
│  - Extract image URLs       │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│   Worker API (port 8002)    │
│   - Serve images via ngrok  │
│   - ColPali embeddings      │
└─────────────────────────────┘
```

## Development

### Project Structure

```
src/mcp_server/
├── __init__.py          # Package metadata
├── __main__.py          # Entry point for `python -m src.mcp_server`
├── server.py            # Main MCP server implementation
├── config.py            # Configuration constants
├── utils.py             # Image fetching, link building, error handling
├── requirements.txt     # MCP server dependencies
└── README.md           # This file
```

### Adding Features

1. **New Tool**: Add to `@app.list_tools()` in `server.py`
2. **New Endpoint**: Update `CONTEXT_ENDPOINT` in `config.py`
3. **Custom Error Handling**: Add to `format_error_message()` in `utils.py`

## Performance

- **Search Latency**: ~450ms (same as backend API)
- **Image Fetch**: ~100-300ms per image (via ngrok)
- **Total Response Time**: ~1-2s for 10 sources with 2 images

## Security

- **Localhost Only**: MCP server assumes DocuSearch runs on localhost
- **HTTPS Images**: Ngrok provides HTTPS for Claude Desktop compatibility
- **No Authentication**: MCP server has no auth (assumes trusted local environment)

## License

Same as DocuSearch project.

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review DocuSearch logs: `tail logs/research-api.log`
3. Test backend API directly: `curl http://localhost:8004/api/research/health`
4. File issue in DocuSearch repository
