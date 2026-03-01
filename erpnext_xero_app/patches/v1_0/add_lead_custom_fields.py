"""
Add custom fields to Lead DocType for pipeline management and scheduling.
"""
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """Add custom fields to Lead DocType."""
    
    custom_fields = {
        "Lead": [
            # Pipeline Stage Section
            {
                "fieldname": "sb_pipeline",
                "fieldtype": "Section Break",
                "label": "Pipeline & Scheduling",
                "insert_after": "blog_subscriber",
            },
            {
                "fieldname": "pipeline_stage",
                "fieldtype": "Select",
                "label": "Pipeline Stage",
                "options": "New\nContacted\nInspection Booked\nQuoted\nWon\nLost",
                "default": "New",
                "reqd": 1,
                "insert_after": "sb_pipeline",
            },
            {
                "fieldname": "job_type",
                "fieldtype": "Select",
                "label": "Job Type",
                "options": "Bathroom\nDeck\nGeneral Carpentry",
                "insert_after": "pipeline_stage",
            },
            {
                "fieldname": "preferred_date",
                "fieldtype": "Date",
                "label": "Preferred Date",
                "insert_after": "job_type",
            },
            {
                "fieldname": "preferred_time",
                "fieldtype": "Time",
                "label": "Preferred Time",
                "insert_after": "preferred_date",
            },
            {
                "fieldname": "site_address",
                "fieldtype": "Small Text",
                "label": "Site Address",
                "insert_after": "preferred_time",
            },
            {
                "fieldname": "cb_pipeline",
                "fieldtype": "Column Break",
                "insert_after": "site_address",
            },
            {
                "fieldname": "auto_create_calendar_event",
                "fieldtype": "Check",
                "label": "Auto Create Calendar Event",
                "default": 1,
                "insert_after": "cb_pipeline",
            },
            {
                "fieldname": "calendar_event_created",
                "fieldtype": "Check",
                "label": "Calendar Event Created",
                "read_only": 1,
                "insert_after": "auto_create_calendar_event",
            },
            {
                "fieldname": "linked_event",
                "fieldtype": "Link",
                "label": "Linked Event",
                "options": "Event",
                "read_only": 1,
                "insert_after": "calendar_event_created",
            },
        ]
    }
    
    create_custom_fields(custom_fields, ignore_validate=True, update=True)
    
    frappe.msgprint("✅ Custom fields added to Lead DocType")

