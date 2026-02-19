from __future__ import annotations

import datetime as dt
from typing import Any, Dict

import frappe
from frappe.utils import now_datetime

from erpnext_xero_app.xero_integration.doctype.xero_mapping.xero_mapping import (
    get_erpnext_name_by_xero_id,
    get_xero_id,
    set_mapping,
)
from erpnext_xero_app.xero_integration.doctype.xero_sync_log.xero_sync_log import create_log
from erpnext_xero_app.xero_integration.xero_client import XeroClient


def _get_settings():
    return frappe.get_single("Xero Settings")


def _get_xero_client(settings) -> XeroClient:
    client_secret = settings.get_password("client_secret") or ""
    access_token = settings.get_password("access_token") if settings.access_token else None
    refresh_token = settings.get_password("refresh_token") if settings.refresh_token else None

    client = XeroClient(
        client_id=settings.client_id or "",
        client_secret=client_secret,
        redirect_uri=settings.redirect_uri or "",
        tenant_id=settings.tenant_id or None,
        access_token=access_token,
        refresh_token=refresh_token,
        token_expires_at=settings.token_expires_at or None,
    )

    # Refresh token if needed, then persist to settings if changed
    before_access = client.access_token
    before_refresh = client.refresh_token
    before_exp = client.token_expires_at

    if client.access_token:
        client.ensure_valid_token()

    changed = (
        client.access_token != before_access
        or client.refresh_token != before_refresh
        or client.token_expires_at != before_exp
    )
    if changed:
        settings.access_token = client.access_token
        settings.refresh_token = client.refresh_token
        settings.token_expires_at = client.token_expires_at
        settings.save(ignore_permissions=True)
        frappe.db.commit()

    # Ensure tenant
    if not client.tenant_id and client.access_token:
        conns = client.get_connections()
        if conns:
            client.tenant_id = conns[0].get("tenantId")
            settings.tenant_id = client.tenant_id
            settings.save(ignore_permissions=True)
            frappe.db.commit()

    return client


def _customer_to_xero_payload(customer: Dict[str, Any]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "Name": customer.get("customer_name") or customer.get("name"),
        "EmailAddress": customer.get("email_id"),
        "Phones": [],
    }
    phone = customer.get("mobile_no") or customer.get("phone")
    if phone:
        payload["Phones"].append({"PhoneType": "DEFAULT", "PhoneNumber": phone[:50]})
    return payload


def _xero_contact_to_customer_values(settings, contact: Dict[str, Any]) -> Dict[str, Any]:
    vals: Dict[str, Any] = {
        "customer_name": contact.get("Name"),
        "customer_type": "Company",
        "customer_group": settings.default_customer_group or "All Customer Groups",
        "territory": settings.default_territory or "All Territories",
        "email_id": contact.get("EmailAddress"),
    }
    phones = contact.get("Phones") or []
    if phones:
        vals["mobile_no"] = phones[0].get("PhoneNumber")
    return vals


# ---------------- enqueue wrappers ----------------


@frappe.whitelist()
def enqueue_customers_to_xero() -> str:
    log_name = create_log(entity="Customers", direction="ERPNext → Xero")
    frappe.enqueue(
        "erpnext_xero_app.xero_integration.sync._run_customers_to_xero",
        queue="long",
        log_name=log_name,
    )
    return log_name


@frappe.whitelist()
def enqueue_customers_from_xero() -> str:
    log_name = create_log(entity="Customers", direction="Xero → ERPNext")
    frappe.enqueue(
        "erpnext_xero_app.xero_integration.sync._run_customers_from_xero",
        queue="long",
        log_name=log_name,
    )
    return log_name


@frappe.whitelist()
def enqueue_invoices_to_xero() -> str:
    log_name = create_log(entity="Invoices", direction="ERPNext → Xero")
    frappe.enqueue(
        "erpnext_xero_app.xero_integration.sync._run_invoices_to_xero",
        queue="long",
        log_name=log_name,
    )
    return log_name


@frappe.whitelist()
def enqueue_invoices_from_xero() -> str:
    log_name = create_log(entity="Invoices", direction="Xero → ERPNext")
    frappe.enqueue(
        "erpnext_xero_app.xero_integration.sync._run_invoices_from_xero",
        queue="long",
        log_name=log_name,
    )
    return log_name


# ---------------- sync implementations ----------------


def _run_customers_to_xero(log_name: str) -> None:
    settings = _get_settings()
    log = frappe.get_doc("Xero Sync Log", log_name)
    log.mark_running()
    try:
        if not settings.sync_customers_to_xero:
            log.mark_success(message="Disabled (sync_customers_to_xero is off).")
            return

        client = _get_xero_client(settings)
        last = settings.last_customers_to_xero_sync_at
        filters = {"modified": (">", last)} if last else {}

        customers = frappe.get_all(
            "Customer",
            filters=filters,
            fields=["name", "customer_name", "email_id", "mobile_no", "phone", "modified"],
            limit_page_length=500,
            order_by="modified asc",
        )

        processed = 0
        for c in customers:
            erp_name = c["name"]
            xero_id = get_xero_id("Customer", erp_name)
            payload = _customer_to_xero_payload(c)
            if xero_id:
                payload["ContactID"] = xero_id

            created = client.upsert_contact(payload)
            new_id = created.get("ContactID")
            if new_id:
                set_mapping(
                    erpnext_doctype="Customer",
                    erpnext_name=erp_name,
                    xero_object="Contact",
                    xero_id=new_id,
                )
                processed += 1

        settings.last_customers_to_xero_sync_at = now_datetime()
        settings.save(ignore_permissions=True)
        frappe.db.commit()

        log.mark_success(message="Customers synced to Xero.", records_processed=processed)
    except Exception as exc:
        log.mark_failed(error=str(exc))
        raise


def _run_customers_from_xero(log_name: str) -> None:
    settings = _get_settings()
    log = frappe.get_doc("Xero Sync Log", log_name)
    log.mark_running()
    try:
        if not settings.sync_customers_from_xero:
            log.mark_success(message="Disabled (sync_customers_from_xero is off).")
            return

        client = _get_xero_client(settings)
        since_dt = settings.last_customers_from_xero_sync_at or None
        contacts = client.list_contacts(since=since_dt)

        processed = 0
        for c in contacts:
            xero_id = c.get("ContactID")
            if not xero_id:
                continue

            existing_customer = get_erpnext_name_by_xero_id(xero_id, "Customer")
            vals = _xero_contact_to_customer_values(settings, c)

            if existing_customer:
                doc = frappe.get_doc("Customer", existing_customer)
                doc.update(vals)
                doc.save(ignore_permissions=True)
                erp_name = doc.name
            else:
                doc = frappe.get_doc({"doctype": "Customer", **vals})
                doc.insert(ignore_permissions=True)
                erp_name = doc.name

            set_mapping(
                erpnext_doctype="Customer",
                erpnext_name=erp_name,
                xero_object="Contact",
                xero_id=xero_id,
            )
            processed += 1

        settings.last_customers_from_xero_sync_at = now_datetime()
        settings.save(ignore_permissions=True)
        frappe.db.commit()

        log.mark_success(message="Customers synced from Xero.", records_processed=processed)
    except Exception as exc:
        log.mark_failed(error=str(exc))
        raise


def _sales_invoice_to_xero_payload(settings, si_doc, xero_contact_id: str) -> Dict[str, Any]:
    account_code = settings.xero_sales_account_code
    if not account_code:
        raise RuntimeError("Please set Xero Sales Account Code in Xero Settings.")

    payload: Dict[str, Any] = {
        "Type": "ACCREC",
        "Contact": {"ContactID": xero_contact_id},
        "Date": str(si_doc.posting_date),
        "DueDate": str(si_doc.due_date) if si_doc.due_date else None,
        "InvoiceNumber": si_doc.name,
        "Status": "AUTHORISED" if si_doc.docstatus == 1 else "DRAFT",
        "LineItems": [],
    }

    for item in si_doc.items:
        line = {
            "Description": item.description or item.item_name or item.item_code,
            "Quantity": float(item.qty or 0),
            "UnitAmount": float(item.rate or 0),
            "AccountCode": str(account_code),
        }
        if settings.xero_tax_type:
            line["TaxType"] = settings.xero_tax_type
        payload["LineItems"].append(line)

    return payload


def _run_invoices_to_xero(log_name: str) -> None:
    settings = _get_settings()
    log = frappe.get_doc("Xero Sync Log", log_name)
    log.mark_running()
    try:
        if not settings.sync_invoices_to_xero:
            log.mark_success(message="Disabled (sync_invoices_to_xero is off).")
            return

        client = _get_xero_client(settings)
        last = settings.last_invoices_to_xero_sync_at
        filters = {"docstatus": 1, "modified": (">", last)} if last else {"docstatus": 1}

        invoices = frappe.get_all(
            "Sales Invoice",
            filters=filters,
            fields=["name", "customer", "posting_date", "due_date", "modified"],
            limit_page_length=200,
            order_by="modified asc",
        )

        processed = 0
        for inv in invoices:
            si_name = inv["name"]
            si = frappe.get_doc("Sales Invoice", si_name)

            customer_name = si.customer
            xero_contact_id = get_xero_id("Customer", customer_name)
            if not xero_contact_id:
                customer = frappe.get_doc("Customer", customer_name)
                contact_payload = _customer_to_xero_payload(customer.as_dict())
                created_contact = client.upsert_contact(contact_payload)
                xero_contact_id = created_contact.get("ContactID")
                if xero_contact_id:
                    set_mapping(
                        erpnext_doctype="Customer",
                        erpnext_name=customer_name,
                        xero_object="Contact",
                        xero_id=xero_contact_id,
                    )

            if not xero_contact_id:
                continue

            xero_invoice_id = get_xero_id("Sales Invoice", si_name)
            payload = _sales_invoice_to_xero_payload(settings, si, xero_contact_id)
            if xero_invoice_id:
                payload["InvoiceID"] = xero_invoice_id

            created = client.upsert_invoice(payload)
            new_id = created.get("InvoiceID")
            if new_id:
                set_mapping(
                    erpnext_doctype="Sales Invoice",
                    erpnext_name=si_name,
                    xero_object="Invoice",
                    xero_id=new_id,
                )
                processed += 1

        settings.last_invoices_to_xero_sync_at = now_datetime()
        settings.save(ignore_permissions=True)
        frappe.db.commit()

        log.mark_success(message="Invoices synced to Xero.", records_processed=processed)
    except Exception as exc:
        log.mark_failed(error=str(exc))
        raise


def _run_invoices_from_xero(log_name: str) -> None:
    settings = _get_settings()
    log = frappe.get_doc("Xero Sync Log", log_name)
    log.mark_running()
    try:
        if not settings.sync_invoices_from_xero:
            log.mark_success(message="Disabled (sync_invoices_from_xero is off).")
            return

        if not settings.default_company or not settings.default_item:
            raise RuntimeError("Set Default Company and Default Item in Xero Settings to import invoices.")

        client = _get_xero_client(settings)
        since_dt = settings.last_invoices_from_xero_sync_at or None
        invoices = client.list_invoices(since=since_dt)

        processed = 0
        for inv in invoices:
            xero_id = inv.get("InvoiceID")
            if not xero_id:
                continue

            existing = get_erpnext_name_by_xero_id(xero_id, "Sales Invoice")
            if existing:
                continue

            contact = inv.get("Contact") or {}
            contact_id = contact.get("ContactID")
            if not contact_id:
                continue

            customer_name = get_erpnext_name_by_xero_id(contact_id, "Customer")
            if not customer_name:
                vals = _xero_contact_to_customer_values(settings, contact)
                cust = frappe.get_doc({"doctype": "Customer", **vals})
                cust.insert(ignore_permissions=True)
                customer_name = cust.name
                set_mapping(
                    erpnext_doctype="Customer",
                    erpnext_name=customer_name,
                    xero_object="Contact",
                    xero_id=contact_id,
                )

            items = []
            for li in inv.get("LineItems") or []:
                qty = float(li.get("Quantity") or 0) or 1.0
                rate = float(li.get("UnitAmount") or 0)
                items.append(
                    {
                        "item_code": settings.default_item,
                        "qty": qty,
                        "rate": rate,
                        "description": li.get("Description"),
                    }
                )

            si = frappe.get_doc(
                {
                    "doctype": "Sales Invoice",
                    "customer": customer_name,
                    "company": settings.default_company,
                    "posting_date": inv.get("Date") or now_datetime().date(),
                    "due_date": inv.get("DueDate"),
                    "items": items,
                }
            )
            si.insert(ignore_permissions=True)

            set_mapping(
                erpnext_doctype="Sales Invoice",
                erpnext_name=si.name,
                xero_object="Invoice",
                xero_id=xero_id,
            )
            processed += 1

        settings.last_invoices_from_xero_sync_at = now_datetime()
        settings.save(ignore_permissions=True)
        frappe.db.commit()

        log.mark_success(message="Invoices synced from Xero.", records_processed=processed)
    except Exception as exc:
        log.mark_failed(error=str(exc))
        raise


def scheduled_sync() -> None:
    """
    Scheduler entrypoint (safe to call hourly).
    Enqueues sync jobs based on flags in Xero Settings.
    """
    settings = _get_settings()
    if settings.sync_customers_to_xero:
        enqueue_customers_to_xero()
    if settings.sync_customers_from_xero:
        enqueue_customers_from_xero()
    if settings.sync_invoices_to_xero:
        enqueue_invoices_to_xero()
    if settings.sync_invoices_from_xero:
        enqueue_invoices_from_xero()


__all__ = [
    "enqueue_customers_to_xero",
    "enqueue_customers_from_xero",
    "enqueue_invoices_to_xero",
    "enqueue_invoices_from_xero",
]

