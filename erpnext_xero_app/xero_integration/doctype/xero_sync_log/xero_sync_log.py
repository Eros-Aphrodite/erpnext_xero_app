from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class XeroSyncLog(Document):
    def mark_running(self):
        self.status = "Running"
        self.started_at = now_datetime()
        self.save(ignore_permissions=True)

    def mark_success(self, *, message: str, records_processed: int = 0, details: str | None = None):
        self.status = "Success"
        self.ended_at = now_datetime()
        self.message = message
        self.records_processed = records_processed
        if details is not None:
            self.details = details
        self.save(ignore_permissions=True)

    def mark_failed(self, *, error: str, details: str | None = None):
        self.status = "Failed"
        self.ended_at = now_datetime()
        self.error = error
        if details is not None:
            self.details = details
        self.save(ignore_permissions=True)


def create_log(*, entity: str, direction: str) -> str:
    doc = frappe.get_doc({"doctype": "Xero Sync Log", "entity": entity, "direction": direction})
    doc.insert(ignore_permissions=True)
    return doc.name


__all__ = ["XeroSyncLog", "create_log"]

