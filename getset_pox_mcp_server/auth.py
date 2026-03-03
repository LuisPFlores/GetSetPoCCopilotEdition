"""
Microsoft Graph Authentication — Client Credentials Flow.

Reads MS_GRAPH_CLIENT_ID, MS_GRAPH_CLIENT_SECRET, and MS_GRAPH_TENANT_ID
from environment variables and acquires Bearer tokens via MSAL's
ConfidentialClientApplication (daemon / application permission flow).

The MSAL app instance is created lazily on first use so that importing
this module does not fail when the env vars are absent (e.g. during tests).
"""

import os
from typing import Optional
import msal

SCOPES = ["https://graph.microsoft.com/.default"]

_app: Optional[msal.ConfidentialClientApplication] = None


def _get_app() -> msal.ConfidentialClientApplication:
    """Return the singleton MSAL ConfidentialClientApplication, creating it on first call."""
    global _app
    if _app is None:
        tenant_id = os.environ["MS_GRAPH_TENANT_ID"]
        client_id = os.environ["MS_GRAPH_CLIENT_ID"]
        client_secret = os.environ["MS_GRAPH_CLIENT_SECRET"]
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        _app = msal.ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=authority,
        )
    return _app


def get_graph_token() -> str:
    """
    Acquire a Microsoft Graph access token using client credentials.

    Uses MSAL's built-in token cache — a cached token is returned for
    successive calls within its validity window, avoiding redundant
    network round-trips.

    Returns:
        A valid Bearer access token string.

    Raises:
        RuntimeError: When MSAL returns an error instead of a token.
        KeyError: When MS_GRAPH_* environment variables are not set.
    """
    result = _get_app().acquire_token_for_client(scopes=SCOPES)
    if "access_token" not in result:
        raise RuntimeError(
            f"MS Graph token error: {result.get('error')}: "
            f"{result.get('error_description')}"
        )
    return result["access_token"]


def reset_app() -> None:
    """
    Clear the cached MSAL application instance.

    Useful in tests or when credentials are rotated at runtime.
    """
    global _app
    _app = None