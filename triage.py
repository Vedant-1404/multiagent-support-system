import os
import json
import logging
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import AgentState

logger = logging.getLogger(__name__)

TRIAGE_SYSTEM_PROMPT = """You are a customer support triage agent. Your job is to classify customer queries.

Classify the user's message into exactly one of these categories:
- billing: questions about invoices, payments, refunds, subscription plans, charges
- technical: bugs, errors, setup issues, feature questions, troubleshooting
- returns: return requests, exchange, damaged goods, order cancellations, delivery issues
- general: everything else

Respond ONLY with a JSON object, no markdown, no explanation:
{
  "intent": "<category>",
  "confidence": <float between 0.0 and 1.0>,
  "reasoning": "<one sentence>"
}"""


def triage_node(state: AgentState) -> AgentState:
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.1,
    )

    messages = [
        SystemMessage(content=TRIAGE_SYSTEM_PROMPT),
        HumanMessage(content=state["user_input"]),
    ]

    try:
        response = llm.invoke(messages)
        raw = response.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw)

        intent = parsed.get("intent", "general")
        confidence = float(parsed.get("confidence", 0.5))
        reasoning = parsed.get("reasoning", "")

        logger.info(f"Triage → intent={intent}, confidence={confidence:.2f}, reason={reasoning}")

        return {
            **state,
            "intent": intent,
            "confidence": confidence,
            "assigned_agent": intent,
        }

    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Triage parsing failed: {e}")
        return {
            **state,
            "intent": "general",
            "confidence": 0.4,
            "assigned_agent": "technical_agent",
        }
