"""
Create a Web Form for Lead capture that customers can fill out.
"""
import frappe


def execute():
    """Create Web Form for Lead."""
    
    if frappe.db.exists("Web Form", "Lead Inquiry"):
        frappe.msgprint("Web Form 'Lead Inquiry' already exists. Skipping creation.")
        return
    
    web_form = frappe.get_doc({
        "doctype": "Web Form",
        "title": "Lead Inquiry",
        "route": "lead-inquiry",
        "doc_type": "Lead",
        "is_standard": 0,
        "published": 1,
        "allow_edit": 0,
        "allow_delete": 0,
        "allow_multiple": 1,
        "login_required": 0,
        "allow_comments": 0,
        "show_attachments": 0,
        "web_form_fields": [
            {
                "fieldname": "lead_name",
                "fieldtype": "Data",
                "label": "Full Name",
                "reqd": 1,
            },
            {
                "fieldname": "email_id",
                "fieldtype": "Data",
                "label": "Email",
                "reqd": 1,
            },
            {
                "fieldname": "mobile_no",
                "fieldtype": "Data",
                "label": "Mobile Number",
            },
            {
                "fieldname": "company_name",
                "fieldtype": "Data",
                "label": "Company Name",
            },
            {
                "fieldname": "sb_pipeline",
                "fieldtype": "Section Break",
                "label": "Project Details",
            },
            {
                "fieldname": "job_type",
                "fieldtype": "Select",
                "label": "Job Type",
                "options": "Bathroom\nDeck\nGeneral Carpentry",
                "reqd": 1,
            },
            {
                "fieldname": "preferred_date",
                "fieldtype": "Date",
                "label": "Preferred Date",
                "reqd": 1,
            },
            {
                "fieldname": "preferred_time",
                "fieldtype": "Time",
                "label": "Preferred Time",
                "reqd": 1,
            },
            {
                "fieldname": "site_address",
                "fieldtype": "Small Text",
                "label": "Site Address",
            },
            {
                "fieldname": "notes",
                "fieldtype": "Text Editor",
                "label": "Additional Notes",
            },
        ],
    })
    
    web_form.insert(ignore_permissions=True)
    frappe.db.commit()
    
    frappe.msgprint("✅ Web Form 'Lead Inquiry' created at route: /lead-inquiry")

