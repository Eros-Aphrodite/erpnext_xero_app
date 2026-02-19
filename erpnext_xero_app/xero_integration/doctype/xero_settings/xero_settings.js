frappe.ui.form.on("Xero Settings", {
  refresh(frm) {
    // Button: Connect to Xero (OAuth)
    if (frm.doc.client_id && frm.doc.redirect_uri) {
      frm.add_custom_button("Connect to Xero", () => {
        frappe.call({
          method: "erpnext_xero_app.xero_integration.api.get_xero_auth_url",
          freeze: true,
          callback(r) {
            if (r.message && r.message.auth_url) {
              // Open OAuth URL in new window
              window.open(r.message.auth_url, "_blank");
              frappe.msgprint({
                title: __("OAuth Started"),
                message: __(
                  "A new window has opened. Please authorize the app in Xero, then return here."
                ),
                indicator: "blue",
              });
            }
          },
        });
      });
    }

    // Button: Test Connection
    frm.add_custom_button("Test Connection", () => {
      frappe.call({
        method:
          "erpnext_xero_app.xero_integration.doctype.xero_settings.xero_settings.test_connection",
        freeze: true,
        freeze_message: __("Testing Xero connection..."),
        callback(r) {
          if (!r.message) return;
          const { ok, message } = r.message;
          frappe.msgprint({
            title: ok ? __("Success") : __("Error"),
            message,
            indicator: ok ? "green" : "red",
          });
        },
      });
    });

    // Button: Sync Customers Now
    frm.add_custom_button("Sync Customers Now", () => {
      frappe.call({
        method:
          "erpnext_xero_app.xero_integration.doctype.xero_settings.xero_settings.sync_customers_now",
        freeze: true,
        freeze_message: __("Syncing customers with Xero..."),
        callback(r) {
          if (!r.message) return;
          const { ok, message } = r.message;
          frappe.msgprint({
            title: ok ? __("Success") : __("Error"),
            message,
            indicator: ok ? "green" : "red",
          });
          frm.reload_doc();
        },
      });
    });

    // Button: Sync Customers From Xero
    frm.add_custom_button("Sync Customers From Xero", () => {
      frappe.call({
        method:
          "erpnext_xero_app.xero_integration.doctype.xero_settings.xero_settings.sync_customers_from_xero_now",
        freeze: true,
        freeze_message: __("Importing customers from Xero..."),
        callback(r) {
          if (!r.message) return;
          const { ok, message } = r.message;
          frappe.msgprint({
            title: ok ? __("Success") : __("Error"),
            message,
            indicator: ok ? "green" : "red",
          });
          frm.reload_doc();
        },
      });
    });

    // Button: Sync Invoices Now
    frm.add_custom_button("Sync Invoices Now", () => {
      frappe.call({
        method:
          "erpnext_xero_app.xero_integration.doctype.xero_settings.xero_settings.sync_invoices_now",
        freeze: true,
        freeze_message: __("Syncing invoices with Xero..."),
        callback(r) {
          if (!r.message) return;
          const { ok, message } = r.message;
          frappe.msgprint({
            title: ok ? __("Success") : __("Error"),
            message,
            indicator: ok ? "green" : "red",
          });
          frm.reload_doc();
        },
      });
    });

    // Button: Sync Invoices From Xero
    frm.add_custom_button("Sync Invoices From Xero", () => {
      frappe.call({
        method:
          "erpnext_xero_app.xero_integration.doctype.xero_settings.xero_settings.sync_invoices_from_xero_now",
        freeze: true,
        freeze_message: __("Importing invoices from Xero..."),
        callback(r) {
          if (!r.message) return;
          const { ok, message } = r.message;
          frappe.msgprint({
            title: ok ? __("Success") : __("Error"),
            message,
            indicator: ok ? "green" : "red",
          });
          frm.reload_doc();
        },
      });
    });
  },
});

