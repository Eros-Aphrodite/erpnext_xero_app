# Copyright (c) 2026 and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document


class XeroTrackingMapping(Document):
	def validate(self):
		self.erpnext_doctype_and_name = f"{self.erpnext_doctype}::{self.erpnext_name}"


def get_tracking_for_erpnext(erpnext_doctype: str, erpnext_name: str) -> dict | None:
	"""Return Xero tracking dict for invoice line: TrackingCategoryID, Name, OptionName. None if no mapping."""
	if not erpnext_name:
		return None
	key = f"{erpnext_doctype}::{erpnext_name}"
	if not frappe.db.exists("Xero Tracking Mapping", key):
		return None
	m = frappe.db.get_value(
		"Xero Tracking Mapping",
		key,
		["xero_tracking_category_id", "xero_tracking_category_name", "xero_tracking_option_name"],
		as_dict=True,
	)
	if not m or not m.get("xero_tracking_category_id") or not m.get("xero_tracking_option_name"):
		return None
	return {
		"TrackingCategoryID": m["xero_tracking_category_id"],
		"Name": m.get("xero_tracking_category_name") or "Project",
		"OptionName": m["xero_tracking_option_name"],
	}
