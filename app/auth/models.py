"""
SQLAlchemy model for the users table.

Matches docs/DATA_MODELS.md → Module 1: Auth exactly.
All field names, types, constraints, and indexes come from that document.

Why separate models.py from schemas.py?
  - models.py = the database table definition (what SQLAlchemy talks to PostgreSQL with)
  - schemas.py = the API data shapes (what FastAPI validates and returns as JSON)
  Keeping them separate means a DB schema change doesn't automatically leak
  into the API,
  and vice versa. You control what data crosses each boundary explicitly.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserRole(str, enum.Enum):
    """RBAC roles stored in the database. Values match DATA_MODELS.md exactly."""

    admin = "admin"
    super_user = "super_user"
    user = "user"


class UserStatus(str, enum.Enum):
    """Account lifecycle statuses. Values match DATA_MODELS.md exactly."""

    active = "active"
    suspended = "suspended"
    locked = "locked"
    inactive = "inactive"
    pending = "pending"


class User(Base):
    """
    Represents a user account in the system.

    Table: users
    Auth module: app/auth/

    Self-referential FKs (created_by, updated_by → users.id) record which
    admin created or last modified each account. For self-registered users,
    both fields are NULL because no authenticated user initiated the action.

    No soft-delete fields on this table — users are not user-created content.
    See DATA_MODELS.md Note under Module 1: Auth.
    """

    __tablename__ = "users"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Identity fields
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # RBAC — default is "user" per DATA_MODELS.md; registration sets "super_user"
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="userrole"), nullable=False, default=UserRole.user)

    # Account lifecycle
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="userstatus"), nullable=False, default=UserStatus.pending
    )

    # Lockout tracking (populated by login feature, NULLable until then)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_password_change: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Name fields (optional)
    first_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Mandatory audit fields (every table must have these — DATA_MODELS.md)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now()
    )
    # Self-referential FKs: nullable because self-registered users have no "creator"
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    # Explicit indexes declared here so Alembic autogenerate picks them up correctly.
    # Named per DATA_MODELS.md naming convention: ix_<table>_<column>
    __table_args__ = (
        Index("ix_users_email", "email"),
        Index("ix_users_username", "username"),
        Index("ix_users_status", "status"),
    )
