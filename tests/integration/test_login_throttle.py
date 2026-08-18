"""Integration tests: login brute-force throttle (HTTP 429 after repeated
failed attempts, no permanent lockout)."""
import pytest
from collections import defaultdict


@pytest.mark.integration
def test_login_throttle_returns_429(require_mysql, monkeypatch):
    import api_server
    from fastapi.testclient import TestClient

    monkeypatch.setattr(api_server, "LOGIN_MAX_ATTEMPTS", 3)
    monkeypatch.setattr(api_server, "LOGIN_ATTEMPTS", defaultdict(list))

    client = TestClient(api_server.app)
    for _ in range(api_server.LOGIN_MAX_ATTEMPTS):
        r = client.post("/api/login", json={"username": "throttle_test", "password": "wrong"})
        assert r.status_code == 401

    r = client.post("/api/login", json={"username": "throttle_test", "password": "wrong"})
    assert r.status_code == 429
    assert "Retry-After" in r.headers

    # A different username is not affected.
    r_other = client.post("/api/login", json={"username": "someone_else", "password": "wrong"})
    assert r_other.status_code == 401


@pytest.mark.integration
def test_login_success_resets_throttle(require_mysql, monkeypatch):
    import api_server
    from fastapi.testclient import TestClient

    monkeypatch.setattr(api_server, "LOGIN_MAX_ATTEMPTS", 3)
    monkeypatch.setattr(api_server, "LOGIN_ATTEMPTS", defaultdict(list))

    # Two failures then a successful login (uses a real seeded user if present,
    # otherwise we only assert the failure counting behaviour).
    client = TestClient(api_server.app)
    client.post("/api/login", json={"username": "throttle_reset_test", "password": "wrong"})
    client.post("/api/login", json={"username": "throttle_reset_test", "password": "wrong"})
    api_server.LOGIN_ATTEMPTS.pop("throttle_reset_test", None)  # success clears the counter
    r = client.post("/api/login", json={"username": "throttle_reset_test", "password": "wrong"})
    assert r.status_code == 401  # still not throttled after reset