from fastapi import APIRouter, Depends, HTTPException
from tortoise.functions import Coalesce, Count

from axegaoshop.db.models.order import Order
from axegaoshop.db.models.promocode import Promocode
from axegaoshop.db.models.user import User
from axegaoshop.services.security.jwt_auth_bearer import JWTBearer
from axegaoshop.services.security.users import current_user_is_admin, get_current_user
from axegaoshop.web.api.promocodes.schema import (
    CreatePromocode,
    PromocodeIn,
    PromocodeIn_Pydantic,
    UpdatePromocode,
)

router = APIRouter()


@router.get(
    path="/promocodes",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    response_model=list[PromocodeIn],
)
async def get_promocodes(limit: int = 20, offset: int = 0):
    promocodes = await (
        Promocode.all()
        .prefetch_related()
        .limit(limit)
        .offset(offset)
        .annotate(usage_count=Coalesce(Count("orders"), 0))
    )

    return promocodes


@router.post(
    path="/promocodes/",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    status_code=201,
)
async def create_promocode(promocode: CreatePromocode):
    """Для создания безлимитного промо: *activations_count = -1*"""
    await Promocode.create(**promocode.model_dump())


@router.patch(
    path="/promocode/{id}",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    response_model=PromocodeIn_Pydantic,
    status_code=200,
)
async def update_promocode(id: int, promocode: UpdatePromocode):
    if not await Promocode.get_or_none(id=id):
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    await Promocode.filter(id=id).update(**promocode.model_dump(exclude_unset=True))

    return await PromocodeIn_Pydantic.from_queryset_single(
        Promocode.filter(id=id).first()
    )


@router.delete(
    path="/promocode/{id}",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    status_code=200,
)
async def delete_promocode(id: int):
    if not await Promocode.get_or_none(id=id):
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    await Promocode.filter(id=id).delete()


@router.get(
    path="/promocode/{name}/use", response_model=PromocodeIn_Pydantic, status_code=200
)
async def apply_promocode(name: str, user: User = Depends(get_current_user)):
    """name - введенный пользователем промокод"""
    promocode: Promocode = await Promocode.get_or_none(name=name)

    if not promocode:
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    if not await promocode.active():
        raise HTTPException(status_code=404, detail="PROMO_INACTIVE")

    if user:
        order = Order.filter(promocode=promocode, user=user, status="finished")
        if await order.exists():
            raise HTTPException(status_code=404, detail="PROMO_ALREADY_USED")

    await promocode.refresh_from_db()

    return await PromocodeIn_Pydantic.from_tortoise_orm(promocode)
