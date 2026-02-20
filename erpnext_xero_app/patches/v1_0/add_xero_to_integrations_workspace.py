"""
Add Xero Settings links to Integrations workspace
"""
import frappe
from frappe.utils import cint


def execute():
	"""Add Xero integration links to the Integrations workspace"""
	if not frappe.db.exists("Workspace", "Integrations"):
		return

	workspace = frappe.get_doc("Workspace", "Integrations")
	
	# Check if Xero links already exist
	xero_links_exist = any(
		link.link_to == "Xero Settings" for link in workspace.links
	)
	
	if xero_links_exist:
		return
	
	# Find the last link index
	last_idx = max([link.idx for link in workspace.links], default=0)
	
	# Add "Xero Integration" card break if it doesn't exist
	xero_card_exists = any(
		link.label == "Xero Integration" and link.type == "Card Break"
		for link in workspace.links
	)
	
	if not xero_card_exists:
		workspace.append("links", {
			"label": "Xero Integration",
			"type": "Card Break",
			"link_count": 3,
			"idx": last_idx + 1,
		})
		last_idx += 1
	
	# Add Xero Settings link
	workspace.append("links", {
		"label": "Xero Settings",
		"type": "Link",
		"link_type": "DocType",
		"link_to": "Xero Settings",
		"idx": last_idx + 1,
	})
	last_idx += 1
	
	# Add Xero Mapping link
	workspace.append("links", {
		"label": "Xero Mapping",
		"type": "Link",
		"link_type": "DocType",
		"link_to": "Xero Mapping",
		"idx": last_idx + 1,
	})
	last_idx += 1
	
	# Add Xero Sync Log link
	workspace.append("links", {
		"label": "Xero Sync Log",
		"type": "Link",
		"link_type": "DocType",
		"link_to": "Xero Sync Log",
		"idx": last_idx + 1,
	})
	
	workspace.save(ignore_permissions=True)
	frappe.db.commit()
