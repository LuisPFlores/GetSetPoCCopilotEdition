"""
POC orchestration tools — end-to-end proof-of-concept automation.

Wraps the GovernInternetAccessPOC function from
getset_pox_mcp.services.poc.poc_service and exposes it as a single
high-level MCP action that orchestrates the full IGA + GSA setup workflow.
"""

from mcp.server.fastmcp import FastMCP
from getset_pox_mcp_server.services_adapter import safe_call

def register_poc_tools(mcp: FastMCP) -> None:
    """Register all POC orchestration tools on the FastMCP instance."""

    @mcp.tool()
    async def poc_govern_internet_access() -> dict:
        """
        Run the complete Govern Internet Access proof-of-concept workflow.

        Orchestrates four automated steps using Microsoft Graph:
          1. Create an Entra ID security group (POC-IA-Users) for internet
             access governance.
          2. Create an Entitlement Management access package catalog
             (POC-Internet-Access-Catalog).
          3. Create an access package (POC-Internet-Access-Package) inside
             the catalog.
          4. Add the security group to the access package as a resource
             (Member role).

        After this POC completes:
          - Users assigned the access package become members of the security
            group.
          - The group can be targeted in Conditional Access and GSA filtering
            policies to govern and monitor internet access.

        Returns:
            {
              "success": true,
              "data": {
                "group_id":               "...",
                "catalog_id":             "...",
                "access_package_id":      "...",
                "resource_assignment_id": "..."
              }
            }
        """
        from getset_pox_mcp.services.poc.poc_service import GovernInternetAccessPOC
        return await safe_call(GovernInternetAccessPOC)