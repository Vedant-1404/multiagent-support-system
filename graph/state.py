from typing import TypedDict, List, Optional, Annotated
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    thread_id: str
    user_input: str
    intent: Optional[str]
    confidence: Optional[float]
    assigned_agent: Optional[str]
    agent_response: Optional[str]
    retry_count: int
    escalated: bool
    escalation_reason: Optional[str]
    final_response: Optional[str]
    guardrail_triggered: bool
    guardrail_reason: Optional[str]
