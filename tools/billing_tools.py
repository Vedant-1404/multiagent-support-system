from langchain_core.tools import tool
from typing import Optional


MOCK_INVOICES = {
    "INV-001": {"amount": 49.99, "status": "paid", "date": "2025-03-01", "plan": "Pro"},
    "INV-002": {"amount": 99.99, "status": "overdue", "date": "2025-03-15", "plan": "Business"},
    "INV-003": {"amount": 19.99, "status": "paid", "date": "2025-04-01", "plan": "Starter"},
}

MOCK_PLANS = {
    "starter": {"price": 19.99, "features": ["5 users", "10GB storage", "Email support"]},
    "pro": {"price": 49.99, "features": ["25 users", "100GB storage", "Priority support", "API access"]},
    "business": {"price": 99.99, "features": ["Unlimited users", "1TB storage", "24/7 support", "SLA"]},
}


@tool
def lookup_invoice(invoice_id: str) -> str:
    """Look up invoice details by invoice ID."""
    inv = MOCK_INVOICES.get(invoice_id.upper())
    if not inv:
        return f"Invoice {invoice_id} not found. Please check the invoice number."
    return (
        f"Invoice {invoice_id}: ${inv['amount']} | Status: {inv['status']} | "
        f"Date: {inv['date']} | Plan: {inv['plan']}"
    )


@tool
def get_plan_details(plan_name: str) -> str:
    """Get details and pricing for a subscription plan."""
    plan = MOCK_PLANS.get(plan_name.lower())
    if not plan:
        available = ", ".join(MOCK_PLANS.keys())
        return f"Plan '{plan_name}' not found. Available plans: {available}"
    features = " | ".join(plan["features"])
    return f"{plan_name.title()} Plan: ${plan['price']}/month — {features}"


@tool
def process_refund_request(invoice_id: str, reason: str) -> str:
    """Submit a refund request for a given invoice."""
    inv = MOCK_INVOICES.get(invoice_id.upper())
    if not inv:
        return f"Cannot process refund: invoice {invoice_id} not found."
    if inv["status"] == "overdue":
        return f"Cannot refund invoice {invoice_id}: payment has not been received yet."
    ticket_id = f"REF-{hash(invoice_id + reason) % 90000 + 10000}"
    return (
        f"Refund request submitted for invoice {invoice_id} (${inv['amount']}). "
        f"Reason: {reason}. Ticket ID: {ticket_id}. "
        f"Processing time: 5-7 business days."
    )


@tool
def check_billing_history(customer_note: str) -> str:
    """Summarise recent billing activity for the customer."""
    paid = [f"{k} (${v['amount']})" for k, v in MOCK_INVOICES.items() if v["status"] == "paid"]
    overdue = [f"{k} (${v['amount']})" for k, v in MOCK_INVOICES.items() if v["status"] == "overdue"]
    summary = f"Paid invoices: {', '.join(paid) if paid else 'none'}. "
    if overdue:
        summary += f"Overdue: {', '.join(overdue)}."
    return summary


BILLING_TOOLS = [lookup_invoice, get_plan_details, process_refund_request, check_billing_history]
