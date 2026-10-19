"""Demo authentication endpoints per Section 7.2 and 7.3."""
from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.exceptions import ResourceNotFound
from app.core.security import ensure_demo_auth_allowed
from app.db.repositories.user_repository import UserRepository
from app.schemas.user import CurrentUserResponse, DemoLoginRequest, DemoLoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/demo-login", response_model=DemoLoginResponse)
async def demo_login(
    req: DemoLoginRequest,
    session: AsyncSession = Depends(get_db),
) -> DemoLoginResponse:
    """Development-only demo login. Validates demo user ID and instructs caller
    to include 'X-Demo-User-ID' header on subsequent requests.
    """
    ensure_demo_auth_allowed()
    user_repo = UserRepository(session)
    user = await user_repo.get_by_public_id(req.public_id.strip())
    if user is None or not user.is_active:
        raise ResourceNotFound(f"Demo user '{req.public_id}' not found or inactive.")

    return DemoLoginResponse(
        message=f"Demo identity '{user.public_id}' ({user.name}, role: {user.role}) validated.",
        public_id=user.public_id,
        role=user.role,
        instruction=f"Include 'X-Demo-User-ID: {user.public_id}' header in all subsequent requests.",
    )


@router.get("/demo-users", response_model=List[CurrentUserResponse])
async def list_demo_users(
    session: AsyncSession = Depends(get_db),
) -> List[CurrentUserResponse]:
    """List available demo personas for development and exploratory testing."""
    ensure_demo_auth_allowed()
    user_repo = UserRepository(session)
    users = await user_repo.get_all()
    return [
        CurrentUserResponse(
            public_id=u.public_id,
            name=u.name,
            role=u.role,
            email=u.email,
        )
        for u in users
    ]
