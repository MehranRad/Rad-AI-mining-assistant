"""Integration tests for the JWT-only session routes (no user_id in the URL).

Contract after the fix:
  GET    /api/sessions                  -> own sessions, HTTP 200
  GET    /api/sessions/{sid}/messages   -> own: 200 | foreign: 403 | missing: 404
  DELETE /api/sessions/{sid}            -> own: 200 | foreign: 403 | missing: 404
  (any of the above)                    -> no token: 401

The user_id in these routes is derived exclusively from the verified JWT —
a client-supplied user_id can no longer drift from the token's user_id.
"""
import pytest
from sqlalchemy import text

import api_server
from chat_storage import storage_engine
from fastapi.testclient import TestClient

OWNER_ID = 9101
FOREIGN_ID = 9102


def _cleanup(session_id):
    if not session_id:
        return
    with storage_engine.begin() as conn:
        conn.execute(text("DELETE FROM ChatMessages WHERE SessionID=:s"), {"s": session_id})
        conn.execute(text("DELETE FROM ChatSessions WHERE SessionID=:s"), {"s": session_id})


@pytest.mark.integration
def test_session_routes_own_foreign_missing(require_mysql):
    session_id = api_server.create_session("owner session", user_id=OWNER_ID)
    try:
        owner_token = api_server.create_access_token(OWNER_ID, "owner", "staff")
        foreign_token = api_server.create_access_token(FOREIGN_ID, "foreign", "staff")
        client = TestClient(api_server.app)

        # Own session -> 200, and it appears in the own session list.
        r = client.get(f"/api/sessions/{session_id}/messages", headers={"Authorization": f"Bearer {owner_token}"})
        assert r.status_code == 200

        r = client.get("/api/sessions", headers={"Authorization": f"Bearer {owner_token}"})
        assert r.status_code == 200
        assert any(s["session_id"] == session_id for s in r.json())

        # Foreign session -> 403, no data leak.
        r = client.get(f"/api/sessions/{session_id}/messages", headers={"Authorization": f"Bearer {foreign_token}"})
        assert r.status_code == 403

        # Missing session -> 404.
        r = client.get("/api/sessions/no-such-session/messages", headers={"Authorization": f"Bearer {owner_token}"})
        assert r.status_code == 404

        # Foreign delete -> 403 and the session survives.
        r = client.delete(f"/api/sessions/{session_id}", headers={"Authorization": f"Bearer {foreign_token}"})
        assert r.status_code == 403
        r = client.get(f"/api/sessions/{session_id}/messages", headers={"Authorization": f"Bearer {owner_token}"})
        assert r.status_code == 200

        # Missing delete -> 404.
        r = client.delete("/api/sessions/no-such-session", headers={"Authorization": f"Bearer {owner_token}"})
        assert r.status_code == 404

        # Own delete -> 200, then the session is gone.
        r = client.delete(f"/api/sessions/{session_id}", headers={"Authorization": f"Bearer {owner_token}"})
        assert r.status_code == 200
        r = client.get(f"/api/sessions/{session_id}/messages", headers={"Authorization": f"Bearer {owner_token}"})
        assert r.status_code == 404
    finally:
        _cleanup(session_id)


@pytest.mark.integration
def test_session_routes_require_auth(require_mysql):
    client = TestClient(api_server.app)
    assert client.get("/api/sessions").status_code == 401
    assert client.get("/api/sessions/whatever/messages").status_code == 401
    assert client.delete("/api/sessions/whatever").status_code == 401
