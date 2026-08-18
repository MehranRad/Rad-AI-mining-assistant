"""
FastAPI wrapper around existing agent.py / chat_storage.py logic.
This file does NOT reimplement any business logic — it only exposes
the existing functions as HTTP endpoints for the Next.js frontend.

SECURITY: role/username/user_id are NEVER trusted from the request body
or URL — they are derived exclusively from a verified JWT issued at
login. This closes a real vulnerability where a client could edit
localStorage to claim any role (e.g. "manager") and bypass RBAC.
"""
import os
import time
import json
import jwt
import datetime
from collections import defaultdict
from fastapi import FastAPI, HTTPException, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv

from agent import ask_question, ask_question_stream, db
from schema_constants import STATUS_RUNNING
from chat_storage import (
    init_chat_tables, create_session, save_message,
    list_sessions, load_messages, delete_session, is_session_owner,
    init_user_table, authenticate_user, list_audit_log
)

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is not set in .env — required for authentication.")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 8

# ----- Simple in-memory login throttling -----
# Purpose: slow down brute-force password guessing without ever locking a
# legitimate user out permanently. After LOGIN_MAX_ATTEMPTS failed attempts
# for one username within LOGIN_WINDOW_SECONDS, further attempts are rejected
# with HTTP 429 for LOGIN_LOCKOUT_SECONDS. A successful login resets the count.
LOGIN_ATTEMPTS = defaultdict(list)  # username -> list of failure timestamps
LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 300
LOGIN_LOCKOUT_SECONDS = 60


def _login_throttle_wait(username: str) -> float:
    """Seconds the caller must wait before retrying, or 0.0 if allowed now."""
    now = time.time()
    recent = [t for t in LOGIN_ATTEMPTS.get(username, []) if now - t < LOGIN_WINDOW_SECONDS]
    LOGIN_ATTEMPTS[username] = recent
    if len(recent) >= LOGIN_MAX_ATTEMPTS:
        return LOGIN_LOCKOUT_SECONDS
    return 0.0

app = FastAPI(title="Rad AI API")

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_chat_tables()
init_user_table()

security_scheme = HTTPBearer()


def create_access_token(user_id: int, username: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=TOKEN_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> dict:
    """
    Verifies the JWT and returns its payload. This is the ONLY source of
    truth for who the caller is — every protected endpoint below uses
    this instead of trusting anything the client sent in the body/URL.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="نشست شما منقضی شده است. دوباره وارد شوید.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="توکن نامعتبر است.")


def require_matching_user(user_id: int, current_user: dict = Depends(get_current_user)) -> dict:
    """
    Extra IDOR guard for the session endpoints below, which still take
    user_id as a URL path parameter (kept for minimal disruption to the
    existing route shapes) — this verifies the path's user_id actually
    matches the authenticated token's user_id, so no user can read/
    delete another user's sessions by guessing/editing the URL.
    """
    if current_user["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="دسترسی غیرمجاز.")
    return current_user


# ---------- Request/response models ----------
class LoginRequest(BaseModel):
    username: str
    password: str

class AskRequest(BaseModel):
    question: str
    history: Optional[List[dict]] = None

class CreateSessionRequest(BaseModel):
    title: str

class SaveMessageRequest(BaseModel):
    session_id: str
    role: str
    content: str
    steps: Optional[List[dict]] = None


# ---------- Auth ----------
@app.post("/api/login")
def login(payload: LoginRequest, response: Response):
    username = payload.username.strip()
    wait = _login_throttle_wait(username)
    if wait > 0:
        response.status_code = 429
        response.headers["Retry-After"] = str(int(wait))
        return {"detail": "تلاش‌های ناموفق زیاد است. لطفاً کمی بعد دوباره تلاش کنید."}
    result = authenticate_user(username, payload.password)
    if result is None:
        LOGIN_ATTEMPTS[username].append(time.time())
        raise HTTPException(status_code=401, detail="نام کاربری یا رمز عبور اشتباه است.")
    LOGIN_ATTEMPTS.pop(username, None)
    token = create_access_token(result["user_id"], result["username"], result["role"])
    return {"token": token, "user": result}


# ---------- Chat / AI ----------
@app.post("/api/ask")
def ask(payload: AskRequest, current_user: dict = Depends(get_current_user)):
    try:
        result = ask_question(
            payload.question,
            role=current_user["role"],
            username=current_user["username"],
            history=payload.history,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ask/stream")
def ask_stream(payload: AskRequest, current_user: dict = Depends(get_current_user)):
    def event_generator():
        for event in ask_question_stream(
            payload.question,
            role=current_user["role"],
            username=current_user["username"],
            history=payload.history,
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ---------- Sessions ----------
@app.get("/api/sessions/{user_id}")
def get_sessions(user_id: int, current_user: dict = Depends(require_matching_user)):
    return list_sessions(user_id=user_id)

@app.get("/api/sessions/{user_id}/{session_id}/messages")
def get_messages(user_id: int, session_id: str, current_user: dict = Depends(require_matching_user)):
    return load_messages(session_id, user_id=user_id)

@app.post("/api/sessions")
def new_session(payload: CreateSessionRequest, current_user: dict = Depends(get_current_user)):
    session_id = create_session(payload.title, user_id=current_user["user_id"])
    return {"session_id": session_id}

@app.post("/api/sessions/message")
def add_message(payload: SaveMessageRequest, current_user: dict = Depends(get_current_user)):
    if not is_session_owner(payload.session_id, current_user["user_id"]):
        raise HTTPException(status_code=403, detail="دسترسی غیرمجاز.")
    save_message(payload.session_id, payload.role, payload.content, payload.steps)
    return {"status": "ok"}

@app.delete("/api/sessions/{user_id}/{session_id}")
def remove_session(user_id: int, session_id: str, current_user: dict = Depends(require_matching_user)):
    delete_session(session_id, user_id=user_id)
    return {"status": "ok"}


# ---------- Snapshot stats (for KPI cards) ----------
@app.get("/api/stats")
def get_stats(current_user: dict = Depends(get_current_user)):
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
        "running": _first_value(db.run(f"SELECT COUNT(*) FROM Equipment WHERE Status='{STATUS_RUNNING}'")),
        "recovery": _first_value(db.run("SELECT AVG(RecoveryRate) FROM Production")),
    }


# ---------- Audit (manager-only) ----------
@app.get("/api/audit")
def audit_log(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "manager":
        raise HTTPException(status_code=403, detail="فقط مدیران می‌توانند گزارش امنیت را مشاهده کنند.")
    limit = 100
    return list_audit_log(limit=limit)