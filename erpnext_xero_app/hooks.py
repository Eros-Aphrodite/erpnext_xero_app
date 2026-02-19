from __future__ import annotations

app_name = "erpnext_xero_app"
app_title = "ERPNext Xero Integration"
app_publisher = "Your Name"
app_description = "Configure and sync ERPNext customers & invoices with Xero."
app_email = "you@example.com"
app_license = "MIT"

scheduler_events = {
    # Safe entrypoint: checks flags in Xero Settings and enqueues jobs
    "hourly": ["erpnext_xero_app.xero_integration.sync.scheduled_sync"]
}

