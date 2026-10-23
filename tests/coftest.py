
import pytest

from app.db.database import Base, engine
import app.db.models
import app.db.message_repository

@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)