from bson import ObjectId
from pydantic import BaseModel, Field, field_validator

from ideanest_assesment.db.models.organization import OrganizationMember


class OrganizationCreate(BaseModel):
    """Schema for creating an organization."""

    name: str
    description: str

class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""

    name: str | None = None
    description: str | None = None

class OrganizationResponse(BaseModel):
    """Schema for the organization response."""

    id: str = Field(..., alias="_id")
    name: str
    description: str
    members: list[OrganizationMember] = []


