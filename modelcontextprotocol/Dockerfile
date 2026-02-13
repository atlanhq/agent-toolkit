# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

# Set environment variables for build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install the project into `/app`
WORKDIR /app

ADD . /app

# Create a virtual environment and install dependencies
RUN python -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
RUN uv sync --no-cache-dir --no-dev --python /app/.venv/bin/python

FROM registry.atlan.com/public/pyatlan:main-latest AS runtime

WORKDIR /home/nonroot/app

COPY --from=builder --chown=nonroot:nonroot /app /home/nonroot/app

# Fix venv python symlink: builder has python at /usr/local/bin, runtime at /usr/bin
RUN ln -sf /usr/bin/python3 /home/nonroot/app/.venv/bin/python && \
    ln -sf /usr/bin/python3 /home/nonroot/app/.venv/bin/python3

# Set the PATH to use the virtual environment
ENV PATH="/home/nonroot/app/.venv/bin:$PATH"

ENV MCP_TRANSPORT="stdio"
ENV MCP_HOST="0.0.0.0"
ENV MCP_PORT="8000"
ENV MCP_PATH="/mcp/"

USER nonroot

ENTRYPOINT ["sh", "-c", "exec python server.py --transport \"$MCP_TRANSPORT\" --host \"$MCP_HOST\" --port \"$MCP_PORT\" --path \"$MCP_PATH\""]
