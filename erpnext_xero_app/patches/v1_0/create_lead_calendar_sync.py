"""
Server Script to auto-create Google Calendar events when Leads are created/updated.
"""
import frappe
from frappe.utils import get_datetime, get_datetime_str, get_time
from datetime import datetime, timedelta


def execute():
    """Create Server Script for Lead → Calendar Event sync."""
    
    script_name = "Auto Create Calendar Event from Lead"
    
    if frappe.db.exists("Server Script", script_name):
        frappe.msgprint(f"Server Script '{script_name}' already exists. Skipping creation.")
        return
    
    script_content = '''# Auto-create Calendar Event when Lead is created/updated with preferred_date and preferred_time

import frappe
from frappe.utils import get_datetime, get_datetime_str, get_time
from datetime import datetime, timedelta

def on_lead_save(doc, method):
    # Only create event if:
    # 1. Auto create is enabled
    # 2. Preferred date and time are set
    # 3. Event hasn't been created yet
    # 4. Pipeline stage is "Inspection Booked" or "New"
    
    if not doc.auto_create_calendar_event:
        return
    
    if not doc.preferred_date or not doc.preferred_time:
        return
    
    if doc.calendar_event_created and doc.linked_event:
        # Event already created, skip
        return
    
    # Only create for certain pipeline stages
    if doc.pipeline_stage not in ["New", "Inspection Booked", "Contacted"]:
        return
    
    try:
        # Combine date and time
        if isinstance(doc.preferred_time, timedelta):
            time_obj = (datetime.min + doc.preferred_time).time()
        else:
            time_obj = get_time(doc.preferred_time) if isinstance(doc.preferred_time, str) else doc.preferred_time
        event_start = datetime.combine(doc.preferred_date, time_obj)
        # Default duration: 60 minutes
        event_end = event_start + timedelta(hours=1)
        
        # Get lead name safely
        lead_name = doc.lead_name or doc.company_name or doc.first_name or doc.email_id or "Unknown Lead"
        
        # Create Event
        event = frappe.get_doc({
            "doctype": "Event",
            "subject": f"{doc.job_type or 'Inspection'} - {lead_name}",
            "description": f"""
Lead: {lead_name}
Email: {doc.email_id or 'N/A'}
Mobile: {doc.mobile_no or 'N/A'}
Job Type: {doc.job_type or 'N/A'}
Site Address: {doc.site_address or 'N/A'}
Notes: {getattr(doc, 'notes', '') or 'N/A'}
            """.strip(),
            "starts_on": get_datetime_str(event_start),
            "ends_on": get_datetime_str(event_end),
            "event_type": "Private",
            "lead": doc.name,
        })
        
        # Add custom fields if they exist
        if hasattr(doc, 'job_type') and doc.job_type:
            event.job_type = doc.job_type
        if hasattr(doc, 'site_address') and doc.site_address:
            event.site_address = doc.site_address
        
        # Enable Google Calendar sync
        event.sync_with_google_calendar = 1
        
        event.insert(ignore_permissions=True)
        
        # Update Lead with event link
        frappe.db.set_value(
            "Lead",
            doc.name,
            {
                "linked_event": event.name,
                "calendar_event_created": 1,
            },
            update_modified=False
        )
        
        frappe.db.commit()
        
        frappe.msgprint(f"✅ Calendar Event '{event.subject}' created successfully")
        
    except Exception as e:
        frappe.log_error(f"Error creating calendar event for Lead {doc.name}: {str(e)}")
        frappe.msgprint(f"⚠️ Error creating calendar event: {str(e)}", indicator="orange")
'''
    
    server_script = frappe.get_doc({
        "doctype": "Server Script",
        "name": script_name,
        "script_type": "DocType Event",
        "reference_doctype": "Lead",
        "doctype_event": "After Save",
        "script": script_content,
        "disabled": 0,
    })
    
    server_script.insert(ignore_permissions=True)
    frappe.db.commit()
    
    frappe.msgprint(f"✅ Server Script '{script_name}' created and enabled")

