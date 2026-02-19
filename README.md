# ERPNext Xero Integration (Frappe App)

This is a **Frappe app skeleton** that adds a **user interface inside ERPNext** to
configure and run synchronization with **Xero**:

- `Xero Settings` DocType with UI fields:
  - Client ID, Client Secret (password fields)
  - Redirect URI
  - Tenant ID
  - Access / Refresh tokens
  - Test Connection button
- Hooks to run sync jobs (customers & invoices) using background jobs or manual buttons.

> This app is designed as a starting point. You can copy it into a real
> Frappe bench and install it with `bench install-app erpnext_xero_app`.

## Basic Structure

```
erpnext_xero_app/
├── erpnext_xero_app/
│   ├── __init__.py
│   ├── hooks.py
│   ├── config/
│   │   └── desktop.py
│   └── xero_integration/
│       ├── __init__.py
│       ├── api.py
│       └── doctype/
│           └── xero_settings/
│               ├── xero_settings.json
│               └── xero_settings.py
└── README.md
```

## Installation (in a real bench)

1. Copy this folder into your bench apps directory, e.g.:

```bash
cp -R erpnext_xero_app /path/to/bench/apps/erpnext_xero_app
```

2. From your bench root:

```bash
bench --site your-site.local install-app erpnext_xero_app
bench migrate
```

3. Log in to ERPNext:
   - Go to **Xero Settings** (via Awesome Bar or under Integrations).
   - Enter **Client ID**, **Client Secret**, **Redirect URI**.
   - Click **Get Xero Tokens** to complete OAuth.
   - Click **Test Connection** to verify.

## Notes

- This is a **template**: you still need to:
  - Wire the OAuth redirect URI in your Xero app.
  - Extend sync logic (customers, invoices) as needed.
  - Add scheduled jobs in `hooks.py` when you are ready.

