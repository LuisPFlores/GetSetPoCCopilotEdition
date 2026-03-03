"""
Entra ID (EID) tools — user, device, and group management.

Wraps the 10 functions in getset_pox_mcp.services.eid.eid_service and
exposes them as MCP tools with snake_case names and typed parameters.
"""

from typing import List, Optional
from mcp.server.fastmcp import FastMCP
from getset_pox_mcp_server.services_adapter import safe_call

def register_eid_tools(mcp: FastMCP) -> None:
    """Register all Entra ID tools on the FastMCP instance."""

    @mcp.tool()
    async def eid_list_users() -> dict:
        """
        List all users in the Microsoft Entra ID (Azure AD) tenant.

        Calls Graph API v1.0 /users and returns the full user collection.

        Returns:
            {"success": true, "data": {"users": [...], "count": N}}
        """
        from getset_pox_mcp.services.eid.eid_service import EID_listUsers
        return await safe_call(EID_listUsers)

    @mcp.tool()
    async def eid_get_user(user_principal_name: str) -> dict:
        """
        Get a specific Entra ID user by object ID or userPrincipalName (UPN).

        Args:
            user_principal_name: The user's object ID (GUID) or UPN
                                 (e.g. alice@contoso.com).

        Returns:
            {"success": true, "data": {"user": {...}}}
        """
        from getset_pox_mcp.services.eid.eid_service import EID_getUser
        return await safe_call(EID_getUser, user_id=user_principal_name)

    @mcp.tool()
    async def eid_search_users(query: str, top: int = 50) -> dict:
        """
        Search Entra ID users whose displayName or UPN starts with the query string.

        Args:
            query: Prefix to match against displayName or userPrincipalName.
            top:   Maximum number of results to return (1–999, default 50).

        Returns:
            {"success": true, "data": {"users": [...], "count": N, "query": "..."}}
        """
        from getset_pox_mcp.services.eid.eid_service import EID_searchUsers
        return await safe_call(EID_searchUsers, query=query, top=top)

    @mcp.tool()
    async def eid_list_devices() -> dict:
        """
        List all devices registered in Entra ID.

        Includes Entra-joined, Hybrid-joined, registered, and compliant devices.

        Returns:
            {"success": true, "data": {"devices": [...], "count": N}}
        """
        from getset_pox_mcp.services.eid.eid_service import EID_listDevices
        return await safe_call(EID_listDevices)

    @mcp.tool()
    async def eid_get_device(device_id: str) -> dict:
        """
        Get a specific Entra ID device by its object ID.

        Args:
            device_id: The Entra ID object ID (GUID) of the device.

        Returns:
            {"success": true, "data": {"device": {...}}}
        """
        from getset_pox_mcp.services.eid.eid_service import EID_getDevice
        return await safe_call(EID_getDevice, device_id=device_id)

    @mcp.tool()
    async def eid_get_groups(top: int = 100) -> dict:
        """
        List all groups in the Entra ID tenant.

        Returns id, displayName, mail, description, and groupTypes for each group.

        Args:
            top: Maximum number of groups to return (1–999, default 100).

        Returns:
            {"success": true, "data": {"groups": [...], "count": N}}
        """
        from getset_pox_mcp.services.eid.eid_service import EID_getGroups
        return await safe_call(EID_getGroups, top=top)

    @mcp.tool()
    async def eid_get_group(group_id: str) -> dict:
        """
        Get a specific Entra ID group by its object ID.

        Args:
            group_id: The object ID (GUID) of the group.

        Returns:
            {"success": true, "data": {"group": {...}}}
        """
        from getset_pox_mcp.services.eid.eid_service import EID_getGroup
        return await safe_call(EID_getGroup, group_id=group_id)

    @mcp.tool()
    async def eid_get_group_members(group_id: str, top: int = 100) -> dict:
        """
        List the direct members of an Entra ID group.

        Returns id, displayName, mail, and userPrincipalName for each member.

        Args:
            group_id: The object ID (GUID) of the group.
            top:      Maximum number of members to return (1–999, default 100).

        Returns:
            {"success": true, "data": {"members": [...], "count": N, "group_id": "..."}}
        """
        from getset_pox_mcp.services.eid.eid_service import EID_getGroupMembers
        return await safe_call(EID_getGroupMembers, group_id=group_id, top=top)

    @mcp.tool()
    async def eid_search_groups(query: str, top: int = 50) -> dict:
        """
        Search Entra ID groups whose displayName starts with the query string.

        Args:
            query: Prefix to match against group displayName.
            top:   Maximum number of results to return (1–999, default 50).

        Returns:
            {"success": true, "data": {"groups": [...], "count": N, "query": "..."}}
        """
        from getset_pox_mcp.services.eid.eid_service import EID_searchGroups
        return await safe_call(EID_searchGroups, query=query, top=top)

    @mcp.tool()
    async def eid_create_security_group(
        group_name: str,
        description: Optional[str] = None,
        user_ids: Optional[List[str]] = None,
        group_ids: Optional[List[str]] = None,
        mail_enabled: bool = False,
        add_prefix: bool = False,
    ) -> dict:
        """
        Create a static-membership Entra ID security group, optionally with members.

        Creates the group then adds any supplied user or nested-group members.
        Suitable for access-control assignments, Conditional Access, Intune
        targeting, and Entitlement Management.

        Args:
            group_name:   Display name for the new group.
            description:  Human-readable description of the group's purpose.
            user_ids:     List of user object IDs (GUIDs) to add as members.
            group_ids:    List of group object IDs to nest inside the new group.
            mail_enabled: Set to true to create a mail-enabled security group.
            add_prefix:   Prepend "POC-" to the group name (useful for test tenants).

        Returns:
            {
              "success": true,
              "data": {
                "group": {"id": "...", "displayName": "...", ...},
                "members": {"users": {"added": N, "failed": M}, "groups": {...}}
              }
            }
        """
        from getset_pox_mcp.services.eid.eid_service import EID_createUserGroups
        return await safe_call(
            EID_createUserGroups,
            groupName=group_name,
            description=description,
            userIds=user_ids or [],
            groupIds=group_ids or [],
            mailEnabled=mail_enabled,
            addPrefix=add_prefix,
        )