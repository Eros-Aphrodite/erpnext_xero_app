from __future__ import annotations

"""
Xero API client used by the Frappe app.

Supports:
- OAuth2 code exchange + refresh token flow
- Connections (tenant discovery)
- Contacts + Invoices endpoints (requires tenant header)
"""

import datetime as dt
import logging
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class XeroAuthError(RuntimeError):
    pass


class XeroClient:
    BASE_URL = "https://api.xero.com/api.xro/2.0"
    CONNECTIONS_URL = "https://api.xero.com/connections"
    TOKEN_URL = "https://identity.xero.com/connect/token"

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        tenant_id: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        token_expires_at: dt.datetime | None = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.tenant_id = tenant_id
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expires_at = token_expires_at
        self._session = requests.Session()

    # ---------------- OAuth ----------------

    def exchange_code_for_token(self, code: str) -> dict[str, Any]:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        resp = self._session.post(
            self.TOKEN_URL, data=data, auth=(self.client_id, self.client_secret), timeout=30
        )
        if not resp.ok:
            raise XeroAuthError(resp.text)
        return resp.json()

    def refresh_access_token(self) -> dict[str, Any]:
        if not self.refresh_token:
            raise XeroAuthError("Missing refresh token.")
        data = {"grant_type": "refresh_token", "refresh_token": self.refresh_token}
        resp = self._session.post(
            self.TOKEN_URL, data=data, auth=(self.client_id, self.client_secret), timeout=30
        )
        if not resp.ok:
            raise XeroAuthError(resp.text)
        return resp.json()

    def ensure_valid_token(self, *, refresh_skew_seconds: int = 120) -> None:
        """
        Ensure access_token is present and not expired.
        If expired (or close), refresh it.

        Caller is responsible for persisting updated tokens.
        """
        if not self.access_token:
            raise XeroAuthError("Missing access token. Connect to Xero first.")

        if not self.token_expires_at:
            return

        now = dt.datetime.utcnow()
        if self.token_expires_at.tzinfo is not None:
            now = dt.datetime.now(dt.timezone.utc)

        if self.token_expires_at <= now + dt.timedelta(seconds=refresh_skew_seconds):
            token_data = self.refresh_access_token()
            self.access_token = token_data.get("access_token")
            # refresh_token can rotate
            self.refresh_token = token_data.get("refresh_token") or self.refresh_token
            expires_in = int(token_data.get("expires_in") or 1800)
            self.token_expires_at = now + dt.timedelta(seconds=expires_in)

    # ---------------- headers/helpers ----------------

    def _auth_headers(self) -> Dict[str, str]:
        if not self.access_token:
            raise XeroAuthError("Missing access token.")
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }

    def _tenant_headers(self) -> Dict[str, str]:
        if not self.tenant_id:
            raise XeroAuthError("Missing tenant id. Fetch connections first.")
        h = self._auth_headers()
        h["Xero-tenant-id"] = self.tenant_id
        h["Content-Type"] = "application/json"
        return h

    def get_connections(self) -> List[Dict[str, Any]]:
        """
        Returns list of connections. Each item contains `tenantId`.
        """
        self.ensure_valid_token()
        resp = self._session.get(self.CONNECTIONS_URL, headers=self._auth_headers(), timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.ensure_valid_token()
        url = f"{self.BASE_URL}/{path.lstrip('/')}"
        resp = self._session.get(url, headers=self._tenant_headers(), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.ensure_valid_token()
        url = f"{self.BASE_URL}/{path.lstrip('/')}"
        resp = self._session.post(url, headers=self._tenant_headers(), json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()

    # ---------------- Contacts ----------------

    def list_contacts(self, since: Optional[dt.datetime] = None) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {}
        if since:
            params["where"] = f"UpdatedDateUTC>DateTime({since.strftime('%Y,%m,%d')})"
        data = self._get("Contacts", params=params)
        return data.get("Contacts", [])

    def upsert_contact(self, contact: Dict[str, Any]) -> Dict[str, Any]:
        payload = {"Contacts": [contact]}
        data = self._post("Contacts", payload)
        contacts = data.get("Contacts", [])
        return contacts[0] if contacts else {}

    # ---------------- Invoices ----------------

    def list_invoices(self, since: Optional[dt.datetime] = None) -> List[Dict[str, Any]]:
        where = 'Type=="ACCREC"'
        if since:
            where += f"&&UpdatedDateUTC>DateTime({since.strftime('%Y,%m,%d')})"
        data = self._get("Invoices", params={"where": where})
        return data.get("Invoices", [])

    def upsert_invoice(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        payload = {"Invoices": [invoice]}
        data = self._post("Invoices", payload)
        invoices = data.get("Invoices", [])
        return invoices[0] if invoices else {}


__all__ = ["XeroClient", "XeroAuthError"]


