import typing
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator
from tortoise.contrib.pydantic import pydantic_model_creator

from axegaoshop.db.models.order import Order
from axegaoshop.settings import settings


class OrderStatus:
    WAIT_FOR_PAYMENT = "waiting_payment"
    CANCELED = "canceled"
    FINISHED = "finished"


class OrderCreate(BaseModel):
    promocode: typing.Optional[str] = None
    straight: bool
    email: str
    payment_type: str

    parameter_id: int | None = None
    count: int | None = None

    @field_validator("payment_type")
    def validate_payment_type(cls, v: str) -> str:
        if v not in settings.payment_types:
            raise ValueError("Unsupported payment type")
        return v

    @field_validator("count")
    def validate_count(cls, v: int | None) -> int | None:
        if v is not None:
            if v <= 0:
                raise ValueError("invalid count")
        return v

    @model_validator(mode="after")
    def validate_order_params(self) -> "OrderCreate":
        if self.straight:
            if not self.parameter_id or not self.count:
                raise ValueError("parameter_id or count required for straight payment")

        if not self.straight:
            if self.parameter_id or self.count:
                raise ValueError(
                    "parameter_id or count shouldn't be used in non-straight payment!"
                )

        return self


class OrderStatusOut(BaseModel):
    status: str


class OrderDataOut(BaseModel):
    id: int = Field(description="Айди параметра (версии товара)")
    title: str
    count: int
    give_type: typing.Literal["string", "hand", "file"]
    photo: str
    items: list[str]

    @model_validator(mode="after")
    def set_give_type(self) -> "OrderDataOut":
        """если нет товаров - выдача руками"""
        if not self.items:
            self.give_type = "hand"
        return self


class OrderFinishOut(BaseModel):
    id: int
    number: str
    result_price: float
    order_data: list[OrderDataOut]
    uri: typing.Optional[str]


class OrderDataHistory(BaseModel):
    number: str
    order_id: int
    date: datetime
    email: str
    product: str
    give_type: str
    count: int


OrderIn_Pydantic = pydantic_model_creator(Order, exclude=("user",))
