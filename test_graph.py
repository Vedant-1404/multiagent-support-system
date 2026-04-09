import pytest
import os
import uuid
os.environ.setdefault("GROQ_API_KEY", "test-key")

from graph.state import AgentState
from graph.edges import (
    route_after_guardrail,
    route_after_triage,
    route_after_specialist,
    ESCALATION_CONFIDENCE_THRESHOLD,
    ESCALATION_RETRY_LIMIT,
)
from guardrails.input_guard import redact_pii, check_blocked_topics


def make_state(**overrides) -> AgentState:
    base = {
        "messages": [],
        "thread_id": str(uuid.uuid4()),
        "user_input": "test message",
        "intent": None,
        "confidence": None,
        "assigned_agent": None,
        "agent_response": None,
        "retry_count": 0,
        "escalated": False,
        "escalation_reason": None,
        "final_response": None,
        "guardrail_triggered": False,
        "guardrail_reason": None,
    }
    return {**base, **overrides}


class TestGuardrailRouting:
    def test_clean_message_routes_to_triage(self):
        state = make_state(guardrail_triggered=False)
        assert route_after_guardrail(state) == "triage"

    def test_triggered_guardrail_routes_to_block(self):
        state = make_state(guardrail_triggered=True)
        assert route_after_guardrail(state) == "guardrail_block"


class TestPIIRedaction:
    def test_email_redacted(self):
        text, found = redact_pii("Contact me at user@example.com please")
        assert "[EMAIL-REDACTED]" in text
        assert "email" in found

    def test_credit_card_redacted(self):
        text, found = redact_pii("My card is 4111 1111 1111 1111")
        assert "[CARD-REDACTED]" in text
        assert "credit_card" in found

    def test_phone_redacted(self):
        text, found = redact_pii("Call me at 555-123-4567")
        assert "[PHONE-REDACTED]" in text
        assert "phone" in found

    def test_clean_text_unchanged(self):
        text, found = redact_pii("I need help with my invoice")
        assert text == "I need help with my invoice"
        assert found == []


class TestBlockedTopics:
    def test_blocked_phrase_detected(self):
        blocked, reason = check_blocked_topics("how to hack into the system")
        assert blocked is True
        assert "hack" in reason

    def test_clean_query_passes(self):
        blocked, _ = check_blocked_topics("I need help with my subscription")
        assert blocked is False


class TestTriageRouting:
    def test_billing_intent_routes_correctly(self):
        state = make_state(intent="billing", confidence=0.9, retry_count=0)
        assert route_after_triage(state) == "billing_agent"

    def test_technical_intent_routes_correctly(self):
        state = make_state(intent="technical", confidence=0.85, retry_count=0)
        assert route_after_triage(state) == "technical_agent"

    def test_returns_intent_routes_correctly(self):
        state = make_state(intent="returns", confidence=0.9, retry_count=0)
        assert route_after_triage(state) == "returns_agent"

    def test_low_confidence_escalates(self):
        state = make_state(intent="billing", confidence=0.3, retry_count=0)
        assert route_after_triage(state) == "escalate"

    def test_high_retry_escalates(self):
        state = make_state(intent="billing", confidence=0.9, retry_count=ESCALATION_RETRY_LIMIT)
        assert route_after_triage(state) == "escalate"

    def test_boundary_confidence_routes_correctly(self):
        state = make_state(intent="technical", confidence=ESCALATION_CONFIDENCE_THRESHOLD, retry_count=0)
        assert route_after_triage(state) == "technical_agent"


class TestSpecialistRouting:
    def test_resolved_routes_to_synthesizer(self):
        state = make_state(escalated=False)
        assert route_after_specialist(state) == "synthesizer"

    def test_escalated_routes_to_escalate(self):
        state = make_state(escalated=True)
        assert route_after_specialist(state) == "escalate"
