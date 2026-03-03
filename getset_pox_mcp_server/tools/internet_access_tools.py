"""
Internet Access / Global Secure Access (GSA) tools.

Wraps the 8 functions in getset_pox_mcp.services.internetAccess.internetAccess_service
and exposes them as MCP tools for managing Global Secure Access web content
filtering, forwarding profiles, TLS inspection, and Conditional Access.
"""

from typing import List, Optional
from mcp.server.fastmcp import FastMCP
from getset_pox_mcp_server.services_adapter import safe_call

def register_internet_access_tools(mcp: FastMCP) -> None:
    """Register all Internet Access / GSA tools on the FastMCP instance."""

    @mcp.tool()
    async def ia_check_forwarding_profile() -> dict:
        """
        Check whether the Global Secure Access Internet Access forwarding profile exists
        and report its current state (enabled / disabled).

        Returns:
            {
              "success": true,
              "data": {"name": "...", "state": "enabled|disabled", "id": "..."}
            }
        """
        from getset_pox_mcp.services.internetAccess.internetAccess_service import (
            IA_checkInternetAccessForwardingProfile,
        )
        return await safe_call(IA_checkInternetAccessForwardingProfile)

    @mcp.tool()
    async def ia_enable_forwarding_profile(
        forwarding_profile_id: str,
        state: str = "enabled",
    ) -> dict:
        """
        Enable or disable the Global Secure Access Internet Access forwarding profile.

        Args:
            forwarding_profile_id: Object ID of the Internet Access forwarding profile.
            state:                 Target state — "enabled" (default) or "disabled".

        Returns:
            {"success": true, "data": {"name": "...", "id": "...", "message": "..."}}
        """
        from getset_pox_mcp.services.internetAccess.internetAccess_service import (
            IA_enableInternetAccessForwardingProfile,
        )
        return await safe_call(
            IA_enableInternetAccessForwardingProfile,
            forwarding_profile_id=forwarding_profile_id,
            state=state,
        )

    @mcp.tool()
    async def ia_create_filtering_policy(
        name: str = "POC-Monitor AI Access",
        description: str = "Monitor access to AI",
        web_categories: Optional[List[str]] = None,
    ) -> dict:
        """
        Create a Global Secure Access web content filtering policy for one or more
        web categories.

        The policy uses action "allow" and logs traffic to the specified
        categories.  Common category values include "ArtificialIntelligence",
        "SocialNetworking", "Gambling", "AdultContent".

        Args:
            name:           Display name for the new filtering policy.
            description:    Human-readable description of the policy purpose.
            web_categories: List of web category names to target
                            (default: ["ArtificialIntelligence"]).

        Returns:
            {"success": true, "data": {"policy_name": "...", "policy_id": "..."}}
        """
        from getset_pox_mcp.services.internetAccess.internetAccess_service import (
            IA_createFilteringPolicy,
        )
        return await safe_call(
            IA_createFilteringPolicy,
            name=name,
            description=description,
            webCategories=web_categories or ["ArtificialIntelligence"],
        )

    @mcp.tool()
    async def ia_create_filtering_profile(
        name: str = "POC-Monitor AI Access Profile",
        description: str = "Profile for monitoring AI access",
        state: str = "enabled",
        priority: int = 1000,
    ) -> dict:
        """
        Create a Global Secure Access filtering profile that acts as a container
        for one or more filtering policies.

        Filtering profiles are then referenced in Conditional Access policies
        to apply web content filtering to specific users or groups.

        Args:
            name:        Display name for the filtering profile.
            description: Human-readable description of the profile.
            state:       "enabled" (default) or "disabled".
            priority:    Evaluation priority — lower number = higher priority
                         (default: 1000).

        Returns:
            {"success": true, "data": {"profile_name": "...", "profile_id": "..."}}
        """
        from getset_pox_mcp.services.internetAccess.internetAccess_service import (
            IA_createFilteringProfile,
        )
        return await safe_call(
            IA_createFilteringProfile,
            name=name,
            description=description,
            state=state,
            priority=priority,
        )

    @mcp.tool()
    async def ia_link_policy_to_profile(
        filtering_profile_id: str,
        filtering_policy_id: str,
        priority: int = 1000,
    ) -> dict:
        """
        Link a web content filtering policy to an existing filtering profile.

        After linking, the profile enforces the policy's rules for users
        targeted by Conditional Access policies that reference this profile.

        Args:
            filtering_profile_id: Object ID of the filtering profile.
            filtering_policy_id:  Object ID of the filtering policy to attach.
            priority:             Link evaluation priority (default: 1000).

        Returns:
            {
              "success": true,
              "data": {
                "profile_id": "...",
                "policy_id": "...",
                "link_id": "..."
              }
            }
        """
        from getset_pox_mcp.services.internetAccess.internetAccess_service import (
            IA_linkPolicyToFilteringProfile,
        )
        return await safe_call(
            IA_linkPolicyToFilteringProfile,
            filtering_profile_id=filtering_profile_id,
            filtering_policy_id=filtering_policy_id,
            priority=priority,
        )

    @mcp.tool()
    async def ia_create_conditional_access_policy(
        filtering_profile_id: str,
        display_name: str = "POC-Monitor AI conditional access policy",
        include_users: Optional[List[str]] = None,
        include_groups: Optional[List[str]] = None,
        include_applications: Optional[List[str]] = None,
    ) -> dict:
        """
        Create a Conditional Access policy that applies a GSA filtering profile
        to the specified users or groups.

        The policy is created in report-only mode
        (enabledForReportingButNotEnforced) so it can be reviewed before
        enforcement.

        Args:
            filtering_profile_id:  Object ID of the GSA filtering profile to apply.
            display_name:          Display name for the Conditional Access policy.
            include_users:         List of user object IDs to include
                                   (default: ["None"] — no individual users).
            include_groups:        List of group object IDs to include.
            include_applications:  List of application IDs to scope the policy to
                                   (defaults to the two GSA service principals).

        Returns:
            {"success": true, "data": {"policy_name": "...", "policy_id": "..."}}
        """
        from getset_pox_mcp.services.internetAccess.internetAccess_service import (
            IA_createConditionalAccessPolicy,
        )
        return await safe_call(
            IA_createConditionalAccessPolicy,
            filtering_profile_id=filtering_profile_id,
            displayName=display_name,
            includeUsers=include_users,
            includeGroups=include_groups,
            includeApplications=include_applications,
        )

    @mcp.tool()
    async def ia_tls_onboarding(
        name: str = "POCEntCA",
        common_name: str = "POCRoot",
        organization_name: str = "POCLtd",
        cert_output_dir: str = "./certs",
        max_retries: int = 5,
    ) -> dict:
        """
        Automate the complete TLS inspection onboarding workflow for
        Global Secure Access.

        Orchestrates four steps with exponential-backoff retry logic:
          1. Generate a Certificate Signing Request (CSR) via Graph API.
          2. Sign the CSR with a self-signed Root CA.
          3. Upload the signed certificate to Graph API.
          4. Save the Root CA certificate locally for device deployment.

        IMPORTANT: After this tool completes, deploy the Root CA certificate
        (rootCA.pem / rootCA.cer) to client devices via Intune, GPO, or SCCM
        before TLS inspection will function.

        Args:
            name:              Certificate name — max 12 alphanumeric characters.
            common_name:       Certificate common name — max 12 chars (spaces allowed).
            organization_name: Organisation name — max 12 alphanumeric characters.
            cert_output_dir:   Local directory where Root CA files will be saved
                               (default: "./certs").
            max_retries:       Maximum retry attempts per step (default: 5).

        Returns:
            {
              "success": true,
              "data": {
                "csr_generation": {...},
                "signing_upload": {...},
                "root_ca_download": {"files_created": {...}},
                "retry_metrics": {...},
                "workflow_log": [...]
              }
            }
        """
        from getset_pox_mcp.services.internetAccess.internetAccess_service import IA_TLSPOCV2
        return await safe_call(
            IA_TLSPOCV2,
            name=name,
            commonName=common_name,
            organizationName=organization_name,
            cert_output_dir=cert_output_dir,
            max_retries=max_retries,
        )

    @mcp.tool()
    async def ia_internet_access_poc(
        forwarding_profile_id: str,
        filtering_policy_name: str = "POC-Monitor AI Access",
        filtering_policy_description: str = "Monitor access to AI",
        filtering_profile_name: str = "POC-Monitor AI Access Profile",
        filtering_profile_description: str = "Profile for monitoring AI access",
        filtering_profile_state: str = "enabled",
        filtering_profile_priority: int = 1000,
        link_priority: int = 1000,
        create_ca_policy: bool = True,
        ca_policy_display_name: str = "POC-Monitor AI conditional access policy",
        ca_policy_include_users: Optional[List[str]] = None,
        ca_policy_include_groups: Optional[List[str]] = None,
        ca_policy_include_applications: Optional[List[str]] = None,
    ) -> dict:
        """
        Run a complete end-to-end Internet Access web content filtering POC in one call.

        Chains five steps automatically:
          1. Enable the Internet Access forwarding profile.
          2. Create a web content filtering policy.
          3. Create a filtering profile.
          4. Link the policy to the profile.
          5. (Optional) Create a report-only Conditional Access policy.

        Use this tool to stand up a fully working Internet Access POC
        environment from scratch with a single action.

        Args:
            forwarding_profile_id:         ID of the Internet Access forwarding profile.
            filtering_policy_name:         Name for the new filtering policy.
            filtering_policy_description:  Description for the filtering policy.
            filtering_profile_name:        Name for the new filtering profile.
            filtering_profile_description: Description for the filtering profile.
            filtering_profile_state:       "enabled" or "disabled" (default: "enabled").
            filtering_profile_priority:    Priority for the filtering profile (default: 1000).
            link_priority:                 Priority for the policy-to-profile link.
            create_ca_policy:              Create a Conditional Access policy (default: true).
            ca_policy_display_name:        Display name for the CA policy.
            ca_policy_include_users:       User IDs for the CA policy scope.
            ca_policy_include_groups:      Group IDs for the CA policy scope.
            ca_policy_include_applications: Application IDs for the CA policy scope.

        Returns:
            {"success": true, "data": {"steps": [...], "summary": "..."}}
        """
        from getset_pox_mcp.services.internetAccess.internetAccess_service import (
            IA_internetAccessPoc,
        )
        return await safe_call(
            IA_internetAccessPoc,
            forwarding_profile_id=forwarding_profile_id,
            filtering_policy_name=filtering_policy_name,
            filtering_policy_description=filtering_policy_description,
            filtering_profile_name=filtering_profile_name,
            filtering_profile_description=filtering_profile_description,
            filtering_profile_state=filtering_profile_state,
            filtering_profile_priority=filtering_profile_priority,
            link_priority=link_priority,
            create_ca_policy=create_ca_policy,
            ca_policy_display_name=ca_policy_display_name,
            ca_policy_include_users=ca_policy_include_users,
            ca_policy_include_groups=ca_policy_include_groups,
            ca_policy_include_applications=ca_policy_include_applications,
        )