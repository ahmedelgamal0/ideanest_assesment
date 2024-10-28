from typing import Dict

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from redis.asyncio import ConnectionPool

from ideanest_assesment.auth.auth import (
    authenticate_user,
    get_current_active_user,
    new_refresh_token,
    revoke_refresh_token,
    signup,
)
from ideanest_assesment.db.models.user import User
from ideanest_assesment.services.redis.dependency import get_redis_pool
from ideanest_assesment.web.api.user.schema import Token, UserCreate, UserResponse

router = APIRouter()


@router.post("/signup", response_model=Dict)
async def signup_endpoint(user_data: UserCreate) -> Dict:
    """Create a new user account."""
    return await signup(user_data.model_dump())


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    """Obtain an access token."""
    return await authenticate_user(form_data)


@router.post("/refresh-token", response_model=Token)
async def refresh_token_endpoint(refresh_token: str) -> Token:
    """Refresh an access token."""
    return await new_refresh_token(refresh_token)


@router.post("/revoke-refresh-token/")
async def revoke_refresh_token_endpoint(
    refresh_token: str,
    current_user: User = Depends(get_current_active_user),
    redis_pool: ConnectionPool = Depends(get_redis_pool),
):
    """Revoke a refresh token."""
    return await revoke_refresh_token(refresh_token, current_user, redis_pool)


@router.get("/users/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Retrieve the current user's information."""
    return current_user
