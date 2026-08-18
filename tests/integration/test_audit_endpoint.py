"""Integration tests: GET /api/audit is manager-only and returns audit rows."""
import pytest


@pytest.mark.integration
def test_audit_endpoint_manager_only(require_mysql):
    import api_server
    from fastapi.testclient import TestClient

    client = TestClient(api_server.app)
    staff_token = api_server.create_access_token(1, "audit_staff", "staff")
    supervisor_token = api_server.create_access_token(2, "audit_sup", "supervisor")
    manager_token = api_server.create_access_token(3, "audit_mgr", "manager")

    assert client.get("/api/audit", headers={"Authorization": f"Bearer {staff_token}"}).status_code == 403
    assert client.get("/api/audit", headers={"Authorization": f"Bearer {supervisor_token}"}).status_code == 403

    r = client.get("/api/audit", headers={"Authorization": f"Bearer {manager_token}"})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    for entry in data:
        assert set(entry) >= {"log_id", "username", "role", "category", "question_text", "was_blocked"}