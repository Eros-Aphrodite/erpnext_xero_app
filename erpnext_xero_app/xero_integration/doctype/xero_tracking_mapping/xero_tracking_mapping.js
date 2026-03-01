frappe.ui.form.on("Xero Tracking Mapping", {
	refresh(frm) {
		frm.add_custom_button(__("Fetch Xero Categories"), () => {
			frappe.call({
				method: "erpnext_xero_app.xero_integration.sync.get_xero_tracking_categories",
				freeze: true,
				freeze_message: __("Fetching from Xero..."),
				callback(r) {
					if (r.exc) return;
					const cats = r.message || [];
					if (!cats.length) {
						frappe.msgprint(__("No active tracking categories in Xero."));
						return;
					}
					const options = [];
					cats.forEach((c) => {
						(c.options || []).forEach((o) => {
							options.push({
								label: `${c.name} → ${o.name}`,
								value: JSON.stringify({
									category_id: c.tracking_category_id,
									category_name: c.name,
									option_id: o.tracking_option_id,
									option_name: o.name,
								}),
							});
						});
					});
					const d = new frappe.ui.Dialog({
						title: __("Select Xero Tracking Category & Option"),
						fields: [{ fieldname: "choice", fieldtype: "Select", label: __("Category → Option"), options: options }],
						primary_action_label: __("Set"),
						primary_action({ choice }) {
							if (!choice) return;
							const v = JSON.parse(choice);
							frm.set_value("xero_tracking_category_id", v.category_id);
							frm.set_value("xero_tracking_category_name", v.category_name);
							frm.set_value("xero_tracking_option_id", v.option_id);
							frm.set_value("xero_tracking_option_name", v.option_name);
							d.hide();
						},
					});
					d.show();
				},
			});
		});
	},
});
