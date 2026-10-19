"""Current user endpoint per Section 7.3."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.db.models.user import User
from app.schemas.user import CurrentUserResponse

router = APIRouter(tags=["user"])


@router.get("/me", response_model=CurrentUserResponse)
async def get_me(user: User = Depends(get_current_user)) -> CurrentUserResponse:
    """Return the profile and role of the currently authenticated demo identity."""
    return CurrentUserResponse(
        public_id=user.public_id,
        name=user.name,
        role=user.role,
        email=user.email,
    )
