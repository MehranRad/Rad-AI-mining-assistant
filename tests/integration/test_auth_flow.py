"""Integration tests: AppUsers CRUD + authentication against a live MySQL DB."""
import pytest
from sqlalchemy import text

from chat_storage import (
    authenticate_user,
    create_user,
    get_user_by_username,
    init_user_table,
    storage_engine,
)

USERNAME = "pytest_temp_user"


def _delete_user(username):
    with storage_engine.begin() as conn:
        conn.execute(text("DELETE FROM AppUsers WHERE Username=:u"), {"u": username})


@pytest.mark.integration
def test_appusers_create_authenticate_duplicate(require_mysql):
    init_user_table()
    _delete_user(USERNAME)
    try:
        assert create_user(USERNAME, "TempPass123", "manager") is True
        assert create_user(USERNAME, "OtherPass", "manager") is False  # duplicate username

        user = get_user_by_username(USERNAME)
        assert user is not None
        assert user["role"] == "manager"
        assert "password_hash" in user  # internal lookup only

        auth = authenticate_user(USERNAME, "TempPass123")
        assert auth == {"user_id": user["user_id"], "username": USERNAME, "role": "manager"}
        assert "password_hash" not in auth  # never exposed

        assert authenticate_user(USERNAME, "WrongPassword") is None
        assert authenticate_user("no_such_user_xyz", "TempPass123") is None
    finally:
        _delete_user(USERNAME)


@pytest.mark.integration
def test_create_user_rejects_invalid_role(require_mysql):
    init_user_table()
    with pytest.raises(ValueError):
        create_user(USERNAME, "TempPass123", "admin")