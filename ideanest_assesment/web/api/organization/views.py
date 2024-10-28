from fastapi import APIRouter, Depends

from ideanest_assesment.auth.auth import get_current_active_user
from ideanest_assesment.db.dao.organization_dao import OrganizationDAO
from ideanest_assesment.db.models.user import User
from ideanest_assesment.web.api.organization.schema import (
    OrganizationCreate,
    OrganizationInvite,
    OrganizationResponse,
    OrganizationUpdate,
)

router = APIRouter()


@router.post(
    "/",
    dependencies=[Depends(get_current_active_user)],
)
async def create_organization_endpoint(
    organization_data: OrganizationCreate,
    current_user: User = Depends(get_current_active_user),
):
    """Create a new organization."""
    organization =  await OrganizationDAO.create_organization(organization_data, current_user)
    return {"id": f"{organization.id}"}

@router.get(
    "/{organization_id}",
    dependencies=[Depends(get_current_active_user)],
)
async def get_organization_endpoint(organization_id: str):
    """Retrieve an organization by its ID."""
    return await OrganizationDAO.get_organization(organization_id)


@router.get(
    "/",
    dependencies=[Depends(get_current_active_user)],
)
async def get_all_organizations_endpoint():
    """Retrieve all organizations."""
    return await OrganizationDAO.get_all_organizations()



@router.put(
    "/{organization_id}",
    dependencies=[Depends(get_current_active_user)],
)
async def update_organization_endpoint(
    organization_id: str,
    organization_data: OrganizationUpdate,
):
    """Update an organization by its ID."""
    return await OrganizationDAO.update_organization(
        organization_id,
        organization_data,
    )


@router.delete(
    "/{organization_id}",
    dependencies=[Depends(get_current_active_user)],
)
async def delete_organization_endpoint(organization_id: str) -> None:
    """Delete an organization by its ID."""
    await OrganizationDAO.delete_organization(organization_id)
    return {"message": "Organization deleted successfully"}


@router.post("/{organization_id}/invite")
async def invite_user_endpoint(
    organization_id: str,
    invite_data: OrganizationInvite,
    current_user: User = Depends(get_current_active_user),
):
    """Invites user to Organization."""
    await OrganizationDAO.invite_user(organization_id, invite_data, current_user)
    return {"message": "User invited successfully"}
