# Atlan MCP Server Deployment Guide

This guide provides detailed information about deploying the Atlan MCP server using different transport protocols and deployment strategies.

## Table of Contents

- [Transport Protocols](#transport-protocols)
  - [STDIO Transport](#stdio-transport)
  - [SSE Transport](#sse-transport)
  - [Streamable HTTP Transport](#streamable-http-transport)
- [Deployment Scenarios](#deployment-scenarios)
  - [Local Development](#local-development)
  - [Production Deployment](#production-deployment)


## Transport Protocols

The Atlan MCP server supports three different transport protocols, each optimized for different deployment scenarios and use cases.

### STDIO Transport

**Description**: Standard Input/Output transport using stdin/stdout for communication.

**Command**:
```bash
uv run atlan-mcp-server --transport stdio
```

**Benefits**:
- ✅ **Simplicity**: Easiest to set up and configure
- ✅ **Local Development**: Perfect for local development and testing
- ✅ **MCP Client Compatibility**: Native support in Claude Desktop and Cursor
- ✅ **Low Overhead**: Minimal resource usage and latency
- ✅ **Direct Communication**: No network stack overhead

**Use Cases**:
- Local development with Claude Desktop or Cursor
- Testing and debugging MCP tools
- Simple integrations where network communication isn't required
- Single-user scenarios

**Limitations**:
- ❌ Not suitable for remote deployments
- ❌ Cannot handle multiple concurrent clients
- ❌ No built-in authentication or authorization

### SSE Transport

**Description**: Server-Sent Events transport for real-time, HTTP-based communication.

**Command**:
```bash
uv run atlan-mcp-server --transport sse --host 0.0.0.0 --port 8000 --path /
```

**Benefits**:
- ✅ **Real-time Communication**: Efficient server-to-client streaming
- ✅ **HTTP-based**: Works with standard HTTP infrastructure
- ✅ **Firewall Friendly**: Uses standard HTTP ports (80/443)
- ✅ **Browser Compatible**: Can be accessed from web browsers
- ✅ **Automatic Reconnection**: Built-in connection recovery
- ✅ **Load Balancer Support**: Works with standard HTTP load balancers
- ✅ **Scalable**: Supports multiple concurrent connections

**Use Cases**:
- Production deployments requiring real-time updates
- Web-based MCP clients
- Multi-user environments
- Cloud deployments with auto-scaling
- Scenarios requiring push notifications or live updates

**Configuration Parameters**:
- `--host`: Server bind address (default: 0.0.0.0)
- `--port`: Server port (default: 8000)
- `--path`: HTTP path (default: /)

**Example Deployment**:
```bash
# Basic SSE server
uv run atlan-mcp-server --transport sse

# Custom configuration
uv run atlan-mcp-server --transport sse --host 127.0.0.1 --port 9000 --path /mcp
```

### Streamable HTTP Transport

**Description**: Full HTTP transport with request/response streaming capabilities.

**Command**:
```bash
uv run atlan-mcp-server --transport streamable-http --host 0.0.0.0 --port 8000 --path /
```

**Benefits**:
- ✅ **Full HTTP Support**: Complete HTTP request/response cycle
- ✅ **REST API Compatible**: Can be integrated with REST APIs
- ✅ **Streaming Responses**: Supports large response streaming
- ✅ **Caching Support**: HTTP caching headers and mechanisms
- ✅ **Authentication Integration**: Easy integration with HTTP auth
- ✅ **Proxy Support**: Works with HTTP proxies and gateways
- ✅ **High Throughput**: Optimized for large data transfers

**Use Cases**:
- High-volume data processing scenarios
- Integration with existing HTTP infrastructure
- Scenarios requiring HTTP caching
- Large file or dataset operations
- Enterprise deployments with complex networking requirements
- API gateway integrations

**Configuration Parameters**:
- `--host`: Server bind address (default: 0.0.0.0)
- `--port`: Server port (default: 8000)  
- `--path`: HTTP path (default: /)

**Example Deployment**:
```bash
# Basic streamable HTTP server
uv run atlan-mcp-server --transport streamable-http

# Production configuration
uv run atlan-mcp-server --transport streamable-http --host 0.0.0.0 --port 443 --path /api/mcp
```

## Deployment Scenarios

### Local Development

**Recommended Transport**: STDIO

```bash
# For Claude Desktop/Cursor integration
uv run atlan-mcp-server --transport stdio
```

**Configuration** (Claude Desktop):
```json
{
  "mcpServers": {
    "Atlan MCP": {
      "command": "uv",
      "args": ["run", "atlan-mcp-server", "--transport", "stdio"],
      "env": {
        "ATLAN_API_KEY": "your_api_key",
        "ATLAN_BASE_URL": "https://your-instance.atlan.com",
        "ATLAN_AGENT_ID": "your_agent_id"
      }
    }
  }
}
```

### Production Deployment

**Recommended Transport**: SSE or Streamable HTTP

For production deployments, you can run the server directly on your host machine or virtual machine:

```bash
# SSE Transport (recommended for production)
uv run atlan-mcp-server --transport sse --host 0.0.0.0 --port 8000

# Streamable HTTP Transport
uv run atlan-mcp-server --transport streamable-http --host 0.0.0.0 --port 8000
```

Make sure to set the required environment variables:
```bash
export ATLAN_API_KEY="your_api_key"
export ATLAN_BASE_URL="https://your-instance.atlan.com"
export ATLAN_AGENT_ID="your_agent_id"
```
