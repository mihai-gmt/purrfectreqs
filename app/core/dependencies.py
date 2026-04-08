"""
Core FastAPI dependencies shared across all modules.

These dependencies are injected into router endpoints via Depends().
Module-specific dependencies belong in their own module's dependencies.py.

Why centralize cross-cutting dependencies here?
  Correlation ID extraction is needed by every module, not just auth.
  Putting it in app/core/ avoids circular imports and makes it clear
  that this is infrastructure, not business logic.
"""

from fastapi import Request


def get_correlation_id(request: Request) -> str:
    """
    Extract the correlation ID from the current request.

    The correlation_id_middleware in app/main.py runs before any endpoint
    and sets request.state.correlation_id — either from the incoming
    X-Correlation-ID header (allowing frontends and API clients to pass
    their own ID for end-to-end tracing) or by generating a new UUID.

    This dependency makes the correlation ID available as a simple string
    parameter in any endpoint via Depends(get_correlation_id).

    Why a dependency instead of reading request.state directly?
      Using Depends() makes the correlation ID appear in the function
      signature, which keeps endpoints explicit about what they need
      and makes testing easier (you can override the dependency).
    """
    return getattr(request.state, "correlation_id", "unknown")
