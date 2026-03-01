"""
API endpoints for Xero OAuth and sync operations.

This module provides whitelisted endpoints that can be called from:
- ERPNext UI (buttons, forms)
- External webhooks (OAuth callbacks)
"""

from __future__ import annotations

import datetime as dt
from urllib.parse import urlencode
from typing import Any

import frappe
from frappe.utils import now_datetime

from erpnext_xero_app.xero_integration.xero_client import XeroClient


def _redirect_url(path: str) -> str:
    """Build redirect URL. When behind proxy (e.g. ngrok), use request host without backend port."""
    if getattr(frappe.local, "request", None) and getattr(frappe.local.request, "host", None):
        host = frappe.local.request.host
        if ":" not in host:
            proto = "https" if frappe.get_request_header("X-Forwarded-Proto") == "https" else "http"
            return f"{proto}://{host}{path}"
    return frappe.utils.get_url(path)


@frappe.whitelist(allow_guest=True)
def xero_oauth_callback(code: str | None = None, state: str | None = None) -> str:
    """
    OAuth callback handler for Xero.

    This endpoint should be set as the Redirect URI in your Xero app:
    https://your-site.frappe.cloud/api/method/erpnext_xero_app.xero_integration.api.xero_oauth_callback

    After user authorizes in Xero, Xero redirects here with a `code`.
    We exchange that code for access/refresh tokens and store them.
    Runs as Administrator so Guest (redirected from Xero) can complete the flow.
    """
    if not code:
        return """
        <html>
        <body>
            <h2>Xero OAuth Error</h2>
            <p>No authorization code received from Xero.</p>
            <p><a href="/app/xero-settings">Go to Xero Settings</a></p>
        </body>
        </html>
        """

    try:
        frappe.set_user("Administrator")
        settings = frappe.get_single("Xero Settings")

        client_secret = settings.get_password("client_secret") or ""
        if not settings.client_id or not client_secret:
            return """
            <html>
            <body>
                <h2>Xero OAuth Error</h2>
                <p>Client ID or Client Secret not configured in Xero Settings.</p>
                <p><a href="/app/xero-settings">Go to Xero Settings</a></p>
            </body>
            </html>
            """

        xero = XeroClient(
            client_id=settings.client_id or "",
            client_secret=client_secret,
            redirect_uri=settings.redirect_uri or "",
        )

        token_data = xero.exchange_code_for_token(code)

        # Store tokens in Xero Settings
        settings.access_token = token_data.get("access_token")
        settings.refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 1800)  # default 30 min
        settings.token_expires_at = now_datetime() + dt.timedelta(seconds=expires_in)

        # Determine tenant via Connections endpoint
        xero.access_token = token_data.get("access_token")
        xero.refresh_token = token_data.get("refresh_token")
        xero.token_expires_at = settings.token_expires_at
        conns = xero.get_connections()
        if conns:
            settings.tenant_id = conns[0].get("tenantId")

        settings.save(ignore_permissions=True)
        frappe.db.commit()

        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = _redirect_url("/app/xero-settings")

    except Exception as exc:
        frappe.log_error(
            f"Xero OAuth callback error: {exc}",
            "Xero OAuth Error",
        )
        return f"""
        <html>
        <body>
            <h2>Xero OAuth Error</h2>
            <p>Error: {exc}</p>
            <p><a href="/app/xero-settings">Go to Xero Settings</a></p>
        </body>
        </html>
        """


@frappe.whitelist()
def get_xero_auth_url() -> dict[str, Any]:
    """
    Generate the Xero authorization URL for OAuth flow.

    Called from a button in the UI to start the OAuth process.
    """
    settings = frappe.get_single("Xero Settings")

    if not settings.client_id or not settings.redirect_uri:
        frappe.throw("Please configure Client ID and Redirect URI in Xero Settings first.")

    scopes = ["accounting.contacts", "accounting.transactions", "offline_access"]
    query = urlencode(
        {
            "response_type": "code",
            "client_id": settings.client_id,
            "redirect_uri": settings.redirect_uri,
            "scope": " ".join(scopes),
            "state": "erpnext",
        }
    )
    auth_url = f"https://login.xero.com/identity/connect/authorize?{query}"

    return {
        "auth_url": auth_url,
        "message": "Click the link below to authorize with Xero:",
    }


__all__ = ["xero_oauth_callback", "get_xero_auth_url"]
