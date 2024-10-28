from datetime import datetime, timedelta
from typing import Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from redis.asyncio import ConnectionPool, Redis

from ideanest_assesment.db.models.user import User, pwd_context
from ideanest_assesment.services.redis.dependency import get_redis_pool
from ideanest_assesment.settings import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/token")

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_MINUTES = settings.refresh_token_expire_minutes


def create_access_token(data: Dict, expires_delta: timedelta | None = None) -> str:
    """
    Create an access token.

    Args:
        data (dict): The data to encode in the token.
        expires_delta (timedelta, optional): An optional timedelta to specify the token expiration time.
            Defaults to ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        str: The encoded JWT access token.
    """  # noqa: E501
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: Dict, expires_delta: timedelta | None = None) -> str:
    """Create a refresh token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Retrieve the current user from the access token.

    Args:
        token (str, optional): The access token. Obtained automatically via the `OAuth2PasswordBearer` scheme.

    Returns:
        User: The current user.

    Raises:
        HTTPException: If the token is invalid or the user is not found.
    """  # noqa: E501
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await User.find_one(User.email == email)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Retrieve the current active user.

    This dependency ensures the user is authenticated and potentially checks for additional
    conditions like account activation status.

    Args:
        current_user (User): The current user, obtained from the `get_current_user` dependency.

    Returns:
        User: The current active user.
    """  # noqa: E501

    # Add any additional checks for user status (e.g., is_active)
    return current_user


async def authenticate_user(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate a user and generate an access token.

    Args:
        form_data (OAuth2PasswordRequestForm): The user's login credentials.

    Returns:
        dict: A dictionary containing the access token and token type.

    Raises:
        HTTPException: If the user credentials are invalid.
    """
    user = await User.find_one(User.email == form_data.username)
    if not user or not user.verify_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires,
    )
    refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    refresh_token = create_refresh_token(
        data={"sub": user.email},
        expires_delta=refresh_token_expires,
    )
    user.refresh_token = refresh_token
    await user.save()
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


async def signup(user_data: dict) -> Dict:
    """
    Create a new user account.

    Args:
        user_data (UserCreate): The user registration data.

    Returns:
        dict: A success message.

    Raises:
        HTTPException: If a user with the provided email already exists.
    """
    existing_user = await User.find_one(User.email == user_data.get("email"))
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = pwd_context.hash(user_data.get("password"))
    new_user = User(
        name=user_data.get("name"),
        email=user_data.get("email"),
        hashed_password=hashed_password,
    )
    await new_user.create()
    return {"message": "User created successfully"}


async def new_refresh_token(
    refresh_token: str,
    redis_pool: ConnectionPool = Depends(get_redis_pool),
):
    """Refresh an access token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await User.find_one(User.email == email)
    if user is None or user.refresh_token != refresh_token:
        raise credentials_exception

    # Check if the refresh token has been revoked
    async with Redis(connection_pool=redis_pool) as redis:
        revoked = await redis.exists(f"revoked_token:{refresh_token}")
    if revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked",
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires,
    )
    refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    new_refresh_token = create_refresh_token(
        # Generate a new refresh token
        data={"sub": user.email},
        expires_delta=refresh_token_expires,
    )
    user.refresh_token = new_refresh_token
    await user.save()
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


async def revoke_refresh_token(
    refresh_token: str,
    current_user: User,
    redis_pool: ConnectionPool = Depends(get_redis_pool),
) -> dict:
    """Revoke a refresh token."""
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None or email != current_user.email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    async with Redis(connection_pool=redis_pool) as redis:
        # Store the refresh token in Redis with an expiration time
        await redis.set(
            f"revoked_token:{refresh_token}",
            1,
            ex=REFRESH_TOKEN_EXPIRE_MINUTES * 60,
        )
    return {"message": "Refresh token revoked"}
