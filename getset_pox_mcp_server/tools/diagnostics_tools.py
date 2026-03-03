"""
Diagnostics tools — Microsoft Graph permission checker.

Exposes one MCP tool that tests all 19 Graph permissions by making live
API calls and returning a structured summary.
"""

from mcp.server.fastmcp import FastMCP
from getset_pox_mcp_server.services_adapter import safe_call


def register_diagnostics_tools(mcp: FastMCP) -> None:
    """Register diagnostics tools on the FastMCP instance."""

    @mcp.tool()
    async def pox_check_token_permissions() -> dict:
        """
        Test all 19 Microsoft Graph API permissions against live endpoints.

        Makes a real HTTP request to each Graph endpoint to verify whether
        the application's service principal has been granted the required
        permission and admin consent is in place.

        Permissions tested (19 total):
          Application.Read.All, Device.Read.All,
          DeviceManagementApps.Read/ReadWrite.All,
          DeviceManagementConfiguration.ReadWrite.All,
          DeviceManagementManagedDevices.ReadWrite.All,
          Directory.Read.All, EntitlementManagement.ReadWrite.All,
          Group.Read/ReadWrite.All, GroupMember.Read/ReadWrite.All,
          NetworkAccess.Read/ReadWrite.All, Policy.Read.All,
          Policy.Read/ReadWrite.ConditionalAccess,
          User.Read.All, User.ReadBasic.All.

        Returns:
            {
              "success": true,
              "data": {
                "summary": {"working": N, "missing": M, "total": 19},
                "tests":   [{"permission": "...", "status": "✅ WORKING | ❌ MISSING"}]
              }
            }
        """
        from getset_pox_mcp.services.diagnostics.diagnostics_service import (
            check_token_permissions,
        )

        return await safe_call(check_token_permissions)