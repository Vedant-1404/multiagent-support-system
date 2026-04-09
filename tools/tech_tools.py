from langchain_core.tools import tool


MOCK_DOCS = {
    "login": "To reset your password: go to Settings > Security > Reset Password. A link will be emailed to you within 2 minutes.",
    "api": "API keys are found in Settings > Developer > API Keys. Rate limit is 1000 req/min on Pro, 5000 on Business.",
    "install": "Install the app: download from our website, run the installer, enter your license key from your welcome email.",
    "export": "To export data: go to Settings > Data > Export. Supports CSV, JSON, and PDF. Exports are emailed within 10 minutes.",
    "sso": "SSO setup requires Business plan. Go to Settings > Security > SSO and follow the SAML 2.0 configuration guide.",
    "webhook": "Webhooks: Settings > Developer > Webhooks. Supports POST to any HTTPS endpoint. Retry logic: 3 attempts.",
    "2fa": "Enable 2FA under Settings > Security > Two-Factor Authentication. Supports TOTP apps and SMS.",
}

MOCK_KNOWN_ISSUES = {
    "slow": "Known issue: dashboard slowness for accounts with 10k+ records. Fix deploying 2025-04-15.",
    "export_fail": "Known issue: CSV exports failing for date ranges > 90 days. Workaround: export in 90-day chunks.",
    "mobile": "Known issue: mobile app crash on iOS 18.3. Update to app v4.2.1 to fix.",
}


@tool
def search_documentation(query: str) -> str:
    """Search the product documentation for answers to technical questions."""
    query_lower = query.lower()
    results = []
    for keyword, content in MOCK_DOCS.items():
        if keyword in query_lower:
            results.append(content)
    if not results:
        return (
            "No specific documentation found for that query. "
            "Please visit help.example.com or contact support with error details."
        )
    return " | ".join(results)


@tool
def check_known_issues(description: str) -> str:
    """Check if the described problem matches any known issues."""
    desc_lower = description.lower()
    matches = []
    for key, issue in MOCK_KNOWN_ISSUES.items():
        if any(word in desc_lower for word in key.split("_")):
            matches.append(issue)
    if not matches:
        return "No known issues match this description. This may be account-specific — please include error messages and steps to reproduce."
    return "Known issues found: " + " | ".join(matches)


@tool
def create_support_ticket(summary: str, priority: str = "medium") -> str:
    """Create a technical support ticket for complex issues."""
    valid = ["low", "medium", "high", "critical"]
    if priority not in valid:
        priority = "medium"
    ticket_id = f"TKT-{hash(summary) % 90000 + 10000}"
    return (
        f"Support ticket created: {ticket_id} | Priority: {priority} | "
        f"Summary: {summary[:80]}. Our team will respond within "
        f"{'1 hour' if priority == 'critical' else '4 hours' if priority == 'high' else '24 hours'}."
    )


@tool
def get_system_status() -> str:
    """Check the current system status and any active incidents."""
    return (
        "System status: All services operational. "
        "Last incident: 2025-03-28 (resolved). "
        "Uptime (30 days): 99.94%. Status page: status.example.com"
    )


TECHNICAL_TOOLS = [search_documentation, check_known_issues, create_support_ticket, get_system_status]
