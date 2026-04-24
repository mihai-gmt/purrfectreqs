"""
Password hashing utilities for the auth module.

Uses passlib with the argon2 backend.

Why argon2 over bcrypt?
  Argon2 won the Password Hashing Competition (2015) and is specifically
  designed to be resistant to GPU-based brute-force attacks by requiring
  configurable amounts of memory. passlib falls back to bcrypt automatically
  if the argon2-cffi package is unavailable, ensuring the app doesn't crash.

  NEVER use hashlib.sha256 or similar non-purpose-built hashes for passwords —
  they are too fast and offer no resistance to GPU attacks.

Raw passwords MUST NOT:
  - Be logged (even at DEBUG level)
  - Be stored in the database
  - Appear in exception messages or error responses
"""

from passlib.context import CryptContext

# CryptContext configures which algorithm(s) are acceptable.
# "deprecated='auto'" means older hashes are automatically upgraded on next
# successful login — you don't need to re-hash all passwords at once if you
# change the algorithm in the future.
_pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password using argon2.

    Args:
        plain_password: The raw password string from the user.

    Returns:
        A passlib argon2 hash string suitable for DB storage.

    Note:
        NEVER log the input or output of this function.
    """
    return _pwd_context.hash(plain_password)  # type: ignore[no-any-return]  # passlib stubs return Any; actual return is str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a stored argon2 hash.

    Args:
        plain_password: The raw password to check.
        hashed_password: The stored hash from the database.

    Returns:
        True if the password matches the hash, False otherwise.

    Note:
        NEVER log the plain_password argument.
    """
    return _pwd_context.verify(plain_password, hashed_password)  # type: ignore[no-any-return]  # passlib stubs return Any; actual return is bool
