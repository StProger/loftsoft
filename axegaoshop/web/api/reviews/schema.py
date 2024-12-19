import datetime
import typing

from pydantic import BaseModel
from tortoise.contrib.pydantic import pydantic_model_creator

from axegaoshop.db.models.order import Order
from axegaoshop.db.models.review import Review


class ReviewCreate(BaseModel):
    """тело отзыва"""

    rate: int  # кол-во звезд в отзыве
    text: str  # текст отзыва
    images: typing.Optional[list[str]] = None
    order_id: int  # айди заказа, по которому пишется отзыв
    product_id: int  # айди товара, по которому пишется отзыв


class ReviewOutput(BaseModel):
    """отзыв на страницы пользователям"""

    id: int
    rate: int
    text: str
    images: typing.Optional[list[str]] = None
    product: str  # название товара
    user: str  # логин пользователя
    user_photo: str  # ава пользователя
    created_datetime: datetime.datetime  # дата создания

    class Config:
        from_attributes = True


class ReviewUpdate(BaseModel):
    """обновление отзыва (пока только текст)"""

    text: str


ReviewIn_Pydantic = pydantic_model_creator(
    Review, exclude=("user", "straight", "result_price", "status", "order", "product")
)
ReviewInAdmin_Pydantic = pydantic_model_creator(
    Review, exclude=("order", "user.orders", "user.shop_cart", "order", "product")
)
