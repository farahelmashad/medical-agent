import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.agent import chat
from langchain_core.messages import HumanMessage, AIMessage

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Cairo Medical Center — AI Receptionist",
    description="Medical appointment booking agent powered by LangGraph",
    version="1.0.0",
)

# Allow Streamlit frontend to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Session storage (in-memory) ───────────────────────────────────────────────
# Maps session_id → list of LangChain messages
sessions: dict = {}


# ── Request / Response models ─────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    session_id: str


class ChatResponse(BaseModel):
    reply: str
    session_id: str


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "Cairo Medical Center AI Receptionist is running"}


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    # Get or create session history
    history = sessions.get(request.session_id, [])

    # Run the agent
    reply, updated_history = chat(request.message, history)

    # Save updated history back to session
    sessions[request.session_id] = updated_history

    return ChatResponse(reply=reply, session_id=request.session_id)


@app.delete("/session/{session_id}")
def clear_session(session_id: str):
    """Clear conversation history for a session (e.g. when patient closes chat)."""
    if session_id in sessions:
        del sessions[session_id]
    return {"status": "session cleared", "session_id": session_id}


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)