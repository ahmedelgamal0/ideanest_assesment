from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Represents the data required to create a new user."""

    name: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Represents the data returned in response to a user creation or retrieval request."""  # noqa: E501

    name: str
    email: EmailStr


class Token(BaseModel):
    """Schema for token response."""

    access_token: str
    refresh_token: str
    token_type: str
