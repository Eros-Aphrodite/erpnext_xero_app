"""
Legacy patch file.

This patch previously disabled the Server Script that creates calendar events
and Google Meet links from Leads submitted via the web form.

The automation is now a core part of the project, so this patch is intentionally
left as a **no-op**. It remains only to avoid import errors if referenced.
"""


def execute():
    """No-op: calendar / Meet integration for Leads stays enabled."""
    return
