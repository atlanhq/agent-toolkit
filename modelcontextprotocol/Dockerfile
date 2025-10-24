# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# Set environment variables for build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install the project into `/app`
WORKDIR /app

# Copy only dependency files first (better caching)
COPY pyproject.toml uv.lock ./
COPY version.py ./
COPY README.md ./

# Create a virtual environment and install dependencies
RUN python -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
RUN uv sync --no-cache-dir --no-dev --python /app/.venv/bin/python

# Copy the rest of the application
COPY . /app

FROM python:3.12-slim-bookworm AS runtime

# Create non-root user with specific UID/GID for better security
RUN groupadd -r -g 1001 appuser && \
    useradd -r -g appuser -u 1001 -m -d /home/appuser appuser

WORKDIR /appuser

COPY --from=builder --chown=appuser:appuser /app /appuser

# Set the PATH to use the virtual environment
ENV PATH="/appuser/.venv/bin:$PATH"

# Environment variables with defaults
ENV MCP_TRANSPORT="stdio" \
    MCP_HOST="0.0.0.0" \
    MCP_PORT="8000" \
    MCP_PATH="/"

# Simple health check for HTTP transports (without external dependencies)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD if [ "$MCP_TRANSPORT" = "sse" ] || [ "$MCP_TRANSPORT" = "streamable-http" ]; then \
        python -c "import urllib.request; urllib.request.urlopen('http://localhost:$MCP_PORT$MCP_PATH', timeout=5)" || exit 1; \
        else exit 0; fi

USER appuser

ENTRYPOINT ["sh", "-c", "exec python server.py --transport \"$MCP_TRANSPORT\" --host \"$MCP_HOST\" --port \"$MCP_PORT\" --path \"$MCP_PATH\""]
