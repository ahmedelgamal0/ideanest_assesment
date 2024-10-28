from typing import List

from beanie import Document, Indexed, Link
from pydantic import BaseModel

from ideanest_assesment.db.models.user import User


class OrganizationMember(BaseModel):
    """Represents a member of an organization."""

    user: Link[User]
    access_level: str

class Organization(Document):
    """Represents an organization."""

    name: Indexed(str, unique=True)
    description: str
    members: List[OrganizationMember] = []

    class Settings:
        name = "organizations"
