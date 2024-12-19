import typing

from pydantic import BaseModel
from tortoise.contrib.pydantic import pydantic_model_creator

from axegaoshop.db.models.promocode import Promocode


class CreatePromocode(BaseModel):
    name: str
    activations_count: int = 1
    sale_percent: float


class UpdatePromocode(BaseModel):
    name: typing.Optional[str] = None
    activations_count: typing.Optional[int] = None
    sale_percent: typing.Optional[float] = None


class UsePromocode(BaseModel):
    name: str
    sale_percent: float


class PromocodeIn(BaseModel):
    id: int
    name: str
    activations_count: int
    sale_percent: int
    usage_count: int


PromocodeIn_Pydantic = pydantic_model_creator(Promocode)
