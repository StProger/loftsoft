import typing

from pydantic import BaseModel
from tortoise.contrib.pydantic import pydantic_model_creator

from axegaoshop.db.models.product import Option


class OptionUpdate(BaseModel):
    title: typing.Optional[str]
    value: typing.Optional[str]
    is_pk: typing.Optional[bool]


class OptionCreate(BaseModel):
    title: str
    value: str
    is_pk: typing.Optional[bool] = False


OptionIn_Pydantic = pydantic_model_creator(Option, exclude=("product",))
