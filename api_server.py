"""
FastAPI wrapper around existing agent.py / chat_storage.py logic.
This file does NOT reimplement any business logic — it only exposes
the existing functions as HTTP endpoints for the Next.js frontend.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import json

from agent import ask_question, ask_question_stream, db
from chat_storage import (
    init_chat_tables, create_session, save_message,
    list_sessions, load_messages, delete_session,
    init_user_table, authenticate_user
)

app = FastAPI(title="Rad AI API")

# Allow the Next.js dev server to call this API.
# When you deploy for real, replace "*" with your actual frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_chat_tables()
init_user_table()


# ---------- Request/response models ----------
class LoginRequest(BaseModel):
    username: str
    password: str

class AskRequest(BaseModel):
    question: str
    role: str
    username: str
    history: Optional[List[dict]] = None

class CreateSessionRequest(BaseModel):
    title: str
    user_id: int

class SaveMessageRequest(BaseModel):
    session_id: str
    role: str
    content: str
    steps: Optional[List[dict]] = None


# ---------- Auth ----------
@app.post("/api/login")
def login(payload: LoginRequest):
    result = authenticate_user(payload.username.strip(), payload.password)
    if result is None:
        raise HTTPException(status_code=401, detail="نام کاربری یا رمز عبور اشتباه است.")
    return result


# ---------- Chat / AI ----------
@app.post("/api/ask")
def ask(payload: AskRequest):
    try:
        result = ask_question(
            payload.question,
            role=payload.role,
            username=payload.username,
            history=payload.history,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ask/stream")
def ask_stream(payload: AskRequest):
    def event_generator():
        for event in ask_question_stream(
            payload.question,
            role=payload.role,
            username=payload.username,
            history=payload.history,
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# ---------- Sessions ----------
@app.get("/api/sessions/{user_id}")
def get_sessions(user_id: int):
    return list_sessions(user_id=user_id)

@app.get("/api/sessions/{user_id}/{session_id}/messages")
def get_messages(user_id: int, session_id: str):
    return load_messages(session_id, user_id=user_id)

@app.post("/api/sessions")
def new_session(payload: CreateSessionRequest):
    session_id = create_session(payload.title, user_id=payload.user_id)
    return {"session_id": session_id}

@app.post("/api/sessions/message")
def add_message(payload: SaveMessageRequest):
    save_message(payload.session_id, payload.role, payload.content, payload.steps)
    return {"status": "ok"}

@app.delete("/api/sessions/{user_id}/{session_id}")
def remove_session(user_id: int, session_id: str):
    delete_session(session_id, user_id=user_id)
    return {"status": "ok"}


# ---------- Snapshot stats (for KPI cards) ----------
@app.get("/api/stats")
def get_stats():
    import ast
    def _first_value(raw):
        try:
            parsed = ast.literal_eval(raw) if isinstance(raw, str) else raw
            return parsed[0][0]
        except Exception:
            return None
    return {
        "employees": _first_value(db.run("SELECT COUNT(*) FROM Employees")),
        "equipment": _first_value(db.run("SELECT COUNT(*) FROM Equipment")),
        "running": _first_value(db.run("SELECT COUNT(*) FROM Equipment WHERE Status='Running'")),
        "recovery": _first_value(db.run("SELECT AVG(RecoveryRate) FROM Production")),
    }