"""
Pydantic schemas for the auth module.

These define the shape of data coming IN (requests) and going OUT (responses)
for auth endpoints. They are completely independent of models.py — never
import SQLAlchemy models here.

Why keep schemas separate from models?
  - Schemas validate and sanitise EXTERNAL data (user input, API clients).
  - Models describe INTERNAL data (how it's stored in PostgreSQL).
  - Keeping them separate means you can change one without touching the other,
    and you control exactly what data the API exposes.
"""

import re

from pydantic import BaseModel, ConfigDict, field_validator

# ---------------------------------------------------------------------------
# Validation constants
# ---------------------------------------------------------------------------

# Password policy (docs/SECURITY.md Section 2):
#   - Minimum 8 characters
#   - At least one letter
#   - At least one digit
#   - At least one special character from the allowed set: @$!%*#?&
#   - No characters outside letters, digits, and the allowed special chars
#
# Why regex over separate checks?
#   A single compiled pattern is faster at runtime and easier to audit —
#   all password rules live in one place.
_PASSWORD_PATTERN = re.compile(r"^(?=.*[a-zA-Z])(?=.*[0-9])(?=.*[@$!%*#?&])[a-zA-Z0-9@$!%*#?&]{8,}$")

# Email format: local-part @ domain . tld (TLD must be ≥2 letters)
# Why not use pydantic's EmailStr?
#   EmailStr uses email-validator which applies RFC 5321 rules. Our tests
#   expect specific error messages from our own validator, so we control
#   validation explicitly with a regex that captures the exact cases we need.
_EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")

# Error messages — defined as constants so they match the feature file exactly.
# Any change here MUST be reflected in the .feature file and vice versa.
MSG_PASSWORD_COMPLEXITY = "Password does not meet the complexity requirements. Please fix it."  # nosec: B105 — user-facing error message, not a credential
MSG_MISSING_FIELDS = "Missing required registration details. Please fix it!"
MSG_EMAIL_FORMAT = "Incorrect email address format. Please fix it."


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class UserRegisterRequest(BaseModel):
    """
    Payload for POST /auth/register.

    All fields are validated before the service layer is reached.
    Validation order (Pydantic v2): fields are validated in declaration order.
    """

    email: str
    password: str
    username: str
    first_name: str | None = None
    last_name: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Reject email addresses that do not match the expected format."""
        if not _EMAIL_PATTERN.match(v):
            raise ValueError(MSG_EMAIL_FORMAT)
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Enforce the password policy from docs/SECURITY.md Section 2.

        Rejects passwords that:
          - Are shorter than 8 characters
          - Contain no letter
          - Contain no digit
          - Contain no allowed special character (@$!%*#?&)
          - Contain characters outside letters, digits, and @$!%*#?&
        """
        if not _PASSWORD_PATTERN.match(v):
            raise ValueError(MSG_PASSWORD_COMPLEXITY)
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Reject empty or whitespace-only usernames."""
        if not v or not v.strip():
            raise ValueError(MSG_MISSING_FIELDS)
        return v


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class UserRegisterResponse(BaseModel):
    """
    Response body for a successful POST /auth/register (HTTP 201).

    Only the `message` field is required by the feature file.
    Additional fields may be added in later features without breaking clients.
    """

    model_config = ConfigDict(from_attributes=True)

    message: str


# ---------------------------------------------------------------------------
# Login schemas
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    """
    Payload for POST /auth/login.

    Uses plain str for email — no EmailStr or format validation.
    Login must accept any string and let the DB lookup determine validity.
    This prevents 422 on malformed emails (feature file Scenario 2 sends
    'john.doe@example' which has no TLD — must get 401, not 422).
    """

    email: str
    password: str


class LoginData(BaseModel):
    """
    Data payload for a successful POST /auth/login (HTTP 200).

    Returned inside ApiResponse[LoginData]. Contains only the access token
    for this feature iteration — refresh token and cookies are deferred.
    """

    model_config = ConfigDict(from_attributes=True)

    access_token: str
    token_type: str = "bearer"
