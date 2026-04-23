import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app import SessionLocal

# Use a test database file
TEST_DB_URL = "sqlite:///./test_game_collection.db"

TestEngine = create_engine(TEST_DB_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TestEngine)


@pytest.fixture(autouse=True, scope="session")
def setup_test_db():
    """Create tables once for the entire test session."""
    Base.metadata.create_all(bind=TestEngine)
    yield
    Base.metadata.drop_all(bind=TestEngine)


@pytest.fixture(scope="function")
def db_session():
    """Provide a transactional scope for each test."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function", autouse=True)
def clean_db(db_session):
    """Clean all data before each test."""
    db_session.execute(text("DELETE FROM achievements"))
    db_session.execute(text("DELETE FROM games"))
    db_session.execute(text("DELETE FROM users"))
    db_session.commit()


@pytest.fixture
def test_user(db_session):
    from app.auth import hash_password
    from app.models import User
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=hash_password("password123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user
