"""
Handles persistent chat storage using the same MySQL database as the AI agent.
This is completely separate from the AI's SQL tool in agent.py: here we
write our OWN trusted, hardcoded SQL (not LLM-generated).
"""
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import json
import uuid
from datetime import datetime

from auth import hash_password, verify_password

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

connection_string = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    f"?connect_timeout=10"
)

# pool_pre_ping=True: before reusing a pooled connection, SQLAlchemy checks
# it's still alive. Without this, a connection that the database server
# silently closed while idle (very common behavior in managed MySQL services
# to save resources) gets reused anyway, causing exactly the
# "[WinError 10054] An existing connection was forcibly closed by the
# remote host" error we just hit — the chat UI sits idle between questions,
# which is exactly the scenario that triggers this.
# pool_recycle=280: proactively replaces connections older than ~4.5 minutes,
# before the server has a chance to drop them on its own.
storage_engine = create_engine(connection_string, pool_pre_ping=True, pool_recycle=280)


def init_chat_tables():
    """Creates the two chat-history tables if they don't already exist."""
    with storage_engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ChatSessions (
                SessionID VARCHAR(36) PRIMARY KEY,
                UserID BIGINT,
                Title VARCHAR(255),
                CreatedAt DATETIME
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ChatMessages (
                MessageID BIGINT AUTO_INCREMENT PRIMARY KEY,
                SessionID VARCHAR(36),
                Role VARCHAR(20),
                Content MEDIUMTEXT,
                StepsJSON MEDIUMTEXT,
                CreatedAt DATETIME
            )
        """))
        # Existing ChatSessions table (created before this change) won't
        # have UserID yet. Add it if missing — safe to run repeatedly.
        try:
            conn.execute(text("ALTER TABLE ChatSessions ADD COLUMN UserID BIGINT"))
        except Exception:
            pass  # column already exists


def create_session(first_message: str, user_id: int) -> str:
    """Creates a new chat session, using the first message as its title."""
    session_id = str(uuid.uuid4())
    title = first_message.strip()
    if len(title) > 60:
        title = title[:57] + "..."

    with storage_engine.begin() as conn:
        conn.execute(
            text("""INSERT INTO ChatSessions (SessionID, UserID, Title, CreatedAt)
                     VALUES (:sid, :uid, :title, :created)"""),
            {"sid": session_id, "uid": user_id, "title": title, "created": datetime.now()}
        )
    return session_id


def save_message(session_id: str, role: str, content: str, steps=None):
    """Saves a single message (user or assistant) into a session."""
    steps_json = json.dumps(steps or [], ensure_ascii=False)
    with storage_engine.begin() as conn:
        conn.execute(
            text("""INSERT INTO ChatMessages (SessionID, Role, Content, StepsJSON, CreatedAt)
                     VALUES (:sid, :role, :content, :steps, :created)"""),
            {"sid": session_id, "role": role, "content": content, "steps": steps_json, "created": datetime.now()}
        )


def list_sessions(user_id: int, limit=30):
    """Returns past chat sessions belonging to ONE user, most recent first."""
    with storage_engine.connect() as conn:
        rows = conn.execute(
            text("""SELECT SessionID, Title, CreatedAt FROM ChatSessions
                     WHERE UserID = :uid ORDER BY CreatedAt DESC LIMIT :lim"""),
            {"uid": user_id, "lim": limit}
        ).fetchall()
    return [{"session_id": r[0], "title": r[1], "created_at": r[2]} for r in rows]


def load_messages(session_id: str, user_id: int):
    """
    Loads all messages of a specific session, in chronological order.
    IDOR guard: first verifies the session actually belongs to user_id —
    a user must not be able to read another user's messages even by
    guessing/supplying another session's SessionID.
    """
    owner_id = get_session_owner(session_id)
    if owner_id is None or owner_id != user_id:
        return []

    with storage_engine.connect() as conn:
        rows = conn.execute(
            text("SELECT Role, Content, StepsJSON FROM ChatMessages WHERE SessionID=:sid ORDER BY MessageID ASC"),
            {"sid": session_id}
        ).fetchall()

    messages = []
    for r in rows:
        try:
            steps = json.loads(r[2]) if r[2] else []
        except Exception:
            steps = []
        messages.append({"role": r[0], "content": r[1], "steps": steps})
    return messages


def delete_session(session_id: str, user_id: int):
    """
    Deletes a session and all of its messages.
    IDOR guard: only deletes if the session actually belongs to user_id.
    """
    owner_id = get_session_owner(session_id)
    if owner_id is None or owner_id != user_id:
        return
    with storage_engine.begin() as conn:
        conn.execute(text("DELETE FROM ChatMessages WHERE SessionID=:sid"), {"sid": session_id})
        conn.execute(text("DELETE FROM ChatSessions WHERE SessionID=:sid"), {"sid": session_id})


def get_session_owner(session_id: str):
    """
    Returns the UserID that owns the given session, or None if no such
    session exists. Single source of truth for the ownership lookup used
    by is_session_owner / load_messages / delete_session.
    """
    with storage_engine.connect() as conn:
        row = conn.execute(
            text("SELECT UserID FROM ChatSessions WHERE SessionID = :sid"),
            {"sid": session_id}
        ).fetchone()
    return row[0] if row is not None else None


def is_session_owner(session_id: str, user_id: int) -> bool:
    """
    Returns True only if the given session exists AND belongs to user_id.
    Used to authorize message writes to a session (IDOR guard, matching the
    checks already done in load_messages/delete_session).
    """
    owner_id = get_session_owner(session_id)
    return owner_id is not None and owner_id == user_id


# ============================================================
# USER AUTHENTICATION / RBAC TABLE
# New in this step. Purely additive — nothing above this line changed.
# Roles: "staff", "supervisor", "manager" (see project design notes).
# Role is only ever set here, at account-creation time by an admin —
# never taken from question text or user-typed claims in the chat.
# ============================================================

VALID_ROLES = ("staff", "supervisor", "manager")


def init_user_table():
    """Creates the AppUsers table if it doesn't already exist."""
    with storage_engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS AppUsers (
                UserID BIGINT AUTO_INCREMENT PRIMARY KEY,
                Username VARCHAR(50) UNIQUE NOT NULL,
                PasswordHash VARCHAR(255) NOT NULL,
                Role VARCHAR(20) NOT NULL,
                CreatedAt DATETIME
            )
        """))


def create_user(username: str, password: str, role: str) -> bool:
    """
    Creates a new user with a PBKDF2-hashed password (via auth.hash_password).
    Returns True on success, False if the username already exists or the
    insert otherwise fails. Raises ValueError if role is not one of
    VALID_ROLES (fail loudly on a programming mistake, don't silently store
    a bad role).
    """
    if role not in VALID_ROLES:
        raise ValueError(f"Invalid role '{role}'. Must be one of {VALID_ROLES}")

    password_hash = hash_password(password)
    try:
        with storage_engine.begin() as conn:
            conn.execute(
                text("""INSERT INTO AppUsers (Username, PasswordHash, Role, CreatedAt)
                         VALUES (:username, :pwhash, :role, :created)"""),
                {"username": username, "pwhash": password_hash, "role": role, "created": datetime.now()}
            )
        return True
    except Exception as e:
        print(f"[create_user] Failed to create user '{username}': {e}")
        return False


def get_user_by_username(username: str):
    """
    Returns {user_id, username, password_hash, role} for the given username,
    or None if no such user exists. password_hash is included here because
    this function is meant for internal use by the login-verification logic
    (which will call auth.verify_password on it) — it is never sent to the UI.
    """
    with storage_engine.connect() as conn:
        row = conn.execute(
            text("SELECT UserID, Username, PasswordHash, Role FROM AppUsers WHERE Username=:username"),
            {"username": username}
        ).fetchone()
    if row is None:
        return None
    return {"user_id": row[0], "username": row[1], "password_hash": row[2], "role": row[3]}

def authenticate_user(username: str, password: str):
    """
    Verifies a username/password pair. Returns a safe user dict
    {user_id, username, role} on success (WITHOUT the password hash),
    or None if the username doesn't exist or the password is wrong.
    This is the ONLY place role is ever derived from — never from
    question text or anything typed into the chat itself.
    """
    user = get_user_by_username(username)
    if user is None:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return {"user_id": user["user_id"], "username": user["username"], "role": user["role"]}

def list_users():
    """Returns all users WITHOUT password hashes — for admin/debugging use only."""
    with storage_engine.connect() as conn:
        rows = conn.execute(
            text("SELECT UserID, Username, Role, CreatedAt FROM AppUsers ORDER BY UserID ASC")
        ).fetchall()
    return [{"user_id": r[0], "username": r[1], "role": r[2], "created_at": r[3]} for r in rows]

# ============================================================
# AUDIT LOG
# New in this step. Purely additive.
# Records WHO asked WHAT CATEGORY of question and WHEN. For
# confidential/individual-data questions, the full question text is
# intentionally NOT stored here (per the project's data-minimization
# goals) — only the category and metadata are logged.
# ============================================================

def init_audit_table():
    """Creates the AuditLog table if it doesn't already exist."""
    with storage_engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS AuditLog (
                LogID BIGINT AUTO_INCREMENT PRIMARY KEY,
                Username VARCHAR(50),
                Role VARCHAR(20),
                QuestionCategory VARCHAR(50),
                QuestionText MEDIUMTEXT,
                WasBlocked BOOLEAN,
                CreatedAt DATETIME
            )
        """))


# Categories for which we deliberately do NOT persist the raw question
# text, even though the category itself is logged. Anything touching
# individual employee data is considered sensitive enough to keep out
# of long-term storage, whether it was allowed (manager) or blocked
# (staff/supervisor).
CONFIDENTIAL_CATEGORIES = {"INDIVIDUAL_PERSONAL_DATA", "ROLE_RESTRICTED_SALARY"}


def log_audit_event(username: str, role: str, category: str, question: str, was_blocked: bool):
    """
    Records one audit entry. If `category` is in CONFIDENTIAL_CATEGORIES,
    the question text is replaced with a placeholder instead of being
    stored verbatim — the category and metadata are still logged, so
    usage patterns remain auditable without retaining sensitive content.
    """
    text_to_store = question
    if category in CONFIDENTIAL_CATEGORIES:
        text_to_store = "[REDACTED — confidential category, text not persisted]"

    with storage_engine.begin() as conn:
        conn.execute(
            text("""INSERT INTO AuditLog (Username, Role, QuestionCategory, QuestionText, WasBlocked, CreatedAt)
                     VALUES (:username, :role, :category, :qtext, :blocked, :created)"""),
            {
                "username": username, "role": role, "category": category,
                "qtext": text_to_store, "blocked": was_blocked, "created": datetime.now()
            }
        )


def list_audit_log(limit=100):
    """Returns recent audit entries, most recent first — for admin review."""
    with storage_engine.connect() as conn:
        rows = conn.execute(
            text("""SELECT LogID, Username, Role, QuestionCategory, QuestionText, WasBlocked, CreatedAt
                     FROM AuditLog ORDER BY CreatedAt DESC LIMIT :lim"""),
            {"lim": limit}
        ).fetchall()
    return [
        {"log_id": r[0], "username": r[1], "role": r[2], "category": r[3],
         "question_text": r[4], "was_blocked": bool(r[5]), "created_at": r[6]}
        for r in rows
    ]

if __name__ == "__main__":
    # Standalone self-test — run with: python chat_storage.py
    # Does NOT touch ChatSessions/ChatMessages logic; only exercises the new
    # AppUsers table, in isolation, before it's wired into app.py.

    print("Creating AppUsers table (if not exists)...")
    init_user_table()
    print("Done.")

    test_username = "test_manager_temp"

    print(f"\nCleaning up any leftover '{test_username}' from a previous test run...")
    with storage_engine.begin() as conn:
        conn.execute(text("DELETE FROM AppUsers WHERE Username=:u"), {"u": test_username})

    print(f"\nCreating test user '{test_username}' with role 'manager'...")
    created = create_user(test_username, "TempPass123", "manager")
    print(f"create_user returned: {created} (expected: True)")

    print(f"\nCreating the SAME username again (should fail, duplicate)...")
    created_dup = create_user(test_username, "AnotherPass", "manager")
    print(f"create_user returned: {created_dup} (expected: False)")

    print(f"\nFetching user by username...")
    user = get_user_by_username(test_username)
    print(f"Fetched: user_id={user['user_id']}, username={user['username']}, role={user['role']}")

    print(f"\nVerifying correct password...")
    ok = verify_password("TempPass123", user["password_hash"])
    print(f"verify_password (correct): {ok} (expected: True)")

    print(f"\nVerifying wrong password...")
    bad = verify_password("WrongPassword", user["password_hash"])
    print(f"verify_password (wrong): {bad} (expected: False)")

    print(f"\nFetching nonexistent user...")
    missing = get_user_by_username("this_user_does_not_exist_xyz")
    print(f"Fetched: {missing} (expected: None)")

    print(f"\nListing all users:")
    for u in list_users():
        print(f"  - {u}")

    print(f"\nTesting authenticate_user with correct password...")
    auth_ok = authenticate_user(test_username, "TempPass123")
    print(f"authenticate_user (correct): {auth_ok} (expected: dict with role='manager')")

    print(f"\nTesting authenticate_user with wrong password...")
    auth_bad = authenticate_user(test_username, "WrongPassword")
    print(f"authenticate_user (wrong): {auth_bad} (expected: None)")

    print(f"\nTesting authenticate_user with nonexistent username...")
    auth_missing = authenticate_user("nonexistent_user_xyz", "anything")
    print(f"authenticate_user (missing user): {auth_missing} (expected: None)")

    print(f"\nCleaning up test user '{test_username}'...")
    with storage_engine.begin() as conn:
        conn.execute(text("DELETE FROM AppUsers WHERE Username=:u"), {"u": test_username})
    print("Cleanup done.")

    print(f"\nTesting audit log...")
    init_audit_table()

    log_audit_event("test_manager_temp", "manager", "SAFE", "چند نفر کارمند داریم؟", was_blocked=False)
    log_audit_event("test_manager_temp", "staff", "ROLE_RESTRICTED_SALARY", "میانگین حقوق چقدر است؟", was_blocked=True)
    log_audit_event("test_manager_temp", "manager", "INDIVIDUAL_PERSONAL_DATA", "حقوق آقای X چقدر است؟", was_blocked=False)

    recent_logs = list_audit_log(limit=5)
    print(f"Retrieved {len(recent_logs)} recent audit log entries:")
    for entry in recent_logs:
        print(f"  - {entry}")

    audit_ok = len(recent_logs) >= 3
    confidential_redacted = any(
        e["category"] in ("ROLE_RESTRICTED_SALARY", "INDIVIDUAL_PERSONAL_DATA")
        and "REDACTED" in e["question_text"]
        for e in recent_logs
    )
    safe_not_redacted = any(
        e["category"] == "SAFE" and "REDACTED" not in e["question_text"]
        for e in recent_logs
    )
    print(f"audit_ok={audit_ok}, confidential_redacted={confidential_redacted}, safe_not_redacted={safe_not_redacted}")

    print(f"\nCleaning up test audit log entries...")
    with storage_engine.begin() as conn:
        conn.execute(text("DELETE FROM AuditLog WHERE Username=:u"), {"u": "test_manager_temp"})

    if (created and not created_dup and ok and not bad and user is not None
            and missing is None and auth_ok is not None and auth_ok.get("role") == "manager"
            and "password_hash" not in auth_ok and auth_bad is None and auth_missing is None
            and audit_ok and confidential_redacted and safe_not_redacted):
        print("\nALL TESTS PASSED")
    else:
        print("\nSOME TESTS FAILED — see above")