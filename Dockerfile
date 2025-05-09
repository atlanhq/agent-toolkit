# Build stage - using Python 3.11 slim image
FROM python:3.11-slim AS builder

# Install UV for efficient package management
RUN pip install --no-cache-dir uv

# Set up working directory
WORKDIR /app

# Configure UV for better performance
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_FROZEN=true

# Copy dependency files first to leverage Docker layer caching
COPY ./modelcontextprotocol/pyproject.toml ./modelcontextprotocol/uv.lock ./

# Install dependencies efficiently with caching
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --no-deps -e .

# Copy application code
COPY ./modelcontextprotocol/ ./modelcontextprotocol/

# Final stage - using the same base image
FROM python:3.11-slim

# Create non-root user with proper permissions
RUN groupadd --system --gid 1001 app && \
    useradd --system --gid app --uid 1001 app && \
    mkdir -p /app && \
    chown app:app /app

WORKDIR /app

# Copy installed packages and application from builder
COPY --from=builder --chown=app:app /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder --chown=app:app /app/modelcontextprotocol/ /app/modelcontextprotocol/

# Install curl for healthcheck (minimal impact on image size)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create healthcheck script
RUN echo '#!/bin/sh\ncurl --fail http://localhost:8000/health || exit 1' > /usr/local/bin/healthcheck.sh && \
    chmod +x /usr/local/bin/healthcheck.sh

# Switch to non-root user
USER app

# Expose the port the app runs on
EXPOSE 8000

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD [ "/usr/local/bin/healthcheck.sh" ]

# Command to run the application
CMD ["python", "-m", "modelcontextprotocol.server"]