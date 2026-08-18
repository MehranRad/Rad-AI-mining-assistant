"""Offline tests: schema_constants must match the real Excel data, and the LLM
TABLE_CONTEXT / fixed queries must render from the constants correctly."""
import check_schema_consistency
import schema_constants as sc


def test_excel_data_matches_constants():
    assert check_schema_consistency.check_excel() == 0


def test_status_running_constant():
    assert sc.STATUS_RUNNING == "در حال کار"
    assert sc.STATUS_RUNNING in sc.EQUIPMENT_STATUSES


def test_mines_contain_zwnj_half_space():
    assert "\u200c" in sc.MINES[2]  # خاتون‌آباد


def test_no_translated_or_phantom_values():
    assert "Running" not in sc.EQUIPMENT_STATUSES       # English glosses live only in STATUS_GLOSS
    assert "Unknown" not in sc.EMPLOYEE_SHIFTS          # real data has روز instead
    assert "متوقف" not in sc.EQUIPMENT_STATUSES         # removed stale value
    assert "مدیر کارخانه" not in sc.JOB_TITLES         # phantom title removed
    assert "مدیر نگهداری و تعمیرات" not in sc.JOB_TITLES


def test_fmt_values_gloss():
    assert sc.fmt_values(("مرد", "زن"), sc.GENDER_GLOSS) == "'مرد' (male), 'زن' (female)"


def test_fmt_values_plain():
    assert sc.fmt_values(("شب", "صبح")) == "'شب', 'صبح'"


def test_fixed_workforce_query_uses_gender_constants():
    assert f"Gender = '{sc.GENDERS[0]}'" in agent_FIXED_WORKFORCE_QUERY()
    assert f"Gender = '{sc.GENDERS[1]}'" in agent_FIXED_WORKFORCE_QUERY()


def agent_FIXED_WORKFORCE_QUERY():
    import agent
    return agent.FIXED_WORKFORCE_QUERY


def test_table_context_uses_constants_and_no_stale_values():
    import agent
    t = agent.TABLE_CONTEXT
    assert "'روز' (day)" in t          # corrected employee shift value documented
    assert "'از رده خارج' (Retired)" in t
    assert "متوقف" not in t            # stale status value gone
    assert "may be NULL for some rows" not in t
    assert "مدیر کارخانه" not in t     # phantom job title gone
    # constants are actually referenced, not just coincidentally present
    assert sc.fmt_values(sc.MINES) in t