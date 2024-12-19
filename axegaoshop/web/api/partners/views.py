from fastapi import APIRouter, Depends, HTTPException

from axegaoshop.db.models.partner import Partner
from axegaoshop.services.security.jwt_auth_bearer import JWTBearer
from axegaoshop.services.security.users import current_user_is_admin
from axegaoshop.web.api.partners.schema import CreatePartner, PartnerIn_Pydantic

router = APIRouter()


@router.post(
    "/partners",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    status_code=201,
)
async def create_partner(partner: CreatePartner):
    await Partner.create(**partner.model_dump())


@router.delete(
    "/partner/{id}",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    status_code=200,
)
async def delete_partner(id: int):
    partner = await Partner.get_or_none(id=id)

    if not partner:
        raise HTTPException(status_code=404, detail="PARTNER_NOT_FOUND")

    await partner.delete()


@router.get("/partners", response_model=list[PartnerIn_Pydantic], status_code=200)
async def get_partners():
    return await PartnerIn_Pydantic.from_queryset(Partner.all())
