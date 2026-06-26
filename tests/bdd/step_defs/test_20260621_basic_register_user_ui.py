"""
BDD step definitions for: Browser User Account Registration UI
Feature file: tests/features/auth/20260621_basic_register_user_ui.feature
Plan: tests/bdd/plans/auth_20260621_basic_register_user_ui.plan.md

Covers 3 UI scenarios:
  - Successful browser registration redirects to the login page
  - Duplicate email re-renders the registration page with an exact error
  - Honeypot-filled bot submission silently redirects without creating a user

All step functions are synchronous because pytest-bdd does not await async step
functions. Async DB and HTTP calls are run through the shared _run() helper.
"""

import asyncio
import re

from httpx import AsyncClient, Response
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

scenarios("../../features/auth/20260621_basic_register_user_ui.feature")

HTML_HEADERS = {"Accept": "text/html"}
CORRELATION_ID = "11111111-1111-4111-8111-111111111111"
DUPLICATE_EMAIL_ERROR = "Email address already in use. Please login with your existing account!"
TOKEN_COOKIE_NAMES = ("access_token", "refresh_token")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run(coro):
    """Run an async coroutine from a sync pytest-bdd step function."""
    return asyncio.get_event_loop().run_until_complete(coro)


def _table_to_dict(datatable: list[list[str]]) -> dict[str, str]:
    """Convert a one-row pytest-bdd datatable into a dictionary."""
    headers = datatable[0]
    values = datatable[1]
    return dict(zip(headers, values, strict=True))


def _html_headers_with_correlation(context: dict) -> dict[str, str]:
    """Return browser headers with a stable correlation ID for log assertions."""
    correlation_id = context.setdefault("correlation_id", CORRELATION_ID)
    return {**HTML_HEADERS, "X-Correlation-ID": correlation_id}


def _assert_html_response(response: Response) -> None:
    """Assert a response is HTML so UI tests do not accidentally exercise JSON paths."""
    content_type = response.headers.get("content-type", "")
    assert "text/html" in content_type, (
        f"Expected a text/html response, got content-type={content_type!r}. Body: {response.text}"
    )


def _extract_honeypot_field_name(html: str) -> str:
    """
    Extract the honeypot field name from rendered HTML.

    The feature does not mandate the field name, only that a hidden honeypot
    exists. Reading it from the page keeps the test focused on browser behavior.
    """
    input_tags = re.findall(r"<input\b[^>]*>", html, flags=re.IGNORECASE)
    for tag in input_tags:
        if "hp-field" not in tag:
            continue
        name_match = re.search(r"\bname=[\"']([^\"']+)[\"']", tag, flags=re.IGNORECASE)
        if name_match:
            return name_match.group(1)
    raise AssertionError("Expected a honeypot input with CSS class 'hp-field' and a name attribute.")


def _response_set_cookie_header(response: Response) -> str:
    """Return all Set-Cookie headers as a single string for portable assertions."""
    return "; ".join(response.headers.get_list("set-cookie"))


async def _get_user_by_email(db_session: AsyncSession, email: str):
    """Read a user by email after expiring the test session transaction cache."""
    from app.auth.models import User

    db_session.expire_all()
    result = await db_session.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def _count_users(db_session: AsyncSession) -> int:
    """Count committed users after expiring the test session transaction cache."""
    from app.auth.models import User

    db_session.expire_all()
    result = await db_session.execute(select(sa_func.count()).select_from(User))
    return int(result.scalar() or 0)


# ---------------------------------------------------------------------------
# Given / Background steps
# ---------------------------------------------------------------------------


@given("I am an unauthenticated visitor")
def unauthenticated_visitor(context: dict):
    """Record that this scenario intentionally sends no auth header or cookies."""
    context["auth_headers"] = {}


@given(parsers.parse('I am on the registration page at "{path}"'))
def on_registration_page(path: str, client: AsyncClient, context: dict):
    """Request the full registration page as a browser would."""
    response = _run(client.get(path, headers=_html_headers_with_correlation(context)))
    context["registration_page_response"] = response
    context["registration_path"] = path


@given("the page is server-rendered HTML containing a registration form")
def registration_page_contains_form(context: dict):
    """Assert the registration page is a full HTML page with a POST form."""
    response = context["registration_page_response"]
    assert response.status_code == 200, (
        f"Expected GET registration page to return HTTP 200, got {response.status_code}. Body: {response.text}"
    )
    _assert_html_response(response)
    html = response.text
    assert "<html" in html.lower(), f"Expected full server-rendered HTML page. Body: {html}"
    assert "<form" in html.lower(), f"Expected registration form in HTML. Body: {html}"
    assert 'method="post"' in html.lower() or "method='post'" in html.lower(), (
        f"Expected registration form to submit with POST. Body: {html}"
    )
    assert context["registration_path"] in html, (
        f"Expected form/page to reference {context['registration_path']!r}. Body: {html}"
    )


@given("the form includes a hidden honeypot field")
def form_includes_honeypot(context: dict):
    """Assert the form exposes a CSP-safe hidden honeypot field."""
    html = context["registration_page_response"].text
    field_name = _extract_honeypot_field_name(html)
    context["honeypot_field_name"] = field_name
    assert 'tabindex="-1"' in html or "tabindex='-1'" in html, (
        f"Expected honeypot field to be removed from tab order. Body: {html}"
    )
    assert 'aria-hidden="true"' in html or "aria-hidden='true'" in html, (
        f"Expected honeypot field to be hidden from assistive tech. Body: {html}"
    )
    assert 'autocomplete="off"' in html or "autocomplete='off'" in html, (
        f"Expected honeypot field autocomplete to be off. Body: {html}"
    )
    assert "style=" not in html.lower(), f"Expected no inline styles for honeypot hiding. Body: {html}"


@given(parsers.parse('no account exists for the email "{email}" or the username "{username}"'))
def no_account_exists_for_email_or_username(
    email: str,
    username: str,
    db_session: AsyncSession,
    context: dict,
):
    """Verify the database starts without the target email or username."""
    from app.auth.models import User

    _run(db_session.expire_all()) if asyncio.iscoroutinefunction(db_session.expire_all) else db_session.expire_all()
    result = _run(db_session.execute(select(User).where((User.email == email) | (User.username == username))))
    existing = result.scalars().first()
    assert existing is None, f"Expected no user with email={email} or username={username}, found {existing!r}."
    context["user_count_before"] = _run(_count_users(db_session))


@given(parsers.parse('an account already exists with the email "{email}"'))
def account_already_exists_with_email(email: str, db_session: AsyncSession, context: dict):
    """Seed a committed existing user for the duplicate-email scenario."""
    from app.auth.models import User
    from app.auth.password import hash_password

    user = User(
        email=email,
        username="existing.user",
        hashed_password=hash_password("Existing1!"),
        role="super_user",
        status="active",
        created_by=None,
        updated_by=None,
    )
    db_session.add(user)
    _run(db_session.commit())
    _run(db_session.refresh(user))
    context["user_count_before"] = _run(_count_users(db_session))


# ---------------------------------------------------------------------------
# When steps
# ---------------------------------------------------------------------------


@when("I fill in the registration form with:")
def fill_registration_form(datatable: list[list[str]], context: dict):
    """Store browser form fields from the scenario datatable."""
    payload = _table_to_dict(datatable)
    context["form_payload"] = payload
    context["attempted_email"] = payload["email"]
    context["attempted_username"] = payload["username"]


@when("I leave the hidden honeypot field empty")
def leave_honeypot_empty(context: dict):
    """Set the rendered honeypot field to an empty value."""
    field_name = context.get("honeypot_field_name", "website")
    context.setdefault("form_payload", {})[field_name] = ""


@when(parsers.parse('the hidden honeypot field is filled with "{value}"'))
def fill_honeypot(value: str, context: dict):
    """Set the rendered honeypot field to a bot-like value."""
    field_name = context.get("honeypot_field_name", "website")
    context.setdefault("form_payload", {})[field_name] = value


@when("I submit the registration form")
def submit_registration_form(client: AsyncClient, context: dict):
    """POST the form as a browser and keep redirects disabled for 303 assertions."""
    response = _run(
        client.post(
            context.get("registration_path", "/auth/register"),
            data=context["form_payload"],
            headers=_html_headers_with_correlation(context),
            follow_redirects=False,
        )
    )
    context["response"] = response


# ---------------------------------------------------------------------------
# Then steps
# ---------------------------------------------------------------------------


@then('my account is created with status "active" and role "super_user"')
def account_created_with_status_and_role(context: dict, db_session: AsyncSession):
    """Verify successful browser registration persisted an active super_user."""
    user = _run(_get_user_by_email(db_session, context["attempted_email"]))
    assert user is not None, f"Expected user with email={context['attempted_email']} to be created."
    assert user.status.value == "active", f"Expected status='active', got {user.status!r}."
    assert user.role.value == "super_user", f"Expected role='super_user', got {user.role!r}."


@then("no authentication tokens or cookies are issued by registration")
def no_auth_tokens_or_cookies_issued(context: dict):
    """Registration must not log the browser in or set auth cookies."""
    response = context["response"]
    set_cookie = _response_set_cookie_header(response).lower()
    for cookie_name in TOKEN_COOKIE_NAMES:
        assert cookie_name not in response.cookies, (
            f"Expected registration not to set {cookie_name!r}; cookies were {response.cookies}."
        )
        assert cookie_name not in set_cookie, (
            f"Expected Set-Cookie not to contain {cookie_name!r}; Set-Cookie was {set_cookie!r}."
        )


@then(parsers.parse('I receive an HTTP 303 redirect with the Location header set to "{location}"'))
def receive_303_redirect_to_location(location: str, context: dict):
    """Assert the browser registration response is a See Other redirect."""
    response = context["response"]
    assert response.status_code == 303, f"Expected HTTP 303, got {response.status_code}. Body: {response.text}"
    assert response.headers.get("location") == location, (
        f"Expected Location={location!r}, got {response.headers.get('location')!r}. Headers: {response.headers}"
    )


@then("my browser lands on the login page")
def browser_lands_on_login_page(client: AsyncClient, context: dict):
    """Follow the redirect manually and assert the placeholder login page is HTML."""
    location = context["response"].headers.get("location")
    landing_response = _run(client.get(location, headers=_html_headers_with_correlation(context)))
    context["login_page_response"] = landing_response
    assert landing_response.status_code == 200, (
        f"Expected login page to return HTTP 200, got {landing_response.status_code}. Body: {landing_response.text}"
    )
    _assert_html_response(landing_response)
    assert "login" in landing_response.text.lower(), (
        f"Expected redirected page to be the login page. Body: {landing_response.text}"
    )


@then("no new account is created")
def no_new_account_created(context: dict, db_session: AsyncSession):
    """Verify duplicate-email rejection did not add another user record."""
    count_now = _run(_count_users(db_session))
    count_before = context.get("user_count_before", 0)
    assert count_now == count_before, (
        f"Expected user count to remain {count_before}, got {count_now}. A rejected registration created a user."
    )


@then("I receive an HTTP 409 response")
def receive_409_response(context: dict):
    """Assert duplicate email returns HTTP 409 to the browser."""
    response = context["response"]
    assert response.status_code == 409, f"Expected HTTP 409, got {response.status_code}. Body: {response.text}"
    _assert_html_response(response)


@then("I remain on the registration page")
def remain_on_registration_page(context: dict):
    """Assert the 409 response re-renders the registration page/form."""
    response = context["response"]
    html = response.text
    assert "<form" in html.lower(), f"Expected re-rendered registration form. Body: {html}"
    assert context.get("registration_path", "/auth/register") in html, (
        f"Expected response to remain on registration form for {context.get('registration_path')!r}. Body: {html}"
    )


@then(parsers.parse('the form displays the error message "{message}"'))
def form_displays_error_message(message: str, context: dict):
    """Assert the duplicate-email error is displayed verbatim in the HTML form."""
    response = context["response"]
    assert message == DUPLICATE_EMAIL_ERROR, "The feature's duplicate-email message changed unexpectedly."
    assert message in response.text, f"Expected error message {message!r} in HTML. Body: {response.text}"


@then("no account is created")
def no_account_created(context: dict, db_session: AsyncSession):
    """Verify honeypot rejection created no attempted account and no extra users."""
    user = _run(_get_user_by_email(db_session, context["attempted_email"]))
    assert user is None, f"Expected no user with email={context['attempted_email']} to be created."
    count_now = _run(_count_users(db_session))
    count_before = context.get("user_count_before", 0)
    assert count_now == count_before, f"Expected user count {count_before}, got {count_now}."


@then("the response is indistinguishable from a successful registration")
def response_indistinguishable_from_success(context: dict):
    """Assert bot rejection exposes the same browser-visible shape as success."""
    response = context["response"]
    assert response.status_code == 303, f"Expected success-shaped HTTP 303, got {response.status_code}."
    assert response.headers.get("location") == "/auth/login", (
        f"Expected success-shaped Location '/auth/login', got {response.headers.get('location')!r}."
    )
    no_auth_tokens_or_cookies_issued(context)


@then("the bot detection event is logged at WARNING level with the correlation ID")
def bot_detection_logged_with_correlation_id(caplog, context: dict):
    """Assert honeypot detection is logged as a warning tied to the request correlation ID."""
    correlation_id = context["correlation_id"]
    warning_records = [record for record in caplog.records if record.levelname == "WARNING"]
    assert warning_records, "Expected at least one WARNING log record for honeypot bot detection."
    matching_records = [
        record
        for record in warning_records
        if getattr(record, "correlation_id", None) == correlation_id
        and ("honeypot" in record.getMessage().lower() or "bot" in record.getMessage().lower())
    ]
    assert matching_records, (
        "Expected a WARNING log mentioning honeypot/bot with "
        f"correlation_id={correlation_id}. Warning logs: "
        f"{[(record.getMessage(), getattr(record, 'correlation_id', None)) for record in warning_records]}"
    )
