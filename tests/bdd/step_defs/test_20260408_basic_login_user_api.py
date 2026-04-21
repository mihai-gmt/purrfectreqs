"""
BDD step definitions for: Basic Login User API
Feature file: tests/features/auth/20260408_basic_login_user_api.feature
Plan: tests/bdd/plans/auth_20260408_basic_login_user_api.plan.md

Covers 5 scenarios:
  - Successful login (200)
  - Incorrect credentials (401)
  - Account lockout on 5th failed attempt (403)
  - Reset failed_login_attempts and unlock on successful login (200)
  - Login fails when account is locked and lock not expired (403)

NOTE: All step functions are synchronous because pytest-bdd does not await
async step functions. Async operations (DB queries, HTTP calls) are run
via asyncio.get_event_loop().run_until_complete().
"""

import asyncio
import re as re_module
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from httpx import AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.password import hash_password

# Load all scenarios from the feature file.
# Path is relative to this step_defs directory.
scenarios("../../features/auth/20260408_basic_login_user_api.feature")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run(coro):
    """Run an async coroutine from a sync step function."""
    return asyncio.get_event_loop().run_until_complete(coro)


def _table_to_dict(datatable: list[list[str]]) -> dict:
    """
    Convert a pytest-bdd datatable (list of lists) to a dict.

    datatable[0] = header row
    datatable[1] = data row
    """
    headers = datatable[0]
    values = datatable[1]
    return dict(zip(headers, values))


def _post_login(client: AsyncClient, email: str, password: str):
    """POST /auth/login and return the response."""
    return _run(client.post("/auth/login", json={"email": email, "password": password}))


def _get_user_from_db(db_session: AsyncSession, email: str) -> User:
    """Re-query user from DB to get fresh state after an API call."""
    # Expire cached objects so the next query hits the database,
    # not SQLAlchemy's identity map with stale attribute values.
    db_session.expire_all()
    result = _run(db_session.execute(select(User).where(User.email == email)))
    user = result.scalars().first()
    assert user is not None, f"Expected user with email={email} in DB"
    return user


# ---------------------------------------------------------------------------
# Given steps
# ---------------------------------------------------------------------------


@given("the login API endpoint (POST auth/login) is available")
def login_endpoint_available():
    """No-op — endpoint existence is validated by the When step."""
    pass


@given("the user exists as a registered user with the details")
def user_exists_as_registered(datatable: list[list[str]], db_session: AsyncSession, context: dict):
    """
    Create a registered user in the test database with the given email and
    password. The password is hashed via argon2 before storage.

    Stores user_email in context so subsequent steps can look up the user.
    """
    data = _table_to_dict(datatable)
    user = User(
        email=data["email"],
        username="john.doe",
        hashed_password=hash_password(data["password"]),
        role="super_user",
        status="active",
        created_by=None,
    )
    db_session.add(user)
    _run(db_session.commit())
    _run(db_session.refresh(user))
    context["user_email"] = data["email"]
    context["user_id"] = user.id


@given(parsers.parse('the user account status is "{status}"'))
def set_user_account_status(status: str, db_session: AsyncSession, context: dict):
    """Update the test user's account status."""
    user = _get_user_from_db(db_session, context["user_email"])
    user.status = status
    _run(db_session.commit())
    _run(db_session.refresh(user))


@given("the user DB field failed_login_attempts is < 4")
def failed_login_attempts_less_than_4(db_session: AsyncSession, context: dict):
    """
    Set failed_login_attempts to a concrete value below 4.

    Uses 2 as the concrete value (per plan Section 8 Scenario 2).
    Records the value so the 'incremented by 1' Then step can verify.
    """
    user = _get_user_from_db(db_session, context["user_email"])
    user.failed_login_attempts = 2
    _run(db_session.commit())
    _run(db_session.refresh(user))
    context["failed_login_attempts_before"] = 2


@given("the user DB field failed_login_attempts is equal to 4")
def failed_login_attempts_equal_to_4(db_session: AsyncSession, context: dict):
    """Set failed_login_attempts to exactly 4 (one away from lockout)."""
    user = _get_user_from_db(db_session, context["user_email"])
    user.failed_login_attempts = 4
    _run(db_session.commit())
    _run(db_session.refresh(user))
    context["failed_login_attempts_before"] = 4


@given("the user db field locked_until is less than current timestamp")
def locked_until_in_past(db_session: AsyncSession, context: dict):
    """Set locked_until to 1 hour ago — lock has expired."""
    user = _get_user_from_db(db_session, context["user_email"])
    # Column is DateTime without timezone
    user.locked_until = datetime.now(UTC) - timedelta(hours=1)
    _run(db_session.commit())
    _run(db_session.refresh(user))


@given("the user db field locked_until is not less than current timestamp")
def locked_until_in_future(db_session: AsyncSession, context: dict):
    """Set locked_until to 1 hour from now — lock is still active."""
    user = _get_user_from_db(db_session, context["user_email"])
    # Column is DateTime without timezone
    user.locked_until = datetime.now(UTC) + timedelta(hours=1)
    _run(db_session.commit())
    _run(db_session.refresh(user))


@given("the user successfuly logs in with the correct details")
def user_logs_in_successfully_given(datatable: list[list[str]], client: AsyncClient, context: dict):
    """
    Scenario 4: the login action happens in this Given step.

    The When step ('the user is successfully logged in') is a state
    confirmation, not the action trigger. The HTTP request and response
    are captured here.
    """
    data = _table_to_dict(datatable)
    context["response"] = _post_login(client, data["email"], data["password"])


# ---------------------------------------------------------------------------
# When steps
# ---------------------------------------------------------------------------


@when("I login with my email address and password")
def login_with_credentials(datatable: list[list[str]], client: AsyncClient, context: dict):
    """POST /auth/login with the user's correct credentials."""
    data = _table_to_dict(datatable)
    context["response"] = _post_login(client, data["email"], data["password"])


@when("I try to login with incorrect username and password combination")
def try_login_incorrect(datatable: list[list[str]], client: AsyncClient, context: dict):
    """POST /auth/login with wrong credentials."""
    data = _table_to_dict(datatable)
    context["response"] = _post_login(client, data["email"], data["password"])


@when("the user logs in with incorrect email and password combination")
def user_logs_in_incorrect(datatable: list[list[str]], client: AsyncClient, context: dict):
    """POST /auth/login with wrong credentials (triggers lockout in Scenario 3)."""
    data = _table_to_dict(datatable)
    context["request_time"] = datetime.now(UTC)
    context["response"] = _post_login(client, data["email"], data["password"])


@when("the user is successfully logged in")
def user_is_successfully_logged_in(context: dict):
    """
    Scenario 4: state confirmation only.

    The login POST already happened in the Given step
    ('the user successfuly logs in with the correct details').
    """
    assert "response" in context, (
        "Expected response to be stored by the Given step. " "The login action must happen before this When step."
    )


@when("the user logs in with the correct details")
def user_logs_in_with_correct_details(datatable: list[list[str]], client: AsyncClient, context: dict):
    """POST /auth/login with correct credentials (Scenario 5: locked account)."""
    data = _table_to_dict(datatable)
    context["response"] = _post_login(client, data["email"], data["password"])


# ---------------------------------------------------------------------------
# Then steps
# ---------------------------------------------------------------------------


@then(parsers.parse("the response status is {status_code:d}"))
def assert_response_status(context: dict, status_code: int):
    """Assert the HTTP response status code."""
    assert context["response"].status_code == status_code, (
        f"Expected HTTP {status_code}, got {context['response'].status_code}. " f"Body: {context['response'].text}"
    )


@then(
    parsers.re(re_module.escape('response is wrapped in {"data": {...}, "message": ' '"...", "correlation_id": "..."}'))
)
def assert_success_envelope(context: dict):
    """Assert the response uses the ApiResponse success envelope."""
    body = context["response"].json()
    assert "data" in body, f"Expected 'data' in response. Got: {body}"
    assert "message" in body, f"Expected 'message' in response. Got: {body}"
    assert "correlation_id" in body, f"Expected 'correlation_id' in response. Got: {body}"


@then("response.data contains a valid authorization token")
def assert_valid_auth_token(context: dict):
    """
    Assert that response.data contains a JWT access token with expected
    claims: sub, role, exp, iat, jti.

    Decodes without signature verification — the test validates claim
    structure, not the signing key.
    """
    body = context["response"].json()
    data = body.get("data", {})
    access_token = data.get("access_token")
    assert access_token, f"Expected 'access_token' in response data. Got: {data}"
    assert data.get("token_type") == "bearer", f"Expected token_type='bearer', got '{data.get('token_type')}'"
    # Decode without verification to check claims structure
    decoded = jwt.decode(
        access_token,
        options={"verify_signature": False},
        algorithms=["HS256"],
    )
    assert "sub" in decoded, f"Expected 'sub' claim in JWT. Got: {decoded}"
    assert "role" in decoded, f"Expected 'role' claim in JWT. Got: {decoded}"
    assert "exp" in decoded, f"Expected 'exp' claim in JWT. Got: {decoded}"
    assert "iat" in decoded, f"Expected 'iat' claim in JWT. Got: {decoded}"
    assert "jti" in decoded, f"Expected 'jti' claim in JWT. Got: {decoded}"


@then(parsers.parse('message is "{message}"'))
def assert_message(context: dict, message: str):
    """Assert the exact message field in the response body."""
    body = context["response"].json()
    assert body.get("message") == message, (
        f"Expected message='{message}', got '{body.get('message')}'. " f"Full body: {body}"
    )


@then(parsers.parse('the message is "{message}"'))
def assert_the_message(context: dict, message: str):
    """Assert the exact message field in the response body (alternate wording)."""
    body = context["response"].json()
    assert body.get("message") == message, (
        f"Expected message='{message}', got '{body.get('message')}'. " f"Full body: {body}"
    )


@then("correlation_id is valid UUID")
def assert_correlation_id_valid(context: dict):
    """Assert the correlation_id in the response is a valid UUID."""
    body = context["response"].json()
    cid = body.get("correlation_id")
    assert cid, f"Expected 'correlation_id' in response. Got: {body}"
    try:
        uuid.UUID(cid)
    except (ValueError, AttributeError):
        raise AssertionError(f"Expected valid UUID for correlation_id, got: {cid}")


@then("correlation_id is a valid UUID")
def assert_correlation_id_a_valid(context: dict):
    """Assert the correlation_id in the response is a valid UUID (alternate wording)."""
    body = context["response"].json()
    cid = body.get("correlation_id")
    assert cid, f"Expected 'correlation_id' in response. Got: {body}"
    try:
        uuid.UUID(cid)
    except (ValueError, AttributeError):
        raise AssertionError(f"Expected valid UUID for correlation_id, got: {cid}")


@then(parsers.parse("failed_login_attempts is set to {count:d}"))
def assert_failed_login_attempts(context: dict, count: int, db_session: AsyncSession):
    """Assert the user's failed_login_attempts DB field equals the expected value."""
    user = _get_user_from_db(db_session, context["user_email"])
    assert user.failed_login_attempts == count, (
        f"Expected failed_login_attempts={count}, " f"got {user.failed_login_attempts}"
    )


@then(
    parsers.re(
        re_module.escape(
            "the response is wrapped in "
            '{"error_code": ..., "message": \u2026, '
            '"correlation_id": \u2026, "details": {}}'
        )
    )
)
def assert_error_envelope(context: dict):
    """Assert the response uses the error envelope structure."""
    body = context["response"].json()
    assert "error_code" in body, f"Expected 'error_code' in response. Got: {body}"
    assert "message" in body, f"Expected 'message' in response. Got: {body}"
    assert "correlation_id" in body, f"Expected 'correlation_id' in response. Got: {body}"
    assert "details" in body, f"Expected 'details' in response. Got: {body}"


@then(parsers.parse('the error_code is "{code}"'))
def assert_error_code(context: dict, code: str):
    """Assert the error_code field matches the expected value."""
    body = context["response"].json()
    assert body.get("error_code") == code, (
        f"Expected error_code='{code}', got '{body.get('error_code')}'. " f"Full body: {body}"
    )


@then("response.details is empty")
def assert_details_empty(context: dict):
    """Assert the details field in the error response is empty."""
    body = context["response"].json()
    details = body.get("details")
    assert details == {} or details is None or details == [], f"Expected empty details, got: {details}"


@then("the user DB field failed_login_attempts is incremented by 1")
def assert_failed_login_attempts_incremented(context: dict, db_session: AsyncSession):
    """Assert failed_login_attempts increased by 1 from the recorded baseline."""
    user = _get_user_from_db(db_session, context["user_email"])
    before = context.get("failed_login_attempts_before", 0)
    expected = before + 1
    assert user.failed_login_attempts == expected, (
        f"Expected failed_login_attempts={expected} (was {before}), " f"got {user.failed_login_attempts}"
    )


@then("the user DB field failed_login_attempts reaches 5")
def assert_failed_login_attempts_reaches_5(context: dict, db_session: AsyncSession):
    """Assert failed_login_attempts is now 5 (lockout threshold)."""
    user = _get_user_from_db(db_session, context["user_email"])
    assert user.failed_login_attempts == 5, f"Expected failed_login_attempts=5, got {user.failed_login_attempts}"


@then(parsers.parse('the user account status is updated to "{status}"'))
def assert_user_status_updated(context: dict, status: str, db_session: AsyncSession):
    """Assert the user's account status was changed to the expected value."""
    user = _get_user_from_db(db_session, context["user_email"])
    assert user.status.value == status, f"Expected status='{status}', got '{user.status.value}'"


@then("the user DB field locked_until is updated with " "UTC aware timestamp of request plus 30 minutes")
def assert_locked_until_set(context: dict, db_session: AsyncSession):
    """
    Assert locked_until is approximately request_time + 30 minutes.

    Allows 60-second tolerance for test execution time.
    """
    user = _get_user_from_db(db_session, context["user_email"])
    assert user.locked_until is not None, "Expected locked_until to be set"
    request_time = context.get("request_time", datetime.now(UTC))
    expected = request_time + timedelta(minutes=30)
    delta = abs((user.locked_until - expected).total_seconds())
    assert delta < 60, f"Expected locked_until ~{expected}, got {user.locked_until} " f"(delta: {delta}s)"


@then(parsers.parse('the account status is set to "{status}"'))
def assert_account_status_set(context: dict, status: str, db_session: AsyncSession):
    """Assert the user's account status matches the expected value."""
    user = _get_user_from_db(db_session, context["user_email"])
    assert user.status.value == status, f"Expected status='{status}', got '{user.status.value}'"


@then(parsers.parse("the user DB field failed_login_attempts is set to {count:d}"))
def assert_user_db_failed_login_set(context: dict, count: int, db_session: AsyncSession):
    """Assert the user's failed_login_attempts DB field equals the expected value."""
    user = _get_user_from_db(db_session, context["user_email"])
    assert user.failed_login_attempts == count, (
        f"Expected failed_login_attempts={count}, " f"got {user.failed_login_attempts}"
    )
