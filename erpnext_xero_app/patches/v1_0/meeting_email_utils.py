"""
Utility functions for sending meeting invite emails.
"""
import frappe
from frappe.utils import format_datetime
import time


@frappe.whitelist()
def send_meeting_invite_email(lead_name, event_name):
    """Send email notification with Google Meet link to customer."""
    try:
        # Wait a moment for Google Calendar sync to complete
        time.sleep(2)
        
        # Reload event to get latest Google Meet link
        event_doc = frappe.get_doc("Event", event_name)
        event_doc.reload()
        
        # Get lead document
        lead_doc = frappe.get_doc("Lead", lead_name)
        
        # Check if email exists
        if not getattr(lead_doc, 'email_id', None):
            frappe.log_error(f"No email found for Lead {lead_name}")
            return
        
        # Format date/time
        starts_on = format_datetime(event_doc.starts_on, "dd MMM yyyy, hh:mm a")
        ends_on = format_datetime(event_doc.ends_on, "hh:mm a") if event_doc.ends_on else ""
        
        # Email subject
        subject = f"Meeting Scheduled: {event_doc.subject}"
        
        # Build email content
        lead_display_name = getattr(lead_doc, 'lead_name', None) or getattr(lead_doc, 'company_name', None) or 'Customer'
        job_type = getattr(lead_doc, 'job_type', None) or 'inspection'
        site_address = getattr(lead_doc, 'site_address', None) or 'N/A'
        
        # Email content with Google Meet link
        meet_link_section = ""
        if event_doc.google_meet_link:
            meet_link_section = f"""
<h3>Join Google Meet</h3>
<p>Click the link below to join the video meeting:</p>
<p><a href="{event_doc.google_meet_link}" style="background-color: #4285f4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Join Google Meet</a></p>
<p>Or copy this link: <a href="{event_doc.google_meet_link}">{event_doc.google_meet_link}</a></p>
"""
        else:
            meet_link_section = """
<p><em>Note: Google Meet link will be available in your Google Calendar event.</em></p>
"""
        
        content = f"""
<h2>Your Appointment Has Been Scheduled</h2>

<p>Dear {lead_display_name},</p>

<p>We have scheduled your {job_type} appointment:</p>

<ul>
    <li><strong>Date & Time:</strong> {starts_on} - {ends_on}</li>
    <li><strong>Job Type:</strong> {job_type}</li>
    <li><strong>Site Address:</strong> {site_address}</li>
</ul>

{meet_link_section}

<p>This event has also been added to your Google Calendar.</p>

<p>We look forward to meeting with you!</p>

<p>Best regards,<br>
Q Finishes Team</p>
        """
        
        # Send email
        frappe.sendmail(
            recipients=[lead_doc.email_id],
            subject=subject,
            message=content,
            reference_doctype="Lead",
            reference_name=lead_doc.name,
        )
        
        frappe.log_error(f"Meeting invite email sent to {lead_doc.email_id} for Event {event_name}")
        
    except Exception as e:
        frappe.log_error(f"Error sending meeting invite email for Lead {lead_name}, Event {event_name}: {str(e)}")
