import typing
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr
from tortoise.contrib.pydantic import pydantic_model_creator

from axegaoshop.db.models.replenish import Replenish
from axegaoshop.db.models.user import User
from axegaoshop.settings import settings


class UserCreate(BaseModel):
    username: str
    password: typing.Optional[str] = None
    email: typing.Optional[EmailStr] = None


class UserUpdate(BaseModel):
    username: typing.Optional[str] = None
    photo: typing.Optional[str] = None


class UserDropPassword(BaseModel):
    email: EmailStr
    password: str


class UserReplenishBalance(BaseModel):
    payment_type: typing.Literal["sbp"]
    amount: float


class UserReplenishOut(BaseModel):
    number: str
    result_price: Decimal
    payment_type: str
    status: str
    created_datetime: datetime


class UserUpdateAdmin(BaseModel):
    username: typing.Optional[str] = None
    photo: typing.Optional[str] = None
    password: typing.Optional[str] = None
    is_admin: typing.Optional[bool] = None
    balance: typing.Optional[float] = None


class UserOutput(BaseModel):
    username: str
    email: typing.Optional[EmailStr]
    photo: typing.Optional[str]
    is_admin: bool
    balance: Decimal
    reg_datetime: datetime
    is_anonymous: bool

    class Config:
        from_attributes = True


class UserProductsComment(BaseModel):
    product_id: int  # айди товара, на который отзыв
    title: str  # название товраа
    order_id: int  # айди заказа


UserIn_Pydantic = pydantic_model_creator(
    User,
    exclude=(
        "replenishes",
        "shop_cart.id",
        "shop_cart.items.id",
        "shop_cart.cart_product",
    ),
)

UserForAdmin_Pydantic = pydantic_model_creator(
    User, exclude=("shop_cart", "orders", "reviews", "replenishes")
)

UserCart_Pydantic = pydantic_model_creator(
    User,
    exclude=(
        "shop_cart.id",
        "shop_cart.product.options",
        "shop_cart.product.category",
        "shop_cart.product.parameters",
        "shop_cart.parameter.data",
        "shop_cart.parameter.id" "shop_cart.product.category_id",
        "shop_cart.product.product_photos.id",
        "shop_cart.parameter.product",
        "shop_cart.reviews",
        "orders",
        "replenishes",
    ),
)

UserReplenish_Pydantic = pydantic_model_creator(Replenish)
