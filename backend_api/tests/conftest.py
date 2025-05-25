import pytest
import asyncio
import os
import pathlib
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Set environment variables for tests *before* other modules are imported
# This ensures that the application modules pick up these test-specific settings at import time.
TEST_API_KEY = "test_api_key_12345_very_secret"
# Use a distinct directory for test databases to avoid any conflict and simplify cleanup.
TEST_DATA_DIR = pathlib.Path("./test_app_data")
TEST_DB_FILENAME = "test_database.db"
TEST_DB_PATH = TEST_DATA_DIR / TEST_DB_FILENAME
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH.resolve()}" # Use absolute path for engine

os.environ["API_KEY"] = TEST_API_KEY
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# Now that env vars are set, we can import app-related modules
from backend_api.main import app  # FastAPI application
from backend_api.database import metadata as app_metadata # Use the app's metadata

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    # policy = asyncio.get_event_loop_policy()
    # res = policy.new_event_loop()
    # asyncio.set_event_loop(res)
    # res._close = res.close
    # return res
    # Pytest-asyncio default mode 'auto' should handle this. If issues, uncomment above.
    # For now, let pytest-asyncio manage the loop.
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    """
    Creates a test SQLAlchemy engine, creates all tables, and cleans up the
    database file after the test session.
    """
    # Ensure the test data directory exists
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Remove the test database file if it exists from a previous run
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    print(f"Creating test database engine for: {TEST_DATABASE_URL}")
    engine = create_async_engine(TEST_DATABASE_URL, echo=False) # Set echo=True for SQL logging

    async with engine.begin() as conn:
        print(f"Creating tables in test database: {TEST_DB_PATH}")
        await conn.run_sync(app_metadata.create_all)

    yield engine # Provide the engine to tests

    # Teardown: close connections and remove the database file
    print(f"Closing test database engine for: {TEST_DATABASE_URL}")
    await engine.dispose()

    if TEST_DB_PATH.exists():
        print(f"Removing test database: {TEST_DB_PATH}")
        TEST_DB_PATH.unlink()
    # Optionally remove the test_app_data directory if empty or if desired
    # try:
    #     TEST_DATA_DIR.rmdir() # Only removes if empty
    # except OSError:
    #     pass # Directory not empty, or other error

@pytest.fixture
async def db_session(test_engine):
    """
    Provides a clean SQLAlchemy AsyncSession for each test function.
    This session is suitable for direct database manipulations within tests.
    It rolls back transactions to ensure test isolation.
    """
    async_session_factory = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_factory() as session:
        # Optionally begin a transaction here if you want each test to run in one.
        # await session.begin()
        yield session
        # Rollback any changes made during the test
        # await session.rollback()
        await session.close()


@pytest.fixture
async def async_client(test_engine): # Depends on test_engine to ensure DB is set up
    """
    Provides an HTTPX AsyncClient for making requests to the FastAPI app.
    The app is configured to use the test database because DATABASE_URL
    was overridden before the app was imported.
    """
    # The app's database connection is managed globally based on DATABASE_URL.
    # We need to ensure the app's database is connected before tests run
    # and disconnected after. This is typically handled by app startup/shutdown events.
    # The AsyncClient context manager for FastAPI apps handles this.
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        yield client

@pytest.fixture
def test_api_key():
    """Provides the API key used for testing."""
    return TEST_API_KEY

@pytest.fixture
async def authenticated_async_client(async_client: AsyncClient, test_api_key: str):
    """
    Provides an HTTPX AsyncClient that is pre-authenticated with the test API key.
    """
    async_client.headers[os.environ.get("API_KEY_NAME", "X-API-Key")] = test_api_key
    yield async_client
