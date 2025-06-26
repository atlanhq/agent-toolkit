## Deployment Guide for Atlan MCP Server

This document explains the various ways you can start the **Atlan MCP Server** and when to choose a given transport mechanism.

### Quick-start

```bash
# Default (stdio – recommended for local development)
python modelcontextprotocol/server.py

# Stream over Server-Sent Events (SSE) – great for browsers or reverse proxies
python modelcontextprotocol/server.py --transport sse --host 0.0.0.0 --port 8000

# Stream over plain HTTP ("streamable-http") – useful when SSE is not available
python modelcontextprotocol/server.py --transport streamable-http --host 0.0.0.0 --port 8000 --path /
```

### Transport options

- **`stdio` (default)**
  Communicates over standard input/output.
  • Benefits: Zero network overhead; perfect for running the agent as a local subprocess.
  • When to use: Local development or when integrating directly with parent processes or editors that spawn the server.

- **`sse`**
  Uses **Server-Sent Events** over HTTP—the server keeps an HTTP connection open and pushes a `text/event-stream` as new data arrives.
  • Benefits: Built-in support in modern browsers & many HTTP reverse proxies; uni-directional and firewall-friendly; low-latency streaming suited for real-time UI updates.
  • When to use: When you are building a Web UI that consumes streamed completions, or you want a push-based model but do not need the bi-directionality of WebSockets.

- **`streamable-http`**
  Sends a standard HTTP response whose body is streamed incrementally (chunked transfer-encoding).
  • Benefits: Works with any HTTP client (curl, Python `requests`, Java `HttpClient`, etc.); no special SSE handling required; plays nicely with infrastructure that terminates or transforms HTTP but does **not** understand event streams.
  • When to use: The consumer is a language or runtime lacking SSE support, or you want to keep the transport strictly within the HTTP spec without custom headers.

> **Note**
> The CLI flag is `--transport streamable-http` (with a hyphen), while you may see it described conceptually as *HTTP-streamable*.

### Choosing between **SSE** and **streamable-HTTP**

Both transports let you receive incremental updates over the network. The table below can help you decide:

| Criterion | Choose **SSE** if… | Choose **streamable-HTTP** if… |
|-----------|-------------------|------------------------------|
| Client library availability | Your consumer is a browser or a library that natively understands `text/event-stream`. | You only have a basic HTTP client that can read a stream of bytes/chunks. |
| Proxy / Load-balancer support | You have control over proxy settings and can enable event-stream passthrough. | You are behind a gateway that **rewrites** or **buffers** SSE but still supports chunked HTTP responses. |
| Simplicity of parsing | You prefer the simple event structure (`data: ...\n\n`). | You prefer raw JSON or text chunks without the SSE framing. |
| Bi-directionality | Not required. | Not required. *(If you need full duplex, consider WebSockets—currently not exposed by the server.)* |

### Environment variables & production tips

* Ensure `ATLAN_BASE_URL` and `ATLAN_API_KEY` are provided (e.g., via a secrets manager).
* Expose the chosen port (`--port`, default `8000`) in your container or deployment manifest.
* Use health checks (e.g., `GET /healthz`) if you add one via a reverse proxy.
* Pin the server image/tag that matches the library versions required by your agent.

---

For additional configuration (timeouts, logging, etc.) refer to `modelcontextprotocol/settings.py` and the root `README.md`.
