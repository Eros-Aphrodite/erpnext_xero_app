"""
Enhanced Server Script to create Google Calendar events with Google Meet links
and send email notifications to customers.
"""
import frappe


def execute():
    """Update Server Script to add Google Meet and email notifications."""
    
    script_name = "Auto Create Calendar Event from Lead"
    
    # Create script if it doesn't exist
    if not frappe.db.exists("Server Script", script_name):
        # Create the base script first
        from erpnext_xero_app.patches.v1_0.create_lead_calendar_sync import execute as create_base_script
        create_base_script()
    
    script = frappe.get_doc("Server Script", script_name)
    
    # Enhanced script with Google Meet and email notifications
    enhanced_script = '''# Auto-create Calendar Event with Google Meet when Lead is created/updated

import frappe
from frappe.utils import get_datetime, get_datetime_str, get_time, format_datetime, get_url
from datetime import datetime, timedelta

def on_lead_save(doc, method):
    # Only create event if:
    # 1. Auto create is enabled
    # 2. Preferred date and time are set
    # 3. Event hasn't been created yet
    # 4. Pipeline stage is "Inspection Booked" or "New"
    
    if not getattr(doc, 'auto_create_calendar_event', False):
        return
    
    if not getattr(doc, 'preferred_date', None) or not getattr(doc, 'preferred_time', None):
        return
    
    if getattr(doc, 'calendar_event_created', False) and getattr(doc, 'linked_event', None):
        # Event already created, skip
        return
    
    # Only create for certain pipeline stages (default to "New" if not set)
    pipeline_stage = getattr(doc, 'pipeline_stage', 'New')
    if pipeline_stage not in ["New", "Inspection Booked", "Contacted"]:
        return
    
    try:
        # Combine date and time
        preferred_time = getattr(doc, 'preferred_time', None)
        if isinstance(preferred_time, timedelta):
            time_obj = (datetime.min + preferred_time).time()
        else:
            time_obj = get_time(preferred_time) if isinstance(preferred_time, str) else preferred_time
        event_start = datetime.combine(getattr(doc, 'preferred_date'), time_obj)
        # Default duration: 60 minutes
        event_end = event_start + timedelta(hours=1)
        
        # Get lead name safely
        lead_name = getattr(doc, 'lead_name', None) or getattr(doc, 'company_name', None) or getattr(doc, 'first_name', None) or getattr(doc, 'email_id', None) or "Unknown Lead"
        
        # Get default Google Calendar for the user
        google_calendar = None
        google_calendar_id = None
        user_calendars = frappe.get_all(
            "Google Calendar",
            filters={"user": doc.owner or frappe.session.user, "enable": 1},
            fields=["name", "google_calendar_id", "user"],
            limit=1
        )
        if user_calendars:
            google_calendar = user_calendars[0].name
            cal_doc = frappe.get_doc("Google Calendar", google_calendar)
            # If calendar_id is None, use "primary" (Google Calendar API special ID for primary calendar)
            if not cal_doc.google_calendar_id:
                # Use "primary" as the calendar ID (Google Calendar API standard)
                google_calendar_id = "primary"
                # Set it on the calendar record to avoid future 403 errors
                frappe.db.set_value("Google Calendar", google_calendar, "google_calendar_id", google_calendar_id, update_modified=False)
            else:
                google_calendar_id = cal_doc.google_calendar_id
        
        # Create Event (enable Google sync only when a calendar is configured)
        event = frappe.get_doc({
            "doctype": "Event",
            "subject": f"{getattr(doc, 'job_type', None) or 'Inspection'} - {lead_name}",
            "description": f"""
Lead: {lead_name}
Email: {getattr(doc, 'email_id', None) or 'N/A'}
Mobile: {getattr(doc, 'mobile_no', None) or 'N/A'}
Job Type: {getattr(doc, 'job_type', None) or 'N/A'}
Site Address: {getattr(doc, 'site_address', None) or 'N/A'}
Notes: {getattr(doc, 'notes', None) or 'N/A'}
            """.strip(),
            "starts_on": get_datetime_str(event_start),
            "ends_on": get_datetime_str(event_end),
            "event_type": "Private",
            "lead": doc.name,
            "sync_with_google_calendar": 1 if google_calendar else 0,
            "add_video_conferencing": 1 if google_calendar else 0,
        })
        
        # Set Google Calendar and calendar ID (required for sync; fetch_from does not run on programmatic create)
        if google_calendar:
            event.google_calendar = google_calendar
        if google_calendar_id:
            event.google_calendar_id = google_calendar_id
        
        # Add custom fields if they exist
        if hasattr(doc, 'job_type') and doc.job_type:
            event.job_type = doc.job_type
        if hasattr(doc, 'site_address') and doc.site_address:
            event.site_address = doc.site_address
        
        # Add customer email as participant (for Google Calendar invite)
        if getattr(doc, 'email_id', None):
            event.append("event_participants", {
                "reference_doctype": "Lead",
                "reference_docname": doc.name,
                "email": doc.email_id,
            })
        
        # Insert event (this will trigger Google Calendar sync via hooks)
        event.insert(ignore_permissions=True)
        
        # Update Lead with event link immediately
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
        
        # Reload event to get Google Meet link (set by Google Calendar sync hook)
        event.reload()
        
        # Send email notification with Google Meet link
        # Use enqueue to ensure Google Calendar sync completes first
        if getattr(doc, 'email_id', None):
            frappe.enqueue(
                "erpnext_xero_app.patches.v1_0.meeting_email_utils.send_meeting_invite_email",
                lead_name=doc.name,
                event_name=event.name,
                queue="short",
                timeout=300
            )
        
        frappe.msgprint(f"✅ Calendar Event '{event.subject}' created successfully")
        
    except Exception as e:
        frappe.log_error(f"Error creating calendar event for Lead {doc.name}: {str(e)}")
        frappe.msgprint(f"⚠️ Error creating calendar event: {str(e)}", indicator="orange")


'''
    
    script.script = enhanced_script
    script.save()
    frappe.db.commit()
    
    frappe.msgprint(f"✅ Server Script '{script_name}' updated with Google Meet and email notifications")
