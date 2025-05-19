# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

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

FROM python:3.12-slim-bookworm AS runtime

RUN groupadd -r appuser && useradd -r -g appuser -m -d /home/appuser appuser

WORKDIR /appuser

COPY --from=builder --chown=appuser:appuser /app /appuser

# Set the PATH to use the virtual environment
ENV PATH="/appuser/.venv/bin:$PATH"

ENV MCP_TRANSPORT="stdio"
ENV MCP_HOST="0.0.0.0"
ENV MCP_PORT="8000"
ENV MCP_PATH="/"

USER appuser

ENTRYPOINT exec python server.py --transport "$MCP_TRANSPORT" --host "$MCP_HOST" --port "$MCP_PORT" --path "$MCP_PATH"
