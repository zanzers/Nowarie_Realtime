import pytest
from unittest.mock import patch

from app.db.database import get_database_url

def test_missing_database_url_raises_value_error():
    with patch.dict("os.environ", {"DATABASE_URL" : ""}):
        with pytest.raises(ValueError, match="DATABASE_URL environment variable is not set"):
            get_database_url()


def test_database_url_is_returned():
    expected_url = "postgresql://test:test@localhost:5432/test_db"

    with patch.dict("os.environ", {"DATABASE_URL": expected_url}):
        result = get_database_url()
    
    assert result == expected_url
