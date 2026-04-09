from graph.state import AgentState


ESCALATION_CONFIDENCE_THRESHOLD = 0.55
ESCALATION_RETRY_LIMIT = 2


def route_after_guardrail(state: AgentState) -> str:
    if state.get("guardrail_triggered"):
        return "guardrail_block"
    return "triage"


def route_after_triage(state: AgentState) -> str:
    intent = state.get("intent", "general")
    confidence = state.get("confidence", 0.0)
    retry_count = state.get("retry_count", 0)

    if confidence < ESCALATION_CONFIDENCE_THRESHOLD or retry_count >= ESCALATION_RETRY_LIMIT:
        return "escalate"

    routing_map = {
        "billing": "billing_agent",
        "technical": "technical_agent",
        "returns": "returns_agent",
        "general": "technical_agent",
    }
    return routing_map.get(intent, "technical_agent")


def route_after_specialist(state: AgentState) -> str:
    if state.get("escalated"):
        return "escalate"
    return "synthesizer"


def route_after_escalation_check(state: AgentState) -> str:
    if state.get("escalated"):
        return "human_handoff"
    return "synthesizer"
