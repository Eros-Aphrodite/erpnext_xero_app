from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class XeroMapping(Document):
    def autoname(self):
        # Unique, stable name for ERPNext-side lookup
        self.name = f"{self.erpnext_doctype}::{self.erpnext_name}"

    def before_save(self):
        self.last_synced_at = now_datetime()


def get_xero_id(erpnext_doctype: str, erpnext_name: str) -> str | None:
    name = f"{erpnext_doctype}::{erpnext_name}"
    if frappe.db.exists("Xero Mapping", name):
        return frappe.db.get_value("Xero Mapping", name, "xero_id")
    return None


def set_mapping(
    *,
    erpnext_doctype: str,
    erpnext_name: str,
    xero_object: str,
    xero_id: str,
) -> None:
    name = f"{erpnext_doctype}::{erpnext_name}"
    if frappe.db.exists("Xero Mapping", name):
        doc = frappe.get_doc("Xero Mapping", name)
        doc.xero_object = xero_object
        doc.xero_id = xero_id
        doc.save(ignore_permissions=True)
    else:
        doc = frappe.get_doc(
            {
                "doctype": "Xero Mapping",
                "erpnext_doctype": erpnext_doctype,
                "erpnext_name": erpnext_name,
                "xero_object": xero_object,
                "xero_id": xero_id,
            }
        )
        doc.insert(ignore_permissions=True)


def get_erpnext_name_by_xero_id(xero_id: str, erpnext_doctype: str) -> str | None:
    return frappe.db.get_value(
        "Xero Mapping",
        {"xero_id": xero_id, "erpnext_doctype": erpnext_doctype},
        "erpnext_name",
    )


__all__ = ["XeroMapping", "get_xero_id", "set_mapping", "get_erpnext_name_by_xero_id"]

