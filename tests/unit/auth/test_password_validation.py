"""
Unit tests for password and email validation in app/auth/schemas.py.

These tests exercise the Pydantic field validators on UserRegisterRequest directly,
without making HTTP calls. They test the validation logic in isolation.

All tests will fail with ImportError until app/auth/schemas.py is implemented.
This is expected — the test suite starts in RED state.

Password policy (per docs/SECURITY.md Section 2):
  - Minimum 8 characters
  - At least one letter
  - At least one number
  - At least one allowed special character: @$!%*#?&
"""

import pytest
from pydantic import ValidationError

# This import will fail until app/auth/schemas.py exists (expected RED state).
from app.auth.schemas import UserRegisterRequest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_request(**overrides) -> dict:
    """
    Return a dict of valid registration data with optional field overrides.

    All values satisfy the password policy and field constraints by default.
    Override individual fields to test specific validation rules.
    """
    data = {
        "email": "test@example.com",
        "password": "Valid1234!",
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
    }
    data.update(overrides)
    return data


# ---------------------------------------------------------------------------
# Happy path — all fields valid
# ---------------------------------------------------------------------------


def test_valid_registration_data():
    """All fields valid — UserRegisterRequest should instantiate without error."""
    request = UserRegisterRequest(**make_request())
    assert request.email == "test@example.com"
    assert request.username == "testuser"
    # Password stored as original string (hashing happens in service).
    assert request.password == "Valid1234!"


# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------


def test_password_too_short():
    """Password shorter than 8 characters should raise ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        UserRegisterRequest(**make_request(password="weak"))
    errors = exc_info.value.errors()
    assert any("password" in str(e["loc"]) for e in errors), (
        f"Expected a validation error for the password field. Got: {errors}"
    )


def test_password_no_letters_no_special_chars():
    """All-numeric password should raise ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        UserRegisterRequest(**make_request(password="11111111111111"))
    errors = exc_info.value.errors()
    assert any("password" in str(e["loc"]) for e in errors), (
        f"Expected a validation error for the password field. Got: {errors}"
    )


def test_password_no_special_chars():
    """
    Password with letters and numbers but no special char should fail.

    'Weak1234' meets the 8-char, letter, and number requirements
    but lacks a special character from @$!%*#?&.
    """
    with pytest.raises(ValidationError) as exc_info:
        UserRegisterRequest(**make_request(password="Weak1234"))
    errors = exc_info.value.errors()
    assert any("password" in str(e["loc"]) for e in errors), (
        f"Expected a validation error for the password field. Got: {errors}"
    )


def test_password_no_letters():
    """Password with numbers and special chars but no letters should fail."""
    with pytest.raises(ValidationError) as exc_info:
        UserRegisterRequest(**make_request(password="1234!!!!!!"))
    errors = exc_info.value.errors()
    assert any("password" in str(e["loc"]) for e in errors), (
        f"Expected a validation error for the password field. Got: {errors}"
    )


def test_password_no_numbers_no_special_chars():
    """Letters-only password should raise ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        UserRegisterRequest(**make_request(password="WeakWeakWeakWeakWeak"))
    errors = exc_info.value.errors()
    assert any("password" in str(e["loc"]) for e in errors), (
        f"Expected a validation error for the password field. Got: {errors}"
    )


def test_password_with_disallowed_special_char():
    """
    Special char NOT in allowed set should raise ValidationError.

    Allowed: @$!%*#?&  — '£' is not in the allowed set.
    """
    with pytest.raises(ValidationError) as exc_info:
        UserRegisterRequest(**make_request(password="Valid123£"))
    errors = exc_info.value.errors()
    assert any("password" in str(e["loc"]) for e in errors), (
        f"Expected a validation error for the password field. Got: {errors}"
    )


def test_all_allowed_special_chars_accepted():
    """Each allowed special character should produce a valid password when used."""
    allowed = "@$!%*#?&"
    for char in allowed:
        password = f"Valid123{char}"
        request = UserRegisterRequest(**make_request(password=password))
        assert request.password == password, f"Password with allowed special char '{char}' should be accepted."


# ---------------------------------------------------------------------------
# Email validation
# ---------------------------------------------------------------------------


def test_email_valid():
    """A well-formed email address should be accepted."""
    request = UserRegisterRequest(**make_request(email="john.doe@example.com"))
    assert request.email == "john.doe@example.com"


def test_email_missing_domain():
    """Email with no domain after '@' should raise ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        UserRegisterRequest(**make_request(email="john.doe9@"))
    errors = exc_info.value.errors()
    assert any("email" in str(e["loc"]) for e in errors), (
        f"Expected a validation error for the email field. Got: {errors}"
    )


def test_email_missing_tld():
    """Email with domain but no TLD should raise ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        UserRegisterRequest(**make_request(email="john.doe9@example"))
    errors = exc_info.value.errors()
    assert any("email" in str(e["loc"]) for e in errors), (
        f"Expected a validation error for the email field. Got: {errors}"
    )


def test_email_missing_at_symbol():
    """Email with no '@' should raise ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        UserRegisterRequest(**make_request(email="notanemail"))
    errors = exc_info.value.errors()
    assert any("email" in str(e["loc"]) for e in errors), (
        f"Expected a validation error for the email field. Got: {errors}"
    )


# ---------------------------------------------------------------------------
# Username validation
# ---------------------------------------------------------------------------


def test_empty_username_rejected():
    """Empty username should raise ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        UserRegisterRequest(**make_request(username=""))
    errors = exc_info.value.errors()
    assert any("username" in str(e["loc"]) for e in errors), (
        f"Expected a validation error for the username field. Got: {errors}"
    )
