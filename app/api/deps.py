"""FastAPI dependency injection providers."""
from __future__ import annotations

from typing import Callable, List, Optional
from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ALL_ROLES, ROLE_ADMIN, ROLE_ADJUSTER, ROLE_CUSTOMER
from app.core.exceptions import AuthRequired, Forbidden, ResourceNotFound
from app.core.security import DEMO_USER_HEADER, ensure_demo_auth_allowed
from app.db.models.user import User
from app.db.repositories.user_repository import UserRepository
from app.db.session import get_db_session


async def get_db() -> AsyncSession:
    """Yield DB session dependency."""
    async for session in get_db_session():
        yield session


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> User:
    """Extract authenticated demo user from headers."""
    ensure_demo_auth_allowed()
    user_id = request.headers.get(DEMO_USER_HEADER) or request.headers.get(
        DEMO_USER_HEADER.lower()
    )
    if not user_id:
        raise AuthRequired(
            f"Missing required authentication header '{DEMO_USER_HEADER}'. "
            "Example: X-Demo-User-ID: U-101"
        )

    user_repo = UserRepository(session)
    user = await user_repo.get_by_public_id(user_id.strip())
    if user is None:
        raise AuthRequired(f"Demo user '{user_id}' not found.")
    return user


def require_roles(*allowed_roles: str) -> Callable:
    """Dependency factory checking that user role is in allowed_roles."""

    async def _role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise Forbidden(
                f"Role '{user.role}' is not authorized to access this resource. "
                f"Required: {', '.join(allowed_roles)}."
            )
        return user

    return _role_checker


require_customer = require_roles(ROLE_CUSTOMER)
require_adjuster = require_roles(ROLE_ADJUSTER)
require_admin = require_roles(ROLE_ADMIN)
require_adjuster_or_admin = require_roles(ROLE_ADJUSTER, ROLE_ADMIN)
