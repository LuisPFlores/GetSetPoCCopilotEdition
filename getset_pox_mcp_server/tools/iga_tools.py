"""
Identity Governance and Administration (IGA) tools.

Wraps the 4 functions in getset_pox_mcp.services.iga.iga_service and
exposes them as MCP tools for Entra Entitlement Management.
"""

from typing import Optional
from mcp.server.fastmcp import FastMCP
from getset_pox_mcp_server.services_adapter import safe_call

def register_iga_tools(mcp: FastMCP) -> None:
    """Register all IGA tools on the FastMCP instance."""

    @mcp.tool()
    async def iga_list_access_packages(
        select: Optional[str] = None,
        filter: Optional[str] = None,
        expand: Optional[str] = None,
    ) -> dict:
        """
        List all Entra Entitlement Management access packages.

        Access packages bundle resources (groups, apps, SharePoint sites) that
        users can request access to through the My Access portal.

        Args:
            select: OData $select — comma-separated property names to return,
                    e.g. "id,displayName,description".
            filter: OData $filter expression to narrow results,
                    e.g. "contains(tolower(displayName),'finance')".
            expand: OData $expand to include related entities,
                    e.g. "accessPackageCatalog".

        Returns:
            {
              "success": true,
              "data": {"accessPackages": [...], "count": N}
            }
        """
        from getset_pox_mcp.services.iga.iga_service import IGA_listAccessPackages
        return await safe_call(
            IGA_listAccessPackages,
            select=select,
            filter=filter,
            expand=expand,
        )

    @mcp.tool()
    async def iga_create_access_catalog(
        display_name: str,
        description: str,
        state: str,
        is_externally_visible: bool,
    ) -> dict:
        """
        Create a new Entra Entitlement Management access package catalog.

        Catalogs are containers for access packages and their associated
        resources.  A published catalog is visible to requestors.

        Args:
            display_name:          Display name for the new catalog (required).
            description:           Human-readable description of the catalog.
            state:                 "published" to make the catalog active, or
                                   "unpublished" to keep it hidden.
            is_externally_visible: True to allow guest/external users to request
                                   packages from this catalog.

        Returns:
            {
              "success": true,
              "data": {"catalog": {...}, "catalogId": "...", "message": "..."}
            }
        """
        from getset_pox_mcp.services.iga.iga_service import IGA_createAccessCatalog
        return await safe_call(
            IGA_createAccessCatalog,
            displayName=display_name,
            description=description,
            state=state,
            isExternallyVisible=is_externally_visible,
        )

    @mcp.tool()
    async def iga_create_access_package(
        catalog_id: str,
        display_name: str,
        description: Optional[str] = None,
    ) -> dict:
        """
        Create a new access package inside an existing Entitlement Management catalog.

        Access packages define what resources users get and for how long once
        their request is approved.

        Args:
            catalog_id:   Object ID of the catalog that will own this package.
            display_name: Display name for the access package.
            description:  Optional description of the access package purpose.

        Returns:
            {
              "success": true,
              "data": {
                "accessPackage": {...},
                "accessPackageId": "...",
                "catalogId": "..."
              }
            }
        """
        from getset_pox_mcp.services.iga.iga_service import IGA_createAccessPackage
        return await safe_call(
            IGA_createAccessPackage,
            catalogId=catalog_id,
            displayName=display_name,
            description=description,
        )

    @mcp.tool()
    async def iga_add_group_to_access_package(
        catalog_id: str,
        access_package_id: str,
        group_object_id: str,
    ) -> dict:
        """
        Add an Entra ID security group as a resource (Member role) to an access package.

        Implements a two-step workflow:
          1. Registers the group with the catalog as a resource.
          2. Links the Member role of that group to the access package scope.

        When a user is granted the access package they are automatically added
        to the group.

        Args:
            catalog_id:        Object ID of the Entitlement Management catalog.
            access_package_id: Object ID of the target access package.
            group_object_id:   Object ID (GUID) of the Entra ID group to add.

        Returns:
            {
              "success": true,
              "data": {
                "catalogId": "...",
                "accessPackageId": "...",
                "groupObjectId": "...",
                "resourceId": "...",
                "roleId": "...",
                "role": "Member"
              }
            }
        """
        from getset_pox_mcp.services.iga.iga_service import IGA_addResourceGrouptoPackage
        return await safe_call(
            IGA_addResourceGrouptoPackage,
            catalogId=catalog_id,
            accessPackageId=access_package_id,
            groupObjectId=group_object_id,
        )