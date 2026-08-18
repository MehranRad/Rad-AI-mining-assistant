"""Regression tests for the concise-answer policy and correct aggregation.

Offline (no MySQL/Ollama): these assert the shared final-answer prompt carries
the concise-policy rules (no SQL dump, no repeated conclusion, no invented
statistical significance, no average-as-total), that both streaming and
non-streaming generation use the SAME shared prompt, and that the Python
precomputations produce clean, significance-free, correctly-aggregated data.
"""
from types import SimpleNamespace

import pytest

import agent
from agent import (
    _build_final_answer_prompt,
    compute_comparison_stats,
    compute_production_per_active_equipment_ratio,
    generate_final_answer,
    generate_final_answer_stream,
    is_production_per_equipment_question,
)


# ---------------------------------------------------------------------------
# Shared prompt carries the concise-answer policy
# ---------------------------------------------------------------------------

def _prompt():
    return _build_final_answer_prompt("سوال تست", ["برخی داده‌ها"])


def test_prompt_single_critical_rules_header():
    assert _prompt().count("CRITICAL RULES:") == 1


def test_prompt_has_no_sql_dump_rule():
    p = _prompt().lower()
    assert "never include the sql query" in p
    assert "raw database result rows" in p
    assert "جزئیات فنی" in p


def test_prompt_has_no_repetition_rule():
    assert "never state the same conclusion twice" in _prompt().lower()


def test_prompt_has_no_statistical_significance_rule():
    p = _prompt()
    assert "statistical significance or correlation" in p
    assert "معنادار" in p
    assert "A plain numeric difference is NOT significance" in p


def test_prompt_has_no_average_as_total_rule():
    p = _prompt().lower()
    assert "never present an average as a total/sum" in p
    assert "مجموع" in p


def test_prompt_concise_policy_and_filler_ban():
    p = _prompt()
    assert "Answer EXACTLY what the user asked, then stop" in p
    assert "در نتیجه" in p  # listed as filler to avoid
    assert "Write the ENTIRE answer in Persian" in p


def test_prompt_keeps_currency_rule():
    assert "تومان" in _prompt()


# ---------------------------------------------------------------------------
# Both streaming and non-streaming generation use the SAME shared prompt
# ---------------------------------------------------------------------------

def test_generate_final_answer_uses_shared_prompt(monkeypatch):
    captured = {}

    def fake_invoke(prompt):
        captured["prompt"] = prompt
        return SimpleNamespace(content="پاسخ کوتاه")

    monkeypatch.setattr(agent, "llm_final", SimpleNamespace(invoke=fake_invoke))
    assert generate_final_answer("سوال", ["داده"]) == "پاسخ کوتاه"
    assert "CRITICAL RULES:" in captured["prompt"]
    assert "سوال" in captured["prompt"]


def test_generate_final_answer_stream_uses_shared_prompt(monkeypatch):
    captured = {}

    def fake_stream(prompt):
        captured["prompt"] = prompt
        return iter([SimpleNamespace(content="تک "), SimpleNamespace(content="یه ")])

    monkeypatch.setattr(agent, "llm_final", SimpleNamespace(stream=fake_stream))
    out = list(generate_final_answer_stream("سوال", ["داده"]))
    assert "".join(out) == "تک یه "
    assert "CRITICAL RULES:" in captured["prompt"]


# ---------------------------------------------------------------------------
# compute_comparison_stats must NOT emit statistical-significance language
# ---------------------------------------------------------------------------

_SAMPLE_PRODUCTION_ROWS = (
    "[('میدوک', 82.5, 5.1, 9.0, 100.0, 20.0, 3000.0, 2500.0), "
    "('سرچشمه', 81.2, 4.0, 9.5, 120.0, 22.0, 2800.0, 2400.0)]"
)


def test_comparison_stats_has_no_significance_flags():
    out = compute_comparison_stats(_SAMPLE_PRODUCTION_ROWS)
    assert out is not None
    low = out.lower()
    assert "meaningful" not in low
    assert "significant" not in low
    assert "IMPORTANT — verified facts" in out
    assert "82.50" in out  # numbers still present verbatim


def test_comparison_stats_handles_sql_error():
    assert compute_comparison_stats("SQL_ERROR: boom") is None
    assert compute_comparison_stats("[]") is None


# ---------------------------------------------------------------------------
# SUM vs AVG correctness (regression for presenting averages as totals)
# ---------------------------------------------------------------------------

def test_table_context_instructs_correct_aggregation():
    t = agent.TABLE_CONTEXT
    assert "SUM vs AVG" in t
    assert "مجموع" in t and "میانگین" in t
    assert "Never answer a TOTAL question with AVG" in t


def test_ratio_query_uses_sum_and_running_status():
    q = agent.FIXED_PRODUCTION_PER_ACTIVE_EQUIPMENT_QUERY
    assert "SUM(CopperOreTon)" in q
    assert "AVG(CopperOreTon)" not in q
    assert "COUNT(EquipmentID)" in q
    assert "در حال کار" in q
    assert "GROUP BY" in q  # never a row-by-row join


# ---------------------------------------------------------------------------
# compute_production_per_active_equipment_ratio
# ---------------------------------------------------------------------------

_RATIO_ROWS = (
    "[('خاتون‌آباد', 100000.0, 100), ('میدوک', 85000.0, 80), "
    "('سرچشمه', 90000.0, 150), ('سونگون', 60000.0, 50)]"
)


def test_ratio_computation_correct_and_ordered():
    out = compute_production_per_active_equipment_ratio(_RATIO_ROWS)
    assert out is not None
    # ratios: سونگون 1200, میدوک 1062.5, خاتون‌آباد 1000, سرچشمه 600
    assert "HIGHEST ore-per-active-equipment mine: سونگون" in out
    assert "سونگون: 1200.000" in out
    assert "میدوک: 1062.500" in out
    assert "سرچشمه: 600.000" in out
    # keeps only the relevant metric, no unrelated production fields
    assert "RecoveryRate" not in out and "Fuel" not in out


def test_ratio_computation_skips_zero_active_count():
    rows = "[('میدوک', 5000.0, 0), ('سرچشمه', 6000.0, 10)]"
    out = compute_production_per_active_equipment_ratio(rows)
    assert out is not None
    assert "میدوک" not in out  # zero active equipment -> skipped
    assert "سرچشمه: 600.000" in out


def test_ratio_computation_error_cases():
    assert compute_production_per_active_equipment_ratio("SQL_ERROR: boom") is None
    assert compute_production_per_active_equipment_ratio("[]") is None


# ---------------------------------------------------------------------------
# is_production_per_equipment_question detection
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "q",
    [
        "کدام معدن نسبت به تعداد تجهیزات فعالش، بیشترین حجم سنگ استخراج‌شده را دارد؟",
        "به ازای هر تجهیز فعال کدام معدن بیشترین سنگ را استخراج کرده؟",
        "نسبت سنگ استخراج‌شده به تعداد تجهیزات هر معدن را مقایسه کن",
    ],
)
def test_detects_production_per_equipment_questions(q):
    assert is_production_per_equipment_question(q) is True


@pytest.mark.parametrize(
    "q",
    [
        "وضعیت تجهیزات معدن میدوک را بگو",
        "میانگین نرخ بازیابی معادن چقدر است؟",
        "چند نفر کارمند داریم؟",
        "کدام معدن بیشترین اضافه‌کاری را دارد؟",
    ],
)
def test_does_not_detect_unrelated_questions(q):
    assert is_production_per_equipment_question(q) is False