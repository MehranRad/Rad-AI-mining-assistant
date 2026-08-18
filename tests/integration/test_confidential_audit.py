"""Integration tests: AuditLog writes and confidential-category redaction."""
import pytest
from sqlalchemy import text

from chat_storage import CONFIDENTIAL_CATEGORIES, init_audit_table, list_audit_log, log_audit_event, storage_engine

USERNAME = "pytest_audit_temp"


def _cleanup():
    with storage_engine.begin() as conn:
        conn.execute(text("DELETE FROM AuditLog WHERE Username=:u"), {"u": USERNAME})


@pytest.mark.integration
def test_audit_redaction_for_confidential_categories(require_mysql):
    init_audit_table()
    _cleanup()
    try:
        log_audit_event(USERNAME, "staff", "ROLE_RESTRICTED_SALARY", "میانگین حقوق چقدر است؟", was_blocked=True)
        log_audit_event(USERNAME, "manager", "INDIVIDUAL_PERSONAL_DATA", "حقوق آقای X چقدر است؟", was_blocked=False)
        log_audit_event(USERNAME, "manager", "SAFE", "چند نفر کارمند داریم؟", was_blocked=False)

        entries = [e for e in list_audit_log(limit=100) if e["username"] == USERNAME]
        assert len(entries) == 3

        confidential = [e for e in entries if e["category"] in CONFIDENTIAL_CATEGORIES]
        safe = [e for e in entries if e["category"] == "SAFE"]
        assert all("REDACTED" in e["question_text"] for e in confidential)
        assert all("REDACTED" not in e["question_text"] for e in safe)
    finally:
        _cleanup()