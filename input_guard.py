import re
import os
import json
import logging
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

from graph.state import AgentState

logger = logging.getLogger(__name__)

BLOCKED_TOPICS = [
    "how to hack", "exploit", "illegal", "bomb", "weapon",
    "jailbreak", "ignore previous instructions",
]

PII_PATTERNS = {
    "credit_card": r"\b(?:\d{4}[\s\-]?){3}\d{4}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone": r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
}

PII_REPLACEMENTS = {
    "credit_card": "[CARD-REDACTED]",
    "ssn": "[SSN-REDACTED]",
    "email": "[EMAIL-REDACTED]",
    "phone": "[PHONE-REDACTED]",
}


def redact_pii(text: str) -> tuple[str, list[str]]:
    redacted = text
    found = []
    for pii_type, pattern in PII_PATTERNS.items():
        if re.search(pattern, redacted):
            redacted = re.sub(pattern, PII_REPLACEMENTS[pii_type], redacted)
            found.append(pii_type)
    return redacted, found


def check_blocked_topics(text: str) -> tuple[bool, str]:
    text_lower = text.lower()
    for topic in BLOCKED_TOPICS:
        if topic in text_lower:
            return True, f"Blocked topic detected: '{topic}'"
    return False, ""


def guardrail_node(state: AgentState) -> AgentState:
    user_input = state["user_input"]

    is_blocked, block_reason = check_blocked_topics(user_input)
    if is_blocked:
        logger.warning(f"Guardrail blocked message: {block_reason}")
        return {
            **state,
            "guardrail_triggered": True,
            "guardrail_reason": block_reason,
        }

    cleaned_input, pii_found = redact_pii(user_input)
    if pii_found:
        logger.info(f"PII redacted: {pii_found}")

    return {
        **state,
        "user_input": cleaned_input,
        "guardrail_triggered": False,
        "guardrail_reason": None,
    }
