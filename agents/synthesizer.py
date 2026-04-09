import os
import json
import logging
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import AgentState

logger = logging.getLogger(__name__)

SYNTHESIZER_PROMPT = """You are a customer support response formatter. 
You receive a draft response from a specialist agent and must:
1. Ensure the tone is warm, professional, and empathetic
2. Keep the response concise — remove repetition
3. Add a closing line offering further help
4. Do NOT add information that wasn't in the draft

Return only the final polished response, nothing else."""


def synthesizer_node(state: AgentState) -> AgentState:
    draft = state.get("agent_response", "")
    if not draft:
        return {**state, "final_response": "I'm sorry, I couldn't process your request. Please try again or contact us directly."}

    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.3,
    )

    try:
        response = llm.invoke([
            SystemMessage(content=SYNTHESIZER_PROMPT),
            HumanMessage(content=f"Draft response:\n{draft}"),
        ])
        final = response.content.strip()
        logger.info("Response synthesized successfully")
        return {**state, "final_response": final}

    except Exception as e:
        logger.error(f"Synthesizer error: {e}")
        return {**state, "final_response": draft}


def human_handoff_node(state: AgentState) -> AgentState:
    reason = state.get("escalation_reason", "Complex issue requiring specialist")
    intent = state.get("intent", "general")
    user_input = state.get("user_input", "")

    ticket_id = f"ESC-{hash(user_input + reason) % 90000 + 10000}"

    context_dump = {
        "ticket_id": ticket_id,
        "intent": intent,
        "escalation_reason": reason,
        "original_message": user_input[:200],
        "retry_count": state.get("retry_count", 0),
    }

    logger.info(f"Human handoff triggered: {json.dumps(context_dump)}")

    final_response = (
        f"I've escalated your request to our specialist team. "
        f"Your ticket number is **{ticket_id}**. "
        f"A team member will reach out within 2 business hours. "
        f"You can also reach us directly at support@example.com with your ticket number."
    )

    return {**state, "final_response": final_response, "escalated": True}


def guardrail_block_node(state: AgentState) -> AgentState:
    reason = state.get("guardrail_reason", "Policy violation")
    logger.warning(f"Guardrail block served to user: {reason}")

    final_response = (
        "I'm unable to process that request as it falls outside our support scope. "
        "If you have a question about your account, orders, or our product, I'm happy to help."
    )

    return {**state, "final_response": final_response}
