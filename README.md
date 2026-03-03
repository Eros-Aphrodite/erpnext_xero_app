### ERPNext Xero Integration

Sync ERPNext customers and sales invoices with Xero.

### Purpose

Use this app to **connect ERPNext to Xero** via OAuth, then **sync Customers and Sales Invoices** in either direction and keep a clear audit trail of each sync run.

### What's included

- **Xero Settings**: store Xero OAuth credentials, default ERPNext mappings for invoice imports, and enable/disable sync directions
- **Xero Mapping / Tracking Mapping**: optional mapping helpers for accounts / tracking categories
- **Xero Sync Log**: log each sync run (direction, status, processed count, details/errors)
- **Scheduled sync**: hourly scheduler entrypoint that checks settings and enqueues jobs

### Installation

Install via bench:

```bash
cd /path/to/frappe-bench
bench get-app $URL_OF_THIS_REPO
bench install-app erpnext_xero_app
bench migrate
bench clear-cache
```

### Configuration (high level)

- Create a Xero app and copy the **Client ID / Client Secret**
- In ERPNext open **Xero Settings** and set:
  - **Client ID**, **Client Secret**, **Redirect URI**
  - Defaults used when importing invoices (Company, Item, Customer Group, Territory, etc.)
  - Turn on the sync toggles you want (customers/invoices, to/from Xero)

### Desk route

- App route: `/app/xero-integration`

