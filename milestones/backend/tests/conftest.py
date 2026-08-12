import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import Database


@pytest.fixture
def db(tmp_path):
    database = Database(tmp_path / "test.db")
    yield database
    database.close()


@pytest.fixture
def registry():
    from app.jobs import JobRegistry

    return JobRegistry()


@pytest.fixture
def client(db, registry):
    from fastapi.testclient import TestClient
    from app.main import create_app

    app = create_app(db, registry)
    return TestClient(app)
