"""
BDD step definitions for: New User Account Registration
Feature file: tests/features/auth/20260407_basic_register_user_api.feature
Plan: tests/bdd/plans/auth_20260407_basic_register_user_api.plan.md

Covers 11 scenarios:
  - Happy path: successful registration
  - Duplicate email (409)
  - Duplicate username (409)
  - Password too short (422)
  - Missing required fields (422)
  - Password: no letters or special chars (422)
  - Password: no special chars (422)
  - Password: no letters (422)
  - Password: no numbers or special chars (422)
  - Email missing domain (422)
  - Email missing domain suffix (422)

NOTE: All step functions are synchronous because pytest-bdd does not await
async step functions. Async operations (DB queries, HTTP calls) are run
via asyncio.get_event_loop().run_until_complete(). This works because
pytest-asyncio's event loop is idle during sync test body execution.
"""

import asyncio

from httpx import AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Load all scenarios from the feature file.
# Path is relative to this step_defs directory.
scenarios("../../features/auth/20260407_basic_register_user_api.feature")


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

    Empty string values are preserved as-is so that missing-field
    scenarios correctly send empty strings to the API.
    """
    headers = datatable[0]
    values = datatable[1]
    return dict(zip(headers, values, strict=True))


# ---------------------------------------------------------------------------
# Given steps
# ---------------------------------------------------------------------------


@given(parsers.parse("no user account exist for the following user registration data:"))
def no_user_exists_for_data(datatable: list[list[str]], db_session: AsyncSession):
    """
    Verify the test database contains no user with the given email or username.

    The datatable has columns: email, password, username.
    This step confirms we are starting from a clean state.
    """
    from app.auth.models import User

    data = _table_to_dict(datatable)
    email = data["email"]
    username = data["username"]

    result = _run(db_session.execute(select(User).where((User.email == email) | (User.username == username))))
    existing = result.scalars().first()
    assert existing is None, (
        f"Expected no user with email={email} or username={username}, but found one. Clean up test data before running."
    )


@given(parsers.parse('an account already exists with the email address "{email}"'))
def account_exists_with_email(email: str, db_session: AsyncSession, context: dict):
    """
    Create a user with the given email address in the test database.

    Used to set up the pre-condition for duplicate-email rejection tests.
    Password is hashed; username is derived from the email local part.
    Records user_count_before so account_not_created can verify no new
    account was added.
    """
    from sqlalchemy import func as sa_func

    from app.auth.models import User
    from app.auth.password import hash_password

    user = User(
        email=email,
        username="existing.user",
        hashed_password=hash_password("Existing1!"),
        role="super_user",
        status="active",
        created_by=None,
    )
    db_session.add(user)
    _run(db_session.commit())
    _run(db_session.refresh(user))

    # Record total user count AFTER seeding so account_not_created
    # can verify no additional user was created.
    result = _run(db_session.execute(select(sa_func.count()).select_from(User)))
    context["user_count_before"] = result.scalar()


@given(parsers.parse('an account already exists with email address "{email}" and username "{username}"'))
def account_exists_with_email_and_username(
    email: str,
    username: str,
    db_session: AsyncSession,
    context: dict,
):
    """
    Create a user with the given email and username in the test database.

    Used to set up the pre-condition for duplicate-username rejection tests.
    Records user_count_before so account_not_created can verify no new
    account was added.
    """
    from sqlalchemy import func as sa_func

    from app.auth.models import User
    from app.auth.password import hash_password

    user = User(
        email=email,
        username=username,
        hashed_password=hash_password("Existing1!"),
        role="super_user",
        status="active",
        created_by=None,
    )
    db_session.add(user)
    _run(db_session.commit())
    _run(db_session.refresh(user))

    # Record count so account_not_created can verify no new user was added.
    # Note: the attempted email in the When step may differ from this email
    # (e.g., username-duplicate scenario uses a different email). The count
    # is stored generically; account_not_created checks by attempted_email.
    result = _run(db_session.execute(select(sa_func.count()).select_from(User)))
    context["user_count_before"] = result.scalar()


# ---------------------------------------------------------------------------
# When steps
# ---------------------------------------------------------------------------


@when("I register with the following details:")
def register_with_details(
    datatable: list[list[str]],
    client: AsyncClient,
    context: dict,
):
    """
    POST /auth/register with the data from the step's inline table.

    Table columns: email, password, username, first_name, last_name.
    The raw payload (including empty strings) is sent so that missing-field
    validation scenarios are exercised correctly.

    Stores both the response and the attempted email in context for Then steps.
    """
    payload = _table_to_dict(datatable)

    # Store the attempted email so Then steps can query the DB by it.
    context["attempted_email"] = payload.get("email", "")

    # Remove keys with empty string values to simulate missing fields.
    # An empty password or username means the field was intentionally omitted.
    clean_payload = {k: v for k, v in payload.items() if v != ""}

    response = _run(client.post("/auth/register", json=clean_payload))
    context["response"] = response


# ---------------------------------------------------------------------------
# Then steps
# ---------------------------------------------------------------------------


@then('my account is created with status "active" and role "super_user"')
def account_created_with_correct_status_and_role(
    context: dict,
    db_session: AsyncSession,
):
    """
    Verify the new user record exists in the DB with status=active
    and role=super_user.
    """
    from app.auth.models import User

    email = context["attempted_email"]
    result = _run(db_session.execute(select(User).where(User.email == email)))
    user = result.scalars().first()

    assert user is not None, f"Expected user with email={email} to exist in DB after successful registration."
    assert user.status.value == "active", f"Expected status='active', got '{user.status}'."
    assert user.role.value == "super_user", f"Expected role='super_user', got '{user.role}'."


@then(parsers.parse("I receive a {status_code:d} response"))
def assert_status_code(context: dict, status_code: int):
    """Assert the HTTP response status code."""
    assert context["response"].status_code == status_code, (
        f"Expected HTTP {status_code}, got {context['response'].status_code}. Body: {context['response'].text}"
    )


@then("I receive a confirmation message that my account was created")
def assert_confirmation_message_present(context: dict):
    """Assert that the response body contains a 'message' field."""
    body = context["response"].json()
    assert "message" in body, f"Expected 'message' field in response body. Got: {body}"
    assert body["message"], f"Expected non-empty 'message' field in response body. Got: {body}"


@then(parsers.parse('the message is "{message}"'))
def assert_success_message(context: dict, message: str):
    """Assert the exact success message returned in the response body."""
    body = context["response"].json()
    assert body.get("message") == message, (
        f"Expected message='{message}', got '{body.get('message')}'. Full body: {body}"
    )


@then("my account is not created")
def account_not_created(context: dict, db_session: AsyncSession):
    """
    Verify no NEW user was created by the registration attempt.

    For duplicate-email/username scenarios, a pre-existing user was created
    in the Given step. This step checks that the total user count did not
    increase — i.e., the registration was rejected and no second account
    was created. For validation-failure scenarios (no Given step), it
    confirms no user exists at all.
    """
    from sqlalchemy import func as sa_func

    from app.auth.models import User

    result = _run(db_session.execute(select(sa_func.count()).select_from(User)))
    count_now = result.scalar()
    count_before = context.get("user_count_before", 0)

    assert count_now == count_before, (
        f"Expected total user count to remain at {count_before}, "
        f"but it is now {count_now}. A rejected registration should "
        f"not create any new users."
    )


@then(parsers.parse('the response message is "{message}"'))
def assert_error_message(context: dict, message: str):
    """Assert the exact error message returned in the response body."""
    body = context["response"].json()
    assert body.get("message") == message, (
        f"Expected message='{message}', got '{body.get('message')}'. Full body: {body}"
    )
