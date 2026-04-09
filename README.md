# Multi-Agent Customer Support System


A production-grade multi-agent customer support system built with **LangGraph**, **Groq**, **Redis**, **FastAPI**, and **Streamlit**. Demonstrates agentic orchestration, tool-calling, persistent memory, guardrails, and human escalation.

---

## Architecture

```
User message
    │
    ▼
┌─────────────┐     PII redaction
│  Guardrails │ ──► topic filtering
└──────┬──────┘
       │
       ▼
┌─────────────┐     Intent classification
│    Triage   │ ──► confidence scoring
│    Agent    │     → billing / technical / returns / escalate
└──────┬──────┘
       │
  ┌────┴─────────────────┐
  ▼          ▼            ▼
Billing   Technical    Returns
 Agent      Agent       Agent
  │  tool-calling loop  │
  └────────┬────────────┘
           │
           ▼
    ┌─────────────┐
    │  Escalation │ ──► Human handoff (ticket + context dump)
    │    Check    │
    └──────┬──────┘
           │ resolved
           ▼
    ┌─────────────┐
    │ Synthesizer │  tone + format polish
    └──────┬──────┘
           │
           ▼
      Final response

Redis checkpointer persists full state per thread_id (multi-turn memory)
```

## Stack

| Layer | Technology |
|-------|-----------|
| Agent orchestration | LangGraph `StateGraph` |
| LLM | Groq `llama-3.1-8b-instant` |
| Memory | Redis via `langgraph-checkpoint-redis` |
| API | FastAPI |
| UI | Streamlit |
| Containerisation | Docker + docker-compose |

## Key Concepts Demonstrated

- **Typed state machine** — `AgentState` TypedDict flows through every node
- **Conditional routing** — intent + confidence + retry count drive edge decisions
- **Tool-calling loops** — each specialist runs up to 3 tool-call rounds before synthesising
- **PII redaction** — regex-based scrubbing before any LLM sees the message
- **Escalation logic** — confidence < 0.55 or retry ≥ 2 triggers human handoff with full context dump
- **Redis checkpointer** — full conversation state persists across API calls by `thread_id`
- **Graceful degradation** — Redis unavailable → falls back to `MemorySaver` automatically

## Project Structure

```
p6-multiagent-support/
├── agents/
│   ├── triage.py          # Intent classification → routing decision
│   ├── billing.py         # Billing specialist + tools
│   ├── technical.py       # Technical specialist + tools
│   ├── returns.py         # Returns specialist + tools
│   └── synthesizer.py     # Response formatter, human handoff, guardrail block
├── graph/
│   ├── state.py           # AgentState TypedDict
│   ├── edges.py           # Conditional edge functions
│   └── builder.py         # StateGraph assembly
├── memory/
│   └── redis_checkpointer.py   # Redis-backed checkpointer with fallback
├── guardrails/
│   └── input_guard.py     # PII redaction + topic filtering
├── tools/
│   ├── billing_tools.py   # Invoice lookup, refund, plan details
│   ├── tech_tools.py      # Docs search, known issues, ticket creation
│   └── returns_tools.py   # Order lookup, RMA, cancellation
├── api/
│   └── main.py            # FastAPI app
├── ui/
│   └── app.py             # Streamlit chat UI
├── tests/
│   └── test_graph.py      # Unit tests for routing + guardrails
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Setup & Running

### Prerequisites

- Python 3.11+
- Docker (for Redis)
- [Groq API key](https://console.groq.com)

### Local dev

```bash
# Clone and install
git clone https://github.com/Vedant-1404/multiagent-support-system.git
cd multiagent-support-system
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# Start API (terminal 1)
uvicorn api.main:app --reload --port 8000

# Start UI (terminal 2)
streamlit run ui/app.py
```

Open [http://localhost:8501](http://localhost:8501) for the chat UI, or [http://localhost:8000/docs](http://localhost:8000/docs) for the API playground.

### Docker (full stack)

```bash
docker-compose up --build
```

### Tests

```bash
pytest tests/ -v
```

## API Reference

### `POST /chat`

```json
{
  "message": "I was charged twice on invoice INV-001",
  "thread_id": "optional-uuid-for-continuity"
}
```

Response:
```json
{
  "response": "I looked into invoice INV-001...",
  "thread_id": "abc-123",
  "intent": "billing",
  "confidence": 0.94,
  "agent_used": "billing",
  "escalated": false,
  "ticket_id": ""
}
```

### `GET /health`

```json
{ "status": "ok", "graph_ready": true }
```

## Example Queries to Try

| Query | Expected routing |
|-------|-----------------|
| "I was charged twice for invoice INV-001" | Billing agent → invoice lookup |
| "My dashboard is loading very slowly" | Technical agent → known issues check |
| "I want to return order ORD-102" | Returns agent → RMA creation |
| "What's included in the Pro plan?" | Billing agent → plan details |
| "I can't log in, forgot my password" | Technical agent → docs search |
| "My item arrived damaged" | Returns agent → policy + RMA |
