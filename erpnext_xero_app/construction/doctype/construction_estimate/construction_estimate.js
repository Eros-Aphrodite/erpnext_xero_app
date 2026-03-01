frappe.ui.form.on("Construction Estimate", {
    refresh(frm) {
        if (!frm.doc.__islocal) {
            frm.add_custom_button(
                __("Create Quotation"),
                () => {
                    frappe.call({
                        method: "erpnext_xero_app.construction.doctype.construction_estimate.construction_estimate.make_quotation",
                        args: {
                            estimate_name: frm.doc.name,
                        },
                        freeze: true,
                        freeze_message: __("Creating Quotation..."),
                        callback: (r) => {
                            if (r.message) {
                                frappe.set_route("Form", "Quotation", r.message);
                            }
                        },
                    });
                },
                __("Create")
            );
        }
    },
});

