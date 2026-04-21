"""
Shared Pydantic schemas used across all modules.

ApiResponse[T] is the standard success envelope for all API endpoints.
Module schemas define only the data payload (the T in ApiResponse[T]).

Why a generic envelope?
  Every success response has the same outer shape: data, message,
  correlation_id. Using a generic model enforces this consistently
  and lets FastAPI generate accurate OpenAPI docs for each endpoint.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """
    Standard success response envelope.

    All API endpoints return this shape:
    {
        "data": { ... },          # T — the endpoint-specific payload
        "message": "...",         # Human-readable status message
        "correlation_id": "..."   # UUID for request tracing
    }
    """

    data: T
    message: str
    correlation_id: str
