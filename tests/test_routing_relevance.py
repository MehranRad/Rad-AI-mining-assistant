"""Regression tests for question-to-SQL relevance and role-based query routing.

These pin down the PRIMARY BUG: broad analytical questions (risk questions in
particular) must route to a focused, intent-aware query set — never to an
unrelated bundle of production + equipment + workforce/salary queries. They run
fully offline: the LLM classifier and DB writes are stubbed, and the fixed-query
routing / role restrictions / aggregation semantics are asserted directly.

For every question we verify:
  * the queries actually executed are relevant to the question
  * restricted SQL stays blocked for staff
  * unrelated tables (Employees/salary) are NOT queried unless the question is
    genuinely about them
  * aggregation (SUM vs AVG vs COUNT) is correct
  * the returned answer is the clean Persian text (no SQL / internal markers)
"""
import pytest

import agent
from agent import (
    ask_question,
    ask_question_stream,
    compute_risk_indicators,
    detect_question_topics,
    is_risk_question,
)


# ---------------------------------------------------------------------------
# Canned result sets (same shapes the real fixed queries return)
# ---------------------------------------------------------------------------

RISK_PROD = (
    "[('سونگون', 78.5, 12.3, 8.1), ('میدوک', 81.5, 5.2, 9.4), "
    "('سرچشمه', 82.0, 9.5, 9.0), ('خاتون\u200cآباد', 79.0, 10.0, 8.6)]"
)
RISK_EQ = (
    "[('سونگون', 'در حال کار', 100), ('سونگون', 'در تعمیر', 15), ('سونگون', 'از رده خارج', 8), "
    "('میدوک', 'در حال کار', 80), ('میدوک', 'در تعمیر', 4), ('میدوک', 'از رده خارج', 2), "
    "('سرچشمه', 'در حال کار', 120), ('سرچشمه', 'در تعمیر', 8), ('سرچشمه', 'از رده خارج', 3), "
    "('خاتون\u200cآباد', 'در حال کار', 90), ('خاتون\u200cآباد', 'در تعمیر', 10), "
    "('خاتون\u200cآباد', 'از رده خارج', 5)]"
)
PROD_COMPARISON = (
    "[('میدوک', 82.5, 5.1, 9.0, 100.0, 20.0, 3000.0, 2500.0), "
    "('سرچشمه', 81.2, 4.0, 9.5, 120.0, 22.0, 2800.0, 2400.0)]"
)
EQ_STATUS = (
    "[('میدوک', 'در حال کار', 80, 1200000.0, 12.0), "
    "('میدوک', 'در تعمیر', 4, 900000.0, 11.0), "
    "('سرچشمه', 'در حال کار', 120, 1300000.0, 13.0)]"
)
TOTALS = "[(12345.0, 54321.0, 999.0, 888.0, 777.0, 666.0)]"
WORKFORCE = "[('سونگون', 600, 12000000.0, 35.0, 500, 100, 1200.0, 2.0)]"

FAKE_ANSWER = "پاسخ فارسی تستی"


def _fake_run(calls):
    def fake_run(sql, *args, **kwargs):
        calls.append(sql)
        if "SUM(DowntimeHours)" in sql:
            return TOTALS
        if "Employees" in sql:
            return WORKFORCE
        if "PurchasePrice" in sql:          # equipment status breakdown
            return EQ_STATUS
        if "EnergyConsumption" in sql:      # full production comparison
            return PROD_COMPARISON
        if "FROM Production" in sql:        # risk production / simple queries
            return RISK_PROD
        if "FROM Equipment" in sql:         # risk equipment counts
            return RISK_EQ
        return "[]"
    return fake_run


@pytest.fixture(autouse=True)
def _hermetic(monkeypatch):
    """No services: regex security layer, no-op audit, deterministic routing."""
    monkeypatch.setattr(agent, "classify_security_risk", lambda q: "LLM_UNAVAILABLE")
    monkeypatch.setattr(agent, "log_audit_event", lambda *a, **k: None)
    monkeypatch.setattr(agent, "_llm_select_topic", lambda q: "production")


def _stub_pipeline(monkeypatch, calls, blocks, complexity=True):
    monkeypatch.setattr(agent, "classify_question_complexity", lambda q: complexity)
    monkeypatch.setattr(agent, "run_sql", _fake_run(calls))

    def fake_answer(question, context_blocks):
        blocks.append(context_blocks)
        return FAKE_ANSWER

    monkeypatch.setattr(agent, "generate_final_answer", fake_answer)
    return fake_answer


# ---------------------------------------------------------------------------
# Risk questions: focused queries, never workforce/salary
# ---------------------------------------------------------------------------

RISK_QUESTIONS = [
    "کدام معدن بیشترین ریسک را دارد؟",
    "ریسک ها چی هستند؟",
    "ریسک کدام معدن بیشتر است؟",
    "کدام معدن شرایط بدتری دارد؟",
    "کدام معدن از نظر عملیاتی پرریسک‌تر است؟",
]


@pytest.mark.parametrize("question", RISK_QUESTIONS)
@pytest.mark.parametrize("role", ["staff", "supervisor", "manager"])
def test_risk_question_runs_only_focused_risk_queries(monkeypatch, question, role):
    calls, blocks = [], []
    _stub_pipeline(monkeypatch, calls, blocks)

    result = ask_question(question, role=role, username="tester")

    assert len(calls) == 2, f"expected 2 risk queries, got: {calls}"
    joined = "\n".join(calls)
    assert "FROM Production" in joined and "FROM Equipment" in joined
    assert "RecoveryRate" in joined and "DowntimeHours" in joined
    assert "Employees" not in joined
    assert "salary" not in joined.lower()
    assert "GROUP BY Mine" in joined

    assert not any(s["result"] == "ROLE_RESTRICTED_SALARY" for s in result["steps"])
    assert result["is_confidential"] is False
    assert result["answer"] == FAKE_ANSWER
    assert "no official risk score" in "\n".join(blocks[0]).lower()


def test_risk_block_transparent_and_significance_free():
    block = compute_risk_indicators(RISK_PROD, RISK_EQ)
    assert block is not None
    low = block.lower()
    for forbidden in ["significant", "meaningful", "معنادار", "همبستگی", "causal"]:
        assert forbidden not in low
    assert "no official risk score" in low
    assert "Employees" not in block
    assert "سونگون" in block and "میدوک" in block


def test_risk_block_error_cases():
    assert compute_risk_indicators("SQL_ERROR: boom", RISK_EQ) is None
    assert compute_risk_indicators(RISK_PROD, "[]") is None


def test_is_risk_question_detector():
    assert is_risk_question("کدام معدن بیشترین ریسک را دارد؟")
    assert is_risk_question("ریسک ها چی هستند؟")
    assert not is_risk_question("وضعیت تجهیزات معدن میدوک را بگو")
    assert not is_risk_question("کدام معدن بیشترین نرخ بازیابی را دارد؟")


# ---------------------------------------------------------------------------
# Question -> topic routing (no more all-three fallback)
# ---------------------------------------------------------------------------

def test_detect_topics_risk():
    assert detect_question_topics("کدام معدن بیشترین ریسک را دارد؟") == {"risk"}
    assert detect_question_topics("ریسک ها چی هستند؟") == {"risk"}


def test_no_keyword_fallback_is_focused_not_all_topics(monkeypatch):
    monkeypatch.setattr(agent, "_llm_select_topic", lambda q: "production")
    assert detect_question_topics("کدام معدن شرایط بهتری دارد؟") == {"production"}
    monkeypatch.setattr(agent, "_llm_select_topic", lambda q: "equipment")
    assert detect_question_topics("کدام معدن شرایط بهتری دارد؟") == {"equipment"}


def test_overtime_question_routes_to_workforce():
    # "اضافه‌کاری" is a workforce concept — must never route to production.
    assert detect_question_topics("کدام معدن بیشترین اضافه‌کاری را دارد؟") == {"workforce"}
    assert detect_question_topics("مجموع اضافه کاری هر معدن") == {"workforce"}


def test_workforce_question_does_not_fire_equipment():
    # "وضعیت" alone must not be treated as an equipment keyword.
    assert detect_question_topics("وضعیت نیروی انسانی معادن را مقایسه کن") == {"workforce"}
    assert detect_question_topics("وضعیت تجهیزات معدن میدوک را بگو") == {"equipment"}


def test_equipment_question_does_not_fire_workforce():
    assert detect_question_topics("وضعیت دستگاه‌های معدن میدوک") == {"equipment"}


# ---------------------------------------------------------------------------
# Single-metric analytical questions (SIMPLE path -> focused SQL)
# ---------------------------------------------------------------------------

def test_highest_recovery_question_routes_to_focused_sql(monkeypatch):
    captured = {}

    def fake_generate_sql(question, role="supervisor"):
        captured["question"] = question
        return ("SELECT Mine, AVG(RecoveryRate) AS AvgRecoveryRate FROM Production "
                "GROUP BY Mine ORDER BY AvgRecoveryRate DESC LIMIT 1")

    calls = []
    monkeypatch.setattr(agent, "classify_question_complexity", lambda q: False)
    monkeypatch.setattr(agent, "generate_sql", fake_generate_sql)
    monkeypatch.setattr(agent, "run_sql", _fake_run(calls))
    monkeypatch.setattr(agent, "generate_final_answer", lambda q, cb: FAKE_ANSWER)

    result = ask_question("کدام معدن بیشترین نرخ بازیابی را دارد؟", role="staff", username="tester")

    assert captured["question"] == "کدام معدن بیشترین نرخ بازیابی را دارد؟"
    assert len(calls) == 1
    assert "AVG(RecoveryRate)" in calls[0]
    assert "SUM" not in calls[0]                      # AVG, not SUM
    assert "Employees" not in calls[0]
    assert result["answer"] == FAKE_ANSWER


def test_most_running_equipment_question_uses_real_status(monkeypatch):
    captured = {}

    def fake_generate_sql(question, role="supervisor"):
        captured["question"] = question
        return ("SELECT Mine, COUNT(EquipmentID) AS Count FROM Equipment "
                "WHERE Status = 'در حال کار' GROUP BY Mine ORDER BY Count DESC LIMIT 1")

    calls = []
    monkeypatch.setattr(agent, "classify_question_complexity", lambda q: False)
    monkeypatch.setattr(agent, "generate_sql", fake_generate_sql)
    monkeypatch.setattr(agent, "run_sql", _fake_run(calls))
    monkeypatch.setattr(agent, "generate_final_answer", lambda q, cb: FAKE_ANSWER)

    result = ask_question("کدام معدن بیشترین تجهیزات در حال کار را دارد؟", role="staff", username="tester")

    assert captured["question"] == "کدام معدن بیشترین تجهیزات در حال کار را دارد؟"
    assert len(calls) == 1
    assert "Status = 'در حال کار'" in calls[0]
    assert "Employees" not in calls[0]
    assert result["answer"] == FAKE_ANSWER


def test_most_retired_equipment_question_uses_real_status(monkeypatch):
    captured = {}

    def fake_generate_sql(question, role="supervisor"):
        captured["question"] = question
        return ("SELECT Mine, COUNT(EquipmentID) AS Count FROM Equipment "
                "WHERE Status = 'از رده خارج' GROUP BY Mine ORDER BY Count DESC LIMIT 1")

    calls = []
    monkeypatch.setattr(agent, "classify_question_complexity", lambda q: False)
    monkeypatch.setattr(agent, "generate_sql", fake_generate_sql)
    monkeypatch.setattr(agent, "run_sql", _fake_run(calls))
    monkeypatch.setattr(agent, "generate_final_answer", lambda q, cb: FAKE_ANSWER)

    result = ask_question("کدام معدن بیشترین تجهیزات از رده خارج را دارد؟", role="staff", username="tester")

    assert len(calls) == 1
    assert "Status = 'از رده خارج'" in calls[0]
    assert "Employees" not in calls[0]
    assert result["answer"] == FAKE_ANSWER


# ---------------------------------------------------------------------------
# Complex-path routing: fixed queries are targeted and mutually exclusive
# ---------------------------------------------------------------------------

def test_complex_production_comparison_does_not_query_workforce_or_equipment(monkeypatch):
    calls, blocks = [], []
    _stub_pipeline(monkeypatch, calls, blocks, complexity=True)

    result = ask_question("کدام معدن بیشترین نرخ بازیابی را دارد؟", role="staff", username="tester")

    assert len(calls) == 1
    assert "FROM Production" in calls[0]
    assert "RecoveryRate" in calls[0]
    assert "Employees" not in calls[0]
    assert "FROM Equipment" not in calls[0]
    assert result["answer"] == FAKE_ANSWER


def test_complex_equipment_question_scopes_to_named_mine(monkeypatch):
    calls, blocks = [], []
    _stub_pipeline(monkeypatch, calls, blocks, complexity=True)

    result = ask_question("وضعیت تجهیزات معدن میدوک را بگو", role="staff", username="tester")

    assert len(calls) == 1
    assert "FROM Equipment" in calls[0]
    assert "WHERE Mine LIKE '%میدوک%'" in calls[0]
    assert "Employees" not in calls[0]
    assert result["answer"] == FAKE_ANSWER


def test_total_downtime_question_runs_only_totals_query(monkeypatch):
    calls, blocks = [], []
    _stub_pipeline(monkeypatch, calls, blocks, complexity=True)

    result = ask_question("مجموع کل ساعات توقف تجهیزات چقدر است؟", role="staff", username="tester")

    assert len(calls) == 1
    assert "SUM(DowntimeHours)" in calls[0]
    assert "FROM Equipment" not in calls[0]
    assert "AvgRecoveryRate" not in calls[0]
    assert "Employees" not in calls[0]
    assert result["answer"] == FAKE_ANSWER


def test_highest_production_volume_runs_production_only(monkeypatch):
    calls, blocks = [], []
    _stub_pipeline(monkeypatch, calls, blocks, complexity=True)

    result = ask_question("کدام معدن بیشترین حجم تولید را دارد؟", role="staff", username="tester")

    assert len(calls) == 1
    assert "FROM Production" in calls[0]
    assert "Employees" not in calls[0]
    assert "FROM Equipment" not in calls[0]
    assert result["answer"] == FAKE_ANSWER


# ---------------------------------------------------------------------------
# Role-based behavior: staff restrictions + manager/supervisor allowances
# ---------------------------------------------------------------------------

def test_staff_restricted_salary_question_stays_blocked(monkeypatch):
    calls = []
    monkeypatch.setattr(agent, "classify_question_complexity", lambda q: False)
    monkeypatch.setattr(
        agent, "generate_sql",
        lambda q, role="supervisor": "SELECT AVG(Salary) FROM Employees",
    )
    monkeypatch.setattr(agent, "run_sql", _fake_run(calls))

    result = ask_question("میانگین حقوق کارکنان چقدر است؟", role="staff", username="tester")

    assert result["is_confidential"] is True            # ROLE_RESTRICTED_SALARY
    assert len(calls) == 0                               # query never ran
    assert "دسترسی" in result["answer"] or "حقوق" in result["answer"]


def test_manager_salary_question_is_allowed(monkeypatch):
    calls = []
    monkeypatch.setattr(agent, "classify_question_complexity", lambda q: False)
    monkeypatch.setattr(
        agent, "generate_sql",
        lambda q, role="supervisor": "SELECT Department, AVG(Salary) FROM Employees GROUP BY Department",
    )
    monkeypatch.setattr(agent, "run_sql", _fake_run(calls))
    monkeypatch.setattr(agent, "generate_final_answer", lambda q, cb: FAKE_ANSWER)

    result = ask_question("میانگین حقوق به تفکیک دپارتمان", role="manager", username="mgr")

    assert len(calls) == 1
    assert "AVG(Salary)" in calls[0]
    assert result["answer"] == FAKE_ANSWER


def test_supervisor_complex_workforce_question_queries_employees(monkeypatch):
    calls, blocks = [], []
    _stub_pipeline(monkeypatch, calls, blocks, complexity=True)

    result = ask_question("وضعیت نیروی انسانی معادن را مقایسه کن", role="supervisor", username="sup")

    assert any("FROM Employees" in c for c in calls), f"expected workforce query, got: {calls}"
    assert "AVG(Salary)" in "\n".join(calls)
    assert result["is_confidential"] is False
    assert result["answer"] == FAKE_ANSWER


def test_staff_complex_workforce_question_is_blocked_without_query(monkeypatch):
    calls, blocks = [], []
    _stub_pipeline(monkeypatch, calls, blocks, complexity=True)

    result = ask_question("وضعیت نیروی انسانی معادن را مقایسه کن", role="staff", username="tester")

    assert not any("FROM Employees" in c for c in calls), f"staff must not run: {calls}"
    assert any(s["result"] == "ROLE_RESTRICTED_SALARY" for s in result["steps"])
    assert "NOT retrieved" in "\n".join(blocks[0])
    assert result["answer"] == FAKE_ANSWER


# ---------------------------------------------------------------------------
# Streaming path mirrors the non-streaming routing
# ---------------------------------------------------------------------------

def test_stream_risk_question_contract(monkeypatch):
    calls = []
    monkeypatch.setattr(agent, "classify_question_complexity", lambda q: True)
    monkeypatch.setattr(agent, "run_sql", _fake_run(calls))

    def fake_stream(question, context_blocks):
        yield "پاسخ "
        yield "فارسی تستی"

    monkeypatch.setattr(agent, "generate_final_answer_stream", fake_stream)

    events = list(ask_question_stream("کدام معدن بیشترین ریسک را دارد؟", role="staff", username="tester"))
    assert [e["type"] for e in events] == ["meta", "token", "token", "done"]
    assert len(calls) == 2
    assert "".join(e["content"] for e in events if e["type"] == "token") == "پاسخ فارسی تستی"
    assert all("Employees" not in c for c in calls)