"""Security utilities — demo identity resolution only.

WARNING: This module provides DEVELOPMENT-ONLY mock identity resolution.
It must never be used in production. Production deployments require
proper authentication (JWT, OAuth2, mTLS, etc.) with token/session verification.
"""
from __future__ import annotations

from app.core.config import get_settings
from app.core.exceptions import AuthRequired, DemoAuthDisabled

DEMO_USER_HEADER = "X-Demo-User-ID"


def ensure_demo_auth_allowed() -> None:
    """Raise DemoAuthDisabled if demo auth is not active."""
    settings = get_settings()
    if not settings.demo_auth_active:
        raise DemoAuthDisabled(
            "Demo authentication is disabled. "
            "Set APP_ENV=development and DEMO_AUTH_ENABLED=true to enable it. "
            "This mechanism is NOT suitable for production use."
        )


def extract_demo_user_id(headers: dict) -> str:
    """Extract and validate the demo user ID from request headers."""
    ensure_demo_auth_allowed()
    user_id = headers.get(DEMO_USER_HEADER) or headers.get(
        DEMO_USER_HEADER.lower()
    )
    if not user_id:
        raise AuthRequired(
            f"Missing {DEMO_USER_HEADER} header. "
            "Include a valid public user ID such as 'U-101'."
        )
    return user_id.strip()
