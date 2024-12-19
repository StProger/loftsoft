from fastapi import APIRouter, Depends, HTTPException

from axegaoshop.db.models.product import Option, Product
from axegaoshop.services.security.jwt_auth_bearer import JWTBearer
from axegaoshop.services.security.users import current_user_is_admin
from axegaoshop.web.api.products.options.schema import (
    OptionCreate,
    OptionIn_Pydantic,
    OptionUpdate,
)

router = APIRouter()


@router.get(path="/product/{id}/options", response_model=list[OptionIn_Pydantic])
async def get_product_options(id: int):
    if not await Product.get_or_none(id=id):
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    return await OptionIn_Pydantic.from_queryset(Option.filter(product_id=id))


@router.post(
    path="/product/{id}/options",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    response_model=OptionIn_Pydantic,
)
async def create_product_option(id: int, option: OptionCreate):

    option = Option(
        title=option.title, value=option.value, is_pk=option.is_pk, product_id=id
    )

    if not await option.is_available():
        raise HTTPException(status_code=400, detail="NOT_AVAILABLE")

    await option.save()

    return option


@router.patch(
    path="/option/{id}",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    response_model=OptionIn_Pydantic,
)
async def update_product_option(id: int, option: OptionUpdate):
    if not await Option.get_or_none(id=id):
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    option_ = Option(title=option.title, value=option.value, is_pk=option.is_pk)
    if option.is_pk:
        if not await option_.is_available():
            raise HTTPException(status_code=400, detail="NOT_AVAILABLE")

    await Option.filter(id=id).update(**option.model_dump(exclude_unset=True))

    return await Option.filter(id=id).first()


@router.delete(
    path="/option/{id}",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    status_code=200,
)
async def delete_product_option(id: int):
    if not await Option.get_or_none(id=id):
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    await Option.filter(id=id).delete()
