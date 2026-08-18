"""Shared pytest fixtures for the mining-assistant test suite.

Two classes of tests:
  * OFFLINE (no marker) — pure functions that must not touch MySQL or Ollama.
  * INTEGRATION (marked `integration`) — need a live MySQL (and sometimes
    Ollama); skipped cleanly when the service is unavailable.

agent.py opens a real MySQL connection at import time (SQLDatabase.from_uri),
so we stub SQLDatabase before any test module imports `agent`. This lets the
pure logic (security guards, prompt builders, schema constants) be tested with
no services at all. Integration tests talk to MySQL through
chat_storage.storage_engine instead of the stubbed `agent.db`.
"""
import langchain_community.utilities as _lcu

import pytest


class _FakeDB:
    """Stand-in for langchain's SQLDatabase used only to let agent.py import
    without connecting. Never used for real queries."""

    def __init__(self, *args, **kwargs):
        pass

    @classmethod
    def from_uri(cls, *args, **kwargs):
        return cls()

    def run(self, query, *args, **kwargs):
        return "[]"


# Replace the module attribute BEFORE agent.py does `from langchain_community
# .utilities import SQLDatabase` at import time.
_lcu.SQLDatabase = _FakeDB


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: requires live MySQL and/or Ollama services (skipped when unavailable)",
    )


@pytest.fixture(scope="session")
def mysql_available():
    """True if a live MySQL connection works."""
    try:
        from sqlalchemy import text
        from chat_storage import storage_engine

        with storage_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@pytest.fixture
def require_mysql(mysql_available):
    if not mysql_available:
        pytest.skip("MySQL is not available; skipping integration test")
    return True