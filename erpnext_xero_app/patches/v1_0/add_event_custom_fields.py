"""
Add custom fields to Event DocType for linking with Leads.
"""
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """Add custom fields to Event DocType."""
    
    custom_fields = {
        "Event": [
            {
                "fieldname": "sb_lead_info",
                "fieldtype": "Section Break",
                "label": "Lead Information",
                "insert_after": "repeat_on",
            },
            {
                "fieldname": "lead",
                "fieldtype": "Link",
                "label": "Lead",
                "options": "Lead",
                "insert_after": "sb_lead_info",
            },
            {
                "fieldname": "job_type",
                "fieldtype": "Select",
                "label": "Job Type",
                "options": "Bathroom\nDeck\nGeneral Carpentry",
                "fetch_from": "lead.job_type",
                "insert_after": "lead",
            },
            {
                "fieldname": "site_address",
                "fieldtype": "Small Text",
                "label": "Site Address",
                "fetch_from": "lead.site_address",
                "insert_after": "job_type",
            },
        ]
    }
    
    create_custom_fields(custom_fields, ignore_validate=True, update=True)
    
    frappe.msgprint("✅ Custom fields added to Event DocType")

