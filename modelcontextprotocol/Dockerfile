FROM registry.atlan.com/public/pyatlan:main-latest

USER root
WORKDIR /home/nonroot/app

# Set UV environment variables
ENV UV_NO_MANAGED_PYTHON=true \
    UV_SYSTEM_PYTHON=true

# Copy project files
COPY --chown=nonroot:nonroot . /home/nonroot/app

# Install MCP server and its deps to system python
# pyatlan and common deps (pydantic, httpx, cryptography, etc.) already in base image
RUN uv pip install --system --no-cache --no-deps . && \
    uv pip install --system --no-cache \
        "fastmcp>=2.14.0" \
        "uvicorn>=0.35.0" && \
    rm -rf /root/.cache ~/.cache

ENV MCP_TRANSPORT="stdio"
ENV MCP_HOST="0.0.0.0"
ENV MCP_PORT="8000"
ENV MCP_PATH="/"

USER nonroot

ENTRYPOINT ["sh", "-c", "exec python server.py --transport \"$MCP_TRANSPORT\" --host \"$MCP_HOST\" --port \"$MCP_PORT\" --path \"$MCP_PATH\""]
