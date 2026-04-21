"""
Shared fixtures for BDD tests.

This module provides:
- async test HTTP client (httpx.AsyncClient via ASGI transport)
- async database session (isolated test database, rolled back after each test)
- context dict for passing data between Given/When/Then steps within a scenario

All imports from app/ will fail with ImportError until the implementation exists.
This is expected — the test suite starts in RED state.
"""

import os

import pytest
import pytest_asyncio
from dotenv import load_dotenv

# Load .env so TEST_DATABASE_URL is available via os.getenv().
# Without this, only shell-exported variables are visible and the
# fallback default (purrfect:purrfect) would be used instead.
load_dotenv()
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Import all models so Base.metadata knows about them when create_all() is called.
# This import fails (ImportError) until app/auth/models.py is created.
import app.auth.models  # noqa: F401, E402

# These imports fail (ImportError) until implementation exists. Expected RED state.
from app.core.database import Base, get_db  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402

# ---------------------------------------------------------------------------
# Test database
# ---------------------------------------------------------------------------

# Use TEST_DATABASE_URL if set, otherwise fall back to the app's DATABASE_URL.
# This means tests run against the same DB as the app — the clean_tables fixture
# truncates tables before/after each test to keep data isolated.
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")

# ---------------------------------------------------------------------------
# Engine — session-scoped: tables created once per test session
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """
    Create the async engine for the test database.

    Creates all tables at session start and drops them at session end.
    Uses a separate test database to keep dev data untouched.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


# ---------------------------------------------------------------------------
# Database session — function-scoped: rolled back after each test
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def db_session(test_engine):
    """
    Provide an isolated async database session for one test.

    Uses a session factory against the test engine. After each test the
    session is rolled back so any changes (including committed ones from
    the app) are undone before the next test starts.

    The client fixture overrides get_db to use this same session, so all
    database operations during a test go through one place.
    """
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session
        # Roll back any uncommitted state. Committed rows are cleaned up
        # by the autouse clean_tables fixture below.
        await session.rollback()


@pytest_asyncio.fixture(autouse=True)
async def clean_tables(test_engine):
    """
    Truncate user-facing tables before AND after every test.

    Runs automatically for every test function (autouse=True).
    Pre-test cleanup ensures each scenario starts with a clean database
    regardless of what the previous test committed — critical for scenarios
    that use a Given step to create pre-existing records (e.g. duplicate-email
    test), where a Then step must assert no *new* record was created.

    Post-test cleanup is kept as a safety net.
    """
    # --- pre-test cleanup ---
    try:
        from sqlalchemy import delete

        from app.auth.models import User

        async with test_engine.begin() as conn:
            await conn.execute(delete(User))
    except ImportError:
        pass  # Models don't exist yet — nothing to clean up

    yield

    # --- post-test cleanup ---
    try:
        from sqlalchemy import delete

        from app.auth.models import User

        async with test_engine.begin() as conn:
            await conn.execute(delete(User))
    except ImportError:
        pass  # Models don't exist yet — nothing to clean up


# ---------------------------------------------------------------------------
# FastAPI test client — uses the test database session
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def client(db_session):
    """
    Async HTTP client pointed at the FastAPI test app.

    Overrides the get_db dependency so every request the app makes
    during a test uses the same isolated test session.
    """

    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://test",
    ) as ac:
        yield ac

    fastapi_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Context — carries state between Given / When / Then steps
# ---------------------------------------------------------------------------


@pytest.fixture
def context() -> dict:
    """
    Shared mutable dict for a single scenario.

    Step definitions store the HTTP response in context["response"] so
    Then steps can assert on it without needing module-level variables.
    Each scenario gets its own fresh dict.
    """
    return {}
