# Copyright Atlan, Inc. All Rights Reserved.
#
# Licensed under the MIT License.

# Build stage with UV for dependency management
FROM python:3.11-slim AS builder

# Install UV
RUN pip install --no-cache-dir uv

# Set up working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking
ENV UV_LINK_MODE=copy

# Prefer the system python
ENV UV_PYTHON_PREFERENCE=only-system

# First, copy all source files
COPY . .

# Create a virtual environment and install the package directly with pip
RUN python -m venv .venv && \
    . .venv/bin/activate && \
    pip install --no-cache-dir -e .

# Final stage
FROM python:3.11-slim

# Install curl for healthcheck and other required tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    groupadd --system --gid 1001 app && \
    useradd --system --gid app --uid 1001 app && \
    mkdir -p /app && \
    chown app:app /app

WORKDIR /app

# Copy the virtual environment and source code
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app /app

# Create healthcheck script
RUN echo '#!/bin/sh\ncurl --fail http://localhost:8000/health || exit 1' > /usr/local/bin/healthcheck.sh && \
    chmod +x /usr/local/bin/healthcheck.sh

# Set PATH to use virtual environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

# Install UV in the final image for running MCP
RUN pip install --no-cache-dir uv

# Create UV cache directory and set proper permissions
RUN mkdir -p /home/app/.cache/uv && \
    chown -R app:app /home/app

# Run as non-root
USER app

# Expose the port the app runs on
EXPOSE 8000

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD [ "/usr/local/bin/healthcheck.sh" ]

CMD ["uv", "run", "--with", "mcp[cli]", "--with", "pyatlan", "mcp", "run", "server.py"]
