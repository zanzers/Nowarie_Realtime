import os
from dotenv import load_dotenv
from sqlalchemy.engine import make_url

load_dotenv()
_test_url = os.getenv("TEST_DATABASE_URL")
if not _test_url:
    raise RuntimeError("TEST_DATABASE_URL is not set; refusing to run tests against the dev database.")
if not (make_url(_test_url).database or "").endswith("_test"):
    raise RuntimeError("TEST_DATABASE_URL must point at a database whose name ends with '_test'.")
os.environ["DATABASE_URL"] = _test_url

import pytest
from app.db.database import Base, engine
import app.db.models
import app.db.message_repository


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)