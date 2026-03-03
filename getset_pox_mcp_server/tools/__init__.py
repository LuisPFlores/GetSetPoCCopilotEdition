"""
Tool registration hub.

``register_all_tools(mcp)`` adds every domain's tools to the FastMCP
instance in a single call from ``server.py`` / ``main_http.py``.
"""

from mcp.server.fastmcp import FastMCP

from getset_pox_mcp_server.tools.diagnostics_tools import register_diagnostics_tools
from getset_pox_mcp_server.tools.eid_tools import register_eid_tools
from getset_pox_mcp_server.tools.iga_tools import register_iga_tools
from getset_pox_mcp_server.tools.internet_access_tools import register_internet_access_tools
from getset_pox_mcp_server.tools.intune_tools import register_intune_tools
from getset_pox_mcp_server.tools.poc_tools import register_poc_tools


def register_all_tools(mcp: FastMCP) -> None:
    """
    Register all GetSetPOx MCP tools with the provided FastMCP instance.

    Groups:
        - Diagnostics  (1 tool)
        - Entra ID     (10 tools)
        - IGA          (4 tools)
        - Internet Access / GSA  (8 tools)
        - Intune       (7 tools)
        - POC          (1 tool)

    Args:
        mcp: The FastMCP server instance to register tools on.
    """
    register_diagnostics_tools(mcp)
    register_eid_tools(mcp)
    register_iga_tools(mcp)
    register_internet_access_tools(mcp)
    register_intune_tools(mcp)
    register_poc_tools(mcp)