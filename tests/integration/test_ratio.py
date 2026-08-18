"""Integration tests: the precomputed ore-per-active-equipment ratio query and
its Python computation run correctly against the live MySQL data."""
import pytest
from sqlalchemy import text

import agent


@pytest.mark.integration
def test_production_per_active_equipment_ratio_live(require_mysql):
    from chat_storage import storage_engine

    with storage_engine.connect() as conn:
        rows = conn.execute(text(agent.FIXED_PRODUCTION_PER_ACTIVE_EQUIPMENT_QUERY)).fetchall()

    assert len(rows) == 4  # one row per mine
    for r in rows:
        mine, total_ore, active_count = r[0], float(r[1]), int(r[2])
        assert mine
        assert total_ore > 0       # SUM of extracted ore per mine
        assert active_count > 0    # COUNT of equipment with Status='در حال کار'

    block = agent.compute_production_per_active_equipment_ratio(str(rows))
    assert block is not None
    assert "HIGHEST ore-per-active-equipment mine:" in block
    assert "meaningful" not in block.lower()
    assert "RecoveryRate" not in block and "Fuel" not in block


@pytest.mark.integration
def test_ratio_query_aggregations_are_correct(require_mysql):
    from chat_storage import storage_engine

    sql = agent.FIXED_PRODUCTION_PER_ACTIVE_EQUIPMENT_QUERY
    with storage_engine.connect() as conn:
        rows = conn.execute(text(sql)).fetchall()

    # Cross-check the SUM against a plain per-mine total query.
    check_sql = "SELECT Mine, SUM(CopperOreTon) FROM Production GROUP BY Mine"
    with storage_engine.connect() as conn:
        expected = dict(conn.execute(text(check_sql)).fetchall())
    for r in rows:
        assert abs(float(r[1]) - float(expected[r[0]])) < 1e-6