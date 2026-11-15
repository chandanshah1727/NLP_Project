"""Select an isolated SQLite database before any backend module is imported."""
import os
import tempfile
from pathlib import Path

_test_database = tempfile.NamedTemporaryFile(prefix="waste-pytest-", suffix=".db", delete=False)
_test_database.close()
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_test_database.name).as_posix()}"
