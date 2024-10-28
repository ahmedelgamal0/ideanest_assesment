from fastapi import HTTPException

from ideanest_assesment.db.models.organization import Organization, OrganizationMember
from ideanest_assesment.db.models.user import User
from ideanest_assesment.web.api.organization.schema import (
    OrganizationCreate,
    OrganizationUpdate,
)


class OrganizationDAO:
    """
    Data Access Object for managing Organization models.

    Provides methods for creating, retrieving, updating, and deleting organizations.
    """

    @classmethod
    async def create_organization(
        cls,
        organization_data: OrganizationCreate,
        current_user: User,
    ) -> Organization:
        """
        Create a new organization.

        Args:
            organization_data (OrganizationCreate): The data for the new organization.
            current_user (User): The user creating the organization.

        Returns:
            OrganizationResponse: The created organization.
        """
        organization = Organization(**organization_data.model_dump())
        # Add the creator as the first admin member
        organization.members.append(
            OrganizationMember(user=current_user, access_level="admin"),
        )
        await organization.create()
        return organization

    @classmethod
    async def get_organization(cls, organization_id: str) -> Organization:
        """
        Retrieve an organization by ID.

        Args:
            organization_id (str): The ID of the organization.

        Returns:
            Organization: The retrieved organization.

        Raises:
            HTTPException: If the organization is not found.
        """
        organization = await Organization.get(organization_id)
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")
        return organization

    @classmethod
    async def get_all_organizations(cls) -> list[Organization]:
        """
        Retrieve all organizations.

        Returns:
            list[OrganizationResponse]: A list of all organizations.
        """
        return await Organization.find_all().to_list()

    @classmethod
    async def update_organization(
        cls,
        organization_id: str,
        organization_data: OrganizationUpdate,
    ) -> Organization:
        """
        Update an organization.

        Args:
            organization_id (str): The ID of the organization to update.
            organization_data (OrganizationUpdate): The data to update.

        Returns:
            Organization: The updated organization.
        """
        organization = await cls.get_organization(organization_id)
        update_data = organization_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(organization, key, value)
        await organization.save()
        return organization

    @classmethod
    async def delete_organization(cls, organization_id: str) -> None:
        """
        Delete an organization.

        Args:
            organization_id (str): The ID of the organization to delete.
        """
        organization = await cls.get_organization(organization_id)
        await organization.delete()
