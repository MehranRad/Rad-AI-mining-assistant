"""Integration tests: session ownership enforcement (IDOR guard) and the
POST /api/sessions/message endpoint."""
import pytest
from sqlalchemy import text

from chat_storage import create_session, is_session_owner, storage_engine

OWNER_ID = 9001
FOREIGN_ID = 9002


def _cleanup(session_id):
    if not session_id:
        return
    with storage_engine.begin() as conn:
        conn.execute(text("DELETE FROM ChatMessages WHERE SessionID=:s"), {"s": session_id})
        conn.execute(text("DELETE FROM ChatSessions WHERE SessionID=:s"), {"s": session_id})


@pytest.mark.integration
def test_is_session_owner(require_mysql):
    session_id = create_session("owner session", user_id=OWNER_ID)
    try:
        assert is_session_owner(session_id, OWNER_ID) is True
        assert is_session_owner(session_id, FOREIGN_ID) is False
        assert is_session_owner("no-such-session", OWNER_ID) is False
    finally:
        _cleanup(session_id)


@pytest.mark.integration
def test_add_message_endpoint_forbids_foreign_session(require_mysql):
    import api_server
    from fastapi.testclient import TestClient

    session_id = api_server.create_session("owner session", user_id=OWNER_ID)
    try:
        owner_token = api_server.create_access_token(OWNER_ID, "owner_user", "staff")
        foreign_token = api_server.create_access_token(FOREIGN_ID, "foreign_user", "staff")
        client = TestClient(api_server.app)

        r_foreign = client.post(
            "/api/sessions/message",
            json={"session_id": session_id, "role": "user", "content": "hi"},
            headers={"Authorization": f"Bearer {foreign_token}"},
        )
        assert r_foreign.status_code == 403

        r_owner = client.post(
            "/api/sessions/message",
            json={"session_id": session_id, "role": "user", "content": "hi"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert r_owner.status_code == 200
    finally:
        _cleanup(session_id)


@pytest.mark.integration
def test_add_message_endpoint_requires_auth(require_mysql):
    import api_server
    from fastapi.testclient import TestClient

    client = TestClient(api_server.app)
    r = client.post(
        "/api/sessions/message",
        json={"session_id": "whatever", "role": "user", "content": "hi"},
    )
    assert r.status_code in (401, 403)