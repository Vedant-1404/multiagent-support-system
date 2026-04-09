import streamlit as st
import requests
import uuid

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Support Assistant",
    page_icon="🤖",
    layout="wide",
)

st.title("Customer Support Assistant")
st.caption("Powered by LangGraph multi-agent system — P6 AI Portfolio")

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_meta" not in st.session_state:
    st.session_state.last_meta = {}
if "pending_input" not in st.session_state:
    st.session_state.pending_input = None

col_chat, col_meta = st.columns([3, 1])

with col_chat:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = None
    if st.session_state.pending_input:
        prompt = st.session_state.pending_input
        st.session_state.pending_input = None

    last_msg = st.session_state.messages[-1]["content"] if st.session_state.messages else ""
    needs_followup = any(phrase in last_msg.lower() for phrase in [
        "could you", "please provide", "can you share", "reason for", "order number"
    ])
    placeholder = "Type your reply here..." if needs_followup else "Ask about billing, technical issues, or returns..."

    if user_input := st.chat_input(placeholder):
        prompt = user_input

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    resp = requests.post(
                        f"{API_URL}/chat",
                        json={"message": prompt, "thread_id": st.session_state.thread_id},
                        timeout=30,
                    )
                    data = resp.json()
                    answer = data.get("response", "Sorry, something went wrong.")
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    st.session_state.last_meta = data
                except requests.exceptions.ConnectionError:
                    err = "Cannot connect to API. Make sure the FastAPI server is running on port 8000."
                    st.error(err)
                    st.session_state.messages.append({"role": "assistant", "content": err})
                except Exception as e:
                    st.error(f"Error: {e}")

with col_meta:
    st.subheader("Agent trace")

    thread_display = st.session_state.thread_id[:8] + "..."
    st.caption(f"Thread: `{thread_display}`")

    if st.session_state.last_meta:
        meta = st.session_state.last_meta
        intent = meta.get("intent", "—")
        confidence = meta.get("confidence", 0)
        agent = meta.get("agent_used", "—")
        escalated = meta.get("escalated", False)
        ticket = meta.get("ticket_id", "")

        st.metric("Intent", intent.title() if intent else "—")
        st.metric("Confidence", f"{confidence:.0%}" if confidence else "—")
        st.metric("Agent", agent.replace("_", " ").title() if agent else "—")

        if escalated:
            st.error("Escalated to human")
            if ticket:
                st.code(ticket)
        else:
            st.success("Resolved by AI")
    else:
        st.info("Send a message to see routing details")

    st.divider()

    if st.button("New conversation", use_container_width=True):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.last_meta = {}
        st.rerun()

    st.subheader("Try these")
    examples = [
        "I was charged twice for invoice INV-001",
        "My dashboard is loading very slowly",
        "I want to return order ORD-102",
        "What's included in the Pro plan?",
        "I can't log in — forgot my password",
        "My item arrived damaged",
    ]
    if not st.session_state.messages:
        for ex in examples:
            if st.button(ex, use_container_width=True, key=ex):
                st.session_state.pending_input = ex
                st.rerun()
    else:
        st.caption("Type your reply in the chat input below")