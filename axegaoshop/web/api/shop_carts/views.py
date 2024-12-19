from fastapi import APIRouter, Depends, HTTPException

from axegaoshop.db.models.order import Order
from axegaoshop.db.models.product import Product
from axegaoshop.db.models.shop_cart import add_to_cart
from axegaoshop.db.models.user import User
from axegaoshop.services.security.jwt_auth_bearer import JWTBearer
from axegaoshop.services.security.users import get_current_user
from axegaoshop.web.api.products.schema import ProductToCart
from axegaoshop.web.api.users.schema import UserCart_Pydantic

router = APIRouter()


@router.post(
    path="/cart/add",
    dependencies=[Depends(JWTBearer())],
    response_model=UserCart_Pydantic,
)
async def add_or_create_cart(
    data: ProductToCart, user: User = Depends(get_current_user)
):
    """
    Работа с корзиной пользователя
    1. В count указывать **полное** количество товара (не инкремент/декремент).
    2. При передаче count=0 происходит **удаление товара** из корзины.
    """
    if not await Product.get_or_none(
        id=data.product_id, parameters__id=data.parameter_id
    ):
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    if data.count < 0:
        raise HTTPException(status_code=400, detail="BAD_COUNT")

    await add_to_cart(user.id, data.product_id, data.parameter_id, data.count)

    # orders = await Order.filter(user=user, status="waiting_payment").all()
    # # отменяем заказ, если есть активный
    # [await order.cancel() for order in orders]

    return await UserCart_Pydantic.from_queryset_single(User.filter(id=user.id).first())


# @router.patch(
#     path="/photo/{id}",
#     dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
#     response_model=PhotoIn_Pydantic
# )
# async def update_product_photo(id: int, parameter: PhotoUpdate):
#     if not await ProductPhoto.get_or_none(id=id):
#         raise HTTPException(status_code=404, detail="NOT_FOUND")
#
#     await ProductPhoto.filter(id=id).update(**parameter.model_dump(exclude_unset=True))
#
#     return await ProductPhoto.filter(id=id).first()
#
#
# @router.delete(
#     path="/photo/{id}",
#     dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
#     status_code=200
# )
# async def delete_product_photo(id: int):
#     if not await ProductPhoto.get_or_none(id=id):
#         raise HTTPException(status_code=404, detail="NOT_FOUND")
#
#     await ProductPhoto.filter(id=id).delete()
