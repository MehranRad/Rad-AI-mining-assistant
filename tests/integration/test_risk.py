"""Integration tests: the focused risk queries run against the live MySQL data
and compute_risk_indicators produces a transparent, significance-free block
grounded in the real numbers."""
import pytest
from sqlalchemy import text

import agent


@pytest.mark.integration
def test_risk_queries_and_computation_live(require_mysql):
    from chat_storage import storage_engine

    with storage_engine.connect() as conn:
        prod = conn.execute(text(agent.FIXED_RISK_PRODUCTION_QUERY)).fetchall()
        eq = conn.execute(text(agent.FIXED_RISK_EQUIPMENT_QUERY)).fetchall()

    assert len(prod) == 4                    # one row per mine
    assert {r[0] for r in prod} == {m for m in agent.MINES}
    for r in prod:
        mine, recovery, downtime, working = r[0], float(r[1]), float(r[2]), float(r[3])
        assert 0 <= recovery <= 100          # RecoveryRate is a percentage
        assert downtime >= 0 and working >= 0

    assert len(eq) >= 3                      # at least one status per mine
    statuses = {r[1] for r in eq}
    assert statuses <= set(agent.EQUIPMENT_STATUSES)

    block = agent.compute_risk_indicators(str(prod), str(eq))
    assert block is not None
    low = block.lower()
    assert "no official risk score" in low
    for forbidden in ["significant", "meaningful", "معنادار", "همبستگی"]:
        assert forbidden not in low
    assert "Employees" not in block
    assert "recoveryrate is a percentage" in low


@pytest.mark.integration
def test_risk_queries_never_touch_employees(require_mysql):
    for sql in [agent.FIXED_RISK_PRODUCTION_QUERY, agent.FIXED_RISK_EQUIPMENT_QUERY]:
        assert "Employees" not in sql
        assert "salary" not in sql.lower()