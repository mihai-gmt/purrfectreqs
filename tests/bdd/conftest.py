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
    Test-side session used by @given (setup) and @then (assertion) steps ONLY.

    This session is intentionally SEPARATE from the sessions the app uses
    during HTTP requests. Sharing a session across the test harness and the
    app makes the app's flushed-but-uncommitted writes visible to assertions,
    which hides transaction-boundary bugs (e.g. work that the app did but
    never committed still appears "persisted" to the test).

    Visibility rules (Postgres READ COMMITTED): any @given that writes must
    call `db_session.commit()` so the app can see it; any @then that reads
    must call `db_session.expire_all()` (already done in _get_user_from_db)
    so it re-reads from the DB and picks up whatever the app committed.
    """
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session
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
async def client(test_engine, db_session):  # noqa: ARG001
    """
    Async HTTP client pointed at the FastAPI test app.

    The get_db override builds a NEW session per request (same lifetime as
    production's get_db) and mirrors production's commit-on-success /
    rollback-on-exception semantics. This is deliberate: if the override
    simply yielded the test's db_session, the app's flushed-but-uncommitted
    writes would be visible to test assertions, masking rollback bugs.

    db_session is taken as a dependency (unused here) so the autouse
    clean_tables fixture and db_session fixture both resolve in the right
    order relative to the client.
    """
    app_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_db():
        async with app_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

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
