from __future__ import annotations


def get_data():
    return [
        {
            "label": "Integrations",
            "items": [
                {
                    "type": "doctype",
                    "name": "Xero Settings",
                    "label": "Xero Settings",
                    "description": "Configure Xero API credentials and sync options.",
                    "icon": "octicon octicon-sync",
                },
                {
                    "type": "doctype",
                    "name": "Xero Mapping",
                    "label": "Xero Mapping",
                    "description": "ERPNext ↔ Xero ID mappings (customers, invoices).",
                    "icon": "octicon octicon-link",
                },
                {
                    "type": "doctype",
                    "name": "Xero Sync Log",
                    "label": "Xero Sync Log",
                    "description": "History of sync runs and errors.",
                    "icon": "octicon octicon-list-unordered",
                }
            ],
        }
    ]

