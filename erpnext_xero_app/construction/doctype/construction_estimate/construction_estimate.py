import frappe
from frappe.model.document import Document


class ConstructionEstimate(Document):
    def validate(self):
        """Recalculate line amounts and totals."""
        total_qty = 0.0
        total_amount = 0.0

        for row in self.items or []:
            row.amount = (row.quantity or 0) * (row.rate or 0)
            total_qty += row.quantity or 0
            total_amount += row.amount or 0

        self.total_qty = total_qty
        self.total_amount = total_amount


@frappe.whitelist()
def make_quotation(estimate_name: str) -> str:
    """Create an ERPNext Quotation from a Construction Estimate.

    Returns the name of the created Quotation.
    """
    estimate = frappe.get_doc("Construction Estimate", estimate_name)

    quotation = frappe.new_doc("Quotation")
    quotation.customer = estimate.customer
    quotation.company = estimate.company
    quotation.transaction_date = estimate.transaction_date

    for row in estimate.items or []:
        if not row.include_in_quotation:
            continue

        if not row.item and not row.description:
            continue

        quotation.append(
            "items",
            {
                "item_code": row.item,
                "description": row.description or row.section,
                "qty": row.quantity or 0,
                "uom": row.uom,
                "rate": row.rate or 0,
            },
        )

    quotation.insert(ignore_permissions=True)

    # Optionally link back to the estimate
    quotation.db_set("remarks", (quotation.remarks or "")
                     + f"\n\nSource Estimate: {estimate.name}")

    return quotation.name

