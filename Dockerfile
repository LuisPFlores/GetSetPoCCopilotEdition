# ---------------------------------------------------------------------------
# GetSetPOx MCP Server — Docker image
# Suitable for Azure Container Apps, Azure App Service, or any OCI host.
# ---------------------------------------------------------------------------

FROM python:3.12-slim

# ── System dependencies (for cryptography wheel) ────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libffi-dev \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# ── Non-root user for security ───────────────────────────────────────────────
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# ── Copy upstream services package first (layer-cache friendly) ─────────────
COPY GetSetPOx_repo/ ./GetSetPOx_repo/

# ── Copy server package ──────────────────────────────────────────────────────
COPY getset_pox_mcp_server/ ./getset_pox_mcp_server/
COPY pyproject.toml ./

# ── Install dependencies ─────────────────────────────────────────────────────
# The pyproject.toml references GetSetPOx_repo as a local path dependency.
RUN pip install --no-cache-dir -e ".[standard]" 2>/dev/null || \
    pip install --no-cache-dir \
        "mcp>=1.2.0" \
        "msal>=1.28.0" \
        "httpx>=0.27.0" \
        "pydantic>=2.0.0" \
        "python-dotenv>=1.0.0" \
        "starlette>=0.37.0" \
        "uvicorn[standard]>=0.29.0" \
        "cryptography>=42.0.0" \
    && pip install --no-cache-dir -e ./GetSetPOx_repo \
    && pip install --no-cache-dir -e .

# ── Switch to non-root ───────────────────────────────────────────────────────
RUN chown -R appuser:appuser /app
USER appuser

# ── Runtime configuration ────────────────────────────────────────────────────
ENV MCP_HTTP_HOST=0.0.0.0 \
    MCP_HTTP_PORT=8080 \
    MCP_LOG_LEVEL=INFO

EXPOSE 8080

# Health check for Azure Container Apps / load balancers
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Default: HTTP transport for Copilot Studio
# Override with: docker run ... python -m getset_pox_mcp_server.server
# for stdio mode (not useful in a container).
CMD ["python", "-m", "getset_pox_mcp_server.main_http"]