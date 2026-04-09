import os
import logging
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from graph.state import AgentState
from tools.returns_tools import RETURNS_TOOLS

logger = logging.getLogger(__name__)

RETURNS_SYSTEM_PROMPT = """You are a specialist returns and order support agent. You have access to tools to:
- Look up order details
- Check return policies for different item types
- Create Return Merchandise Authorizations (RMAs)
- Cancel unshipped orders

Always look up the order first, check the applicable return policy, then proceed with the action.
Be empathetic with customers who received damaged or wrong items. Be clear about timelines and next steps."""


def returns_node(state: AgentState) -> AgentState:
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.2,
    ).bind_tools(RETURNS_TOOLS)

    messages = [
        SystemMessage(content=RETURNS_SYSTEM_PROMPT),
        HumanMessage(content=state["user_input"]),
    ]

    try:
        response = llm.invoke(messages)
        messages.append(response)

        max_tool_rounds = 3
        rounds = 0

        while response.tool_calls and rounds < max_tool_rounds:
            rounds += 1
            tool_map = {t.name: t for t in RETURNS_TOOLS}
            for tc in response.tool_calls:
                tool_fn = tool_map.get(tc["name"])
                if tool_fn:
                    result = tool_fn.invoke(tc["args"])
                    messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
                    logger.info(f"Returns tool {tc['name']} called → {str(result)[:80]}")

            response = llm.invoke(messages)
            messages.append(response)

        final_answer = response.content
        escalate = any(phrase in final_answer.lower() for phrase in [
            "cannot resolve", "escalat", "human agent", "manager", "dispute"
        ])

        return {
            **state,
            "agent_response": final_answer,
            "escalated": escalate,
            "escalation_reason": "Returns issue requires human review" if escalate else None,
        }

    except Exception as e:
        logger.error(f"Returns agent error: {e}")
        return {
            **state,
            "agent_response": "I encountered an issue processing your return request. Let me connect you with our returns team.",
            "escalated": True,
            "escalation_reason": f"Returns agent exception: {str(e)}",
        }
