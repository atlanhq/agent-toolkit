# Atlan MCP Server Deployment Guide

This guide covers transport modes and basic deployment options for the Atlan MCP Server.

## Transport Modes

The Atlan MCP Server supports three transport modes. For more details about MCP transport modes, see the [official MCP documentation](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports).

| Transport Mode | Use Case | Benefits | When to Use |
|---|---|---|---|
| **stdio** (Default) | Local development, IDE integrations | Simple, direct communication | Claude Desktop, Cursor IDE, VSCode |
| **SSE** (Server-Sent Events) | Remote deployments, web browsers | Real-time streaming, web-compatible | Cloud deployments, web clients |
| **streamable-http** | HTTP-based remote connections | Standard HTTP, load balancer friendly | Kubernetes, containerized deployments |

## Basic Deployment Examples

### Local Development (stdio)
```bash
# Default stdio mode
python server.py

# Or explicitly specify stdio
python server.py --transport stdio
```

### VSCode Integration

VSCode integration with MCP servers supports multiple approaches:

#### Using AI Toolkit Extension
```bash
# Install the AI Toolkit extension in VSCode
# Then configure MCP server through the Agent Builder interface
# Command: uvx
# Arguments: atlan-mcp-server
# Environment Variables: ATLAN_API_KEY, ATLAN_BASE_URL, ATLAN_AGENT_ID
```

#### Manual VSCode Configuration
```json
// In VSCode settings.json
{
  "mcp.servers": {
    "atlan": {
      "command": "uvx",
      "args": ["atlan-mcp-server"],
      "env": {
        "ATLAN_API_KEY": "<YOUR_API_KEY>",
        "ATLAN_BASE_URL": "https://<YOUR_INSTANCE>.atlan.com",
        "ATLAN_AGENT_ID": "<YOUR_AGENT_ID>"
      }
    }
  }
}
```

### Cloud Deployment (SSE)
```bash
# Docker with SSE
docker run -d \
  -p 8000:8000 \
  -e ATLAN_API_KEY="<YOUR_API_KEY>" \
  -e ATLAN_BASE_URL="https://<YOUR_INSTANCE>.atlan.com" \
  -e MCP_TRANSPORT="sse" \
  ghcr.io/atlanhq/atlan-mcp-server:latest

# Python with SSE
python server.py --transport sse --host 0.0.0.0 --port 8000
```

### HTTP Deployment (streamable-http)
```bash
# Docker with HTTP
docker run -d \
  -p 8000:8000 \
  -e ATLAN_API_KEY="<YOUR_API_KEY>" \
  -e ATLAN_BASE_URL="https://<YOUR_INSTANCE>.atlan.com" \
  -e MCP_TRANSPORT="streamable-http" \
  ghcr.io/atlanhq/atlan-mcp-server:latest

# Python with HTTP
python server.py --transport streamable-http --host 0.0.0.0 --port 8000
```

## Environment Variables

### Required
- `ATLAN_API_KEY`: Your Atlan API key
- `ATLAN_BASE_URL`: Your Atlan instance URL

### Transport Configuration
- `MCP_TRANSPORT`: Transport mode (stdio/sse/streamable-http)
- `MCP_HOST`: Host address for network transports (default: 0.0.0.0)
- `MCP_PORT`: Port number for network transports (default: 8000)
- `MCP_PATH`: Path for streamable-http transport (default: /)

### Optional
- `ATLAN_AGENT_ID`: Agent identifier
- `RESTRICTED_TOOLS`: Comma-separated list of tools to restrict

For additional support, refer to the main [README](../README.md) or contact support@atlan.com.
