"""API-key authentication for the transport layer.

If an API key is configured, every route except ``/health`` requires a matching
``X-API-Key`` header. When no key is configured the dependency is a no-op (local use).
"""

from __future__ import annotations

from fastapi import Header, HTTPException, Request, status


async def require_api_key(
    request: Request,
    x_api_key: str | None = Header(default=None),
) -> None:
    """Reject requests without a valid ``X-API-Key`` when a key is configured."""
    expected = request.app.state.config.api_key
    if expected is None:
        return
    if x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing API key",
        )
