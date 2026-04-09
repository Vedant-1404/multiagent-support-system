from langgraph.graph import StateGraph, END

from graph.state import AgentState
from graph.edges import (
    route_after_guardrail,
    route_after_triage,
    route_after_specialist,
)
from guardrails.input_guard import guardrail_node
from agents.triage import triage_node
from agents.billing import billing_node
from agents.technical import technical_node
from agents.returns import returns_node
from agents.synthesizer import synthesizer_node, guardrail_block_node, human_handoff_node


def build_graph(checkpointer=None):
    builder = StateGraph(AgentState)

    builder.add_node("guardrail", guardrail_node)
    builder.add_node("triage", triage_node)
    builder.add_node("billing_agent", billing_node)
    builder.add_node("technical_agent", technical_node)
    builder.add_node("returns_agent", returns_node)
    builder.add_node("synthesizer", synthesizer_node)
    builder.add_node("human_handoff", human_handoff_node)
    builder.add_node("guardrail_block", guardrail_block_node)

    builder.set_entry_point("guardrail")

    builder.add_conditional_edges(
        "guardrail",
        route_after_guardrail,
        {
            "triage": "triage",
            "guardrail_block": "guardrail_block",
        },
    )

    builder.add_conditional_edges(
        "triage",
        route_after_triage,
        {
            "billing_agent": "billing_agent",
            "technical_agent": "technical_agent",
            "returns_agent": "returns_agent",
            "escalate": "human_handoff",
        },
    )

    for specialist in ["billing_agent", "technical_agent", "returns_agent"]:
        builder.add_conditional_edges(
            specialist,
            route_after_specialist,
            {
                "escalate": "human_handoff",
                "synthesizer": "synthesizer",
            },
        )

    builder.add_edge("synthesizer", END)
    builder.add_edge("human_handoff", END)
    builder.add_edge("guardrail_block", END)

    return builder.compile(checkpointer=checkpointer)
