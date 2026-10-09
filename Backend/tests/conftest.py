import pytest
from app.database.session import init_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Ensure database tables are initialized before tests execute."""
    init_db()
