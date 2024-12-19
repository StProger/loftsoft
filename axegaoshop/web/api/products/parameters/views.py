from fastapi import APIRouter, Depends, HTTPException

from axegaoshop.db.models.product import (
    Parameter,
    Product,
    change_parameter_order,
    update_parameter_data,
)
from axegaoshop.services.security.jwt_auth_bearer import JWTBearer
from axegaoshop.services.security.users import current_user_is_admin
from axegaoshop.web.api.products.parameters.schema import (
    ParameterCreate,
    ParameterIn_Pydantic,
    ParameterOrderChange,
    ParameterUpdate,
)

router = APIRouter()


@router.get(path="/product/{id}/parameters", response_model=list[ParameterIn_Pydantic])
async def get_product_parameters(id: int):
    if not await Product.get_or_none(id=id):
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    return await ParameterIn_Pydantic.from_queryset(Parameter.filter(product_id=id))


@router.post(
    path="/product/{id}/parameters",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    response_model=ParameterIn_Pydantic,
)
async def create_product_parameter(id: int, parameter: ParameterCreate):
    if not await Product.get_or_none(id=id):
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    parameter_ = Parameter(
        title=parameter.title,
        description=parameter.description,
        price=parameter.price,
        give_type=parameter.give_type,
        has_sale=parameter.has_sale,
        sale_price=parameter.sale_price,
        product_id=id,
    )

    await parameter_.save()

    return parameter_


@router.patch(
    path="/parameter/{id}",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    response_model=ParameterIn_Pydantic,
)
async def update_product_parameter(id: int, parameter: ParameterUpdate):
    if not await Parameter.get_or_none(id=id):
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    await Parameter.filter(id=id).update(**parameter.model_dump(exclude_unset=True))

    return await Parameter.filter(id=id).first()


@router.patch(
    path="/parameter/{id}/data",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    status_code=200,
)
async def update_product_parameter_data(id: int, data: list[str]):
    """обновление строк параметра товара"""
    if not await Parameter.get_or_none(id=id):
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    await update_parameter_data(id, data)


@router.delete(
    path="/parameter/{id}",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    status_code=200,
)
async def delete_product_parameter(id: int):
    if not await Parameter.get_or_none(id=id):
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    await Parameter.filter(id=id).delete()


@router.post(
    "/parameter/order",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    status_code=200,
)
async def change_product_order_router(parameter_ids: list[int]):
    res = await change_parameter_order(parameter_ids)

    if not res:
        raise HTTPException(status_code=404, detail="NOT_FOUND")
