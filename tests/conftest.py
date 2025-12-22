"""Pytest configuration and shared fixtures."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.main import app, get_db
from backend.app.database import Base, User, Conversation, Message


# In-memory database for testing
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db():
    """Create test database and tables."""
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session):
    """Create test client with overridden database."""
    app.dependency_overrides[get_db] = override_get_db
    
    client = TestClient(app)
    yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db: Session):
    """Create a test user."""
    user = User(
        username="testuser",
        password_hash=User.hash_password("password123")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_user_2(db: Session):
    """Create a second test user."""
    user = User(
        username="testuser2",
        password_hash=User.hash_password("password456")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_conversation(db: Session, test_user: User):
    """Create a test conversation."""
    conv = Conversation(
        user_id=test_user.id,
        title="Test Conversation"
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@pytest.fixture
def test_messages(db: Session, test_conversation: Conversation):
    """Create test messages."""
    messages = [
        Message(
            conversation_id=test_conversation.id,
            role="user",
            content="Hello, how are you?"
        ),
        Message(
            conversation_id=test_conversation.id,
            role="assistant",
            content="I'm doing well, thank you!"
        ),
    ]
    db.add_all(messages)
    db.commit()
    for msg in messages:
        db.refresh(msg)
    return messages


@pytest.fixture
def mock_query_request():
    """Mock query request payload."""
    return {
        "query": "What is depression?",
        "user_id": "default",
        "session_id": None
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "auth: mark test as authentication test"
    )
    config.addinivalue_line(
        "markers", "conversation: mark test as conversation test"
    )
    config.addinivalue_line(
        "markers", "message: mark test as message test"
    )
    config.addinivalue_line(
        "markers", "dsm5: mark test as DSM-5 tool test"
    )
    config.addinivalue_line(
        "markers", "cypher: mark test as Cypher query test"
    )
