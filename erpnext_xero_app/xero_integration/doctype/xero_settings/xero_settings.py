from __future__ import annotations

import frappe
from frappe.model.document import Document

from erpnext_xero_app.xero_integration.xero_client import XeroClient


class XeroSettings(Document):
    """
    Single DocType used to store Xero credentials and sync options.

    Users can manage credentials via the ERPNext UI (no config file),
    and use actions to connect/test/sync.
    """

    def get_xero_client(self) -> XeroClient:
        """Build a XeroClient from stored settings."""
        client_secret = self.get_password("client_secret") or ""
        access_token = self.get_password("access_token") if self.access_token else None
        refresh_token = self.get_password("refresh_token") if self.refresh_token else None

        return XeroClient(
            client_id=self.client_id or "",
            client_secret=client_secret,
            redirect_uri=self.redirect_uri or "",
            tenant_id=self.tenant_id or None,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=self.token_expires_at or None,
        )


@frappe.whitelist()
def test_connection() -> dict:
    """
    Called from a button in the UI to verify that:
    - Client ID / Secret are present
    - Access Token / Tenant ID allow a simple API call
    """
    settings = frappe.get_single("Xero Settings")
    client = settings.get_xero_client()

    try:
        # Ensure token is valid (refresh if needed)
        if client.access_token:
            before_access = client.access_token
            before_refresh = client.refresh_token
            before_exp = client.token_expires_at
            client.ensure_valid_token()
            if (
                client.access_token != before_access
                or client.refresh_token != before_refresh
                or client.token_expires_at != before_exp
            ):
                settings.access_token = client.access_token
                settings.refresh_token = client.refresh_token
                settings.token_expires_at = client.token_expires_at
                settings.save(ignore_permissions=True)
                frappe.db.commit()

        # Discover tenant via Connections endpoint if missing
        if not client.tenant_id:
            conns = client.get_connections()
            if not conns:
                raise RuntimeError("No Xero connections found for this access token.")
            client.tenant_id = conns[0].get("tenantId")
            settings.tenant_id = client.tenant_id
            settings.save(ignore_permissions=True)
            frappe.db.commit()

        # Lightweight ping: list contacts (may be 0)
        contacts = client.list_contacts(since=None)
        ok = True
        message = f"Connection OK. Tenant linked. Retrieved {len(contacts)} contacts (or 0 if empty)."
    except Exception as exc:  # pragma: no cover - runtime only
        ok = False
        message = f"Connection failed: {exc}"

    return {"ok": ok, "message": message}


@frappe.whitelist()
def sync_customers_now() -> dict:
    """
    Trigger customer sync (ERPNext → Xero) from the ERPNext UI.
    Runs synchronously so the user sees the result immediately.
    """
    from erpnext_xero_app.xero_integration.sync import create_log, _run_customers_to_xero

    log_name = create_log(entity="Customers", direction="ERPNext → Xero")
    _run_customers_to_xero(log_name=log_name)
    return {"ok": True, "message": f"Customer sync completed. Log: {log_name}", "log": log_name}


@frappe.whitelist()
def sync_invoices_now() -> dict:
    """
    Trigger invoice sync (ERPNext → Xero) from the ERPNext UI.
    Runs synchronously so the user sees the result immediately.
    """
    from erpnext_xero_app.xero_integration.sync import create_log, _run_invoices_to_xero

    log_name = create_log(entity="Invoices", direction="ERPNext → Xero")
    _run_invoices_to_xero(log_name=log_name)
    return {"ok": True, "message": f"Invoice sync completed. Log: {log_name}", "log": log_name}


@frappe.whitelist()
def sync_customers_from_xero_now() -> dict:
    """Trigger customer sync (Xero → ERPNext).
    Runs synchronously so the user sees the result immediately.
    """
    from erpnext_xero_app.xero_integration.sync import create_log, _run_customers_from_xero

    log_name = create_log(entity="Customers", direction="Xero → ERPNext")
    _run_customers_from_xero(log_name=log_name)
    return {"ok": True, "message": f"Customer import completed. Log: {log_name}", "log": log_name}


@frappe.whitelist()
def sync_invoices_from_xero_now() -> dict:
    """Trigger invoice sync (Xero → ERPNext).
    Runs synchronously so the user sees the result immediately.
    """
    from erpnext_xero_app.xero_integration.sync import create_log, _run_invoices_from_xero

    log_name = create_log(entity="Invoices", direction="Xero → ERPNext")
    _run_invoices_from_xero(log_name=log_name)
    return {"ok": True, "message": f"Invoice import completed. Log: {log_name}", "log": log_name}

