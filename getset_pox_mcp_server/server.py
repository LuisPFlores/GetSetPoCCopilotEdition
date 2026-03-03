"""
GetSetPOx MCP Server — stdio entry point.

Run this module to expose all 31 GetSetPOx tools over the MCP stdio
transport, which is compatible with:

  * Cline / Claude Code
  * GitHub Copilot CLI
  * VS Code MCP extension
  * Any stdio-based MCP client

Usage
-----
Direct::

    python -m getset_pox_mcp_server.server

Or after ``pip install -e .``::

    getset-pox-mcp-server

Environment variables required::

    MS_GRAPH_CLIENT_ID      — Azure AD app registration client ID
    MS_GRAPH_CLIENT_SECRET  — Client secret
    MS_GRAPH_TENANT_ID      — Azure AD tenant ID

Optional::

    MCP_LOG_LEVEL           — Logging level (DEBUG / INFO / WARNING, default INFO)

mcp.json / VS Code settings example::

    {
      "servers": {
        "getset-pox": {
          "command": "python",
          "args": ["-m", "getset_pox_mcp_server.server"],
          "env": {
            "MS_GRAPH_CLIENT_ID":     "${env:MS_GRAPH_CLIENT_ID}",
            "MS_GRAPH_CLIENT_SECRET": "${env:MS_GRAPH_CLIENT_SECRET}",
            "MS_GRAPH_TENANT_ID":     "${env:MS_GRAPH_TENANT_ID}"
          }
        }
      }
    }
"""

import logging
import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load .env if present (ignored when env vars are already set by the host)
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
# FastMCP instance
# ---------------------------------------------------------------------------
mcp = FastMCP(
    name="getset_pox",
    instructions=(
        "GetSetPOx MCP server — provides tools for managing Microsoft Entra ID, "
        "Intune, Global Secure Access (Internet Access), Identity Governance & "
        "Administration (IGA / Entitlement Management), and end-to-end POC "
        "automation via Microsoft Graph API with client credential authentication."
    ),
)

# ---------------------------------------------------------------------------
# Register all domain tools
# ---------------------------------------------------------------------------
from getset_pox_mcp_server.tools import register_all_tools  # noqa: E402

register_all_tools(mcp)

logger.info("GetSetPOx MCP server initialised — %d tools registered", len(mcp._tool_manager._tools))

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the MCP server over stdio (default transport for Cline / Copilot CLI)."""
    logger.info("Starting GetSetPOx MCP server (stdio transport)")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()