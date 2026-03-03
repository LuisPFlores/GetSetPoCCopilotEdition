"""
GetSetPOx MCP Server — HTTP entry point for Copilot Studio.

Uses the MCP **Streamable HTTP** transport (mcp >= 1.2), which exposes
a single ``/mcp`` endpoint that handles both GET (SSE stream) and POST
(JSON-RPC messages).  This is the transport recommended for hosting
behind Azure Container Apps / App Service and consuming from
Microsoft Copilot Studio's MCP connector.

Routes
------
GET  /health  — liveness probe (JSON)
GET  /mcp     — MCP Streamable HTTP endpoint (SSE stream)
POST /mcp     — MCP Streamable HTTP endpoint (JSON-RPC messages)

Usage
-----
Local::

    python -m getset_pox_mcp_server.main_http

Docker / Azure Container Apps::

    docker run -p 80:80 \\
      -e MS_GRAPH_CLIENT_ID=... \\
      -e MS_GRAPH_CLIENT_SECRET=... \\
      -e MS_GRAPH_TENANT_ID=... \\
      getset-pox-mcp-server

MCP endpoint URL for Copilot Studio::

    https://<yourapp>.azurecontainerapps.io/mcp

Environment variables
---------------------
Required:
    MS_GRAPH_CLIENT_ID      — Azure AD app registration client ID
    MS_GRAPH_CLIENT_SECRET  — Client secret
    MS_GRAPH_TENANT_ID      — Azure AD tenant ID

Optional:
    MCP_HTTP_HOST           — Bind host (default: 0.0.0.0)
    MCP_HTTP_PORT           — Bind port (default: 80)
    MCP_LOG_LEVEL           — Logging level (default: INFO)
"""

import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

# Load .env if present
load_dotenv()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=os.environ.get("MCP_LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastMCP instance + tool registration
# ---------------------------------------------------------------------------
mcp = FastMCP(
    name="getset_pox",
    instructions=(
        "GetSetPOx MCP server — provides tools for managing Microsoft Entra ID, "
        "Intune, Global Secure Access (Internet Access), Identity Governance & "
        "Administration (IGA / Entitlement Management), and end-to-end POC "
        "automation via Microsoft Graph API with client credential authentication."
    ),
    # host="0.0.0.0" disables the auto-enable of DNS-rebinding protection
    # (which only applies when host is 127.0.0.1/localhost).
    # Actual bind address and port are controlled by uvicorn settings below.
    host="0.0.0.0",
    port=int(os.environ.get("MCP_HTTP_PORT", "80")),
)

from getset_pox_mcp_server.tools import register_all_tools  # noqa: E402

register_all_tools(mcp)
logger.info("GetSetPOx HTTP MCP server — %d tools registered", len(mcp._tool_manager._tools))

# ---------------------------------------------------------------------------
# Build the streamable HTTP ASGI app once at module level so that the
# session_manager is initialised before build_app() is called by uvicorn.
# ---------------------------------------------------------------------------
_mcp_asgi = mcp.streamable_http_app()   # creates mcp._session_manager

# ---------------------------------------------------------------------------
# Health-check endpoint
# ---------------------------------------------------------------------------

async def healthcheck(request: Request) -> JSONResponse:
    """Liveness probe for load-balancers and container health checks."""
    tool_names = list(mcp._tool_manager._tools.keys())
    return JSONResponse(
        {
            "status": "ok",
            "server": "getset_pox_mcp",
            "transport": "streamable-http",
            "mcp_endpoint": "/mcp",
            "tool_count": len(tool_names),
            "tools": tool_names,
        }
    )

# ---------------------------------------------------------------------------
# Combined lifespan
#
# Starlette does NOT propagate lifespan events into mounted sub-apps.
# The streamable_http_app() embeds a lifespan that runs
#   mcp.session_manager.run()
# which initialises the anyio TaskGroup that the StreamableHTTPASGIApp needs.
# We reproduce that here in the outer app's lifespan so the task group
# is active for every request routed through Mount("/", _mcp_asgi).
# ---------------------------------------------------------------------------

@asynccontextmanager
async def _lifespan(app: Starlette):
    """Start the MCP session manager task group, then yield to serve requests."""
    async with mcp.session_manager.run():
        logger.info("MCP session manager started — ready to serve /mcp")
        yield
    logger.info("MCP session manager stopped")

# ---------------------------------------------------------------------------
# Build the Starlette ASGI app
# ---------------------------------------------------------------------------

def build_app() -> Starlette:
    """
    Build the Starlette ASGI application.

    Routes:
      GET  /health  — liveness probe
      *    /mcp     — MCP Streamable HTTP (GET=SSE stream, POST=JSON-RPC)
    """
    app = Starlette(
        lifespan=_lifespan,
        routes=[
            Route("/health", endpoint=healthcheck, methods=["GET"]),
            Mount("/", app=_mcp_asgi),
        ],
    )

    # CORS — allows Copilot Studio (hosted origin) to reach this endpoint.
    # Restrict allow_origins in production.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Start the HTTP MCP server with uvicorn."""
    host = os.environ.get("MCP_HTTP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_HTTP_PORT", "80"))

    logger.info("Starting GetSetPOx MCP server (streamable-http) on %s:%s", host, port)
    logger.info("MCP endpoint : http://%s:%s/mcp", host, port)
    logger.info("Health check : http://%s:%s/health", host, port)

    uvicorn.run(
        "getset_pox_mcp_server.main_http:build_app",
        factory=True,
        host=host,
        port=port,
        log_level=os.environ.get("MCP_LOG_LEVEL", "info").lower(),
    )

if __name__ == "__main__":
    main()