"""
Services Adapter — bridges MS_GRAPH_* credentials to the existing
getset_pox_mcp service layer and normalises all service responses into
a stable JSON shape consumed by every MCP tool.

Auth bridge
-----------
The upstream services (eid_service, iga_service, etc.) authenticate via
``getset_pox_mcp.authentication.middleware.get_auth_middleware()``, which
reads ``ENTRA_*`` environment variables.  This module copies the
``MS_GRAPH_*`` variables into the corresponding ``ENTRA_*`` slots *before*
those modules are imported, so the existing auth machinery works without
modification.

Response normalisation
----------------------
Every tool returns one of two shapes:

Success::

    {
        "success": true,
        "data": { ... }          # raw service payload
    }

Failure::

    {
        "success": false,
        "error": {
            "code":    "SERVICE_ERROR",
            "message": "...",
            "details": { ... }   # raw error payload for diagnostics
        }
    }
"""

import os
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Auth bridge: map MS_GRAPH_* → ENTRA_* so existing middleware works
# ---------------------------------------------------------------------------

def _init_entra_env() -> None:
    """
    Copy MS_GRAPH_* credentials into ENTRA_* env vars (only if not already set)
    so that ``getset_pox_mcp.authentication.middleware`` picks them up.
    """
    mapping = {
        "MS_GRAPH_TENANT_ID": "ENTRA_TENANT_ID",
        "MS_GRAPH_CLIENT_ID": "ENTRA_CLIENT_ID",
        "MS_GRAPH_CLIENT_SECRET": "ENTRA_CLIENT_SECRET",
    }
    for ms_key, entra_key in mapping.items():
        val = os.environ.get(ms_key)
        if val and not os.environ.get(entra_key):
            os.environ[entra_key] = val
            logger.debug("Bridged %s → %s", ms_key, entra_key)

    # Ensure application-mode auth is activated
    if not os.environ.get("ENTRA_ENABLE_AUTH"):
        os.environ["ENTRA_ENABLE_AUTH"] = "true"
    if not os.environ.get("ENTRA_AUTH_MODE"):
        os.environ["ENTRA_AUTH_MODE"] = "application"


# Run the bridge immediately so that any subsequent import of the upstream
# services finds the ENTRA_* vars already in place.
_init_entra_env()


# ---------------------------------------------------------------------------
# Response normalisation helpers
# ---------------------------------------------------------------------------

def normalize_response(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a raw service dict into the canonical ``{success, data/error}`` shape.

    The upstream services use ``status: "success" | "error" | "partial" | …``.
    This function maps every non-error variant to ``success: true``.

    Args:
        result: Raw dict returned by any upstream service function.

    Returns:
        Normalised dict with ``success`` (bool) plus either ``data`` or ``error``.
    """
    status = result.get("status", "")
    if status in ("success", "already_set", "partial"):
        return {"success": True, "data": result}
    if status in ("error", "not_found"):
        return {
            "success": False,
            "error": {
                "code": "SERVICE_ERROR",
                "message": result.get("message", "An error occurred"),
                "details": result,
            },
        }
    # Unknown / missing status — treat as success and pass through
    return {"success": True, "data": result}


def error_response(code: str, message: str, details: Any = None) -> Dict[str, Any]:
    """
    Build a structured error response for validation failures or unexpected
    exceptions that occur *before* calling the underlying service.

    Args:
        code:    Short upper-case error code (e.g. ``"MISSING_PARAMETER"``).
        message: Human-readable description of the error.
        details: Optional extra context (exception string, partial result, etc.).

    Returns:
        Normalised error dict.
    """
    payload: Dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        payload["details"] = details
    return {"success": False, "error": payload}


async def safe_call(service_fn, **kwargs) -> Dict[str, Any]:
    """
    Await a service coroutine and convert any unhandled exception into a
    structured error response.

    Args:
        service_fn: An async callable from one of the upstream service modules.
        **kwargs:   Arguments forwarded to the service function.

    Returns:
        Normalised ``{success, data/error}`` dict.
    """
    try:
        result = await service_fn(**kwargs)
        return normalize_response(result)
    except Exception as exc:  # pragma: no cover
        logger.exception("Unhandled exception in service call %s", getattr(service_fn, "__name__", "?"))
        return error_response(
            code="UNEXPECTED_ERROR",
            message=str(exc),
            details={"service": getattr(service_fn, "__name__", str(service_fn))},
        )