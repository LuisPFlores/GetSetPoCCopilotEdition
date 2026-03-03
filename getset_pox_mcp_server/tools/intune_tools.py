"""
Microsoft Intune tools — device management and app deployment.

Wraps the 7 functions in getset_pox_mcp.services.intune.intune_service and
exposes them as MCP tools for managing Intune-enrolled devices and deploying
the Global Secure Access Windows client.
"""

from typing import List, Optional
from mcp.server.fastmcp import FastMCP
from getset_pox_mcp_server.services_adapter import safe_call

def register_intune_tools(mcp: FastMCP) -> None:
    """Register all Intune tools on the FastMCP instance."""

    @mcp.tool()
    async def intune_list_managed_devices(top: int = 10) -> dict:
        """
        List managed devices enrolled in Microsoft Intune.

        Returns device name, OS, assigned user, and object ID for each device.

        Args:
            top: Number of devices to return (default: 10).

        Returns:
            {"success": true, "data": {"devices": [...], "count": N}}
        """
        from getset_pox_mcp.services.intune.intune_service import IN_listIntuneManagedDevices
        return await safe_call(IN_listIntuneManagedDevices, top=top)

    @mcp.tool()
    async def intune_get_device_details(device_id: str) -> dict:
        """
        Get detailed information about a specific Intune-managed device.

        Returns OS version, compliance state, enrollment date, last sync time,
        serial number, model, manufacturer, and assigned user.

        Args:
            device_id: The Intune managed device object ID (GUID).

        Returns:
            {"success": true, "data": {"device": {...}}}
        """
        from getset_pox_mcp.services.intune.intune_service import IN_getManagedDeviceDetails
        return await safe_call(IN_getManagedDeviceDetails, deviceId=device_id)

    @mcp.tool()
    async def intune_list_compliance_policies() -> dict:
        """
        List all device compliance policies configured in Microsoft Intune.

        Returns the display name, platform (Windows, iOS, Android, macOS),
        description, and object ID for each policy.

        Returns:
            {"success": true, "data": {"policies": [...], "count": N}}
        """
        from getset_pox_mcp.services.intune.intune_service import IN_listDeviceCompliancePolicies
        return await safe_call(IN_listDeviceCompliancePolicies)

    @mcp.tool()
    async def intune_list_config_profiles() -> dict:
        """
        List all device configuration profiles configured in Microsoft Intune.

        Returns the display name, platform, description, and object ID for
        each profile.

        Returns:
            {"success": true, "data": {"profiles": [...], "count": N}}
        """
        from getset_pox_mcp.services.intune.intune_service import IN_listDeviceConfigurationProfiles
        return await safe_call(IN_listDeviceConfigurationProfiles)

    @mcp.tool()
    async def intune_sync_device(device_id: str) -> dict:
        """
        Send a sync command to a specific Intune-managed device.

        The device will check in with Intune on its next polling cycle and
        apply any pending policies or app assignments.

        Args:
            device_id: The Intune managed device object ID (GUID).

        Returns:
            {"success": true, "data": {"deviceId": "...", "message": "Sync command sent"}}
        """
        from getset_pox_mcp.services.intune.intune_service import IN_syncManagedDevice
        return await safe_call(IN_syncManagedDevice, deviceId=device_id)

    @mcp.tool()
    async def intune_deploy_gsa_client(
        display_name: str = "Global Secure Access Client",
        description: str = "Microsoft Global Secure Access Windows client for secure network connectivity",
        publisher: str = "Microsoft",
        sas_url: Optional[str] = None,
    ) -> dict:
        """
        Download the Global Secure Access (GSA) Windows client installer and
        upload it to Microsoft Intune as a Win32 LOB application.

        Handles the complete multi-step deployment workflow:
          1. Download the .intunewin package from Azure Blob Storage.
          2. Create the Win32LobApp entry in Intune.
          3. Create a content version and file placeholder.
          4. Upload the encrypted installer to Azure Storage in chunks.
          5. Commit the upload and finalize the content version.

        After completion, assign the app to device groups using
        intune_assign_app_to_groups.

        Args:
            display_name: Display name shown in the Intune Company Portal
                          (default: "Global Secure Access Client").
            description:  App description shown to end users.
            publisher:    Publisher name (default: "Microsoft").
            sas_url:      Optional custom SAS URL to download the installer from.
                          Leave blank to use the default hosted package.

        Returns:
            {
              "success": true,
              "data": {
                "app_id": "...",
                "content_version_id": "...",
                "display_name": "..."
              }
            }
        """
        from getset_pox_mcp.services.intune.intune_service import IN_prepGSAWinClient
        return await safe_call(
            IN_prepGSAWinClient,
            displayName=display_name,
            description=description,
            publisher=publisher,
            sasUrl=sas_url,
        )

    @mcp.tool()
    async def intune_assign_app_to_groups(
        app_id: str,
        group_ids: List[str],
        intent: str = "required",
        notification_settings: str = "showAll",
        restart_grace_period: int = 1440,
        delivery_optimization_priority: str = "notConfigured",
    ) -> dict:
        """
        Assign an Intune Win32 application to one or more Entra ID device groups.

        Each group receives a separate assignment record with the specified
        deployment intent, notification, and restart settings.

        Args:
            app_id:        Object ID of the Win32 LOB app in Intune.
            group_ids:     List of Entra ID group object IDs to assign the app to.
            intent:        Deployment intent — "required" (mandatory install),
                           "available" (shown in Company Portal), or "uninstall".
            notification_settings:
                           "showAll" — show install and restart notifications,
                           "showReboot" — only restart notifications,
                           "hideAll" — silent install.
            restart_grace_period:
                           Minutes before forcing a device restart after install
                           (default: 1440 = 24 hours).
            delivery_optimization_priority:
                           "notConfigured" (default) or "foreground" for
                           prioritised download.

        Returns:
            {
              "success": true,
              "data": {
                "app": {"id": "...", "displayName": "..."},
                "assignment": {
                  "intent": "...",
                  "totalGroups": N,
                  "successfulAssignments": N,
                  "failedAssignments": 0
                },
                "assignments": [{"groupId": "...", "assignmentId": "..."}]
              }
            }
        """
        from getset_pox_mcp.services.intune.intune_service import IN_intuneAppAssignment
        return await safe_call(
            IN_intuneAppAssignment,
            appId=app_id,
            groupIds=group_ids,
            intent=intent,
            notificationSettings=notification_settings,
            restartGracePeriod=restart_grace_period,
            deliveryOptimizationPriority=delivery_optimization_priority,
        )