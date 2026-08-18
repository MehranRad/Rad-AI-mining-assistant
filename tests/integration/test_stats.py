"""Integration tests: /api/stats returns values consistent with the real data
(the "running equipment" KPI uses the correct Persian Status value)."""
import pandas as pd
import pytest
from sqlalchemy import text

from schema_constants import STATUS_RUNNING


@pytest.mark.integration
def test_stats_running_kpi_uses_persian_status(require_mysql, monkeypatch):
    import agent
    import api_server
    from fastapi.testclient import TestClient

    df = pd.read_excel("data/Equipment.xlsx")
    expected_running = int((df["Status"].astype(str).str.strip() == STATUS_RUNNING).sum())
    assert expected_running == 532  # sanity: known value in the source data

    def real_run(sql, *args, **kwargs):
        with agent_db_engine().connect() as conn:
            return str(conn.execute(text(sql)).fetchall())

    def agent_db_engine():
        from chat_storage import storage_engine
        return storage_engine

    monkeypatch.setattr(agent.db, "run", real_run)

    client = TestClient(api_server.app)
    token = api_server.create_access_token(1, "stats_tester", "manager")
    r = client.get("/api/stats", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["running"] == expected_running
    assert data["equipment"] == len(df)
    assert data["employees"] == int((pd.read_excel("data/Employees.xlsx")).shape[0])