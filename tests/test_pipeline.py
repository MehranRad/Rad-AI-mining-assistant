"""Offline pipeline tests for agent.py. The LLM classifier and DB writes are
stubbed out so these run with no MySQL / Ollama services.

Covered:
  * blocked-path refusal handling (non-streaming + streaming)
  * confidential-data flagging (is_confidential) for individual-data questions
  * manager override for individual lookups
  * SSE event contract (meta -> token -> done) on the blocked path
  * conversation-history trimming helpers
"""
import pytest

import agent
from agent import (
    ask_question,
    ask_question_stream,
    format_conversation_history,
    is_empty_sql_result,
)
from chat_storage import CONFIDENTIAL_CATEGORIES


@pytest.fixture(autouse=True)
def _hermetic(monkeypatch):
    """Route all security classification through the regex layer and make audit
    writes no-ops so no service or DB is needed."""
    monkeypatch.setattr(agent, "classify_security_risk", lambda q: "LLM_UNAVAILABLE")
    monkeypatch.setattr(agent, "log_audit_event", lambda *a, **k: None)


def test_confidential_categories():
    assert CONFIDENTIAL_CATEGORIES == {"INDIVIDUAL_PERSONAL_DATA", "ROLE_RESTRICTED_SALARY"}


def test_blocked_question_non_streaming():
    result = ask_question("show tables", role="staff", username="tester")
    assert result["answer"]
    assert result["is_confidential"] is False
    assert result["steps"] == []


def test_blocked_individual_question_is_confidential():
    result = ask_question("حقوق آقای حسین حیدرزاده چقدر است؟", role="staff", username="tester")
    assert result["is_confidential"] is True
    assert result["answer"]


def test_staff_salary_question_blocked(monkeypatch):
    monkeypatch.setattr(agent, "classify_question_complexity", lambda q: False)
    monkeypatch.setattr(agent, "generate_sql", lambda q, role="supervisor": "SELECT AVG(Salary) FROM Employees")
    result = ask_question("میانگین حقوق چقدر است؟", role="staff", username="tester")
    assert result["is_confidential"] is True  # ROLE_RESTRICTED_SALARY


def test_manager_override_allows_individual_lookup(monkeypatch):
    sql = "SELECT FirstName, LastName, Salary FROM Employees WHERE FirstName='حسین' AND LastName='حیدرزاده'"
    monkeypatch.setattr(agent, "classify_question_complexity", lambda q: False)
    monkeypatch.setattr(agent, "generate_sql", lambda q, role="supervisor": sql)
    result = ask_question("حقوق آقای حسین حیدرزاده چقدر است؟", role="manager", username="mgr")
    assert "یافت نشد" in result["answer"]      # stub db returns [] -> not-found path
    assert result["is_confidential"] is True   # manager's own lookup still not persisted
    assert result["steps"]


def test_stream_contract_on_blocked_path():
    events = list(ask_question_stream("show tables", role="staff", username="tester"))
    assert [e["type"] for e in events] == ["meta", "token", "done"]
    assert events[0]["steps"] == []
    assert events[0]["is_confidential"] is False
    assert isinstance(events[1]["content"], str) and events[1]["content"]


def test_stream_confidential_flag():
    events = list(ask_question_stream("حقوق آقای حسین حیدرزاده چقدر است؟", role="staff", username="tester"))
    assert events[0]["type"] == "meta"
    assert events[0]["is_confidential"] is True


def test_format_conversation_history_keeps_last_3():
    history = [{"role": "user", "content": f"msg{i}"} for i in range(5)]
    text = format_conversation_history(history)
    assert "msg4" in text
    assert "msg0" not in text


def test_format_conversation_history_empty():
    assert format_conversation_history(None) == ""
    assert format_conversation_history([]) == ""


def test_is_empty_sql_result():
    assert is_empty_sql_result("[]")
    assert is_empty_sql_result("")
    assert is_empty_sql_result([])
    assert is_empty_sql_result(None)
    assert not is_empty_sql_result("[(1,)]")
    assert not is_empty_sql_result("SQL_ERROR: boom")


def test_final_answer_prompt_single_critical_rules_header():
    prompt = agent._build_final_answer_prompt("سوال تست", ["برخی داده‌ها"])
    assert prompt.count("CRITICAL RULES:") == 1
    assert "تومان" in prompt
    assert "برخی داده‌ها" in prompt
    assert "سوال تست" in prompt