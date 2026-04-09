import os
import logging
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage

from graph.state import AgentState
from tools.billing_tools import BILLING_TOOLS

logger = logging.getLogger(__name__)

BILLING_SYSTEM_PROMPT = """You are a specialist billing support agent. You have access to tools to:
- Look up invoices
- Check subscription plan details
- Process refund requests
- Review billing history

Be concise, professional, and accurate. Always use tools to verify information before responding.
If you cannot resolve the issue with available tools, say so clearly and recommend escalation.
Never make up invoice numbers, amounts, or account details."""


def billing_node(state: AgentState) -> AgentState:
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.2,
    ).bind_tools(BILLING_TOOLS)

    messages = [
        SystemMessage(content=BILLING_SYSTEM_PROMPT),
        HumanMessage(content=state["user_input"]),
    ]

    try:
        response = llm.invoke(messages)
        messages.append(response)

        max_tool_rounds = 3
        rounds = 0

        while response.tool_calls and rounds < max_tool_rounds:
            rounds += 1
            tool_map = {t.name: t for t in BILLING_TOOLS}
            for tc in response.tool_calls:
                tool_fn = tool_map.get(tc["name"])
                if tool_fn:
                    result = tool_fn.invoke(tc["args"])
                    messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
                    logger.info(f"Billing tool {tc['name']} called → {str(result)[:80]}")

            response = llm.invoke(messages)
            messages.append(response)

        final_answer = response.content
        escalate = any(phrase in final_answer.lower() for phrase in [
            "cannot resolve", "escalat", "human agent", "beyond my ability"
        ])

        return {
            **state,
            "agent_response": final_answer,
            "escalated": escalate,
            "escalation_reason": "Billing issue unresolvable by automation" if escalate else None,
        }

    except Exception as e:
        logger.error(f"Billing agent error: {e}")
        return {
            **state,
            "agent_response": "I encountered an issue processing your billing query. Let me connect you with a specialist.",
            "escalated": True,
            "escalation_reason": f"Billing agent exception: {str(e)}",
        }
