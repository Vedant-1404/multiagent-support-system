import os
import logging
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from graph.state import AgentState
from tools.tech_tools import TECHNICAL_TOOLS

logger = logging.getLogger(__name__)

TECHNICAL_SYSTEM_PROMPT = """You are a specialist technical support agent. You have access to tools to:
- Search product documentation
- Check known issues and workarounds
- Create support tickets for complex problems
- Check system status

Be precise, use technical language appropriately for the user's level, and always check documentation
and known issues before suggesting workarounds. If an issue is complex or requires account access,
create a support ticket. Never guess at solutions — use your tools."""


def technical_node(state: AgentState) -> AgentState:
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.2,
    ).bind_tools(TECHNICAL_TOOLS)

    messages = [
        SystemMessage(content=TECHNICAL_SYSTEM_PROMPT),
        HumanMessage(content=state["user_input"]),
    ]

    try:
        response = llm.invoke(messages)
        messages.append(response)

        max_tool_rounds = 3
        rounds = 0

        while response.tool_calls and rounds < max_tool_rounds:
            rounds += 1
            tool_map = {t.name: t for t in TECHNICAL_TOOLS}
            for tc in response.tool_calls:
                tool_fn = tool_map.get(tc["name"])
                if tool_fn:
                    result = tool_fn.invoke(tc["args"])
                    messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
                    logger.info(f"Technical tool {tc['name']} called → {str(result)[:80]}")

            response = llm.invoke(messages)
            messages.append(response)

        final_answer = response.content
        escalate = any(phrase in final_answer.lower() for phrase in [
            "cannot resolve", "escalat", "human agent", "account access required"
        ])

        return {
            **state,
            "agent_response": final_answer,
            "escalated": escalate,
            "escalation_reason": "Technical issue requires human intervention" if escalate else None,
        }

    except Exception as e:
        logger.error(f"Technical agent error: {e}")
        return {
            **state,
            "agent_response": "I ran into an issue diagnosing your technical problem. Connecting you to our technical team.",
            "escalated": True,
            "escalation_reason": f"Technical agent exception: {str(e)}",
        }
