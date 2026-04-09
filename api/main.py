import os
import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)

from graph.builder import build_graph
from memory.redis_checkpointer import get_checkpointer

graph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global graph
    checkpointer = get_checkpointer()
    graph = build_graph(checkpointer=checkpointer)
    logger.info("Multi-agent graph initialised")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="P6 Multi-Agent Customer Support",
    description="LangGraph-powered multi-agent support system with triage, specialists, and escalation",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    thread_id: str = ""


class ChatResponse(BaseModel):
    response: str
    thread_id: str
    intent: str = "blocked"
    confidence: float = 0.0
    agent_used: str = "guardrail"
    escalated: bool = False
    ticket_id: str = ""


@app.get("/health")
async def health():
    return {"status": "ok", "graph_ready": graph is not None}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not graph:
        raise HTTPException(status_code=503, detail="Graph not initialised")

    thread_id = request.thread_id or str(uuid.uuid4())

    initial_state = {
        "messages": [],
        "thread_id": thread_id,
        "user_input": request.message,
        "intent": "unknown",
        "confidence": 0.0,
        "assigned_agent": "unknown",
    }

    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = graph.invoke(initial_state, config=config)

        final = result.get("final_response", "No response generated.")
        ticket = ""
        if result.get("escalated") and "ESC-" in final:
            import re
            m = re.search(r"ESC-\d+", final)
            if m:
                ticket = m.group()

        return ChatResponse(
            response=final,
            thread_id=thread_id,
            intent=result.get("intent", "unknown"),
            confidence=result.get("confidence", 0.0),
            agent_used=result.get("assigned_agent", "unknown"),
            escalated=result.get("escalated", False),
            ticket_id=ticket,
        )

    except Exception as e:
        logger.error(f"Graph invocation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {
        "project": "P6 Multi-Agent Customer Support",
        "docs": "/docs",
        "health": "/health",
    }
