from langchain_core.tools import tool


MOCK_ORDERS = {
    "ORD-100": {"item": "Pro Subscription", "date": "2025-03-01", "status": "active", "amount": 49.99},
    "ORD-101": {"item": "Business Plan", "date": "2025-02-15", "status": "active", "amount": 99.99},
    "ORD-102": {"item": "Hardware Kit", "date": "2025-01-10", "status": "delivered", "amount": 299.00},
}

RETURN_POLICY = {
    "software": "Software subscriptions can be cancelled anytime. Refunds available within 30 days of purchase.",
    "hardware": "Hardware returns accepted within 14 days of delivery in original packaging. Restocking fee: 10%.",
    "damaged": "Damaged items: contact support within 7 days with photos. Free replacement or full refund.",
    "cancelled": "Cancelled orders before dispatch: full refund within 3 business days.",
}


@tool
def lookup_order(order_id: str) -> str:
    """Look up order details by order ID."""
    order = MOCK_ORDERS.get(order_id.upper())
    if not order:
        return f"Order {order_id} not found. Please double-check the order number from your confirmation email."
    return (
        f"Order {order_id}: {order['item']} | Status: {order['status']} | "
        f"Date: {order['date']} | Amount: ${order['amount']}"
    )


@tool
def check_return_policy(item_type: str) -> str:
    """Check the return policy for a specific item type (software/hardware/damaged/cancelled)."""
    policy = RETURN_POLICY.get(item_type.lower())
    if not policy:
        options = ", ".join(RETURN_POLICY.keys())
        return f"No policy found for '{item_type}'. Available categories: {options}"
    return f"Return policy for {item_type}: {policy}"


@tool
def create_rma(order_id: str, reason: str, item_condition: str = "unknown") -> str:
    """Create a Return Merchandise Authorization (RMA) for a product return."""
    order = MOCK_ORDERS.get(order_id.upper())
    if not order:
        return f"Cannot create RMA: order {order_id} not found."
    if order["status"] == "active" and "subscription" in order["item"].lower():
        return (
            f"Order {order_id} is a subscription — use the cancellation flow instead. "
            f"Go to Settings > Subscription > Cancel."
        )
    rma_id = f"RMA-{hash(order_id + reason) % 90000 + 10000}"
    return (
        f"RMA created: {rma_id} for order {order_id} ({order['item']}). "
        f"Reason: {reason} | Condition: {item_condition}. "
        f"Ship the item to: Returns Dept, 123 Support Lane, Tech City, CA 94000. "
        f"Include RMA number on the package. Refund processed within 5-7 business days of receipt."
    )


@tool
def cancel_order(order_id: str, reason: str) -> str:
    """Cancel an order that hasn't been dispatched yet."""
    order = MOCK_ORDERS.get(order_id.upper())
    if not order:
        return f"Order {order_id} not found."
    if order["status"] == "delivered":
        return f"Order {order_id} already delivered. Please use the return/RMA process instead."
    cancel_ref = f"CAN-{hash(order_id) % 90000 + 10000}"
    return (
        f"Cancellation request {cancel_ref} submitted for order {order_id}. "
        f"Refund of ${order['amount']} will be processed within 3 business days."
    )


RETURNS_TOOLS = [lookup_order, check_return_policy, create_rma, cancel_order]
